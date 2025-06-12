#!/usr/bin/env python3
"""
交互式面试测试脚本
让用户亲自参与面试，体验真正的AI智能面试流程
"""
import requests
import json
import time
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.logger import get_logger

# 创建测试专用的日志记录器
test_logger = get_logger("interview_test")

BASE_URL = "http://localhost:8000"

def setup_prerequisites():
    """设置前置条件：岗位要求和简历"""
    test_logger.info("🔧 设置前置条件...")
    
    # 加载岗位要求
    test_logger.info("   加载岗位要求...")
    job_url = f"{BASE_URL}/api/job/upload-requirement"
    job_response = requests.post(job_url)
    
    if job_response.status_code != 200:
        test_logger.error(f"❌ 岗位要求加载失败: {job_response.text}")
        return False
    
    # 上传简历
    test_logger.info("   上传简历...")
    resume_files = [f for f in os.listdir('./data') if f.endswith('.pdf')]
    if not resume_files:
        test_logger.error("❌ 未找到PDF简历文件")
        return False
    
    resume_file = resume_files[0]
    resume_path = f"./data/{resume_file}"
    resume_url = f"{BASE_URL}/api/resume/upload"
    
    with open(resume_path, 'rb') as f:
        files = {'file': (resume_file, f, 'application/pdf')}
        response = requests.post(resume_url, files=files)
    
    if response.status_code != 200:
        test_logger.error(f"❌ 简历处理失败: {response.text}")
        return False
    
    # 执行匹配度分析
    test_logger.info("   执行匹配度分析...")
    match_url = f"{BASE_URL}/api/match/analyze"
    match_response = requests.post(match_url)
    
    if match_response.status_code != 200:
        test_logger.error(f"❌ 匹配度分析失败: {match_response.text}")
        return False
    
    # 显示匹配度结果
    match_result = match_response.json()
    match_report = match_result['match_report']
    
    test_logger.info("✅ 前置条件设置完成！")
    test_logger.info(f"   📊 匹配度得分: {match_report['total_score']:.3f}")
    test_logger.info(f"   📊 匹配等级: {match_report['match_level']}")
    test_logger.info(f"   📊 推荐决策: {match_report.get('recommendation', {}).get('decision', '未知')}")
    
    return True

def start_interview_session():
    """开始面试会话"""
    test_logger.info("\n🤖 启动面试会话...")
    
    start_url = f"{BASE_URL}/api/interview/start"
    response = requests.post(start_url)
    
    if response.status_code != 200:
        test_logger.error(f"❌ 面试启动失败: {response.text}")
        return None
    
    result = response.json()
    session_id = result['session_id']
    first_question = result['question']
    candidate_info = result['candidate_info']
    
    test_logger.info("✅ 面试会话创建成功！")
    test_logger.info(f"   👤 候选人: {candidate_info.get('name', '未知')}")
    test_logger.info(f"   💼 岗位: {candidate_info.get('job_title', 'AI算法工程师')}")
    test_logger.info(f"   🆔 会话ID: {session_id}")
    
    return session_id, first_question

def conduct_interactive_interview(session_id, first_question):
    """进行交互式面试"""
    test_logger.info("\n" + "=" * 60)
    test_logger.info("🎙️  开始智能面试！")
    test_logger.info("💡 提示: 输入 'quit' 或 '退出' 结束面试")
    test_logger.info("=" * 60)
    
    current_question = first_question
    question_round = 1
    answer_url = f"{BASE_URL}/api/interview/answer"
    
    while True:
        # 显示当前问题
        test_logger.info(f"\n🤖 面试官 (第{question_round}轮):")
        test_logger.info(f"   {current_question}")
        
        # 获取用户答案
        test_logger.info(f"\n👤 您的回答:")
        user_answer = input("   >> ").strip()
        
        # 检查是否要退出
        if user_answer.lower() in ['quit', 'exit', '退出', 'q']:
            test_logger.info("\n👋 面试结束，感谢您的参与！")
            break
        
        if not user_answer:
            test_logger.warning("⚠️  请输入您的回答")
            continue
        
        # 发送答案并获取下一个问题
        test_logger.info("\n🤔 面试官正在思考下一个问题...")
        
        payload = {
            "message": user_answer,
            "session_id": session_id
        }
        
        response = requests.post(answer_url, json=payload)
        
        if response.status_code != 200:
            test_logger.error(f"❌ 发送回答失败: {response.text}")
            break
        
        result = response.json()
        current_question = result['question']
        question_round = result['question_round']
        
        # 显示分隔线
        test_logger.info("-" * 60)
    
    return session_id

def show_interview_summary(session_id):
    """显示面试总结"""
    test_logger.info("\n📋 面试总结")
    test_logger.info("=" * 40)
    
    history_url = f"{BASE_URL}/api/interview/history/{session_id}"
    response = requests.get(history_url)
    
    if response.status_code != 200:
        test_logger.error(f"❌ 获取面试历史失败: {response.text}")
        return
    
    result = response.json()
    history = result['history']
    question_count = result['question_count']
    candidate_info = result['candidate_info']
    
    test_logger.info(f"👤 候选人: {candidate_info.get('name', '未知')}")
    test_logger.info(f"🔢 总问题数: {question_count}")
    test_logger.info(f"💬 对话轮次: {len(history)}")
    
    test_logger.info(f"\n📝 完整对话记录:")
    test_logger.info("-" * 40)
    
    for i, item in enumerate(history, 1):
        role = "🤖 面试官" if item['role'] == 'interviewer' else "👤 候选人"
        content = item['content']
        
        test_logger.info(f"\n{i}. {role}:")
        # 长文本换行显示
        if len(content) > 80:
            lines = [content[i:i+80] for i in range(0, len(content), 80)]
            for line in lines:
                test_logger.info(f"   {line}")
        else:
            test_logger.info(f"   {content}")
    
    test_logger.info("\n" + "=" * 40)
    test_logger.info("🎉 面试体验完成！")

def main():
    """主函数"""
    test_logger.info("🚀 AI智能面试系统 - 交互式体验")
    test_logger.info("=" * 60)
    
    # 检查服务器状态
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            test_logger.error("❌ 服务器未响应，请先启动服务器")
            return
        test_logger.info("✅ 服务器连接正常")
    except Exception as e:
        test_logger.error(f"❌ 无法连接到服务器: {e}")
        test_logger.info("💡 请确保已启动FastAPI服务器: python main.py")
        return
    
    # 设置前置条件
    if not setup_prerequisites():
        test_logger.error("❌ 前置条件设置失败")
        return
    
    # 开始面试
    interview_data = start_interview_session()
    if not interview_data:
        test_logger.error("❌ 面试启动失败")
        return
    
    session_id, first_question = interview_data
    
    # 进行交互式面试
    final_session_id = conduct_interactive_interview(session_id, first_question)
    
    # 显示面试总结
    if final_session_id:
        show_interview_summary(final_session_id)

if __name__ == "__main__":
    main() 