"""
全局状态管理器 - 管理分析器实例，避免循环导入
"""
from app.config.settings import get_spark_config
from app.services.resume_analyzer import ResumeAnalyzer
from app.services.job_analyzer import JobAnalyzer

# 全局变量存储分析器实例
_resume_analyzer = None
_job_analyzer = None


def get_resume_analyzer():
    """获取简历分析器实例"""
    global _resume_analyzer
    if _resume_analyzer is None:
        _resume_analyzer = ResumeAnalyzer(get_spark_config())
    return _resume_analyzer


def get_job_analyzer():
    """获取岗位分析器实例"""
    global _job_analyzer
    if _job_analyzer is None:
        _job_analyzer = JobAnalyzer(get_spark_config())
    return _job_analyzer


def reset_analyzers():
    """重置所有分析器实例"""
    global _resume_analyzer, _job_analyzer
    _resume_analyzer = None
    _job_analyzer = None 