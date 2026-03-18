"""
MySQL版本的主应用入口
用于替换内存存储，实现数据持久化
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.core.config import get_settings
from app.api.v1 import router as api_v1_router
from app.api.v1.products_mysql_router import router as mysql_products_router
from app.services.database_init import init_database

settings = get_settings()

# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# 创建 FastAPI 应用
app = FastAPI(
    title="ContentAgent API (MySQL版)",
    description="智能直播辅助 Agent 系统 API - 使用MySQL数据库",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_v1_router, prefix="/api/v1", tags=["Agent"])
app.include_router(mysql_products_router, prefix="/api/v1", tags=["商品管理(MySQL)"])


@app.get("/")
async def root():
    """根路径"""
    return {"message": "ContentAgent API (MySQL版)", "version": "2.0.0"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "version": "2.0.0", "database": "MySQL"}


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("ContentAgent API (MySQL版) 启动中...")
    
    # 初始化数据库
    try:
        init_database()
        logger.info("✅ 数据库初始化完成")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        # 不阻止应用启动，因为可能是数据库连接问题


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("ContentAgent API (MySQL版) 关闭中...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main_mysql:app", host="0.0.0.0", port=8000, reload=False)