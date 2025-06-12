"""
面试相关的数据模型
"""
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class InterviewMessage(BaseModel):
    """面试消息模型"""
    message: str
    session_id: Optional[str] = None


class InterviewResponse(BaseModel):
    """面试响应模型"""
    question: str
    session_id: str
    candidate_info: Dict
    question_round: int
    is_follow_up: bool = False


class InterviewSession:
    """面试会话类"""
    def __init__(self, session_id: str, candidate_info: Dict):
        self.session_id = session_id
        self.candidate_info = candidate_info
        self.conversation_history = []
        self.question_count = 0
        self.created_at = datetime.now()
        self.follow_up_count = 0  # 当前话题的连续追问次数
        self.last_topic = ""      # 上一个话题，用于判断是否换话题 