"""
LLM 客户端配置
"""
from openai import OpenAI
from app.core.config import get_settings

settings = get_settings()


def get_llm_client() -> OpenAI:
    """获取 LLM 客户端"""
    return OpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout=60.0
    )


def call_llm(prompt: str, system_prompt: str = None) -> str:
    """
    调用 LLM 生成回复

    Args:
        prompt: 用户提示
        system_prompt: 系统提示（可选）

    Returns:
        LLM 生成的文本
    """
    # 检查 API Key 是否设置
    if not settings.llm_api_key or settings.llm_api_key == "your_api_key_here":
        print("[LLM] API Key 未设置，使用基础话术")
        raise Exception("API Key 未设置，请在 .env 文件中配置 LLM_API_KEY")
    
    client = get_llm_client()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )

    content = response.choices[0].message.content
    return content if content else ""
