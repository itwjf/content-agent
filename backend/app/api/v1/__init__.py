"""
API v1 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.llm import call_llm

router = APIRouter()


# ==================== 请求/响应模型 ====================

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str


class LLMTestRequest(BaseModel):
    """LLM 测试请求"""
    prompt: str
    system_prompt: str = "你是一个helpful的AI助手"


class LLMTestResponse(BaseModel):
    """LLM 测试响应"""
    result: str
    model: str


# ==================== 路由 ====================

@router.get("/health", response_model=HealthResponse)
async def health():
    """健康检查接口"""
    return HealthResponse(status="ok", version="1.0.0")


@router.post("/llm/test", response_model=LLMTestResponse)
async def test_llm(request: LLMTestRequest):
    """测试 LLM 连接"""
    try:
        from app.core.config import get_settings
        settings = get_settings()

        result = call_llm(
            prompt=request.prompt,
            system_prompt=request.system_prompt
        )

        return LLMTestResponse(
            result=result,
            model=settings.llm_model
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 调用失败: {str(e)}")
