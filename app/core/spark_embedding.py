#!/usr/bin/env python3
"""
本地Embedding服务
使用sentence-transformers提供文本向量化功能
支持缓存、批处理、GPU加速等优化功能
"""

import numpy as np
import hashlib
import time
import torch
from typing import List, Optional, Dict, Union
from functools import lru_cache
from threading import Lock
from app.utils.logger import spark_embedding_logger
from app.config.settings import settings


class LocalEmbeddings:
    """本地Embedding服务 - 优化版"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LocalEmbeddings, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化本地Embedding服务"""
        if hasattr(self, '_initialized'):
            return
            
        self.local_model = None
        self.device = self._get_optimal_device()
        self.model_name = getattr(settings, 'EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        self.batch_size = getattr(settings, 'EMBEDDING_BATCH_SIZE', 32)
        self.cache_size = getattr(settings, 'EMBEDDING_CACHE_SIZE', 1000)
        self.dimension = 384  # 默认维度
        
        # 性能统计
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'total_time': 0.0,
            'avg_time': 0.0
        }
        
        self._text_cache: Dict[str, List[float]] = {}
        self._cache_lock = Lock()
        
        self._init_local_model()
        self._initialized = True
    
    def _get_optimal_device(self) -> str:
        """获取最优设备"""
        if torch.cuda.is_available():
            device = 'cuda'
            spark_embedding_logger.info(f"🚀 使用GPU加速: {torch.cuda.get_device_name()}")
        else:
            device = 'cpu'
            spark_embedding_logger.info("💻 使用CPU计算")
        return device
    
    def _init_local_model(self):
        """初始化本地embedding模型"""
        try:
            from sentence_transformers import SentenceTransformer
            
            spark_embedding_logger.info(f"🔄 加载embedding模型: {self.model_name}")
            self.local_model = SentenceTransformer(self.model_name, device=self.device)
            
            # 获取实际向量维度
            self.dimension = self.local_model.get_sentence_embedding_dimension()
            
            spark_embedding_logger.info(f"✅ 本地embedding模型加载成功 (维度: {self.dimension}, 设备: {self.device})")
            
        except ImportError:
            spark_embedding_logger.error("❌ sentence-transformers未安装，请安装：pip install sentence-transformers")
            raise
        except Exception as e:
            spark_embedding_logger.error(f"❌ 本地模型加载失败: {e}")
            raise
    
    def _get_text_hash(self, text: str) -> str:
        """生成文本哈希用于缓存"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _get_from_cache(self, text: str) -> Optional[List[float]]:
        """从缓存获取embedding"""
        text_hash = self._get_text_hash(text)
        with self._cache_lock:
            return self._text_cache.get(text_hash)
    
    def _save_to_cache(self, text: str, embedding: List[float]):
        """保存embedding到缓存"""
        text_hash = self._get_text_hash(text)
        with self._cache_lock:
            # 简单的LRU实现
            if len(self._text_cache) >= self.cache_size:
                # 删除最旧的一个
                oldest_key = next(iter(self._text_cache))
                del self._text_cache[oldest_key]
            
            self._text_cache[text_hash] = embedding
    
    def _preprocess_text(self, text: str) -> str:
        """文本预处理"""
        if not text or not text.strip():
            return ""
        
        # 基本清理
        text = text.strip()
        # 移除过多的空白字符
        text = ' '.join(text.split())
        
        return text
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入文档 - 批处理优化版"""
        start_time = time.time()
        
        if not texts:
            return []
        
        # 预处理文本
        processed_texts = [self._preprocess_text(text) for text in texts]
        
        # 检查缓存
        results = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(processed_texts):
            cached_embedding = self._get_from_cache(text)
            if cached_embedding is not None:
                results.append((i, cached_embedding))
                self.stats['cache_hits'] += 1
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # 对未缓存的文本进行批处理
        if uncached_texts:
            uncached_embeddings = self._embed_with_local_model(uncached_texts)
            
            # 保存到缓存并添加到结果
            for idx, (original_idx, embedding) in enumerate(zip(uncached_indices, uncached_embeddings)):
                self._save_to_cache(processed_texts[original_idx], embedding)
                results.append((original_idx, embedding))
        
        # 按原始顺序排序
        results.sort(key=lambda x: x[0])
        final_results = [embedding for _, embedding in results]
        
        # 更新统计
        elapsed_time = time.time() - start_time
        self._update_stats(len(texts), elapsed_time)
        
        return final_results
    
    def embed_query(self, text: str) -> List[float]:
        """嵌入查询"""
        return self.embed_documents([text])[0]
    
    def _embed_with_local_model(self, texts: List[str]) -> List[List[float]]:
        """使用本地模型生成embedding - 批处理版"""
        if not texts:
            return []
            
        if self.local_model is not None:
            try:
                # 分批处理大量文本
                all_embeddings = []
                
                for i in range(0, len(texts), self.batch_size):
                    batch_texts = texts[i:i + self.batch_size]
                    batch_embeddings = self.local_model.encode(
                        batch_texts,
                        convert_to_tensor=False,
                        show_progress_bar=False,
                        batch_size=min(self.batch_size, len(batch_texts))
                    )
                    all_embeddings.extend(batch_embeddings.tolist())
                
                return all_embeddings
                
            except Exception as e:
                spark_embedding_logger.error(f"❌ embedding生成失败: {e}")
                return [self._generate_fallback_vector(text) for text in texts]
        else:
            spark_embedding_logger.error("❌ 本地模型未初始化")
            return [self._generate_fallback_vector(text) for text in texts]
    
    def _generate_fallback_vector(self, text: str) -> List[float]:
        """生成备用向量 - 改进版"""
        if not text:
            text = "empty_text"
            
        # 使用更稳定的哈希方法
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        seed = int(text_hash[:8], 16) % (2**32)
        
        np.random.seed(seed)
        vector = np.random.randn(self.dimension)
        vector = vector / np.linalg.norm(vector)
        
        return vector.tolist()
    
    def _update_stats(self, num_texts: int, elapsed_time: float):
        """更新性能统计"""
        self.stats['total_requests'] += num_texts
        self.stats['total_time'] += elapsed_time
        self.stats['avg_time'] = self.stats['total_time'] / max(self.stats['total_requests'], 1)
    
    def get_stats(self) -> Dict:
        """获取性能统计"""
        cache_hit_rate = (self.stats['cache_hits'] / max(self.stats['total_requests'], 1)) * 100
        
        return {
            **self.stats,
            'cache_hit_rate': f"{cache_hit_rate:.2f}%",
            'cache_size': len(self._text_cache),
            'model_name': self.model_name,
            'device': self.device,
            'dimension': self.dimension
        }
    
    def clear_cache(self):
        """清空缓存"""
        with self._cache_lock:
            self._text_cache.clear()
        spark_embedding_logger.info("🧹 embedding缓存已清空")
    
    def warmup(self):
        """模型预热"""
        if self.local_model:
            spark_embedding_logger.info("🔥 开始模型预热...")
            dummy_texts = ["预热文本", "warmup text", "模型初始化"]
            self.embed_documents(dummy_texts)
            spark_embedding_logger.info("✅ 模型预热完成")


# 向后兼容 - 重命名但保持接口一致
SparkEmbeddings = LocalEmbeddings

# 全局实例
_global_embeddings = None

def get_embeddings() -> LocalEmbeddings:
    """获取embedding实例 - 单例模式"""
    global _global_embeddings
    if _global_embeddings is None:
        _global_embeddings = LocalEmbeddings()
    return _global_embeddings


# 便捷函数
def embed_text(text: str) -> List[float]:
    """快速嵌入单个文本"""
    return get_embeddings().embed_query(text)

def embed_texts(texts: List[str]) -> List[List[float]]:
    """快速嵌入多个文本"""
    return get_embeddings().embed_documents(texts)

def get_embedding_stats() -> Dict:
    """获取embedding性能统计"""
    return get_embeddings().get_stats()

def clear_embedding_cache():
    """清空embedding缓存"""
    get_embeddings().clear_cache() 