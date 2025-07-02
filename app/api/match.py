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
    
    # 重置之前的匹配报告
    current_match_report = None
    
    resume_analyzer = get_resume_analyzer()
    job_analyzer = get_job_analyzer()
    
    if not resume_analyzer:
        raise HTTPException(status_code=400, detail="请先上传简历")
    if not job_analyzer:
        raise HTTPException(status_code=400, detail="请先加载岗位要求")
    
    try:
        # 初始化匹配分析器
        job_matcher = ResumeJobMatcher(get_spark_config())
        
        # 获取简历信息
        candidate_info = resume_analyzer.get_candidate_info()
        job_requirements = job_analyzer.get_job_info()
        
        # 获取简历文本，优先使用原始内容
        resume_text = getattr(resume_analyzer, 'resume_content', 
                             resume_analyzer.get_resume_text() if hasattr(resume_analyzer, 'get_resume_text') else "")
        job_text = getattr(job_analyzer, 'job_content', "")
        
        # 生成匹配度报告
        match_report = job_matcher.generate_comprehensive_match_report(
            candidate_info, job_requirements, resume_text, job_text
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


def reset_current_match_report():
    """重置当前匹配报告"""
    global current_match_report
    current_match_report = None 