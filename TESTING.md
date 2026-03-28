# AgnesAgent 测试指南

本文档介绍如何为AgnesAgent项目编写和运行自动化测试。

## 概述

AgnesAgent项目使用pytest作为测试框架，支持单元测试、集成测试和性能测试。测试代码组织在`tests/`目录下，按功能模块划分为多个子目录。

## 测试目录结构

```
tests/
├── __init__.py
├── conftest.py              # 公共fixtures和配置
├── test_llm.py             # 现有LLM测试
├── test_config.py          # 现有配置测试
├── test_dashboard.py       # 现有仪表板测试
├── test_server.py          # 现有服务器测试
├── test_web2_build.py      # 现有Web2构建测试
├── core/                   # 核心模块测试
│   ├── test_chat_history.py
│   ├── test_prompt_templates.py
│   ├── test_streamer.py
│   └── test_llm_provider.py
├── skills/                 # 技能系统测试
│   ├── test_skill_engine.py
│   ├── test_yaml_loader.py
│   └── test_skill_registry.py
├── mcp/                    # MCP模块测试
│   ├── test_mcp_server.py
│   ├── test_mcp_client.py
│   └── test_mcp_registry.py
├── web2/                   # Web2控制台测试
│   ├── test_app_config.py
│   ├── test_pages.py
│   └── test_schemas.py
├── utils/                  # 工具函数测试
│   ├── test_config_loader.py
│   └── test_logger.py
└── integration/            # 集成测试
    ├── test_agent_integration.py
    └── test_web_integration.py
```

## 测试依赖

项目在`pyproject.toml`中配置了开发依赖（包含测试依赖）：

```toml
[dependency-groups]
dev = [
    "basedpyright>=1.38.3",
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
    "pytest-benchmark>=4.0.0",
    "httpx>=0.27.0",
    "respx>=0.20.0",
]
```

安装开发依赖：
```bash
uv sync --dev
```

## 运行测试

### 使用测试脚本（推荐）

项目提供了`run_tests.sh`脚本，支持多种测试运行方式：

```bash
# 运行所有测试
./run_tests.sh -a

# 运行所有测试并生成覆盖率报告
./run_tests.sh -a -c

# 只运行单元测试
./run_tests.sh -u

# 只运行集成测试
./run_tests.sh -i

# 包含慢速测试
./run_tests.sh -a -s

# 运行指定模块测试
./run_tests.sh -m core        # 核心模块
./run_tests.sh -m skills      # 技能模块
./run_tests.sh -m mcp         # MCP模块
./run_tests.sh -m web2        # Web2模块

# 运行指定测试文件
./run_tests.sh -f tests/test_llm.py

# 运行包含关键词的测试
./run_tests.sh -k 'test_chat'

# 生成HTML测试报告
./run_tests.sh -a -r

# 详细输出
./run_tests.sh -a -v

# 清理测试缓存
./run_tests.sh --clean
```

### 直接使用uv run pytest

也可以直接使用uv run pytest命令：

```bash
# 运行所有测试
uv run pytest

# 运行指定目录测试
uv run pytest tests/core/

# 运行指定文件
uv run pytest tests/test_llm.py

# 运行指定测试类
uv run pytest tests/core/test_chat_history.py::TestChatHistoryBasic

# 运行指定测试方法
uv run pytest tests/core/test_chat_history.py::TestChatHistoryBasic::test_init_empty

# 生成覆盖率报告
uv run pytest --cov=agnes --cov=web2 --cov-report=html

# 生成JUnit XML报告
uv run pytest --junitxml=test-results.xml

# 并行运行测试
uv run pytest -n auto
```

## 测试标记

项目使用pytest标记来分类测试：

```python
# 慢速测试
@pytest.mark.slow
def test_large_history():
    pass

# 集成测试
@pytest.mark.integration
def test_agent_integration():
    pass

# 异步测试
@pytest.mark.asyncio
async def test_async_tool():
    pass
```

运行特定标记的测试：
```bash
# 只运行慢速测试
uv run pytest -m slow

# 只运行集成测试
uv run pytest -m integration

# 不运行慢速测试
uv run pytest -m "not slow"
```

## 编写测试

### 基本测试结构

```python
import pytest
from agnes.core.chat_history import ChatHistory

class TestChatHistoryBasic:
    """ChatHistory 基础功能测试"""

    def test_init_empty(self):
        """测试初始化空对话历史"""
        history = ChatHistory()
        assert len(history) == 0
        assert history.max_messages == 20  # 默认值

    def test_add_user_message(self):
        """测试添加用户消息"""
        history = ChatHistory()
        history.add_user_message("你好")
        assert len(history) == 1
        assert history[0].role == "user"
        assert history[0].content == "你好"
```

### 异步测试

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_tool():
    """测试异步工具"""
    server = MCPServer()
    
    async def async_add(x: int, y: int) -> int:
        await asyncio.sleep(0.01)
        return x + y
    
    server.register_tool("async_add", async_add)
    result = await server.call_tool("async_add", {"x": 10, "y": 20})
    assert result == 30
