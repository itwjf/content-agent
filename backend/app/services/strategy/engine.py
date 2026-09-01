"""
策略引擎（SubTask 8.2 / 8.3）
- 滑动窗口指标计算：人气趋势、弹幕速率、负面占比、转化事件
- 5 条可配置基础策略规则（阈值来自 config），动态调整决策权重
- 权重被导演引擎消费：LLM 提示注入 + 规则降级分支选择
- 每次调整记录原因与前后权重快照（strategy_adjustments 表）并推送 WebSocket
"""
import asyncio
import time
from collections import defaultdict, deque
from typing import Optional

from loguru import logger

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.gateway.models import MetricEvent
from app.services.ws_hub import ws_hub

# 决策权重维度：促单/安抚/答疑/推进（导演引擎按权重选择侧重方向）
DEFAULT_WEIGHTS: dict[str, float] = {"促单": 1.0, "安抚": 1.0, "答疑": 1.0, "推进": 1.0}
WEIGHT_MIN, WEIGHT_MAX = 0.5, 3.0
WEIGHT_DECAY = 0.8          # 每轮评估权重向默认值回归的比例（避免只升不降）
METRIC_TYPES = {"popularity", "danmaku_rate", "like", "cart_click", "order"}


class StrategyEngine:
    """策略引擎（进程内单例）"""

    def __init__(self):
        self._weights: dict[int, dict[str, float]] = {}
        # metric_type -> deque[(ts, value)]
        self._metric_windows: dict[int, dict[str, deque]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=600))
        )
        # 决策轮反馈窗口：(ts, total, negative, questions, buy_intent)
        self._feedback_windows: dict[int, deque] = defaultdict(lambda: deque(maxlen=600))
        self._last_eval: dict[int, float] = {}

    # ---------- 权重 ----------

    def get_weights(self, session_id: int) -> dict[str, float]:
        return dict(self._weights.get(session_id, DEFAULT_WEIGHTS))

    def reset(self, session_id: int) -> dict[str, float]:
        """重置为默认权重（场次开始/人工干预时调用）"""
        self._weights[session_id] = dict(DEFAULT_WEIGHTS)
        logger.info(f"[策略] 场次 {session_id} 权重已重置为默认值")
        return self.get_weights(session_id)

    # ---------- 数据入口 ----------

    def on_metric(self, event: MetricEvent) -> Optional[dict]:
        """指标入库后调用：写滑动窗口并触发评估；返回调整记录（有调整时）"""
        if event.metric_type in METRIC_TYPES:
            self._metric_windows[event.session_id][event.metric_type].append(
                (event.recorded_at.timestamp(), event.value)
            )
        return self.evaluate(event.session_id)

    def feedback(self, session_id: int, total: int, negative: int,
                 questions: int, buy_intent: int) -> Optional[dict]:
        """决策轮互动反馈（调度器每轮决策后调用）：累计弹幕情绪窗口并触发评估"""
        self._feedback_windows[session_id].append(
            (time.time(), total, negative, questions, buy_intent)
        )
        return self.evaluate(session_id)

    # ---------- 滑动窗口计算 ----------

    def _popularity_trend(self, session_id: int) -> tuple[Optional[float], Optional[float]]:
        """返回 (窗口内相对变化率, 最新值)；样本不足返回 (None, latest)"""
        points = list(self._metric_windows[session_id].get("popularity", ()))
        if not points:
            return None, None
        latest = points[-1][1]
        if len(points) < 2:
            return None, latest
        first = points[0][1]
        if first <= 0:
            return None, latest
        return (latest - first) / first, latest

    def _danmaku_stats(self, session_id: int, window_seconds: float) -> dict:
        """汇总决策反馈窗口：总弹幕数、负面占比、提问数、购买意向数、弹幕速率(条/分)"""
        now = time.time()
        total = negative = questions = buy = 0
        for ts, t, neg, q, b in list(self._feedback_windows[session_id]):
            if now - ts <= window_seconds:
                total += t
                negative += neg
                questions += q
                buy += b
        rate_per_min = total / (window_seconds / 60.0) if window_seconds > 0 else 0.0
        neg_ratio = negative / total if total > 0 else 0.0
        return {"total": total, "negative": negative, "negative_ratio": neg_ratio,
                "questions": questions, "buy_intent": buy, "rate_per_min": rate_per_min}

    def _conversion_sum(self, session_id: int, window_seconds: float) -> float:
        """窗口内转化事件总量（购物车点击 + 下单）"""
        now = time.time()
        total = 0.0
        for mtype in ("cart_click", "order"):
            for ts, value in list(self._metric_windows[session_id].get(mtype, ())):
                if now - ts <= window_seconds:
                    total += value
        return total

    # ---------- 规则评估与调权 ----------

    def evaluate(self, session_id: int) -> Optional[dict]:
        """评估全部规则；命中则调整权重、落库并推送。受最小评估间隔节流。"""
        settings = get_settings()
        now = time.time()
        if now - self._last_eval.get(session_id, 0) < settings.strategy_eval_interval:
            return None
        self._last_eval[session_id] = now

        window = settings.strategy_window_seconds
        pop_change, pop_latest = self._popularity_trend(session_id)
        dm = self._danmaku_stats(session_id, window)
        conversions = self._conversion_sum(session_id, window)

        stats = {
            "popularity_change": round(pop_change, 4) if pop_change is not None else None,
            "popularity_latest": pop_latest,
            "danmaku_rate_per_min": round(dm["rate_per_min"], 2),
            "negative_ratio": round(dm["negative_ratio"], 4),
            "conversions": conversions,
        }

        # 5 条可配置基础策略规则（阈值均来自配置）
        rules_hit = []
        if pop_change is not None and pop_change >= settings.strategy_popularity_rise:
            rules_hit.append({"rule": "人气上升", "bump": {"促单": 0.3},
                              "reason": f"人气上涨{pop_change:.0%}，加大促单力度", "stats": stats})
        if pop_change is not None and pop_change <= -settings.strategy_popularity_drop:
            rules_hit.append({"rule": "人气下降", "bump": {"推进": 0.3},
                              "reason": f"人气下跌{abs(pop_change):.0%}，转为互动拉新与节奏推进", "stats": stats})
        if dm["total"] >= 5 and dm["negative_ratio"] >= settings.strategy_negative_ratio:
            rules_hit.append({"rule": "负面聚集", "bump": {"安抚": 0.5},
                              "reason": f"负面弹幕占比{dm['negative_ratio']:.0%}超阈值，提升安抚优先级", "stats": stats})
        if dm["rate_per_min"] >= settings.strategy_danmaku_rate_high:
            rules_hit.append({"rule": "高频提问", "bump": {"答疑": 0.3},
                              "reason": f"弹幕速率{dm['rate_per_min']:.0f}条/分，集中答疑", "stats": stats})
        if conversions >= settings.strategy_conversion_high:
            rules_hit.append({"rule": "转化活跃", "bump": {"促单": 0.5},
                              "reason": f"窗口内转化事件{conversions:.0f}次，乘势促单", "stats": stats})

        if not rules_hit:
            return None

        # 权重先向默认回归，再叠加规则增量（限幅）
        weights = self._weights.get(session_id, dict(DEFAULT_WEIGHTS))
        before = dict(weights)
        for key in weights:
            weights[key] = round(1.0 + (weights[key] - 1.0) * WEIGHT_DECAY, 4)
        for hit in rules_hit:
            for key, bump in hit["bump"].items():
                weights[key] = round(min(WEIGHT_MAX, max(WEIGHT_MIN, weights[key] + bump)), 4)
        self._weights[session_id] = weights

        record = {
            "session_id": session_id,
            "rules_hit": [{k: v for k, v in hit.items() if k != "bump"} for hit in rules_hit],
            "reason": "；".join(hit["reason"] for hit in rules_hit),
            "weights_before": before,
            "weights_after": weights,
            "stats": stats,
        }
        self._persist(record)
        self._broadcast(session_id, record)
        logger.info(f"[策略] 场次 {session_id} 调权: {before} → {weights}（{record['reason']}）")
        return record

    # ---------- 持久化与广播 ----------

    def _persist(self, record: dict) -> None:
        """调整记录落库（独立短会话，失败不阻塞策略链路）"""
        try:
            db = SessionLocal()
            try:
                from app.models.live_models import StrategyAdjustment

                db.add(StrategyAdjustment(
                    session_id=record["session_id"],
                    rules_hit=record["rules_hit"],
                    reason=record["reason"],
                    weights_before=record["weights_before"],
                    weights_after=record["weights_after"],
                ))
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[策略] 调整记录落库失败（场次 {record['session_id']}）: {e}")

    def _broadcast(self, session_id: int, record: dict) -> None:
        """推送策略调整事件给监场台（展示调整原因）"""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(ws_hub._push(session_id, "strategy", record))
        except RuntimeError:
            pass  # 无事件循环（如纯单元测试）时跳过


# 进程级单例
strategy_engine = StrategyEngine()
