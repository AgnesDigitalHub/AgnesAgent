<div align="center">

<img src="icon.png" alt="AgnesAgent Logo" width="120"/>

# AgnesAgent

**高度可扩展、跨平台的 AI Agent 基础设施**

<div>
<img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="python">
<img src="https://img.shields.io/badge/status-beta-orange.svg" alt="status">
<a href="https://github.com/AgnesDigitalHub/AgnesAgent/stargazers"><img src="https://img.shields.io/github/stars/AgnesDigitalHub/AgnesAgent.svg" alt="GitHub stars"></a>
<a href="https://github.com/AgnesDigitalHub/AgnesAgent/blob/main/LICENSE"><img src="https://img.shields.io/github/license/AgnesDigitalHub/AgnesAgent.svg" alt="MIT license"></a>
</div>

<br>

<a href="https://github.com/AgnesDigitalHub/AgnesAgent">主页</a> ｜
<a href="https://github.com/AgnesDigitalHub/AgnesAgent/issues">问题提交</a> ｜
<a href="https://github.com/orgs/AgnesDigitalHub/projects/1">项目进度</a>

</div>

> **Everyone may be Agnes with Agent** — AgnesAgent 致力于让每个人都能拥有自己的 AI Agent 分身。

AgnesAgent 是一个开源的 AI Agent 基础框架，专注于构建可扩展的智能体能力。目前已完成核心 LLM 对话基础设施，并正在扩展工具调用、MCP 能力和游戏自动化支持。无论是桌面助手、自动化工作流，还是游戏 Agent，AgnesAgent 都能为你提供可靠的底层支持。

> ⚠️ **注意**：当前为 `0.1.0beta` 版本，许多功能尚未经过完整测试。欢迎提交 Issue 反馈问题，或参与贡献。

---

## ✨ 功能特性

### 已实现（待完整测试）⚠️

| 模块 | 功能 | 描述 | 测试状态 |
|------|------|------|----------|
| **LLM 核心** | 多模型支持 | OpenAI、Ollama、DeepSeek、Gemini、Anthropic 等所有 OpenAI 兼容接口 | 🔶 部分测试 |
| **对话管理** | 对话历史 | 支持多轮对话，自动维护上下文窗口 | 🔶 部分测试 |
| **人格系统** | 角色管理 | 配置化人格管理，支持自定义角色 | 🔶 部分测试 |
| **流式输出** | 实时响应 | 完整支持流式生成 | 🔶 部分测试 |
| **Web UI** | 可视化管理 | 基于 FastAPI + Amis 构建现代化管理控制台 | 🔶 部分测试 |
| **配置化** | YAML 配置 | 统一配置入口，易于部署和维护 | 🔶 部分测试 |
| **技能系统** | 工具调用框架 | 可扩展的 Skill 框架，统一调用接口 | 🔶 部分测试 |
| **屏幕感知** | 屏幕捕获 + OCR | 基于 mss + easyocr，支持游戏屏幕文字识别 | 🔶 部分测试 |
| **输入控制** | 键盘 + 鼠标 | 基于 pynput，自动化控制输入设备 | 🔶 部分测试 |
| **MCP** | Model Context Protocol | 完整实现 MCP 服务端，可以将本地技能暴露为 MCP 工具 | 🔶 部分测试 |
| **MCP 客户端** | 外部服务集成 | 支持连接外部 MCP 服务器，在 AgnesAgent 中调用远程工具 | 🔶 部分测试 |

### 开发中 🚧

- [ ] 长期记忆与知识库
- [ ] 分层规划与推理（ReAct 循环）
- [ ] 浏览器自动化（Playwright 集成）
- [ ] 代码执行沙箱
- [ ] 游戏自动化 Agent 完整示例

---

## 🚀 快速开始

### 环境准备

