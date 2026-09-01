"""
决策调度器
按场次维护弹幕滑动窗口：窗口到期 → LLM互动理解 → 导演引擎产出脚本 → 合规检查 → 决策落库 → WebSocket 推送
"""
import asyncio
from collections import defaultdict
from typing import Optional

from loguru import logger

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.agent.llm_interaction_engine import llm_interaction_engine
from app.services.director.engine import director_engine
from app.services.gateway.models import DanmakuEvent
from app.services.live_session_service import LiveSessionService
from app.services.modules.compliance_module import compliance_module
from app.services.modules.structure_engine import structure_engine
from app.services.showcase.service import showcase_service
from app.services.strategy.engine import strategy_engine
from app.services.ws_hub import ws_hub

MAX_BUFFER = 100  # 单场次窗口缓冲上限


class DecisionScheduler:
    """场次级决策调度器（进程内单例）"""

    def __init__(self):
        self.window = get_settings().decision_window_seconds
        self._buffers: dict[int, list[DanmakuEvent]] = defaultdict(list)
        self._loops: dict[int, asyncio.Task] = {}
        self._options: dict[int, dict] = {}
        self._paused: set[int] = set()  # 人工接管：暂停自动决策（弹幕仍缓冲）

    # ---------- 生命周期 ----------

    def start(self, session_id: int, options: Optional[dict] = None) -> None:
        """启动场次决策循环"""
        if session_id in self._loops:
            return
        self._options[session_id] = options or {}
        self._loops[session_id] = asyncio.create_task(self._loop(session_id))
        logger.info(f"[决策] 场次 {session_id} 决策循环已启动（窗口={self.window}s）")

    async def stop(self, session_id: int) -> None:
        """停止场次决策循环"""
        task = self._loops.pop(session_id, None)
        self._buffers.pop(session_id, None)
        self._options.pop(session_id, None)
        if task:
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
            logger.info(f"[决策] 场次 {session_id} 决策循环已停止")

    def is_running(self, session_id: int) -> bool:
        return session_id in self._loops

    # ---------- 人工接管 ----------

    def pause(self, session_id: int) -> bool:
        """人工接管：暂停自动决策（弹幕仍进缓冲，恢复后一并消费）"""
        if session_id not in self._loops:
            return False
        self._paused.add(session_id)
        logger.info(f"[决策] 场次 {session_id} 自动决策已暂停（人工接管）")
        return True

    def resume(self, session_id: int) -> bool:
        """恢复自动决策"""
        if session_id not in self._loops:
            return False
        self._paused.discard(session_id)
        logger.info(f"[决策] 场次 {session_id} 自动决策已恢复")
        return True

    def is_paused(self, session_id: int) -> bool:
        return session_id in self._paused

    def control_status(self, session_id: int) -> str:
        """自动决策状态：running / paused / stopped"""
        if session_id not in self._loops:
            return "stopped"
        return "paused" if session_id in self._paused else "running"

    # ---------- 事件入口 ----------

    def feed(self, event: DanmakuEvent) -> None:
        """网关弹幕钩子：写入场次窗口缓冲"""
        if event.session_id in self._loops:
            buffer = self._buffers[event.session_id]
            if len(buffer) < MAX_BUFFER:
                buffer.append(event)

    # ---------- 决策主流程 ----------

    async def _loop(self, session_id: int) -> None:
        while True:
            await asyncio.sleep(self.window)
            if session_id in self._paused:
                continue  # 人工接管中：跳过自动决策
            try:
                await self.decide_now(session_id)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"[决策] 场次 {session_id} 决策循环异常: {e}")

    async def decide_now(self, session_id: int) -> Optional[dict]:
        """立即执行一轮决策（窗口到期自动触发 / API 手动触发）"""
        events = self._buffers.get(session_id, [])
        if not events:
            return None
        messages = [e.content for e in events]
        self._buffers[session_id] = []  # 清空已消费

        db = SessionLocal()
        try:
            service = LiveSessionService(db)
            session = service.get_session(session_id)
            if not session or session.status != "liveing":
                logger.warning(f"[决策] 场次 {session_id} 不在直播中，跳过")
                return None

            product = self._resolve_product(db, session_id)
            product_name = (product or {}).get("产品名称", "")
            stage = session.current_stage
            script_stages = (session.script or {}).get("stages") if isinstance(session.script, dict) else None

            # 1. LLM 互动理解（内含规则降级）
            interaction = await llm_interaction_engine.analyze(messages, product_context=product_name)
            interaction["_messages"] = messages  # 供导演引擎引用弹幕原文

            # 1.5 策略引擎：累计本轮互动反馈（负面/提问/购买意向）并评估调权，命中规则会落库+WS推送
            emotion_stats = interaction.get("情绪统计") or {}
            strategy_engine.feedback(
                session_id,
                total=len(messages),
                negative=len(interaction.get("负面反馈", [])),
                questions=len(interaction.get("高频问题", [])),
                buy_intent=int(emotion_stats.get("购买意向", 0) or 0),
            )
            strategy_weights = strategy_engine.get_weights(session_id)

            # 2. 导演引擎产出脚本（内含规则降级；融合剧本、商品与策略权重）
            script = await director_engine.produce(
                session_id=session_id,
                stage=stage,
                product_data=product,
                interaction_result=interaction,
                script_stages=script_stages,
                strategy_weights=strategy_weights,
            )

            # 3. 合规检查与修正（违禁词自动替换为建议词，结果随决策落库；TTS 前还有硬闸门）
            compliance = self._apply_compliance(script)
            script.compliance = compliance

            # 4. 决策记录落库
            record = service.add_decision(
                session_id=session_id,
                script=script.to_persist_dict(),
                trigger_reason=script.trigger_reason,
                priority=script.priority,
                compliance_result=compliance,
                degraded=script.degraded,
            )
        finally:
            db.close()

        # 5. WebSocket 实时推送
        await ws_hub.push_decision(session_id, {
            **script.to_persist_dict(),
            "record_id": record.id,
        })

        # 6. 展示适配：合规硬闸门 → TTS → 字幕/动作包 →（可选）数字人形象
        try:
            package = await showcase_service.present(script)
            await ws_hub._push(session_id, "presentation", package)
            if package["mode"] == "blocked" or package["compliance_gate"]["blocked_lines"]:
                await ws_hub.push_alert(session_id, {
                    "level": "warning",
                    "kind": "compliance",
                    "message": "部分台词被合规闸门拦截，未进入播出环节",
                    "detail": package["compliance_gate"],
                })
        except Exception as e:
            logger.error(f"[决策] 场次 {session_id} 展示适配失败（不影响决策链路）: {e}")

        logger.info(f"[决策] 场次 {session_id} 产出决策 #{record.id}（{script.source}，{script.priority}优先级）")
        return script.to_persist_dict()

    # ---------- 内部工具 ----------

    def _resolve_product(self, db, session_id: int) -> Optional[dict]:
        """解析当前商品：优先场次绑定(options.product_sku)，否则取商品库第一个（演示兜底）"""
        from app.services.product_service import ProductService

        product_service = ProductService(db)
        product = None
        sku = self._options.get(session_id, {}).get("product_sku")
        if sku:
            product = product_service.get_product(sku)
        if not product:
            products = product_service.get_products(limit=1)
            product = products[0] if products else None
        if not product:
            return None
        return {
            "sku_id": product.sku_id,
            "产品名称": product.name,
            "规格": product.spec,
            "价格": product.price,
            "成分": product.ingredients or [],
            "功效": product.effects or [],
        }

    @staticmethod
    def _apply_compliance(script) -> dict:
        """对每句台词做合规检查；不通过时用建议词自动替换原文"""
        violations = []
        corrected = False
        for i, line in enumerate(script.lines):
            result = compliance_module.check(line.text)
            if not result["passed"]:
                violations.extend(result["violations"])
                line.text = result["suggestion"]  # 违禁词替换为建议词
                corrected = True
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "corrected": corrected,
            "note": "违禁词已按建议词替换" if corrected else "合规通过",
        }


# 进程级单例
decision_scheduler = DecisionScheduler()
