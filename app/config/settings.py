"""
配置文件 - 管理API密钥和LangSmith设置
"""
import os

# LangSmith 配置
LANGSMITH_CONFIG = {
    "LANGCHAIN_TRACING_V2": "true",
    "LANGCHAIN_API_KEY": "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",
    "LANGCHAIN_PROJECT": "interview-analysis"
}

# 星火大模型配置 - 使用Spark 4.0 Ultra版本
SPARK_CONFIG = {
    "app_id": "afcfb309",  # 填入你的星火应用ID，例如: "12345678"
    "api_key": "f7f0e3b8deb2d4540c87aa5a6145bc85",  # 填入你的星火API Key，例如: "abcd1234efgh5678"
    "api_secret": "NmIwNDM2ZWFkYTI0NzM5NWM0OWEyMTli",  # 填入你的星火API Secret，例如: "xyz9876543210"
    "spark_url": "wss://spark-api.xf-yun.com/v4.0/chat",  # Spark 4.0 Ultra接口地址
    "domain": "4.0Ultra",  # Spark 4.0 Ultra领域
    "model_name": "Spark 4.0 Ultra"  # 模型名称
}

# Embedding模型配置
class EmbeddingSettings:
    """Embedding模型配置类"""
    
    # 模型选择
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 默认模型，支持多语言
    # 其他可选模型:
    # "paraphrase-multilingual-MiniLM-L12-v2"  # 更好的多语言支持
    # "all-mpnet-base-v2"  # 更高质量但稍慢
    # "distiluse-base-multilingual-cased"  # 蒸馏版多语言模型
    
    # 批处理配置
    EMBEDDING_BATCH_SIZE = 32  # 批处理大小，根据内存调整
    
    # 缓存配置
    EMBEDDING_CACHE_SIZE = 1000  # 缓存条目数量
    
    # 性能配置
    ENABLE_GPU = True  # 是否启用GPU加速（需要CUDA）
    
    # 预处理配置
    MAX_TEXT_LENGTH = 512  # 最大文本长度，超出会截断
    MIN_TEXT_LENGTH = 1    # 最小文本长度
    
    @classmethod
    def get_model_options(cls):
        """获取可用的模型选项"""
        return {
            "all-MiniLM-L6-v2": {
                "name": "MiniLM-L6-v2",
                "description": "轻量级多语言模型，平衡性能和速度",
                "dimension": 384,
                "languages": ["中文", "英文", "多语言"]
            },
            "paraphrase-multilingual-MiniLM-L12-v2": {
                "name": "Multilingual-MiniLM-L12-v2", 
                "description": "更强的多语言理解能力",
                "dimension": 384,
                "languages": ["中文", "英文", "多语言"]
            },
            "all-mpnet-base-v2": {
                "name": "MPNet-Base-v2",
                "description": "高质量英文模型",
                "dimension": 768,
                "languages": ["英文"]
            }
        }

# 创建全局配置实例
settings = EmbeddingSettings()

def get_spark_config():
    """获取星火大模型配置（用于LLM，不含embedding）"""
    return SPARK_CONFIG

def setup_langsmith():
    """设置LangSmith环境变量"""
    for key, value in LANGSMITH_CONFIG.items():
        os.environ[key] = value
    print("✅ LangSmith追踪已启用")
    print(f"📊 项目名称: {LANGSMITH_CONFIG['LANGCHAIN_PROJECT']}")
    print(f"🔗 访问 https://smith.langchain.com/ 查看追踪数据")

def get_openai_key():
    """为了兼容性保留，实际返回空字符串"""
    return ""

def print_embedding_config():
    """打印embedding配置信息"""
    print("\n🔧 Embedding配置信息:")
    print(f"📦 模型名称: {settings.EMBEDDING_MODEL}")
    print(f"📊 批处理大小: {settings.EMBEDDING_BATCH_SIZE}")
    print(f"💾 缓存大小: {settings.EMBEDDING_CACHE_SIZE}")
    print(f"🚀 GPU加速: {'启用' if settings.ENABLE_GPU else '禁用'}")
    print(f"📏 文本长度限制: {settings.MIN_TEXT_LENGTH}-{settings.MAX_TEXT_LENGTH}")

if __name__ == "__main__":
    setup_langsmith()
    print(f"星火大模型配置已加载: {SPARK_CONFIG['model_name']}")
    print_embedding_config() 