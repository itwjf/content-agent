"""
平台接入网关 - 统一消息模型与状态定义
所有弹幕来源（模拟/浏览器采集/官方API）归一化为统一事件协议
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DanmakuEvent(BaseModel):
    """统一弹幕事件（网关输出协议）"""
    session_id: int = Field(..., description="所属场次ID")
    platform: str = Field(..., description="来源平台：douyin/taobao/kuaishou/mock/browser")
    user_id: Optional[str] = Field(None, description="脱敏后的用户ID")
    content: str = Field(..., description="弹幕内容")
    sent_at: datetime = Field(default_factory=datetime.now, description="弹幕发送时间")
    raw: Optional[Dict[str, Any]] = Field(None, description="原始消息数据（各平台保留原始结构）")


class MetricEvent(BaseModel):
    """统一实时指标事件（网关输出协议）"""
    session_id: int = Field(..., description="所属场次ID")
    metric_type: str = Field(..., description="指标类型：popularity/danmaku_rate/like/cart_click/order")
    value: float = Field(..., description="指标值")
    source: str = Field("manual", description="数据来源：api/manual/mock")
    recorded_at: datetime = Field(default_factory=datetime.now, description="指标记录时间")


class AdapterStatusResponse(BaseModel):
    """适配器状态响应"""
    name: str = Field(..., description="适配器名称（唯一标识）")
    adapter_type: str = Field(..., description="适配器类型：mock/browser/official")
    description: str = Field("", description="适配器说明")
    enabled: bool = Field(False, description="是否启用（配置+运行时开关）")
    status: str = Field("stopped", description="运行状态：stopped/running/error/not_ready")
    error: Optional[str] = Field(None, description="最近一次错误信息")
    session_id: Optional[int] = Field(None, description="当前服务的场次ID")
    buffer_size: int = Field(0, description="当前缓冲区消息数")
