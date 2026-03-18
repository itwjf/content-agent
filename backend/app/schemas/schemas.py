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


class AgentOutput(BaseModel):
    """Agent 完整输出"""
    提词指令: PromptInstruction


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
