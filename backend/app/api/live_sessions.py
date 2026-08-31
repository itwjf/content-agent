"""
直播场次管理路由 - 场次生命周期与回放查询
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import (
    LiveSessionCreate,
    LiveSessionUpdate,
    LiveSessionResponse,
    DanmakuMessageResponse,
    DecisionRecordResponse,
    LiveMetricCreate,
    LiveMetricResponse,
)
from app.services.live_session_service import LiveSessionService

router = APIRouter()


@router.post("/sessions", response_model=LiveSessionResponse)
async def create_session(data: LiveSessionCreate, db: Session = Depends(get_db)):
    """创建直播场次（状态：待开播）"""
    service = LiveSessionService(db)
    return service.create_session(data)


@router.get("/sessions", response_model=List[LiveSessionResponse])
async def list_sessions(
    status: Optional[str] = Query(None, description="按状态过滤：pending/liveing/ended/error"),
    skip: int = 0,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    """获取场次列表"""
    service = LiveSessionService(db)
    return service.list_sessions(status=status, skip=skip, limit=limit)


@router.get("/sessions/{session_id}", response_model=LiveSessionResponse)
async def get_session(session_id: int, db: Session = Depends(get_db)):
    """获取场次详情"""
    service = LiveSessionService(db)
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="场次不存在")
    return session


@router.post("/sessions/{session_id}/start", response_model=LiveSessionResponse)
async def start_session(session_id: int, db: Session = Depends(get_db)):
    """开始直播（待开播 → 直播中）"""
    service = LiveSessionService(db)
    try:
        session = service.start_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not session:
        raise HTTPException(status_code=404, detail="场次不存在")
    return session


@router.post("/sessions/{session_id}/end", response_model=LiveSessionResponse)
async def end_session(session_id: int, db: Session = Depends(get_db)):
    """结束直播（直播中 → 已结束）"""
    service = LiveSessionService(db)
    try:
        session = service.end_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not session:
        raise HTTPException(status_code=404, detail="场次不存在")
    return session


@router.put("/sessions/{session_id}", response_model=LiveSessionResponse)
async def update_session(session_id: int, data: LiveSessionUpdate, db: Session = Depends(get_db)):
    """更新场次信息（标题/平台/当前阶段/剧本）"""
    service = LiveSessionService(db)
    session = service.update_session(session_id, data)
    if not session:
        raise HTTPException(status_code=404, detail="场次不存在")
    return session


# ---------- 回放查询 ----------

@router.get("/sessions/{session_id}/replay/danmaku", response_model=List[DanmakuMessageResponse])
async def get_danmaku_replay(
    session_id: int,
    start_time: Optional[datetime] = Query(None, description="起始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    skip: int = 0,
    limit: int = Query(500, le=2000),
    db: Session = Depends(get_db),
):
    """查询场次弹幕回放"""
    service = LiveSessionService(db)
    if not service.get_session(session_id):
        raise HTTPException(status_code=404, detail="场次不存在")
    return service.get_danmaku(session_id, start_time=start_time, end_time=end_time, skip=skip, limit=limit)


@router.get("/sessions/{session_id}/replay/decisions", response_model=List[DecisionRecordResponse])
async def get_decision_replay(
    session_id: int,
    skip: int = 0,
    limit: int = Query(500, le=2000),
    db: Session = Depends(get_db),
):
    """查询场次决策历史回放"""
    service = LiveSessionService(db)
    if not service.get_session(session_id):
        raise HTTPException(status_code=404, detail="场次不存在")
    return service.get_decisions(session_id, skip=skip, limit=limit)


@router.get("/sessions/{session_id}/metrics", response_model=List[LiveMetricResponse])
async def get_session_metrics(
    session_id: int,
    metric_type: Optional[str] = Query(None, description="指标类型：popularity/danmaku_rate/like/cart_click/order"),
    start_time: Optional[datetime] = Query(None, description="起始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    skip: int = 0,
    limit: int = Query(1000, le=5000),
    db: Session = Depends(get_db),
):
    """查询场次实时指标"""
    service = LiveSessionService(db)
    if not service.get_session(session_id):
        raise HTTPException(status_code=404, detail="场次不存在")
    return service.get_metrics(
        session_id, metric_type=metric_type, start_time=start_time, end_time=end_time, skip=skip, limit=limit
    )
