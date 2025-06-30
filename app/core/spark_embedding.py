#!/usr/bin/env python3
"""
本地Embedding服务
使用sentence-transformers提供文本向量化功能
"""

import numpy as np
from typing import List
from app.utils.logger import spark_embedding_logger


class LocalEmbeddings:
    """本地Embedding服务"""
    
    def __init__(self):
        """初始化本地Embedding服务"""
        self.local_model = None
        self._init_local_model()
    
    def _init_local_model(self):
        """初始化本地embedding模型"""
        try:
            from sentence_transformers import SentenceTransformer
            # 使用适合多语言的模型
            self.local_model = SentenceTransformer('all-MiniLM-L6-v2')
            spark_embedding_logger.info("✅ 本地embedding模型加载成功")
        except ImportError:
            spark_embedding_logger.error("❌ sentence-transformers未安装，请安装：pip install sentence-transformers")
            raise
        except Exception as e:
            spark_embedding_logger.error(f"❌ 本地模型加载失败: {e}")
            raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入文档"""
        return self._embed_with_local_model(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """嵌入查询"""
        return self._embed_with_local_model([text])[0]
    
    def _embed_with_local_model(self, texts: List[str]) -> List[List[float]]:
        """使用本地模型生成embedding"""
        if self.local_model is not None:
            embeddings = self.local_model.encode(texts)
            return embeddings.tolist()
        else:
            spark_embedding_logger.error("❌ 本地模型未初始化")
            # 作为最后的fallback
            return [self._generate_fallback_vector(text) for text in texts]
    
    def _generate_fallback_vector(self, text: str, dimension: int = 384) -> List[float]:
        """生成备用向量"""
        text_hash = hash(text)
        np.random.seed(abs(text_hash) % (2**32))
        vector = np.random.randn(dimension)
        vector = vector / np.linalg.norm(vector)
        return vector.tolist()


# 向后兼容 - 重命名但保持接口一致
SparkEmbeddings = LocalEmbeddings

def get_embeddings():
    """获取embedding实例"""
    return LocalEmbeddings() 