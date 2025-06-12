# 🌐 API调用指南 - JavaScript版

本文档详细说明如何使用JavaScript调用AI智能面试系统的后端API接口。

## 📋 目录
- [基础配置](#基础配置)
- [API接口说明](#api接口说明)
- [完整使用流程](#完整使用流程)
- [错误处理](#错误处理)
- [实际应用示例](#实际应用示例)

## 🔧 基础配置

### API基础信息
```javascript
const API_BASE_URL = 'http://localhost:8000';

// 通用请求头
const defaultHeaders = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
};

// 通用请求配置
const requestConfig = {
    mode: 'cors',
    credentials: 'same-origin'
};
```

### 通用请求函数
```javascript
// 封装GET请求
async function apiGet(endpoint) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'GET',
            headers: defaultHeaders,
            ...requestConfig
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('GET请求失败:', error);
        throw error;
    }
}

// 封装POST请求
async function apiPost(endpoint, data = null) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: defaultHeaders,
            body: data ? JSON.stringify(data) : null,
            ...requestConfig
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('POST请求失败:', error);
        throw error;
    }
}

// 封装文件上传请求
async function apiUpload(endpoint, formData) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            body: formData, // 不设置Content-Type，让浏览器自动设置
            ...requestConfig
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('文件上传失败:', error);
        throw error;
    }
}
```

## 📡 API接口说明

### 1. 🔍 健康检查
```javascript
/**
 * 检查服务器健康状态
 * @returns {Promise<Object>} 健康状态信息
 */
async function checkHealth() {
    const result = await apiGet('/health');
    console.log('服务状态:', result);
    return result;
}

// 使用示例
checkHealth().then(data => {
    console.log('✅ 服务正常:', data.status);
}).catch(error => {
    console.error('❌ 服务异常:', error);
});
```

### 2. 📄 简历上传
```javascript
/**
 * 上传简历文件
 * @param {File} file - PDF简历文件
 * @returns {Promise<Object>} 上传结果
 */
async function uploadResume(file) {
    // 验证文件类型
    if (file.type !== 'application/pdf') {
        throw new Error('只支持PDF格式的简历文件');
    }
    
    // 验证文件大小 (限制10MB)
    if (file.size > 10 * 1024 * 1024) {
        throw new Error('文件大小不能超过10MB');
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    const result = await apiUpload('/api/resume/upload', formData);
    console.log('简历上传成功:', result);
    return result;
}

// 使用示例 - 从HTML文件输入获取
document.getElementById('resumeFile').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (file) {
        try {
            const result = await uploadResume(file);
            alert(`✅ 简历上传成功！\n解析内容: ${result.summary}`);
        } catch (error) {
            alert(`❌ 上传失败: ${error.message}`);
        }
    }
});
```

### 3. 💼 岗位要求管理
```javascript
/**
 * 上传岗位要求（使用默认AI工程师岗位）
 * @returns {Promise<Object>} 上传结果
 */
async function uploadJobRequirement() {
    const result = await apiPost('/api/job/upload-requirement');
    console.log('岗位要求加载成功:', result);
    return result;
}

/**
 * 上传自定义岗位要求
 * @param {string} jobDescription - 岗位描述文本
 * @returns {Promise<Object>} 上传结果
 */
async function uploadCustomJobRequirement(jobDescription) {
    const data = {
        job_description: jobDescription,
        job_title: "自定义岗位",
        requirements: jobDescription
    };
    
    const result = await apiPost('/api/job/upload-custom', data);
    console.log('自定义岗位要求上传成功:', result);
    return result;
}

// 使用示例
uploadJobRequirement().then(data => {
    console.log('✅ 默认岗位加载成功');
}).catch(error => {
    console.error('❌ 岗位加载失败:', error);
});
```

### 4. 🔍 匹配度分析
```javascript
/**
 * 分析简历与岗位的匹配度
 * @returns {Promise<Object>} 匹配分析结果
 */
async function analyzeMatch() {
    const result = await apiPost('/api/match/analyze');
    console.log('匹配分析完成:', result);
    return result;
}

/**
 * 解析匹配结果
 * @param {Object} matchResult - 匹配分析结果
 */
function parseMatchResult(matchResult) {
    const { match_report } = matchResult;
    
    return {
        totalScore: match_report.total_score,
        vectorScore: match_report.vector_similarity_score,
        llmScore: match_report.llm_analysis_score,
        matchLevel: match_report.match_level,
        recommendation: match_report.recommendation,
        strengths: match_report.analysis_details.strengths,
        weaknesses: match_report.analysis_details.weaknesses,
        suggestions: match_report.analysis_details.suggestions
    };
}

// 使用示例
analyzeMatch().then(data => {
    const result = parseMatchResult(data);
    console.log(`✅ 匹配度分析完成:`);
    console.log(`   总分: ${(result.totalScore * 100).toFixed(1)}%`);
    console.log(`   匹配等级: ${result.matchLevel}`);
    console.log(`   推荐决策: ${result.recommendation}`);
    console.log(`   优势: ${result.strengths.join(', ')}`);
    console.log(`   不足: ${result.weaknesses.join(', ')}`);
}).catch(error => {
    console.error('❌ 匹配分析失败:', error);
});
```

### 5. 🎙️ 面试管理
```javascript
/**
 * 开始面试会话
 * @returns {Promise<Object>} 面试开始结果
 */
async function startInterview() {
    const result = await apiPost('/api/interview/start');
    console.log('面试开始:', result);
    return result;
}

/**
 * 提交面试回答
 * @param {string} sessionId - 面试会话ID
 * @param {string} answer - 候选人回答
 * @returns {Promise<Object>} 下个问题或面试结果
 */
async function submitAnswer(sessionId, answer) {
    const data = {
        session_id: sessionId,
        answer: answer
    };
    
    const result = await apiPost('/api/interview/answer', data);
    console.log('回答提交成功:', result);
    return result;
}

/**
 * 获取面试历史
 * @param {string} sessionId - 面试会话ID
 * @returns {Promise<Object>} 面试对话历史
 */
async function getInterviewHistory(sessionId) {
    const result = await apiGet(`/api/interview/history/${sessionId}`);
    console.log('面试历史:', result);
    return result;
}

// 使用示例
let currentSessionId = null;

startInterview().then(data => {
    currentSessionId = data.session_id;
    console.log(`✅ 面试开始 (会话ID: ${currentSessionId})`);
    console.log(`🤖 面试官: ${data.question}`);
    
    // 这里可以显示问题给用户
    displayQuestion(data.question);
}).catch(error => {
    console.error('❌ 面试开始失败:', error);
});
```

## 🔄 完整使用流程

### 完整的面试流程示例
```javascript
class InterviewSystem {
    constructor() {
        this.sessionId = null;
        this.interviewHistory = [];
    }
    
    /**
     * 完整的面试流程
     */
    async startCompleteInterview(file) {
        try {
            // 1. 检查服务健康状态
            console.log('🔍 检查服务状态...');
            await this.checkHealth();
            
            // 2. 上传简历
            console.log('📄 上传简历...');
            const resumeResult = await this.uploadResume(file);
            
            // 3. 加载岗位要求
            console.log('💼 加载岗位要求...');
            await this.uploadJobRequirement();
            
            // 4. 分析匹配度
            console.log('🔍 分析匹配度...');
            const matchResult = await this.analyzeMatch();
            this.displayMatchResult(matchResult);
            
            // 5. 开始面试
            console.log('🎙️ 开始面试...');
            const interviewResult = await this.startInterview();
            this.sessionId = interviewResult.session_id;
            
            console.log('✅ 面试系统准备就绪！');
            return {
                sessionId: this.sessionId,
                firstQuestion: interviewResult.question,
                matchResult: matchResult
            };
            
        } catch (error) {
            console.error('❌ 面试流程失败:', error);
            throw error;
        }
    }
    
    /**
     * 提交回答并获取下一个问题
     */
    async continueInterview(answer) {
        if (!this.sessionId) {
            throw new Error('面试会话未开始');
        }
        
        try {
            const result = await submitAnswer(this.sessionId, answer);
            
            // 记录对话历史
            this.interviewHistory.push({
                type: 'answer',
                content: answer,
                timestamp: new Date()
            });
            
            if (result.question) {
                this.interviewHistory.push({
                    type: 'question',
                    content: result.question,
                    timestamp: new Date()
                });
                
                return {
                    hasNextQuestion: true,
                    question: result.question,
                    isFollowUp: result.is_follow_up || false
                };
            } else {
                // 面试结束
                return {
                    hasNextQuestion: false,
                    summary: result.interview_summary || '面试已完成',
                    history: this.interviewHistory
                };
            }
            
        } catch (error) {
            console.error('❌ 提交回答失败:', error);
            throw error;
        }
    }
    
    /**
     * 获取完整面试历史
     */
    async getFullHistory() {
        if (!this.sessionId) {
            throw new Error('面试会话未开始');
        }
        
        return await getInterviewHistory(this.sessionId);
    }
    
    // 辅助方法
    async checkHealth() {
        return await checkHealth();
    }
    
    async uploadResume(file) {
        return await uploadResume(file);
    }
    
    async uploadJobRequirement() {
        return await uploadJobRequirement();
    }
    
    async analyzeMatch() {
        return await analyzeMatch();
    }
    
    async startInterview() {
        return await startInterview();
    }
    
    displayMatchResult(matchResult) {
        const result = parseMatchResult(matchResult);
        console.log(`📊 匹配分析结果:`);
        console.log(`   ✨ 总体匹配度: ${(result.totalScore * 100).toFixed(1)}%`);
        console.log(`   🎯 匹配等级: ${result.matchLevel}`);
        console.log(`   💡 推荐决策: ${result.recommendation}`);
    }
}
```

### 实际使用示例
```javascript
// 创建面试系统实例
const interviewSystem = new InterviewSystem();

// HTML中的使用示例
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('resumeFile');
    const startButton = document.getElementById('startInterview');
    const answerInput = document.getElementById('answerInput');
    const submitButton = document.getElementById('submitAnswer');
    const questionDiv = document.getElementById('question');
    const historyDiv = document.getElementById('history');
    
    // 开始面试
    startButton.addEventListener('click', async () => {
        const file = fileInput.files[0];
        if (!file) {
            alert('请先选择简历文件');
            return;
        }
        
        try {
            startButton.disabled = true;
            startButton.textContent = '准备中...';
            
            const result = await interviewSystem.startCompleteInterview(file);
            
            // 显示第一个问题
            questionDiv.innerHTML = `
                <div class="question">
                    <h3>🤖 面试官：</h3>
                    <p>${result.firstQuestion}</p>
                </div>
            `;
            
            // 启用回答输入
            answerInput.disabled = false;
            submitButton.disabled = false;
            
            alert(`✅ 面试准备完成！\n匹配度: ${(result.matchResult.match_report.total_score * 100).toFixed(1)}%`);
            
        } catch (error) {
            alert(`❌ 面试准备失败: ${error.message}`);
        } finally {
            startButton.disabled = false;
            startButton.textContent = '开始面试';
        }
    });
    
    // 提交回答
    submitButton.addEventListener('click', async () => {
        const answer = answerInput.value.trim();
        if (!answer) {
            alert('请输入回答内容');
            return;
        }
        
        try {
            submitButton.disabled = true;
            submitButton.textContent = '提交中...';
            
            const result = await interviewSystem.continueInterview(answer);
            
            // 添加到历史记录
            historyDiv.innerHTML += `
                <div class="answer">
                    <h4>👤 你的回答：</h4>
                    <p>${answer}</p>
                </div>
            `;
            
            if (result.hasNextQuestion) {
                // 显示下一个问题
                const followUpText = result.isFollowUp ? '(追问)' : '';
                questionDiv.innerHTML = `
                    <div class="question">
                        <h3>🤖 面试官 ${followUpText}：</h3>
                        <p>${result.question}</p>
                    </div>
                `;
                
                historyDiv.innerHTML += `
                    <div class="question">
                        <h4>🤖 面试官 ${followUpText}：</h4>
                        <p>${result.question}</p>
                    </div>
                `;
            } else {
                // 面试结束
                questionDiv.innerHTML = `
                    <div class="summary">
                        <h3>🎉 面试完成！</h3>
                        <p>${result.summary}</p>
                    </div>
                `;
                
                answerInput.disabled = true;
                submitButton.disabled = true;
            }
            
            // 清空输入框
            answerInput.value = '';
            
        } catch (error) {
            alert(`❌ 提交失败: ${error.message}`);
        } finally {
            if (!answerInput.disabled) {
                submitButton.disabled = false;
                submitButton.textContent = '提交回答';
            }
        }
    });
    
    // 回车键提交
    answerInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitButton.click();
        }
    });
});
```

## 🚨 错误处理

### 常见错误及处理方法
```javascript
// 错误处理工具类
class ErrorHandler {
    static handle(error) {
        console.error('API错误:', error);
        
        if (error.message.includes('404')) {
            return '❌ 接口不存在，请检查API地址';
        } else if (error.message.includes('500')) {
            return '❌ 服务器内部错误，请稍后重试';
        } else if (error.message.includes('网络')) {
            return '❌ 网络连接失败，请检查网络';
        } else if (error.message.includes('文件')) {
            return '❌ 文件处理失败，请检查文件格式';
        } else {
            return `❌ 未知错误: ${error.message}`;
        }
    }
    
    static async retryRequest(requestFn, maxRetries = 3) {
        for (let i = 0; i < maxRetries; i++) {
            try {
                return await requestFn();
            } catch (error) {
                if (i === maxRetries - 1) throw error;
                
                console.warn(`请求失败，正在重试 (${i + 1}/${maxRetries})...`);
                await this.sleep(1000 * (i + 1)); // 递增延迟
            }
        }
    }
    
    static sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// 使用示例
try {
    const result = await ErrorHandler.retryRequest(() => analyzeMatch());
} catch (error) {
    const errorMessage = ErrorHandler.handle(error);
    alert(errorMessage);
}
```

## 📱 前端HTML示例

### 完整的HTML页面示例
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI智能面试系统</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
        .question { background: #f0f8ff; padding: 15px; border-radius: 8px; margin: 10px 0; }
        .answer { background: #f0fff0; padding: 15px; border-radius: 8px; margin: 10px 0; }
        .summary { background: #fff8dc; padding: 15px; border-radius: 8px; margin: 10px 0; }
        input[type="file"], textarea, button { margin: 10px 0; padding: 10px; }
        textarea { width: 100%; height: 100px; resize: vertical; }
        button { background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .loading { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI智能面试系统</h1>
        
        <div class="section">
            <h2>📄 上传简历</h2>
            <input type="file" id="resumeFile" accept=".pdf">
            <button id="startInterview">开始面试</button>
        </div>
        
        <div class="section">
            <h2>🎙️ 面试对话</h2>
            <div id="question"></div>
            <textarea id="answerInput" placeholder="请输入您的回答..." disabled></textarea>
            <button id="submitAnswer" disabled>提交回答</button>
        </div>
        
        <div class="section">
            <h2>📝 对话历史</h2>
            <div id="history"></div>
        </div>
    </div>
    
    <!-- 引入上面的JavaScript代码 -->
    <script>
        // 这里放入上面所有的JavaScript代码
    </script>
</body>
</html>
```

## 🔧 高级用法

### 自定义配置
```javascript
// 自定义API配置
const customConfig = {
    baseURL: 'https://your-domain.com/api',
    timeout: 30000,
    retryTimes: 3,
    enableLogging: true
};

// 使用自定义配置创建API客户端
class CustomAPIClient {
    constructor(config) {
        this.baseURL = config.baseURL;
        this.timeout = config.timeout;
        this.retryTimes = config.retryTimes;
        this.enableLogging = config.enableLogging;
    }
    
    log(message) {
        if (this.enableLogging) {
            console.log(`[API Client] ${message}`);
        }
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        this.log(`请求: ${options.method || 'GET'} ${url}`);
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.log(`响应成功: ${JSON.stringify(data).substring(0, 100)}...`);
            return data;
            
        } catch (error) {
            clearTimeout(timeoutId);
            this.log(`请求失败: ${error.message}`);
            throw error;
        }
    }
}
```

---

## 📞 技术支持

如果在使用过程中遇到问题：

1. **检查服务状态**: 先调用 `/health` 接口确认服务正常
2. **查看浏览器控制台**: 查看详细的错误信息
3. **检查网络连接**: 确保能够访问后端服务
4. **验证文件格式**: 确保上传的是PDF格式的简历文件

## 🚀 开始使用

1. 确保后端服务已启动 (`python main.py`)
2. 复制上面的JavaScript代码到你的项目中
3. 根据需要修改API_BASE_URL
4. 开始构建你的AI面试前端应用！