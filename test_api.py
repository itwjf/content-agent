#!/usr/bin/env python3
"""
测试 ContentAgent API 的脚本
"""
import requests
import json

# API 基础URL
BASE_URL = "http://localhost:8000/api/v1"

def test_llm():
    """测试LLM连接"""
    print("=== 测试LLM连接 ===")
    url = f"{BASE_URL}/llm/test"
    data = {
        "prompt": "测试LLM连接",
        "system_prompt": "你是一个helpful的AI助手"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"LLM响应: {result.get('result', '无响应')}")
        print(f"使用模型: {result.get('model', '未知')}")
        return True
    except Exception as e:
        print(f"LLM测试失败: {e}")
        return False

def test_agent_decide():
    """测试Agent决策功能"""
    print("\n=== 测试Agent决策功能 ===")
    url = f"{BASE_URL}/agent/decide"
    
    # 测试数据
    data = {
        "直播状态": {
            "当前阶段": "产品讲解期",
            "已直播时长": 900,
            "计划总时长": 3600
        },
        "弹幕数据": {
            "最近30秒消息": ["油皮能用吗？", "价格太贵了", "油皮能用吗？"]
        },
        "商品数据": {
            "sku_id": "12345",
            "产品名称": "控油修护精华液",
            "价格": 350,
            "成分": ["水杨酸", "烟酰胺"],
            "功效": ["控油", "修护"]
        },
        "后台数据": {
            "在线人数": 1250
        }
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("=== Agent决策结果 ===")
            print(f"优先级: {result.get('提词指令', {}).get('优先级', '未知')}")
            print(f"建议话术: {result.get('提词指令', {}).get('建议话术', '无')}")
            print(f"动作建议: {result.get('提词指令', {}).get('动作建议', '无')}")
            print(f"触发原因: {result.get('提词指令', {}).get('触发原因', '无')}")
            print(f"合规检查: {result.get('提词指令', {}).get('合规检查', '未知')}")
            return True
        else:
            print(f"Agent决策失败: {response.text}")
            return False
    except Exception as e:
        print(f"Agent决策测试失败: {e}")
        return False

def test_compliance():
    """测试合规检查功能"""
    print("\n=== 测试合规检查功能 ===")
    url = f"{BASE_URL}/compliance/check"
    data = {
        "text": "这款产品是最好的，保证100%有效，全网最低价"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"合规检查通过: {result.get('passed', False)}")
        print(f"违规词: {result.get('violations', [])}")
        print(f"修改建议: {result.get('suggestion', '无')}")
        return True
    except Exception as e:
        print(f"合规检查测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试ContentAgent API...")
    
    # 测试健康检查
    try:
        health_response = requests.get("http://localhost:8000/health")
        if health_response.status_code == 200:
            print("✅ 服务健康检查通过")
        else:
            print("❌ 服务健康检查失败")
            return
    except Exception as e:
        print(f"❌ 无法连接服务: {e}")
        return
    
    # 运行各项测试
    llm_ok = test_llm()
    agent_ok = test_agent_decide()
    compliance_ok = test_compliance()
    
    print(f"\n=== 测试总结 ===")
    print(f"LLM连接: {'✅' if llm_ok else '❌'}")
    print(f"Agent决策: {'✅' if agent_ok else '❌'}")
    print(f"合规检查: {'✅' if compliance_ok else '❌'}")
    
    if llm_ok and agent_ok and compliance_ok:
        print("🎉 所有测试通过！系统运行正常")
    else:
        print("⚠️  部分功能存在问题，请检查日志")

if __name__ == "__main__":
    main()