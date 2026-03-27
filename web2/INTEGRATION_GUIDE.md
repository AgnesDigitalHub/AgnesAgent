# Web2 界面集成指南

## 概述

已成功为 AgnesAgent 项目创建了基于 NiceGUI 的新 web2 界面，风格参考 AstrBot 项目的简洁现代设计。

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

### 方式 1：通过主服务器访问（推荐）

1. 启动 AgnesAgent 服务器：
   ```bash
   uv run main.py --server
   ```

2. 在浏览器中访问：
   - 旧界面 (amis): http://127.0.0.1:8000/
   - 新界面 (NiceGUI): http://127.0.0.1:8000/web2

### 方式 2：独立运行 web2

```bash
cd web2
uv run app.py
```

然后访问 http://127.0.0.1:8080

## 项目结构

```
web2/
├── __init__.py          # 模块初始化
├── app.py               # 主应用入口
├── INTEGRATION_GUIDE.md # 本指南
├── static/              # 静态资源目录（待创建）
└── pages/               # 页面模块
    ├── __init__.py
    ├── dashboard.py
    ├── models.py
    ├── chat.py
    ├── agents.py
    ├── prompts.py
    ├── tools.py
    ├── knowledge.py
    ├── workflows.py
    ├── logs.py
    ├── publish.py
    ├── users.py
    └── settings.py
```

## API 集成

web2 界面与 AgnesAgent 的 API 完全集成：

- 所有配置通过 `/api/profiles` 端点管理
- 聊天功能通过 WebSocket `/ws/chat` 实现
- OpenAI 兼容 API 在 `/v1/` 下提供

## 已修复的问题

1. **导入问题** - 修复了相对导入错误，支持从不同目录运行
2. **API 错误** - 修复了 `is_active` 字段验证错误，确保返回 boolean 类型
3. **NiceGUI 组件兼容性** - 修复了 `ui.card_text` 和 `ui.card_actions` 不存在的问题

## 新功能

1. **侧边栏切换按钮** - 在左上角添加了菜单按钮，可展开/收起侧边栏
2. **响应式布局** - 根据侧边栏状态自动调整内容区域的边距

## 设计风格

- 使用 NiceGUI 组件库
- 采用现代化的 Material Design 风格
- 左侧导航栏 + 顶部标题栏布局
- 卡片式设计展示内容
- 响应式布局，支持移动端

## 下一步

1. 完善各个页面的功能实现
2. 添加实时数据更新
3. 完善表单验证
4. 添加更多交互功能
5. 优化用户体验

## 技术栈

- **后端**: Python + FastAPI + NiceGUI
- **前端**: NiceGUI (基于 Vue 3 + Quasar)
- **API**: RESTful + WebSocket