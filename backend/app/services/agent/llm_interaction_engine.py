"""
LLM 互动理解引擎
批量弹幕语义分析（意图识别/情绪分析/高频问题聚合），LLM 超时或失败自动降级到关键词规则方案。
输出结构与现有 InteractionModule 保持兼容（中文键），下游模块可无差别消费。
"""
import asyncio
import json
import re
from typing import List, Optional

from loguru import logger

from app.core.config import get_settings
from app.core.llm import call_llm
from app.services.modules.interaction_module import interaction_module

SYSTEM_PROMPT = """你是直播电商弹幕分析专家。请对批量弹幕做语义分析，严格输出 JSON（不要输出任何其他文字或代码块标记）：
{
  "意图列表": [{"消息": "原文", "意图": ["提问|负面|购买意向|赞美|中性"], "优先级": 0-100整数}],
  "高频问题": [{"问题": "聚合约后的问题", "出现次数": 整数, "优先级": 0-100整数}],
  "情绪统计": {"提问": 整数, "负面": 整数, "购买意向": 整数, "赞美": 整数, "中性": 整数},
  "负面反馈": ["负面弹幕原文"],
  "关键洞察": "一句话总结当前直播间最需要注意的信号"
}

规则：
1. 优先级参考：购买意向90+、刷屏高频问题85+、负面85+、普通提问70、赞美40、中性50
2. 高频问题需将同义表达聚合为一条（如"油皮能用吗/大油田能用不"聚合成"油皮适用性"）
3. 情绪统计总数必须等于弹幕条数
4. 语义判断优先于字面关键词（如"大油田踩雷没"应识别为提问而非负面）"""

MAX_BATCH = 30  # 单次送 LLM 的最大弹幕条数


def _parse_llm_json(text: str) -> dict:
    """解析 LLM 返回的 JSON（容忍代码块围栏）"""
    text = text.strip()
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", text)
    if fence:
        text = fence.group(1).strip()
    return json.loads(text)


def _clamp(value, lo=0, hi=100) -> int:
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return 50


class LLMInteractionEngine:
    """LLM 驱动的互动理解引擎（带规则降级）"""

    def __init__(self, timeout: Optional[float] = None):
        self.timeout = timeout if timeout is not None else get_settings().llm_interaction_timeout

    async def analyze(self, messages: List[str], product_context: Optional[str] = None) -> dict:
        """分析弹幕：LLM 语义分析优先，超时/失败降级规则方案

        Returns:
            与 InteractionModule 输出兼容的分析结果，额外包含：
            - degraded: 是否为降级产出
            - degrade_reason: 降级原因（仅降级时）
            - 关键洞察: LLM 一句话总结（仅 LLM 成功时）
        """
        if not messages:
            return {"意图列表": [], "高频问题": [], "情绪统计": {}, "负面反馈": [], "degraded": False}

        try:
            result = await asyncio.wait_for(
                self._llm_analyze(messages, product_context), timeout=self.timeout
            )
            result["degraded"] = False
            return result
        except asyncio.TimeoutError:
            reason = f"LLM 分析超时（>{self.timeout}s）"
        except Exception as e:
            reason = f"LLM 分析失败: {type(e).__name__}: {e}"

        logger.warning(f"[互动理解] {reason}，降级为规则方案")
        fallback = interaction_module.analyze(messages)
        fallback["degraded"] = True
        fallback["degrade_reason"] = reason
        return fallback

    async def _llm_analyze(self, messages: List[str], product_context: Optional[str]) -> dict:
        """调用 LLM 做批量语义分析（阻塞调用放线程池）"""
        batch = [m.strip() for m in messages if m and m.strip()][:MAX_BATCH]
        context_line = f"\n当前讲解商品：{product_context}" if product_context else ""
        prompt = f"弹幕列表（共{len(batch)}条）：\n" + "\n".join(f"{i + 1}. {m}" for i, m in enumerate(batch)) + context_line

        raw = await asyncio.to_thread(call_llm, prompt, SYSTEM_PROMPT)
        result = _parse_llm_json(raw)

        # 结构规范化与兜底
        intents = result.get("意图列表", [])
        for item in intents:
            if isinstance(item.get("意图"), str):
                item["意图"] = [item["意图"]]
            item["优先级"] = _clamp(item.get("优先级", 50))
        questions = result.get("高频问题", [])
        for item in questions:
            item["出现次数"] = int(item.get("出现次数", 1))
            item["优先级"] = _clamp(item.get("优先级", 50))
        questions.sort(key=lambda x: x["优先级"], reverse=True)
        return {
            "意图列表": intents,
            "高频问题": questions[:10],
            "情绪统计": result.get("情绪统计", {}),
            "负面反馈": result.get("负面反馈", []),
            "关键洞察": result.get("关键洞察", ""),
        }


# 引擎实例
llm_interaction_engine = LLMInteractionEngine()
