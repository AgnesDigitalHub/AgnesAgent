"""
screen_capture - 截取当前游戏画面
支持全屏截取和区域截取
"""
import base64
import io
import time
from typing import Any, Dict, Optional
from PIL import Image
from agnes.skills.base import BaseSkill, SkillSchema, SkillResult, SkillMetadata


class ScreenCaptureSkill(BaseSkill):
    """截取当前屏幕画面（全屏或指定区域）"""

    name = "screen_capture"
    description = "截取当前屏幕画面，支持全屏截取和指定区域截取。返回 PNG 格式的图像数据。"

    metadata = SkillMetadata(
        version="1.0.0",
        category="perception",
        permission_level="safe",
        cost=0.01,
        tags=["screen", "capture", "image", "vision", "game"]
    )

    def __init__(self):
        self._mss = None
        self._initialized = False

    def _lazy_init(self):
        """延迟初始化 mss"""
        if self._initialized:
            return
        import mss
        self._mss = mss.mss()
        self._initialized = True

    def get_schema(self) -> SkillSchema:
        return SkillSchema(
            name=self.name,
            description=self.description,
            parameters={
                "left": {
                    "type": "integer",
                    "description": "截取区域左边界坐标，如果不指定则截取全屏"
                },
                "top": {
                    "type": "integer",
                    "description": "截取区域上边界坐标，如果不指定则截取全屏"
                },
                "width": {
                    "type": "integer",
                    "description": "截取区域宽度，如果不指定则截取全屏"
                },
                "height": {
                    "type": "integer",
                    "description": "截取区域高度，如果不指定则截取全屏"
                },
                "monitor": {
                    "type": "integer",
                    "description": "截取哪个显示器，从1开始计数，默认1",
                    "default": 1
                },
                "quality": {
                    "type": "integer",
                    "description": "PNG 压缩质量（1-100），越大质量越好默认 90",
                    "default": 90
                },
                "return_base64": {
                    "type": "boolean",
                    "description": "是否返回 base64 编码，默认 True",
                    "default": True
                }
            },
            required=[],
            returns={
                "base64": "string - Base64 编码的 PNG 图像",
                "width": "integer - 图像宽度",
                "height": "integer - 图像高度",
                "left": "integer - 实际左边界",
                "top": "integer - 实际上边界",
                "monitor": "integer - 显示器编号"
            }
        )

    async def execute(self, parameters: Dict[str, Any]) -> SkillResult:
        start_time = time.time()

        try:
            self._lazy_init()

            left = parameters.get("left")
            top = parameters.get("top")
            width = parameters.get("width")
            height = parameters.get("height")
            monitor = parameters.get("monitor", 1) - 1  # mss 从0开始
            quality = parameters.get("quality", 90)
            return_base64 = parameters.get("return_base64", True)

            # 获取显示器信息
            monitors = self._mss.monitors
            if monitor >= len(monitors):
                return SkillResult.error(
                    "invalid_monitor",
                    f"显示器编号 {monitor + 1} 不存在，系统只有 {len(monitors) - 1} 个显示器"
                )

            if left is None or top is None or width is None or height is None:
                # 全屏截取
                monitor_box = monitors[monitor]
                bbox = {
                    "left": monitor_box["left"],
                    "top": monitor_box["top"],
                    "width": monitor_box["width"],
                    "height": monitor_box["height"]
                }
            else:
                # 区域截取 - 相对于显示器左上角
                base_monitor = monitors[monitor]
                bbox = {
                    "left": base_monitor["left"] + left,
                    "top": base_monitor["top"] + top,
                    "width": width,
                    "height": height
                }

            # 截取
            screenshot = self._mss.grab(bbox)

            # 转换为 PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

            # 压缩为 PNG
            buf = io.BytesIO()
            img.save(buf, format="PNG", quality=quality)
            buf.seek(0)
            image_bytes = buf.getvalue()

            result = {
                "width": screenshot.width,
                "height": screenshot.height,
                "left": bbox["left"],
                "top": bbox["top"],
                "monitor": monitor + 1
            }

            if return_base64:
                result["base64"] = base64.b64encode(image_bytes).decode("utf-8")

            execution_time = (time.time() - start_time) * 1000
            return SkillResult.ok(result, execution_time_ms=execution_time)

        except ImportError:
            return SkillResult.error(
                "dependency_missing",
                "mss 库未安装，请安装: pip install mss"
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return SkillResult.error("exception", str(e), execution_time)

    def __del__(self):
        """清理资源"""
        if self._mss:
            self._mss.close()


# 注册到全局注册表
from agnes.skills.registry import registry
registry.register(ScreenCaptureSkill())
