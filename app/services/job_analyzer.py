"""
岗位需求分析器 - 使用星火大模型分析岗位要求并构建向量数据库
"""
import os
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.spark_llm import SparkLLM
from app.core.spark_embedding import SparkEmbeddings
from langchain_core.messages import HumanMessage
from langchain_community.vectorstores import Chroma
from typing import Dict, List
import json
import re
from app.utils.logger import job_analyzer_logger
from app.utils.json_helper import JSONHelper

class JobAnalyzer:
    def __init__(self, spark_config: Dict):
        self.spark_config = spark_config
        self.embeddings = SparkEmbeddings(
            app_id=spark_config.get("app_id", ""),
            api_key=spark_config.get("api_key", ""),
            api_secret=spark_config.get("api_secret", "")
        )
        self.llm = SparkLLM(
            app_id=spark_config.get("app_id", ""),
            api_key=spark_config.get("api_key", ""),
            api_secret=spark_config.get("api_secret", ""),
            temperature=0.3
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            length_function=len,
        )
        
        # 初始化向量数据库
        self.vector_store = None
        self.job_content = ""
        self.structured_job_data = {}
        
    def load_job_requirement(self, file_path: str) -> str:
        """从文件中加载岗位要求"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            job_analyzer_logger.error(f"岗位要求文件加载失败: {e}")
            return ""
    
    def extract_structured_job_info(self, job_text: str) -> Dict:
        """使用LLM提取结构化的岗位信息"""
        prompt = f"""
        请分析以下岗位要求，提取关键信息并以JSON格式返回：

        岗位要求文本：
        {job_text}

        请按以下结构提取信息：
        {{
            "job_title": "职位名称",
            "company": "公司名称", 
            "department": "部门",
            "salary_range": "薪资范围",
            "experience_requirement": {{
                "min_years": 最低年限数字,
                "max_years": 最高年限数字,
                "level": "级别描述"
            }},
            "education_requirement": {{
                "min_degree": "最低学历要求",
                "preferred_majors": ["专业1", "专业2"]
            }},
            "hard_requirements": {{
                "必须技能": ["技能1", "技能2"],
                "必须经验": ["经验1", "经验2"]
            }},
            "core_skills": {{
                "技能名称": {{"weight": 权重数字, "level": "要求级别", "required": true/false}},
                "计算机视觉": {{"weight": 0.35, "level": "精通", "required": true}}
            }},
            "preferred_skills": {{
                "技能名称": {{"weight": 权重数字, "level": "要求级别"}},
                "CUDA编程": {{"weight": 0.1, "level": "了解"}}
            }},
            "project_requirements": ["项目要求1", "项目要求2"],
            "bonus_points": ["加分项1", "加分项2"]
        }}
        
        注意：
        1. 权重数字应为0-1之间的小数，所有核心技能权重之和应接近1
        2. 如果信息不存在，请用"未提及"或空数组表示
        3. 确保JSON格式正确
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        # 打印原始响应内容用于调试
        job_analyzer_logger.debug(f"🔍 星火大模型原始返回内容:")
        job_analyzer_logger.debug(f"'{response.content}'")
        job_analyzer_logger.debug(f"🔍 内容长度: {len(response.content)}")
        job_analyzer_logger.debug(f"🔍 前100个字符: {repr(response.content[:100])}")
        
        # 使用统一的JSON解析方法
        structured_data = JSONHelper.parse_llm_response(response.content, "岗位信息提取")
        
        if structured_data is None:
            raise ValueError(f"岗位信息提取失败：无法解析LLM返回的JSON格式")
            
        return structured_data
    

    

    
    def create_vector_database(self, job_text: str) -> bool:
        """创建岗位要求的向量数据库"""
        try:
            # 分割文本
            chunks = self.text_splitter.split_text(job_text)
            
            # 创建Chroma向量存储
            persist_directory = "./chroma_db_job"
            self.vector_store = Chroma.from_texts(
                texts=chunks,
                embedding=self.embeddings,
                persist_directory=persist_directory,
                collection_name="job_requirements"
            )
            
            return True
        except Exception as e:
            job_analyzer_logger.error(f"岗位要求向量数据库创建失败: {e}")
            return False
    
    def search_job_context(self, query: str, k: int = 3) -> List[str]:
        """搜索岗位要求相关内容"""
        if not self.vector_store:
            return []
        
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            return [doc.page_content for doc in docs]
        except Exception as e:
            job_analyzer_logger.error(f"岗位要求检索失败: {e}")
            return []
    
    def process_job_requirement(self, file_path: str) -> bool:
        """处理岗位要求文件"""
        try:
            # 1. 加载岗位要求文件
            self.job_content = self.load_job_requirement(file_path)
            if not self.job_content:
                return False
            
            # 2. 提取结构化信息
            self.structured_job_data = self.extract_structured_job_info(self.job_content)
            
            # 3. 创建向量数据库
            success = self.create_vector_database(self.job_content)
            
            return success
        except Exception as e:
            job_analyzer_logger.error(f"岗位要求处理失败: {e}")
            return False
    
    def get_job_info(self) -> Dict:
        """获取岗位基本信息"""
        return self.structured_job_data
    
    def get_job_summary(self) -> str:
        """获取岗位要求摘要"""
        if not self.structured_job_data:
            return "岗位信息未加载"
        
        job_title = self.structured_job_data.get("job_title", "未知职位")
        company = self.structured_job_data.get("company", "未知公司")
        exp_req = self.structured_job_data.get("experience_requirement", {})
        
        summary = f"职位：{job_title}\n"
        summary += f"公司：{company}\n"
        summary += f"经验要求：{exp_req.get('min_years', 0)}-{exp_req.get('max_years', 0)}年\n"
        
        # 核心技能概览
        core_skills = self.structured_job_data.get("core_skills", {})
        if core_skills:
            top_skills = sorted(core_skills.items(), 
                              key=lambda x: x[1].get("weight", 0), 
                              reverse=True)[:3]
            skills_str = ", ".join([skill for skill, _ in top_skills])
            summary += f"核心技能：{skills_str}"
        
        return summary
    
