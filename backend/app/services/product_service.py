"""
商品服务 - MySQL版本
用于替换内存存储，实现数据持久化
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
from app.models.product_models import Product
from app.schemas.schemas import ProductCreate, ProductResponse


class ProductService:
    """商品服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_product(self, product_data: ProductCreate) -> Product:
        """创建商品"""
        # 检查SKU是否已存在
        existing = self.db.query(Product).filter(Product.sku_id == product_data.sku_id).first()
        if existing:
            raise ValueError(f"商品SKU {product_data.sku_id} 已存在")
        
        # 创建商品
        db_product = Product(
            sku_id=product_data.sku_id,
            name=product_data.name,
            category=product_data.category,
            brand=product_data.brand,
            spec=product_data.spec,
            price=product_data.price,
            original_price=product_data.original_price,
            ingredients=product_data.ingredients,
            effects=product_data.effects,
            description=product_data.description,
            selling_points=product_data.selling_points
        )
        
        self.db.add(db_product)
        self.db.commit()
        self.db.refresh(db_product)
        return db_product
    
    def get_product(self, sku_id: str) -> Optional[Product]:
        """获取单个商品"""
        return self.db.query(Product).filter(Product.sku_id == sku_id).first()
    
    def get_products(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """获取商品列表"""
        return self.db.query(Product).offset(skip).limit(limit).all()
    
    def update_product(self, sku_id: str, product_data: ProductCreate) -> Optional[Product]:
        """更新商品"""
        db_product = self.get_product(sku_id)
        if not db_product:
            return None
        
        # 更新字段
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_product, field, value)
        
        self.db.commit()
        self.db.refresh(db_product)
        return db_product
    
    def delete_product(self, sku_id: str) -> bool:
        """删除商品"""
        db_product = self.get_product(sku_id)
        if not db_product:
            return False
        
        self.db.delete(db_product)
        self.db.commit()
        return True
    
    def init_sample_data(self):
        """初始化示例数据"""
        sample_products = [
            {
                "sku_id": "12345",
                "name": "控油修护精华液",
                "category": "护肤品",
                "brand": "品牌A",
                "spec": "30ml",
                "price": 350,
                "original_price": 499,
                "ingredients": ["水杨酸", "烟酰胺", "透明质酸"],
                "effects": ["控油", "修护", "保湿"],
                "description": "专为油皮设计的控油修护精华，温和不刺激",
                "selling_points": ["油皮亲妈", "持久控油", "温和不刺激"]
            },
            {
                "sku_id": "67890",
                "name": "氨基酸洁面乳",
                "category": "护肤品",
                "brand": "品牌A",
                "spec": "100ml",
                "price": 129,
                "original_price": 199,
                "ingredients": ["氨基酸", "神经酰胺", "甘草酸二钾"],
                "effects": ["温和清洁", "补水", "舒缓"],
                "description": "氨基酸温和洁面，敏感肌可用",
                "selling_points": ["温和不刺激", "敏感肌适用", "泡沫丰富"]
            },
            {
                "sku_id": "11111",
                "name": "美白淡斑精华液",
                "category": "护肤品",
                "brand": "品牌B",
                "spec": "50ml",
                "price": 299,
                "original_price": 399,
                "ingredients": ["维生素C", "烟酰胺", "熊果苷"],
                "effects": ["美白", "淡斑", "提亮"],
                "description": "高浓度VC美白精华，28天提亮肤色",
                "selling_points": ["28天见效", "高浓度VC", "淡化色斑"]
            }
        ]
        
        for product_data in sample_products:
            try:
                self.create_product(ProductCreate(**product_data))
            except ValueError:
                # SKU已存在，跳过
                continue


# 创建服务实例的函数
def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)