"""
JSON处理工具模块
统一处理LLM响应的JSON解析、清理和错误处理
"""
import json
import re
import string
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class JSONHelper:
    """JSON处理帮助类，统一处理LLM响应的JSON解析"""
    
    @staticmethod
    def parse_llm_response(response_content: str, operation_name: str = "JSON解析") -> Optional[Dict]:
        """
        统一的LLM响应JSON解析方法
        
        Args:
            response_content: LLM原始响应内容
            operation_name: 操作名称，用于日志输出
            
        Returns:
            解析后的JSON字典，失败时返回None
        """
        # 清理响应内容
        cleaned_content = JSONHelper._clean_response_content(response_content)
        
        # 尝试直接解析
        try:
            result = json.loads(cleaned_content)
            logger.info(f"✅ {operation_name}直接解析成功!")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"❌ {operation_name}失败: {e}")
            logger.debug(f"🔍 原始内容前200字符: {repr(response_content[:200])}")
            logger.debug(f"🔍 清理后内容前200字符: {repr(cleaned_content[:200])}")
            logger.error(f"❌ JSON解析错误详情:")
            logger.error(f"   错误位置: 第{e.lineno}行, 第{e.colno}列")
            logger.error(f"   错误信息: {e.msg}")
            
            # 尝试高级清理
            better_cleaned = JSONHelper._advanced_json_cleaning(response_content)
            if better_cleaned and better_cleaned != cleaned_content:
                logger.debug(f"🧹 高级清理后内容: {repr(better_cleaned[:200])}")
                try:
                    result = json.loads(better_cleaned)
                    logger.info(f"✅ {operation_name}高级清理解析成功!")
                    return result
                except json.JSONDecodeError as e2:
                    logger.error(f"❌ 高级清理后仍然失败: {e2}")
            
            # 尝试智能提取
            extracted_json = JSONHelper._extract_json_from_text(response_content)
            if extracted_json:
                extracted_json = JSONHelper._remove_control_characters(extracted_json)
                try:
                    result = json.loads(extracted_json)
                    logger.info(f"✅ {operation_name}智能提取成功!")
                    return result
                except json.JSONDecodeError:
                    logger.error(f"❌ {operation_name}智能提取仍然无效")
            
            return None
    
    @staticmethod
    def _clean_response_content(content: str) -> str:
        """基础的响应内容清理"""
        cleaned_content = content.strip()
        
        # 移除BOM字符
        if cleaned_content.startswith('\ufeff'):
            cleaned_content = cleaned_content[1:]
        
        # 移除代码块标记
        if cleaned_content.startswith('```json'):
            cleaned_content = cleaned_content[7:]
        elif cleaned_content.startswith('```'):
            cleaned_content = cleaned_content[3:]
        
        if cleaned_content.endswith('```'):
            cleaned_content = cleaned_content[:-3]
        
        cleaned_content = cleaned_content.strip()
        
        # 清理控制字符和特殊字符
        cleaned_content = JSONHelper._remove_control_characters(cleaned_content)
        
        return cleaned_content
    
    @staticmethod
    def _remove_control_characters(text: str) -> str:
        """移除JSON中的控制字符和特殊字符"""
        # 移除所有控制字符，但保留换行符、制表符和回车符
        printable = set(string.printable)
        cleaned = ''.join(char for char in text if char in printable or char.isprintable())
        
        # 替换常见的问题字符
        replacements = {
            '\x00': '', '\x01': '', '\x02': '', '\x03': '', '\x04': '', '\x05': '',
            '\x06': '', '\x07': '', '\x08': '', '\x0b': '', '\x0c': '', '\x0e': '',
            '\x0f': '', '\x10': '', '\x11': '', '\x12': '', '\x13': '', '\x14': '',
            '\x15': '', '\x16': '', '\x17': '', '\x18': '', '\x19': '', '\x1a': '',
            '\x1b': '', '\x1c': '', '\x1d': '', '\x1e': '', '\x1f': '',
        }
        
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        
        return cleaned
    
    @staticmethod
    def _extract_json_from_text(response_text: str) -> Optional[str]:
        """从响应文本中智能提取JSON"""
        text = response_text.strip()
        
        # 查找JSON代码块
        patterns = [
            r'```json\s*(.*?)\s*```',  # ```json ... ```
            r'```\s*(.*?)\s*```',      # ``` ... ```
            r'\{.*\}'                  # { ... }
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content = match.group(1) if pattern != r'\{.*\}' else match.group(0)
                logger.debug(f"🔍 找到JSON内容: {content[:100]}...")
                return content.strip()
        
        return None
    
    @staticmethod
    def _advanced_json_cleaning(response_text: str) -> Optional[str]:
        """高级JSON清理方法"""
        text = response_text.strip()
        
        # 移除BOM字符
        if text.startswith('\ufeff'):
            text = text[1:]
        
        # 尝试多种模式提取JSON
        patterns = [
            r'```json\s*(.*?)\s*```',  # json代码块
            r'```\s*(.*?)\s*```',      # 普通代码块
            r'(?s)\{.*\}',             # 第一个完整的JSON对象
            r'(?s)\[.*\]'              # JSON数组
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content = match.group(1) if pattern.startswith(r'```') else match.group(0)
                content = content.strip()
                
                # 高级清理
                content = JSONHelper._fix_common_json_issues(content)
                
                # 验证是否为有效JSON
                try:
                    json.loads(content)
                    return content
                except json.JSONDecodeError:
                    continue
        
        return None
    
    @staticmethod
    def _fix_common_json_issues(content: str) -> str:
        """修复常见的JSON格式问题"""
        # 移除控制字符
        content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
        
        # 修复单引号为双引号（更精确的匹配）
        content = re.sub(r"'([^']*)':", r'"\1":', content)  # 键的单引号
        content = re.sub(r":\s*'([^']*)'", r': "\1"', content)  # 值的单引号
        
        # 修复尾部逗号
        content = re.sub(r',(\s*[}\]])', r'\1', content)
        
        # 修复缺少引号的键
        content = re.sub(r'(\w+):', r'"\1":', content)
        
        # 修复缺少引号的字符串值（不是数字、布尔值或null）
        content = re.sub(r':\s*([^",\[\]{}0-9][^",\[\]{}]*?)([,}\]])', r': "\1"\2', content)
        
        # 修复换行问题
        content = re.sub(r'\n\s*', ' ', content)
        
        return content.strip()
    
    @staticmethod
    def safe_parse_with_fallback(response_content: str, 
                                operation_name: str = "JSON解析",
                                fallback_data: Optional[Dict] = None) -> Dict:
        """
        安全的JSON解析，带回退选项
        
        Args:
            response_content: LLM响应内容
            operation_name: 操作名称
            fallback_data: 解析失败时的回退数据
            
        Returns:
            解析成功的JSON字典或回退数据
        """
        result = JSONHelper.parse_llm_response(response_content, operation_name)
        
        if result is not None:
            return result
        
        # 使用回退数据
        if fallback_data is not None:
            logger.warning(f"⚠️ {operation_name}失败，使用回退数据")
            return fallback_data
        
        # 默认回退数据
        logger.warning(f"⚠️ {operation_name}失败，使用默认回退数据")
        return {
            "error": "JSON解析失败",
            "raw_response": response_content[:200] + "..." if len(response_content) > 200 else response_content
        } 