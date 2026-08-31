"""
浏览器采集回传路由（官方渠道兜底方案，SubTask 7.1）
挂载前缀：/api/v1/gateway/browser
- POST /ingest/{session_id} ：采集脚本批量回传弹幕，归一化为统一 DanmakuEvent
- GET  /collector.js        ：下发注入脚本（服务地址/场次/令牌按查询参数动态注入）
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field
from loguru import logger

from app.core.config import get_settings
from app.services.gateway import gateway_manager
from app.services.gateway.collector_script import COLLECTOR_JS_TEMPLATE
from app.services.gateway.models import DanmakuEvent

import json

router = APIRouter()


class BrowserDanmakuItem(BaseModel):
    """采集脚本回传的单条弹幕"""
    user_id: Optional[str] = Field(None, description="脱敏后的用户标识（采集端已完成哈希）")
    content: str = Field(..., min_length=1, max_length=200, description="弹幕内容")
    sent_at: Optional[datetime] = Field(None, description="弹幕发送时间（缺省用服务端接收时间）")
    raw: Optional[dict] = Field(None, description="附加信息（页面URL等）")


class BrowserIngestRequest(BaseModel):
    """采集脚本批量回传请求"""
    token: Optional[str] = Field(None, description="回传令牌（后端配置了 browser_collect_token 时必填）")
    platform: str = Field("browser", description="采集来源标识")
    items: list[BrowserDanmakuItem] = Field(..., min_length=1, description="弹幕列表")


def _get_browser_adapter():
    adapter = gateway_manager.get_adapter("browser")
    if adapter is None:
        raise HTTPException(status_code=503, detail="浏览器采集适配器未注册")
    return adapter


@router.post("/ingest/{session_id}")
async def ingest(session_id: int, body: BrowserIngestRequest):
    """采集脚本回传弹幕 → 归一化进统一消息模型（需先为场次启动 browser 适配器）"""
    # 令牌校验：后端配置了令牌则必须匹配；未配置则放行（建议仅内网/本机使用）
    expected = get_settings().browser_collect_token
    if expected and body.token != expected:
        raise HTTPException(status_code=401, detail="回传令牌校验失败")

    adapter = _get_browser_adapter()
    if not adapter.is_serving(session_id):
        raise HTTPException(
            status_code=409,
            detail=f"浏览器采集适配器未在服务场次 {session_id}，请先调用 "
                   f"POST /api/v1/gateway/sessions/{session_id}/start 启动 browser 适配器",
        )

    events = [
        DanmakuEvent(
            session_id=session_id,
            platform="browser",
            user_id=item.user_id,
            content=item.content,
            sent_at=item.sent_at or datetime.now(),
            raw=item.raw,
        )
        for item in body.items
    ]
    accepted = adapter.submit(events)
    if accepted < len(events):
        logger.warning(f"[浏览器采集] 场次 {session_id} 回传 {len(events)} 条，仅接收 {accepted} 条")
    return {"session_id": session_id, "received": len(events), "accepted": accepted}


@router.get("/collector.js", response_class=Response)
async def collector_js(
    request: Request,
    session_id: Optional[int] = None,
    token: Optional[str] = None,
    server: Optional[str] = None,
):
    """下发浏览器采集脚本

    - server: 后端地址（默认当前请求的 base_url）
    - session_id: 场次ID（默认取 browser 适配器当前绑定的场次）
    - token: 回传令牌（默认取配置 browser_collect_token）
    """
    adapter = _get_browser_adapter()
    sid = session_id or (adapter._session_id if adapter.status == "running" else None)
    if sid is None:
        raise HTTPException(
            status_code=400,
            detail="无法确定场次ID：请先为场次启动 browser 适配器，或通过 ?session_id= 指定",
        )
    server_url = (server or str(request.base_url)).rstrip("/")
    token_value = token if token is not None else get_settings().browser_collect_token

    script = (
        COLLECTOR_JS_TEMPLATE
        .replace("__CA_SERVER__", json.dumps(server_url))
        .replace("__CA_SESSION_ID__", str(int(sid)))
        .replace("__CA_TOKEN__", json.dumps(token_value or ""))
    )
    return Response(content=script, media_type="application/javascript; charset=utf-8")
