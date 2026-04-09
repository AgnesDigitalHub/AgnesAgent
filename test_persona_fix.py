#!/usr/bin/env python3
"""测试人格修复是否正常工作"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from web2.persona import PersonaStore


def test_persona_loading():
    """测试人格加载是否正常"""
    print("正在测试人格加载...")

    try:
        # 创建人格存储实例
        persona_store = PersonaStore(Path("config/personas/personas.json"))

        # 尝试列出所有格
        personas = persona_store.list_personas()

        print(f"✓ 成功加载 {len(personas)} 个人格")

        for persona in personas:
            print(f"  - {persona.full_name} (ID: {persona.id})")
            print(f"    Identity: {persona.identity}")

        print("\n✓ 所有测试通过！人格管理功能已修复。")
        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_persona_loading()
    sys.exit(0 if success else 1)
