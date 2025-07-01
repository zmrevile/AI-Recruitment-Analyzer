"""
主API路由汇总
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.api import match, interview
from datetime import datetime
import os
from app.core.state_manager import get_resume_analyzer, get_job_analyzer


# 创建主路由器
api_router = APIRouter()

# 包含所有子路由
api_router.include_router(match.router)
api_router.include_router(interview.router)


@api_router.post("/upload")
async def upload_files(
    resume_file: UploadFile = File(..., description="PDF格式简历文件"),
    job_file: UploadFile = File(..., description="TXT格式岗位要求文件")
):
    """
    同时上传简历和岗位要求文件
    
    Args:
        resume_file: PDF格式简历文件
        job_file: TXT格式岗位要求文件
        
    Returns:
        简历和岗位分析结果
    """
    # 验证文件格式
    if not resume_file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="简历文件只支持PDF格式")
    
    if not job_file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="岗位要求文件只支持TXT格式")
    
    try:
        # 获取分析器实例
        resume_analyzer = get_resume_analyzer()
        job_analyzer = get_job_analyzer()
        
        # 处理简历文件
        upload_dir = "./uploads"
        os.makedirs(upload_dir, exist_ok=True)
        resume_path = os.path.join(upload_dir, resume_file.filename)
        
        with open(resume_path, "wb") as buffer:
            content = await resume_file.read()
            buffer.write(content)
        
        resume_success = resume_analyzer.process_resume(resume_path)
        if not resume_success:
            raise HTTPException(status_code=500, detail="简历处理失败")
        
        # 清理临时简历文件
        os.remove(resume_path)
        
        # 处理岗位要求文件
        job_content = await job_file.read()
        job_text = job_content.decode('utf-8')
        
        job_success = job_analyzer.process_job_content(job_text)
        if not job_success:
            raise HTTPException(status_code=500, detail="岗位要求处理失败")
        
        # 获取分析结果
        candidate_info = resume_analyzer.get_candidate_info()
        job_info = job_analyzer.get_job_info()
        job_summary = job_analyzer.get_job_summary()
        
        return {
            "status": "success",
            "message": "简历和岗位要求上传分析成功",
            "candidate_info": candidate_info,
            "job_info": job_info,
            "job_summary": job_summary,
            "resume_processed": True,
            "job_processed": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")


@api_router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "4.0.0"
    } 