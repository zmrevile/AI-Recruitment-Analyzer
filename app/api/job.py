"""
岗位相关API路由
"""
from fastapi import APIRouter, HTTPException
from app.core.spark_llm import SparkLLM
from app.config.settings import get_spark_config
from app.services.job_analyzer import JobAnalyzer


router = APIRouter(prefix="/api/job", tags=["岗位管理"])

# 全局变量存储分析器实例
job_analyzer = None


@router.post("/upload-requirement")
async def upload_job_requirement():
    """
    加载默认AI工程师岗位要求
    
    Returns:
        岗位要求分析结果
    """
    global job_analyzer
    
    try:
        # 初始化岗位分析器
        if job_analyzer is None:
            job_analyzer = JobAnalyzer(get_spark_config())
        
        # 处理岗位要求文件
        job_file_path = "./data/job_requirement_ai_engineer.txt"
        success = job_analyzer.process_job_requirement(job_file_path)
        if not success:
            raise HTTPException(status_code=500, detail="岗位要求处理失败")
        
        # 获取岗位信息
        job_info = job_analyzer.get_job_info()
        job_summary = job_analyzer.get_job_summary()
        
        return {
            "status": "success",
            "message": "岗位要求加载成功",
            "job_info": job_info,
            "job_summary": job_summary,
            "job_processed": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"岗位要求处理失败: {str(e)}")


def get_job_analyzer():
    """获取岗位分析器实例"""
    return job_analyzer 