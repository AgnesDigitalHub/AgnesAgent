#!/usr/bin/env python3
"""测试 dashboard 页面"""

from web2.schemas.dashboard import get_dashboard_schema

print("测试 dashboard 页面构建...")
schema = get_dashboard_schema()
print(f"✓ 导入成功！")
print(f"  title: {schema.get('title')}")
print(f"  type: {schema.get('type')}")
print(f"  body: {type(schema.get('body'))}, length: {len(schema['body']) if isinstance(schema['body'], list) else 1}")

print("\n完整 schema JSON：")
import json
print(json.dumps(schema, indent=2, ensure_ascii=False))