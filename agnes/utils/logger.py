import logging
import sys


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        if levelname in self.COLORS:
            color = self.COLORS[levelname]
            reset = self.COLORS["RESET"]
            record.levelname = f"{color}{levelname}{reset}"
            record.msg = f"{color}{record.msg}{reset}"

        return super().format(record)


def get_logger(
    name: str = "agnes",
    level: int = logging.INFO,
    log_file: str | None = None,
    colored: bool = True,
) -> logging.Logger:
    """
    获取配置好的 logger

    Args:
        name: Logger 名称
        level: 日志级别
        log_file: 日志文件路径 (可选)
        colored: 是否使用彩色输出

    Returns:
        配置好的 logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if colored and sys.platform != "win32":
        formatter = ColoredFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
