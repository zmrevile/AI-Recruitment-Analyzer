"""
AI智能面试系统 4.0 - 项目启动脚本
"""
import sys
import os

# 将项目根目录添加到Python路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 