"""
简历相关API路由
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
import os
import shutil
from app.config.settings import get_spark_config
from app.services.resume_analyzer import ResumeAnalyzer
from app.services.resume_job_matcher import ResumeJobMatcher
from app.api.job import get_job_analyzer


router = APIRouter(prefix="/api/resume", tags=["简历管理"])

# 全局变量存储分析器实例
resume_analyzer = None
job_matcher = None


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    """
    上传并分析简历
    
    Args:
        file: PDF简历文件
        
    Returns:
        分析结果和候选人信息
    """
    global resume_analyzer
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF格式的简历")
    
    try:
        # 初始化简历分析器
        if resume_analyzer is None:
            resume_analyzer = ResumeAnalyzer(get_spark_config())
        
        # 保存上传的文件
        upload_dir = "./uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 处理简历
        success = resume_analyzer.process_resume(file_path)
        if not success:
            raise HTTPException(status_code=500, detail="简历处理失败")
        
        # 获取候选人信息
        candidate_info = resume_analyzer.get_candidate_info()
        
        # 清理临时文件
        os.remove(file_path)
        
        return {
            "status": "success",
            "message": "简历上传并分析成功",
            "candidate_info": candidate_info,
            "resume_processed": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


def get_resume_analyzer():
    """获取简历分析器实例"""
    return resume_analyzer


def get_job_matcher():
    """获取匹配分析器实例"""
    return job_matcher 