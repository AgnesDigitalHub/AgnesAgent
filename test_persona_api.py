#!/usr/bin/env python3
"""测试人格 API 端点"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime

from web2.persona import PersonaStore


def test_list_personas():
    """测试人格列表 API 逻辑"""
    print("正在测试人格列表 API...")

    try:
        # 创建人格存储实例
        persona_store = PersonaStore(Path("config/personas/personas.json"))

        # 获取所有格
        all_personas = persona_store.list_personas()
        print(f"✓ 成功获取 {len(all_personas)} 个人格")

        # 按修改时间倒序
        all_personas.sort(key=lambda p: p.updated_at or datetime.min, reverse=True)

        # 准备返回数据
        items = []
        for p in all_personas:
            pd = p.to_dict()
            print(f"\n人格: {pd.get('full_name')}")
            print(f"  ID: {pd.get('id')}")
            print(f"  Identity: {pd.get('identity')}")
            print(f"  Description: {pd.get('description')}")
            print(f"  所有字段: {list(pd.keys())}")
            items.append(pd)

        print(f"\n✓ API 返回数据准备完成，共 {len(items)} 个项目")
        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_list_personas()
    sys.exit(0 if success else 1)
