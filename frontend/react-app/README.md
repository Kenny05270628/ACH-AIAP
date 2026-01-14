# 智能面试辅助平台 (React + Tailwind CSS)

这是一个基于React + Tailwind CSS的智能面试辅助平台前端应用，提供简历上传、AI分析和面试问题生成功能。

## 项目结构

```
.
├── src/
│   ├── components/           # 组件目录
│   │   ├── Button.jsx        # 按钮组件
│   │   └── HomePage.jsx      # 首页组件
│   ├── lib/                  # 工具函数
│   │   └── utils.js          # 工具函数
│   ├── services/             # API服务
│   │   └── api.js            # 后端API调用
│   ├── App.jsx               # 应用入口组件
│   ├── index.css             # 全局样式
│   └── main.jsx              # 应用主入口
├── dist/                     # 构建输出目录
├── package.json              # 项目配置
├── vite.config.js            # Vite配置
├── tailwind.config.js        # Tailwind CSS配置
├── postcss.config.js         # PostCSS配置
└── jsconfig.json             # JavaScript配置
```

## 功能特性

1. **简历上传**：支持PDF和DOCX格式的简历文件上传
2. **AI简历分析**：利用AI技术对简历内容进行深度分析和多维度评分
3. **面试问题生成**：基于岗位名称和简历内容，生成针对性的面试问题

## 技术栈

- **React 18**：前端框架
- **Vite**：构建工具
- **Tailwind CSS**：样式框架
- **JavaScript**：开发语言

## 安装和运行

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

应用将在 http://localhost:5173 启动

### 3. 构建生产版本

```bash
npm run build
```

构建输出将放在 `dist` 目录

### 4. 预览生产版本

```bash
npm run preview
```

## API配置

后端API地址配置在 `src/services/api.js` 文件中，默认使用 `http://localhost:8080`。如需修改，请编辑该文件：

```javascript
const API_BASE_URL = 'http://localhost:8080';  // 修改为实际的后端API地址
```

## 与原有Streamlit应用的关系

本项目是现有的Streamlit前端应用的替代方案，提供了更现代化、更美观的用户界面。两者可以同时存在，互不影响：

- Streamlit应用：`frontend/app/app.py`
- React应用：`frontend/react-app/`

## 注意事项

1. 确保后端服务已经启动并正常运行
2. 首次使用时，需要在后端配置有效的API密钥
3. 支持的简历格式：PDF、DOCX
4. 生成面试问题时，建议提供详细的岗位名称，以获得更精准的问题