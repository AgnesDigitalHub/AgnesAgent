# AgnesAgent

一个可扩展的跨平台 AI Agent 框架，目前正在积极开发中。

## 功能特性

### Phase 1：LLM 核心 (已完成)

- **多模型支持**：OpenAI、Ollama、OpenVINO、OpenVINO Server
- **对话历史管理**：支持多轮对话，自动裁剪历史记录
- **提示词模板**：内置多种角色模板（默认助手、VTuber、编程专家、翻译）
- **流式输出**：支持实时流式响应
- **Web UI**：内置 Web 界面，可在浏览器中配置和使用
- **配置化**：YAML 配置文件，易于扩展

## 快速开始

```bash
# 安装依赖
uv sync

# 复制配置
cp config/config.yaml.example config/config.yaml

# 编辑配置文件，设置你的 API Key 或模型路径

# 列出可用的提示词模板
uv run main.py --list-templates
```

## 使用方式

### 1. Web 模式（推荐）⭐

#### 新版 WebUI (web2)
FastAPI + AMIS 构建，带可视化模型管理和流式对话：
```bash
uv run main.py --web2
```
访问 http://127.0.0.1:8000 使用

#### 旧版 Web 控制台
```bash
uv run main.py --web
```
访问 http://127.0.0.1:8000 使用

### 2. 交互式对话模式

```bash
# 智能模式：已配置则直接启动，未配置则显示菜单
uv run main.py --chat

# 强制跳过菜单（使用配置文件）
uv run main.py --chat --no-select
```

**智能判断规则：**
- 如果配置文件有自定义的 model、api_key 或 base_url → 直接启动
- 如果是默认配置 → 显示交互式菜单

## 使用示例

### 基础对话

```python
from agnes import AgnesAgent, PromptTemplates

async with AgnesAgent("config/config.yaml") as agent:
    # 设置角色
    agent.set_system_prompt(PromptTemplates.DEFAULT_ASSISTANT.template)

    # 对话
    response = await agent.chat("你好，请介绍一下你自己。")
    print(response.content)
```

### 多轮对话

```python
async with AgnesAgent("config/config.yaml") as agent:
    agent.set_system_prompt(PromptTemplates.DEFAULT_ASSISTANT.template)

    await agent.chat("我叫小明")
    response = await agent.chat("我叫什么名字？")
    print(response.content)  # 会记得"小明"
```

### 流式输出

```python
async with AgnesAgent("config/config.yaml") as agent:
    print("Agnes: ", end="", flush=True)
    async for token in agent.chat_stream("讲一个短故事"):
        print(token, end="", flush=True)
```

## 计划功能

Phase 1：LLM 核心     → ✅ 可靠的多模型对话基础
Phase 2：工具与技能   → 电脑操控、代码执行、文件/浏览器控制
Phase 3：记忆系统     → 短期上下文 + 长期知识库
Phase 4：游戏 Agent   → 结构化感知、分层规划、动作执行

## 贡献

想先讨论想法再写代码？开一个 [Discussion](https://github.com/AgnesDigitalHub/AgnesAgent/discussions)。发现 Bug 或有具体提案？开一个 [Issue](https://github.com/AgnesDigitalHub/AgnesAgent/issues)。

想了解如何在本地运行项目，请查看 [CONTRIBUTING.md](./CONTRIBUTING.md)。

> 📋 [查看项目进度 →](https://github.com/orgs/AgnesDigitalHub/projects/1)

## 鸣谢

- [ATRI](https://github.com/moeru-ai/airi/)
- [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber)

## License

MIT