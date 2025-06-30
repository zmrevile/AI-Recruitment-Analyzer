# AI智能面试系统

基于星火大模型的智能面试系统，支持简历分析、岗位匹配和个性化面试问题生成。

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 核心功能

- **简历解析**: 自动提取简历关键信息
- **岗位分析**: 结构化分析岗位要求
- **智能匹配**: 基于向量相似度和LLM分析的综合匹配
- **AI面试**: 基于匹配结果生成个性化面试问题
- **智能追问**: 根据回答内容智能判断是否需要深入追问
- **上下文感知**: 基于对话历史调整问题策略

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd AI-Recruitment-Analyzer

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置星火大模型

在 `app/config/settings.py` 中配置你的星火大模型密钥：

```python
SPARK_CONFIG = {
    "app_id": "your_app_id",
    "api_key": "your_api_key", 
    "api_secret": "your_api_secret",
    # ... 其他配置
}
```

### 3. 启动服务

```bash
# 启动主服务
python main.py
```

服务启动后访问：
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 4. 体验AI面试

```bash
python tests/interactive_interview_test.py
```

## 📋 使用流程

1. **📄 简历上传**: 上传PDF格式简历
2. **💼 岗位配置**: 加载岗位要求（默认AI工程师岗位）
3. **🔍 匹配分析**: 智能计算简历与岗位的匹配度
4. **🎙️ 开始面试**: 基于匹配结果生成个性化面试问题
5. **💬 互动问答**: 与AI面试官进行真实对话
6. **📊 面试总结**: 获得完整的面试记录和分析

## 📡 API接口说明

### 核心API端点

| 端点 | 方法 | 功能 | 说明 |
|------|------|------|------|
| `/health` | GET | 健康检查 | 检查服务状态 |
| `/api/resume/upload` | POST | 上传简历 | 支持PDF格式 |
| `/api/job/upload-requirement` | POST | 加载岗位要求 | 默认AI工程师岗位 |
| `/api/match/analyze` | POST | 匹配度分析 | 智能匹配算法 |
| `/api/interview/start` | POST | 开始面试 | 创建面试会话 |
| `/api/interview/answer` | POST | 提交回答 | 获取下一个问题 |
| `/api/interview/history/{session_id}` | GET | 面试历史 | 获取对话记录 |

### JavaScript调用示例

```javascript
// 基础配置
const API_BASE_URL = 'http://localhost:8000';

// 通用请求函数
async function apiGet(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    return await response.json();
}

async function apiPost(endpoint, data = null) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: data ? JSON.stringify(data) : null
    });
    return await response.json();
}

// 文件上传
async function uploadResume(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/resume/upload`, {
        method: 'POST',
        body: formData
    });
    return await response.json();
}

// 完整流程示例
async function completeInterviewFlow() {
    try {
        // 1. 检查服务状态
        await apiGet('/health');
        
        // 2. 上传简历
        const file = document.getElementById('resumeFile').files[0];
        await uploadResume(file);
        
        // 3. 加载岗位要求
        await apiPost('/api/job/upload-requirement');
        
        // 4. 分析匹配度
        const matchResult = await apiPost('/api/match/analyze');
        console.log(`匹配度: ${matchResult.match_report.total_score}`);
        
        // 5. 开始面试
        const interview = await apiPost('/api/interview/start');
        console.log('面试开始:', interview.question);
        
        // 6. 提交回答
        const nextQuestion = await apiPost('/api/interview/answer', {
            session_id: interview.session_id,
            answer: "这是我的回答"
        });
        
    } catch (error) {
        console.error('流程执行失败:', error);
    }
}
```

### Python调用示例

```python
import requests

# 1. 上传简历
with open('resume.pdf', 'rb') as f:
    files = {'file': ('resume.pdf', f, 'application/pdf')}
    response = requests.post('http://localhost:8000/api/resume/upload', files=files)

# 2. 加载岗位要求
requests.post('http://localhost:8000/api/job/upload-requirement')

# 3. 分析匹配度
match_result = requests.post('http://localhost:8000/api/match/analyze').json()
print(f"匹配度: {match_result['match_report']['total_score']:.3f}")

# 4. 开始面试
interview = requests.post('http://localhost:8000/api/interview/start').json()
print(f"第一个问题: {interview['question']}")
```

## 🔧 技术特性

### AI能力
- **星火大模型**: 使用星火4.0 Ultra模型进行对话生成
- **本地向量化**: 基于sentence-transformers本地模型，无需API密钥
- **智能匹配**: 结合向量相似度(20%)和LLM分析(80%)的双重保障
- **上下文记忆**: 基于对话历史的智能问题生成

### 匹配算法
- **向量相似度**: 使用余弦相似度计算语义匹配  
- **LLM分析**: 大模型深度分析技能和经验匹配
- **加权评分**: 向量相似度20% + LLM分析80%
- **匹配等级**: 自动判定匹配等级和推荐决策

### 系统优势
- **本地化**: embedding模型完全本地运行，无网络依赖
- **高精度**: 修复了向量相似度虚高问题，匹配结果准确
- **易部署**: 基于FastAPI，支持多种部署方式
- **可扩展**: 模块化架构，易于扩展新功能

## 🏗️ 项目结构

```
AI-Recruitment-Analyzer/
├── main.py                    # 项目启动入口
├── requirements.txt           # 项目依赖
├── app/
│   ├── main.py               # FastAPI应用
│   ├── api/                  # API路由层
│   │   ├── resume.py         # 简历管理
│   │   ├── job.py            # 岗位管理
│   │   ├── match.py          # 匹配分析
│   │   └── interview.py      # 面试管理
│   ├── services/             # 业务逻辑层
│   │   ├── resume_analyzer.py
│   │   ├── job_analyzer.py
│   │   ├── resume_job_matcher.py
│   │   └── enhanced_interview_generator.py
│   ├── core/                 # 核心组件
│   │   ├── spark_llm.py      # 星火大模型
│   │   └── spark_embedding.py # 本地向量化
│   ├── config/               # 配置管理
│   └── utils/                # 工具函数
├── tests/                    # 测试模块
└── logs/                     # 日志文件
```

## 🛠️ 开发指南

### 开发模式启动
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 添加新功能
1. 在 `app/api/` 中添加新的路由文件
2. 在 `app/services/` 中实现具体业务逻辑
3. 在 `app/models/` 中定义数据结构

## 🎯 适用场景

- **HR初筛**: 自动化简历筛选和初步面试
- **技术面试**: 技术岗位的专业技能评估
- **面试培训**: 候选人面试技巧训练
- **招聘效率**: 提升招聘流程的效率和标准化

## 🔒 注意事项

1. **API密钥**: 需要配置星火大模型API密钥
2. **文件格式**: 目前仅支持PDF格式简历
3. **数据隐私**: 简历数据仅用于分析，不会永久存储

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

🚀 **开始你的AI面试之旅吧！** 

如有问题或建议，请提交Issue或联系开发团队。 