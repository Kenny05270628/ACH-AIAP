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
- **AI集成**：SiliconFlow API (提供通义千问模型)
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

在`backend/config/config.py`文件中配置API密钥：

```python
# 硅基流动API配置
SILICONFLOW_API_KEY = "your-api-key-here"
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"

# 大模型参数配置
# 使用硅基流动上的通义千问模型 (聊天生成模型)
MODEL_NAME = "Qwen/Qwen2-7B-Instruct"
MAX_TOKENS = 2048
temperature = 0.7
```

### 3. 启动服务

#### 启动FastAPI后端

```bash
# 从项目根目录启动
uv run python backend/app/main.py 8080
```

后端API将在 `http://localhost:8080` 上运行。

#### 启动Streamlit前端

```bash
# 从项目根目录启动
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false STREAMLIT_SERVER_HEADLESS=true uv run streamlit run frontend/app/app.py --server.port 8501 --server.address 0.0.0.0
```

前端界面将在 `http://localhost:8501` 上运行。

### 4. 测试API

运行测试脚本验证API功能：

```bash
# 运行后端测试
uv run python tests/backend/test_api.py
uv run python tests/backend/test_ai_analysis.py
uv run python tests/backend/test_resume_upload.py
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
├── backend/            # 后端代码目录
│   ├── app/            # FastAPI应用主目录
│   │   ├── __init__.py
│   │   └── main.py     # 后端API主文件
│   ├── config/         # 后端配置目录
│   │   ├── __init__.py
│   │   └── config.py   # 配置文件
│   └── __init__.py
├── frontend/           # 前端代码目录
│   └── app/            # Streamlit应用目录
│       └── app.py      # 前端应用主文件
├── docs/               # 文档目录
│   ├── README.md       # 项目说明文档
│   └── note.md         # 项目需求分析与技术架构文档
├── tests/              # 测试代码目录
│   ├── backend/        # 后端测试
│   │   ├── test_ai_analysis.py
│   │   ├── test_api.py
│   │   └── test_resume_upload.py
│   └── frontend/       # 前端测试目录（预留）
├── uploads/            # 上传文件存储目录
├── temp/               # 临时文件目录
├── .gitignore          # Git忽略文件配置
├── .python-version     # Python版本配置
├── pyproject.toml      # 项目依赖配置
├── test_resume.docx    # 测试用简历文件
├── test_resume.pdf     # 测试用简历文件
├── test_resume.txt     # 测试用简历文件
└── uv.lock             # 依赖锁文件
```

## 注意事项

1. 确保已在`backend/config/config.py`中正确配置SiliconFlow API密钥
2. 仅支持PDF和DOCX格式的简历文件
3. 上传的简历文件存储在`uploads/`目录中
4. 临时处理的文件存储在`temp/`目录中
5. 当前实现使用内存存储简历数据，生产环境建议使用数据库
6. 已将`uploads/`和`temp/`目录添加到`.gitignore`中，避免将用户文件提交到版本控制

## 开发计划

- [ ] 完善用户认证系统
- [ ] 实现面试历史记录功能
- [ ] 优化AI分析算法
- [ ] 支持多语言界面
- [ ] 部署到生产环境

## 许可证

MIT
