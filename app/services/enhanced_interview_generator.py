"""
智能面试问题生成器
完全基于星火大模型，像真正面试官一样根据简历、岗位要求和对话历史动态生成问题
"""
from typing import Dict, List, Optional
from app.core.spark_llm import SparkLLM
from langchain_core.messages import HumanMessage
from app.utils.json_helper import JSONHelper
import json
import re
from app.utils.logger import interview_generator_logger

class EnhancedInterviewGenerator:
    def __init__(self, spark_config: Dict):
        self.llm = SparkLLM(
            app_id=spark_config.get("app_id", ""),
            api_key=spark_config.get("api_key", ""),
            api_secret=spark_config.get("api_secret", ""),
            spark_url=spark_config.get("spark_url", "wss://spark-api.xf-yun.com/v3.5/chat"),
            domain=spark_config.get("domain", "generalv3.5"),
            temperature=0.7
        )
    

    

    
    def generate_next_question(self, candidate_info: Dict, job_info: Dict, 
                             conversation_history: List = None, 
                             current_round: int = 1,
                             resume_context: List[str] = None,
                             job_context: List[str] = None) -> Dict:
        """生成下一个面试问题"""
        prompt = self._build_interviewer_prompt(
            candidate_info, job_info, conversation_history, current_round,
            resume_context, job_context
        )
        
        print(f"🤖 面试官正在思考第{current_round}个问题...")
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        # 使用统一的JSON解析方法
        question_data = JSONHelper.parse_llm_response(response.content, "问题生成")
        
        if not question_data:
            raise ValueError(f"问题生成失败：无法解析响应内容为有效JSON格式")
        
        return question_data
    
    def should_follow_up(self, last_question: str, candidate_answer: str, 
                        resume_context: List[str] = None, 
                        job_context: List[str] = None) -> Dict:
        """智能判断是否需要追问"""
        prompt = self._build_follow_up_decision_prompt(
            last_question, candidate_answer, resume_context, job_context
        )
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        decision_data = JSONHelper.parse_llm_response(response.content, "追问判断")
        
        if not decision_data:
            raise ValueError(f"追问判断失败：无法解析响应内容为有效JSON格式")
        
        return decision_data
    
    def generate_follow_up_question(self, last_question: str, candidate_answer: str,
                                   follow_up_focus: str, resume_context: List[str] = None,
                                   job_context: List[str] = None) -> Dict:
        """生成追问问题"""
        prompt = self._build_follow_up_question_prompt(
            last_question, candidate_answer, follow_up_focus, resume_context, job_context
        )
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        question_data = JSONHelper.parse_llm_response(response.content, "追问生成")
        
        if not question_data:
            raise ValueError(f"追问生成失败：无法解析响应内容为有效JSON格式")
        
        return question_data
    
    def _build_interviewer_prompt(self, candidate_info: Dict, job_info: Dict, 
                                 conversation_history: List, current_round: int,
                                 resume_context: List[str] = None,
                                 job_context: List[str] = None) -> str:
        """构建面试官角色提示词"""
        history_summary = self._summarize_conversation_history(conversation_history)
        interview_stage = self._determine_interview_stage(current_round, conversation_history)
        context_info = self._build_context_info(resume_context, job_context)
        
        return f"""
你是一位经验丰富的技术面试官，正在面试一位候选人。请基于以下信息生成下一个面试问题：

## 候选人简历信息：
{json.dumps(candidate_info, ensure_ascii=False, indent=2)}

## 岗位要求：
{json.dumps(job_info, ensure_ascii=False, indent=2)}

{context_info}

## 面试进展：
- 当前是第{current_round}个问题
- 面试阶段：{interview_stage}

## 对话历史摘要：
{history_summary}

## 面试官指导原则：
1. **利用检索上下文**：优先基于检索到的相关简历片段和岗位要求进行提问
2. **像真正面试官一样思考**：考虑候选人的背景、岗位要求和已经了解的信息
3. **循序渐进**：根据面试阶段调整问题深度和类型
4. **有针对性**：基于简历亮点或潜在关注点提问
5. **避免重复**：不要问已经讨论过的内容
6. **自然过渡**：问题要符合面试对话的自然流程
7. **深度挖掘**：如果检索到相关内容，要深入询问具体细节

## 面试阶段策略：
- **开场阶段**(1轮)：了解基本情况，缓解紧张感
- **技能验证**(2-6轮)：深入了解技术能力和项目经验  
- **深度评估**(7-10轮)：考察思维方式、解决问题能力
- **收尾阶段**(10+轮)：补充了解、给候选人提问机会

请直接返回纯JSON格式的面试问题，不要包含任何代码块标记、解释或思考过程：

{{
    "type": "context_enhanced_question",
    "category": "问题类别（如：技能验证、项目经验、思维方式等）",
    "question": "具体问题内容（要自然、专业，优先基于检索上下文）",
    "focus": "考察重点",
    "expected_depth": "期望回答深度（basic/medium/high）",
    "interviewer_thinking": "面试官的思考逻辑（为什么问这个问题）",
    "context_used": "是否使用了检索上下文（true/false）"
}}
"""
    
    def _build_follow_up_decision_prompt(self, last_question: str, candidate_answer: str,
                                       resume_context: List[str] = None,
                                       job_context: List[str] = None) -> str:
        """构建追问判断提示词"""
        context_info = self._build_context_info(resume_context, job_context)
        
        return f"""
你是一位经验丰富的面试官。请分析候选人的回答，判断是否需要进行追问。

问题：{last_question}

候选人回答：{candidate_answer}

{context_info}

请根据以下标准判断是否需要追问：

**需要追问的情况：**
1. 回答过于简短或笼统，缺乏具体细节
2. 提到了有趣的技术点但没有深入解释
3. 回答中有专业术语但没有展示真正理解
4. 提到了项目或经验但缺少具体数据和成果
5. 回答与简历信息不一致，需要澄清
6. 涉及岗位核心技能，值得深入了解

**不需要追问的情况：**
1. 回答详细充分，已经展示了相关能力
2. 已经连续追问2次以上同一话题
3. 回答与岗位要求关联度较低
4. 候选人明显对该话题不熟悉，继续追问意义不大
5. 候选人不想回答这个问题

请返回JSON格式：
{{
    "should_follow_up": true/false,
    "reason": "判断原因",
    "follow_up_focus": "如果需要追问，重点关注什么方面",
    "confidence": "high/medium/low",
    "suggested_direction": "建议的追问方向或下一个话题方向"
}}
"""
    
    def _build_follow_up_question_prompt(self, last_question: str, candidate_answer: str,
                                       follow_up_focus: str, resume_context: List[str] = None,
                                       job_context: List[str] = None) -> str:
        """构建追问问题提示词"""
        context_info = self._build_context_info(resume_context, job_context)
        
        return f"""
你是一位专业的面试官，需要基于候选人的回答生成一个精准的追问。

原问题：{last_question}

候选人回答：{candidate_answer}

追问重点：{follow_up_focus}

{context_info}

请生成一个自然、有针对性的追问问题，要求：
1. 基于候选人刚才的回答内容
2. 挖掘更深层的技术细节或实践经验
3. 验证候选人的真实理解程度
4. 保持面试对话的自然流畅
5. 如果有简历信息，可以结合简历内容进行验证

返回JSON格式：
{{
    "type": "follow_up_question",
    "category": "追问类别",
    "question": "具体的追问问题",
    "focus": "考察重点",
    "expected_depth": "期望回答深度（basic/medium/high）",
    "interviewer_thinking": "面试官的思考逻辑",
    "follow_up_level": "第几层追问（first/second/third）"
}}
"""
    
    def _build_context_info(self, resume_context: List[str] = None, 
                           job_context: List[str] = None) -> str:
        """构建上下文信息"""
        context_info = ""
        if resume_context and len(resume_context) > 0:
            context_info += f"""
## 🔍 相关简历片段（基于对话检索）：
{chr(10).join([f"- {ctx}" for ctx in resume_context])}
"""
        
        if job_context and len(job_context) > 0:
            context_info += f"""
## 🎯 相关岗位要求（基于对话检索）：
{chr(10).join([f"- {ctx}" for ctx in job_context])}
"""
        return context_info
    
    def _summarize_conversation_history(self, conversation_history: List) -> str:
        """生成对话历史摘要"""
        if not conversation_history:
            return "这是面试的开始，还没有对话历史。"
        
        topics_discussed = []
        for item in conversation_history:
            if isinstance(item, dict):
                if "category" in item:
                    topics_discussed.append(item["category"])
                elif "question" in item:
                    keywords = self._extract_keywords_from_question(item["question"])
                    topics_discussed.extend(keywords)
        
        if topics_discussed:
            unique_topics = list(set(topics_discussed))
            return f"已经讨论的话题：{', '.join(unique_topics[:5])}"
        else:
            return "对话历史不够清晰，需要从基础开始了解。"
    
    def _extract_keywords_from_question(self, question: str) -> List[str]:
        """从问题中提取关键词"""
        key_terms = ["技能", "项目", "经验", "工作", "学习", "挑战", "团队", "技术"]
        return [term for term in key_terms if term in question]
    
    def _determine_interview_stage(self, current_round: int, conversation_history: List) -> str:
        """判断当前面试阶段"""
        stage_map = {
            (1, 1): "开场阶段 - 建立融洽关系，了解基本情况",
            (2, 6): "技能验证阶段 - 深入了解技术能力和项目经验",
            (7, 10): "深度评估阶段 - 考察思维方式和解决问题能力",
        }
        
        for (start, end), stage in stage_map.items():
            if start <= current_round <= end:
                return stage
        
        return "收尾阶段 - 补充了解，回答候选人问题"
    
