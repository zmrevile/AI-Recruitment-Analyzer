基于星火大模型的智能面试系统，支持简历分析、岗位匹配和个性化面试问题生成。

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 核心功能

### 🎯 **智能匹配分析**
- **简历解析**: 自动提取简历关键信息
- **岗位分析**: 结构化分析岗位要求
- **智能匹配**: 基于向量相似度和LLM分析的综合匹配
- **匹配报告**: 详细的匹配度分析和推荐建议

### 🎙️ **AI面试体验**
- **动态问题生成**: 基于简历和岗位要求个性化生成面试问题
- **智能追问**: 根据回答内容智能判断是否需要深入追问
- **上下文感知**: 基于对话历史和简历内容调整问题策略
- **真实面试流程**: 模拟真实面试官的思维过程

### 📊 **数据分析**
- **向量语义搜索**: 使用Chroma向量数据库进行语义检索
- **多维度评估**: 技能匹配、经验适配、综合评分
- **可视化报告**: 详细的分析结果和建议

## 🏗️ 项目架构

```
langchain/
├── main.py                    # 🚀 项目启动入口
├── requirements.txt           # 📦 项目依赖
├── .gitignore                # 🚫 Git忽略文件
├── README.md                 # 📖 项目文档
│
├── app/                      # 🏗️ 主应用模块
│   ├── __init__.py
│   ├── main.py              # 🎯 FastAPI应用
│   │
│   ├── api/                 # 🌐 API路由层
│   │   ├── __init__.py
│   │   ├── main.py          # 路由汇总
│   │   ├── job.py           # 岗位管理API
│   │   ├── resume.py        # 简历管理API
│   │   ├── match.py         # 匹配分析API
│   │   └── interview.py     # 面试管理API
│   │
│   ├── models/              # 📋 数据模型层
│   │   ├── __init__.py
│   │   └── interview.py     # 面试相关模型
│   │
│   ├── services/            # 🛠️ 业务逻辑层
│   │   ├── __init__.py
│   │   ├── resume_analyzer.py        # 简历分析服务
│   │   ├── job_analyzer.py           # 岗位分析服务
│   │   ├── resume_job_matcher.py     # 匹配分析服务
│   │   └── enhanced_interview_generator.py  # 面试生成服务
│   │
│   ├── core/                # ⚡ 核心组件层
│   │   ├── __init__.py
│   │   ├── spark_llm.py     # 星火大模型包装器
│   │   └── spark_embedding.py  # 星火向量化服务
│   │
│   ├── config/              # ⚙️ 配置管理层
│   │   ├── __init__.py
│   │   └── settings.py      # 配置文件
│   │
│   └── utils/               # 🔧 工具函数层
│       ├── __init__.py
│       ├── logger.py        # 日志工具
│       └── json_helper.py   # JSON处理工具
│
├── data/                    # 📂 数据文件
│
├── tests/                   # 🧪 测试模块
│   ├── __init__.py
│   └── interactive_interview_test.py
│
├── docs/                    # 📚 文档目录
└── logs/                    # 📜 日志文件
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd langchain

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

在新的终端窗口中运行交互式测试：

```bash
python tests/interactive_interview_test.py
```

## 📋 使用流程

### 完整面试流程

1. **📄 简历上传**: 上传PDF格式简历
2. **💼 岗位配置**: 加载岗位要求（默认AI工程师岗位）
3. **🔍 匹配分析**: 智能计算简历与岗位的匹配度
4. **🎙️ 开始面试**: 基于匹配结果生成个性化面试问题
5. **💬 互动问答**: 与AI面试官进行真实对话
6. **📊 面试总结**: 获得完整的面试记录和分析

### API使用示例

```python
import requests

# 1. 上传简历
with open('resume.pdf', 'rb') as f:
    files = {'file': ('resume.pdf', f, 'application/pdf')}
    response = requests.post('http://localhost:8000/api/resume/upload', files=files)

# 2. 加载岗位要求
response = requests.post('http://localhost:8000/api/job/upload-requirement')

