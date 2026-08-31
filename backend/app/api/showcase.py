"""
展示适配层路由
- POST /api/v1/showcase/preview：文本 → 合规闸门 → TTS → 输出包（独立测试展示链路）
- GET  /api/v1/showcase/audio/{filename}：播放合成的音频文件
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services.director.models import DirectorLine, DirectorScript
from app.services.showcase.service import showcase_service

router = APIRouter()


class ShowcasePreviewRequest(BaseModel):
    """展示链路预览请求"""
    text: str = Field(..., description="台词文本")
    emotion: str = Field("neutral", description="情绪：neutral/enthusiastic/warm/urgent/serious")
    pace: str = Field("normal", description="语速：slow/normal/fast")
    session_id: int = Field(0, description="关联场次（0=不关联）")


@router.post("/preview")
async def showcase_preview(body: ShowcasePreviewRequest):
    """展示链路独立预览：不走决策链路，直接合成指定文本"""
    script = DirectorScript(
        session_id=body.session_id,
        stage="预览",
        lines=[DirectorLine(text=body.text, emotion=body.emotion, pace=body.pace)],
        trigger_reason="展示链路预览",
    )
    package = await showcase_service.present(script)
    return package


@router.get("/audio/{filename}")
async def serve_audio(filename: str):
    """播放 TTS 合成的音频文件"""
    # 文件名安全校验（防目录穿越）
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="非法文件名")
    filepath = Path(get_settings().tts_output_dir) / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="音频文件不存在")
    media_type = "audio/wav" if filepath.suffix == ".wav" else "audio/mpeg"
    return FileResponse(filepath, media_type=media_type)
