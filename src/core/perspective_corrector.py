"""
图像透视校正模块
"""

from typing import List, Optional, Tuple

import cv2
import numpy as np

from .image_types import PerspectiveCorrectionResult

class PerspectiveCorrector:
    """图像透视校正器"""

    def __init__(
        self,
        canny_threshold1: int = 50,
        canny_threshold2: int = 150,
        min_area_ratio: float = 0.1,
        epsilon_ratio: float = 0.02,
    ):
        self.canny_threshold1 = canny_threshold1
        self.canny_threshold2 = canny_threshold2
        self.min_area_ratio = min_area_ratio
        self.epsilon_ratio = epsilon_ratio

    def correct(self, image: np.ndarray) -> PerspectiveCorrectionResult:
        """执行透视校正"""
        if image is None or image.size == 0:
            raise ValueError("输入图像不能为空")

        rgb_image = self._ensure_rgb(image)
        gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, self.canny_threshold1, self.canny_threshold2)

        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

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

    def _ensure_rgb(self, image: np.ndarray) -> np.ndarray:
        """确保输入图像为 RGB"""
        if image.ndim == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        if image.ndim == 3 and image.shape[2] == 3:
            return image.copy()
        if image.ndim == 3 and image.shape[2] == 4:
            return cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        raise ValueError("不支持的图像格式")

    def _find_document_corners(
        self,
        contours: List[np.ndarray],
        image_shape: Tuple[int, int],
    ) -> Optional[np.ndarray]:
        """从轮廓中寻找最可能的文档四边形"""
        image_height, image_width = image_shape
        min_area = image_height * image_width * self.min_area_ratio

        candidates: List[Tuple[float, np.ndarray]] = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(
                contour,
                self.epsilon_ratio * perimeter,
                True,
            )

            if len(approx) == 4:
                candidates.append((area, approx.reshape(4, 2)))

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1].astype(np.float32)

    def _order_points(self, points: np.ndarray) -> np.ndarray:
        """按左上、右上、右下、左下排序四个点"""
        rect = np.zeros((4, 2), dtype=np.float32)

        sums = points.sum(axis=1)
        rect[0] = points[np.argmin(sums)]
        rect[2] = points[np.argmax(sums)]

        diffs = np.diff(points, axis=1)
        rect[1] = points[np.argmin(diffs)]
        rect[3] = points[np.argmax(diffs)]

        return rect

    def _warp_perspective(
        self,
        image: np.ndarray,
        corners: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """执行透视变换"""
        top_left, top_right, bottom_right, bottom_left = corners

        width_top = np.linalg.norm(top_right - top_left)
        width_bottom = np.linalg.norm(bottom_right - bottom_left)
        max_width = max(int(round(width_top)), int(round(width_bottom)), 1)

        height_right = np.linalg.norm(bottom_right - top_right)
        height_left = np.linalg.norm(bottom_left - top_left)
        max_height = max(int(round(height_right)), int(round(height_left)), 1)

        destination = np.array(
            [
                [0, 0],
                [max_width - 1, 0],
                [max_width - 1, max_height - 1],
                [0, max_height - 1],
            ],
            dtype=np.float32,
        )

        matrix = cv2.getPerspectiveTransform(corners, destination)
        warped = cv2.warpPerspective(image, matrix, (max_width, max_height))
        return warped, matrix