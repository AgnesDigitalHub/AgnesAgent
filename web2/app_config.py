"""
web2 - Amis SPA 应用配置加载器
异步按需加载版本：
1. 加载 YAML 配置（只加载菜单和应用信息）
2. 顶层 App 配置中每个页面只提供 schemaApi，不嵌入 schema
3. 单独提供获取单个页面 schema 的接口
4. 前端点击页面时再异步获取 schema
"""

import yaml
import logging
from importlib import import_module
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# 获取当前文件所在目录
current_dir = Path(__file__).parent.resolve()
config_dir = current_dir / "config"


class AmisAppConfig:
    """Amis 应用配置管理器 - 异步按需加载版本"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (config_dir / "app.yaml")
        self.raw_config: Dict[str, Any] = {}
        self.app_config: Dict[str, Any] = {}
        self._loaded: bool = False
        self.api_prefix: str = "/api"
        
    def load_yaml(self) -> Dict[str, Any]:
        """加载 YAML 配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件未找到: {self.config_path}")
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.raw_config = yaml.safe_load(f)
        
        # 获取 API 前缀
        app_config = self.raw_config.get("config", {})
        self.api_prefix = app_config.get("api_prefix", "/api")
        
        logger.info(f"已加载 YAML 配置: {self.config_path}")
        return self.raw_config
    
    def _import_schema_getter(self, page_name: str):
        """动态导入页面 schema 获取函数"""
        try:
            # 尝试从 schemas 包导入
            module_name = f"web2.schemas.{page_name}"
            module = import_module(module_name)
            getter_name = f"get_{page_name}_schema"
            if hasattr(module, getter_name):
                return getattr(module, getter_name)
        except ImportError:
            # 尝试直接导入（当在 web2 目录直接运行时）
            try:
                module_name = f"schemas.{page_name}"
                module = import_module(module_name)
                getter_name = f"get_{page_name}_schema"
                if hasattr(module, getter_name):
                    return getattr(module, getter_name)
            except ImportError as e:
                logger.warning(f"无法导入 schema: {page_name}, 错误: {e}")
                return None
        
        return None
    
    def get_page_schema(self, page_name: str) -> Optional[Dict[str, Any]]:
        """
        获取单个页面的 schema - 用于异步请求
        每次请求都会重新构建（也可以加缓存）
        """
        getter = self._import_schema_getter(page_name)
        if getter is None:
            return None
        
        try:
            schema = getter()
            # 确保页面有正确的 name/path
            if "name" not in schema:
                schema["name"] = page_name
            if "path" not in schema:
                schema["path"] = page_name
            logger.debug(f"已构建页面 schema: {page_name}")
            return schema
        except Exception as e:
            logger.error(f"构建页面 schema 失败 [{page_name}]: {e}")
            return {
                "type": "page",
                "title": page_name,
                "body": [
                    {
                        "type": "alert",
                        "level": "danger",
                        "body": f"页面 {page_name} 构建失败: {str(e)}"
                    }
                ]
            }
    
    def build_amis_app(self) -> Dict[str, Any]:
        """
        构建顶层 Amis App 配置（异步版本）：
        1. 加载 YAML
        2. 为每个页面设置 schemaApi = "get:/api/pages/{page_name}"
        3. 返回顶层 App 配置（不包含页面内容，只包含路由信息）
        """
        if not self.raw_config:
            self.load_yaml()
        
        app_config = self.raw_config.copy()
        pages_config = app_config.get("pages", {})
        app_config_data = app_config.get("config", {})
        
        logger.info(f"配置文件加载完成，app 标题: {app_config.get('app', {}).get('title')}")
        logger.info(f"菜单项数量: {len(app_config.get('menus', []))}")
        logger.info(f"页面定义数量: {len(pages_config)}")
        
        # 删除顶层多余字段，防止冲突
        if "name" in app_config:
            del app_config["name"]
        
        # 为每个页面配置 schemaApi
        # 在异步模式下，Amis 需要的结构是：
        # pages: [
        #   {
        #     "url": "/dashboard",
        #     "schemaApi": "get:/api/pages/dashboard"
        #   }
        # ]
        amis_pages = []
        
        # 添加首页路由
        amis_pages.append({
            "label": "首页",
            "url": "/",
            "schema": {
                "type": "page",
                "title": "欢迎",
                "body": "欢迎使用 Agnes Agent 控制台！请从左侧导航选择功能。"
            }
        })
        
        for page_name, page_data in pages_config.items():
            # 从菜单找 url
            path = page_name
            menus = self.raw_config.get("menus", [])
            for menu in menus:
                if menu.get("name") == page_name and "url" in menu:
                    path = menu["url"].lstrip("/")
                    break
            
            # 使用 schemaApi 而非内嵌 schema
            # app 挂载在根路径，url 必须以 / 开头，否则 AMIS 不识别为合法菜单项
            # 从菜单配置中获取 label 和 icon，这是 AMIS 生成侧边栏菜单需要的
            label = page_name
            icon = None
            menus = self.raw_config.get("menus", [])
            for menu in menus:
                if menu.get("name") == page_name:
                    label = menu.get("label", menu.get("name", page_name))
                    icon = menu.get("icon")
                    break
            
            page_config = {
                "label": label,
                "url": f"/{path}",  # AMIS 要求 url 必须以 / 开头
                "schemaApi": f"get:{self.api_prefix}/pages/{page_name}"
            }
            if icon:
                # AMIS cxd 主题默认使用 Font Awesome 图标
                # Material Design 名称需要转换为 fa fa-xxx 格式
                if not icon.startswith('fa '):
                    # 下划线转横线，添加 fa fa- 前缀
                    fa_icon = icon.replace('_', '-')
                    page_config["icon"] = f"fa fa-{fa_icon}"
                else:
                    page_config["icon"] = icon
            
            amis_pages.append(page_config)
        
        # 转换为 Amis App 结构
        result = self._convert_to_amis_structure(app_config, amis_pages)
        self.app_config = result
        self._loaded = True
        
        logger.info(f"已构建顶层 Amis 应用配置，共 {len(pages_config)} 个页面（异步模式）")
        return result
    
    def _convert_to_amis_structure(self, config: Dict[str, Any], amis_pages: list) -> Dict[str, Any]:
        """将我们的配置转换为 Amis 需要的结构"""
        app_info = config.get("app", {})
        app_config = config.get("config", {})
        
        # 构建带导航的整体布局
        # 明确指定使用侧边栏布局
        # 这确保 AMIS 一定会生成侧边栏
        result = {
            "type": "app",
            "brandName": app_info.get("title", "Amis App"),
            "description": app_info.get("description", ""),
            "theme": app_config.get("theme", "cxd"),
            "locale": app_config.get("locale", "zh-CN"),
            "layout": "aside",  # 明确指定侧边栏布局
            "pages": amis_pages
        }
        
        # 故意删除 name 字段，防止覆盖 brandName
        if "name" in result:
            del result["name"]
        
        return result
    
    def _convert_menus_to_amis_links(self, menus):
        """转换菜单配置为 Amis nav links 格式"""
        links = []
        for menu in menus:
            if menu.get("name") == "divider":
                links.append({
                    "type": "divider"
                })
                continue
                
            link = {
                "label": menu.get("label", menu.get("name")),
                "icon": menu.get("icon"),
                "to": "/" + menu.get("url", "").lstrip("/") if menu.get("url") else None,
            }
            # 如果有子菜单
            if "children" in menu:
                children = self._convert_menus_to_amis_links(menu["children"])
                link["children"] = children
            links.append(link)
        return links
    
    def get_amis_app_json(self) -> Dict[str, Any]:
        """获取完整的 Amis 应用 JSON 配置"""
        if not self._loaded:
            return self.build_amis_app()
        return self.app_config


# 单例模式，全局保存构建好的配置
_app_config_instance: Optional[AmisAppConfig] = None
_cached_amis_app: Optional[Dict[str, Any]] = None


def get_app_config(config_path: Optional[Path] = None) -> AmisAppConfig:
    """获取应用配置单例"""
    global _app_config_instance
    if _app_config_instance is None:
        _app_config_instance = AmisAppConfig(config_path)
    return _app_config_instance


def get_built_amis_app(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """获取构建好的完整 Amis 应用配置（带缓存）"""
    global _cached_amis_app
    if _cached_amis_app is None:
        config = get_app_config(config_path)
        _cached_amis_app = config.build_amis_app()
    return _cached_amis_app


def reload_amis_app(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """重新加载并构建 Amis 应用配置"""
    global _cached_amis_app, _app_config_instance
    _cached_amis_app = None
    _app_config_instance = None
    return get_built_amis_app(config_path)