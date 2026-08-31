"""
Pydantic 数据模型 - 用于 API 请求/响应验证
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== 直播相关模型 ====================

class LiveStatus(BaseModel):
    """直播状态"""
    当前阶段: str = Field(..., description="当前直播阶段")
    已直播时长: int = Field(..., description="已直播时长（秒）")
    计划总时长: int = Field(..., description="计划总时长（秒）")
    当前产品: Optional[str] = Field(None, description="当前产品 SKU_ID")


class EmotionAnalysis(BaseModel):
    """情绪分析结果"""
    高频词: Dict[str, int] = Field(default_factory=dict, description="高频词及出现次数")
    负面反馈: List[str] = Field(default_factory=list, description="负面反馈列表")


class DanmuData(BaseModel):
    """弹幕数据"""
    最近30秒消息: List[str] = Field(default_factory=list, description="最近30秒的弹幕消息")
    情绪分析: EmotionAnalysis = Field(default_factory=EmotionAnalysis, description="情绪分析结果")


class ProductData(BaseModel):
    """商品数据"""
    sku_id: str = Field(..., description="商品 SKU ID")
    产品名称: str = Field(..., description="产品名称")
    规格: Optional[str] = Field(None, description="规格")
    价格: float = Field(..., description="价格")
    成分: List[str] = Field(default_factory=list, description="成分列表")
    功效: List[str] = Field(default_factory=list, description="功效列表")


class BackendData(BaseModel):
    """后台数据"""
    在线人数: int = Field(0, description="当前在线人数")
    购物车点击率: Optional[str] = Field(None, description="购物车点击率变化")
    转化率: Optional[str] = Field(None, description="转化率")


class AgentInput(BaseModel):
    """Agent 完整输入"""
    直播状态: LiveStatus
    弹幕数据: DanmuData
    商品数据: ProductData
    后台数据: BackendData


# ==================== 输出相关模型 ====================

class PromptInstruction(BaseModel):
    """提词指令"""
    优先级: str = Field(..., description="优先级：高/中/低")
    建议话术: str = Field(..., description="建议话术")
    动作建议: Optional[str] = Field(None, description="动作建议")
    触发原因: str = Field(..., description="触发原因")
    合规检查: str = Field(..., description="合规检查结果")


class LiveStructure(BaseModel):
    """直播结构信息"""
    当前阶段: str
    阶段描述: str
    下一阶段: Optional[str] = None
    阶段提示: List[str] = Field(default_factory=list)
    下一阶段准备: List[str] = Field(default_factory=list)
    阶段切换建议: Optional[Dict[str, str]] = None


class AgentOutput(BaseModel):
    """Agent 完整输出"""
    提词指令: PromptInstruction
    直播结构: LiveStructure


# ==================== 商品相关模型 ====================

class ProductCreate(BaseModel):
    """商品创建请求"""
    sku_id: str
    name: str
    category: Optional[str] = None
    brand: Optional[str] = None
    spec: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    ingredients: List[str] = Field(default_factory=list)
    effects: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    selling_points: List[str] = Field(default_factory=list)


class ProductResponse(BaseModel):
    """商品响应"""
    id: int
    sku_id: str
    name: str
    category: Optional[str]
    brand: Optional[str]
    spec: Optional[str]
    price: float
    original_price: Optional[float]
    ingredients: List[str]
    effects: List[str]
    description: Optional[str]
    selling_points: List[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 合规检查模型 ====================

class ComplianceCheckRequest(BaseModel):
    """合规检查请求"""
    text: str = Field(..., description="待检查的文本")


class ComplianceCheckResponse(BaseModel):
    """合规检查响应"""
    passed: bool = Field(..., description="是否通过")
    violations: List[str] = Field(default_factory=list, description="违规词列表")
    suggestion: Optional[str] = Field(None, description="修改建议")


# ==================== 直播场次相关模型 ====================

class LiveSessionCreate(BaseModel):
    """场次创建请求"""
    title: str = Field(..., description="场次标题")
    platform: str = Field("mock", description="平台来源：douyin/taobao/kuaishou/mock")
    script: Optional[Dict[str, Any]] = Field(None, description="整场剧本（阶段规划+目标+话术要点）")


class LiveSessionUpdate(BaseModel):
    """场次更新请求"""
    title: Optional[str] = None
    platform: Optional[str] = None
    current_stage: Optional[str] = None
    script: Optional[Dict[str, Any]] = None


class LiveSessionResponse(BaseModel):
    """场次响应"""
    id: int
    title: str
    platform: str
    status: str
    current_stage: str
    script: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DanmakuMessageResponse(BaseModel):
    """弹幕消息响应"""
    id: int
    session_id: int
    platform: Optional[str] = None
    user_id: Optional[str] = None
    content: str
    raw: Optional[Dict[str, Any]] = None
    sent_at: datetime
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DecisionRecordResponse(BaseModel):
    """决策记录响应"""
    id: int
    session_id: int
    trigger_reason: Optional[str] = None
    script: Optional[Dict[str, Any]] = None
    priority: Optional[str] = None
    compliance_result: Optional[Dict[str, Any]] = None
    adopted: bool = False
    degraded: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LiveMetricCreate(BaseModel):
    """指标注入请求"""
    metric_type: str = Field(..., description="指标类型：popularity/danmaku_rate/like/cart_click/order")
    value: float = Field(..., description="指标值")
    source: str = Field("manual", description="数据来源：api/manual/mock")
    recorded_at: Optional[datetime] = Field(None, description="指标记录时间，不传则为当前时间")


class LiveMetricResponse(BaseModel):
    """指标响应"""
    id: int
    session_id: int
    metric_type: str
    value: float
    source: str
    recorded_at: datetime
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
