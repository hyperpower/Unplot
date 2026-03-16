"""
图像归一化模块
"""

from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..pipeline import PipelineContext, StepRegistry
from .base import ImageProcessStep
from .image_types import NormalizationResult


@StepRegistry.register
class ImageNormalizer(ImageProcessStep):
    """图像归一化处理器。"""

    def __init__(
        self,
        max_dimension: int = 1600,
        use_clahe: bool = True,
        blur_kernel_size: int = 3,
        *,
        name: str | None = None,
        enabled: bool = True,
        config: dict | None = None,
    ):
        defaults = {
            "input_key": "image",
            "output_key": "image",
            "result_key": "normalization_result",
            "max_dimension": max_dimension,
            "use_clahe": use_clahe,
            "blur_kernel_size": blur_kernel_size,
        }
        merged_config = {**defaults, **(config or {})}
        super().__init__(name=name, enabled=enabled, config=merged_config)
        self.max_dimension = int(merged_config["max_dimension"])
        self.use_clahe = bool(merged_config["use_clahe"])
        self.blur_kernel_size = int(merged_config["blur_kernel_size"])

    def normalize(self, image: np.ndarray) -> NormalizationResult:
        if image is None or image.size == 0:
            raise ValueError("输入图像不能为空")

        rgb_image = self._ensure_rgb_uint8(image)
        resized_image, scale_factor = self._resize_if_needed(rgb_image)
        grayscale_image = cv2.cvtColor(resized_image, cv2.COLOR_RGB2GRAY)
        enhanced_image = self._enhance_grayscale(grayscale_image)

        return NormalizationResult(
            original_image=rgb_image,
            normalized_image=resized_image,
            grayscale_image=grayscale_image,
            enhanced_image=enhanced_image,
            scale_factor=scale_factor,
            metadata={
                "original_shape": tuple(rgb_image.shape),
                "normalized_shape": tuple(resized_image.shape),
                "dtype": str(resized_image.dtype),
                "use_clahe": self.use_clahe,
                "blur_kernel_size": self.blur_kernel_size,
            },
        )

    def _resize_if_needed(self, image: np.ndarray) -> tuple[np.ndarray, float]:
        height, width = image.shape[:2]
        longest_edge = max(height, width)
        if longest_edge <= self.max_dimension:
            return image.copy(), 1.0

        scale = self.max_dimension / float(longest_edge)
        new_width = max(1, int(round(width * scale)))
        new_height = max(1, int(round(height * scale)))
        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        return resized, scale

    def _enhance_grayscale(self, grayscale: np.ndarray) -> np.ndarray:
        result = grayscale.copy()
        if self.use_clahe:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            result = clahe.apply(result)

        kernel_size = self._normalized_kernel_size(self.blur_kernel_size)
        if kernel_size > 1:
            result = cv2.GaussianBlur(result, (kernel_size, kernel_size), 0)
        return result

    def _normalized_kernel_size(self, kernel_size: Optional[int]) -> int:
        if kernel_size is None or kernel_size <= 1:
            return 1
        if kernel_size % 2 == 0:
            return kernel_size + 1
        return kernel_size

    def run(self, context: PipelineContext) -> None:
        image = self._require_context_value(
            context,
            self._get_config_value("input_key", "image"),
        )
        result = self.normalize(image)
        self._set_context_value(context, self._get_config_value("result_key", "normalization_result"), result)
        self._set_context_value(context, self._get_config_value("output_key", "image"), result.normalized_image)
