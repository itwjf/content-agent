"""
导演引擎
融合：整场剧本（阶段目标/话术要点）+ 商品信息 + 互动理解结果 → 导演脚本
LLM 产出优先，失败/超时降级为规则模板（复用卖点模块话术）
"""
import asyncio
import json
import re
from typing import Optional

from loguru import logger

from app.core.config import get_settings
from app.core.llm import call_llm
from app.services.agent.llm_interaction_engine import _parse_llm_json
from app.services.director.models import DirectorLine, DirectorScript, EMOTIONS, PACES, PRIORITIES
from app.services.modules.selling_point_module import selling_point_module

SYSTEM_PROMPT = """你是直播电商的导演，为数字人主播生成下一轮口播的导演脚本。严格输出 JSON（不要任何其他文字或代码块标记）：
{
  "lines": [
    {"text": "台词（口语化，50-100字）", "emotion": "neutral|enthusiastic|warm|urgent|serious", "action": "动作建议", "pace": "slow|normal|fast"}
  ],
  "show_product_card": true或false,
  "priority": "高|中|低",
  "trigger_reason": "触发原因（30字内）"
}

规则：
1. lines 为 1~2 句；必须直接回应高频问题/负面反馈/购买意向，或推进当前阶段目标
2. 涉及产品宣传时严守广告法：不得使用"最/第一/唯一/保证/绝对/根治"等违禁词
3. 购买意向优先级高；负面反馈优先安抚；刷屏问题必须回应
4. action 面向数字人画面（如"拿起产品展示成分表"/"切商品特写"/"指向弹幕"）"""


