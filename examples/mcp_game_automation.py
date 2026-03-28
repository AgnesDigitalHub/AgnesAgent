#!/usr/bin/env python
"""
示例: 使用 MCP 暴露游戏自动化 Skills

用法:
  uv run python examples/mcp_game_automation.py        - 启动 MCP STDIO 服务
  uv run python examples/mcp_game_automation.py --help - 显示帮助信息
"""

import asyncio
import logging
import sys

from agnes.mcp.server import create_default_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(__doc__)
        print("\n可用工具:")
        print("  screen_capture   - 截取屏幕截图")
        print("  ocr_read         - 识别图片中的文字")
        print("  keyboard_action  - 执行键盘操作")
        print("  mouse_action     - 执行鼠标操作")
        return

    logger.info("Starting Agnes Game Automation MCP Server...")
    logger.info("Available Skills: screen_capture, ocr_read, keyboard_action, mouse_action")
    server = create_default_server()
    await server.run_stdio()


if __name__ == "__main__":
    asyncio.run(main())
