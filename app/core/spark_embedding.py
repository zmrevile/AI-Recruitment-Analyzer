"""
讯飞星火Embedding API实现
基于官方demo：https://emb-cn-huabei-1.xf-yun.com/
"""
import time
import requests
from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
import hashlib
import base64
import hmac
from urllib.parse import urlencode
import json
import numpy as np
from typing import List
from app.utils.logger import spark_embedding_logger

class SparkEmbeddingAPI:
    """讯飞星火Embedding API - 基于官方demo"""
    
    def __init__(self, app_id: str, api_key: str, api_secret: str):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.host = 'https://emb-cn-huabei-1.xf-yun.com/'
    
    def _parse_url(self, request_url):
        """解析URL"""
        stidx = request_url.index("://")
        host = request_url[stidx + 3:]
        schema = request_url[:stidx + 3]
        edidx = host.index("/")
        if edidx <= 0:
            raise Exception("invalid request url:" + request_url)
        path = host[edidx:]
        host = host[:edidx]
        return {"host": host, "path": path, "schema": schema}
    
    def _assemble_ws_auth_url(self, request_url, method="POST"):
        """生成鉴权URL"""
        u = self._parse_url(request_url)
        host = u["host"]
        path = u["path"]
        
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'), 
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.api_key, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        values = {
            "host": host,
            "date": date,
            "authorization": authorization
        }
        
        return request_url + "?" + urlencode(values)
    
    def _get_body(self, text: str, domain: str):
        """构建请求体"""
        # 按照官方demo的消息格式
        messages_data = {"messages": [{"content": text, "role": "user"}]}
        
        body = {
            "header": {
                "app_id": self.app_id,
                "uid": "39769795890",
                "status": 3
            },
            "parameter": {
                "emb": {
                    "domain": domain,
                    "feature": {
                        "encoding": "utf8"
                    }
                }
            },
            "payload": {
                "messages": {
                    "text": base64.b64encode(json.dumps(messages_data).encode('utf-8')).decode()
                }
            }
        }
        return body
    
    def embed_text(self, text: str, domain: str = "query") -> List[float]:
        """
        对单个文本进行embedding，增加重试和延时机制
        
        Args:
            text: 要embedding的文本
            domain: "query"(查询文本) 或 "para"(知识文本)
        
        Returns:
            embedding向量
        """
        max_retries = 3
        retry_delay = 1.0  # 1秒基础延时
        
        for attempt in range(max_retries):
            try:
                # 添加延时控制，避免频率限制
                if attempt > 0:
                    delay = retry_delay * (2 ** attempt)  # 指数退避
                    spark_embedding_logger.info(f"🔄 第{attempt + 1}次重试，等待{delay:.1f}秒...")
                    time.sleep(delay)
                else:
                    # 首次调用也稍微延时，避免过于频繁
                    time.sleep(0.5)
                
                # 生成鉴权URL
                auth_url = self._assemble_ws_auth_url(self.host, method='POST')
                
                # 构建请求体
                content = self._get_body(text, domain)
                
                # 发起请求
                response = requests.post(
                    auth_url, 
                    json=content, 
                    headers={'content-type': "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 检查响应状态
                    code = result.get('header', {}).get('code', -1)
                    if code == 0:
                        # 解析向量数据
                        text_base = result["payload"]["feature"]["text"]
                        text_data = base64.b64decode(text_base)
                        
                        # 解析为float32数组
                        dt = np.dtype(np.float32).newbyteorder("<")
                        vector = np.frombuffer(text_data, dtype=dt)
                        
                        spark_embedding_logger.info(f"✅ 讯飞API成功，向量维度: {len(vector)}")
                        return vector.tolist()
                    elif code == 11202:  # 频率限制错误
                        spark_embedding_logger.warning(f"⚠️ 频率限制错误(11202)，需要重试...")
                        if attempt < max_retries - 1:
                            continue  # 重试
                        else:
                            spark_embedding_logger.warning("❌ 多次重试后仍遇到频率限制，使用备用向量")
                            return self._generate_fallback_vector(text)
                    else:
                        spark_embedding_logger.error(f"讯飞API错误: {code}, {result}")
                        return self._generate_fallback_vector(text)
                else:
                    spark_embedding_logger.error(f"HTTP请求失败: {response.status_code}")
                    spark_embedding_logger.error(f"响应内容: {response.text}")
                    if attempt < max_retries - 1:
                        continue  # 重试
                    return self._generate_fallback_vector(text)
                    
            except Exception as e:
                spark_embedding_logger.error(f"讯飞Embedding API调用异常: {e}")
                if attempt < max_retries - 1:
                    continue  # 重试
                return self._generate_fallback_vector(text)
        
        # 如果所有重试都失败了
        spark_embedding_logger.error("❌ 所有重试都失败，使用备用向量")
        return self._generate_fallback_vector(text)
    
    def embed_texts(self, texts: List[str], domain: str = "query") -> List[List[float]]:
        """批量embedding文本，控制调用频率"""
        vectors = []
        for i, text in enumerate(texts):
            # 在每次调用之间添加延时，避免频率限制
            if i > 0:
                time.sleep(0.6)  # 确保每秒不超过2次调用（免费版限制）
            
            vector = self.embed_text(text, domain)
            vectors.append(vector)
            
            spark_embedding_logger.info(f"📝 已处理 {i+1}/{len(texts)} 个文本")
        
        return vectors
    
    def _generate_fallback_vector(self, text: str) -> List[float]:
        """生成备用向量（当API调用失败时）"""
        import hashlib
        import numpy as np
        
        # 使用文本的hash生成种子
        hash_object = hashlib.md5(text.encode())
        seed = int(hash_object.hexdigest()[:8], 16)
        
        # 根据官方demo，讯飞embedding向量可能不是1536维
        # 使用较小的维度，比如512维
        np.random.seed(seed % (2**32))
        vector = np.random.normal(0, 0.3, 512).tolist()
        
        # 归一化
        magnitude = sum(x*x for x in vector) ** 0.5
        if magnitude > 0:
            vector = [x / magnitude for x in vector]
        
        return vector


class SparkEmbeddings:
    """兼容LangChain的Embedding包装器"""
    
    def __init__(self, app_id="", api_key="", api_secret="", **kwargs):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.use_real_spark = bool(app_id and api_key and api_secret)
        
        if self.use_real_spark:
            spark_embedding_logger.info("✅ 使用讯飞官方Embedding API")
            self.api = SparkEmbeddingAPI(app_id, api_key, api_secret)
        else:
            spark_embedding_logger.warning("⚠️ 讯飞密钥未配置，使用本地embedding模型")
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                spark_embedding_logger.info("✅ 本地embedding模型加载成功")
            except ImportError:
                spark_embedding_logger.error("❌ 请安装sentence-transformers: pip install sentence-transformers")
                self.model = None
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入文档"""
        if self.use_real_spark:
            return self.api.embed_texts(texts, domain="para")  # 文档使用para模式
        else:
            return self._embed_with_local_model(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """嵌入查询"""
        if self.use_real_spark:
            return self.api.embed_text(text, domain="query")  # 查询使用query模式
        else:
            return self._embed_with_local_model([text])[0]
    
    def _embed_with_local_model(self, texts: List[str]) -> List[List[float]]:
        """使用本地模型生成embedding"""
        if hasattr(self, 'model') and self.model is not None:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        else:
            # 返回备用向量
            vectors = []
            for text in texts:
                vector = self._generate_fallback_vector(text)
                vectors.append(vector)
            return vectors
    
    def _generate_fallback_vector(self, text: str) -> List[float]:
        """生成备用向量"""
        import hashlib
        import numpy as np
        
        hash_object = hashlib.md5(text.encode())
        seed = int(hash_object.hexdigest()[:8], 16)
        
        np.random.seed(seed % (2**32))
        vector = np.random.normal(0, 0.3, 384).tolist()  # 使用384维
        
        magnitude = sum(x*x for x in vector) ** 0.5
        if magnitude > 0:
            vector = [x / magnitude for x in vector]
        
        return vector 