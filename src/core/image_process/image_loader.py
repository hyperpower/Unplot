"""
图像加载模块
"""

from __future__ import annotations

import os
from typing import Optional, Tuple

import cv2
import numpy as np

from ..pipeline import PipelineContext, StepRegistry
from .base import ImageProcessStep


@StepRegistry.register
class ImageLoader(ImageProcessStep):
    """图像加载器类。"""

    SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif"]

    def __init__(
        self,
        *,
        name: str | None = None,
        enabled: bool = True,
        config: dict | None = None,
    ):
        defaults = {
            "path": None,
            "path_key": "image_path",
            "output_image_key": "image",
            "output_path_key": "loaded_image_path",
        }
        merged_config = {**defaults, **(config or {})}
        super().__init__(name=name, enabled=enabled, config=merged_config)
        self._image: Optional[np.ndarray] = None
        self._image_path: Optional[str] = None

    @property
    def image(self) -> Optional[np.ndarray]:
        return self._image

    @property
    def image_path(self) -> Optional[str]:
        return self._image_path

    @property
    def image_size(self) -> Optional[Tuple[int, int]]:
        if self._image is not None:
            return (self._image.shape[1], self._image.shape[0])
        return None

    def load(self, path: str) -> bool:
        """加载图像文件。"""
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext not in self.SUPPORTED_FORMATS:
                raise ValueError(f"不支持的图像格式：{ext}")

            image = cv2.imread(path, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("无法读取图像文件")

            self._image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self._image_path = path
            return True
        except Exception as exc:
            print(f"加载图像失败：{exc}")
            self._image = None
            self._image_path = None
            return False

    def unload(self) -> None:
        """卸载当前图像。"""
        self._image = None
        self._image_path = None

    def get_pixel(self, x: int, y: int) -> Optional[Tuple[int, int, int]]:
        """获取指定位置的像素值。"""
        if self._image is None:
            return None

        h, w = self._image.shape[:2]
        if 0 <= x < w and 0 <= y < h:
            return tuple(self._image[y, x].tolist())
        return None

    def run(self, context: PipelineContext) -> None:
        """从上下文或配置读取路径并加载图像。"""
        path = self._get_config_value("path")
        if path is None:
            path = context.get(self._get_config_value("path_key", "image_path"))
        if not path:
            raise ValueError("缺少图像路径，无法执行加载步骤")

        if not self.load(str(path)):
            raise ValueError(f"图像加载失败: {path}")

        self._set_context_value(
            context,
            self._get_config_value("output_image_key", "image"),
            self._image,
        )
        self._set_context_value(
            context,
            self._get_config_value("output_path_key", "loaded_image_path"),
            self._image_path,
        )
