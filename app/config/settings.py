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
    "app_id": "",  # 填入你的星火应用ID，例如: "12345678"
    "api_key": "",  # 填入你的星火API Key，例如: "abcd1234efgh5678"
    "api_secret": "",  # 填入你的星火API Secret，例如: "xyz9876543210"
    "spark_url": "wss://spark-api.xf-yun.com/v4.0/chat",  # Spark 4.0 Ultra接口地址
    "domain": "4.0Ultra",  # Spark 4.0 Ultra领域
    "model_name": "Spark 4.0 Ultra"  # 模型名称
}

def setup_langsmith():
    """设置LangSmith环境变量"""
    for key, value in LANGSMITH_CONFIG.items():
        os.environ[key] = value
    print("✅ LangSmith追踪已启用")
    print(f"📊 项目名称: {LANGSMITH_CONFIG['LANGCHAIN_PROJECT']}")
    print(f"🔗 访问 https://smith.langchain.com/ 查看追踪数据")

def get_spark_config():
    """获取星火大模型配置"""  
    return SPARK_CONFIG

def get_openai_key():
    """为了兼容性保留，实际返回空字符串"""
    return ""

if __name__ == "__main__":
    setup_langsmith()
    print(f"星火大模型配置已加载: {SPARK_CONFIG['model_name']}") 