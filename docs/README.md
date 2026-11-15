# 智能面试辅助平台

一个基于 FastAPI 的智能面试辅助系统，集成了简历分析和 AI 模拟面试功能。

## 功能特性

- **简历上传与解析**：支持PDF和DOCX格式的简历上传与内容提取
- **AI智能分析**：利用通义千问API对简历进行专业分析，提供优化建议
- **AI模拟面试**：基于岗位生成面试问题（答案评估待实现）
- **用户友好界面**：原生 HTML + Tailwind CSS 单页应用，含雷达图与流式分析进度

## 技术栈

- **后端**：FastAPI
- **前端**：原生 HTML/JS + Tailwind CSS（Chart.js 雷达图）
- **简历解析**：pdfplumber, python-docx
- **AI集成**：SiliconFlow API (提供通义千问模型)
- **部署**：Docker Compose（后端、前端、PostgreSQL、Redis）
- **虚拟环境**：uv

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
uv venv

# 按锁文件安装依赖（推荐）
uv sync
```

### 2. 配置API密钥

复制模板并填入真实密钥（`.env` 已被 `.gitignore` 忽略）：

```bash
cp .env.example .env
```

```bash
# .env
SILICONFLOW_API_KEY=your-api-key-here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
MODEL_NAME=Qwen/Qwen3.5-4B
MAX_TOKENS=4096
temperature=0.7
DATABASE_URL=postgresql://achuser:achpassword@localhost:5432/achdb
```

后端启动时会自动读取项目根目录的 `.env`；容器环境由 `docker-compose.yml` 的 `env_file` 注入，已存在的环境变量优先（容器内 `DATABASE_URL` 指向 `postgres:5432`）。

### 3. 启动服务

#### 方式一：Docker Compose（推荐）

```bash
docker compose up --build -d
```

- 后端 API：`http://localhost:8080`
- 前端页面：`http://localhost:8501`
- PostgreSQL：`5432`，Redis：`6379`

> 修改 `frontend/index.html` 后需重新构建前端容器：`docker compose up -d --build frontend`。

#### 方式二：本地开发

```bash
# 启动FastAPI后端
uv run python backend/app/main.py 8080

# 启动前端静态服务
cd frontend && python -m http.server 8501
```

后端API将在 `http://localhost:8080` 上运行，前端页面在 `http://localhost:8501`。

> `frontend/app/app.py` 是早期 Streamlit 版本，当前未部署，仅作历史保留。

### 4. 测试API

先确保后端已在 8080 端口运行，再执行：

```bash
uv run python tests/backend/test_api.py
uv run python tests/backend/test_resume_upload.py
uv run python tests/backend/test_ai_analysis.py
```

## API端点

### 简历管理

- `GET /` - 健康检查
- `POST /api/v1/resume/upload` - 上传简历文件（支持PDF/DOCX）
- `GET /api/v1/resume/analyze?resume_id=...` - 分析简历内容（SSE 流式返回处理进度与分析结果）
- `GET /api/v1/resume/{resume_id}` - 获取简历状态

### 面试功能

- `POST /api/v1/interview/start` - 开始AI模拟面试
- `POST /api/v1/interview/answer` - 提交面试答案并由AI评分（返回分数、评语与改进建议，结果落库）
- `GET /api/v1/interview/{interview_id}` - 获取面试详情与所有已提交答案的评估结果

## 项目结构

```
.
├── backend/            # 后端代码目录
│   ├── app/            # FastAPI应用主目录
│   │   ├── __init__.py
│   │   ├── main.py     # 后端API主文件（含SSE流式分析）
│   │   ├── db.py       # PostgreSQL 连接池与建表
│   │   └── repository.py # 数据访问层（简历/分析/面试）
│   ├── config/         # 后端配置目录
│   │   ├── __init__.py
│   │   └── config.py   # 读取 .env / 环境变量
│   └── __init__.py
├── frontend/           # 前端代码目录
│   ├── index.html      # 单页应用（当前部署版本）
│   └── app/app.py      # Streamlit 历史版本（未部署）
├── docs/               # 文档目录
│   ├── README.md       # 项目说明文档
│   ├── dev-progress.md # 开发进度报告
│   └── note.md         # 项目需求分析与技术架构文档
├── tests/              # 测试代码目录
│   ├── backend/        # 后端测试
│   │   ├── test_ai_analysis.py
│   │   ├── test_api.py
│   │   └── test_resume_upload.py
│   └── frontend/       # 前端测试目录（预留）
├── uploads/            # 上传文件存储目录
├── temp/               # 临时文件目录
├── .env.example        # 环境变量模板（复制为 .env）
├── .gitignore          # Git忽略文件配置
├── .dockerignore
├── docker-compose.yml  # 后端/前端/PostgreSQL/Redis 编排
├── Dockerfile.backend
├── Dockerfile.frontend
├── .python-version     # Python版本配置
├── pyproject.toml      # 项目依赖配置
├── test_resume.docx    # 测试用简历文件
├── test_resume.pdf     # 测试用简历文件
├── test_resume.txt     # 测试用简历文件
└── uv.lock             # 依赖锁文件
```

## 注意事项

1. 在项目根目录 `.env` 中配置 SiliconFlow API 密钥（参考 `.env.example`），密钥不会进入版本控制
2. 仅支持PDF和DOCX格式的简历文件
3. 上传的简历文件实际保存在 `temp/` 目录中
4. 简历、分析结果与面试会话存储在 PostgreSQL（`resumes`、`resume_analyses`、`interviews`、`interview_answers` 四张表），表结构在后端启动时自动创建
5. `uploads/`、`temp/` 和 `.env` 已加入 `.gitignore`
6. 前端 API 地址默认按当前主机名推导（`8501` → `8080`），跨机部署时需调整 `frontend/index.html` 中的 `API_URL`

## 开发计划

- [x] 接入 PostgreSQL，实现简历/分析/面试数据持久化
- [ ] 接入 Redis（缓存或限流）
- [ ] 完善用户认证系统
- [ ] 实现面试答案评估与历史记录
- [ ] 支持多语言界面
- [ ] 部署到生产环境

## 许可证

MIT
