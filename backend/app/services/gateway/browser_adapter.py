"""
浏览器端采集适配器（占位）
通过浏览器端脚本采集直播页评论并回传网关，作为无官方渠道时的兜底方案。
具体实现见 spec Task 7，当前仅注册占位，不可启用。
"""
from typing import Any

from app.services.gateway.base_adapter import BasePlatformAdapter, EventCallback


class BrowserCollectAdapter(BasePlatformAdapter):
    """浏览器采集适配器（占位，Task 7 实现）"""
    name = "browser"
    adapter_type = "browser"
    description = "浏览器端弹幕采集（官方渠道兜底，Task 7 实现）"

    def __init__(self):
        super().__init__()
        self._enabled = False

    async def _run(self, session_id: int, on_event: EventCallback, options: dict) -> None:
        raise NotImplementedError("浏览器采集适配器尚未实现（计划于 Task 7 交付）")
