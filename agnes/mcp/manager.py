"""
MCP Manager - Enhanced MCP Server Management
Provides:
- Status monitoring & health checks
- Security sandbox & permission control
- Token usage tracking & cost monitoring
- Environment & secret management
"""

import json
import logging
import os
import shutil
import subprocess
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any, Optional

from cryptography.fernet import Fernet
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class HealthStatus(StrEnum):
    """MCP 服务器健康状态"""

    UNKNOWN = "unknown"
    RUNNING = "running"
    STOPPED = "stopped"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class ToolCallRecord:
    """工具调用记录 - 用于日志和监控"""

    server_id: str
    tool_name: str
    arguments: dict[str, Any]
    start_time: float
    end_time: float
    duration_ms: float
    input_tokens: int
    output_tokens: int
    success: bool
    error: str | None = None
    required_confirmation: bool = False
    confirmed: bool = False

    def to_dict(self):
        return {
            "server_id": self.server_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "success": self.success,
            "error": self.error,
            "required_confirmation": self.required_confirmation,
            "confirmed": self.confirmed,
            "timestamp": datetime.fromtimestamp(self.start_time).isoformat(),
        }


@dataclass
class MCPStats:
    """MCP 统计信息"""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_duration_ms: float = 0.0
    last_call_time: datetime | None = None

    def record_call(self, record: ToolCallRecord):
        """记录一次调用"""
        self.total_calls += 1
        self.total_input_tokens += record.input_tokens
        self.total_output_tokens += record.output_tokens
        self.total_duration_ms += record.duration_ms
        self.last_call_time = datetime.fromtimestamp(record.start_time)
        if record.success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1

    def to_dict(self):
        return asdict(self)


class MCPSecurityConfig(BaseModel):
    """安全配置"""

    readonly: bool = False
    """只读模式"""

    confirm_on_dangerous: bool = True
    """高危操作需要人工确认"""

    allowed_paths: list[str] = []
    """允许访问的文件路径白名单"""

    allowed_domains: list[str] = []
    """允许访问的域名白名单"""

    blocked_operations: list[str] = [
        "delete",
        "remove",
        "rm",
        "drop",
        "truncate",
        "write",
        "create",
        "mkdir",
        "rmdir",
        "unlink",
    ]
    """只读模式下拦截的操作关键词"""


class DangerousOperationDetector:
    """高危操作检测器"""

    # 常见高危操作关键词
    DANGEROUS_KEYWORDS = {
        # 文件系统
        "delete",
        "remove",
        "rm",
        "unlink",
        "rmdir",
        "drop",
        "truncate",
        "overwrite",
        "format",
        # 网络
        "post",
        "put",
        "delete",
        "patch",
        # 数据库
        "drop",
        "create",
        "alter",
        "delete",
        "update",
        # 系统
        "exec",
        "system",
        "shell",
        "command",
        "kill",
        "shutdown",
    }

    @classmethod
    def is_dangerous(cls, tool_name: str, arguments: dict[str, Any]) -> bool:
        """检测是否为高危操作"""
        # 检查工具名称
        tool_lower = tool_name.lower()
        for keyword in cls.DANGEROUS_KEYWORDS:
            if keyword in tool_lower:
                return True

        # 检查参数值
        def check_dict(d: dict):
            for key, value in d.items():
                key_lower = key.lower()
                for keyword in cls.DANGEROUS_KEYWORDS:
                    if keyword in key_lower:
                        return True
                if isinstance(value, str):
                    value_lower = value.lower()
                    for keyword in cls.DANGEROUS_KEYWORDS:
                        if keyword in value_lower:
                            return True
                elif isinstance(value, dict):
                    if check_dict(value):
                        return True
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            if check_dict(item):
                                return True
            return False

        return check_dict(arguments)


class PathValidator:
    """路径验证器 - 实现作用域限制"""

    @staticmethod
    def normalize_path(path: str) -> Path:
        """规范化路径"""
        return Path(path).expanduser().resolve()

    @classmethod
    def is_path_allowed(cls, path: str, allowed_paths: list[str]) -> bool:
        """检查路径是否在允许列表内"""
        if not allowed_paths:
            return True  # 没有限制则允许所有路径

        target = cls.normalize_path(path)

        for allowed in allowed_paths:
            allowed_path = cls.normalize_path(allowed)
            # 检查目标路径是否是允许路径的子目录
            try:
                if target == allowed_path or allowed_path in target.parents:
                    return True
            except Exception:
                continue

        return False

    @classmethod
    def check_write_operation(
        cls,
        path: str,
        allowed_paths: list[str],
        readonly: bool,
    ) -> tuple[bool, str]:
        """
        检查写操作是否允许
        返回 (是否允许, 错误信息)
        """
        if readonly:
            return False, "此服务器已设置为只读模式，不允许写操作"

        if not cls.is_path_allowed(path, allowed_paths):
            return False, f"路径 {path} 不在允许访问范围内，当前配置只允许访问: {allowed_paths}"

        return True, ""


