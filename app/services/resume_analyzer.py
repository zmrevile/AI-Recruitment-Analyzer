"""
简历分析器
"""
import os
import fitz
import time
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.spark_llm import SparkLLM
from app.core.spark_embedding import get_embeddings
from langchain_core.messages import HumanMessage
from langchain_community.vectorstores import Chroma
from typing import Dict, List
import json
from app.utils.logger import resume_analyzer_logger

class ResumeAnalyzer:
    def __init__(self, spark_config: Dict):
        self.embeddings = get_embeddings()  # 使用优化后的单例模式
        self.llm = SparkLLM(
            app_id=spark_config.get("app_id", ""),
            api_key=spark_config.get("api_key", ""),
            api_secret=spark_config.get("api_secret", ""),
            temperature=0.3
        )
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.vector_store = None
        self.resume_content = ""
        self.candidate_info = {}
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """从PDF提取文本"""
        try:
            doc = fitz.open(pdf_path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            return text
        except Exception as e:
            resume_analyzer_logger.error(f"PDF提取失败: {e}")
            return ""
    
    def analyze_resume_structure(self, text: str) -> Dict:
        """分析简历结构"""
        prompt = f"""
分析简历并以JSON返回：
简历文本：{text}

格式：
{{
    "name": "姓名",
    "position": "目标职位", 
    "education": "教育背景",
    "experience": "工作经验",
    "skills": "技能列表",
    "projects": [{{"name": "项目名", "description": "描述", "tech_stack": "技术栈", "role": "角色", "achievements": "成果", "duration": "时长"}}],
    "contact": "联系方式"
}}

如信息不存在则填"未提及"。
"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            try:
                return json.loads(response.content)
            except:
                return {
                    "name": "候选人", "position": "未明确", "education": "未分析",
                    "experience": "未分析", "skills": "未分析",
                    "projects": [{"name": "需要了解", "description": "解析失败", "tech_stack": "未明确", 
                                "role": "未明确", "achievements": "未明确", "duration": "未明确"}],
                    "contact": "未提及"
                }
        except Exception as e:
            resume_analyzer_logger.error(f"简历分析失败: {e}")
            return {
                "name": "候选人", "position": "未明确", "education": "未分析",
                "experience": "未分析", "skills": "未分析",
                "projects": [{"name": "需询问", "description": "分析失败", "tech_stack": "需询问",
                            "role": "需询问", "achievements": "需询问", "duration": "需询问"}],
                "contact": "未分析"
            }
    
    def create_vector_database(self, resume_text: str) -> bool:
        """创建向量数据库"""
        try:
            chunks = self.text_splitter.split_text(resume_text)
            timestamp = int(time.time() * 1000)
            
            self.vector_store = Chroma.from_texts(
                texts=chunks,
                embedding=self.embeddings,
                persist_directory="./chroma_db",
                collection_name=f"resume_{timestamp}"
            )
            return True
        except Exception as e:
            resume_analyzer_logger.error(f"向量数据库创建失败: {e}")
            return False
    
    def search_resume_context(self, query: str, k: int = 3) -> List[str]:
        """搜索简历内容"""
        if not self.vector_store:
            return []
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            return [doc.page_content for doc in docs]
        except Exception as e:
            resume_analyzer_logger.error(f"向量搜索失败: {e}")
            return []
    
    def process_resume(self, pdf_path: str) -> bool:
        """处理简历文件"""
        try:
            # 清空旧数据
            self.resume_content = ""
            self.candidate_info = {}
            self.vector_store = None
            
            self.resume_content = self.extract_text_from_pdf(pdf_path)
            if not self.resume_content:
                return False
            
            self.candidate_info = self.analyze_resume_structure(self.resume_content)
            return self.create_vector_database(self.resume_content)
        except Exception as e:
            resume_analyzer_logger.error(f"简历处理失败: {e}")
            return False
    
    def get_candidate_info(self) -> Dict:
        """获取候选人信息"""
        return self.candidate_info
    
    def get_resume_summary(self) -> str:
        """获取简历摘要"""
        return self.resume_content[:500] + "..." if len(self.resume_content) > 500 else self.resume_content
    
    def get_resume_text(self) -> str:
        """获取完整简历文本"""
        return self.resume_content 