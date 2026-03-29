# 贡献指南

欢迎参与 AgnesAgent 项目！

## 开发环境

使用 uv 安装开发依赖：

```bash
uv sync --dev
```

## 代码风格

项目使用 ruff 进行代码检查和格式化：

```bash
# 格式化代码
uv run ruff format

# 检查代码
uv run ruff check --fix
```

## 提交前检查(未完成)

确保运行：

```bash
uv run python -m basedpyright
uv run pytest
```

## 提交 PR

1. Fork 项目
2. 创建分支
3. 提交更改
4. 推送到分支
5. 创建 PR
