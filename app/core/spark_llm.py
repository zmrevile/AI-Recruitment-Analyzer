"""
星火大模型LangChain包装器
提供与ChatOpenAI兼容的接口
"""
import json
import hashlib
import hmac
import base64
import time
import websocket
from urllib.parse import urlparse, urlencode
from typing import List, Dict, Any, Optional
from langchain_core.language_models.llms import LLM
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import LLMResult, Generation
from pydantic import Field
import threading
import json
from app.utils.logger import spark_llm_logger


class SparkLLM(LLM):
    """星火大模型LangChain包装器"""
    
    app_id: str = Field(default="")
    api_key: str = Field(default="")
    api_secret: str = Field(default="")
    spark_url: str = Field(default="wss://spark-api.xf-yun.com/v4.0/chat")
    domain: str = Field(default="4.0Ultra")
    model_name: str = Field(default="Spark 4.0 Ultra")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=4096)
    response_text: str = Field(default="", exclude=True)
    response_complete: bool = Field(default=False, exclude=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @property
    def _llm_type(self) -> str:
        return "spark"
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        """调用星火大模型"""
        if not self.app_id or not self.api_key or not self.api_secret:
            raise ValueError("星火大模型密钥未配置，请提供 app_id、api_key 和 api_secret")
        
        return self._real_call(prompt)
    

    
    def _real_call(self, prompt: str) -> str:
        """真实调用星火大模型"""
        # 重置响应
        self.response_text = ""
        self.response_complete = False
        
        # 生成认证URL
        auth_url = self._create_auth_url()
        
        # 准备消息（改为正确的格式）
        messages = [{"role": "user", "content": prompt}]
        
        # 建立WebSocket连接
        ws = websocket.WebSocketApp(
            auth_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=lambda ws: self._on_open(ws, messages)
        )
        
        # 运行WebSocket
        ws.run_forever()
        
        if not self.response_text:
            raise RuntimeError("星火大模型调用失败：未收到有效响应")
        
        return self.response_text
    
    def _create_auth_url(self) -> str:
        """创建认证URL"""
        url = urlparse(self.spark_url)
        host = url.netloc
        path = url.path
        
        # 生成RFC1123格式的时间戳
        now = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
        
        # 拼接字符串
        signature_origin = f"host: {host}\ndate: {now}\nGET {path} HTTP/1.1"
        
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": now,
            "host": host
        }
        
        # 拼接鉴权参数，生成url
        url = self.spark_url + '?' + urlencode(v)
        return url
    
    def _on_message(self, ws, message):
        """处理WebSocket消息"""
        try:
            data = json.loads(message)
            code = data['header']['code']
            
            if code != 0:
                spark_llm_logger.error(f'请求错误: {code}, {data}')
                ws.close()
            else:
                choices = data["payload"]["choices"]
                status = choices["status"]
                
                # 检查是否有content字段
                if "text" in choices and len(choices["text"]) > 0:
                    text_item = choices["text"][0]
                    if "content" in text_item:
                        content = text_item["content"]
                        self.response_text += content
                    elif "reasoning_content" in text_item:
                        # 4.0 Ultra模型可能使用reasoning_content
                        content = text_item["reasoning_content"]
                        self.response_text += content
                
                if status == 2:
                    self.response_complete = True
                    ws.close()
        except Exception as e:
            spark_llm_logger.error(f"消息处理错误: {e}")
            ws.close()
    
    def _on_error(self, ws, error):
        """处理WebSocket错误"""
        spark_llm_logger.error(f"WebSocket错误: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket关闭"""
        self.response_complete = True
    
    def _on_open(self, ws, messages):
        """WebSocket打开，发送消息"""
        # 将字符串消息转换为官方要求的格式
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted_messages.append(msg)
            else:
                formatted_messages.append({
                    "role": "user",
                    "content": msg
                })
        
        # �� 生成唯一的会话ID，避免上下文记忆
        timestamp = int(time.time() * 1000)
        unique_uid = f"user_{timestamp}"
        unique_chat_id = f"chat_{timestamp}"
        
        data = {
            "header": {
                "app_id": self.app_id,
                "uid": unique_uid  # 🆕 使用唯一用户ID
            },
            "parameter": {
                "chat": {  # 4.0 Ultra模型使用"chat"
                    "domain": self.domain,
                    "chat_id": unique_chat_id,  # 🆕 使用唯一聊天ID
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
            },
            "payload": {
                "message": {
                    "text": formatted_messages
                }
            }
        }
        spark_llm_logger.debug(f"🔍 发送的数据格式: {json.dumps(data, ensure_ascii=False, indent=2)}")
        ws.send(json.dumps(data))
    
    def invoke(self, messages: List[BaseMessage], **kwargs) -> AIMessage:
        """兼容ChatOpenAI的invoke方法"""
        # 将消息转换为文本
        prompt = ""
        for msg in messages:
            if isinstance(msg, HumanMessage):
                prompt += f"Human: {msg.content}\n"
            elif isinstance(msg, SystemMessage):
                prompt += f"System: {msg.content}\n"
        
        # 调用模型
        response = self._call(prompt)
        
        # 返回AIMessage
        return AIMessage(content=response)


 