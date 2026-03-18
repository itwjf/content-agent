"""
核心配置模块
"""
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # LLM 配置
    llm_api_key: str
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"

    # SiliconFlow Embedding API 配置
    siliconflow_api_key: Optional[str] = None

    # MySQL 配置
    mysql_root_password: str = "your_mysql_root_password_here"
    mysql_database: str = "your_mysql_database_here"
    mysql_user: str = "your_mysql_username_here"
    mysql_password: str = "your_mysql_password_here"
    
    # 数据库配置
    database_url: str = "mysql+pymysql://content_agent:content123@mysql:3306/content_agent"

    # Qdrant 配置
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # 服务配置
    debug: bool = True
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
