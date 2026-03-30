#!/usr/bin/env python3
"""测试配置加载"""

import os
import sys
import unittest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agnes.utils.config_loader import ConfigLoader


class TestConfigLoader(unittest.TestCase):
    """配置加载器测试"""

    def setUp(self):
        """测试前准备"""
        self.test_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")

    def test_config_load(self):
        """测试配置加载"""
        loader = ConfigLoader(self.test_config_path)
        config = loader.load()

        # 验证默认值
        self.assertIsNotNone(config.llm)
        self.assertIsNotNone(config.asr)
        self.assertIsNotNone(config.audio)
        self.assertIsNotNone(config.vad)
        self.assertIsNotNone(config.proxy)

        # 验证配置值
        self.assertEqual(config.llm.provider, "ollama")
        self.assertEqual(config.asr.provider, "local_whisper")

    def test_proxy_none_handling(self):
        """测试 proxy 为 None 的情况"""
        loader = ConfigLoader(self.test_config_path)
        config = loader.load()

        # 即使 config.yaml 中 proxy 为 None，也应该有默认值
        self.assertIsNotNone(config.proxy)
        self.assertIsNone(config.proxy.http_proxy)
        self.assertIsNone(config.proxy.https_proxy)

    def test_set_proxy_env(self):
        """测试设置代理环境变量"""
        loader = ConfigLoader(self.test_config_path)
        config = loader.load()

        # 保存原始环境变量
        original_http = os.environ.get("http_proxy")
        original_https = os.environ.get("https_proxy")

        try:
            # 测试设置代理
            config.proxy.http_proxy = "http://test-proxy:8080"
            config.proxy.https_proxy = "http://test-proxy:8080"
            loader.set_proxy_env(config)

            self.assertEqual(os.environ.get("http_proxy"), "http://test-proxy:8080")
            self.assertEqual(os.environ.get("https_proxy"), "http://test-proxy:8080")
        finally:
            # 恢复原始环境变量
            if original_http:
                os.environ["http_proxy"] = original_http
            elif "http_proxy" in os.environ:
                del os.environ["http_proxy"]

            if original_https:
                os.environ["https_proxy"] = original_https
            elif "https_proxy" in os.environ:
                del os.environ["https_proxy"]


if __name__ == "__main__":
    unittest.main()
