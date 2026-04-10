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

## 提交前检查

pre-commit 已配置，提交时会自动运行：

- ruff 格式化和检查
- 文件末尾换行符修复
- 尾随空格清理

如需手动运行检查：

```bash
# 运行测试（推荐覆盖率目标 40%+）
uv run pytest

# 可选：类型检查（不强制）
uv run python -m basedpyright
```

## 提交 PR

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m "feat: add feature"`)
4. 推送到分支 (`git push origin feature/your-feature`)
5. 创建 Pull Request
