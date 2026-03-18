"""
Agent 决策中枢 - 整合所有模块
功能：接收多模块输入，进行优先级打分和决策融合，生成最终提词指令
"""
from typing import Dict, List, Optional
from app.services.modules.interaction_module import analyze_danmu
from app.services.modules.selling_point_module import generate_selling_points
from app.services.modules.compliance_module import check_compliance
from app.services.modules.structure_engine import get_current_stage, get_stage_transition_advice
from app.services.rag_service import rag_service


class DecisionAgent:
    """Agent 决策中枢"""

    # 优先级打分配置
    PRIORITY_SCORES = {
        # 弹幕触发
        "弹幕高频问题": 90,      # 弹幕重复提问 ≥2次
        "弹幕负面反馈": 85,      # 弹幕中有负面评价
        "弹幕购买意向": 88,      # 弹幕中有购买意向

        # 阶段触发
        "阶段切换": 70,          # 阶段自动切换
        "阶段提示": 60,          # 阶段内提示

        # 商品卖点
        "卖点匹配": 65,          # 卖点与问题匹配
        "普通卖点": 50,          # 普通卖点推送
    }

    def __init__(self):
        pass

    def decide(self, input_data: Dict) -> Dict:
        """
        Agent 核心决策

        Args:
            input_data: 完整的输入数据

        Returns:
            提词指令
        """
        # 1. 解析输入
        live_status = input_data.get("直播状态", {})
        danmu_data = input_data.get("弹幕数据", {})
        product_data = input_data.get("商品数据", {})
        backend_data = input_data.get("后台数据", {})

        # 2. 调用各模块
        # 2.1 互动理解模块
        danmu_result = analyze_danmu(danmu_data.get("最近30秒消息", []))

        # 2.2 卖点拆解模块
        # 提取高频问题
        user_questions = danmu_result.get("高频问题", [])

        # 2.3 搜索RAG知识库
        rag_context = ""
        if user_questions:
            # 把高频问题转为查询
            query_text = " ".join([q.get("关键词", "") for q in user_questions[:3]])
            rag_results = rag_service.search(
                collection_name="products",
                query=query_text,
                top_k=2
            )
            if rag_results:
                rag_context = "\n".join([r["text"] for r in rag_results])
                print(f"[RAG] 搜索到 {len(rag_results)} 条相关知识")

        # 2.4 卖点拆解模块
        selling_result = generate_selling_points(product_data, user_questions, rag_context)

        # 2.3 内容结构引擎
        current_stage_info = get_current_stage(
            current_time=live_status.get("已直播时长", 0),
            total_time=live_status.get("计划总时长", 3600),
            manual_stage=live_status.get("当前阶段")
        )

        # 2.4 阶段切换建议
        stage_advice = get_stage_transition_advice(
            current_stage=current_stage_info.get("当前阶段"),
            backend_data=backend_data
        )

        # 3. 优先级打分
        candidates = self._score_candidates(
            danmu_result=danmu_result,
            selling_result=selling_result,
            current_stage_info=current_stage_info,
            stage_advice=stage_advice,
            backend_data=backend_data
        )

        # 4. 选择最高优先级
        if not candidates:
            # 无触发项，使用默认话术
            final_instruction = self._generate_default_instruction(
                product_data, current_stage_info
            )
        else:
            # 选择最高分
            best_candidate = max(candidates, key=lambda x: x["总分"])
            final_instruction = best_candidate["提词内容"]

        # 5. 合规检查
        compliance_result = check_compliance(final_instruction.get("建议话术", ""))

        # 6. 构建最终输出
        output = {
            "提词指令": {
                "优先级": final_instruction.get("优先级", "中"),
                "建议话术": compliance_result.get("suggestion", final_instruction.get("建议话术", "")),
                "动作建议": final_instruction.get("动作建议", ""),
                "触发原因": final_instruction.get("触发原因", ""),
                "合规检查": "通过" if compliance_result.get("passed") else f"有{len(compliance_result.get('violations', []))}处需修改"
            }
        }

        # 如果有违规，添加警告
        if not compliance_result.get("passed"):
            output["提词指令"]["违规词"] = [
                v["word"] for v in compliance_result.get("violations", [])
            ]
            output["提词指令"]["修改建议"] = compliance_result.get("suggestion", "")

        return output

    def _score_candidates(
        self,
        danmu_result: Dict,
        selling_result: Dict,
        current_stage_info: Dict,
        stage_advice: Dict,
        backend_data: Dict
    ) -> List[Dict]:
        """对各模块输出进行优先级打分"""
        candidates = []

        # 1. 弹幕高频问题
        high_freq_questions = danmu_result.get("高频问题", [])
        for question in high_freq_questions:
            if question.get("出现次数", 0) >= 2:
                candidates.append({
                    "类型": "弹幕高频问题",
                    "触发原因": f"弹幕高频问题: {question['关键词']}",
                    "提词内容": {
                        "优先级": "高",
                        "建议话术": selling_result.get("生成话术", ""),
                        "动作建议": "回答弹幕问题",
                    },
                    "基础分": self.PRIORITY_SCORES["弹幕高频问题"],
                    "额外分": question.get("优先级", 0) - 50
                })

        # 2. 弹幕负面反馈
        negative_feedback = danmu_result.get("负面反馈", [])
        if negative_feedback:
            candidates.append({
                "类型": "弹幕负面反馈",
                "触发原因": "弹幕出现负面反馈",
                "提词内容": {
                    "优先级": "高",
                    "建议话术": self._generate_response_to_negative(negative_feedback[0], selling_result),
                    "动作建议": "正面回应用户顾虑",
                },
                "基础分": self.PRIORITY_SCORES["弹幕负面反馈"],
                "额外分": len(negative_feedback) * 5
            })

        # 3. 弹幕购买意向
        intents = danmu_result.get("意图列表", [])
        purchase_intents = [i for i in intents if "购买意向" in i.get("意图", [])]
        if purchase_intents:
            candidates.append({
                "类型": "弹幕购买意向",
                "触发原因": "弹幕出现购买意向",
                "提词内容": {
                    "优先级": "高",
                    "建议话术": "想要的宝宝们赶紧下单，优惠名额有限！",
                    "动作建议": "引导下单",
                },
                "基础分": self.PRIORITY_SCORES["弹幕购买意向"],
                "额外分": 0
            })

        # 4. 阶段切换建议
        if stage_advice.get("建议") and "准备进入" in stage_advice.get("建议", ""):
            next_stage = stage_advice.get("建议", "").replace("准备进入", "")
            candidates.append({
                "类型": "阶段切换",
                "触发原因": stage_advice.get("原因", ""),
                "提词内容": {
                    "优先级": "中",
                    "建议话术": self._get_stage_script(next_stage),
                    "动作建议": f"进入{next_stage}",
                },
                "基础分": self.PRIORITY_SCORES["阶段切换"],
                "额外分": 0
            })

        # 5. 卖点匹配
        matched_points = selling_result.get("匹配卖点", [])
        if matched_points:
            for point in matched_points:
                candidates.append({
                    "类型": "卖点匹配",
                    "触发原因": f"匹配用户问题: {point.get('问题', '')}",
                    "提词内容": {
                        "优先级": "中",
                        "建议话术": point.get("话术", ""),
                        "动作建议": "展示产品",
                    },
                    "基础分": self.PRIORITY_SCORES["卖点匹配"],
                    "额外分": point.get("优先级", 0) - 50
                })

        # 6. 计算总分并排序
        for candidate in candidates:
            candidate["总分"] = candidate["基础分"] + candidate["额外分"]

        candidates.sort(key=lambda x: x["总分"], reverse=True)

        return candidates

    def _generate_response_to_negative(self, negative_msg: str, selling_result: Dict) -> str:
        """生成回应负面反馈的话术"""
        # 简单规则匹配
        if "贵" in negative_msg:
            return "价格方面真的是全网最低了，性价比超高，买到就是赚到！"

        return "感谢您的反馈，我们一直致力于提供最好的产品和服务，有任何问题随时联系我们！"

    def _get_stage_script(self, stage: str) -> str:
        """获取阶段转换话术"""
        scripts = {
            "产品讲解期": "接下来让我们详细了解一下这款产品...",
            "促单期": "家人们，现在是最优惠的价格，错过不再有！",
            "问答互动期": "有任何问题欢迎在弹幕里问我！",
            "结尾期": "感谢家人们的支持，记得关注我们，下次直播再见！"
        }
        return scripts.get(stage, "让我们继续...")

    def _generate_default_instruction(
        self,
        product_data: Dict,
        current_stage_info: Dict
    ) -> Dict:
        """生成默认提词指令"""
        product_name = product_data.get("产品名称", "这款产品")
        current_stage = current_stage_info.get("当前阶段", "产品讲解期")

        return {
            "优先级": "低",
            "建议话术": f"欢迎来到直播间！今天给大家介绍{product_name}，{current_stage_info.get('阶段描述', '')}",
            "动作建议": "继续当前内容",
            "触发原因": "常规播报"
        }


# Agent 实例
decision_agent = DecisionAgent()


def agent_decide(input_data: Dict) -> Dict:
    """
    Agent 决策入口

    Args:
        input_data: 完整的输入数据

    Returns:
        提词指令
    """
    return decision_agent.decide(input_data)
