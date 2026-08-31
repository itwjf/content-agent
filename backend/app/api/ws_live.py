"""
WebSocket 实时通道端点
- /ws/live/{session_id}?last_event_id=<seq>：实时接收 danmaku/decision/metric/stage 四类消息
- 断线重连：客户端重连时携带上次收到的最大 seq（last_event_id），服务端增量补拉
"""
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.database import SessionLocal
from app.services.live_session_service import LiveSessionService
from app.services.ws_hub import ws_hub

router = APIRouter()


@router.websocket("/ws/live/{session_id}")
async def ws_live(websocket: WebSocket, session_id: int, last_event_id: int = 0):
    """直播实时通道"""
    # 校验场次存在
    db = SessionLocal()
    try:
        session = LiveSessionService(db).get_session(session_id)
    finally:
        db.close()
    if not session:
        await websocket.close(code=4404, reason="场次不存在")
        return

    await ws_hub.connect(websocket, session_id, last_event_id=last_event_id)

    try:
        while True:
            # 接收客户端消息：仅处理 ping 保活，其余忽略（控制类操作走 REST）
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except (ValueError, TypeError):
                continue
            if msg.get("action") == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "ts": msg.get("ts", "")}))
    except WebSocketDisconnect:
        ws_hub.disconnect(websocket, session_id)
    except Exception:
        ws_hub.disconnect(websocket, session_id)
