"""
平台接入网关管理器
- 适配器注册与状态管理
- 会话级适配器启动/停止/切换
- 统一事件处理：持久化（MySQL）→ 广播钩子（WebSocket，Task 3 接入）
"""
import asyncio
from typing import Any, Awaitable, Callable, Optional

from loguru import logger

from app.core.database import SessionLocal
from app.services.gateway.base_adapter import AdapterStartError, BasePlatformAdapter, EventCallback
from app.services.gateway.models import DanmakuEvent
from app.services.gateway.mock_adapter import MockDanmakuAdapter
from app.services.gateway.browser_adapter import BrowserCollectAdapter
from app.services.gateway.official_adapters import (
    DouyinOfficialAdapter,
    TaobaoOfficialAdapter,
    KuaishouOfficialAdapter,
)

# 广播钩子：Task 3 的 WebSocket 层注册，实现服务端实时推送
BroadcastHook = Callable[[DanmakuEvent], Awaitable[None]]


class GatewayManager:
    """网关管理器（进程内单例）"""

    def __init__(self):
        self._adapters: dict[str, BasePlatformAdapter] = {}
        # session_id -> 正在服务的适配器名
        self._session_bindings: dict[int, str] = {}
        self._hooks: list[BroadcastHook] = []

    # ---------- 注册 ----------

    def register(self, adapter: BasePlatformAdapter) -> None:
        self._adapters[adapter.name] = adapter
        logger.info(f"[网关] 注册适配器: {adapter.name} ({adapter.adapter_type})")

    def register_defaults(self) -> None:
        """按默认配置注册全部适配器"""
        self.register(MockDanmakuAdapter())
        self.register(BrowserCollectAdapter())
        self.register(DouyinOfficialAdapter())
        self.register(TaobaoOfficialAdapter())
        self.register(KuaishouOfficialAdapter())
        # 模拟源默认启用（开发/演示用），其余默认禁用
        self._adapters["mock"].set_enabled(True)

    # ---------- 广播钩子 ----------

    def add_hook(self, hook: BroadcastHook) -> None:
        """注册事件广播钩子（WebSocket 层调用）"""
        if hook not in self._hooks:
            self._hooks.append(hook)

    def remove_hook(self, hook: BroadcastHook) -> None:
        if hook in self._hooks:
            self._hooks.remove(hook)

    # ---------- 状态 ----------

    def get_status(self) -> list[dict]:
        return [adapter.status_info() for adapter in self._adapters.values()]

    def get_adapter(self, name: str) -> Optional[BasePlatformAdapter]:
        return self._adapters.get(name)

    def set_enabled(self, name: str, enabled: bool) -> None:
        adapter = self._adapters.get(name)
        if not adapter:
            raise KeyError(f"适配器 {name} 不存在")
        adapter.set_enabled(enabled)
        logger.info(f"[网关] 适配器 {name} {'启用' if enabled else '禁用'}")

    # ---------- 会话级控制 ----------

    async def start_for_session(
        self, session_id: int, adapter_name: str, options: Optional[dict[str, Any]] = None
    ) -> dict:
        """为场次启动指定适配器；若该场次已有适配器在运行则先停止（即切换）"""
        adapter = self._adapters.get(adapter_name)
        if not adapter:
            raise KeyError(f"适配器 {adapter_name} 不存在")

        # 已绑定同场次则先停止（切换场景）
        bound_name = self._session_bindings.get(session_id)
        if bound_name:
            await self._adapters[bound_name].stop()
            self._session_bindings.pop(session_id, None)
            logger.info(f"[网关] 场次 {session_id} 已从 {bound_name} 切换至 {adapter_name}")

        def _on_event(event: DanmakuEvent) -> Any:
            return self._handle_event(event)

        try:
            await adapter.start(session_id, _on_event, options)
        except AdapterStartError as e:
            raise
        self._session_bindings[session_id] = adapter_name
        return adapter.status_info()

    async def stop_for_session(self, session_id: int) -> bool:
        """停止场次的适配器"""
        bound_name = self._session_bindings.pop(session_id, None)
        if not bound_name:
            return False
        await self._adapters[bound_name].stop()
        return True

    def get_session_binding(self, session_id: int) -> Optional[str]:
        return self._session_bindings.get(session_id)

    # ---------- 事件处理链 ----------

    async def _handle_event(self, event: DanmakuEvent) -> None:
        """统一事件处理：持久化 → 广播钩子"""
        self._persist_danmaku(event)
        for hook in list(self._hooks):
            try:
                await hook(event)
            except Exception as e:
                logger.error(f"[网关] 广播钩子执行失败: {e}")

    def _persist_danmaku(self, event: DanmakuEvent) -> None:
        """弹幕落库（独立短会话，失败不阻塞事件流）"""
        try:
            db = SessionLocal()
            try:
                from app.services.live_session_service import LiveSessionService

                service = LiveSessionService(db)
                service.add_danmaku(
                    session_id=event.session_id,
                    content=event.content,
                    platform=event.platform,
                    user_id=event.user_id,
                    raw=event.raw,
                    sent_at=event.sent_at,
                )
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[网关] 弹幕落库失败（场次 {event.session_id}）: {e}")


# 进程级单例
gateway_manager = GatewayManager()
