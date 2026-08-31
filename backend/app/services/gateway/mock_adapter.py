"""
模拟弹幕源适配器
支持场景化弹幕序列回放：高频提问 / 负面刷屏 / 购买意向 / 综合
"""
import asyncio
import hashlib
from datetime import datetime
from typing import Any

from loguru import logger

from app.services.gateway.base_adapter import BasePlatformAdapter, EventCallback
from app.services.gateway.models import DanmakuEvent

# 场景化弹幕剧本
SCENARIOS: dict[str, list[str]] = {
    # 高频提问：同一问题刷屏（模拟真实直播间重复提问）
    "高频提问": [
        "油皮能用吗？",
        "敏感肌可以用吗？",
        "油皮能用吗？",
        "有没有小样？",
        "孕妇可以用吗？",
        "油皮能用吗？",
        "和XX大牌比怎么样？",
    ],
    # 负面刷屏：负面反馈聚集
    "负面刷屏": [
        "价格太贵了",
        "效果没有说的那么好吧",
        "上次买的感觉一般",
        "太贵了，等打折",
        "用着有点刺激",
        "不值这个价",
    ],
    # 购买意向：下单意向集中
    "购买意向": [
        "怎么拍？",
        "链接在哪里？",
        "已拍，等发货",
        "拍了两单！",
        "这个有优惠吗？",
        "第一次买，试试看",
    ],
    # 综合：混合场景（默认）
    "综合": [
        "油皮能用吗？",
        "价格太贵了",
        "怎么拍？",
        "有没有小样？",
        "主播讲解一下成分呗",
        "已拍！",
        "敏感肌能用吗？",
        "效果怎么样？",
        "太贵了",
        "链接发一下",
    ],
}


class MockDanmakuAdapter(BasePlatformAdapter):
    """模拟弹幕源适配器

    options:
        scenario: str   场景名（高频提问/负面刷屏/购买意向/综合），默认"综合"
        interval: float 每条弹幕间隔秒数，默认 2.0
        loop: bool      是否循环播放，默认 True
        user_prefix: str 模拟用户ID前缀，默认 "mock_user"
    """

    name = "mock"
    adapter_type = "mock"
    description = "模拟弹幕源：按场景回放弹幕序列（开发/演示用）"

    async def _run(self, session_id: int, on_event: EventCallback, options: dict) -> None:
        scenario = options.get("scenario", "综合")
        interval = float(options.get("interval", 2.0))
        loop = bool(options.get("loop", True))
        user_prefix = options.get("user_prefix", "mock_user")

        messages = SCENARIOS.get(scenario)
        if messages is None:
            raise ValueError(f"未知场景: {scenario}，可选: {list(SCENARIOS.keys())}")

        logger.info(f"[网关] 模拟源开始回放 | 场次={session_id} 场景={scenario} 间隔={interval}s 循环={loop}")

        seq = 0
        while self._running:
            for content in messages:
                if not self._running:
                    break
                seq += 1
                # 生成稳定的脱敏用户ID（同一内容同一用户，模拟真实刷屏感）
                uid_hash = hashlib.md5(f"{user_prefix}_{seq % 20}".encode()).hexdigest()[:12]
                event = DanmakuEvent(
                    session_id=session_id,
                    platform="mock",
                    user_id=uid_hash,
                    content=content,
                    sent_at=datetime.now(),
                    raw={"scenario": scenario, "seq": seq},
                )
                self._push(event)
                await on_event(event)
                await asyncio.sleep(interval)
            if not loop:
                break

        logger.info(f"[网关] 模拟源回放结束 | 场次={session_id} 共{seq}条")