# 3. 分析匹配度
response = requests.post('http://localhost:8000/api/match/analyze')
match_result = response.json()
print(f"匹配度: {match_result['match_report']['total_score']:.3f}")

# 4. 开始面试
response = requests.post('http://localhost:8000/api/interview/start')
first_question = response.json()
print(f"第一个问题: {first_question}")
```

## 🔧 技术特性

### 🧠 **AI能力**
- **星火大模型集成**: 使用最新的星火4.0 Ultra模型
- **智能向量化**: 基于星火官方Embedding API
- **语义理解**: 深度理解简历内容和岗位要求
- **动态问题生成**: 实时生成个性化面试问题

### 📊 **匹配算法**
- **向量相似度**: 使用余弦相似度计算语义匹配
- **LLM智能分析**: 大模型深度分析技能和经验匹配
- **加权评分**: 综合多维度因素的智能评分
- **匹配等级**: 自动判定匹配等级和推荐决策

### 🎯 **面试策略**
- **分阶段面试**: 开场、技能验证、深度评估、收尾
- **智能追问**: 基于回答质量自动判断是否深入追问
- **上下文记忆**: 记住前面的对话，避免重复提问
- **个性化调整**: 根据候选人背景调整问题难度

## 📚 API文档

### 核心API端点

| 端点 | 方法 | 功能 | 说明 |
|------|------|------|------|
| `/api/resume/upload` | POST | 上传简历 | 支持PDF格式 |
| `/api/job/upload-requirement` | POST | 加载岗位要求 | 默认AI工程师岗位 |
| `/api/match/analyze` | POST | 匹配度分析 | 计算简历与岗位匹配度 |
| `/api/interview/start` | POST | 开始面试 | 创建面试会话 |
| `/api/interview/answer` | POST | 提交回答 | 获取下一个问题 |
| `/api/interview/history/{session_id}` | GET | 面试历史 | 获取对话记录 |
| `/health` | GET | 健康检查 | 服务状态检查 |

详细API文档请访问: http://localhost:8000/docs

## 🛠️ 开发指南

### 开发模式启动

```bash
# 热重载模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 添加新功能

1. **添加API端点**: 在 `app/api/` 中添加新的路由文件
2. **业务逻辑**: 在 `app/services/` 中实现具体功能
3. **数据模型**: 在 `app/models/` 中定义数据结构
4. **工具函数**: 在 `app/utils/` 中添加通用工具

### 测试

```bash
# 运行交互式测试
python tests/interactive_interview_test.py

# 添加新的测试文件到 tests/ 目录
```

## 📊 系统特点

### ✅ **优势**
- 🚀 **高精度匹配**: 结合向量相似度和LLM分析，匹配准确率高
- 🧠 **智能对话**: 像真实面试官一样思考和提问
- 📈 **可扩展性**: 模块化架构，易于扩展新功能
- 🔧 **易于部署**: 基于FastAPI，支持多种部署方式
- 📱 **用户友好**: 完整的API文档和交互式测试

### 🎯 **适用场景**
- **HR初筛**: 自动化简历筛选和初步面试
- **技术面试**: 技术岗位的专业技能评估
- **面试培训**: 候选人面试技巧训练
- **招聘效率**: 提升招聘流程的效率和标准化

## 🔒 注意事项

1. **API密钥安全**: 请妥善保管星火大模型API密钥
2. **数据隐私**: 简历数据仅用于分析，不会永久存储
3. **网络要求**: 需要稳定的网络连接访问星火API
4. **文件格式**: 目前仅支持PDF格式简历

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建功能分支: `git checkout -b feature/新功能`
3. 提交更改: `git commit -am '添加新功能'`
4. 推送分支: `git push origin feature/新功能`
5. 提交Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [星火大模型](https://www.xfyun.cn/) - 提供强大的AI能力
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能Web框架
- [LangChain](https://langchain.com/) - AI应用开发框架
- [Chroma](https://www.trychroma.com/) - 向量数据库

---

🚀 **开始你的AI面试之旅吧！** 

如有问题或建议，请提交Issue或联系开发团队。 