"""LLM 功能测试"""

import pytest

from agnes.core import ChatHistory, PromptTemplates


class TestChatHistory:
    """测试对话历史管理"""

    def test_init_empty(self):
        """测试初始化空对话历史"""
        history = ChatHistory()
        assert len(history) == 0

    def test_init_with_system_prompt(self):
        """测试带系统提示词初始化"""
        history = ChatHistory(system_prompt="你是一个助手")
        assert len(history) == 1
        assert history[0].role == "system"
        assert history[0].content == "你是一个助手"

    def test_add_user_message(self):
        """测试添加用户消息"""
        history = ChatHistory()
        history.add_user_message("你好")
        assert len(history) == 1
        assert history[0].role == "user"
        assert history[0].content == "你好"

    def test_add_assistant_message(self):
        """测试添加助手消息"""
        history = ChatHistory()
        history.add_assistant_message("你好！")
        assert len(history) == 1
        assert history[0].role == "assistant"
        assert history[0].content == "你好！"

    def test_to_openai_format(self):
        """测试转换为 OpenAI 格式"""
        history = ChatHistory()
        history.add_user_message("你好")
        history.add_assistant_message("你好！")

        messages = history.to_openai_format()
        assert len(messages) == 2
        assert messages[0] == {"role": "user", "content": "你好"}
        assert messages[1] == {"role": "assistant", "content": "你好！"}

    def test_trim_history(self):
        """测试裁剪历史记录"""
        history = ChatHistory(max_messages=3)
        for i in range(5):
            history.add_user_message(f"消息 {i}")

        # 应该只保留最后 3 条
        assert len(history) == 3
        assert history[0].content == "消息 2"

    def test_clear_history(self):
        """测试清空历史"""
        history = ChatHistory(system_prompt="系统提示")
        history.add_user_message("你好")
        history.clear()

        # 应该只保留系统提示
        assert len(history) == 1
        assert history[0].role == "system"

    def test_update_system_prompt(self):
        """测试更新系统提示词"""
        history = ChatHistory(system_prompt="初始提示")
        history.add_system_message("新的提示")

        assert len(history) == 1
        assert history[0].content == "新的提示"


class TestPromptTemplates:
    """测试提示词模板"""

    def test_list_templates(self):
        """测试列出所有模板"""
        templates = PromptTemplates.list_templates()
        assert len(templates) > 0

    def test_get_template(self):
        """测试获取指定模板"""
        template = PromptTemplates.get_template("default_assistant")
        assert template is not None
        assert template.name == "default_assistant"

    def test_template_format(self):
        """测试模板格式化"""
        template = PromptTemplates.TRANSLATOR
        result = template.format(target_language="英语")
        assert "英语" in result

    def test_template_format_missing_variable(self):
        """测试模板缺少变量时抛出异常"""
        template = PromptTemplates.VTUBER
        with pytest.raises(ValueError):
            template.format(name="测试")  # 缺少其他变量
