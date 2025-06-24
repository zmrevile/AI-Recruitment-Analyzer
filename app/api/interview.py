"""
面试相关API路由
"""
from fastapi import APIRouter, HTTPException
from typing import Dict
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
from app.models.interview import InterviewMessage, InterviewResponse, InterviewSession, InterviewStartRequest
from app.config.settings import get_spark_config
from app.services.enhanced_interview_generator import EnhancedInterviewGenerator
from app.api.resume import get_resume_analyzer
from app.api.job import get_job_analyzer
from app.api.match import get_current_match_report


router = APIRouter(prefix="/api/interview", tags=["面试管理"])

# 全局变量存储面试会话和生成器
interview_sessions: Dict[str, InterviewSession] = {}
enhanced_generator = None


@router.post("/start")
async def start_interview(request: InterviewStartRequest):
    """
    开始面试会话（基于匹配度分析）
    
    Args:
        request: 包含session_id的请求对象
    
    Returns:
        第一个面试问题内容
    """
    global enhanced_generator, interview_sessions
    
    # 检查session_id是否已存在
    if request.session_id in interview_sessions:
        raise HTTPException(status_code=400, detail=f"会话ID {request.session_id} 已存在")
    
    resume_analyzer = get_resume_analyzer()
    job_analyzer = get_job_analyzer()
    current_match_report = get_current_match_report()
    
    if resume_analyzer is None:
        raise HTTPException(status_code=400, detail="请先上传简历")
    
    if job_analyzer is None:
        raise HTTPException(status_code=400, detail="请先加载岗位要求")
        
    if current_match_report is None:
        raise HTTPException(status_code=400, detail="请先进行匹配度分析")
    
    try:
        # 初始化增强问题生成器
        if enhanced_generator is None:
            enhanced_generator = EnhancedInterviewGenerator(get_spark_config())
        
        # 使用传入的session_id创建新的面试会话
        session_id = request.session_id
        candidate_info = resume_analyzer.get_candidate_info()
        job_info = job_analyzer.get_job_info()
        
        # 初始化会话
        session = InterviewSession(session_id, candidate_info)
        interview_sessions[session_id] = session
        
        # 使用新的智能面试生成器生成第一个问题
        first_question_obj = enhanced_generator.generate_next_question(
            candidate_info, job_info, 
            conversation_history=[], 
            current_round=1,
            resume_context=[],  # 第一个问题时没有历史回答，不需要检索
            job_context=[]
        )
        first_question = first_question_obj["question"]
        
        # 添加问题到对话历史
        session.conversation_history.append(HumanMessage(content=first_question))
        session.question_count += 1
        
        # 增强候选人信息，包含匹配度信息（保留在session中，但不返回）
        enhanced_candidate_info = {
            **candidate_info,
            "match_score": current_match_report.get("total_score", 0),
            "match_level": current_match_report.get("match_level", "未知"),
            "job_title": job_info.get("job_title", "AI算法工程师")
        }
        session.candidate_info = enhanced_candidate_info
        
        # 第一个问题不是追问
        session.current_is_follow_up = False
        
        # 只返回问题内容
        return first_question
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"面试启动失败: {str(e)}")


