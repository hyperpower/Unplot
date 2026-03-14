"""
ROI 提取模块
"""

from typing import Optional, Tuple

import cv2
import numpy as np

from .image_types import LayoutDetectionResult, LayoutRegion, ROIExtractionResult

class ROIExtractor:
    """图像 ROI 提取器"""

    def extract(
        self,
        image: np.ndarray,
        layout_result: LayoutDetectionResult,
    ) -> ROIExtractionResult:
        """根据版面检测结果提取关键 ROI"""
        if image is None or image.size == 0:
            raise ValueError("输入图像不能为空")

        rgb_image = self._ensure_rgb(image)
        plot_region = self._find_region(layout_result, "plot")
        chart_region = self._find_region(layout_result, "chart")
        legend_region = self._find_region(layout_result, "legend_candidate")

        base_region = plot_region or chart_region
        if base_region is None:
            return ROIExtractionResult(
                source_image=rgb_image,
                success=False,
                metadata={"reason": "未找到 plot 或 chart 区域"},
            )

        plot_bbox = self._clip_bbox(base_region.bbox, rgb_image.shape[:2])
        plot_roi = self._crop(rgb_image, plot_bbox)

        x_axis_bbox = self._estimate_x_axis_bbox(plot_bbox, rgb_image.shape[:2])
        y_axis_bbox = self._estimate_y_axis_bbox(plot_bbox, rgb_image.shape[:2])
        legend_bbox = None
        legend_roi = None

        if legend_region is not None:
            legend_bbox = self._clip_bbox(legend_region.bbox, rgb_image.shape[:2])
            legend_roi = self._crop(rgb_image, legend_bbox)

        return ROIExtractionResult(
            source_image=rgb_image,
            plot_roi=plot_roi,
            x_axis_roi=self._crop(rgb_image, x_axis_bbox),
            y_axis_roi=self._crop(rgb_image, y_axis_bbox),
            legend_roi=legend_roi,
            plot_bbox=plot_bbox,
            x_axis_bbox=x_axis_bbox,
            y_axis_bbox=y_axis_bbox,
            legend_bbox=legend_bbox,
            success=True,
            metadata={
                "base_region_label": base_region.label,
                "layout_success": layout_result.success,
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

    def _find_region(
        self,
        layout_result: LayoutDetectionResult,
        label: str,
    ) -> Optional[LayoutRegion]:
        """按标签查找区域"""
        for region in layout_result.regions:
            if region.label == label:
                return region
        return None

    def _clip_bbox(
        self,
        bbox: Tuple[int, int, int, int],
        image_shape: Tuple[int, int],
    ) -> Tuple[int, int, int, int]:
        """将 bbox 限制在图像边界内"""
        x, y, w, h = bbox
        image_height, image_width = image_shape

        x = max(0, min(x, image_width - 1))
        y = max(0, min(y, image_height - 1))
        w = max(1, min(w, image_width - x))
        h = max(1, min(h, image_height - y))
        return (x, y, w, h)

    def _crop(
        self,
        image: np.ndarray,
        bbox: Tuple[int, int, int, int],
    ) -> np.ndarray:
        """裁剪图像区域"""
        x, y, w, h = bbox
        return image[y : y + h, x : x + w].copy()

    def _estimate_x_axis_bbox(
        self,
        plot_bbox: Tuple[int, int, int, int],
        image_shape: Tuple[int, int],
    ) -> Tuple[int, int, int, int]:
        """估计 X 轴区域"""
        x, y, w, h = plot_bbox
        axis_height = max(12, int(h * 0.18))
        bbox = (x, y + h, w, axis_height)
        return self._clip_bbox(bbox, image_shape)

    def _estimate_y_axis_bbox(
        self,
        plot_bbox: Tuple[int, int, int, int],
        image_shape: Tuple[int, int],
    ) -> Tuple[int, int, int, int]:
        """估计 Y 轴区域"""
        x, y, w, h = plot_bbox
        axis_width = max(12, int(w * 0.18))
        bbox = (x - axis_width, y, axis_width, h)
        return self._clip_bbox(bbox, image_shape)