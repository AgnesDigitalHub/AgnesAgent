"""
感知类 Skills - 获取游戏状态信息
"""
from agnes.skills.perception.screen_capture import ScreenCaptureSkill
from agnes.skills.perception.ocr_read import OcrReadSkill

__all__ = [
    "ScreenCaptureSkill",
    "OcrReadSkill",
]
