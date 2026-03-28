"""
ocr_read - 识别图像中的文字
支持从截图或区域进行 OCR 识别
"""

import base64
import io
import time
from typing import Any

from PIL import Image

from agnes.skills.base import BaseSkill, SkillMetadata, SkillResult, SkillSchema


class OcrReadSkill(BaseSkill):
    """对图像区域进行 OCR 文字识别"""

    name = "ocr_read"
    description = "识别图像中的文字内容，可用于读取游戏界面的文字、对话框内容等。"

    metadata = SkillMetadata(
        version="1.0.0",
        category="perception",
        permission_level="safe",
        cost=0.02,
        tags=["ocr", "text", "recognition", "vision"],
    )

    def __init__(self):
        self._reader = None
        self._initialized = False

    def _lazy_init(self):
        """延迟初始化 easyocr"""
        if self._initialized:
            return
        import easyocr

        # 默认加载中英文模型，可根据需要配置
        self._reader = easyocr.Reader(["ch_sim", "en"])
        self._initialized = True

    def get_schema(self) -> SkillSchema:
        return SkillSchema(
            name=self.name,
            description=self.description,
            parameters={
                "image_base64": {"type": "string", "description": "Base64 编码的 PNG/JPG 图像数据"},
                "region": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "裁剪区域 [left, top, width, height]，可选",
                },
                "detail": {
                    "type": "integer",
                    "description": "返回结果细节级别，0=仅纯文本，1=带框坐标，默认 0",
                    "default": 0,
                },
                "paragraph": {"type": "boolean", "description": "是否将文本合并为段落，默认 True", "default": True},
            },
            required=["image_base64"],
            returns={"text": "string - 识别出的纯文本", "boxes": "array - 如果 detail=1，返回每个文字框的信息"},
        )

    async def execute(self, parameters: dict[str, Any]) -> SkillResult:
        start_time = time.time()

        try:
            self._lazy_init()

            image_b64 = parameters.get("image_base64", "")
            region = parameters.get("region")  # [left, top, width, height]
            detail = parameters.get("detail", 0)
            paragraph = parameters.get("paragraph", True)

            # 解码 base64
            try:
                image_data = base64.b64decode(image_b64)
            except Exception as e:
                return SkillResult.error("invalid_base64", f"Base64 解码失败: {e}")

            # 打开图像
            img = Image.open(io.BytesIO(image_data))

            # 如果指定了区域，裁剪
            if region and len(region) == 4:
                left, top, width, height = region
                img = img.crop((left, top, left + width, top + height))

            # OCR 识别
            result = self._reader.readtext(img, detail=1, paragraph=paragraph)

            execution_time = (time.time() - start_time) * 1000

            if detail == 0:
                # 只返回纯文本
                full_text = "\n".join([text for _, text, _ in result])
                return SkillResult.ok({"text": full_text, "boxes": None}, execution_time_ms=execution_time)
            else:
                # 返回带坐标的详细信息
                boxes = []
                full_text = []
                for bbox, text, conf in result:
                    boxes.append(
                        {"bbox": [bbox[0][0], bbox[0][1], bbox[2][0], bbox[2][1]], "text": text, "confidence": conf}
                    )
                    full_text.append(text)
                return SkillResult.ok({"text": "\n".join(full_text), "boxes": boxes}, execution_time_ms=execution_time)

        except ImportError:
            return SkillResult.error(
                "dependency_missing",
                "easyocr 库未安装，请安装: pip install easyocr\n首次运行会自动下载模型文件，请耐心等待",
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return SkillResult.error("exception", str(e), execution_time)


# 注册到全局注册表
from agnes.skills.registry import registry

registry.register(OcrReadSkill())
