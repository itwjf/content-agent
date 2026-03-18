"""
数据库初始化脚本
用于创建表结构和初始化数据
"""
from sqlalchemy import create_engine
from app.core.config import get_settings
from app.core.database import Base
from app.models.product_models import Product
from app.schemas.schemas import ProductCreate
from app.services.product_service import ProductService
from sqlalchemy.orm import sessionmaker

settings = get_settings()

def init_database():
    """初始化数据库"""
    print("开始初始化数据库...")
    
    # 创建数据库引擎
    engine = create_engine(settings.database_url)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")
    
    # 创建会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 初始化商品服务
        product_service = ProductService(db)
        
        # 检查是否已有数据
        existing_count = db.query(Product).count()
        if existing_count > 0:
            print(f"数据库中已有 {existing_count} 条商品数据，跳过初始化")
            return
        
        # 初始化示例数据
        print("开始初始化示例商品数据...")
        product_service.init_sample_data()
        print("✅ 示例商品数据初始化完成")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database()