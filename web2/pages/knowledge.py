"""
Knowledge Base Page - AMIS Schema
知识库管理：支持文档上传、向量检索、RAG 配置
"""


def get_knowledge_schema() -> dict:
    """获取知识库管理页面 schema"""
    from web2.schemas.knowledge import get_knowledge_schema as _get_schema

    return _get_schema()
