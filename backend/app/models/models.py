"""
数据库模型
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Enum
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class LiveStage(str, enum.Enum):
    """直播阶段枚举"""
    PREheating = "预热期"           # 预热期
    PRODUCT_INTRO = "产品讲解期"     # 产品讲解期
    PROMOTION = "促单期"            # 促单期
    Q&A = "问答互动期"              # 问答互动期
    ENDING = "结尾期"               # 结尾期


class Product(Base):
    """商品模型"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku_id = Column(String(50), unique=True, index=True, nullable=False, comment="SKU ID")

    # 商品基本信息
    name = Column(String(200), nullable=False, comment="产品名称")
    category = Column(String(50), comment="商品分类")
    brand = Column(String(100), comment="品牌")
    spec = Column(String(100), comment="规格")
    price = Column(Float, nullable=False, comment="价格")
    original_price = Column(Float, comment="原价")

    # 商品属性
    ingredients = Column(JSON, comment="成分列表")
    effects = Column(JSON, comment="功效列表")
    description = Column(Text, comment="商品描述")
    selling_points = Column(JSON, comment="卖点列表")

    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Product {self.sku_id} - {self.name}>"


class ComplianceWord(Base):
    """合规违禁词模型"""
    __tablename__ = "compliance_words"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(100), unique=True, index=True, nullable=False, comment="违禁词")
    category = Column(String(50), comment="分类：敏感词/极限词/虚假宣传等")
    severity = Column(String(20), default="medium", comment="严重程度：low/medium/high")
    suggestion = Column(String(200), comment="替换建议")

    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<ComplianceWord {self.word}>"


class DecisionLog(Base):
    """决策日志模型"""
    __tablename__ = "decision_logs"

    id = Column(Integer, primary_key=True, index=True)

    # 输入数据（JSON 存储）
    input_data = Column(JSON, comment="输入数据")

    # 输出数据
    output_result = Column(JSON, comment="输出结果")

    # 决策信息
    priority = Column(String(20), comment="优先级")
    trigger_reason = Column(String(200), comment="触发原因")

    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<DecisionLog {self.id} - {self.trigger_reason}>"
