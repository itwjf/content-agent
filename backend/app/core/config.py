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

    # 平台接入网关配置
    gateway_mock_interval: float = 2.0          # 模拟源默认出弹幕间隔（秒）
    douyin_api_enabled: bool = False            # 抖音官方API（需资质，默认禁用）
    taobao_api_enabled: bool = False            # 淘宝官方API（需资质，默认禁用）
    kuaishou_api_enabled: bool = False          # 快手官方API（需资质，默认禁用）
    browser_adapter_enabled: bool = False       # 浏览器采集适配器（Task 7 实现）
    browser_collect_token: str = ""             # 浏览器采集回传令牌（为空则不校验，仅建议内网/本机使用）

    # 决策中枢配置
    llm_interaction_timeout: float = 3.0        # LLM 互动理解超时（秒），超时降级规则方案
    decision_window_seconds: float = 10.0       # 决策滑动窗口（秒）
    decision_llm_timeout: float = 5.0           # 导演脚本 LLM 超时（秒），超时降级规则模板

    # 实时指标与策略引擎配置
    strategy_window_seconds: float = 60.0       # 滑动窗口长度（秒）
    strategy_eval_interval: float = 10.0        # 策略评估最小间隔（秒），防抖动
    strategy_popularity_rise: float = 0.2       # 人气上涨阈值（窗口内相对涨幅）
    strategy_popularity_drop: float = 0.15      # 人气下跌阈值（窗口内相对跌幅）
    strategy_negative_ratio: float = 0.3        # 负面弹幕占比阈值
    strategy_danmaku_rate_high: float = 15.0    # 高频弹幕阈值（条/分钟）
    strategy_conversion_high: float = 10.0      # 窗口内转化事件（购物车点击+下单）阈值
    metric_api_pull_enabled: bool = False       # 官方API指标拉取（需平台资质，默认禁用）

    # 展示适配层配置（TTS）
    tts_provider: str = "mock"                  # TTS 提供方：mock/cosyvoice/http
    tts_cosyvoice_base_url: Optional[str] = None    # 本地 CosyVoice HTTP 服务地址
    tts_http_base_url: Optional[str] = None         # 商用 TTS API 地址
    tts_http_api_key: Optional[str] = None          # 商用 TTS API 密钥（不落代码）
    tts_voice: str = "default"                      # 音色
    tts_output_dir: str = "./tts_output"            # 音频文件输出目录

    # 展示适配层配置（2D 数字人形象驱动）
    avatar_enabled: bool = False                    # 是否启用形象驱动（需 GPU 推理服务）
    avatar_service_url: Optional[str] = None        # MuseTalk/LivePortrait 推理服务地址
    avatar_base_video_id: str = "default"           # 底版素材ID（真人录制/照片/AI生成，3~5套轮换）
    avatar_ai_label: bool = True                    # 是否叠加"AI 生成内容"标识（平台报备要求）

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
