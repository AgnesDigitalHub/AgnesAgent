"""
web2 - Amis SPA 应用配置加载器
异步按需加载版本：
1. 加载 YAML 配置（只加载菜单和应用信息）
2. 顶层 App 配置中每个页面只提供 schemaApi，不嵌入 schema
3. 单独提供获取单个页面 schema 的接口
4. 前端点击页面时再异步获取 schema
"""

import logging
from importlib import import_module
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# 获取当前文件所在目录
current_dir = Path(__file__).parent.resolve()
config_dir = current_dir / "config"


class AmisAppConfig:
    """Amis 应用配置管理器 - 异步按需加载版本"""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or (config_dir / "app.yaml")
        self.raw_config: dict[str, Any] = {}
        self.app_config: dict[str, Any] = {}
        self._loaded: bool = False
        self.api_prefix: str = "/api"

    def load_yaml(self) -> dict[str, Any]:
        """加载 YAML 配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件未找到: {self.config_path}")

        with open(self.config_path, encoding="utf-8") as f:
            self.raw_config = yaml.safe_load(f)

        # 获取 API 前缀
        app_config = self.raw_config.get("config", {})
        self.api_prefix = app_config.get("api_prefix", "/api")

        # 设置日志级别
        log_level_name = app_config.get("log_level", "info").upper()
        log_level = getattr(logging, log_level_name, logging.INFO)
        logging.getLogger().setLevel(log_level)

        logger.info(f"已加载 YAML 配置: {self.config_path}")
        logger.info(f"日志级别设置为: {log_level_name} ({log_level})")
        return self.raw_config

    def _import_schema_getter(self, page_name: str):
        """动态导入页面 schema 获取函数"""
        import importlib.util
        import sys
        from pathlib import Path

        logger.info(f"尝试导入页面 schema: page_name={page_name}")
        logger.debug(f"Python sys.path: {sys.path[:5]}...")

        getter_name = f"get_{page_name}_schema"
        logger.info(f"需要的获取函数名称: {getter_name}")

        # 尝试 1: 从 web2.schemas 包导入（从项目根目录启动时）
        try:
            module_name = f"web2.schemas.{page_name}"
            logger.debug(f"尝试导入: {module_name}")
            module = import_module(module_name)
            if hasattr(module, getter_name):
                logger.debug(f"导入成功: {module_name}")
                return getattr(module, getter_name)
        except ImportError as e:
            logger.info(f"导入 web2.schemas.{page_name} 失败: {e}")

        # 尝试 2: 尝试直接从当前包导入（当在 web2 目录直接运行时）
        try:
            module_name = f".schemas.{page_name}"
            logger.debug(f"尝试导入相对包: {module_name}")
            module = import_module(module_name, package="web2")
            if hasattr(module, getter_name):
                logger.debug(f"导入成功: {module_name} 从相对包")
                return getattr(module, getter_name)
        except ImportError as e2:
            logger.info(f"导入相对包失败: {e2}")

        # 尝试 3: 直接通过文件路径导入（最可靠的方式）
        try:
            schema_dir = Path(__file__).parent / "schemas"
            module_path = schema_dir / f"{page_name}.py"
            if not module_path.exists():
                logger.error(f"schema 文件不存在: {module_path} (检查路径是否正确)")
                logger.error(f"当前目录: {Path.cwd()}")
                return None

            logger.info(f"尝试文件路径导入: {module_path}")
            spec = importlib.util.spec_from_file_location(f"web2.schemas.{page_name}", module_path)
            if spec is None or spec.loader is None:
                logger.error(f"无法创建模块 spec: {module_path}")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[f"web2.schemas.{page_name}"] = module
            spec.loader.exec_module(module)

            if hasattr(module, getter_name):
                logger.info(f"文件路径导入成功: {module_path}")
                return getattr(module, getter_name)
            else:
                logger.error(f"模块中找不到 {getter_name} 函数，模块内容: {dir(module)}")
                return None

        except Exception as e:
            logger.error(f"文件路径导入也失败: {page_name}, 错误: {e}", exc_info=True)
            return None

        return None

    def get_page_schema(self, page_name: str) -> dict[str, Any] | None:
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
                "body": [{"type": "alert", "level": "danger", "body": f"页面 {page_name} 构建失败: {str(e)}"}],
            }

    def build_amis_app(self) -> dict[str, Any]:
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
        amis_pages.append(
            {
                "label": "首页",
                "url": "/",
                "schema": {
                    "type": "page",
                    "title": "Agnes Agent",
                    "body": {
                        "type": "flex",
                        "className": "p-4 justify-center items-center",
                        "items": [
                            {
                                "type": "card",
                                "className": "w-1/3",
                                "body": {
                                    "type": "tpl",
                                    "tpl": "<div class='text-lg font-bold text-center'>Agnes Agent</div><div class='text-gray-500 text-center'>高度可扩展、跨平台的 AI Agent 基础架构</div>",
                                },
                            },
                            {
                                "type": "card",
                                "className": "w-1/3 ml-4",
                                "body": {
                                    "type": "tpl",
                                    "tpl": "<div class='text-lg font-bold text-center'>GitHub</div><div class='text-gray-500 text-center'><a href='https://github.com/AgnesDigitalHub/AgnesAgent' target='_blank'>AgnesDigitalHub/AgnesAgent</a></div>",
                                },
                            },
                            {
                                "type": "card",
                                "className": "w-1/3 ml-4",
                                "body": {
                                    "type": "tpl",
                                    "tpl": "<div class='text-lg font-bold text-center'>提交 Issue</div><div class='text-gray-500 text-center'><a href='https://github.com/AgnesDigitalHub/AgnesAgent/issues' target='_blank'>报告问题或建议</a></div>",
                                },
                            },
                        ],
                    },
                },
            }
        )

        # 递归收集所有页面（从菜单配置）
        # 只有有 url 的菜单项才会被当作页面添加
        # 有 children 的折叠菜单项不会作为页面，只会处理它的 children
        def collect_pages_from_menus(menus, parent_path=""):
            collected = []
            for menu in menus:
                if "children" in menu and menu["children"]:
                    # 有子菜单：只递归处理子菜单，父菜单本身不添加页面
                    # 父菜单只作为折叠项展示在侧边栏
                    collected.extend(collect_pages_from_menus(menu["children"], menu.get("url", "")))
                    # 如果父菜单自己也有 url（极少数情况），才额外添加它
                    if "url" in menu and menu["url"]:
                        page_name = menu.get("name")
                        if page_name:
                            url_path = menu["url"].lstrip("/")
                            # url_path 转换为文件名：mcp/servers -> mcp_servers
                            page_name_py = url_path.replace("/", "_").replace("-", "_")

                            # 获取 label 和 icon
                            label = menu.get("label", page_name)
                            icon = menu.get("icon")

                            page_config = {
                                "label": label,
                                "url": f"/{url_path}",  # AMIS 要求 url 必须以 / 开头
                                "schemaApi": f"get:{self.api_prefix}/pages/{url_path}",
                            }
                            if icon:
                                if not icon.startswith("fa "):
                                    fa_icon = icon.replace("_", "-")
                                    page_config["icon"] = f"fa fa-{fa_icon}"
                                else:
                                    page_config["icon"] = icon
                            collected.append(page_config)
                elif "url" in menu:
                    # 叶子节点（有 url 没有 children）才添加页面
                    page_name = menu.get("name")
                    if not page_name:
                        continue

                    url_path = menu["url"].lstrip("/")
                    # url_path 转换为文件名：mcp/servers -> mcp_servers
                    page_name_py = url_path.replace("/", "_").replace("-", "_")

                    # 获取 label 和 icon
                    label = menu.get("label", page_name)
                    icon = menu.get("icon")

                    page_config = {
                        "label": label,
                        "url": f"/{url_path}",  # AMIS 要求 url 必须以 / 开头
                        "schemaApi": f"get:{self.api_prefix}/pages/{url_path}",
                    }
                    if icon:
                        # AMIS cxd 主题默认使用 Font Awesome 图标
                        # Material Design 名称需要转换为 fa fa-xxx 格式
                        if not icon.startswith("fa "):
                            # 下划线转横线，添加 fa fa- 前缀
                            fa_icon = icon.replace("_", "-")
                            page_config["icon"] = f"fa fa-{fa_icon}"
                        else:
                            page_config["icon"] = icon

                    collected.append(page_config)
            return collected

        # 从菜单配置递归收集所有页面
        menus = self.raw_config.get("menus", [])
        collected_pages = collect_pages_from_menus(menus)
        amis_pages.extend(collected_pages)

        # 转换为 Amis App 结构
        result = self._convert_to_amis_structure(app_config, amis_pages)
        self.app_config = result
        self._loaded = True

        logger.info(f"已构建顶层 Amis 应用配置，共 {len(pages_config)} 个页面（异步模式）")
        return result

    def _convert_to_amis_structure(self, config: dict[str, Any], amis_pages: list) -> dict[str, Any]:
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
            "pages": amis_pages,
        }

        # 故意删除 name 字段，防止覆盖 brandName
        if "name" in result:
            del result["name"]

        logger.debug(f"构建顶层 App 结构，pages 数量: {len(amis_pages)}")
        for i, page in enumerate(amis_pages):
            logger.debug(
                f"  page[{i}]: label={page.get('label')}, url={page.get('url')}, schemaApi={page.get('schemaApi')}"
            )

        return result

    def _convert_menus_to_amis_links(self, menus):
        """转换菜单配置为 Amis nav links 格式"""
        links = []
        for menu in menus:
            if menu.get("name") == "divider":
                links.append({"type": "divider"})
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

    def get_amis_app_json(self) -> dict[str, Any]:
        """获取完整的 Amis 应用 JSON 配置"""
        if not self._loaded:
            return self.build_amis_app()
        return self.app_config


# 单例模式，全局保存构建好的配置
_app_config_instance: AmisAppConfig | None = None
_cached_amis_app: dict[str, Any] | None = None


def get_app_config(config_path: Path | None = None) -> AmisAppConfig:
    """获取应用配置单例"""
    global _app_config_instance
    if _app_config_instance is None:
        _app_config_instance = AmisAppConfig(config_path)
    return _app_config_instance


def get_built_amis_app(config_path: Path | None = None) -> dict[str, Any]:
    """获取构建好的完整 Amis 应用配置（带缓存）"""
    global _cached_amis_app
    if _cached_amis_app is None:
        config = get_app_config(config_path)
        _cached_amis_app = config.build_amis_app()
    return _cached_amis_app


def reload_amis_app(config_path: Path | None = None) -> dict[str, Any]:
    """重新加载并构建 Amis 应用配置"""
    global _cached_amis_app, _app_config_instance
    _cached_amis_app = None
    _app_config_instance = None
    return get_built_amis_app(config_path)
