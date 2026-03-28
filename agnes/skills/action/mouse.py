"""
mouse_action - 鼠标输入控制
支持移动、点击、滚轮、拖拽
"""

import asyncio
import time
from typing import Any

from agnes.skills.base import BaseSkill, SkillMetadata, SkillResult, SkillSchema


class MouseActionSkill(BaseSkill):
    """鼠标输入控制，模拟移动、点击、滚轮、拖拽"""

    name = "mouse_action"
    description = "模拟鼠标输入，支持移动指针、点击、滚轮滚动和拖拽操作。"

    metadata = SkillMetadata(
        version="1.0.0",
        category="action",
        permission_level="restricted",
        cost=0.0,
        tags=["mouse", "input", "control", "click", "move"],
    )

    def __init__(self):
        self._controller = None
        self._initialized = False

    def _lazy_init(self):
        """延迟初始化 pynput"""
        if self._initialized:
            return
        from pynput import mouse

        self._controller = mouse.Controller()
        self._mouse = mouse
        self._initialized = True

    def get_schema(self) -> SkillSchema:
        return SkillSchema(
            name=self.name,
            description=self.description,
            parameters={
                "action": {
                    "type": "string",
                    "enum": ["move", "click", "press", "release", "scroll", "drag"],
                    "description": (
                        "动作类型:\n"
                        "- move: 移动鼠标到指定坐标\n"
                        "- click: 点击按键（按下后松开）\n"
                        "- press: 按下按键不放\n"
                        "- release: 松开按键\n"
                        "- scroll: 滚动滚轮\n"
                        "- drag: 从起点拖拽到终点"
                    ),
                },
                "x": {"type": "integer", "description": "目标 X 坐标（屏幕绝对坐标），适用于 move/click/drag"},
                "y": {"type": "integer", "description": "目标 Y 坐标（屏幕绝对坐标），适用于 move/click/drag"},
                "from_x": {"type": "integer", "description": "拖拽起点 X，适用于 drag"},
                "from_y": {"type": "integer", "description": "拖拽起点 Y，适用于 drag"},
                "button": {
                    "type": "string",
                    "enum": ["left", "right", "middle"],
                    "description": "鼠标按键，默认 left",
                    "default": "left",
                },
                "clicks": {"type": "integer", "description": "点击次数，默认 1，2=双击", "default": 1},
                "delta_y": {"type": "integer", "description": "滚轮滚动量，正数向上，负数向下，适用于 scroll"},
                "delta_x": {"type": "integer", "description": "水平滚轮滚动量，默认 0", "default": 0},
                "duration_ms": {
                    "type": "integer",
                    "description": "移动持续时间毫秒（平滑移动），默认 0 瞬间移动",
                    "default": 0,
                },
                "post_delay_ms": {"type": "integer", "description": "动作完成后额外延迟毫秒，默认 0", "default": 0},
            },
            required=["action"],
            returns={
                "success": "boolean - 是否成功",
                "action": "string - 执行的动作",
                "current_x": "integer - 当前 X 坐标",
                "current_y": "integer - 当前 Y 坐标",
            },
        )

    def _parse_button(self, button_name: str):
        """解析按键名称"""
        button_name = button_name.lower()
        if button_name == "left":
            return self._mouse.Button.left
        elif button_name == "right":
            return self._mouse.Button.right
        elif button_name == "middle":
            return self._mouse.Button.middle
        else:
            raise ValueError(f"Unknown button: {button_name}")

    async def _smooth_move(self, from_x: int, from_y: int, to_x: int, to_y: int, duration_ms: int):
        """平滑移动"""
        steps = max(1, duration_ms // 10)
        dx = (to_x - from_x) / steps
        dy = (to_y - from_y) / steps
        step_delay = duration_ms / (steps * 1000.0)

        current_x = from_x
        current_y = from_y

        for _ in range(steps):
            current_x += dx
            current_y += dy
            self._controller.position = (int(round(current_x)), int(round(current_y)))
            await asyncio.sleep(step_delay)

        # 确保最终位置准确
        self._controller.position = (to_x, to_y)

    async def execute(self, parameters: dict[str, Any]) -> SkillResult:
        start_time = time.time()

        try:
            self._lazy_init()

            action = parameters.get("action", "").lower()
            x = parameters.get("x")
            y = parameters.get("y")
            from_x = parameters.get("from_x")
            from_y = parameters.get("from_y")
            button_name = parameters.get("button", "left")
            clicks = parameters.get("clicks", 1)
            delta_y = parameters.get("delta_y")
            delta_x = parameters.get("delta_x", 0)
            duration_ms = parameters.get("duration_ms", 0)
            post_delay_ms = parameters.get("post_delay_ms", 0)

            button = self._parse_button(button_name)

            if action == "move":
                if x is None or y is None:
                    return SkillResult.error("missing_parameter", "参数 'x' 和 'y' 是必须的")

                if duration_ms > 0:
                    current = self._controller.position
                    await self._smooth_move(current[0], current[1], x, y, duration_ms)
                else:
                    self._controller.position = (x, y)

            elif action in ["click", "press", "release"]:
                if x is not None and y is not None:
                    # 先移动再点击
                    if duration_ms > 0:
                        current = self._controller.position
                        await self._smooth_move(current[0], current[1], x, y, duration_ms)
                    else:
                        self._controller.position = (x, y)

                if action == "click":
                    # 多次点击
                    for i in range(clicks):
                        if i > 0:
                            await asyncio.sleep(0.1)
                        self._controller.press(button)
                        await asyncio.sleep(0.01)
                        self._controller.release(button)
                elif action == "press":
                    self._controller.press(button)
                elif action == "release":
                    self._controller.release(button)

            elif action == "scroll":
                if delta_y is None:
                    return SkillResult.error("missing_parameter", "参数 'delta_y' 是必须的")
                self._controller.scroll(delta_x, delta_y)

            elif action == "drag":
                if from_x is None or from_y is None or x is None or y is None:
                    return SkillResult.error("missing_parameter", "参数 'from_x', 'from_y', 'x', 'y' 都必须")

                # 移动到起点
                self._controller.position = (from_x, from_y)
                await asyncio.sleep(0.05)
                # 按下
                self._controller.press(button)
                await asyncio.sleep(0.05)
                # 移动到终点
                if duration_ms > 0:
                    await self._smooth_move(from_x, from_y, x, y, duration_ms)
                else:
                    self._controller.position = (x, y)
                await asyncio.sleep(0.05)
                # 松开
                self._controller.release(button)

            else:
                return SkillResult.error("invalid_action", f"未知动作类型: {action}")

            # 额外延迟
            if post_delay_ms > 0:
                await asyncio.sleep(post_delay_ms / 1000.0)

            # 获取当前位置
            current_pos = self._controller.position

            execution_time = (time.time() - start_time) * 1000
            return SkillResult.ok(
                {
                    "action": action,
                    "current_x": current_pos[0],
                    "current_y": current_pos[1],
                },
                execution_time_ms=execution_time,
            )

        except ImportError:
            return SkillResult.error("dependency_missing", "pynput 库未安装，请安装: pip install pynput")
        except ValueError as e:
            execution_time = (time.time() - start_time) * 1000
            return SkillResult.error("invalid_parameter", str(e), execution_time)
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return SkillResult.error("exception", str(e), execution_time)


# 注册到全局注册表
from agnes.skills.registry import registry

registry.register(MouseActionSkill())
