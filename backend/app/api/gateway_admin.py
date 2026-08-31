"""
网关管理路由 - 适配器状态查询/启停开关/会话绑定
挂载前缀：/api/v1/gateway
"""
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.gateway import gateway_manager
from app.services.live_session_service import LiveSessionService
from app.services.director.scheduler import decision_scheduler

router = APIRouter()


class AdapterStartRequest(BaseModel):
    """场次启动适配器请求"""
    adapter_name: str = Field(..., description="适配器名称：mock/browser/douyin/taobao/kuaishou")
    options: dict = Field(default_factory=dict, description="适配器选项（mock: scenario/interval/loop）")


class AdapterStartResponse(BaseModel):
    """场次启动适配器响应"""
    session_id: int
    adapter_name: str
    status: dict


@router.get("/adapters", response_model=list[dict])
async def list_adapters():
    """查询全部适配器状态"""
    return gateway_manager.get_status()


@router.post("/adapters/{name}/enable", response_model=dict)
async def enable_adapter(name: str):
    """启用适配器（运行时开关）"""
    try:
        gateway_manager.set_enabled(name, True)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return gateway_manager.get_adapter(name).status_info()


@router.post("/adapters/{name}/disable", response_model=dict)
async def disable_adapter(name: str):
    """禁用适配器（若在运行中会先停止）"""
    try:
        adapter = gateway_manager.get_adapter(name)
        if not adapter:
            raise KeyError(f"适配器 {name} 不存在")
        if adapter.status == "running" and adapter._session_id:
            await gateway_manager.stop_for_session(adapter._session_id)
        gateway_manager.set_enabled(name, False)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return adapter.status_info()


@router.post("/sessions/{session_id}/start", response_model=AdapterStartResponse)
async def start_adapter_for_session(session_id: int, body: AdapterStartRequest, db: Session = Depends(get_db)):
    """为场次启动指定弹幕来源适配器（若已有运行中适配器则为切换）"""
    # 校验场次存在且未结束
    service = LiveSessionService(db)
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="场次不存在")
    if session.status == "ended":
        raise HTTPException(status_code=400, detail="场次已结束，不能启动弹幕源")

    try:
        status = await gateway_manager.start_for_session(session_id, body.adapter_name, body.options)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 联动启动决策循环（弹幕窗口 → 互动理解 → 导演脚本 → 落库 → WS推送）
    decision_scheduler.start(session_id, options=body.options)
    return AdapterStartResponse(session_id=session_id, adapter_name=body.adapter_name, status=status)


@router.post("/sessions/{session_id}/stop", response_model=dict)
async def stop_adapter_for_session(session_id: int):
    """停止场次的弹幕来源适配器与决策循环"""
    stopped = await gateway_manager.stop_for_session(session_id)
    await decision_scheduler.stop(session_id)
    return {"session_id": session_id, "stopped": stopped}


@router.post("/sessions/{session_id}/decide", response_model=dict)
async def decide_now(session_id: int, db: Session = Depends(get_db)):
    """立即触发一轮决策（使用当前窗口缓冲的弹幕，用于测试与手动兜底）"""
    service = LiveSessionService(db)
    if not service.get_session(session_id):
        raise HTTPException(status_code=404, detail="场次不存在")
    result = await decision_scheduler.decide_now(session_id)
    if result is None:
        return {"session_id": session_id, "produced": False,
                "message": "窗口缓冲无新弹幕或场次未开播"}
    return {"session_id": session_id, "produced": True, "script": result}
