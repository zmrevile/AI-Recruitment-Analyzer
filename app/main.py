"""
AI智能面试系统 4.0 - 星火版
基于星火大模型的智能面试系统，支持匹配度分析和个性化问题生成
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.main import api_router
from app import __version__, __title__


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title=f"{__title__} - 星火版",
        description="基于星火大模型的智能面试系统，支持匹配度分析和个性化问题生成",
        version=__version__
    )

    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 包含API路由
    app.include_router(api_router)

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 