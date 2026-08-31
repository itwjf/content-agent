"""
直播场次域数据模型
包含：直播场次、弹幕消息、决策记录、实时指标
"""
from sqlalchemy import Column, Integer, BigInteger, String, Float, Text, DateTime, JSON, Boolean, Index
from sqlalchemy.sql import func
from app.core.database import Base


class LiveSession(Base):
    """直播场次模型"""
    __tablename__ = "live_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="场次标题")
    platform = Column(String(50), default="mock", comment="平台来源：douyin/taobao/kuaishou/mock")
    status = Column(String(20), default="pending", index=True,
                    comment="状态：pending待开播/liveing直播中/ended已结束/error异常")
    current_stage = Column(String(50), default="预热期", comment="当前直播阶段")
    script = Column(JSON, comment="导入的整场剧本（阶段规划+目标+话术要点）")
    started_at = Column(DateTime, comment="开始时间")
    ended_at = Column(DateTime, comment="结束时间")

    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<LiveSession(id={self.id}, title='{self.title}', status='{self.status}')>"


class DanmakuMessage(Base):
    """弹幕消息模型"""
    __tablename__ = "danmaku_messages"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, nullable=False, index=True, comment="所属场次ID")
    platform = Column(String(50), comment="来源平台")
    user_id = Column(String(64), comment="脱敏后的用户ID")
    content = Column(String(500), nullable=False, comment="弹幕内容")
    raw = Column(JSON, comment="原始消息数据")
    sent_at = Column(DateTime, nullable=False, comment="弹幕发送时间")

    created_at = Column(DateTime, server_default=func.now(), comment="入库时间")

    __table_args__ = (
        Index("idx_danmaku_session_time", "session_id", "sent_at"),
    )

    def __repr__(self):
        return f"<DanmakuMessage(id={self.id}, session_id={self.session_id}, content='{self.content[:20]}')>"


class DecisionRecord(Base):
    """决策记录模型"""
    __tablename__ = "decision_records"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, nullable=False, index=True, comment="所属场次ID")
    trigger_reason = Column(String(200), comment="触发原因")
    script = Column(JSON, comment="导演脚本（lines/emotion/action/pace/show_product_card等）")
    priority = Column(String(20), comment="优先级：高/中/低")
    compliance_result = Column(JSON, comment="合规检查结果")
    adopted = Column(Boolean, default=False, comment="是否被采纳")
    degraded = Column(Boolean, default=False, comment="是否为LLM降级产出")

    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    __table_args__ = (
        Index("idx_decision_session_time", "session_id", "created_at"),
    )

    def __repr__(self):
        return f"<DecisionRecord(id={self.id}, session_id={self.session_id}, trigger='{self.trigger_reason}')>"


class LiveMetric(Base):
    """实时指标模型"""
    __tablename__ = "live_metrics"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, nullable=False, index=True, comment="所属场次ID")
    metric_type = Column(String(50), nullable=False, comment="指标类型：popularity在线人数/danmaku_rate弹幕速率/like点赞/cart_click购物车点击/order下单")
    value = Column(Float, nullable=False, comment="指标值")
    source = Column(String(20), default="manual", comment="数据来源：api官方接口/manual手动注入/mock模拟")
    recorded_at = Column(DateTime, nullable=False, comment="指标记录时间")

    created_at = Column(DateTime, server_default=func.now(), comment="入库时间")

    __table_args__ = (
        Index("idx_metric_session_type_time", "session_id", "metric_type", "recorded_at"),
    )

    def __repr__(self):
        return f"<LiveMetric(id={self.id}, session_id={self.session_id}, type='{self.metric_type}', value={self.value})>"
