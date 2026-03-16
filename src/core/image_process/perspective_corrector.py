"""
图像透视校正模块
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import cv2
import numpy as np

from ..pipeline import PipelineContext, StepRegistry
from .base import ImageProcessStep
from .image_types import PerspectiveCorrectionResult


@StepRegistry.register
class PerspectiveCorrector(ImageProcessStep):
    """图像透视校正器。"""

    def __init__(
        self,
        canny_threshold1: int = 50,
        canny_threshold2: int = 150,
        min_area_ratio: float = 0.1,
        epsilon_ratio: float = 0.02,
        *,
        name: str | None = None,
        enabled: bool = True,
        config: dict | None = None,
    ):
        defaults = {
            "input_key": "image",
            "output_key": "image",
            "result_key": "perspective_result",
            "canny_threshold1": canny_threshold1,
            "canny_threshold2": canny_threshold2,
            "min_area_ratio": min_area_ratio,
            "epsilon_ratio": epsilon_ratio,
        }
        merged_config = {**defaults, **(config or {})}
        super().__init__(name=name, enabled=enabled, config=merged_config)
        self.canny_threshold1 = int(merged_config["canny_threshold1"])
        self.canny_threshold2 = int(merged_config["canny_threshold2"])
        self.min_area_ratio = float(merged_config["min_area_ratio"])
        self.epsilon_ratio = float(merged_config["epsilon_ratio"])

    def correct(self, image: np.ndarray) -> PerspectiveCorrectionResult:
        if image is None or image.size == 0:
            raise ValueError("输入图像不能为空")

        rgb_image = self._ensure_rgb(image)
        gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, self.canny_threshold1, self.canny_threshold2)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        corners = self._find_document_corners(contours, rgb_image.shape[:2])
        if corners is None:
            return PerspectiveCorrectionResult(
                image=rgb_image,
                success=False,
                corners=None,
                transform_matrix=None,
                confidence=0.0,
                metadata={"reason": "未找到可用于透视校正的四边形区域"},
            )

        ordered_corners = self._order_points(corners)
        warped, matrix = self._warp_perspective(rgb_image, ordered_corners)
        contour_area = cv2.contourArea(ordered_corners.astype(np.float32))
        image_area = float(rgb_image.shape[0] * rgb_image.shape[1])
        confidence = min(1.0, contour_area / image_area)
        return PerspectiveCorrectionResult(
            image=warped,
            success=True,
            corners=[tuple(map(float, point)) for point in ordered_corners],
            transform_matrix=matrix,
            confidence=confidence,
            metadata={
                "source_shape": tuple(rgb_image.shape),
                "result_shape": tuple(warped.shape),
            },
        )

    def _find_document_corners(
        self,
        contours: List[np.ndarray],
        image_shape: Tuple[int, int],
    ) -> Optional[np.ndarray]:
        image_height, image_width = image_shape
        min_area = image_height * image_width * self.min_area_ratio
        candidates: List[Tuple[float, np.ndarray]] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, self.epsilon_ratio * perimeter, True)
            if len(approx) == 4:
                candidates.append((area, approx.reshape(4, 2)))
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1].astype(np.float32)

    def _order_points(self, points: np.ndarray) -> np.ndarray:
        rect = np.zeros((4, 2), dtype=np.float32)
        sums = points.sum(axis=1)
        rect[0] = points[np.argmin(sums)]
        rect[2] = points[np.argmax(sums)]
        diffs = np.diff(points, axis=1)
        rect[1] = points[np.argmin(diffs)]
        rect[3] = points[np.argmax(diffs)]
        return rect

    def _warp_perspective(self, image: np.ndarray, corners: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        top_left, top_right, bottom_right, bottom_left = corners
        width_top = np.linalg.norm(top_right - top_left)
        width_bottom = np.linalg.norm(bottom_right - bottom_left)
        max_width = max(int(round(width_top)), int(round(width_bottom)), 1)
        height_right = np.linalg.norm(bottom_right - top_right)
        height_left = np.linalg.norm(bottom_left - top_left)
        max_height = max(int(round(height_right)), int(round(height_left)), 1)
        destination = np.array(
            [[0, 0], [max_width - 1, 0], [max_width - 1, max_height - 1], [0, max_height - 1]],
            dtype=np.float32,
        )
        matrix = cv2.getPerspectiveTransform(corners, destination)
        warped = cv2.warpPerspective(image, matrix, (max_width, max_height))
        return warped, matrix

    def run(self, context: PipelineContext) -> None:
        image = self._require_context_value(context, self._get_config_value("input_key", "image"))
        result = self.correct(image)
        self._set_context_value(context, self._get_config_value("result_key", "perspective_result"), result)
        self._set_context_value(context, self._get_config_value("output_key", "image"), result.image)
