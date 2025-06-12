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
        self.embeddings = SparkEmbeddings(
            app_id=spark_config.get("app_id", ""),
            api_key=spark_config.get("api_key", ""),
            api_secret=spark_config.get("api_secret", "")
        )
    
    def calculate_vector_similarity(self, resume_text: str, job_text: str) -> Dict:
        """
        计算简历和岗位要求的向量相似度
        
        Args:
            resume_text: 简历完整文本
            job_text: 岗位要求完整文本
            
        Returns:
            包含相似度分数和分析的字典
        """
        try:
            # 获取文本的向量表示
            resume_vector = self.embeddings.embed_query(resume_text)
            job_vector = self.embeddings.embed_query(job_text)
            
            # 转换为numpy数组
            resume_vec = np.array(resume_vector).reshape(1, -1)
            job_vec = np.array(job_vector).reshape(1, -1)
            
            # 计算余弦相似度
            similarity_score = cosine_similarity(resume_vec, job_vec)[0][0]
            resume_matcher_logger.info(f"📊 向量相似度计算结果: {similarity_score}")
            resume_matcher_logger.debug(f"📊 简历向量维度: {len(resume_vector)}, 岗位向量维度: {len(job_vector)}")
            
            # 分析相似度等级
            if similarity_score >= 0.85:
                similarity_level = "极高匹配"
                confidence = "高"
            elif similarity_score >= 0.75:
                similarity_level = "高度匹配"
                confidence = "高"
            elif similarity_score >= 0.65:
                similarity_level = "良好匹配"
                confidence = "中"
            elif similarity_score >= 0.55:
                similarity_level = "基本匹配"
                confidence = "中"
            else:
                similarity_level = "匹配度较低"
                confidence = "低"
            
            return {
                "similarity_score": float(similarity_score),
                "similarity_level": similarity_level,
                "confidence": confidence,
                "vector_dimensions": len(resume_vector)
            }
            
        except Exception as e:
            resume_matcher_logger.error(f"向量相似度计算失败: {e}")
            return {
                "similarity_score": 0.0,
                "similarity_level": "计算失败",
                "confidence": "无",
                "error": str(e)
            }
    
    def analyze_with_llm(self, resume_text: str, job_requirements: Dict, 
                        vector_similarity: Dict) -> Dict:
        """
        使用大模型进行综合匹配分析
        
        Args:
            resume_text: 简历文本
            job_requirements: 岗位要求结构化数据
            vector_similarity: 向量相似度结果
            
        Returns:
            LLM分析结果
        """
        try:
            # 构建分析提示词
            analysis_prompt = f"""
作为资深HR和技术专家，请分析以下简历与岗位要求的匹配度：

**岗位要求：**
{json.dumps(job_requirements, ensure_ascii=False, indent=2)}

**候选人简历：**
{resume_text}

**向量相似度参考：**
- 语义相似度得分：{vector_similarity.get('similarity_score', 0):.3f}
- 相似度等级：{vector_similarity.get('similarity_level', '未知')}

请从以下维度进行分析并给出JSON格式的结果：

1. **技能匹配分析** - 评估候选人技能与岗位要求的匹配程度
2. **经验适配度** - 分析工作经验是否符合岗位需求
3. **综合匹配度** - 给出0-1之间的总体匹配得分
4. **优势亮点** - 候选人的突出优势
5. **不足之处** - 需要关注的短板
6. **面试建议** - 面试重点关注的方面
7. **录用建议** - 是否推荐录用及原因

请严格按照以下JSON格式返回，不要添加任何解释文字：

{{
    "overall_score": 0.0-1.0的匹配得分,
    "match_level": "高度匹配/良好匹配/基本匹配/不匹配",
    "skill_analysis": {{
        "score": 0.0-1.0,
        "description": "技能匹配分析说明",
        "matched_skills": ["匹配的技能列表"],
        "missing_skills": ["缺少的关键技能"]
    }},
    "experience_analysis": {{
        "score": 0.0-1.0,
        "description": "经验适配分析",
        "relevant_experience": ["相关经验描述"]
    }},
    "strengths": ["优势1", "优势2"],
    "weaknesses": ["不足1", "不足2"],
    "interview_focus": ["面试重点1", "面试重点2"],
    "recommendation": {{
        "decision": "推荐/谨慎考虑/不推荐",
        "reason": "推荐理由",
        "confidence": "高/中/低"
    }},
    "analysis_summary": "简要总结分析结果"
}}

重要提醒：
1. 请只返回JSON，不要添加任何```json```代码块标记
2. 不要在JSON前后添加任何解释文字
3. 确保所有字符串值都用双引号包围
4. 确保overall_score是0到1之间的数字
"""
            
            resume_matcher_logger.info("🤖 正在使用大模型进行综合分析...")
            response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
            
            # 打印原始响应用于调试
            resume_matcher_logger.debug(f"🔍 LLM原始响应内容:")
            resume_matcher_logger.debug(f"'{response.content}'")
            resume_matcher_logger.debug(f"🔍 响应长度: {len(response.content)}")
            resume_matcher_logger.debug(f"🔍 前200字符: {repr(response.content[:200])}")
            
            # 使用统一的JSON解析方法
            llm_analysis = JSONHelper.parse_llm_response(response.content, "LLM匹配分析")
            
            if llm_analysis is not None:
                resume_matcher_logger.info("✅ LLM JSON解析成功!")
                resume_matcher_logger.debug(f"📊 LLM返回的overall_score: {llm_analysis.get('overall_score', 'N/A')}")
                return {
                    "success": True,
                    "analysis": llm_analysis,
                    "raw_response": response.content
                }
            else:
                # 如果JSON解析失败，使用备用分析结果
                resume_matcher_logger.warning("⚠️ 使用备用分析结果 overall_score=0.5")
                return {
                    "success": False,
                    "analysis": {
                        "overall_score": 0.5,
                        "match_level": "需要人工评估",
                        "analysis_summary": "LLM分析结果解析失败，需要人工审核"
                    },
                    "raw_response": response.content,
                    "error": "JSON解析失败"
                }
                
        except Exception as e:
            resume_matcher_logger.error(f"LLM分析失败: {e}")
            return {
                "success": False,
                "analysis": {
                    "overall_score": 0.0,
                    "match_level": "分析失败",
                    "analysis_summary": f"分析过程出错: {str(e)}"
                },
                "error": str(e)
            }
    

    
    def generate_comprehensive_match_report(self, candidate_info: Dict, 
                                           job_requirements: Dict,
                                           resume_full_text: str = "",
                                           job_full_text: str = "") -> Dict:
        """
        生成简化的综合匹配度报告
        结合向量相似度和大模型分析
        
        Args:
            candidate_info: 候选人基本信息
            job_requirements: 岗位要求
            resume_full_text: 简历完整文本
            job_full_text: 岗位完整文本描述
            
        Returns:
            综合匹配报告
        """
        resume_matcher_logger.info("🔍 开始生成综合匹配度报告...")
        
        # 1. 计算向量相似度
        vector_similarity = {}
        if resume_full_text and job_full_text:
            resume_matcher_logger.info("📊 计算向量语义相似度...")
            vector_similarity = self.calculate_vector_similarity(resume_full_text, job_full_text)
        
        # 2. 大模型综合分析
        resume_matcher_logger.info("🧠 启动大模型智能分析...")
        llm_analysis = self.analyze_with_llm(
            resume_full_text or str(candidate_info), 
            job_requirements, 
            vector_similarity
        )
        
        # 3. 整合分析结果
        if llm_analysis["success"]:
            analysis_data = llm_analysis["analysis"]
            
            # 结合向量相似度调整最终得分
            vector_score = vector_similarity.get("similarity_score", 0.5)
            llm_score = analysis_data.get("overall_score", 0.5)
            
            resume_matcher_logger.info(f"📊 得分计算详情:")
            resume_matcher_logger.info(f"   向量相似度得分: {vector_score}")
            resume_matcher_logger.info(f"   LLM分析得分: {llm_score}")
            
            # 加权平均（向量相似度30%，LLM分析70%）
            final_score = vector_score * 0.3 + llm_score * 0.7
            resume_matcher_logger.info(f"   最终加权得分: {vector_score} * 0.3 + {llm_score} * 0.7 = {final_score}")
            
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
                "analysis_method": "向量相似度 + 大模型智能分析",
                "confidence": self._calculate_analysis_confidence(vector_similarity, llm_analysis)
            }
        else:
            # LLM分析失败时，仅基于向量相似度
            vector_score = vector_similarity.get("similarity_score", 0.0)
            resume_matcher_logger.warning(f"⚠️ LLM分析失败，使用向量相似度: {vector_score}")
            
            return {
                "total_score": vector_score,
                "match_level": vector_similarity.get("similarity_level", "无法评估"),
                "vector_similarity": vector_similarity,
                "llm_analysis": {"error": "LLM分析失败"},
                "recommendation": {
                    "decision": "需要人工评估",
                    "reason": "自动分析失败",
                    "confidence": "低"
                },
                "analysis_summary": "仅基于向量相似度的初步评估，建议人工复核",
                "analysis_method": "向量相似度（备用模式）",
                "confidence": "低"
            }
    
    def _calculate_analysis_confidence(self, vector_similarity: Dict, 
                                     llm_analysis: Dict) -> str:
        """计算分析结果的置信度"""
        confidence_factors = []
        
        # 向量相似度置信度
        vector_conf = vector_similarity.get("confidence", "低")
        confidence_factors.append(vector_conf)
        
        # LLM分析置信度
        if llm_analysis.get("success", False):
            llm_conf = llm_analysis.get("analysis", {}).get("recommendation", {}).get("confidence", "中")
            confidence_factors.append(llm_conf)
        
        # 综合置信度
        if "高" in confidence_factors and len(confidence_factors) >= 2:
            return "高"
        elif "中" in confidence_factors or "高" in confidence_factors:
            return "中"
        else:
            return "低"
    
    # 已删除未使用的analyze_resume_against_job_vectordb方法 