# data 目录说明

此目录用于存储**用户自定义数据**，这些数据不应该被提交到 Git 版本控制。

## 目录结构

```
data/
├── README.md          # 此说明文件
├── skills/            # 用户自定义技能 (YAML 格式)
├── personas/          # 用户自定义人格/Agent 配置
├── llm_profiles/      # 用户自定义 LLM 模型配置
├── mcp/              # MCP 运行时数据
│   └── servers.json  # MCP 服务器配置
└── stats/            # 使用统计数据
```

## 加载顺序

技能加载顺序：
1. 系统内置技能 (`config/skills/`)
2. 用户自定义技能 (`data/skills/`)

如果存在同名技能，用户自定义技能会覆盖系统技能。

## Git 忽略

整个 `data/` 目录已经在 `.gitignore` 中被忽略，你的本地数据不会被提交。