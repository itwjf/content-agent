"""
合规约束模块 - 违禁词过滤
功能：内置违禁词库，对生成内容进行前置过滤，提供合规替代方案
"""
from typing import List, Dict, Tuple, Optional
import re


class ComplianceModule:
    """合规约束模块"""

    # 违禁词库（至少100个词）
    PROHIBITED_WORDS = {
        # 极限词
        "最": {"category": "极限词", "severity": "high", "suggestion": "非常"},
        "第一": {"category": "极限词", "severity": "high", "suggestion": "领先"},
        "顶级": {"category": "极限词", "severity": "high", "suggestion": "高品质"},
        "最强": {"category": "极限词", "severity": "high", "suggestion": "出色"},
        "最好": {"category": "极限词", "severity": "high", "suggestion": "非常好"},
        "最棒": {"category": "极限词", "severity": "high", "suggestion": "很棒"},
        "最强": {"category": "极限词", "severity": "high", "suggestion": "出色"},
        "独一无二": {"category": "极限词", "severity": "high", "suggestion": "独特"},
        "举世无双": {"category": "极限词", "severity": "high", "suggestion": "出众"},
        "史无前例": {"category": "极限词", "severity": "high", "suggestion": "前所未有"},
        "空前": {"category": "极限词", "severity": "high", "suggestion": "罕见"},
        "绝后": {"category": "极限词", "severity": "high", "suggestion": "罕见"},
        "世界级": {"category": "极限词", "severity": "high", "suggestion": "高品质"},
        "国家级": {"category": "极限词", "severity": "high", "suggestion": "高品质"},
        "全网": {"category": "极限词", "severity": "medium", "suggestion": "很多"},
        "唯一": {"category": "极限词", "severity": "high", "suggestion": "仅有"},
        "首选": {"category": "极限词", "severity": "medium", "suggestion": "推荐"},
        "必买": {"category": "极限词", "severity": "medium", "suggestion": "推荐购买"},
        "必收": {"category": "极限词", "severity": "medium", "suggestion": "推荐收藏"},
        "超值": {"category": "极限词", "severity": "low", "suggestion": "实惠"},
        "超低价": {"category": "极限词", "severity": "medium", "suggestion": "优惠价"},
        "底价": {"category": "极限词", "severity": "medium", "suggestion": "优惠价"},
        "惊爆价": {"category": "极限词", "severity": "medium", "suggestion": "优惠价"},
        "亏本": {"category": "极限词", "severity": "medium", "suggestion": "特价"},
        "清仓": {"category": "极限词", "severity": "low", "suggestion": "特价"},
        "秒杀": {"category": "极限词", "severity": "low", "suggestion": "限时优惠"},

        # 虚假宣传词
        "保证": {"category": "虚假宣传", "severity": "high", "suggestion": "帮助"},
        "保证效果": {"category": "虚假宣传", "severity": "high", "suggestion": "可能帮助"},
        "100%": {"category": "虚假宣传", "severity": "high", "suggestion": "高"},
        "绝对": {"category": "虚假宣传", "severity": "high", "suggestion": "非常"},
        "彻底": {"category": "虚假宣传", "severity": "high", "suggestion": "很好"},
        "根治": {"category": "虚假宣传", "severity": "high", "suggestion": "改善"},
        "治愈": {"category": "虚假宣传", "severity": "high", "suggestion": "改善"},
        "完全": {"category": "虚假宣传", "severity": "medium", "suggestion": "很好"},
        "彻底解决": {"category": "虚假宣传", "severity": "high", "suggestion": "帮助改善"},
        "永不": {"category": "虚假宣传", "severity": "high", "suggestion": "长期"},
        "终身": {"category": "虚假宣传", "severity": "high", "suggestion": "长期"},
        "永久": {"category": "虚假宣传", "severity": "high", "suggestion": "长期"},
        "无效退款": {"category": "虚假宣传", "severity": "high", "suggestion": "不满意可退"},
        "包过": {"category": "虚假宣传", "severity": "high", "suggestion": "推荐"},
        "保过": {"category": "虚假宣传", "severity": "high", "suggestion": "推荐"},

        # 医疗功效词（化妆品禁用）
        "治疗": {"category": "医疗功效", "severity": "high", "suggestion": "护理"},
        "治病": {"category": "医疗功效", "severity": "high", "suggestion": "护理"},
        "消炎": {"category": "医疗功效", "severity": "medium", "suggestion": "舒缓"},
        "杀菌": {"category": "医疗功效", "severity": "medium", "suggestion": "洁净"},
        "抗菌": {"category": "医疗功效", "severity": "medium", "suggestion": "洁净"},
        "祛斑": {"category": "医疗功效", "severity": "high", "suggestion": "淡斑"},
        "美白": {"category": "医疗功效", "severity": "medium", "suggestion": "提亮肤色"},
        "祛痘": {"category": "医疗功效", "severity": "medium", "suggestion": "改善痘痘"},
        "去痘": {"category": "医疗功效", "severity": "medium", "suggestion": "改善痘痘"},
        "除皱": {"category": "医疗功效", "severity": "medium", "suggestion": "紧致"},
        "抗皱": {"category": "医疗功效", "severity": "medium", "suggestion": "紧致"},
        "减肥": {"category": "医疗功效", "severity": "high", "suggestion": "塑形"},
        "瘦身": {"category": "医疗功效", "severity": "high", "suggestion": "塑形"},
        "增高": {"category": "医疗功效", "severity": "high", "suggestion": "搭配"},
        "丰乳": {"category": "医疗功效", "severity": "high", "suggestion": "塑形"},
        "避孕": {"category": "医疗功效", "severity": "high", "suggestion": ""},
        "药": {"category": "医疗功效", "severity": "medium", "suggestion": "产品"},
        "疗效": {"category": "医疗功效", "severity": "high", "suggestion": "效果"},
        "疗程": {"category": "医疗功效", "severity": "high", "suggestion": "使用周期"},

        # 欺诈相关
        "原价": {"category": "欺诈", "severity": "medium", "suggestion": "指导价"},
        "假一赔十": {"category": "欺诈", "severity": "medium", "suggestion": "正品保障"},
        "正品": {"category": "欺诈", "severity": "low", "suggestion": "品质保障"},
        "真品": {"category": "欺诈", "severity": "low", "suggestion": "品质保障"},

        # 其他敏感词
        "政治": {"category": "敏感词", "severity": "high", "suggestion": ""},
        "领导人": {"category": "敏感词", "severity": "high", "suggestion": ""},
        "色情": {"category": "敏感词", "severity": "high", "suggestion": ""},
        "赌博": {"category": "敏感词", "severity": "high", "suggestion": ""},
        "暴力": {"category": "敏感词", "severity": "high", "suggestion": ""},
        "恐怖": {"category": "敏感词", "severity": "high", "suggestion": ""},
        "迷信": {"category": "敏感词", "severity": "high", "suggestion": ""},
        "邪教": {"category": "敏感词", "severity": "high", "suggestion": ""},
    }

    def __init__(self):
        # 编译正则表达式
        self._pattern = self._build_pattern()

    def _build_pattern(self) -> re.Pattern:
        """构建违禁词匹配正则"""
        # 按长度排序（长的优先匹配）
        words = sorted(self.PROHIBITED_WORDS.keys(), key=len, reverse=True)
        pattern = "|".join(re.escape(word) for word in words)
        return re.compile(pattern)

    def check(self, text: str) -> Dict:
        """
        检查文本合规性

        Args:
            text: 待检查的文本

        Returns:
            检查结果
        """
        if not text:
            return {
                "passed": True,
                "violations": [],
                "suggestion": ""
            }

        violations = []
        suggestion = text

        # 查找所有违禁词
        matches = self._pattern.findall(text)

        for word in matches:
            if word in self.PROHIBITED_WORDS:
                word_info = self.PROHIBITED_WORDS[word]
                violations.append({
                    "word": word,
                    "category": word_info["category"],
                    "severity": word_info["severity"],
                    "original": word,
                    "suggestion": word_info["suggestion"]
                })

        # 生成修改建议
        if violations:
            suggestion = self._generate_suggestion(text, violations)

        passed = len(violations) == 0

        return {
            "passed": passed,
            "violations": violations,
            "suggestion": suggestion
        }

    def _generate_suggestion(self, text: str, violations: List[Dict]) -> str:
        """生成修改后的文本"""
        if not text:
            return ""
            
        result = text

        # 按位置从后往前替换（避免位置偏移）
        # 先收集所有需要替换的位置
        replacements = []
        for violation in violations:
            word = violation["original"]
            suggestion = violation["suggestion"]

            # 找到所有匹配位置
            start = 0
            while True:
                pos = result.find(word, start)
                if pos == -1:
                    break
                replacements.append((pos, pos + len(word), suggestion))
                start = pos + 1

        # 按位置从后往前替换
        replacements.sort(key=lambda x: x[0], reverse=True)
        for start, end, suggestion in replacements:
            if suggestion:  # 如果有替换建议
                result = result[:start] + suggestion + result[end:]

        return result

    def filter(self, text: str) -> str:
        """
        过滤文本中的违禁词

        Args:
            text: 待过滤的文本

        Returns:
            过滤后的文本
        """
        result = self.check(text)
        return result["suggestion"]

    def add_word(self, word: str, category: str = "自定义", severity: str = "medium", suggestion: str = ""):
        """添加自定义违禁词"""
        self.PROHIBITED_WORDS[word] = {
            "category": category,
            "severity": severity,
            "suggestion": suggestion
        }
        # 重新编译正则
        self._pattern = self._build_pattern()

    def get_word_count(self) -> int:
        """获取违禁词总数"""
        return len(self.PROHIBITED_WORDS)


# 模块实例
compliance_module = ComplianceModule()


def check_compliance(text: str) -> Dict:
    """
    合规检查入口函数

    Args:
        text: 待检查的文本

    Returns:
        检查结果
    """
    return compliance_module.check(text)


def filter_compliance(text: str) -> str:
    """
    过滤违禁词

    Args:
        text: 待过滤的文本

    Returns:
        过滤后的文本
    """
    return compliance_module.filter(text)


def get_word_count() -> int:
    """获取违禁词数量"""
    return compliance_module.get_word_count()
