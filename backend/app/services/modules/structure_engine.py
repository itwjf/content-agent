"""
内容结构引擎 - 直播阶段管理
功能：管理直播阶段划分与时间规划，实时提示当前阶段及下一阶段准备
"""
from typing import Dict, List, Optional
from enum import Enum


class LiveStageEnum(str, Enum):
    """直播阶段枚举"""
    PREHEATING = "预热期"
    PRODUCT_INTRO = "产品讲解期"
    PROMOTION = "促单期"
    QA = "问答互动期"
    ENDING = "结尾期"


class StructureEngine:
    """内容结构引擎"""

    # 阶段配置
    STAGE_CONFIG = {
        "预热期": {
            "duration_ratio": 0.1,  # 占总时长的10%
            "description": "欢迎观众，介绍直播主题",
            "next": "产品讲解期",
            "tips": [
                "欢迎家人们来到直播间",
                "今天给大家介绍XX产品",
                "先关注直播间，不迷路"
            ]
        },
        "产品讲解期": {
            "duration_ratio": 0.5,  # 占总时长的50%
            "description": "详细介绍产品特点、功效、使用方法",
            "next": "促单期",
            "tips": [
                "详细介绍产品成分",
                "演示产品使用方法",
                "对比同类产品优势"
            ]
        },
        "促单期": {
            "description": "强调优惠力度，引导下单",
            "next": "问答互动期",
            "tips": [
                "强调限时优惠",
                "说明赠品福利",
                "倒数下单时机"
            ]
        },
        "问答互动期": {
            "description": "回答观众问题，增加互动",
            "next": "促单期",
            "tips": [
                "回答弹幕问题",
                "根据反馈调整话术",
                "引导观众下单"
            ]
        },
        "结尾期": {
            "description": "总结回顾，感谢观众",
            "next": None,
            "tips": [
                "感谢观众支持",
                "预告下次直播",
                "引导关注收藏"
            ]
        }
    }

    def __init__(self):
        pass

    def get_current_stage(
        self,
        current_time: int,
        total_time: int,
        manual_stage: str = None
    ) -> Dict:
        """
        获取当前直播阶段

        Args:
            current_time: 已直播时长（秒）
            total_time: 计划总时长（秒）
            manual_stage: 手动指定的阶段（优先级最高）

        Returns:
            阶段信息
        """
        # 如果手动指定了阶段，优先使用
        if manual_stage and manual_stage in self.STAGE_CONFIG:
            return self._build_stage_info(manual_stage, current_time, total_time)

        # 根据时间自动判断阶段
        if total_time <= 0:
            return self._build_stage_info("产品讲解期", current_time, total_time)

        progress = current_time / total_time

        # 根据进度判断阶段
        if progress < 0.1:
            stage = "预热期"
        elif progress < 0.6:
            stage = "产品讲解期"
        elif progress < 0.75:
            stage = "促单期"
        elif progress < 0.9:
            stage = "问答互动期"
        else:
            stage = "结尾期"

        return self._build_stage_info(stage, current_time, total_time)

    def _build_stage_info(self, stage: str, current_time: int, total_time: int) -> Dict:
        """构建阶段信息"""
        config = self.STAGE_CONFIG.get(stage, {})
        next_stage = config.get("next")

        # 计算当前阶段已用时间
        if total_time > 0 and stage in ["预热期", "产品讲解期"]:
            ratio = config.get("duration_ratio", 0.1)
            stage_duration = total_time * ratio
            stage_elapsed = current_time - (total_time * sum(
                self.STAGE_CONFIG.get(s, {}).get("duration_ratio", 0)
                for s in list(self.STAGE_CONFIG.keys())[:list(self.STAGE_CONFIG.keys()).index(stage)]
            ))
        else:
            stage_duration = 0
            stage_elapsed = 0

        return {
            "当前阶段": stage,
            "阶段描述": config.get("description", ""),
            "下一阶段": next_stage,
            "阶段提示": config.get("tips", []),
            "阶段时长": stage_duration,
            "阶段已用时间": stage_elapsed,
            "下一阶段准备": self._get_next_stage_tips(next_stage)
        }

    def _get_next_stage_tips(self, next_stage: Optional[str]) -> List[str]:
        """获取下一阶段的准备提示"""
        if not next_stage:
            return []

        config = self.STAGE_CONFIG.get(next_stage, {})
        return config.get("tips", [])

    def get_stage_transition_advice(
        self,
        current_stage: str,
        backend_data: Dict = None
    ) -> Dict:
        """
        获取阶段切换建议

        Args:
            current_stage: 当前阶段
            backend_data: 后台数据（在线人数、转化率等）

        Returns:
            切换建议
        """
        if current_stage not in self.STAGE_CONFIG:
            return {"建议": "继续当前阶段", "原因": ""}

        config = self.STAGE_CONFIG.get(current_stage, {})
        next_stage = config.get("next")

        # 根据后台数据调整建议
        if backend_data:
            online_count = backend_data.get("在线人数", 0)
            conversion_rate = backend_data.get("转化率", "0%")

            # 在线人数多，可以多互动
            if online_count > 1000 and current_stage == "产品讲解期":
                return {
                    "建议": "可以提前进入问答互动",
                    "原因": f"当前在线人数{online_count}，互动氛围好"
                }

            # 转化率高，加快节奏
            if "上升" in str(conversion_rate) or float(conversion_rate.replace("%", "").replace("上升", "").replace("下降", "")) > 3:
                if current_stage == "问答互动期":
                    return {
                        "建议": "可以回到促单期",
                        "原因": "转化率表现良好，把握机会促单"
                    }

        # 默认建议
        if next_stage:
            return {
                "建议": f"准备进入{next_stage}",
                "原因": f"当前阶段即将结束，{next_stage}是下一步"
            }

        return {
            "建议": "继续当前阶段",
            "原因": "直播即将结束"
        }


# 模块实例
structure_engine = StructureEngine()


def get_current_stage(current_time: int, total_time: int, manual_stage: str = None) -> Dict:
    """
    获取当前直播阶段

    Args:
        current_time: 已直播时长（秒）
        total_time: 计划总时长（秒）
        manual_stage: 手动指定的阶段

    Returns:
        阶段信息
    """
    return structure_engine.get_current_stage(current_time, total_time, manual_stage)


def get_stage_transition_advice(current_stage: str, backend_data: Dict = None) -> Dict:
    """
    获取阶段切换建议

    Args:
        current_stage: 当前阶段
        backend_data: 后台数据

    Returns:
        切换建议
    """
    return structure_engine.get_stage_transition_advice(current_stage, backend_data)
