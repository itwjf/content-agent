"""
2D 数字人形象驱动适配器
- 预期服务形态：本地/云 GPU 部署 MuseTalk / LivePortrait 推理服务
- 接口约定：POST {avatar_service_url}/render
    请求体：{audio_path|audio_url, base_video_id, emotion}
    响应：{"video_url": "..."}
- 未启用或服务不可用时返回 None，由展示服务降级为"TTS + 字幕"纯声音形态
"""
from typing import Optional

import httpx
from loguru import logger

from app.core.config import get_settings


class AvatarResult:
    def __init__(self, video_url: str, mode: str = "avatar"):
        self.video_url = video_url
        self.mode = mode  # avatar / audio_subtitle


class BaseAvatarAdapter:
    name: str = "base"

    def render(self, audio_url: str, emotion: str = "neutral", base_video_id: Optional[str] = None) -> Optional[AvatarResult]:
        raise NotImplementedError


class MuseTalkAdapter(BaseAvatarAdapter):
    """MuseTalk/LivePortrait 推理服务适配器（可配置端点）"""
    name = "musetalk"

    def render(self, audio_url: str, emotion: str = "neutral", base_video_id: Optional[str] = None) -> Optional[AvatarResult]:
        settings = get_settings()
        if not settings.avatar_enabled or not settings.avatar_service_url:
            return None
        try:
            resp = httpx.post(
                f"{settings.avatar_service_url.rstrip('/')}/render",
                json={
                    "audio_url": audio_url,
                    "base_video_id": base_video_id or settings.avatar_base_video_id,
                    "emotion": emotion,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            video_url = data.get("video_url")
            if not video_url:
                raise ValueError("响应缺少 video_url")
            return AvatarResult(video_url, "avatar")
        except Exception as e:
            logger.warning(f"[形象驱动] 渲染失败，降级为音频+字幕形态: {e}")
            return None


def get_avatar_adapter() -> BaseAvatarAdapter:
    return MuseTalkAdapter()
