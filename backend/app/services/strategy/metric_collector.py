"""
实时指标采集入口（SubTask 8.1）
- 手动注入（监场台/模拟源）：入库 LiveMetric → WS 推送 → 策略引擎滑动窗口
- 官方 API 拉取：占位（需平台资质审批后对接，默认禁用）
"""
from typing import Optional

from loguru import logger

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.gateway.models import MetricEvent
from app.services.live_session_service import LiveSessionService
from app.services.strategy.engine import strategy_engine
from app.services.ws_hub import ws_hub


class OfficialMetricPuller:
    """官方平台指标拉取占位

    人气/转化数据官方接口需平台资质审批（同弹幕官方适配器），资质获批后
    在各平台实现 _pull() 并启用 METRIC_API_PULL_ENABLED。未对接前启用会报错。
    """

    async def start_pull(self, session_id: int, interval: float = 30.0) -> None:
        settings = get_settings()
        if not settings.metric_api_pull_enabled:
            logger.info(f"[指标] 场次 {session_id} 官方API拉取未启用，等待手动注入/模拟源数据")
            return
        raise NotImplementedError(
            "官方指标API尚未对接（需平台资质审批与接口联调）。"
            "请通过监场台/模拟源手动注入指标。"
        )


class MetricCollector:
    """指标采集服务"""

    def __init__(self):
        self.api_puller = OfficialMetricPuller()

    async def ingest(self, session_id: int, events: list[MetricEvent]) -> list[dict]:
        """批量采集指标：入库 → WS 推送 → 策略引擎窗口；返回入库结果"""
        saved: list[dict] = []
        db = SessionLocal()
        try:
            service = LiveSessionService(db)
            for event in events:
                metric = service.add_metric(
                    session_id=session_id,
                    metric_type=event.metric_type,
                    value=event.value,
                    source=event.source,
                    recorded_at=event.recorded_at,
                )
                saved.append({
                    "id": metric.id,
                    "metric_type": metric.metric_type,
                    "value": metric.value,
                    "source": metric.source,
                    "recorded_at": metric.recorded_at.isoformat(),
                })
        finally:
            db.close()

        # WS 推送 + 策略引擎窗口（入库成功后进行，失败不阻断）
        adjustment = None
        for event in events:
            try:
                await ws_hub.push_metric(event)
            except Exception as e:
                logger.warning(f"[指标] WS 推送失败（场次 {session_id}）: {e}")
            try:
                adjustment = strategy_engine.on_metric(event) or adjustment
            except Exception as e:
                logger.error(f"[指标] 策略引擎评估失败（场次 {session_id}）: {e}")

        result = {"metrics": saved, "strategy_adjusted": adjustment is not None}
        if adjustment:
            result["strategy_adjustment"] = adjustment
        return result


# 进程级单例
metric_collector = MetricCollector()
