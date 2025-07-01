"""
匹配度分析API路由
"""
from fastapi import APIRouter, HTTPException
from app.config.settings import get_spark_config
from app.services.resume_job_matcher import ResumeJobMatcher
from app.core.state_manager import get_resume_analyzer, get_job_analyzer


router = APIRouter(prefix="/api/match", tags=["匹配度分析"])

# 全局变量存储匹配报告
current_match_report = None


@router.post("/analyze")
async def analyze_resume_job_match():
    """
    分析简历与岗位的匹配度
    
    Returns:
        详细的匹配度分析报告
    """
    global current_match_report
    
    resume_analyzer = get_resume_analyzer()
    job_analyzer = get_job_analyzer()
    
    if resume_analyzer is None:
        raise HTTPException(status_code=400, detail="请先上传简历")
    
    if job_analyzer is None:
        raise HTTPException(status_code=400, detail="请先加载岗位要求")
    
    try:
        # 初始化匹配分析器
        job_matcher = ResumeJobMatcher(get_spark_config())
        
        # 获取简历信息
        candidate_info = resume_analyzer.get_candidate_info()
        resume_skills = candidate_info.get("skills", [])
        
        # 获取岗位要求
        job_requirements = job_analyzer.get_job_info()
        
        # 获取完整文本用于向量相似度计算
        resume_full_text = resume_analyzer.get_resume_text() if hasattr(resume_analyzer, 'get_resume_text') else ""
        job_full_text = job_analyzer.job_content if hasattr(job_analyzer, 'job_content') else ""
        
        # 获取岗位向量数据库
        job_vector_store = job_analyzer.vector_store if hasattr(job_analyzer, 'vector_store') else None
        
        # 生成匹配度报告（简化版：向量相似度 + LLM分析）
        match_report = job_matcher.generate_comprehensive_match_report(
            candidate_info, job_requirements,
            resume_full_text, job_full_text
        )
        
        # 存储当前匹配报告，用于后续面试问题生成
        current_match_report = match_report
        
        return {
            "status": "success",
            "message": "匹配度分析完成",
            "match_report": match_report,
            "candidate_name": candidate_info.get("name", "候选人"),
            "job_title": job_requirements.get("job_title", "AI算法工程师")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匹配度分析失败: {str(e)}")


def get_current_match_report():
    """获取当前匹配报告"""
    return current_match_report 