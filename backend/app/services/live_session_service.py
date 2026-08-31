"""
直播场次服务 - 场次生命周期管理与数据回放查询
"""
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.live_models import LiveSession, DanmakuMessage, DecisionRecord, LiveMetric
from app.schemas.schemas import LiveSessionCreate, LiveSessionUpdate


class LiveSessionService:
    """直播场次服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ---------- 场次生命周期 ----------

    def create_session(self, data: LiveSessionCreate) -> LiveSession:
        """创建场次（状态：待开播）"""
        session = LiveSession(
            title=data.title,
            platform=data.platform,
            status="pending",
            current_stage="预热期",
            script=data.script,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: int) -> Optional[LiveSession]:
        """获取单个场次"""
        return self.db.query(LiveSession).filter(LiveSession.id == session_id).first()

    def list_sessions(self, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[LiveSession]:
        """获取场次列表（可按状态过滤）"""
        query = self.db.query(LiveSession)
        if status:
            query = query.filter(LiveSession.status == status)
        return query.order_by(LiveSession.id.desc()).offset(skip).limit(limit).all()

    def start_session(self, session_id: int) -> Optional[LiveSession]:
        """开始直播（待开播 → 直播中）"""
        session = self.get_session(session_id)
        if not session:
            return None
        if session.status not in ("pending", "error"):
            raise ValueError(f"场次当前状态为 {session.status}，不能开始直播")
        session.status = "liveing"
        session.started_at = datetime.now()
        self.db.commit()
        self.db.refresh(session)
        return session

    def end_session(self, session_id: int) -> Optional[LiveSession]:
        """结束直播（直播中 → 已结束）"""
        session = self.get_session(session_id)
        if not session:
            return None
        if session.status != "liveing":
            raise ValueError(f"场次当前状态为 {session.status}，不能结束直播")
        session.status = "ended"
        session.ended_at = datetime.now()
        self.db.commit()
        self.db.refresh(session)
        return session

    def update_session(self, session_id: int, data: LiveSessionUpdate) -> Optional[LiveSession]:
        """更新场次信息（标题/平台/当前阶段/剧本）"""
        session = self.get_session(session_id)
        if not session:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(session, field, value)
        self.db.commit()
        self.db.refresh(session)
        return session

    # ---------- 数据写入（供后续网关/决策链路调用） ----------

    def add_danmaku(self, session_id: int, content: str, platform: Optional[str] = None,
                    user_id: Optional[str] = None, raw: Optional[dict] = None,
                    sent_at: Optional[datetime] = None) -> DanmakuMessage:
        """写入一条弹幕"""
        message = DanmakuMessage(
            session_id=session_id,
            platform=platform,
            user_id=user_id,
            content=content,
            raw=raw,
            sent_at=sent_at or datetime.now(),
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def add_decision(self, session_id: int, script: Optional[dict] = None,
                     trigger_reason: Optional[str] = None, priority: Optional[str] = None,
                     compliance_result: Optional[dict] = None, adopted: bool = False,
                     degraded: bool = False) -> DecisionRecord:
        """写入一条决策记录"""
        record = DecisionRecord(
            session_id=session_id,
            script=script,
            trigger_reason=trigger_reason,
            priority=priority,
            compliance_result=compliance_result,
            adopted=adopted,
            degraded=degraded,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def add_metric(self, session_id: int, metric_type: str, value: float,
                   source: str = "manual", recorded_at: Optional[datetime] = None) -> LiveMetric:
        """写入一条实时指标"""
        metric = LiveMetric(
            session_id=session_id,
            metric_type=metric_type,
            value=value,
            source=source,
            recorded_at=recorded_at or datetime.now(),
        )
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    # ---------- 回放查询 ----------

    def get_danmaku(self, session_id: int, start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None, skip: int = 0, limit: int = 500) -> List[DanmakuMessage]:
        """查询场次弹幕（回放）"""
        query = self.db.query(DanmakuMessage).filter(DanmakuMessage.session_id == session_id)
        if start_time:
            query = query.filter(DanmakuMessage.sent_at >= start_time)
        if end_time:
            query = query.filter(DanmakuMessage.sent_at <= end_time)
        return query.order_by(DanmakuMessage.sent_at.asc()).offset(skip).limit(limit).all()

    def get_decisions(self, session_id: int, skip: int = 0, limit: int = 500) -> List[DecisionRecord]:
        """查询场次决策历史（回放）"""
        return (
            self.db.query(DecisionRecord)
            .filter(DecisionRecord.session_id == session_id)
            .order_by(DecisionRecord.created_at.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_metrics(self, session_id: int, metric_type: Optional[str] = None,
                    start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
                    skip: int = 0, limit: int = 1000) -> List[LiveMetric]:
        """查询场次实时指标"""
        query = self.db.query(LiveMetric).filter(LiveMetric.session_id == session_id)
        if metric_type:
            query = query.filter(LiveMetric.metric_type == metric_type)
        if start_time:
            query = query.filter(LiveMetric.recorded_at >= start_time)
        if end_time:
            query = query.filter(LiveMetric.recorded_at <= end_time)
        return query.order_by(LiveMetric.recorded_at.asc()).offset(skip).limit(limit).all()
