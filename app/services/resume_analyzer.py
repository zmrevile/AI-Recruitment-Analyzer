"""
简历分析器 - 使用星火大模型分析简历并构建向量数据库
"""
import os
import fitz  # PyMuPDF
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.spark_llm import SparkLLM
from app.core.spark_embedding import SparkEmbeddings
from langchain_core.messages import HumanMessage
from langchain_community.vectorstores import Chroma
from typing import Dict, List
import json
from app.utils.logger import resume_analyzer_logger

class ResumeAnalyzer:
    def __init__(self, spark_config: Dict):
        self.spark_config = spark_config
        self.embeddings = SparkEmbeddings()  # 现在使用本地模型，无需配置
        self.llm = SparkLLM(
            app_id=spark_config.get("app_id", ""),
            api_key=spark_config.get("api_key", ""),
            api_secret=spark_config.get("api_secret", ""),
            temperature=0.3
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # 初始化Chroma向量数据库
        self.vector_store = None
        self.resume_content = ""
        self.candidate_info = {}
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """从PDF中提取文本"""
        try:
            # 使用PyMuPDF提取文本
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            resume_analyzer_logger.error(f"PDF文本提取失败: {e}")
            return ""
    
    def analyze_resume_structure(self, text: str) -> Dict:
        """分析简历结构，提取关键信息"""
        prompt = f"""
        请分析以下简历文本，提取关键信息并以JSON格式返回：
        
        简历文本：
        {text}
        
        请提取以下信息：
        {{
            "name": "姓名",
            "position": "目标职位",
            "education": "教育背景",
            "experience": "工作经验",
            "skills": "技能列表",
            "projects": "项目经验",
            "contact": "联系方式"
        }}
        
        如果某些信息不存在，请用"未提及"表示。
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            # 尝试解析JSON，如果失败则返回基本结构
            try:
                info = json.loads(response.content)
                return info
            except:
                return {
                    "name": "候选人",
                    "position": "未明确",
                    "education": response.content[:200],
                    "experience": "详见简历",
                    "skills": "详见简历",
                    "projects": "详见简历",
                    "contact": "未提及"
                }
        except Exception as e:
            resume_analyzer_logger.error(f"简历分析失败: {e}")
            return {
                "name": "候选人",
                "position": "未明确",
                "education": "未分析",
                "experience": "未分析",
                "skills": "未分析", 
                "projects": "未分析",
                "contact": "未分析"
            }
    
    def create_vector_database(self, resume_text: str) -> bool:
        """创建向量数据库"""
        try:
            # 分割文本
            chunks = self.text_splitter.split_text(resume_text)
            
            # 创建Chroma向量存储，使用新的collection名称避免维度冲突
            persist_directory = "./chroma_db"
            collection_name = "resume_collection_v2"  # 新的collection名称
            
            self.vector_store = Chroma.from_texts(
                texts=chunks,
                embedding=self.embeddings,
                persist_directory=persist_directory,
                collection_name=collection_name
            )
            
            return True
        except Exception as e:
            resume_analyzer_logger.error(f"向量数据库创建失败: {e}")
            return False
    
    def search_resume_context(self, query: str, k: int = 3) -> List[str]:
        """搜索简历相关内容"""
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
            # 提取PDF文本
            self.resume_content = self.extract_text_from_pdf(pdf_path)
            if not self.resume_content:
                return False
            
            # 分析简历结构
            self.candidate_info = self.analyze_resume_structure(self.resume_content)
            
            # 创建向量数据库
            success = self.create_vector_database(self.resume_content)
            
            return success
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
        return self.resume_content if hasattr(self, 'resume_content') else "" 