@router.post("/answer")
async def submit_answer(interview_msg: InterviewMessage):
    """
    提交回答并获取下一个问题
    
    Args:
        interview_msg: 包含回答内容和会话ID的消息
        
    Returns:
        下一个面试问题内容
    """
    global enhanced_generator
    
    if interview_msg.session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    
    resume_analyzer = get_resume_analyzer()
    job_analyzer = get_job_analyzer()
    
    if resume_analyzer is None:
        raise HTTPException(status_code=400, detail="简历分析器未初始化")
    
    try:
        session = interview_sessions[interview_msg.session_id]
        
        # 添加用户回答到对话历史
        session.conversation_history.append(AIMessage(content=interview_msg.message))
        
        # 基于回答内容搜索相关简历信息
        resume_context = resume_analyzer.search_resume_context(
            interview_msg.message, k=3
        )
        
        # 基于回答内容搜索相关岗位要求信息
        job_context = job_analyzer.search_job_context(
            interview_msg.message, k=3
        )
        
        # 获取最后一个问题
        last_question = ""
        for msg in reversed(session.conversation_history):
            if isinstance(msg, HumanMessage):
                last_question = msg.content
                break
        
        # 智能判断是否需要追问
        follow_up_decision = enhanced_generator.should_follow_up(
            last_question, interview_msg.message, resume_context, job_context
        )
        
        # 考虑连续追问次数，避免过度追问
        should_follow_up = (follow_up_decision.get("should_follow_up", False) and 
                             session.follow_up_count < 2)  # 最多连续追问2次
        
        # 根据判断结果生成问题
        job_info = job_analyzer.get_job_info()
        session.question_count += 1
        
        if should_follow_up:
            # 生成追问问题
            next_question_obj = enhanced_generator.generate_follow_up_question(
                last_question, interview_msg.message,
                follow_up_decision.get("follow_up_focus", "技术细节"),
                resume_context, job_context
            )
            is_follow_up = True
            session.follow_up_count += 1  # 增加追问计数
        else:
            # 生成新话题问题
            next_question_obj = enhanced_generator.generate_next_question(
                session.candidate_info, job_info,
                conversation_history=session.conversation_history,
                current_round=session.question_count,
                resume_context=resume_context,
                job_context=job_context
            )
            is_follow_up = False
            session.follow_up_count = 0  # 重置追问计数
        
        next_question = next_question_obj["question"]
        
        # 添加新问题到对话历史
        session.conversation_history.append(HumanMessage(content=next_question))
        
        # 保留追问状态和轮次信息在session中（但不返回）
        session.current_is_follow_up = is_follow_up
        
        # 只返回问题内容
        return next_question
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理回答失败: {str(e)}")


@router.get("/history/{session_id}")
async def get_interview_history(session_id: str):
    """
    获取面试对话历史
    
    Args:
        session_id: 会话ID
        
    Returns:
        完整的面试对话历史
    """
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    
    session = interview_sessions[session_id]
    
    history = []
    for msg in session.conversation_history:
        if isinstance(msg, HumanMessage):
            history.append({"role": "interviewer", "content": msg.content})
        elif isinstance(msg, AIMessage):
            history.append({"role": "candidate", "content": msg.content})
    
    return {
        "session_id": session_id,
        "candidate_info": session.candidate_info,
        "question_count": session.question_count,
        "history": history,
        "created_at": session.created_at.isoformat()
    }


@router.get("/candidate-info")
async def get_candidate_info():
    """
    获取当前候选人信息
    
    Returns:
        候选人详细信息
    """
    resume_analyzer = get_resume_analyzer()
    
    if resume_analyzer is None:
        raise HTTPException(status_code=400, detail="请先上传简历")
    
    candidate_info = resume_analyzer.get_candidate_info()
    resume_summary = resume_analyzer.get_resume_summary()
    
    return {
        "candidate_info": candidate_info,
        "resume_summary": resume_summary,
        "vector_db_ready": resume_analyzer.vector_store is not None
    }


@router.post("/end/{session_id}")
async def end_interview(session_id: str):
    """
    结束面试会话
    
    Args:
        session_id: 要结束的会话ID
        
    Returns:
        面试总结
    """
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    
    session = interview_sessions[session_id]
    
    # 生成面试总结
    total_questions = session.question_count
    total_answers = len([msg for msg in session.conversation_history if isinstance(msg, AIMessage)])
    duration = datetime.now() - session.created_at
    
    # 删除会话
    del interview_sessions[session_id]
    
    return {
        "status": "success",
        "message": "面试已结束",
        "summary": {
            "candidate_name": session.candidate_info.get('name', '候选人'),
            "total_questions": total_questions,
            "total_answers": total_answers,
            "duration_minutes": int(duration.total_seconds() / 60),
            "session_ended_at": datetime.now().isoformat()
        }
    }


@router.get("/sessions")
async def list_interview_sessions():
    """
    列出所有活跃的面试会话
    
    Returns:
        会话列表及其基本信息
    """
    sessions_info = []
    for session_id, session in interview_sessions.items():
        sessions_info.append({
            "session_id": session_id,
            "candidate_name": session.candidate_info.get('name', '候选人'),
            "question_count": session.question_count,
            "created_at": session.created_at.isoformat(),
            "last_activity": datetime.now().isoformat()
        })
    
    return {
        "active_sessions": len(sessions_info),
        "sessions": sessions_info
    } 