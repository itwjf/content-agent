"""
WebSocket 实时推送枢纽
- 按场次管理连接
- 统一事件信封：{type, seq, ts, data}
- 每场次维护单调递增序列号与有界事件历史，支持客户端携带 last_event_id 增量补拉
- 历史超出缓冲范围时提示客户端走 REST 回放接口
"""
import asyncio
import json
from collections import defaultdict, deque
from datetime import datetime
from typing import Any

from fastapi import WebSocket
from loguru import logger

from app.services.gateway.models import DanmakuEvent, MetricEvent

HISTORY_SIZE = 2000  # 每场次保留的最近事件数（超出部分走 REST 回放）


class LiveConnectionHub:
    """实时连接枢纽（进程内单例）"""

    def __init__(self):
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._history: dict[int, deque] = defaultdict(lambda: deque(maxlen=HISTORY_SIZE))
        self._seq: dict[int, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    # ---------- 连接管理 ----------

    async def connect(self, websocket: WebSocket, session_id: int, last_event_id: int = 0) -> None:
        """接受连接并按 last_event_id 增量补拉错过的消息"""
        await websocket.accept()
        missed: list[dict] = []
        gap = False
        async with self._lock:
            history = self._history[session_id]
            if last_event_id > 0 and history:
                oldest_seq = history[0]["seq"]
                if last_event_id < oldest_seq - 1:
                    gap = True  # 有事件超出缓冲，需要客户端走 REST 回放
                missed = [m for m in history if m["seq"] > last_event_id]
            self._connections[session_id].add(websocket)

        # 先补拉历史，再正式进入推送流
        for msg in missed:
            try:
                await websocket.send_text(json.dumps(msg, ensure_ascii=False))
            except Exception:
                self.disconnect(websocket, session_id)
                return
        if gap:
            try:
                await websocket.send_text(json.dumps({
                    "type": "gap",
                    "seq": last_event_id,
                    "ts": datetime.now().isoformat(),
                    "data": {"message": "部分历史事件超出缓冲范围，请调用 /api/v1/live/sessions/{id}/replay/* 补拉"},
                }, ensure_ascii=False))
            except Exception:
                pass
        logger.info(f"[WS] 场次 {session_id} 新连接（last_event_id={last_event_id}，补拉{len(missed)}条，gap={gap}）")

    def disconnect(self, websocket: WebSocket, session_id: int) -> None:
        self._connections[session_id].discard(websocket)
        if not self._connections[session_id]:
            self._connections.pop(session_id, None)
        logger.info(f"[WS] 场次 {session_id} 连接断开")

    def connection_count(self, session_id: int) -> int:
        return len(self._connections.get(session_id, ()))

    # ---------- 推送 ----------

    async def _push(self, session_id: int, msg_type: str, data: Any) -> int:
        """生成信封（seq 单调递增）、写入历史、广播给该场次全部连接"""
        async with self._lock:
            self._seq[session_id] += 1
            envelope = {
                "type": msg_type,
                "seq": self._seq[session_id],
                "ts": datetime.now().isoformat(),
                "data": data,
            }
            self._history[session_id].append(envelope)
            connections = list(self._connections.get(session_id, ()))

        dead: list[WebSocket] = []
        for ws in connections:
            try:
                await ws.send_text(json.dumps(envelope, ensure_ascii=False))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, session_id)
        return envelope["seq"]

    async def push_danmaku(self, event: DanmakuEvent) -> None:
        """推送弹幕事件（注册为网关广播钩子）"""
        await self._push(event.session_id, "danmaku", event.model_dump(mode="json"))

    async def push_decision(self, session_id: int, decision: dict) -> None:
        """推送决策/导演脚本事件（Task 5 决策链路调用）"""
        await self._push(session_id, "decision", decision)

    async def push_metric(self, event: MetricEvent) -> None:
        """推送实时指标事件（Task 8 指标采集调用）"""
        await self._push(event.session_id, "metric", event.model_dump(mode="json"))

    async def push_stage(self, session_id: int, stage_info: dict) -> None:
        """推送直播阶段变更事件"""
        await self._push(session_id, "stage", stage_info)


# 进程级单例
ws_hub = LiveConnectionHub()
