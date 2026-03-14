"""
图像归一化模块
"""

from typing import Optional

import cv2
import numpy as np

from .image_types import NormalizationResult


class ImageNormalizer:
    """图像归一化处理器"""

    def __init__(
        self,
        max_dimension: int = 1600,
        use_clahe: bool = True,
        blur_kernel_size: int = 3,
    ):
        self.max_dimension = max_dimension
        self.use_clahe = use_clahe
        self.blur_kernel_size = blur_kernel_size

    def normalize(self, image: np.ndarray) -> NormalizationResult:
        """执行图像归一化处理"""
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

    def _ensure_rgb_uint8(self, image: np.ndarray) -> np.ndarray:
        """确保输入图像为 RGB uint8"""
        if image.dtype != np.uint8:
            image = self._convert_to_uint8(image)

        if image.ndim == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

        if image.ndim == 3 and image.shape[2] == 3:
            return image.copy()

        if image.ndim == 3 and image.shape[2] == 4:
            return cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)

        raise ValueError("不支持的图像格式")

    def _convert_to_uint8(self, image: np.ndarray) -> np.ndarray:
        """将图像转换为 uint8"""
        clipped = np.clip(image, 0, None)

        if clipped.size == 0:
            raise ValueError("输入图像不能为空")

        max_value = float(np.max(clipped))
        if max_value <= 1.0:
            clipped = clipped * 255.0
        elif max_value > 255.0:
            clipped = clipped / max_value * 255.0

        return clipped.astype(np.uint8)

    def _resize_if_needed(self, image: np.ndarray) -> tuple[np.ndarray, float]:
        """在超过尺寸限制时缩放图像"""
        height, width = image.shape[:2]
        longest_edge = max(height, width)

        if longest_edge <= self.max_dimension:
            return image.copy(), 1.0

        scale = self.max_dimension / float(longest_edge)
        new_width = max(1, int(round(width * scale)))
        new_height = max(1, int(round(height * scale)))
        resized = cv2.resize(
            image,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA,
        )
        return resized, scale

    def _enhance_grayscale(self, grayscale: np.ndarray) -> np.ndarray:
        """增强灰度图像"""
        result = grayscale.copy()

        if self.use_clahe:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            result = clahe.apply(result)

        kernel_size = self._normalized_kernel_size(self.blur_kernel_size)
        if kernel_size > 1:
            result = cv2.GaussianBlur(result, (kernel_size, kernel_size), 0)

        return result

    def _normalized_kernel_size(self, kernel_size: Optional[int]) -> int:
        """规范化高斯模糊核大小"""
        if kernel_size is None or kernel_size <= 1:
            return 1
        if kernel_size % 2 == 0:
            return kernel_size + 1
        return kernel_size