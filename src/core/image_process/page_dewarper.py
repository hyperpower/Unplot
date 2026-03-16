"""
页面去弯曲模块
"""

from __future__ import annotations

import cv2
import numpy as np

from ..pipeline import PipelineContext, StepRegistry
from .base import ImageProcessStep
from .image_types import DewarpResult


@StepRegistry.register
class PageDewarper(ImageProcessStep):
    """页面去弯曲处理器。"""

    def __init__(
        self,
        blur_kernel_size: int = 5,
        projection_smooth_ratio: float = 0.02,
        curvature_threshold: float = 0.15,
        *,
        name: str | None = None,
        enabled: bool = True,
        config: dict | None = None,
    ):
        defaults = {
            "input_key": "image",
            "output_key": "image",
            "result_key": "dewarp_result",
            "blur_kernel_size": blur_kernel_size,
            "projection_smooth_ratio": projection_smooth_ratio,
            "curvature_threshold": curvature_threshold,
        }
        merged_config = {**defaults, **(config or {})}
        super().__init__(name=name, enabled=enabled, config=merged_config)
        self.blur_kernel_size = int(merged_config["blur_kernel_size"])
        self.projection_smooth_ratio = float(merged_config["projection_smooth_ratio"])
        self.curvature_threshold = float(merged_config["curvature_threshold"])

    def dewarp(self, image: np.ndarray) -> DewarpResult:
        if image is None or image.size == 0:
            raise ValueError("输入图像不能为空")
        rgb_image = self._ensure_rgb(image)
        gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)

        kernel_size = self._normalized_kernel_size(self.blur_kernel_size)
        if kernel_size > 1:
            gray = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)

        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 15)
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
        return DewarpResult(
            image=corrected,
            success=True,
            confidence=min(0.85, 0.4 + curvature_score),
            method="lightweight_projection_flatten",
            metadata={
                "curvature_score": float(curvature_score),
                "horizontal_curvature": float(horizontal_curvature),
                "vertical_curvature": float(vertical_curvature),
                "note": "当前为轻量去弯曲实现，后续可替换为更强的非线性模型",
            },
        )

    def _normalized_kernel_size(self, kernel_size: int) -> int:
        if kernel_size <= 1:
            return 1
        if kernel_size % 2 == 0:
            return kernel_size + 1
        return kernel_size

    def _estimate_profile_curvature(self, profile: np.ndarray) -> float:
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
        return float(np.mean(np.abs(second_derivative))) / amplitude

    def _lightweight_flatten(self, image: np.ndarray) -> np.ndarray:
        return cv2.bilateralFilter(image, d=7, sigmaColor=40, sigmaSpace=40)

    def run(self, context: PipelineContext) -> None:
        image = self._require_context_value(context, self._get_config_value("input_key", "image"))
        result = self.dewarp(image)
        self._set_context_value(context, self._get_config_value("result_key", "dewarp_result"), result)
        self._set_context_value(context, self._get_config_value("output_key", "image"), result.image)
