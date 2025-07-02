"""
简历与岗位匹配度分析模块
"""
import json
from typing import Dict
from langchain_core.messages import HumanMessage
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.core.spark_llm import SparkLLM
from app.core.spark_embedding import get_embeddings
from app.utils.logger import resume_matcher_logger
from app.utils.json_helper import JSONHelper

class ResumeJobMatcher:
    def __init__(self, spark_config: Dict):
        self.llm = SparkLLM(
            app_id=spark_config.get("app_id", ""),
            api_key=spark_config.get("api_key", ""),
            api_secret=spark_config.get("api_secret", ""),
            temperature=0.3
        )
        self.embeddings = get_embeddings()  # 使用优化后的单例模式
    
    def calculate_vector_similarity(self, resume_text: str, job_text: str) -> Dict:
        """计算向量相似度"""
        try:
            resume_vector = self.embeddings.embed_query(resume_text)
            job_vector = self.embeddings.embed_query(job_text)
            
            resume_vec = np.array(resume_vector).reshape(1, -1)
            job_vec = np.array(job_vector).reshape(1, -1)
            similarity_score = cosine_similarity(resume_vec, job_vec)[0][0]
            
            return {
                "similarity_score": float(similarity_score),
                "resume_length": len(resume_text.strip()),
                "job_length": len(job_text.strip())
            }
        except Exception as e:
            resume_matcher_logger.error(f"向量相似度计算失败: {e}")
            return {"similarity_score": 0.0, "error": str(e)}
    
    def analyze_with_llm(self, resume_text: str, job_requirements: Dict) -> Dict:
        """使用LLM分析匹配度"""
        try:
            # 每次创建新的LLM实例避免会话记忆
            fresh_llm = SparkLLM(
                app_id=self.llm.app_id,
                api_key=self.llm.api_key,
                api_secret=self.llm.api_secret,
                temperature=0.3
            )
            
            resume_length = len(resume_text.strip())
            
            if resume_length < 50:
                # 短简历处理
                prompt = f"""
忽略之前对话，分析以下简历匹配度：

岗位要求：{json.dumps(job_requirements, ensure_ascii=False)}
简历内容（{resume_length}字符）：{resume_text}

重要：简历信息严重不足，严禁编造内容。

返回JSON格式：
{{
    "overall_score": 0.1,
    "match_level": "不匹配",
    "skill_analysis": {{"score": 0.1, "matched_skills": [], "missing_skills": ["所有岗位要求技能"]}},
    "experience_analysis": {{"score": 0.1, "description": "简历信息不足，无法评估"}},
    "strengths": ["无法识别"],
    "weaknesses": ["信息严重不足"],
    "interview_focus": ["要求完整简历"],
    "recommendation": {{"decision": "不推荐", "reason": "信息不足"}},
    "analysis_summary": "简历信息不足，无法评估"
}}
"""
            else:
                # 正常简历处理
                prompt = f"""
忽略之前对话，分析简历匹配度：

岗位要求：{json.dumps(job_requirements, ensure_ascii=False)}
简历内容：{resume_text}

基于实际简历内容分析，返回JSON：
{{
    "overall_score": 0.0-1.0,
    "match_level": "匹配等级",
    "skill_analysis": {{"score": 0.0-1.0, "matched_skills": ["实际匹配技能"], "missing_skills": ["缺少技能"]}},
    "experience_analysis": {{"score": 0.0-1.0, "description": "经验评估"}},
    "strengths": ["真实优势"],
    "weaknesses": ["真实不足"],
    "interview_focus": ["面试重点"],
    "recommendation": {{"decision": "推荐/谨慎考虑/不推荐", "reason": "理由"}},
    "analysis_summary": "分析总结"
}}
"""
            
            response = fresh_llm.invoke([HumanMessage(content=prompt)])
            llm_analysis = JSONHelper.parse_llm_response(response.content, "LLM匹配分析")
            
            return {"success": True, "analysis": llm_analysis} if llm_analysis else {
                "success": False,
                "analysis": {"overall_score": 0.5, "match_level": "解析失败", "analysis_summary": "解析失败"}
            }
                
        except Exception as e:
            resume_matcher_logger.error(f"LLM分析失败: {e}")
            return {
                "success": False,
                "analysis": {"overall_score": 0.0, "match_level": "分析失败", "analysis_summary": f"错误: {e}"}
            }
    
    def generate_comprehensive_match_report(self, candidate_info: Dict, 
                                           job_requirements: Dict,
                                           resume_full_text: str = "",
                                           job_full_text: str = "") -> Dict:
        """生成匹配度报告"""
        # 向量相似度分析
        vector_similarity = {}
        if resume_full_text and job_full_text:
            vector_similarity = self.calculate_vector_similarity(resume_full_text, job_full_text)
        
        # LLM分析
        llm_input_text = resume_full_text if resume_full_text.strip() else str(candidate_info)
        llm_analysis = self.analyze_with_llm(llm_input_text, job_requirements)
        
        if llm_analysis["success"]:
            analysis_data = llm_analysis["analysis"]
            vector_score = vector_similarity.get("similarity_score", 0.0)
            llm_score = analysis_data.get("overall_score", 0.0)
            final_score = vector_score * 0.2 + llm_score * 0.8
            
            return {
                "total_score": final_score,
                "match_level": analysis_data.get("match_level", "未知"),
                "vector_similarity": vector_similarity,
                "llm_analysis": analysis_data,
                "recommendation": analysis_data.get("recommendation", {}),
                "strengths": analysis_data.get("strengths", []),
                "weaknesses": analysis_data.get("weaknesses", []),
                "interview_focus": analysis_data.get("interview_focus", []),
                "analysis_summary": analysis_data.get("analysis_summary", ""),
                "analysis_method": "双轨制：向量相似度 + LLM分析"
            }
        else:
            # 降级使用向量相似度
            vector_score = vector_similarity.get("similarity_score", 0.0)
            return {
                "total_score": vector_score,
                "match_level": "基于向量相似度",
                "vector_similarity": vector_similarity,
                "llm_analysis": {"error": "LLM分析失败"},
                "analysis_summary": "仅基于向量相似度评估",
                "analysis_method": "单轨模式：向量相似度"
            }
    
 