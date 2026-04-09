"""
empty_trash - 清空回收站/垃圾箱技能
支持跨平台：Windows、macOS、Linux
"""

import os
import subprocess
import sys
import time
from typing import Any

from agnes.skills.base import BaseSkill, SkillMetadata, SkillResult, SkillSchema


class EmptyTrashSkill(BaseSkill):
    """清空系统回收站/垃圾箱，释放磁盘空间"""

    name = "empty_trash"
    description = "清空系统回收站（垃圾箱），释放磁盘空间。支持 Windows、macOS 和 Linux。"

    metadata = SkillMetadata(
        version="1.0.0",
        category="system",
        permission_level="restricted",
        cost=0.0,
        tags=["system", "maintenance", "cleanup", "disk", "trash"],
    )

    def get_schema(self) -> SkillSchema:
        return SkillSchema(
            name=self.name,
            description=self.description,
            parameters={
                "confirm": {
                    "type": "boolean",
                    "description": "确认清空回收站，此操作不可撤销。默认 false",
                    "default": False,
                }
            },
            required=[],
            returns={
                "success": "boolean - 是否成功清空",
                "platform": "string - 当前操作系统",
                "message": "string - 结果信息",
            },
        )

    def _detect_platform(self) -> str:
        """检测操作系统"""
        platform = sys.platform
        if platform == "win32":
            return "windows"
        elif platform == "darwin":
            return "macos"
        elif platform.startswith("linux"):
            return "linux"
        else:
            return "unknown"

    async def _empty_windows(self) -> tuple[bool, str]:
        """清空Windows回收站"""
        try:
            # 使用PowerShell命令清空回收站
            cmd = [
                "powershell",
                "-Command",
                "$shell = New-Object -ComObject Shell.Application; $namespace = $shell.Namespace(0x0a); $items = $namespace.Items(); foreach($item in $items) { $item.InvokeVerb('delete') }; Start-Sleep -Seconds 1",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                return True, "Windows 回收站已清空"
            else:
                return False, f"清空失败: {result.stderr}"
        except Exception as e:
            return False, str(e)

    async def _empty_macos(self) -> tuple[bool, str]:
        """清空macOS垃圾箱"""
        try:
            # AppleScript清空垃圾箱
            cmd = [
                "osascript",
                "-e",
                'tell application "Finder" to empty trash',
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                return True, "macOS 垃圾箱已清空"
            else:
                return False, f"清空失败: {result.stderr}"
        except Exception as e:
            return False, str(e)

    async def _empty_linux(self) -> tuple[bool, str]:
        """清空Linux回收站（不同桌面环境可能位置不同）"""
        # 常见回收站位置
        trash_locations = [
            os.path.expanduser("~/.local/share/Trash"),
            os.path.expanduser("~/.Trash"),
            os.path.expanduser("~/.trash"),
        ]

        found = False
        deleted_files = 0
        deleted_size = 0

        for trash_dir in trash_locations:
            if os.path.exists(trash_dir):
                found = True
                try:
                    # 统计文件数量和大小（简化版，实际删除通过命令）
                    if os.path.exists(os.path.join(trash_dir, "files")):
                        # FreeDesktop标准
                        import shutil

                        shutil.rmtree(os.path.join(trash_dir, "files"))
                        shutil.rmtree(os.path.join(trash_dir, "info"))
                        os.makedirs(os.path.join(trash_dir, "files"))
                        os.makedirs(os.path.join(trash_dir, "info"))
                        return True, "Linux 回收站已清空（FreeDesktop标准）"
                    else:
                        # 直接删除整个目录内容
                        for item in os.listdir(trash_dir):
                            item_path = os.path.join(trash_dir, item)
                            try:
                                if os.path.isdir(item_path):
                                    import shutil

                                    shutil.rmtree(item_path)
                                else:
                                    os.remove(item_path)
                                deleted_files += 1
                            except Exception:
                                pass
                except Exception as e:
                    continue

        if found and deleted_files >= 0:
            return True, f"Linux 回收站已清空，删除了 {deleted_files} 个文件"
        elif found:
            return False, "找到回收站但清空失败"
        else:
            return True, "未找到回收站，可能已经为空或使用不同的回收站位置"

    async def execute(self, parameters: dict[str, Any]) -> SkillResult:
        start_time = time.time()

        try:
            confirm = parameters.get("confirm", False)

            if not confirm:
                return SkillResult.error(
                    "confirmation_required",
                    "需要确认才能清空回收站，请设置参数 'confirm': true。此操作不可撤销。",
                    (time.time() - start_time) * 1000,
                )

            platform = self._detect_platform()

            if platform == "windows":
                success, message = await self._empty_windows()
            elif platform == "macos":
                success, message = await self._empty_macos()
            elif platform == "linux":
                success, message = await self._empty_linux()
            else:
                return SkillResult.error(
                    "unsupported_platform",
                    f"不支持的操作系统: {platform}",
                    (time.time() - start_time) * 1000,
                )

            execution_time = (time.time() - start_time) * 1000
            if success:
                return SkillResult.ok(
                    {"success": True, "platform": platform, "message": message},
                    execution_time_ms=execution_time,
                )
            else:
                return SkillResult.error("execution_failed", message, execution_time)

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return SkillResult.error("exception", str(e), execution_time)


# 注册到全局注册表
from agnes.skills.registry import registry

registry.register(EmptyTrashSkill())
