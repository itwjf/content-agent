"""
平台接入网关 - 统一适配器框架
"""
from app.services.gateway.base_adapter import AdapterStartError, BasePlatformAdapter
from app.services.gateway.manager import GatewayManager, gateway_manager

__all__ = [
    "AdapterStartError",
    "BasePlatformAdapter",
    "GatewayManager",
    "gateway_manager",
]
