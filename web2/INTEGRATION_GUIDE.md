# Web 界面集成指南

## 概述

AgnesAgent 使用基于 AMIS 的 Web 界面作为唯一的可视化控制台，风格参考 AstrBot 项目的简洁现代设计。

## 功能模块

web2 包含以下页面模块：

- **Dashboard** - 系统概览和统计数据
- **模型管理** - LLM 模型配置和管理
- **对话** - 与 AI 对话的聊天界面
- **Agent 管理** - Agent 配置管理
- **Prompt IDE** - Prompt 编写和测试
- **工具/插件** - 工具和插件管理
- **知识库/RAG** - 知识库管理
- **Workflow 编排** - 工作流编排
- **运行日志** - 系统运行日志
- **API/集成发布** - API 发布配置
- **用户权限** - 用户和权限管理
- **系统设置** - 系统配置

## 使用方法

### 启动 Web 控制台

```bash
uv run main.py --server
```

然后在浏览器中访问：http://127.0.0.1:8000

### 独立运行（开发调试用）

```bash
cd web2
uv run app.py
```

然后访问 http://127.0.0.1:8080

## 项目结构

```
web2/                      # Web 控制台（唯一界面）
├── __init__.py            # 模块初始化
├── app.py                 # FastAPI + AMIS 主应用
├── app_config.py          # AMIS 应用配置
├── INTEGRATION_GUIDE.md   # 本指南
├── config/                # 配置文件
│   └── app.yaml           # AMIS 应用配置
├── schemas/               # AMIS Schema 定义
│   ├── agents.py
│   ├── chat.py
│   ├── dashboard.py
│   ├── models.py
│   └── ...
├── pages/                 # 页面模块（遗留，待清理）
└── static/                # 静态资源
```

> **注意**: `web2/pages/` 目录包含遗留的 NiceGUI 代码，当前使用 `web2/schemas/` 下的 AMIS Schema 配置。

## API 集成

web2 界面与 AgnesAgent 的 API 完全集成：

- 所有配置通过 `/api/profiles` 端点管理
- 聊天功能通过 WebSocket `/ws/chat` 实现
- OpenAI 兼容 API 在 `/v1/` 下提供

## 设计风格

- 使用 AMIS (百度开源前端低代码框架)
- 采用现代化的 Material Design 风格
- 左侧导航栏 + 顶部标题栏布局
- 卡片式设计展示内容
- 响应式布局，支持移动端

## 技术栈

- **后端**: Python + FastAPI
- **前端**: AMIS (百度开源前端低代码框架，基于 React)
- **API**: RESTful + WebSocket
