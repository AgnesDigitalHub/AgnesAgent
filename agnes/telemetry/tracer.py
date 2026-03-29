"""
OpenTelemetry Tracer 核心配置
提供 tracer 实例和基本的跨度管理
"""

import logging
from collections.abc import Callable
from contextlib import AbstractContextManager, contextmanager

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.semconv.resource import ResourceAttributes

logger = logging.getLogger(__name__)

# 全局 tracer 提供者
_tracer_provider: TracerProvider | None = None
_tracer: trace.Tracer | None = None


def configure_tracer(
    service_name: str = "agnes-agent",
    service_version: str = "1.0.0",
    enable_console: bool = True,
    otlp_endpoint: str | None = None,
) -> trace.Tracer:
    """
    配置 OpenTelemetry tracer
    :param service_name: 服务名称
    :param service_version: 服务版本
    :param enable_console: 是否输出到控制台
    :param otlp_endpoint: OTLP 端点地址，例如 "http://localhost:4317"
    :return: Tracer 实例
    """
    global _tracer_provider, _tracer

    # 创建资源
    resource = Resource.create(
        {
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: service_name,
        }
    )

    # 创建提供者
    _tracer_provider = TracerProvider(resource=resource)

    # 添加控制台导出器（用于开发调试）
    if enable_console:
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        _tracer_provider.add_span_processor(processor)

    # 添加 OTLP 导出器（用于生产环境）
    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
            _tracer_provider.add_span_processor(processor)
            logger.info(f"已配置 OTLP 导出器: {otlp_endpoint}")
        except ImportError:
            logger.warning("未安装 opentelemetry-exporter-otlp，无法使用 OTLP 导出")

    # 设置全局提供者
    trace.set_tracer_provider(_tracer_provider)

    # 获取 tracer
    _tracer = trace.get_tracer(service_name, service_version)

    logger.info(f"OpenTelemetry tracer 已配置: service={service_name}")
    return _tracer


def get_tracer() -> trace.Tracer:
    """获取全局 tracer，如果未配置则自动配置"""
    global _tracer
    if _tracer is None:
        return configure_tracer()
    return _tracer


@contextmanager
def start_span(
    name: str,
    attributes: dict | None = None,
) -> AbstractContextManager[trace.Span]:
    """
    启动一个新的跨度，用于上下文管理器
    :param name: 跨度名称
    :param attributes: 跨度属性
    :yield: 当前跨度
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield span


def get_current_span() -> trace.Span:
    """获取当前活跃的跨度"""
    return trace.get_current_span()


def trace_function(name: str | None = None, attributes: dict | None = None):
    """
    函数追踪装饰器
    :param name: 跨度名称，默认使用函数名
    :param attributes: 固定属性
    """

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            span_name = name or func.__name__
            with start_span(span_name, attributes) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                return func(*args, **kwargs)

        return wrapper

    return decorator
