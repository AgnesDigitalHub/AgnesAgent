"""
延迟导入工具

用于优化启动时间和内存占用，只在需要时才加载模块
"""

from __future__ import annotations

import importlib
import sys
from typing import TYPE_CHECKING, Any, TypeVar

T = TypeVar("T")


class LazyModule:
    """
    延迟加载模块

    只在首次访问属性时才实际导入模块
    """

    def __init__(self, module_name: str, package: str | None = None):
        self._module_name = module_name
        self._package = package
        self._module: Any = None
        self._loaded = False

    def _load(self) -> Any:
        """实际加载模块"""
        if not self._loaded:
            self._module = importlib.import_module(self._module_name, self._package)
            self._loaded = True
        return self._module

    def __getattr__(self, name: str) -> Any:
        """代理属性访问到实际模块"""
        module = self._load()
        return getattr(module, name)

    def __dir__(self) -> list[str]:
        """支持 dir() 函数"""
        module = self._load()
        return dir(module)

    def __repr__(self) -> str:
        status = "loaded" if self._loaded else "lazy"
        return f"<LazyModule '{self._module_name}' ({status})>"


class LazyImport:
    """
    延迟导入装饰器/上下文管理器

    用于延迟导入重型依赖
    """

    def __init__(self, module_name: str, attr_name: str | None = None):
        self.module_name = module_name
        self.attr_name = attr_name
        self._module: Any = None
        self._attr: Any = None

    def _import(self) -> Any:
        """执行实际导入"""
        if self._module is None:
            self._module = importlib.import_module(self.module_name)
            if self.attr_name:
                self._attr = getattr(self._module, self.attr_name)
        return self._attr if self.attr_name else self._module

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """作为函数调用时，导入并调用"""
        target = self._import()
        return target(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """代理属性访问"""
        module = self._import()
        return getattr(module, name)

    def __enter__(self) -> Any:
        """上下文管理器入口"""
        return self._import()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器出口"""
        pass


def lazy_import(module_name: str, attr_name: str | None = None) -> LazyImport:
    """
    创建延迟导入对象

    Args:
        module_name: 模块名称
        attr_name: 可选，模块中的属性名称

    Returns:
        LazyImport: 延迟导入对象

    Example:
        >>> np = lazy_import("numpy")
        >>> pd = lazy_import("pandas")
        >>> AsyncOpenAI = lazy_import("openai", "AsyncOpenAI")
    """
    return LazyImport(module_name, attr_name)


def import_on_demand(module_name: str) -> LazyModule:
    """
    创建延迟加载的模块

    Args:
        module_name: 模块名称

    Returns:
        LazyModule: 延迟加载的模块对象

    Example:
        >>> np = import_on_demand("numpy")
        >>> # 此时 numpy 还未加载
        >>> arr = np.array([1, 2, 3])  # 此时才加载 numpy
    """
    return LazyModule(module_name)


# 常用重型依赖的延迟导入
if TYPE_CHECKING:
    # 类型检查时导入，实际运行时不导入
    import numpy as np
    import pandas as pd
    from openai import AsyncOpenAI
else:
    # 实际运行时创建延迟导入对象
    np = None  # 使用 import_on_demand 在需要时导入
    pd = None
    AsyncOpenAI = None


def get_numpy() -> Any:
    """获取 numpy（延迟导入）"""
    global np
    if np is None:
        np = importlib.import_module("numpy")
    return np


def get_pandas() -> Any:
    """获取 pandas（延迟导入）"""
    global pd
    if pd is None:
        pd = importlib.import_module("pandas")
    return pd


def get_openai() -> Any:
    """获取 openai（延迟导入）"""
    if "openai" not in sys.modules:
        return importlib.import_module("openai")
    return sys.modules["openai"]
