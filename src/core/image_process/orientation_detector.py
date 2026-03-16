"""
图像方向检测模块
"""

from __future__ import annotations

import math
from typing import List

import cv2
import numpy as np

from ..pipeline import PipelineContext, StepRegistry
from .base import ImageProcessStep
from .image_types import OrientationResult


@StepRegistry.register
class OrientationDetector(ImageProcessStep):
    """图像方向检测与校正器。"""

    def __init__(
        self,
        canny_threshold1: int = 50,
        canny_threshold2: int = 150,
        hough_threshold: int = 80,
        min_line_length: int = 80,
        max_line_gap: int = 10,
        *,
        name: str | None = None,
        enabled: bool = True,
        config: dict | None = None,
    ):
        defaults = {
            "input_key": "image",
            "output_key": "image",
            "result_key": "orientation_result",
            "canny_threshold1": canny_threshold1,
            "canny_threshold2": canny_threshold2,
            "hough_threshold": hough_threshold,
            "min_line_length": min_line_length,
            "max_line_gap": max_line_gap,
        }
        merged_config = {**defaults, **(config or {})}
        super().__init__(name=name, enabled=enabled, config=merged_config)
        self.canny_threshold1 = int(merged_config["canny_threshold1"])
        self.canny_threshold2 = int(merged_config["canny_threshold2"])
        self.hough_threshold = int(merged_config["hough_threshold"])
        self.min_line_length = int(merged_config["min_line_length"])
        self.max_line_gap = int(merged_config["max_line_gap"])

    def detect_and_correct(self, image: np.ndarray) -> OrientationResult:
        if image is None or image.size == 0:
            raise ValueError("输入图像不能为空")

        rgb_image = self._ensure_rgb(image)
        gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, self.canny_threshold1, self.canny_threshold2)
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=self.hough_threshold,
            minLineLength=self.min_line_length,
            maxLineGap=self.max_line_gap,
        )

        angles = self._extract_angles(lines)
        if not angles:
            return OrientationResult(
                image=rgb_image,
                angle=0.0,
                success=False,
                confidence=0.0,
                method="hough_lines",
                metadata={"reason": "未检测到足够的有效直线"},
            )

        dominant_angle = self._estimate_dominant_angle(angles)
        corrected = self._rotate_image(rgb_image, -dominant_angle)
        confidence = min(1.0, len(angles) / 20.0)
        return OrientationResult(
            image=corrected,
            angle=dominant_angle,
            success=True,
            confidence=confidence,
            method="hough_lines",
            metadata={"line_count": len(angles), "raw_angles": angles},
        )

    def _extract_angles(self, lines: np.ndarray | None) -> List[float]:
        if lines is None:
            return []
        angles: List[float] = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            dx = x2 - x1
            dy = y2 - y1
            if dx == 0 and dy == 0:
                continue
            angle = math.degrees(math.atan2(dy, dx))
            normalized_angle = self._normalize_angle(angle)
            if abs(normalized_angle) <= 45:
                angles.append(normalized_angle)
        return angles

    def _normalize_angle(self, angle: float) -> float:
        while angle >= 90:
            angle -= 180
        while angle < -90:
            angle += 180
        return angle

    def _estimate_dominant_angle(self, angles: List[float]) -> float:
        median_angle = float(np.median(np.array(angles, dtype=np.float32)))
        if abs(median_angle) < 0.5:
            return 0.0
        if abs(abs(median_angle) - 90.0) < 5.0:
            return 90.0 if median_angle > 0 else -90.0
        return median_angle

    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        if abs(angle) < 1e-6:
            return image.copy()
        height, width = image.shape[:2]
        center = (width / 2.0, height / 2.0)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        cos_value = abs(matrix[0, 0])
        sin_value = abs(matrix[0, 1])
        new_width = int((height * sin_value) + (width * cos_value))
        new_height = int((height * cos_value) + (width * sin_value))
        matrix[0, 2] += (new_width / 2) - center[0]
        matrix[1, 2] += (new_height / 2) - center[1]
        return cv2.warpAffine(
            image,
            matrix,
            (new_width, new_height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )

    def run(self, context: PipelineContext) -> None:
        image = self._require_context_value(context, self._get_config_value("input_key", "image"))
        result = self.detect_and_correct(image)
        self._set_context_value(context, self._get_config_value("result_key", "orientation_result"), result)
        self._set_context_value(context, self._get_config_value("output_key", "image"), result.image)
