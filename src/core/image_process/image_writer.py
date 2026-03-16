"""
图像保存模块
"""

from __future__ import annotations

import os
from typing import Optional

import cv2
import numpy as np

from ..pipeline import PipelineContext, StepRegistry
from .base import ImageProcessStep


@StepRegistry.register
class ImageWriter(ImageProcessStep):
    """图像保存器类。"""

    SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"]

    def __init__(
        self,
        *,
        name: str | None = None,
        enabled: bool = True,
        config: dict | None = None,
    ):
        defaults = {
            "input_key": "image",
            "path": None,
            "path_key": "output_path",
            "quality": 95,
            "output_key": "save_success",
        }
        merged_config = {**defaults, **(config or {})}
        super().__init__(name=name, enabled=enabled, config=merged_config)

    def save(
        self,
        image: np.ndarray,
        path: str,
        quality: Optional[int] = 95,
    ) -> bool:
        """保存图像到指定路径。"""
        try:
            if image is None or image.size == 0:
                raise ValueError("输入图像不能为空")

            ext = os.path.splitext(path)[1].lower()
            if ext not in self.SUPPORTED_FORMATS:
                raise ValueError(f"不支持的图像格式：{ext}")

            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

            image_to_save = self._prepare_image_for_save(image)
            params = self._get_save_params(ext, quality)
            success = cv2.imwrite(path, image_to_save, params)
            if not success:
                raise ValueError("图像写入失败")
            return True
        except Exception as exc:
            print(f"保存图像失败：{exc}")
            return False

    def _prepare_image_for_save(self, image: np.ndarray) -> np.ndarray:
        if image.dtype != np.uint8:
            image = self._convert_to_uint8(image)

        if image.ndim == 2:
            return image
        if image.ndim == 3 and image.shape[2] == 3:
            return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        if image.ndim == 3 and image.shape[2] == 4:
            return cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA)
        raise ValueError("不支持的图像格式")

    def _get_save_params(self, ext: str, quality: Optional[int]) -> list[int]:
        if ext in [".jpg", ".jpeg"]:
            jpeg_quality = 95 if quality is None else max(0, min(100, int(quality)))
            return [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
        if ext == ".png":
            return [cv2.IMWRITE_PNG_COMPRESSION, 3]
        return []

    def run(self, context: PipelineContext) -> None:
        """从上下文读取图像并保存。"""
        image = self._require_context_value(
            context,
            self._get_config_value("input_key", "image"),
        )
        path = self._get_config_value("path")
        if path is None:
            path = context.get(self._get_config_value("path_key", "output_path"))
        if not path:
            raise ValueError("缺少输出路径，无法执行保存步骤")

        quality = self._get_config_value("quality", 95)
        success = self.save(image, str(path), quality)
        if not success:
            raise ValueError(f"图像保存失败: {path}")

        self._set_context_value(
            context,
            self._get_config_value("output_key", "save_success"),
            success,
        )
