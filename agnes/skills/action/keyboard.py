"""
keyboard_action - 键盘输入控制
支持按键按下、松开、单次点击、组合键
"""
import time
import asyncio
from typing import Any, Dict, List, Optional
from agnes.skills.base import BaseSkill, SkillSchema, SkillResult, SkillMetadata


class KeyboardActionSkill(BaseSkill):
    """键盘输入控制，模拟按键按下、松开、点击和组合键"""

    name = "keyboard_action"
    description = "模拟键盘输入，支持按键按下、松开、单次点击和组合键。"

    metadata = SkillMetadata(
        version="1.0.0",
        category="action",
        permission_level="restricted",
        cost=0.0,
        tags=["keyboard", "input", "control"]
    )

    def __init__(self):
        self._controller = None
        self._initialized = False

    def _lazy_init(self):
        """延迟初始化 pynput"""
        if self._initialized:
            return
        from pynput import keyboard
        self._controller = keyboard.Controller()
        self._keyboard = keyboard
        self._initialized = True

    def get_schema(self) -> SkillSchema:
        return SkillSchema(
            name=self.name,
            description=self.description,
            parameters={
                "action": {
                    "type": "string",
                    "enum": ["press", "release", "tap", "combo", "sequence"],
                    "description": (
                        "动作类型:\n"
                        "- press: 按下按键不放\n"
                        "- release: 松开按键\n"
                        "- tap: 点击一次（按下后立即松开）\n"
                        "- combo: 组合键（同时按下多个）\n"
                        "- sequence: 顺序按键"
                    )
                },
                "key": {
                    "type": "string",
                    "description": "按键名称，适用于 press/release/tap。例如: a, enter, space, tab, backspace, escape, f1-f12, left, right, up, down, shift, ctrl, alt"
                },
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "按键列表，适用于 combo/sequence"
                },
                "delay_ms": {
                    "type": "integer",
                    "description": "按键之间延迟毫秒，适用于 combo/sequence，默认 50",
                    "default": 50
                },
                "post_delay_ms": {
                    "type": "integer",
                    "description": "动作完成后额外延迟毫秒，默认 0",
                    "default": 0
                }
            },
            required=["action"],
            returns={
                "success": "boolean - 是否成功",
                "action": "string - 执行的动作"
            }
        )

    def _parse_key(self, key_name: str):
        """解析按键名称到 pynput Key"""
        key_name = key_name.lower().strip()

        # 特殊键
        special_keys = {
            # 控制键
            "ctrl": self._keyboard.Key.ctrl,
            "control": self._keyboard.Key.ctrl,
            "shift": self._keyboard.Key.shift,
            "alt": self._keyboard.Key.alt,
            "cmd": self._keyboard.Key.cmd,
            "win": self._keyboard.Key.cmd,
            "windows": self._keyboard.Key.cmd,
            "menu": self._keyboard.Key.menu,

            # 导航
            "esc": self._keyboard.Key.esc,
            "escape": self._keyboard.Key.esc,
            "tab": self._keyboard.Key.tab,
            "enter": self._keyboard.Key.enter,
            "return": self._keyboard.Key.enter,
            "backspace": self._keyboard.Key.backspace,
            "delete": self._keyboard.Key.delete,
            "space": self._keyboard.Key.space,
            "spacebar": self._keyboard.Key.space,

            # 方向键
            "up": self._keyboard.Key.up,
            "down": self._keyboard.Key.down,
            "left": self._keyboard.Key.left,
            "right": self._keyboard.Key.right,

            # 功能键
            "f1": self._keyboard.Key.f1,
            "f2": self._keyboard.Key.f2,
            "f3": self._keyboard.Key.f3,
            "f4": self._keyboard.Key.f4,
            "f5": self._keyboard.Key.f5,
            "f6": self._keyboard.Key.f6,
            "f7": self._keyboard.Key.f7,
            "f8": self._keyboard.Key.f8,
            "f9": self._keyboard.Key.f9,
            "f10": self._keyboard.Key.f10,
            "f11": self._keyboard.Key.f11,
            "f12": self._keyboard.Key.f12,

            # 编辑
            "home": self._keyboard.Key.home,
            "end": self._keyboard.Key.end,
            "page_up": self._keyboard.Key.page_up,
            "pagedown": self._keyboard.Key.page_down,
            "page_down": self._keyboard.Key.page_down,
            "insert": self._keyboard.Key.insert,
        }

        if key_name in special_keys:
            return special_keys[key_name]

        # 普通字符
        if len(key_name) == 1:
            return self._keyboard.KeyCode.from_char(key_name)

        # 数字
        if key_name.isdigit():
            return self._keyboard.KeyCode.from_char(key_name)

        # 未知
        raise ValueError(f"Unknown key name: {key_name}")

    async def execute(self, parameters: Dict[str, Any]) -> SkillResult:
        start_time = time.time()

        try:
            self._lazy_init()

            action = parameters.get("action", "").lower()
            key = parameters.get("key")
            keys = parameters.get("keys", [])
            delay_ms = parameters.get("delay_ms", 50)
            post_delay_ms = parameters.get("post_delay_ms", 0)

            if action in ["press", "release", "tap"]:
                if not key:
                    return SkillResult.error("missing_parameter", "参数 'key' 是必须的")

                parsed_key = self._parse_key(key)

                if action == "press":
                    self._controller.press(parsed_key)
                elif action == "release":
                    self._controller.release(parsed_key)
                elif action == "tap":
                    self._controller.press(parsed_key)
                    await asyncio.sleep(0.01)
                    self._controller.release(parsed_key)

            elif action == "combo":
                # 组合键：依次按下，然后反向松开
                if not keys or not isinstance(keys, list) or len(keys) == 0:
                    return SkillResult.error("missing_parameter", "参数 'keys' 必须是非空列表")

                parsed_keys = [self._parse_key(k) for k in keys]
                # 依次按下
                for k in parsed_keys:
                    self._controller.press(k)
                    await asyncio.sleep(delay_ms / 1000.0)
                # 反向松开
                for k in reversed(parsed_keys):
                    self._controller.release(k)
                    await asyncio.sleep(delay_ms / 1000.0)

            elif action == "sequence":
                # 顺序按键
                if not keys or not isinstance(keys, list) or len(keys) == 0:
                    return SkillResult.error("missing_parameter", "参数 'keys' 必须是非空列表")

                for k in keys:
                    parsed = self._parse_key(k)
                    self._controller.press(parsed)
                    await asyncio.sleep(0.01)
                    self._controller.release(parsed)
                    await asyncio.sleep(delay_ms / 1000.0)

            else:
                return SkillResult.error("invalid_action", f"未知动作类型: {action}")

            # 额外延迟
            if post_delay_ms > 0:
                await asyncio.sleep(post_delay_ms / 1000.0)

            execution_time = (time.time() - start_time) * 1000
            return SkillResult.ok({
                "action": action,
            }, execution_time_ms=execution_time)

        except ImportError:
            return SkillResult.error(
                "dependency_missing",
                "pynput 库未安装，请安装: pip install pynput"
            )
        except ValueError as e:
            execution_time = (time.time() - start_time) * 1000
            return SkillResult.error("invalid_key", str(e), execution_time)
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return SkillResult.error("exception", str(e), execution_time)


# 注册到全局注册表
from agnes.skills.registry import registry
registry.register(KeyboardActionSkill())