```

### 使用fixtures

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_llm_provider():
    """模拟LLM Provider"""
    provider = AsyncMock()
    provider.chat = AsyncMock(return_value=MagicMock(content="测试响应"))
    return provider

@pytest.fixture
def mock_agent(mock_llm_provider):
    """模拟AgnesAgent实例"""
    agent = MagicMock()
    agent.llm_provider = mock_llm_provider
    agent.chat = AsyncMock(return_value=MagicMock(content="测试响应"))
    return agent

def test_agent_chat(mock_agent):
    """测试Agent对话"""
    response = mock_agent.chat("你好")
    assert response.content == "测试响应"
```

### 测试异常

```python
import pytest

def test_missing_required_parameter():
    """测试缺少必需参数"""
    engine = SkillEngine()
    
    yaml_content = """
name: required_test
description: 必需参数测试
parameters:
  required_param:
    type: string
required:
  - required_param
execution: |
  result = params['required_param']
"""
    # 测试应该抛出KeyError
    with pytest.raises(KeyError):
        engine.execute_skill("required_test", {})
```

### 性能测试

```python
import pytest
import time

@pytest.mark.slow
def test_large_history():
    """测试大量消息处理"""
    history = ChatHistory(max_messages=1000)
    
    start_time = time.time()
    
    # 添加1000条消息
    for i in range(1000):
        history.add_user_message(f"消息{i}")
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    # 验证性能
    assert elapsed < 1.0  # 应该在1秒内完成
    assert len(history) == 1000
```

## 测试覆盖率

### 生成覆盖率报告

```bash
# 生成HTML覆盖率报告
uv run pytest --cov=agnes --cov=web2 --cov-report=html

# 生成XML覆盖率报告
uv run pytest --cov=agnes --cov=web2 --cov-report=xml

# 终端显示覆盖率
uv run pytest --cov=agnes --cov=web2 --cov-report=term-missing
```

### 覆盖率目标

- **核心模块**: 80%以上
- **工具函数**: 90%以上
- **API端点**: 70%以上
- **整体覆盖率**: 75%以上

## 持续集成

### GitHub Actions配置

```yaml
name: Python Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install uv
        uv sync
    - name: Run tests
      run: |
        ./run_tests.sh -a -c
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 测试最佳实践

### 1. 测试命名

- 测试文件：`test_<module_name>.py`
- 测试类：`Test<FeatureName>`
- 测试方法：`test_<specific_behavior>`

### 2. 测试隔离

- 每个测试应该独立运行
- 使用fixtures设置测试环境
- 测试后清理资源

### 3. 测试数据

- 使用临时文件进行文件操作测试
- 使用mock避免外部依赖
- 准备边界情况测试数据

### 4. 断言

- 使用明确的断言消息
- 测试预期异常
- 验证副作用

### 5. 文档

- 为复杂测试添加注释
- 说明测试目的和方法
- 记录特殊测试情况

## 调试测试

### 运行单个测试

```bash
# 运行单个测试文件
uv run pytest tests/test_llm.py -v

# 运行单个测试类
uv run pytest tests/test_llm.py::TestChatHistory -v

# 运行单个测试方法
uv run pytest tests/test_llm.py::TestChatHistory::test_init_empty -v
```

### 调试输出

```bash
# 显示打印输出
uv run pytest -s

# 显示详细输出
uv run pytest -v

# 显示本地变量
uv run pytest -l

# 在第一次失败时停止
uv run pytest -x

# 显示最慢的10个测试
uv run pytest --durations=10
```

### 使用pdb调试

```python
def test_debug_example():
    """调试示例"""
    history = ChatHistory()
    history.add_user_message("测试")
    
    # 设置断点
    import pdb; pdb.set_trace()
    
    assert len(history) == 1
```

## 常见问题

### 1. 导入错误

确保项目根目录在Python路径中：
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 2. 异步测试失败

确保使用`pytest-asyncio`：
```bash
pip install pytest-asyncio
```

### 3. Mock不工作

检查mock路径是否正确：
```python
# 正确的mock路径
with patch('agnes.skills.engine.SkillEngine.execute_skill') as mock:
    pass
```

### 4. 覆盖率不准确

检查是否排除了不需要的文件：
```python
# pytest.ini 或 pyproject.toml
[tool.coverage.run]
omit = [
    "tests/*",
    "*/test_*",
    "*/__pycache__/*",
]
```

## 测试报告

### HTML报告

测试脚本支持生成HTML测试报告：
```bash
./run_tests.sh -a -r
```

报告文件：`test-report.html`

### JUnit XML报告

用于CI/CD集成：
```bash
uv run pytest --junitxml=test-results.xml
```

### 覆盖率报告

- HTML报告：`htmlcov/index.html`
- XML报告：`coverage.xml`
- 终端报告：直接显示在终端

## 总结

AgnesAgent项目的测试框架提供了完整的测试解决方案，包括：

1. **模块化测试组织**：按功能模块组织测试代码
2. **丰富的测试类型**：单元测试、集成测试、性能测试
3. **灵活的测试运行**：支持多种测试运行方式
4. **完善的测试工具**：fixtures、mock、断言等
5. **详细的测试报告**：覆盖率、性能、结果分析

通过遵循本文档的指导，开发者可以有效地编写和维护高质量的测试代码，确保AgnesAgent项目的稳定性和可靠性。