"""
AI智能面试系统 4.0 - 星火版
基于星火大模型的智能面试系统，支持匹配度分析和个性化问题生成
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.main import api_router
from app import __version__, __title__
from app.utils.logger import spark_embedding_logger


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

    # 启动事件：预加载embedding模型
    @app.on_event("startup")
    async def startup_event():
        """应用启动时预加载模型"""
        try:
            spark_embedding_logger.info("🚀 应用启动中...")
            
            # 预加载embedding模型
            from app.core.spark_embedding import preload_embeddings
            
            success = preload_embeddings()
            
            if success:
                spark_embedding_logger.info("🎉 应用启动完成，所有模型已预加载！")
            else:
                spark_embedding_logger.warning("⚠️ 应用启动完成，但embedding模型预加载失败")
            
        except Exception as e:
            spark_embedding_logger.error(f"❌ 应用启动过程中发生错误: {e}")
            # 不阻止应用启动，但记录错误
            import traceback
            spark_embedding_logger.error(f"详细错误: {traceback.format_exc()}")

    # 关闭事件：清理资源
    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭时清理资源"""
        try:
            spark_embedding_logger.info("🔄 应用关闭中，清理embedding缓存...")
            from app.core.spark_embedding import clear_embedding_cache
            clear_embedding_cache()
            spark_embedding_logger.info("✅ 资源清理完成")
        except Exception as e:
            spark_embedding_logger.error(f"❌ 资源清理失败: {e}")

    # 包含API路由
    app.include_router(api_router)

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 