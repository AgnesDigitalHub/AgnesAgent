# AgnesAgent

一个可扩展的跨平台 AI Agent 框架,目前还在开发中，尚未完成。

## 快速开始

```bash
# 安装
uv sync

# 复制配置
cp config/config.yaml.example config.yaml

# 运行
uv run main.py
```

## 功能

- [ ]Provider 模式，易于扩展
- [ ]支持 Ollama、OpenAI、OpenVINO 等 LLM
- [ ]支持 Whisper ASR
- [ ]音频录制 + VAD
- [ ]流式输出
- [ ]代理支持

## 鸣谢

- [ATRI](https://github.com/moeru-ai/airi/)实现LLM逻辑的参考

## License

MIT
