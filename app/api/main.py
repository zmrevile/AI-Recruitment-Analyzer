"""
主API路由汇总
"""
from fastapi import APIRouter
from app.api import job, resume, match, interview
from datetime import datetime


# 创建主路由器
api_router = APIRouter()

# 包含所有子路由
api_router.include_router(job.router)
api_router.include_router(resume.router)
api_router.include_router(match.router)
api_router.include_router(interview.router)


@api_router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "4.0.0"
    } 