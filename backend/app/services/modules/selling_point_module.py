"""
卖点拆解模块 - 商品参数转化为利益点
功能：将产品参数转化为利益点，结合用户问题推送最匹配卖点
"""
from typing import List, Dict, Optional
from app.core.llm import call_llm


class SellingPointModule:
    """卖点拆解模块"""

    # 功效到利益点的映射
    EFFECT_TO_BENEFIT = {
        "控油": ["减少皮肤油光", "保持妆容持久", "告别大油田"],
        "修护": ["改善肌肤问题", "强化皮肤屏障", "肌肤焕新"],
        "保湿": ["深层补水", "锁住水分", "水润一整天"],
        "美白": ["提亮肤色", "淡化色斑", "焕白肌肤"],
        "抗衰老": ["紧致肌肤", "减少细纹", "逆龄生长"],
        "防晒": ["隔离紫外线", "防止晒伤", "防晒伤"],
        "祛痘": ["消炎祛痘", "净化毛孔", "告别痘痘"],
        "敏感": ["温和不刺激", "舒缓肌肤", "适合敏感肌"],
    }

    # 成分到功效的映射
    INGREDIENT_TO_EFFECT = {
        "水杨酸": "控油、祛痘",
        "烟酰胺": "美白、提亮",
        "透明质酸": "保湿、补水",
        "维生素C": "美白、抗氧化",
        "视黄醇": "抗衰老",
        "神经酰胺": "修护、保湿",
        "积雪草": "舒缓、修护",
        "果酸": "去角质、美白",
        "氨基酸": "温和清洁",
        "胶原蛋白": "紧致、抗衰老",
    }

    def __init__(self):
        pass

    def generate_selling_points(
        self,
        product_data: Dict,
        user_questions: List[Dict] = None,
        rag_context: str = ""
    ) -> Dict:
        """
        生成卖点话术

        Args:
            product_data: 商品数据
            user_questions: 用户问题列表（可选）
            rag_context: RAG知识库检索结果（可选）

        Returns:
            卖点结果
        """
        # 1. 提取商品卖点
        product_selling_points = self._extract_product_selling_points(product_data)

        # 2. 匹配用户问题
        matched_points = []
        if user_questions:
            matched_points = self._match_questions_to_points(
                user_questions,
                product_selling_points,
                product_data
            )

        # 3. 生成话术
        script = self._generate_script(product_data, matched_points, rag_context)

        return {
            "商品卖点": product_selling_points,
            "匹配卖点": matched_points,
            "生成话术": script
        }

    def _extract_product_selling_points(self, product_data: Dict) -> List[Dict]:
        """提取商品卖点"""
        points = []

        # 从功效中提取卖点
        effects = product_data.get("功效", [])
        for effect in effects:
            benefit = self.EFFECT_TO_BENEFIT.get(effect, [effect])
            points.append({
                "类型": "功效",
                "关键词": effect,
                "利益点": benefit if isinstance(benefit, list) else [benefit]
            })

        # 从成分中提取卖点
        ingredients = product_data.get("成分", [])
        for ingredient in ingredients:
            effect = self.INGREDIENT_TO_EFFECT.get(ingredient, "")
            points.append({
                "类型": "成分",
                "关键词": ingredient,
                "关联功效": effect
            })

        # 从规格/价格中提取卖点
        price = product_data.get("价格", 0)
        original_price = product_data.get("原价")
        if original_price and original_price > price:
            discount = (original_price - price) / original_price * 100
            points.append({
                "类型": "价格",
                "关键词": f"{int(discount)}折",
                "利益点": [f"省{original_price - price}元", "限时优惠"]
            })

        return points

    def _match_questions_to_points(
        self,
        questions: List[Dict],
        selling_points: List[Dict],
        product_data: Dict
    ) -> List[Dict]:
        """匹配用户问题与商品卖点"""
        matched = []

        for question in questions:
            question_text = question.get("关键词", "")
            question_priority = question.get("优先级", 50)

            # 匹配卖点
            for point in selling_points:
                point_keywords = point.get("利益点", []) + [point.get("关键词", "")]
                point_keywords_str = "".join([str(kw) for kw in point_keywords])
                point_type = point.get("类型", "")

                # 检查问题是否与卖点相关
                # 1. 完全包含匹配
                # 2. 关键词重叠匹配（如"油皮"匹配"控油"中的"油"字）
                is_match = False
                for kw in point_keywords:
                    kw = str(kw)
                    # 双向包含检查
                    if kw in question_text or question_text in kw:
                        is_match = True
                        break
                    # 关键词重叠检查（至少有一个中文字符相同）
                    common_chars = set(kw) & set(question_text)
                    if len(common_chars) >= 1 and len(kw) <= 6:
                        is_match = True
                        break

                if is_match:
                    matched.append({
                        "问题": question_text,
                        "匹配卖点": point,
                        "匹配类型": point_type,
                        "优先级": question_priority,
                        "话术": self._generate_point_script(
                            question_text,
                            point,
                            product_data
                        )
                    })
                    break

        # 按优先级排序
        matched.sort(key=lambda x: x["优先级"], reverse=True)
        return matched

    def _generate_point_script(
        self,
        question: str,
        point: Dict,
        product_data: Dict
    ) -> str:
        """为单个卖点生成话术"""
        product_name = product_data.get("产品名称", "这款产品")

        point_type = point.get("类型", "")
        keyword = point.get("关键词", "")

        if point_type == "功效":
            benefits = point.get("利益点", [])
            benefit = benefits[0] if benefits else keyword
            return f"关于{question}，{product_name}添加了{keyword}成分，{benefit}，非常适合你！"

        elif point_type == "成分":
            effect = point.get("关联功效", "")
            return f"{question}的问题，{product_name}含有{keyword}成分，{effect}，放心使用！"

        elif point_type == "价格":
            benefits = point.get("利益点", [])
            benefit = benefits[0] if benefits else ""
            return f"价格方面真的非常实惠，{benefit}，错过不再有！"

        return f"{product_name}正好满足你的{question}需求！"

    def _generate_script(
        self,
        product_data: Dict,
        matched_points: List[Dict] = None,
        rag_context: str = ""
    ) -> str:
        """生成完整话术（优先调用 LLM，失败时降级为基础话术）"""
        product_name = product_data.get("产品名称", "这款产品")
        effects = product_data.get("功效", [])
        price = product_data.get("价格", 0)

        # 基础话术（兜底）
        base_script = f"欢迎来到直播间！今天给大家介绍{product_name}，"
        if effects:
            effect_str = "、".join(effects[:3])
            base_script += f"具有{effect_str}等多重功效，"
        base_script += f"价格只需要{price}元，性价比非常高！"

        # 无论是否有匹配卖点，都尝试调用 LLM 生成话术
        try:
            prompt = self._build_llm_prompt(product_data, matched_points or [], rag_context)
            print(f"[LLM] 开始调用，prompt 长度: {len(prompt)}")
            llm_script = call_llm(
                prompt=prompt,
                system_prompt="你是一个专业的直播主播，擅长根据用户问题生成针对性的产品话术。话术要自然、亲切、有说服力，50-100字。"
            )
            print(f"[LLM] 调用成功，返回长度: {len(llm_script)}")
            return llm_script
        except Exception as e:
            print(f"[LLM] 调用失败，降级为基础话术: {e}")
            return base_script

        return base_script

    def _build_llm_prompt(self, product_data: Dict, matched_points: List[Dict], rag_context: str = "") -> str:
        """构建 LLM 生成话术的 prompt"""
        product_name = product_data.get("产品名称", "")
        price = product_data.get("价格", 0)
        effects = product_data.get("功效", [])
        ingredients = product_data.get("成分", [])

        # 提取问题
        questions = [p["问题"] for p in matched_points[:3]]
        questions_str = "、".join(questions) if questions else "无"

        # 添加RAG知识库内容
        rag_section = f"\n\n参考知识库内容：\n{rag_context}" if rag_context else ""

        prompt = f"""
请为主播生成一段直播话术。

产品信息：
- 产品名称：{product_name}
- 价格：{price}元
- 功效：{", ".join(effects)}
- 成分：{", ".join(ingredients)}

用户高频问题：{questions_str}
{rag_section}

要求：
1. 话术要自然亲切，像正常主播说话
2. 要回答用户的问题
3. 长度控制在50-100字
4. 不要包含违禁词

直接输出话术，不要其他内容。
"""
        return prompt


# 模块实例
selling_point_module = SellingPointModule()


def generate_selling_points(
    product_data: Dict,
    user_questions: List[Dict] = None
) -> Dict:
    """
    卖点生成入口函数

    Args:
        product_data: 商品数据
        user_questions: 用户问题列表

    Returns:
        卖点结果
    """
    return selling_point_module.generate_selling_points(product_data, user_questions)
