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

## 📋 特别提醒：
{self._get_smart_interview_guidance(current_round, conversation_history, job_info)}

{context_info}

## 面试进展：
- 当前是第{current_round}个问题
- 面试阶段：{interview_stage}

## 对话历史摘要：
{history_summary}

## 面试官指导原则：
1. **智能阶段判断**：根据对话历史和候选人回答质量，智能判断当前应该问基础知识还是项目经验
2. **基础优先**：在深入项目之前，先验证岗位核心技能的基础知识
3. **利用检索上下文**：优先基于检索到的相关简历片段和岗位要求进行提问
4. **像真正面试官一样思考**：考虑候选人的背景、岗位要求和已经了解的信息
5. **循序渐进**：先基础知识，再项目经验，最后深度思维
6. **有针对性**：基于岗位要求的核心技能进行重点提问
7. **避免重复**：不要问已经讨论过的内容
8. **自然过渡**：问题要符合面试对话的自然流程
9. **深度挖掘**：如果检索到相关内容，要深入询问具体细节
10. **灵活调整**：如果候选人基础扎实，可以提前进入项目阶段；如果基础薄弱，继续巩固基础知识

## 面试流程策略（软约束，灵活调整）：

### 第一个问题固定要求：
第一个问题必须是自我介绍，例如：
- "请简单介绍一下您自己，包括您的技术背景和工作经历"
- "能否请您先做个自我介绍，重点说说您的技术经验"
- "我们先从自我介绍开始吧，请谈谈您的专业背景和技术特长"

### 后续问题智能策略：
面试官应该根据对话进展和候选人回答质量，灵活选择问题类型：

**阶段1 - 基础专业知识验证（优先级高）：**
- 先验证岗位要求的核心技能和基础知识
- 问一些该岗位必须掌握的基本概念和技术
- 确保候选人具备基础的专业素养
- 例如：算法基础、编程语言特性、基本架构概念等

**阶段2 - 项目经验深入（在基础验证后）：**
- 当候选人展示了足够的基础知识后，再深入项目经验
- 询问项目的技术实现细节、遇到的挑战、解决方案
- 验证理论知识在实际项目中的应用能力
- 了解候选人的项目贡献和技术成长

**阶段3 - 深度思维考察：**
- 考察解决问题的思路和方法
- 了解学习能力和适应能力
- 评估技术视野和发展潜力

**智能判断原则：**
- 如果候选人基础知识回答得不够好，继续问基础问题，暂不进入项目阶段
- 如果候选人展示了扎实的基础，可以提前进入项目经验阶段
- 根据岗位要求的核心技能，优先验证最重要的基础知识
- 不要死板地按轮次执行，要根据候选人的实际表现灵活调整

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
5. 候选人明确表示不想回答这个问题

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
    
    def _get_smart_interview_guidance(self, current_round: int, conversation_history: List, job_info: Dict) -> str:
        """智能生成面试指导建议"""
        if current_round == 1:
            return "⚠️ 这是第一个问题，必须是自我介绍相关的问题！不要问具体的技术或项目问题。"
        
        # 分析对话历史，判断是否已经充分验证基础知识
        basic_knowledge_covered = self._analyze_basic_knowledge_coverage(conversation_history, job_info)
        project_questions_asked = self._analyze_project_questions_coverage(conversation_history)
        
        if not basic_knowledge_covered:
            return f"""
🎯 当前建议：优先验证基础专业知识
- 重点关注岗位要求的核心技能基础知识
- 先确保候选人具备必要的理论基础
- 暂时不要深入项目细节，除非候选人主动提及且回答充分
- 可以问一些该岗位必须掌握的基本概念和技术原理
"""
        elif not project_questions_asked:
            return f"""
✅ 基础知识验证阶段已完成，建议进入项目经验阶段
- 可以开始深入了解候选人的项目经验
- 重点询问项目的技术实现细节、遇到的挑战、解决方案
- 验证理论知识在实际项目中的应用能力
- 了解候选人的具体贡献和技术成长
"""
        else:
            return f"""
🔍 进入深度评估阶段
- 可以考察解决问题的思路和方法
- 了解学习能力和适应能力
- 评估技术视野和发展潜力
- 或者针对之前回答不够详细的地方进行深入追问
"""

    def _analyze_basic_knowledge_coverage(self, conversation_history: List, job_info: Dict) -> bool:
        """分析是否已经充分验证了基础知识"""
        if not conversation_history or len(conversation_history) < 4:  # 至少需要2轮问答
            return False
        
        # 简单的关键词匹配来判断是否问过基础问题
        basic_keywords = ["算法", "数据结构", "原理", "概念", "基础", "理论", "定义", "区别", "优缺点"]
        
        questions_content = []
        for msg in conversation_history:
            if hasattr(msg, 'content'):
                questions_content.append(msg.content.lower())
        
        questions_text = " ".join(questions_content)
        basic_question_count = sum(1 for keyword in basic_keywords if keyword in questions_text)
        
        # 如果问过至少2个基础问题，认为基础知识验证已经开始
        return basic_question_count >= 2

    def _analyze_project_questions_coverage(self, conversation_history: List) -> bool:
        """分析是否已经问过项目相关问题"""
        if not conversation_history:
            return False
        
        project_keywords = ["项目", "开发", "实现", "架构", "技术栈", "挑战", "解决方案", "经验"]
        
        questions_content = []
        for msg in conversation_history:
            if hasattr(msg, 'content'):
                questions_content.append(msg.content.lower())
        
        questions_text = " ".join(questions_content)
        project_question_count = sum(1 for keyword in project_keywords if keyword in questions_text)
        
        return project_question_count >= 2

    def _determine_interview_stage(self, current_round: int, conversation_history: List) -> str:
        """判断当前面试阶段"""
        if current_round == 1:
            return "开场阶段 - 自我介绍"
        elif current_round <= 3:
            return "基础知识验证阶段 - 了解专业基础"
        elif current_round <= 8:
            return "项目经验阶段 - 深入了解实践能力"
        else:
            return "深度评估阶段 - 综合能力考察"
    
