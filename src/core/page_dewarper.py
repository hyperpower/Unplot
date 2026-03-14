"""
页面去弯曲模块
"""

import cv2
import numpy as np

from .image_types import DewarpResult

class PageDewarper:
    """页面去弯曲处理器

    第一版提供轻量实现：
    - 对输入做基础平滑
    - 使用形态学与投影估计页面是否存在明显弯曲
    - 当前默认不做复杂非线性矫正，而是保留原图结构并返回分析信息
    """

    def __init__(
        self,
        blur_kernel_size: int = 5,
        projection_smooth_ratio: float = 0.02,
        curvature_threshold: float = 0.15,
    ):
        self.blur_kernel_size = blur_kernel_size
        self.projection_smooth_ratio = projection_smooth_ratio
        self.curvature_threshold = curvature_threshold

    def dewarp(self, image: np.ndarray) -> DewarpResult:
        """执行页面去弯曲分析与轻量处理"""
        if image is None or image.size == 0:
            raise ValueError("输入图像不能为空")

        rgb_image = self._ensure_rgb(image)
        gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)

        kernel_size = self._normalized_kernel_size(self.blur_kernel_size)
        if kernel_size > 1:
            gray = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)

        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            31,
            15,
        )

        horizontal_profile = np.sum(binary > 0, axis=1).astype(np.float32)
        vertical_profile = np.sum(binary > 0, axis=0).astype(np.float32)

        horizontal_curvature = self._estimate_profile_curvature(horizontal_profile)
        vertical_curvature = self._estimate_profile_curvature(vertical_profile)
        curvature_score = max(horizontal_curvature, vertical_curvature)

        if curvature_score < self.curvature_threshold:
            return DewarpResult(
                image=rgb_image.copy(),
                success=True,
                confidence=max(0.2, 1.0 - curvature_score),
                method="identity",
                metadata={
                    "curvature_score": float(curvature_score),
                    "horizontal_curvature": float(horizontal_curvature),
                    "vertical_curvature": float(vertical_curvature),
                    "note": "未检测到明显页面弯曲，返回原图",
                },
            )

        corrected = self._lightweight_flatten(rgb_image)
        confidence = min(0.85, 0.4 + curvature_score)

        return DewarpResult(
            image=corrected,
            success=True,
            confidence=confidence,
            method="lightweight_projection_flatten",
            metadata={
                "curvature_score": float(curvature_score),
                "horizontal_curvature": float(horizontal_curvature),
                "vertical_curvature": float(vertical_curvature),
                "note": "当前为轻量去弯曲实现，后续可替换为更强的非线性模型",
            },
        )

    def _ensure_rgb(self, image: np.ndarray) -> np.ndarray:
        """确保输入图像为 RGB"""
        if image.ndim == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        if image.ndim == 3 and image.shape[2] == 3:
            return image.copy()
        if image.ndim == 3 and image.shape[2] == 4:
            return cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        raise ValueError("不支持的图像格式")

    def _normalized_kernel_size(self, kernel_size: int) -> int:
        """规范化核大小"""
        if kernel_size <= 1:
            return 1
        if kernel_size % 2 == 0:
            return kernel_size + 1
        return kernel_size

    def _estimate_profile_curvature(self, profile: np.ndarray) -> float:
        """根据投影曲线估计弯曲程度"""
        if profile.size < 5:
            return 0.0

        smooth_window = max(3, int(round(profile.size * self.projection_smooth_ratio)))
        if smooth_window % 2 == 0:
            smooth_window += 1

        kernel = np.ones(smooth_window, dtype=np.float32) / float(smooth_window)
        smoothed = np.convolve(profile, kernel, mode="same")

        second_derivative = np.diff(smoothed, n=2)
        if second_derivative.size == 0:
            return 0.0

        amplitude = float(np.max(smoothed) - np.min(smoothed))
        if amplitude <= 1e-6:
            return 0.0

        curvature = float(np.mean(np.abs(second_derivative))) / amplitude
        return curvature

    def _lightweight_flatten(self, image: np.ndarray) -> np.ndarray:
        """执行轻量平整化处理

        当前版本不做真正的非线性展平，只做轻量增强与边界平滑，
        为后续更强算法预留统一接口。
        """
        filtered = cv2.bilateralFilter(image, d=7, sigmaColor=40, sigmaSpace=40)
        return filtered