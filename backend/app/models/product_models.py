"""
商品数据模型 - MySQL版本
用于替换内存存储，实现数据持久化
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Product(Base):
    """商品模型"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sku_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(100))
    brand = Column(String(100))
    spec = Column(String(100))
    price = Column(Float, nullable=False)
    original_price = Column(Float)
    ingredients = Column(JSON)  # 成分列表
    effects = Column(JSON)      # 功效列表
    description = Column(Text)
    selling_points = Column(JSON)  # 卖点列表
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Product(sku_id='{self.sku_id}', name='{self.name}')>"