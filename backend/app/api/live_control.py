"""
监场台人工控制路由（Task 9.3）
挂载前缀：/api/v1/live
- POST /sessions/{id}/takeover      人工接管：暂停自动决策（弹幕仍缓冲）
- POST /sessions/{id}/restore       恢复自动决策
- GET  /sessions/{id}/control/status  自动决策状态
- POST /sessions/{id}/manual-script   手动下发话术：合规检查 → 决策落库 → WS推送 → TTS 展示包
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.director.models import DirectorLine, DirectorScript
from app.services.director.scheduler import decision_scheduler
from app.services.live_session_service import LiveSessionService
from app.services.showcase.service import showcase_service
from app.services.ws_hub import ws_hub

router = APIRouter()


class ManualScriptRequest(BaseModel):
    """人工接管手动话术请求"""
    text: str = Field(..., min_length=1, max_length=500, description="话术文本")
    emotion: str = Field("neutral", description="情绪：neutral/enthusiastic/warm/urgent/serious")
    pace: str = Field("normal", description="语速：slow/normal/fast")


def _require_live_session(db: Session, session_id: int):
    session = LiveSessionService(db).get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="场次不存在")
    return session


@router.post("/sessions/{session_id}/takeover")
async def takeover(session_id: int, db: Session = Depends(get_db)):
    """人工接管：暂停该场次自动决策（弹幕仍缓冲，恢复后一并消费）"""
    _require_live_session(db, session_id)
    if not decision_scheduler.pause(session_id):
        raise HTTPException(status_code=409, detail="决策循环未在运行，请先启动场次弹幕源")
    await ws_hub._push(session_id, "control", {"auto_decision": "paused"})
    return {"session_id": session_id, "auto_decision": "paused"}


@router.post("/sessions/{session_id}/restore")
async def restore(session_id: int, db: Session = Depends(get_db)):
    """恢复自动决策"""
    _require_live_session(db, session_id)
    if not decision_scheduler.resume(session_id):
        raise HTTPException(status_code=409, detail="决策循环未在运行，请先启动场次弹幕源")
    await ws_hub._push(session_id, "control", {"auto_decision": "running"})
    return {"session_id": session_id, "auto_decision": "running"}


@router.get("/sessions/{session_id}/control/status")
def control_status(session_id: int, db: Session = Depends(get_db)):
    """查询自动决策状态：running / paused / stopped"""
    _require_live_session(db, session_id)
    return {"session_id": session_id, "auto_decision": decision_scheduler.control_status(session_id)}


@router.post("/sessions/{session_id}/manual-script")
async def manual_script(session_id: int, body: ManualScriptRequest, db: Session = Depends(get_db)):
    """人工接管手动话术：同样过合规检查 → 决策落库(adopted) → WS推送 → TTS 展示包"""
    session = _require_live_session(db, session_id)
    if session.status != "liveing":
        raise HTTPException(status_code=409, detail="场次不在直播中，无法下发话术")

    # 1. 构建脚本并做合规检查（违禁词自动替换为建议词，结果随决策落库）
    script = DirectorScript(
        session_id=session_id,
        stage=session.current_stage,
        lines=[DirectorLine(text=body.text, emotion=body.emotion, pace=body.pace)],
        priority="高",
        trigger_reason="人工接管：监场台手动下发话术",
        source="manual",
    )
    compliance = decision_scheduler._apply_compliance(script)
    script.compliance = compliance

    # 2. 决策记录落库（adopted=True 表示人工采用）
    service = LiveSessionService(db)
    record = service.add_decision(
        session_id=session_id,
        script=script.to_persist_dict(),
        trigger_reason=script.trigger_reason,
        priority=script.priority,
        compliance_result=compliance,
        adopted=True,
        degraded=False,
    )

    # 3. WebSocket 推送决策与展示包（TTS 合成/硬闸门在展示服务内）
    await ws_hub.push_decision(session_id, {**script.to_persist_dict(), "record_id": record.id})
    try:
        package = await showcase_service.present(script)
        await ws_hub._push(session_id, "presentation", package)
        if package["mode"] == "blocked" or package["compliance_gate"]["blocked_lines"]:
            await ws_hub.push_alert(session_id, {
                "level": "warning",
                "kind": "compliance",
                "message": "手动话术部分内容被合规闸门拦截，未进入播出环节",
                "detail": package["compliance_gate"],
            })
    except Exception as e:
        package = None
        from loguru import logger
        logger.error(f"[人工控制] 场次 {session_id} 手动话术展示适配失败: {e}")

    return {
        "record_id": record.id,
        "compliance": compliance,
        "package": package,
    }
