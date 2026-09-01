"""
实时指标采集与策略管理路由（Task 8）
挂载前缀：/api/v1/live
- POST /sessions/{id}/metrics                  指标注入（监场台/模拟源手动注入；官方API拉取为占位）
- GET  /sessions/{id}/strategy/weights          当前决策权重
- POST /sessions/{id}/strategy/reset            重置为默认权重
- GET  /sessions/{id}/strategy/adjustments      策略调整历史（原因+前后权重快照）
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.live_models import StrategyAdjustment
from app.services.gateway.models import MetricEvent
from app.services.live_session_service import LiveSessionService
from app.services.strategy.engine import strategy_engine
from app.services.strategy.metric_collector import metric_collector

router = APIRouter()

ALLOWED_METRIC_TYPES = {"popularity", "danmaku_rate", "like", "cart_click", "order"}


class MetricItem(BaseModel):
    """单条指标注入项"""
    metric_type: str = Field(..., description="指标类型：popularity/danmaku_rate/like/cart_click/order")
    value: float = Field(..., description="指标值")
    source: str = Field("manual", description="数据来源：api/manual/mock")
    recorded_at: Optional[datetime] = Field(None, description="指标时间（缺省用服务端时间）")


class MetricIngestRequest(BaseModel):
    """指标批量注入请求"""
    items: List[MetricItem] = Field(..., min_length=1, description="指标列表")


def _require_session(db: Session, session_id: int):
    service = LiveSessionService(db)
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="场次不存在")
    return session


@router.post("/sessions/{session_id}/metrics")
async def ingest_metrics(session_id: int, body: MetricIngestRequest, db: Session = Depends(get_db)):
    """手动注入实时指标（监场台/模拟源）→ 入库 + WS推送 + 策略引擎评估"""
    _require_session(db, session_id)
    bad = [item.metric_type for item in body.items if item.metric_type not in ALLOWED_METRIC_TYPES]
    if bad:
        raise HTTPException(status_code=400, detail=f"不支持的指标类型: {bad}，可选: {sorted(ALLOWED_METRIC_TYPES)}")

    events = [
        MetricEvent(
            session_id=session_id,
            metric_type=item.metric_type,
            value=item.value,
            source=item.source,
            recorded_at=item.recorded_at or datetime.now(),
        )
        for item in body.items
    ]
    return await metric_collector.ingest(session_id, events)


@router.get("/sessions/{session_id}/strategy/weights")
def get_strategy_weights(session_id: int, db: Session = Depends(get_db)):
    """查询当前场次决策权重（促单/安抚/答疑/推进）"""
    _require_session(db, session_id)
    return {"session_id": session_id, "weights": strategy_engine.get_weights(session_id)}


@router.post("/sessions/{session_id}/strategy/reset")
def reset_strategy_weights(session_id: int, db: Session = Depends(get_db)):
    """重置场次决策权重为默认值（人工干预）"""
    _require_session(db, session_id)
    return {"session_id": session_id, "weights": strategy_engine.reset(session_id)}


@router.get("/sessions/{session_id}/strategy/adjustments")
def list_strategy_adjustments(session_id: int, skip: int = 0, limit: int = 200,
                              db: Session = Depends(get_db)):
    """查询策略调整历史（可审计的优化轨迹）"""
    _require_session(db, session_id)
    rows = (
        db.query(StrategyAdjustment)
        .filter(StrategyAdjustment.session_id == session_id)
        .order_by(StrategyAdjustment.created_at.desc())
        .offset(skip)
        .limit(min(limit, 1000))
        .all()
    )
    return [
        {
            "id": row.id,
            "session_id": row.session_id,
            "rules_hit": row.rules_hit,
            "reason": row.reason,
            "weights_before": row.weights_before,
            "weights_after": row.weights_after,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]
