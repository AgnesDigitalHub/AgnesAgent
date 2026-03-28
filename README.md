<div align="center">

<img src="icon.png" alt="AgnesAgent Logo" width="120"/>

# AgnesAgent

**高度可扩展、跨平台的 AI Agent 基础设施**

<div>
<img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="python">
<a href="https://github.com/AgnesDigitalHub/AgnesAgent/stargazers"><img src="https://img.shields.io/github/stars/AgnesDigitalHub/AgnesAgent.svg" alt="GitHub stars"></a>
<a href="https://github.com/AgnesDigitalHub/AgnesAgent/blob/main/LICENSE"><img src="https://img.shields.io/github/license/AgnesDigitalHub/AgnesAgent.svg" alt="MIT license"></a>
</div>

<br>

<a href="https://github.com/AgnesDigitalHub/AgnesAgent">主页</a> ｜
<a href="https://github.com/AgnesDigitalHub/AgnesAgent/issues">问题提交</a> ｜
<a href="https://github.com/orgs/AgnesDigitalHub/projects/1">项目进度</a>

</div>

AgnesAgent 是一个开源的 AI Agent 基础框架，专注于构建可扩展的智能体能力。目前已完成核心 LLM 对话基础设施，并正在扩展工具调用、MCP 能力和游戏自动化支持。无论是桌面助手、自动化工作流，还是游戏 Agent，AgnesAgent 都能为你提供可靠的底层支持。

## ✨ 功能特性

### 已完成 ✅

| 模块 | 功能 | 描述 |
|---------|---------|---------|
| **LLM 核心** | 多模型支持 | OpenAI、Ollama、DeepSeek、Gemini、Anthropic 等所有 OpenAI 兼容接口 |
| **对话管理** | 对话历史 | 支持多轮对话，自动维护上下文窗口 |
| **人格系统** | 角色管理 | 配置化人格管理，支持自定义角色 |
| **流式输出** | 实时响应 | 完整支持流式生成 |
| **Web UI** | 可视化管理 | 基于 FastAPI + Amis 构建现代化管理控制台 |
| **配置化** | YAML 配置 | 统一配置入口，易于部署和维护 |
| **技能系统** | 工具调用框架 | 可扩展的 Skill 框架，统一调用接口 |
| **屏幕感知** | 屏幕捕获 + OCR | 基于 mss + easyocr，支持游戏屏幕文字识别 |
| **输入控制** | 键盘 + 鼠标 | 基于 pynput，自动化控制输入设备 |
| **MCP** | Model Context Protocol | 完整实现 MCP 服务端，可以将本地技能暴露为 MCP 工具 |
| **MCP 客户端** | 外部服务集成 | 支持连接外部 MCP 服务器，在 AgnesAgent 中调用远程工具 |

### 开发中 🚧

- [ ] 长期记忆与知识库
- [ ] 分层规划与推理
- [ ] 浏览器自动化
- [ ] 代码执行沙箱
- [ ] 游戏自动化 Agent 示例

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

### 启动 Web 控制台（推荐）

```bash
# 启动新版 Web2 Amis 控制台
uv run main.py --web2
```

访问 http://127.0.0.1:8000 即可使用。

### 交互式对话

```bash
# 交互式菜单模式
uv run main.py --chat
```


## 💡 使用示例

### 基础对话

```python
from agnes import AgnesAgent

async with AgnesAgent("config/config.yaml") as agent:
    # 设置系统提示词
    agent.set_system_prompt("你是一个有用的助手。")

    # 对话
    response = await agent.chat("你好，请介绍一下你自己。")
    print(response.content)
```

### MCP 游戏自动化示例

提供了完整的 MCP 服务器示例，可以将屏幕捕获、OCR、键盘、鼠标技能暴露为 MCP 工具：

```bash
# 查看帮助
uv run python examples/mcp_game_automation.py --help

# 启动 MCP 服务（STDIO 模式）
uv run python examples/mcp_game_automation.py
```

可用工具：
- `screen_capture` - 截取屏幕截图
- `ocr_read` - 识别图片中的文字
- `keyboard_action` - 执行键盘操作
- `mouse_action` - 执行鼠标操作

## 支持的 LLM 提供商

| 提供商 | 支持情况 | 备注 |
|---------|---------|---------|
| OpenAI | ✅ | 原生支持 |
| 任意 OpenAI 兼容服务 | ✅ | OpenAI 兼容
| Ollama | ✅ | 本地部署 |
| DeepSeek | ✅ | OpenAI 兼容 |
| Google Gemini | ✅ | OpenAI 兼容 |
| Anthropic | ✅ | OpenAI 兼容 |
| OpenVINO | ✅ | 本地量化模型 |

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

## 🙏 鸣谢

本项目的诞生离不开以下开源项目的帮助：

- [ATRI](https://github.com/moeru-ai/airi/) - 自动化参考
- [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) - 本地化参考
- [AstrBot](https://github.com/AstrBotDevs/AstrBot) - web控制台参考

## ⭐ Star History

如果本项目对你有帮助，请给个 Star ⭐️，这是我们持续维护的动力！

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=AgnesDigitalHub/AgnesAgent&type=Date)](https://star-history.com/#AgnesDigitalHub/AgnesAgent&Date)

</div>

## 📄 License

MIT License - 查看 [LICENSE](./LICENSE) 了解详情。