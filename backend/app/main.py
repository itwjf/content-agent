"""
FastAPI 主应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.core.config import get_settings
from app.api.v1 import router as api_v1_router

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
    title="ContentAgent API",
    description="智能直播辅助 Agent 系统 API",
    version="1.0.0",
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


@app.get("/")
async def root():
    """根路径"""
    return {"message": "ContentAgent API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "version": "1.0.0"}


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("ContentAgent API 启动中...")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("ContentAgent API 关闭中...")
