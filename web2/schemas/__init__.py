"""
web2 - 所有页面 schema 模块
每个页面对应一个模块，每个模块提供 get_xxx_schema() 函数
返回已经使用 Pydantic 构建好的 schema dict

注意：不需要在这里预导入，由 app_config.py 动态导入解决循环依赖问题
"""

# 空的 __init__.py，只作为包标识
# 所有 schema 模块由 app_config.py 动态按需导入
__all__ = []
