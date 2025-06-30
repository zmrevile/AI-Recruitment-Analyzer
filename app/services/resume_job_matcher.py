"""
简历与岗位匹配度分析模块 - 简化版
基于向量相似度和大模型分析的智能匹配系统
"""
import json
from typing import Dict, List, Tuple
from langchain_core.messages import HumanMessage
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.core.spark_llm import SparkLLM
from app.core.spark_embedding import SparkEmbeddings
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
        self.embeddings = SparkEmbeddings()  # 现在使用本地模型，无需配置
    
    def calculate_vector_similarity(self, resume_text: str, job_text: str) -> Dict:
        """
        计算简历和岗位要求的向量相似度（简化版）
        
        Args:
            resume_text: 简历完整文本
            job_text: 岗位要求完整文本
            
        Returns:
            包含相似度分数的字典
        """
        try:
            # 获取文本的向量表示
            resume_vector = self.embeddings.embed_query(resume_text)
            job_vector = self.embeddings.embed_query(job_text)
            
            # 转换为numpy数组并计算余弦相似度
            resume_vec = np.array(resume_vector).reshape(1, -1)
            job_vec = np.array(job_vector).reshape(1, -1)
            similarity_score = cosine_similarity(resume_vec, job_vec)[0][0]
            
            resume_matcher_logger.info(f"📊 向量相似度: {similarity_score:.4f}")
            
            return {
                "similarity_score": float(similarity_score),
                "resume_length": len(resume_text.strip()),
                "job_length": len(job_text.strip())
            }
            
        except Exception as e:
            resume_matcher_logger.error(f"向量相似度计算失败: {e}")
            return {"similarity_score": 0.0, "error": str(e)}
    
    def analyze_with_llm(self, resume_text: str, job_requirements: Dict) -> Dict:
        """
        使用大模型进行独立匹配分析
        
        Args:
            resume_text: 简历文本
            job_requirements: 岗位要求结构化数据
            
        Returns:
            LLM分析结果
        """
        try:
            # 构建简洁的分析提示词
            analysis_prompt = f"""
作为资深HR和技术专家，请分析以下简历与岗位要求的匹配度：

**岗位要求：**
{json.dumps(job_requirements, ensure_ascii=False, indent=2)}

**候选人简历：**
{resume_text}

请从以下维度进行客观分析：

1. **技能匹配** - 技能是否符合岗位要求
2. **经验适配** - 工作经验是否匹配
3. **综合评估** - 给出0-1之间的匹配得分
4. **优势分析** - 候选人的突出优势
5. **不足分析** - 需要关注的短板
6. **面试建议** - 面试重点
7. **录用建议** - 是否推荐及原因

请严格按照以下JSON格式返回：

{{
    "overall_score": 0.0-1.0的匹配得分,
    "match_level": "极高匹配/高度匹配/良好匹配/基本匹配/不匹配",
    "skill_analysis": {{
        "score": 0.0-1.0,
        "matched_skills": ["匹配的技能"],
        "missing_skills": ["缺少的技能"]
    }},
    "experience_analysis": {{
        "score": 0.0-1.0,
        "description": "经验匹配说明"
    }},
    "strengths": ["优势1", "优势2"],
    "weaknesses": ["不足1", "不足2"],
    "interview_focus": ["重点1", "重点2"],
    "recommendation": {{
        "decision": "推荐/谨慎考虑/不推荐",
        "reason": "推荐理由"
    }},
    "analysis_summary": "总结"
}}

注意：只返回JSON，不要添加其他内容。
"""
            
            resume_matcher_logger.info("🤖 LLM独立分析中...")
            response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
            
            # 解析LLM响应
            llm_analysis = JSONHelper.parse_llm_response(response.content, "LLM匹配分析")
            
            if llm_analysis:
                resume_matcher_logger.info("✅ LLM分析完成")
                return {"success": True, "analysis": llm_analysis}
            else:
                resume_matcher_logger.warning("⚠️ LLM分析解析失败")
                return {
                    "success": False,
                    "analysis": {
                        "overall_score": 0.5,
                        "match_level": "需要人工评估",
                        "analysis_summary": "LLM分析结果解析失败"
                    }
                }
                
        except Exception as e:
            resume_matcher_logger.error(f"LLM分析失败: {e}")
            return {
                "success": False,
                "analysis": {
                    "overall_score": 0.0,
                    "match_level": "分析失败",
                    "analysis_summary": f"分析过程出错: {str(e)}"
                }
            }
    
    def generate_comprehensive_match_report(self, candidate_info: Dict, 
                                           job_requirements: Dict,
                                           resume_full_text: str = "",
                                           job_full_text: str = "") -> Dict:
        """
        生成双轨制匹配度报告：向量相似度 + LLM独立分析
        
        Args:
            candidate_info: 候选人基本信息
            job_requirements: 岗位要求
            resume_full_text: 简历完整文本
            job_full_text: 岗位完整文本描述
            
        Returns:
            综合匹配报告
        """
        resume_matcher_logger.info("🔍 生成双轨制匹配分析报告...")
        
        # 轨道1：向量语义相似度
        vector_similarity = {}
        if resume_full_text and job_full_text:
            resume_matcher_logger.info("📊 计算向量语义相似度...")
            vector_similarity = self.calculate_vector_similarity(resume_full_text, job_full_text)
        
        # 轨道2：LLM独立分析
        resume_matcher_logger.info("🧠 LLM独立智能分析...")
        llm_analysis = self.analyze_with_llm(
            resume_full_text or str(candidate_info), 
            job_requirements
        )
        
        # 组装最终报告
        if llm_analysis["success"]:
            analysis_data = llm_analysis["analysis"]
            
            # 获取各项得分
            vector_score = vector_similarity.get("similarity_score", 0.0)
            llm_score = analysis_data.get("overall_score", 0.0)
            
            # 调整权重：降低向量相似度影响，提高LLM权重
            # 由于向量相似度存在系统性偏差，我们主要依赖LLM分析
            final_score = vector_score * 0.2 + llm_score * 0.8
            
            resume_matcher_logger.info(f"📊 得分汇总:")
            resume_matcher_logger.info(f"   向量相似度: {vector_score:.3f} (权重20%)")
            resume_matcher_logger.info(f"   LLM智能分析: {llm_score:.3f} (权重80%)")
            resume_matcher_logger.info(f"   综合得分: {final_score:.3f}")
            
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
                "analysis_method": "双轨制：向量相似度 + LLM独立分析"
            }
        else:
            # LLM分析失败，仅使用向量相似度
            vector_score = vector_similarity.get("similarity_score", 0.0)
            resume_matcher_logger.warning(f"⚠️ 降级为单轨模式，仅使用向量相似度: {vector_score:.3f}")
            
            return {
                "total_score": vector_score,
                "match_level": "基于向量相似度评估",
                "vector_similarity": vector_similarity,
                "llm_analysis": {"error": "LLM分析失败"},
                "analysis_summary": "仅基于向量相似度的评估，建议人工复核",
                "analysis_method": "单轨模式：仅向量相似度"
            }
    
 