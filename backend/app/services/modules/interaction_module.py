"""
互动理解模块 - 弹幕语义分析
功能：实时弹幕语义分析，识别用户意图、高频问题、情绪
"""
from typing import List, Dict, Tuple
from collections import Counter
import re


class InteractionModule:
    """互动理解模块"""

    # 意图关键词映射
    INTENT_KEYWORDS = {
        "提问": ["吗", "呢", "能不能", "可以", "有没有", "怎么", "多少", "什么", "?", "？"],
        "负面": ["贵", "太贵", "不好", "差", "坑", "骗", "退货", "投诉", "垃圾", "烂"],
        "购买意向": ["买", "下单", "怎么买", "多少钱", "在哪买", "链接", "拍", "抢"],
        "赞美": ["好", "棒", "赞", "喜欢", "好看", "实惠", "划算", "推荐"],
    }

    def __init__(self):
        pass

    def analyze(self, danmu_messages: List[str]) -> Dict:
        """
        分析弹幕数据

        Args:
            danmu_messages: 弹幕消息列表

        Returns:
            分析结果字典
        """
        if not danmu_messages:
            return {
                "意图列表": [],
                "高频问题": [],
                "情绪统计": {},
                "负面反馈": []
            }

        # 1. 意图识别
        intents = self._recognize_intents(danmu_messages)

        # 2. 高频问题提取
        high_freq_questions = self._extract_high_freq_questions(danmu_messages)

        # 3. 情绪统计
        emotion_stats = self._count_emotions(danmu_messages)

        # 4. 负面反馈提取
        negative_feedback = self._extract_negative_feedback(danmu_messages)

        return {
            "意图列表": intents,
            "高频问题": high_freq_questions,
            "情绪统计": emotion_stats,
            "负面反馈": negative_feedback
        }

    def _recognize_intents(self, messages: List[str]) -> List[Dict]:
        """识别用户意图"""
        intent_results = []

        for msg in messages:
            msg = msg.strip()
            if not msg:
                continue

            # 匹配意图类型
            recognized_intents = []
            for intent_type, keywords in self.INTENT_KEYWORDS.items():
                if any(kw in msg for kw in keywords):
                    recognized_intents.append(intent_type)

            if recognized_intents:
                intent_results.append({
                    "消息": msg,
                    "意图": recognized_intents,
                    "优先级": self._calculate_intent_priority(recognized_intents)
                })

        return intent_results

    def _calculate_intent_priority(self, intents: List[str]) -> int:
        """计算意图优先级分数"""
        priority_map = {
            "购买意向": 90,
            "提问": 70,
            "负面": 85,
            "赞美": 40
        }

        # 返回最高优先级
        max_priority = 0
        for intent in intents:
            priority = priority_map.get(intent, 50)
            max_priority = max(max_priority, priority)

        return max_priority

    def _extract_high_freq_questions(self, messages: List[str]) -> List[Dict]:
        """提取高频问题"""
        # 提取问题关键词（2-6个字符的中文词）
        words = []
        for msg in messages:
            # 提取中文词组
            chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,6}', msg)
            words.extend(chinese_words)

        # 统计词频
        word_counts = Counter(words)

        # 取出现次数 >= 2 的高频词
        high_freq = [
            {"关键词": word, "出现次数": count, "优先级": min(100, 50 + count * 15)}
            for word, count in word_counts.items()
            if count >= 2
        ]

        # 按优先级排序
        high_freq.sort(key=lambda x: x["优先级"], reverse=True)

        return high_freq[:10]  # 最多返回10个

    def _count_emotions(self, messages: List[str]) -> Dict:
        """统计情绪"""
        emotion_count = {
            "提问": 0,
            "负面": 0,
            "购买意向": 0,
            "赞美": 0,
            "中性": 0
        }

        for msg in messages:
            msg = msg.strip()
            if not msg:
                continue

            matched = False
            for emotion_type, keywords in self.INTENT_KEYWORDS.items():
                if any(kw in msg for kw in keywords):
                    emotion_count[emotion_type] += 1
                    matched = True
                    break

            if not matched:
                emotion_count["中性"] += 1

        return emotion_count

    def _extract_negative_feedback(self, messages: List[str]) -> List[str]:
        """提取负面反馈"""
        negative_keywords = self.INTENT_KEYWORDS["负面"]
        negative_messages = []

        for msg in messages:
            msg = msg.strip()
            if any(kw in msg for kw in negative_keywords):
                negative_messages.append(msg)

        return negative_messages


# 模块实例
interaction_module = InteractionModule()


def analyze_danmu(danmu_messages: List[str]) -> Dict:
    """
    弹幕分析入口函数

    Args:
        danmu_messages: 弹幕消息列表

    Returns:
        分析结果
    """
    return interaction_module.analyze(danmu_messages)
