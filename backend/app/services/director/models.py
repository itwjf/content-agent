"""
导演脚本数据模型
面向数字人的结构化输出：台词 + 情绪 + 动作 + 节奏 + 商品卡指令
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# 合法取值
EMOTIONS = {"neutral", "enthusiastic", "warm", "urgent", "serious"}
PACES = {"slow", "normal", "fast"}
PRIORITIES = {"高", "中", "低"}


class DirectorLine(BaseModel):
    """单句台词（含表演指令）"""
    text: str = Field(..., description="台词内容")
    emotion: str = Field("neutral", description="情绪：neutral平静/enthusiastic热情/warm亲切/urgent紧迫/serious认真")
    action: str = Field("", description="动作建议（映射为画面层操作：如'展示成分表'/'切商品特写'）")
    pace: str = Field("normal", description="语速：slow/normal/fast")


class DirectorScript(BaseModel):
    """导演脚本：决策中枢的最终输出，驱动 TTS/数字人与监场台"""
    session_id: int = Field(..., description="场次ID")
    stage: str = Field(..., description="产出时的直播阶段")
    lines: List[DirectorLine] = Field(default_factory=list, description="台词列表（1~3句）")
    show_product_card: bool = Field(False, description="是否弹出商品卡")
    product_sku: Optional[str] = Field(None, description="当前讲解商品SKU")
    priority: str = Field("中", description="优先级：高/中/低")
    trigger_reason: str = Field("", description="触发原因")
    source: str = Field("llm", description="产出方式：llm/rule（降级）")
    degraded: bool = Field(False, description="是否为降级产出")
    compliance: dict = Field(default_factory=dict, description="合规检查结果：{passed, violations, suggestion}")
    created_at: datetime = Field(default_factory=datetime.now, description="产出时间")

    def to_persist_dict(self) -> dict:
        """转换为 DecisionRecord.script 存储结构"""
        return self.model_dump(mode="json")