class EncryptedSecretManager:
    """加密密钥管理器"""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._key = self._load_or_create_key()
        self._fernet = Fernet(self._key)
        self._secrets: dict[str, dict[str, str]] = self._load_secrets()

    def _load_or_create_key(self) -> bytes:
        """加载或新建加密密钥"""
        key_file = self.storage_path.parent / "secret.key"
        if key_file.exists():
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            # 设置权限
            try:
                key_file.chmod(0o600)
            except Exception:
                pass
            return key

    def _load_secrets(self) -> dict[str, dict[str, str]]:
        """加载加密的密钥"""
        if not self.storage_path.exists():
            return {}
        try:
            with open(self.storage_path, "rb") as f:
                encrypted_data = f.read()
            if not encrypted_data:
                return {}
            decrypted = self._fernet.decrypt(encrypted_data)
            return json.loads(decrypted.decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to load encrypted secrets: {e}")
            return {}

    def _save_secrets(self):
        """保存加密的密钥"""
        try:
            data = json.dumps(self._secrets).encode("utf-8")
            encrypted = self._fernet.encrypt(data)
            with open(self.storage_path, "wb") as f:
                f.write(encrypted)
            # 设置权限
            try:
                self.storage_path.chmod(0o600)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Failed to save encrypted secrets: {e}")
            raise

    def get_secrets(self, environment: str = "default") -> dict[str, str]:
        """获取指定环境的所有密钥"""
        return self._secrets.get(environment, {})

    def set_secret(self, key: str, value: str, environment: str = "default"):
        """设置密钥"""
        if environment not in self._secrets:
            self._secrets[environment] = {}
        self._secrets[environment][key] = value
        self._save_secrets()

    def delete_secret(self, key: str, environment: str = "default") -> bool:
        """删除密钥"""
        if environment not in self._secrets:
            return False
        if key not in self._secrets[environment]:
            return False
        del self._secrets[environment][key]
        self._save_secrets()
        return True

    def list_keys(self, environment: str = "default") -> list[str]:
        """列出所有密钥名称"""
        return list(self._secrets.get(environment, {}).keys())

    def inject_to_env(self, env: dict[str, str], environment: str = "default") -> dict[str, str]:
        """将密钥注入到环境变量字典"""
        result = env.copy()
        secrets = self.get_secrets(environment)
        for key, value in secrets.items():
            result[key] = value
        return result


class DependencyInstaller:
    """依赖安装器 - 自动检测和安装缺失依赖"""

    @staticmethod
    def check_command_exists(cmd: str) -> bool:
        """检查命令是否存在"""
        return shutil.which(cmd) is not None

    @staticmethod
    def get_install_command(dependency: str) -> str | None:
        """获取依赖的安装命令"""
        install_commands = {
            "node": {
                "darwin": "brew install node",
                "linux": "curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs",
                "ubuntu": "curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs",
                "debian": "curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs",
            },
            "npm": None,  # npm comes with node
            "npx": None,  # npx comes with npm
            "uv": "curl -LsSf https://astral.sh/uv/install.sh | sh",
            "uvx": None,  # uvx comes with uv
            "python": None,  # python should already be here
        }

        import platform

        system = platform.system().lower()

        if dependency not in install_commands:
            return None

        cmd = install_commands[dependency]
        if isinstance(cmd, dict):
            # 按系统选择
            if system in cmd:
                return cmd[system]
            elif "linux" in cmd and system == "linux":
                return cmd["linux"]
            else:
                return None
        return cmd

    @classmethod
    def install_dependency(cls, dependency: str) -> tuple[bool, str]:
        """安装依赖"""
        # 先检查是否已经存在
        if cls.check_command_exists(dependency):
            return True, f"{dependency} 已经安装"

        install_cmd = cls.get_install_command(dependency)
        if not install_cmd:
            return False, f"未找到 {dependency} 的自动安装方式，请手动安装"

        try:
            logger.info(f"Installing {dependency} with command: {install_cmd}")
            result = subprocess.run(
                install_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
            )

            if result.returncode == 0:
                return True, f"{dependency} 安装成功\n{result.stdout}"
            else:
                return False, f"{dependency} 安装失败: {result.stderr}"

        except Exception as e:
            return False, f"安装 {dependency} 发生异常: {str(e)}"

    @classmethod
    def check_missing_dependencies(cls, required_deps: list[str]) -> list[str]:
        """检查缺失的依赖"""
        missing = []
        for dep in required_deps:
            if not cls.check_command_exists(dep):
                missing.append(dep)
        return missing


class MCPEnhancedManager:
    """增强的MCP管理器，集成所有高级功能"""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 工具调用日志
        self.call_logs: list[ToolCallRecord] = []
        self.log_file = storage_dir / "call_logs.json"
        self._load_call_logs()

        # 统计信息
        self.stats: dict[str, MCPStats] = {}

        # 待确认的操作
        self.pending_confirmations: dict[str, dict[str, Any]] = {}

        # 加密密钥管理
        self.secret_manager = EncryptedSecretManager(storage_dir / "secrets.enc")

    def _load_call_logs(self):
        """加载调用日志"""
        if self.log_file.exists():
            try:
                with open(self.log_file, encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    record = ToolCallRecord(
                        server_id=item["server_id"],
                        tool_name=item["tool_name"],
                        arguments=item["arguments"],
                        start_time=item["start_time"],
                        end_time=item["end_time"],
                        duration_ms=item["duration_ms"],
                        input_tokens=item["input_tokens"],
                        output_tokens=item["output_tokens"],
                        success=item["success"],
                        error=item.get("error"),
                        required_confirmation=item.get("required_confirmation", False),
                        confirmed=item.get("confirmed", False),
                    )
                    self.call_logs.append(record)
                    # 更新统计
                    if record.server_id not in self.stats:
                        self.stats[record.server_id] = MCPStats()
                    self.stats[record.server_id].record_call(record)
            except Exception as e:
                logger.error(f"Failed to load call logs: {e}")

    def _save_call_logs(self):
        """保存调用日志"""
        try:
            # 只保留最近1000条，避免文件过大
            logs_to_save = self.call_logs[-1000:]
            data = [log.to_dict() for log in logs_to_save]
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save call logs: {e}")

    def estimate_tool_tokens(self, tool_info: dict[str, Any]) -> int:
        """预估工具调用会增加的token消耗
        基于工具名称、描述、参数schema粗略估算
        """
        # 基础估算：每个工具大约消耗
        base = 50  # 基础 overhead
        name_len = len(tool_info.get("name", ""))
        desc_len = len(tool_info.get("description", ""))

        # 参数schema估算
        input_schema = tool_info.get("input_schema", {})
        properties = input_schema.get("properties", {})
        schema_size = sum(len(str(p)) for p in properties.values())

        total = base + (name_len // 2) + (desc_len // 3) + (schema_size // 4)
        return max(total, 50)  # 至少50token

    def estimate_server_tokens(self, tools: list[dict[str, Any]]) -> int:
        """预估整个服务器的token消耗"""
        return sum(self.estimate_tool_tokens(tool) for tool in tools)

    def begin_tool_call(
        self,
        server_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        security_config: MCPSecurityConfig,
    ) -> tuple[bool, str, str | None]:
        """
        开始工具调用前的安全检查
        返回:
        - 是否允许继续
        - 消息
        - 如果需要确认，返回confirmation_id
        """
        # 检查是否高危操作
        if security_config.confirm_on_dangerous and DangerousOperationDetector.is_dangerous(tool_name, arguments):
            # 需要人工确认
            import uuid

            confirmation_id = f"{server_id}_{tool_name}_{uuid.uuid4().hex[:8]}"
            self.pending_confirmations[confirmation_id] = {
                "server_id": server_id,
                "tool_name": tool_name,
                "arguments": arguments,
                "security_config": security_config.dict(),
                "created_at": time.time(),
            }
            return False, "此操作被标记为高危操作，需要您的确认后才能执行", confirmation_id

        # 检查文件路径是否合法（如果参数中包含路径）
        # 尝试在参数中查找路径
        def find_and_check_paths(d: dict) -> tuple[bool, str]:
            for key, value in d.items():
                key_lower = key.lower()
                if (
                    "path" in key_lower or "file" in key_lower or "directory" in key_lower or "dir" in key_lower
                ) and isinstance(value, str):
                    # 可能是路径，检查一下
                    allowed, msg = PathValidator.check_write_operation(
                        value,
                        security_config.allowed_paths,
                        security_config.readonly,
                    )
                    if not allowed:
                        return False, msg
                elif isinstance(value, dict):
                    ok, msg = find_and_check_paths(value)
                    if not ok:
                        return False, msg
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            ok, msg = find_and_check_paths(item)
                            if not ok:
                                return False, msg
            return True, ""

        ok, msg = find_and_check_paths(arguments)
        if not ok:
            return False, msg, None

        # 所有检查通过
        return True, "", None

    def confirm_pending_operation(self, confirmation_id: str) -> dict[str, Any] | None:
        """确认待执行的操作，返回操作信息供执行"""
        if confirmation_id not in self.pending_confirmations:
            return None
        operation = self.pending_confirmations.pop(confirmation_id)
        return operation

    def finish_tool_call(
        self,
        server_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        start_time: float,
        success: bool,
        input_tokens: int = 0,
        output_tokens: int = 0,
        error: str | None = None,
        required_confirmation: bool = False,
        confirmed: bool = False,
    ) -> ToolCallRecord:
        """完成工具调用，记录日志"""
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        # 如果没有提供token估算，使用估算值
        if input_tokens == 0:
            # 粗略估算参数的token数量
            input_tokens = len(str(arguments)) // 4

        record = ToolCallRecord(
            server_id=server_id,
            tool_name=tool_name,
            arguments=arguments,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            success=success,
            error=error,
            required_confirmation=required_confirmation,
            confirmed=confirmed,
        )

        self.call_logs.append(record)
        if server_id not in self.stats:
            self.stats[server_id] = MCPStats()
        self.stats[server_id].record_call(record)
        self._save_call_logs()

        return record

    def get_call_logs(
        self,
        server_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """获取调用日志"""
        if server_id:
            logs = [log for log in self.call_logs if log.server_id == server_id]
        else:
            logs = self.call_logs
        # 返回最新的N条
        return [log.to_dict() for log in logs[-limit:]]

    def get_stats(self, server_id: str | None = None) -> dict[str, Any]:
        """获取统计信息"""
        if server_id:
            if server_id in self.stats:
                return {server_id: self.stats[server_id].to_dict()}
            else:
                return {server_id: MCPStats().to_dict()}
        else:
            return {sid: stats.to_dict() for sid, stats in self.stats.items()}

    def check_health(self, server_id: str, connected: bool, last_error: str | None) -> HealthStatus:
        """根据连接信息判断健康状态"""
        if connected:
            return HealthStatus.RUNNING
        if last_error is None:
            return HealthStatus.STOPPED
        if "timeout" in last_error.lower() or "timed out" in last_error.lower():
            return HealthStatus.TIMEOUT
        if last_error:
            return HealthStatus.ERROR
        return HealthStatus.UNKNOWN

    def get_call_stats(self) -> dict[str, Any]:
        """获取全局调用统计概览（用于日志页面）"""
        total_calls = sum(stats.total_calls for stats in self.stats.values())
        successful = sum(stats.successful_calls for stats in self.stats.values())
        if total_calls == 0:
            success_rate = 0
        else:
            success_rate = round((successful / total_calls) * 100, 1)
        avg_duration = (
            round(sum(stats.total_duration_ms for stats in self.stats.values()) / total_calls, 1)
            if total_calls > 0
            else 0
        )
        total_tokens = sum(stats.total_input_tokens + stats.total_output_tokens for stats in self.stats.values())

        return {
            "stats": {
                "total_calls": total_calls,
                "success_rate": success_rate,
                "avg_duration": avg_duration,
                "total_tokens": total_tokens,
            }
        }

    def delete_call_log(self, log_id: str) -> bool:
        """删除单条日志"""
        # log_id 是基于 timestamp + index 生成，我们需要找到匹配的日志
        # 简化实现：遍历查找匹配 timestamp 前缀
        for i, log in enumerate(self.call_logs):
            if str(int(log.start_time)) in log_id:
                del self.call_logs[i]
                self._save_call_logs()
                return True
        return False

    def clear_call_logs(self):
        """清空所有日志"""
        self.call_logs.clear()
        self.stats.clear()
        self._save_call_logs()


# 全局单例
_root_dir = Path(__file__).parent.parent.parent / "config" / "mcp"
enhanced_manager = MCPEnhancedManager(_root_dir / "management")
