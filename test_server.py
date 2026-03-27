#!/usr/bin/env python3
"""
测试服务器路径和模板加载
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== 当前目录结构 ===")
print(f"__file__: {__file__}")
print(f"当前工作目录: {os.getcwd()}")
print()

# 检查 server/api.py 所在的目录
server_module = sys.modules.get("agnes.server.api")
if server_module:
    print(f"server.api.__file__: {server_module.__file__}")
else:
    import agnes.server.api

    print(f"server.api.__file__: {agnes.server.api.__file__}")
    server_module = agnes.server.api

# 计算模板路径
api_dir = os.path.dirname(server_module.__file__)
template_path1 = os.path.join(api_dir, "../web/templates/index.html")
template_path2 = os.path.join(api_dir, "../templates/index.html")

print()
print("=== 模板路径测试 ===")
print(f"路径1: {os.path.abspath(template_path1)} - 存在: {os.path.exists(template_path1)}")
print(f"路径2: {os.path.abspath(template_path2)} - 存在: {os.path.exists(template_path2)}")

# 检查 agnes/web/templates 目录
web_templates_dir = os.path.join(os.path.dirname(__file__), "agnes/web/templates")
print()
print(
    f"agnest/web/templates: {os.path.abspath(web_templates_dir)} - 存在: {os.path.exists(web_templates_dir)}"
)
if os.path.exists(web_templates_dir):
    print(f"文件列表: {os.listdir(web_templates_dir)}")

# 检查 agnes/templates 目录
templates_dir = os.path.join(os.path.dirname(__file__), "agnes/templates")
print()
print(f"agnest/templates: {os.path.abspath(templates_dir)} - 存在: {os.path.exists(templates_dir)}")
if os.path.exists(templates_dir):
    print(f"文件列表: {os.listdir(templates_dir)}")
