# 智能面试辅助平台

一个基于FastAPI和Streamlit的智能面试辅助系统，集成了简历分析和AI模拟面试功能。

## 功能特性

- **简历上传与解析**：支持PDF和DOCX格式的简历上传与内容提取
- **AI智能分析**：利用通义千问API对简历进行专业分析，提供优化建议
- **AI模拟面试**：基于岗位生成面试问题，支持答案评估（待完善）
- **用户友好界面**：使用Streamlit构建的直观操作界面

## 技术栈

- **后端**：FastAPI
- **前端**：Streamlit
- **简历解析**：pdfplumber, python-docx
- **AI集成**：通义千问API (dashscope)
- **虚拟环境**：uv

## 快速开始

### 1. 安装依赖

```bash
# 创建并激活虚拟环境
uv venv

# 安装项目依赖
uv add fastapi uvicorn pdfplumber python-docx dashscope python-multipart streamlit requests
```

### 2. 配置API密钥

在`config.py`文件中配置通义千问API密钥：

```python
# 通义千问API密钥
DASHSCOPE_API_KEY = "your-api-key-here"

# 模型配置
MODEL_NAME = "qwen-plus"
MAX_TOKENS = 2000
```

### 3. 启动服务

#### 启动FastAPI后端

```bash
uv run python main.py 8080
```

后端API将在 `http://localhost:8080` 上运行。

#### 启动Streamlit前端

```bash
uv run streamlit run app.py --server.port 8501
```

前端界面将在 `http://localhost:8501` 上运行。

### 4. 测试API

运行测试脚本验证API功能：

```bash
uv run python test_api.py
```

## API端点

### 简历管理

- `GET /` - 健康检查
- `POST /api/v1/resume/upload` - 上传简历文件（支持PDF/DOCX）
- `POST /api/v1/resume/analyze` - 分析简历内容
- `GET /api/v1/resume/{resume_id}` - 获取简历详情

### 面试功能

- `POST /api/v1/interview/start` - 开始AI模拟面试
- `POST /api/v1/interview/answer` - 提交面试答案

## 项目结构

```
.
├── main.py              # FastAPI后端主文件
├── app.py               # Streamlit前端主文件
├── config.py            # 配置文件
├── test_api.py          # API测试脚本
├── requirements.txt     # 项目依赖
└── temp/                # 临时文件目录
```

## 注意事项

1. 确保已正确配置通义千问API密钥
2. 仅支持PDF和DOCX格式的简历文件
3. 临时文件目录`temp/`用于存储上传的简历文件
4. 当前实现使用内存存储简历数据，生产环境建议使用数据库

## 开发计划

- [ ] 完善用户认证系统
- [ ] 实现面试历史记录功能
- [ ] 优化AI分析算法
- [ ] 支持多语言界面
- [ ] 部署到生产环境

## 许可证

MIT
