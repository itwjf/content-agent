"""
平台接入适配器基类
定义 connect/断线重连/消息缓冲/事件分发 的统一骨架
"""
import asyncio
from abc import ABC, abstractmethod
from collections import deque
from typing import Any, Awaitable, Callable, Optional

from loguru import logger

from app.services.gateway.models import DanmakuEvent

# 事件回调：接收统一弹幕事件
EventCallback = Callable[[DanmakuEvent], Awaitable[None]]


class AdapterStartError(RuntimeError):
    """适配器启动失败（未启用/未实现等）"""


class BasePlatformAdapter(ABC):
    """平台适配器基类

    子类实现 _run() 主循环：产生 DanmakuEvent 并调用 on_event 回调。
    断线/异常时抛出异常，由基类负责指数退避重连；重试耗尽后置为 error 状态。
    """

    name: str = "base"
    adapter_type: str = "base"  # mock/browser/official
    description: str = ""

    def __init__(self, buffer_size: int = 1000, max_retries: int = 3, retry_backoff: float = 2.0):
        # 消息缓冲：断线期间暂存，防止消息丢失（有界队列，超出丢弃最旧）
        self._buffer: deque[DanmakuEvent] = deque(maxlen=buffer_size)
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._session_id: Optional[int] = None
        self._error: Optional[str] = None
        self._enabled = False
        self._max_retries = max_retries
        self._retry_backoff = retry_backoff

    # ---------- 状态 ----------

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def status(self) -> str:
        if self._running:
            return "running"
        if self._error:
            return "error"
        return "stopped"

    def status_info(self) -> dict:
        return {
            "name": self.name,
            "adapter_type": self.adapter_type,
            "description": self.description,
            "enabled": self._enabled,
            "status": self.status,
            "error": self._error,
            "session_id": self._session_id if self._running else None,
            "buffer_size": len(self._buffer),
        }

    def set_enabled(self, enabled: bool) -> None:
        """运行时启用/禁用开关（与配置开关叠加）"""
        self._enabled = enabled

    # ---------- 生命周期 ----------

    async def start(self, session_id: int, on_event: EventCallback, options: dict[str, Any] | None = None) -> None:
        """启动适配器为指定场次服务"""
        if self._running:
            raise AdapterStartError(f"适配器 {self.name} 已在运行中（场次 {self._session_id}）")
        if not self._enabled:
            raise AdapterStartError(f"适配器 {self.name} 未启用")

        self._running = True
        self._error = None
        self._session_id = session_id
        self._task = asyncio.create_task(self._run_with_retry(session_id, on_event, options or {}))
        logger.info(f"[网关] 适配器 {self.name} 已启动，服务场次 {session_id}")

    async def stop(self) -> None:
        """停止适配器"""
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None
        self._session_id = None
        logger.info(f"[网关] 适配器 {self.name} 已停止")

    # ---------- 内部机制 ----------

    def _push(self, event: DanmakuEvent) -> None:
        """写入消息缓冲（断线续传与审计基础）"""
        self._buffer.append(event)

    async def _run_with_retry(self, session_id: int, on_event: EventCallback, options: dict) -> None:
        """带指数退避重连的主循环"""
        retries = 0
        while self._running:
            try:
                await self._run(session_id, on_event, options)
                break  # 正常结束（非断线）
            except asyncio.CancelledError:
                raise
            except Exception as e:
                retries += 1
                self._error = f"{type(e).__name__}: {e}"
                logger.warning(f"[网关] 适配器 {self.name} 异常（第{retries}次）: {e}")
                if not self._running or retries > self._max_retries:
                    logger.error(f"[网关] 适配器 {self.name} 重试耗尽，停止运行")
                    self._running = False
                    break
                await asyncio.sleep(self._retry_backoff * retries)

    @abstractmethod
    async def _run(self, session_id: int, on_event: EventCallback, options: dict) -> None:
        """适配器主循环：产生事件并调用 on_event；断线时抛出异常触发重连"""
        raise NotImplementedError
