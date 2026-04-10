<div align="center">

<img src="icon.png" alt="AgnesAgent Logo" width="120"/>

# AgnesAgent

**可扩展的 AI Agent 基础设施**

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

> **Everyone may be Agnes with Agent** — 每个人都能拥有自己的 AI Agent。

AgnesAgent 是一个开源 AI Agent 框架，支持多 LLM 提供商、工具调用、MCP 协议、长期记忆和任务规划。

> ⚠️ **注意**：当前为 `0.1.0beta` 版本，API 可能变动。欢迎提交 Issue 反馈问题。

---

## ✨ 功能特性

| 模块 | 功能 | 状态 |
|------|------|------|
| **LLM 核心** | OpenAI/Ollama/DeepSeek/Gemini 等兼容接口 | ✅ |
| **对话管理** | 多轮对话，上下文窗口管理 | ✅ |
| **人格系统** | YAML 配置化角色管理 | ✅ |
| **流式输出** | 实时响应流 | ✅ |
| **Web UI** | FastAPI + Amis 管理控制台 | ✅ |
| **技能系统** | 可扩展 Skill 框架 | ✅ |
| **MCP 协议** | 服务端/客户端完整实现 | ✅ |
| **长期记忆** | 向量存储 + 语义检索 | ✅ |
| **任务规划** | ReAct 推理 + 任务分解 | ✅ |
| **性能优化** | 缓存/索引/连接池/监控 | ✅ |
| **屏幕感知** | 屏幕捕获 + OCR | ✅ |
| **输入控制** | 键盘/鼠标自动化 | ✅ |

---

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/AgnesDigitalHub/AgnesAgent.git
cd AgnesAgent

# 基础安装（仅核心功能）
uv sync

# 完整安装（所有功能）
uv sync --extra all

# 按需安装特定功能
uv sync --extra memory    # 向量数据库和嵌入
uv sync --extra audio     # 音频处理
uv sync --extra gameautomation  # 屏幕和输入控制
```

### 配置

```bash
cp config/config.yaml.example config/config.yaml
# 编辑 config/config.yaml 设置 API Key
```

### 启动

```bash
# 启动 Web 控制台
uv run main.py --server

# 交互式对话
uv run main.py --chat
```

访问 http://127.0.0.1:8000

---

## 🗺️ 路线图

| 阶段 | 目标 | 状态 |
|------|------|------|
| Phase 1 | 核心能力：记忆、规划、MCP、屏幕感知、输入控制 | ✅ |
| Phase 2 | 体验升级：UI 深化、人格市场、浏览器自动化、多模态 | 🚧 |
| Phase 3 | 工程化：测试覆盖 40%+、CI/CD、Docker 部署 | 📋 |
| Phase 4 | v1.0 发布：文档站、生态建设 | 📋 |

---

## 🛠️ 开发

```bash
git clone https://github.com/AgnesDigitalHub/AgnesAgent
uv pip install pre-commit
pre-commit install
```

## ❤️ 贡献

欢迎 Issues / PR！查看 [CONTRIBUTING.md](./CONTRIBUTING.md)。

> 📋 [项目进度 →](https://github.com/orgs/AgnesDigitalHub/projects/1)

---

## 🙏 鸣谢

- [ATRI](https://github.com/moeru-ai/airi/)
- [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber)
- [AstrBot](https://github.com/AstrBotDevs/AstrBot)

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=AgnesDigitalHub/AgnesAgent&type=Date)](https://star-history.com/#AgnesDigitalHub/AgnesAgent&Date)

---

## 📝 更新日志

查看 [CHANGELOG.md](./CHANGELOG.md)

当前版本：**0.1.0beta** (2026-03-29)

---

## 📄 License

MIT License - 查看 [LICENSE](./LICENSE)