AgnesAgent 使用 [uv](https://docs.astral.sh/uv/) 进行依赖管理，请先安装 uv。

### 从源码安装

```bash
# 克隆项目
git clone https://github.com/AgnesDigitalHub/AgnesAgent.git
cd AgnesAgent

# 安装依赖
uv sync
```

### 配置

```bash
# 复制配置文件
cp config/config.yaml.example config/config.yaml

# 编辑配置文件，设置你的 API Key 或模型路径
# 如果你需要游戏自动化功能，安装额外依赖：
uv sync --extra gameautomation
```

### 启动

```bash
# 启动框架本体
uv run main.py --web2
```

访问 http://127.0.0.1:8000 即可使用。

### 交互式对话

```bash
# 交互式菜单模式
uv run main.py --chat
```

### MCP 游戏自动化示例（开发中）

```bash
# 查看帮助
uv run python examples/mcp_game_automation.py --help

# 启动 MCP 服务（STDIO 模式）
uv run python examples/mcp_game_automation.py
```

可用工具（开发中）：

- `screen_capture` - 截取屏幕截图
- `ocr_read` - 识别图片中的文字
- `keyboard_action` - 执行键盘操作
- `mouse_action` - 执行鼠标操作

---

## 支持的 LLM 提供商

| 提供商 | 支持情况 | 备注 |
|---------|---------|---------|
| OpenAI | ✅ | 原生支持 |
| 任意 OpenAI 兼容服务 | ✅ | OpenAI 兼容 |
| Ollama | ✅ | 本地部署 |
| DeepSeek | ✅ | OpenAI 兼容 |
| Google Gemini | ✅ | OpenAI 兼容 |
| Anthropic | ✅ | OpenAI 兼容 |
| OpenVINO | ✅ | 本地量化模型 |

---

## 🗺️ 开发路线图

> 当前版本：`0.1.0beta` · 目标版本：`v1.0`
> 详细进度请见 [项目看板](https://github.com/orgs/AgnesDigitalHub/projects/1)

### Phase 1 · 智能扩展（Month 1–2）

攻克全部 🚧 开发中条目，让 Agnes 具备真正的智能体能力。

**长期记忆 & 知识库**
- [ ] 集成向量数据库（Chroma / Qdrant）
- [ ] 实现 Embedding 管道，将对话与文档写入向量库
- [ ] 记忆检索接口，按相关性召回上下文
- [ ] 支持手动添加知识文档（PDF / Markdown / 网页）

**分层规划 & 推理**
- [ ] 实现 ReAct 循环（Reason → Act → Observe）
- [ ] 支持任务拆解：将复杂目标分解为子任务树
- [ ] 规划结果可视化（在 Web UI 展示思维链）

**浏览器自动化**
- [ ] 集成 Playwright，封装为 Skill
- [ ] 支持：打开页面、点击、填表、截图、读取 DOM
- [ ] 将浏览器工具暴露为 MCP 工具

**代码执行沙箱**
- [ ] 基于 Docker 实现隔离代码运行环境
- [ ] 支持 Python / JS / Shell，捕获输出和错误
- [ ] 超时限制 & 资源配额（内存 / CPU）

**游戏 Agent 完整示例**
- [ ] 补齐 `mcp_game_automation.py` 全部工具
- [ ] 选定游戏做端到端 Demo
- [ ] 录制演示 GIF，更新 README

🎯 **阶段里程碑**：Agnes 可以记忆、规划、操控浏览器、运行代码，游戏 Agent 示例可演示。

---

### Phase 2 · 体验升级（Month 2–4）

深化 Web UI，让非开发者也能直接上手。

**Web UI 深化**
- [ ] 记忆 & 知识库管理页（增删查文档）
- [ ] 任务规划可视化面板（思维链 / 子任务树）
- [ ] 工具调用日志实时展示
- [ ] 暗色主题 & 移动端适配

**人格系统增强**
- [ ] 人格模板市场（内置多套预设角色）
- [ ] Web UI 可视化编辑人格（无需手写 YAML）
- [ ] 人格导入 / 导出（分享 `.agnes` 人格文件）

**交互体验**
- [ ] 对话中展示 Agent 实时思考状态（工具调用进度）
- [ ] 支持图片 / 文件上传（多模态输入）
- [ ] 快捷指令面板（常用动作一键触发）

🎯 **阶段里程碑**：UI 完整呈现 Agent 能力，非开发者可直接上手使用。

---

### Phase 3 · 工程化（Month 3–5）

补齐测试体系与 CI/CD，为正式发布做准备。

**测试体系**
- [ ] 技能单元测试（每个 Skill 至少 3 个用例）
- [ ] LLM 对话集成测试（mock 模型输出）
- [ ] MCP 工具调用端到端测试
- [ ] Eval 脚本：评估记忆召回质量 & 规划准确率

**CI/CD 流水线**
- [ ] GitHub Actions：PR 自动 ruff lint + pytest
- [ ] 自动发布 Release（tag 触发 + CHANGELOG 生成）
- [ ] 依赖安全扫描（pip-audit / Dependabot）

**部署 & 可观测性**
- [ ] Docker Compose 一键启动（含向量库服务）
- [ ] 云平台部署指南（Railway / Fly.io / 自托管）
- [ ] 结构化日志：Token 消耗 / 工具延迟 / 错误率

🎯 **阶段里程碑**：测试覆盖率 ≥ 70%，Docker 一键部署，CI 全绿。

---

### Phase 4 · 生态 & v1.0（Month 4–6）

完善文档，建设社区，正式发布。

**文档建设**
- [ ] 搭建文档站（VitePress）并部署到 GitHub Pages
- [ ] 架构概览图（组件关系、数据流向）
- [ ] 技能开发指南（手把手写自定义 Skill）
- [ ] MCP 插件接入教程

**社区 & 生态**
- [ ] Issue 模板（Bug / Feature / Skill 贡献）
- [ ] good-first-issue 清单（降低贡献门槛）
- [ ] Skill 插件注册表（社区贡献的技能目录）

**v1.0 正式发布**
- [ ] 发布博客：回顾 0→1 历程 & 路线图展望
- [ ] Demo 视频（展示记忆、规划、游戏 Agent）
- [ ] 提交到 Awesome-LLM-Agents 等列表

🎯 **阶段里程碑**：v1.0 正式发布，文档站上线，首批社区插件合并。

---

## 🛠️ 开发

AgnesAgent 使用 `ruff` 进行代码格式化和检查。

```bash
git clone https://github.com/AgnesDigitalHub/AgnesAgent
uv pip install pre-commit
pre-commit install
```

## ❤️ 贡献

欢迎任何 Issues / Pull Requests！对于新功能的添加，请先通过 Issue 讨论。

想了解如何贡献，请查看 [CONTRIBUTING.md](./CONTRIBUTING.md)。

> 📋 [查看项目进度 →](https://github.com/orgs/AgnesDigitalHub/projects/1)

---

## 🙏 鸣谢

本项目的诞生离不开以下开源项目的帮助：

- [ATRI](https://github.com/moeru-ai/airi/) - 自动化参考
- [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) - 本地化参考
- [AstrBot](https://github.com/AstrBotDevs/AstrBot) - web 控制台参考

---

## ⭐ Star History

如果本项目对你有帮助，请给个 Star ⭐️，这是我们持续维护的动力！

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=AgnesDigitalHub/AgnesAgent&type=Date)](https://star-history.com/#AgnesDigitalHub/AgnesAgent&Date)

</div>

---

## 📝 更新日志

完整的版本历史和更新记录请查看 [CHANGELOG.md](./CHANGELOG.md)。

当前版本：**0.1.0beta** (2026-03-29)

---

## 📄 License

MIT License - 查看 [LICENSE](./LICENSE) 了解详情。
