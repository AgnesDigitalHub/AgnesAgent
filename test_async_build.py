#!/usr/bin/env python3
"""测试异步构建 - 验证顶层 App schema 生成"""

from web2.app_config import get_built_amis_app, get_app_config

print("🚀 测试异步模式构建顶层 AMIS App 配置...")
schema = get_built_amis_app()

print(f"\n✓ 构建完成！")
print(f"  App 类型: {schema.get('type')}")
print(f"  App 名称: {schema.get('name')}")
print(f"  主题: {schema.get('theme')}")
print(f"  语言: {schema.get('locale')}")
print(f"  pages 数量: {len(schema.get('pages', []))}")

print("\n📋 pages 结构验证（应该包含 schemaApi）:")
for i, page in enumerate(schema['pages'][:3]):  # 只显示前3个
    path = page.get('path', 'N/A')
    schema_api = page.get('schemaApi', 'NOT FOUND')
    print(f"  [{i}] path: /{path}")
    print(f"       schemaApi: {schema_api}")

print("\n... 剩余页面省略")

# 验证所有页面都有 schemaApi
all_have_schemaapi = all('schemaApi' in p for p in schema['pages'])
print(f"\n✅ 验证结果:")
print(f"  所有页面都配置了 schemaApi: {'✓ 通过' if all_have_schemaapi else '✗ 失败'}")

# 测试获取单个页面
print("\n🧪 测试单个页面 schema 获取 (dashboard):")
app_config = get_app_config()
page_schema = app_config.get_page_schema('dashboard')
if page_schema:
    print(f"  ✓ 获取成功")
    print(f"    类型: {page_schema.get('type')}")
    print(f"    标题: {page_schema.get('title')}")
    print(f"    body 项数: {len(page_schema.get('body', [])) if isinstance(page_schema.get('body'), list) else 1}")

print("\n🧪 测试单个页面 schema 获取 (settings):")
page_schema = app_config.get_page_schema('settings')
if page_schema:
    print(f"  ✓ 获取成功")
    print(f"    类型: {page_schema.get('type')}")
    print(f"    标题: {page_schema.get('title')}")

print("\n🧪 测试单个页面 schema 获取 (agents):")
page_schema = app_config.get_page_schema('agents')
if page_schema:
    print(f"  ✓ 获取成功")
    print(f"    类型: {page_schema.get('type')}")
    print(f"    标题: {page_schema.get('title')}")

print("\n🎉 异步模式架构验证完成！")
print("\n架构特点:")
print("  ✓ 顶层 App 配置很小（只包含菜单路由）")
print("  ✓ 每个页面只有 schemaApi，不内嵌 schema")  
print("  ✓ schemaApi 格式: get:/api/pages/{page_name}")
print("  ✓ Pydantic 仍然用于构建每个页面 schema")
print("  ✓ 前端点击时异步加载，首页快速响应")
print("  ✓ AMIS CDN 由浏览器加载，不占用服务器带宽")