class DirectorEngine:
    """导演引擎"""

    def __init__(self):
        self.llm_timeout = get_settings().decision_llm_timeout

    async def produce(
        self,
        session_id: int,
        stage: str,
        product_data: Optional[dict],
        interaction_result: dict,
        script_stages: Optional[list] = None,
    ) -> DirectorScript:
        """产出导演脚本：LLM 优先，规则降级

        Args:
            session_id: 场次ID
            stage: 当前直播阶段
            product_data: 商品数据（中文键：产品名称/价格/成分/功效/规格）
            interaction_result: LLM互动理解结果（含 degraded 标记）
            script_stages: 整场剧本的阶段规划（[{stage, goal, key_points, talk_points}]）
        """
        stage_plan = self._find_stage_plan(script_stages, stage)
        degraded = bool(interaction_result.get("degraded"))

        try:
            script = await asyncio.wait_for(
                self._llm_produce(session_id, stage, stage_plan, product_data, interaction_result),
                timeout=self.llm_timeout,
            )
            script.degraded = degraded
            return script
        except asyncio.TimeoutError:
            reason = f"导演脚本 LLM 超时（>{self.llm_timeout}s）"
        except Exception as e:
            reason = f"导演脚本 LLM 失败: {type(e).__name__}: {e}"

        logger.warning(f"[导演] {reason}，降级为规则模板")
        script = self._rule_produce(session_id, stage, stage_plan, product_data, interaction_result)
        script.degraded = True
        script.trigger_reason = f"{script.trigger_reason}（{reason}）" if script.trigger_reason else reason
        return script

    # ---------- LLM 产出 ----------

    async def _llm_produce(self, session_id, stage, stage_plan, product_data, interaction_result) -> DirectorScript:
        lines_desc = "\n".join(f"{i + 1}. {m}" for i, m in enumerate(interaction_result.get("_messages", []))[:10])
        high_freq = json.dumps(interaction_result.get("高频问题", [])[:5], ensure_ascii=False)
        negatives = json.dumps(interaction_result.get("负面反馈", [])[:5], ensure_ascii=False)
        insight = interaction_result.get("关键洞察", "无")
        emotion_stats = json.dumps(interaction_result.get("情绪统计", {}), ensure_ascii=False)

        plan_desc = "无（使用默认阶段目标）"
        if stage_plan:
            plan_desc = json.dumps(stage_plan, ensure_ascii=False)

        product_desc = "无（未绑定商品）"
        if product_data:
            product_desc = json.dumps(product_data, ensure_ascii=False)

        prompt = f"""当前直播阶段：{stage}
阶段剧本规划：{plan_desc}

商品信息：{product_desc}

互动理解结果：
- 情绪统计：{emotion_stats}
- 高频问题：{high_freq}
- 负面反馈：{negatives}
- 关键洞察：{insight}
- 弹幕原文抽样：
{lines_desc}

请生成本轮导演脚本。"""

        raw = await asyncio.to_thread(call_llm, prompt, SYSTEM_PROMPT)
        parsed = _parse_llm_json(raw)

        lines = []
        for line in parsed.get("lines", [])[:3]:
            emotion = line.get("emotion", "neutral")
            pace = line.get("pace", "normal")
            lines.append(DirectorLine(
                text=str(line.get("text", "")).strip(),
                emotion=emotion if emotion in EMOTIONS else "neutral",
                action=str(line.get("action", "")),
                pace=pace if pace in PACES else "normal",
            ))
        lines = [l for l in lines if l.text]
        if not lines:
            raise ValueError("LLM 返回的 lines 为空")

        priority = parsed.get("priority", "中")
        return DirectorScript(
            session_id=session_id,
            stage=stage,
            lines=lines,
            show_product_card=bool(parsed.get("show_product_card", False)),
            product_sku=(product_data or {}).get("sku_id"),
            priority=priority if priority in PRIORITIES else "中",
            trigger_reason=str(parsed.get("trigger_reason", "")),
            source="llm",
        )

    # ---------- 规则降级 ----------

    def _rule_produce(self, session_id, stage, stage_plan, product_data, interaction_result) -> DirectorScript:
        """规则模板：负面安抚 > 高频问题应答 > 购买意向促单 > 阶段推进"""
        negatives = interaction_result.get("负面反馈", [])
        questions = interaction_result.get("高频问题", [])
        emotion_stats = interaction_result.get("情绪统计", {})

        # 1. 负面反馈聚集 → 安抚 + 价值强调
        if negatives:
            return DirectorScript(
                session_id=session_id, stage=stage,
                lines=[DirectorLine(
                    text="有宝宝提到价格问题，咱们这款用的是正规配方，一分价钱一分货，大家理性看待，适合自己的才是最好的。",
                    emotion="warm", action="保持微笑，语气诚恳", pace="slow",
                )],
                priority="高", trigger_reason="负面反馈聚集，启动安抚策略",
                source="rule",
            )

        # 2. 高频问题 → 复用卖点模块匹配话术
        if questions:
            top_question = questions[0].get("问题", "")
            matched = []
            if product_data:
                sell_result = selling_point_module.generate_selling_points(product_data, [{"关键词": top_question, "优先级": 85}])
                matched = sell_result.get("匹配卖点", [])
            text = matched[0]["话术"] if matched else f"很多宝宝在问{top_question}，这款产品正好针对这个问题做了专门设计，大家放心。"
            return DirectorScript(
                session_id=session_id, stage=stage,
                lines=[DirectorLine(text=text, emotion="enthusiastic", action="拿起产品展示", pace="normal")],
                show_product_card=bool(product_data),
                product_sku=(product_data or {}).get("sku_id"),
                priority="高", trigger_reason=f"弹幕高频问题：{top_question}",
                source="rule",
            )

        # 3. 购买意向 → 促单
        if emotion_stats.get("购买意向", 0) > 0:
            product_name = (product_data or {}).get("产品名称", "这款产品")
            return DirectorScript(
                session_id=session_id, stage=stage,
                lines=[DirectorLine(
                    text=f"看到很多宝宝想拍{product_name}，点击下方商品卡就可以下单，库存有限，喜欢的宝宝抓紧哦！",
                    emotion="urgent", action="指向商品卡位置", pace="fast",
                )],
                show_product_card=True,
                product_sku=(product_data or {}).get("sku_id"),
                priority="高", trigger_reason="弹幕购买意向集中，推商品卡促单",
                source="rule",
            )

        # 4. 默认 → 阶段推进话术
        talk_points = (stage_plan or {}).get("talk_points") or []
        tips = (stage_plan or {}).get("key_points") or []
        text = talk_points[0] if talk_points else (tips[0] if tips else "感谢家人们的陪伴，有问题随时打在公屏上，主播都会一一回复！")
        return DirectorScript(
            session_id=session_id, stage=stage,
            lines=[DirectorLine(text=text, emotion="warm", action="保持自然互动", pace="normal")],
            priority="中", trigger_reason="无高优事件，按剧本推进当前阶段",
            source="rule",
        )

    # ---------- 剧本工具 ----------

    @staticmethod
    def _find_stage_plan(script_stages: Optional[list], stage: str) -> Optional[dict]:
        """从整场剧本中匹配当前阶段的规划"""
        if not script_stages:
            return None
        for plan in script_stages:
            if isinstance(plan, dict) and plan.get("stage") == stage:
                return plan
        return None


# 引擎实例
director_engine = DirectorEngine()
