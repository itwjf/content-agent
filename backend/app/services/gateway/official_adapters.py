"""
官方开放平台 API 适配器（禁用占位）
抖音/淘宝/快手官方弹幕接口需要企业资质与权限审批，资质获批并完成对接前保持禁用。
每个适配器在 _run() 中直接抛出 NotImplementedError，防止在未对接的情况下被启用。
"""
from typing import Any

from app.services.gateway.base_adapter import BasePlatformAdapter, EventCallback
from app.core.config import get_settings


class _BaseOfficialAdapter(BasePlatformAdapter):
    """官方 API 适配器基类：仅占位，未对接平台接口"""
    adapter_type = "official"
    platform: str = ""

    def __init__(self):
        super().__init__()
        settings = get_settings()
        enabled_map = {
            "douyin": settings.douyin_api_enabled,
            "taobao": settings.taobao_api_enabled,
            "kuaishou": settings.kuaishou_api_enabled,
        }
        # 配置开关默认关闭；即使配置打开，未实现对接时启动仍会报错
        self._enabled = bool(enabled_map.get(self.name, False))

    async def _run(self, session_id: int, on_event: EventCallback, options: dict) -> None:
        raise NotImplementedError(
            f"{self.name} 官方API适配器尚未对接（需平台资质审批与接口联调）。"
            f"请使用 mock 或 browser 适配器。"
        )


class DouyinOfficialAdapter(_BaseOfficialAdapter):
    """抖音开放平台弹幕适配器（占位）"""
    name = "douyin"
    platform = "douyin"
    description = "抖音开放平台弹幕（需企业资质+权限审批，未对接）"


class TaobaoOfficialAdapter(_BaseOfficialAdapter):
    """淘宝开放平台弹幕适配器（占位）"""
    name = "taobao"
    platform = "taobao"
    description = "淘宝开放平台弹幕（需ISV资质，未对接）"


class KuaishouOfficialAdapter(_BaseOfficialAdapter):
    """快手开放平台弹幕适配器（占位）"""
    name = "kuaishou"
    platform = "kuaishou"
    description = "快手开放平台弹幕（需资质，未对接）"
