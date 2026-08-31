"""
浏览器端采集适配器（官方渠道兜底方案）
由浏览器端脚本（油猴/控制台注入）采集直播页评论，通过回传接口推送到本适配器，
归一化为统一 DanmakuEvent 进入决策链路。使用方式与风险提示见 docs/platform-access.md。
"""
import asyncio

from loguru import logger

from app.core.config import get_settings
from app.services.gateway.base_adapter import BasePlatformAdapter, EventCallback
from app.services.gateway.models import DanmakuEvent


class BrowserCollectAdapter(BasePlatformAdapter):
    """浏览器采集适配器（接收型）

    与 mock/官方适配器的"主动拉取"不同，本适配器是"被动接收"：
    - 采集脚本通过 POST /api/v1/gateway/browser/ingest/{session_id} 回传弹幕
    - submit() 将事件写入内部队列，_run() 消费队列并走统一事件链（落库→钩子广播）
    - 未运行时回传的事件直接拒绝（HTTP 409），由采集端自行退避重试
    """

    name = "browser"
    adapter_type = "browser"
    description = "浏览器端弹幕采集（官方渠道兜底：油猴/控制台脚本回传）"

    def __init__(self):
        super().__init__(max_retries=1)  # 接收型无需断线重连风暴
        self._queue: asyncio.Queue[DanmakuEvent] = asyncio.Queue(maxsize=500)
        self._enabled = get_settings().browser_adapter_enabled

    # ---------- 事件注入（回传接口调用） ----------

    def is_serving(self, session_id: int) -> bool:
        """判断适配器是否正在为指定场次服务"""
        return self._running and self._session_id == session_id

    def submit(self, events: list[DanmakuEvent]) -> int:
        """注入采集到的弹幕事件，返回实际接收条数（队列满时丢弃最新并计数）"""
        if not self.is_serving(events[0].session_id if events else -1):
            return 0
        accepted = 0
        for event in events:
            try:
                self._queue.put_nowait(event)
                accepted += 1
            except asyncio.QueueFull:
                logger.warning("[网关] 浏览器采集队列已满，丢弃新事件（采集端请降低频率）")
                break
        return accepted

    # ---------- 主循环 ----------

    async def _run(self, session_id: int, on_event: EventCallback, options: dict) -> None:
        logger.info(
            f"[网关] 浏览器采集适配器就绪 | 场次={session_id} "
            f"回传地址=/api/v1/gateway/browser/ingest/{session_id}"
        )
        while self._running:
            event = await self._queue.get()  # stop() 取消任务时在此中断
            self._push(event)
            await on_event(event)
