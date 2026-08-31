"""
直播场次路由聚合
"""
from fastapi import APIRouter

from app.api.live_sessions import router as live_sessions_router

router = APIRouter()
router.include_router(live_sessions_router, prefix="/live", tags=["直播场次"])
