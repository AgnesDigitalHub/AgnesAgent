# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0beta] - 2026-03-29

### Added

- web控制台，默认端口：8000
- 模型配置管理界面
- 模型管理界面

### 🐛 Bug Fixes (Web UI)

- 修复模型管理页面点击"新增配置"时自动请求 fetch-models API 的问题
  - 移除表单中模型选择器的自动加载逻辑
  - 模型列表现在只在用户点击"获取可用模型"按钮后才加载
- 修复新增配置流程过于复杂的问题
  - 简化新增配置表单，用户只需选择 AI 供应商即可创建
  - 自动生成唯一配置 ID（基于供应商名称，重复时添加数字后缀）
  - 其他配置项（API Key、模型等）可在创建后通过编辑功能完善

### ✨ Features (Web UI)

- 新增配置流程优化：选择供应商 → 自动创建 → 编辑完善
- 编辑配置保持完整功能，支持手动刷新模型列表

### 🔧 Improvements (Web UI)

- 优化配置管理用户体验
- 改进 AMIS 表单交互逻辑

### 📚 Documentation

- 更新 README.md，添加更新日志链接
- 优化项目文档结构

---

## [0.0.1beta] - 2026-03-25

### Added

- 建立llm基础框架,建立简单对话逻辑
- 增加LLM供应商(Ollama, OpenAI)
- 增加控制台交互功能
- 增加流式输出功能