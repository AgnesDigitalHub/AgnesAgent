#!/usr/bin/env python3
"""
测试 python-amis 重构是否成功
"""

import sys
sys.path.insert(0, '.')

# 测试所有schema文件是否都能正常导入和生成
def test_all_schemas():
    print("🧪 开始测试所有web2 schemas...\n")
    
    tests = [
        ("dashboard", "get_dashboard_schema"),
        ("models", "get_models_schema"),
        ("chat", "get_chat_schema"), 
        ("agents", "get_agents_schema"),
        ("prompts", "get_prompts_schema"),
        ("knowledge", "get_knowledge_schema"),
        ("tools", "get_tools_schema"),
        ("workflows", "get_workflows_schema"),
        ("logs", "get_logs_schema"),
        ("users", "get_users_schema"),
        ("settings", "get_settings_schema"),
        ("publish", "get_publish_schema"),
    ]
    
    success_count = 0
    failed_count = 0
    
    for module_name, func_name in tests:
        try:
            # 动态导入
            module = __import__(f"web2.schemas.{module_name}", fromlist=[func_name])
            func = getattr(module, func_name)
            schema = func()
            
            # 验证返回结构
            assert isinstance(schema, dict), "返回值不是字典"
            assert "type" in schema, "缺少type字段"
            assert "title" in schema, "缺少title字段"
            
            print(f"✅ {module_name}: 成功生成Schema")
            print(f"   标题: {schema['title']}, 类型: {schema['type']}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ {module_name}: 失败 - {str(e)}")
            failed_count += 1
    
    print(f"\n📊 测试完成: 成功 {success_count}, 失败 {failed_count}")
    
    if failed_count == 0:
        print("\n🎉 所有schema文件都使用python-amis重构成功!")
        return True
    else:
        print(f"\n⚠️  有 {failed_count} 个文件失败，请检查错误")
        return False


if __name__ == "__main__":
    success = test_all_schemas()
    sys.exit(0 if success else 1)