"""
统一的日志配置模块
提供项目范围内的日志管理功能
"""
import logging
import os
from datetime import datetime
from pathlib import Path

class LoggerConfig:
    """日志配置类"""
    
    @staticmethod
    def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
        """
        设置日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            配置好的日志记录器
        """
        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 创建日志记录器
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # 文件处理器 - 所有日志
        today = datetime.now().strftime('%Y-%m-%d')
        file_handler = logging.FileHandler(
            log_dir / f"app_{today}.log", 
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # 错误日志文件处理器
        error_handler = logging.FileHandler(
            log_dir / f"error_{today}.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # 添加处理器到日志记录器
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        
        return logger

# 创建不同模块的日志记录器
def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器"""
    return LoggerConfig.setup_logger(name)

# 预定义的日志记录器
main_logger = get_logger("main")
spark_llm_logger = get_logger("spark_llm")
spark_embedding_logger = get_logger("spark_embedding")
resume_analyzer_logger = get_logger("resume_analyzer")
job_analyzer_logger = get_logger("job_analyzer")
interview_generator_logger = get_logger("interview_generator")
resume_matcher_logger = get_logger("resume_matcher") 