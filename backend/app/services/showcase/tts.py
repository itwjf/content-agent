"""
TTS 语音合成适配器
- mock: 静音占位音频（无任何外部依赖，保证链路可演示）
- cosyvoice: 本地部署的 CosyVoice HTTP 服务（FunAudioLLM/CosyVoice api 部署形态）
- http: 通用商用 TTS HTTP API（火山引擎/硅基等，可配置端点与密钥）
统一输出 TTSResult（音频文件 URL + 时长估算）
"""
import math
import struct
import wave
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional

import httpx
from loguru import logger

from app.core.config import get_settings


class TTSError(RuntimeError):
    """TTS 合成失败"""


class TTSResult:
    def __init__(self, audio_url: str, duration_ms: int, provider: str):
        self.audio_url = audio_url          # 可播放的音频 URL（/api/v1/showcase/audio/xxx.wav）
        self.duration_ms = duration_ms      # 音频时长（估算，用于字幕时间轴）
        self.provider = provider


def _estimate_ms(text: str, pace: str = "normal") -> int:
    """按中文语速估算时长：正常约 4字/秒"""
    rate = {"slow": 2.8, "normal": 4.0, "fast": 5.2}.get(pace, 4.0)
    return max(800, min(30000, int(len(text) / rate * 1000)))


class BaseTTSAdapter(ABC):
    name: str = "base"

    @abstractmethod
    def synthesize(self, text: str, emotion: str = "neutral", pace: str = "normal") -> TTSResult:
        raise NotImplementedError


class MockTTSAdapter(BaseTTSAdapter):
    """静音占位音频：零依赖，保证无 API Key/GPU 时全链路可演示"""
    name = "mock"

    def synthesize(self, text: str, emotion: str = "neutral", pace: str = "normal") -> TTSResult:
        settings = get_settings()
        out_dir = Path(settings.tts_output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        duration_ms = _estimate_ms(text, pace)
        sample_rate = 16000
        filename = f"mock_{abs(hash(text)) % 10**10}.wav"
        filepath = out_dir / filename

        # 生成静音 WAV（标准库，无第三方依赖）
        num_frames = int(sample_rate * duration_ms / 1000)
        with wave.open(str(filepath), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            silent_frame = struct.pack("<h", 0)
            wf.writeframes(silent_frame * num_frames)

        return TTSResult(f"/api/v1/showcase/audio/{filename}", duration_ms, "mock")


class CosyVoiceTTSAdapter(BaseTTSAdapter):
    """本地部署 CosyVoice HTTP 服务适配器

    预期服务：POST {base_url}  请求体 {text, voice, speed}
    返回：音频二进制（wav/mp3）
    """
    name = "cosyvoice"

    def synthesize(self, text: str, emotion: str = "neutral", pace: str = "normal") -> TTSResult:
        settings = get_settings()
        if not settings.tts_cosyvoice_base_url:
            raise TTSError("未配置 TTS_COSYVOICE_BASE_URL")
        speed = {"slow": 0.85, "normal": 1.0, "fast": 1.2}.get(pace, 1.0)
        try:
            resp = httpx.post(
                settings.tts_cosyvoice_base_url,
                json={"text": text, "voice": settings.tts_voice, "speed": speed, "emotion": emotion},
                timeout=15.0,
            )
            resp.raise_for_status()
        except Exception as e:
            raise TTSError(f"CosyVoice 合成失败: {e}")

        out_dir = Path(settings.tts_output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"cv_{abs(hash(text)) % 10**10}.wav"
        (out_dir / filename).write_bytes(resp.content)
        return TTSResult(f"/api/v1/showcase/audio/{filename}", _estimate_ms(text, pace), "cosyvoice")


class HttpTTSAdapter(BaseTTSAdapter):
    """通用商用 TTS HTTP API 适配器（火山引擎/硅基等）

    预期：POST {base_url}，Header 携带 Authorization: Bearer {api_key}
    请求体 {text, voice, speed}，返回音频二进制或 {"audio": "base64或url"}
    """
    name = "http"

    def synthesize(self, text: str, emotion: str = "neutral", pace: str = "normal") -> TTSResult:
        settings = get_settings()
        if not settings.tts_http_base_url:
            raise TTSError("未配置 TTS_HTTP_BASE_URL")
        speed = {"slow": 0.85, "normal": 1.0, "fast": 1.2}.get(pace, 1.0)
        headers = {"Authorization": f"Bearer {settings.tts_http_api_key}"} if settings.tts_http_api_key else {}
        try:
            resp = httpx.post(
                settings.tts_http_base_url,
                json={"text": text, "voice": settings.tts_voice, "speed": speed},
                headers=headers,
                timeout=15.0,
            )
            resp.raise_for_status()
        except Exception as e:
            raise TTSError(f"商用 TTS 合成失败: {e}")

        out_dir = Path(settings.tts_output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        content_type = resp.headers.get("content-type", "")
        if "json" in content_type:
            data = resp.json()
            audio_ref = data.get("audio") or data.get("url")
            if not audio_ref:
                raise TTSError("商用 TTS 响应缺少 audio 字段")
            return TTSResult(audio_ref, _estimate_ms(text, pace), "http")
        filename = f"httptts_{abs(hash(text)) % 10**10}.wav"
        (out_dir / filename).write_bytes(resp.content)
        return TTSResult(f"/api/v1/showcase/audio/{filename}", _estimate_ms(text, pace), "http")


def get_tts_adapter() -> BaseTTSAdapter:
    """按配置返回 TTS 适配器；配置的外部适配器不可用时自动降级为 mock"""
    settings = get_settings()
    provider_map = {
        "cosyvoice": CosyVoiceTTSAdapter,
        "http": HttpTTSAdapter,
    }
    chosen: Optional[BaseTTSAdapter] = None
    cls = provider_map.get(settings.tts_provider)
    if cls:
        chosen = cls()
    if chosen is None:
        return MockTTSAdapter()

    # 包装：外部适配器失败时降级 mock，不阻塞链路
    class _FallbackTTS(BaseTTSAdapter):
        name = chosen.name

        def synthesize(self, text, emotion="neutral", pace="normal"):
            try:
                return chosen.synthesize(text, emotion, pace)
            except TTSError as e:
                logger.warning(f"[TTS] {chosen.name} 失败降级为 mock: {e}")
                return MockTTSAdapter().synthesize(text, emotion, pace)

    return _FallbackTTS()
