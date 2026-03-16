"""
ROI 提取模块
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from ..pipeline import PipelineContext, StepRegistry
from .base import ImageProcessStep
from .image_types import LayoutDetectionResult, LayoutRegion, ROIExtractionResult


@StepRegistry.register
class ROIExtractor(ImageProcessStep):
    """图像 ROI 提取器。"""

    def __init__(
        self,
        *,
        name: str | None = None,
        enabled: bool = True,
        config: dict | None = None,
    ):
        defaults = {
            "input_key": "image",
            "layout_key": "layout_result",
            "result_key": "roi_result",
            "plot_key": "plot_roi",
            "x_axis_key": "x_axis_roi",
            "y_axis_key": "y_axis_roi",
            "legend_key": "legend_roi",
        }
        merged_config = {**defaults, **(config or {})}
        super().__init__(name=name, enabled=enabled, config=merged_config)

    def extract(
        self,
        image: np.ndarray,
        layout_result: LayoutDetectionResult,
    ) -> ROIExtractionResult:
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
        x_axis_bbox = self._estimate_x_axis_bbox(plot_bbox, rgb_image.shape[:2])
        y_axis_bbox = self._estimate_y_axis_bbox(plot_bbox, rgb_image.shape[:2])
        legend_bbox = None
        legend_roi = None
        if legend_region is not None:
            legend_bbox = self._clip_bbox(legend_region.bbox, rgb_image.shape[:2])
            legend_roi = self._crop(rgb_image, legend_bbox)

        return ROIExtractionResult(
            source_image=rgb_image,
            plot_roi=self._crop(rgb_image, plot_bbox),
            x_axis_roi=self._crop(rgb_image, x_axis_bbox),
            y_axis_roi=self._crop(rgb_image, y_axis_bbox),
            legend_roi=legend_roi,
            plot_bbox=plot_bbox,
            x_axis_bbox=x_axis_bbox,
            y_axis_bbox=y_axis_bbox,
            legend_bbox=legend_bbox,
            success=True,
            metadata={"base_region_label": base_region.label, "layout_success": layout_result.success},
        )

    def _find_region(self, layout_result: LayoutDetectionResult, label: str) -> Optional[LayoutRegion]:
        for region in layout_result.regions:
            if region.label == label:
                return region
        return None

    def _clip_bbox(self, bbox: Tuple[int, int, int, int], image_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
        x, y, w, h = bbox
        image_height, image_width = image_shape
        x = max(0, min(x, image_width - 1))
        y = max(0, min(y, image_height - 1))
        w = max(1, min(w, image_width - x))
        h = max(1, min(h, image_height - y))
        return (x, y, w, h)

    def _crop(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        x, y, w, h = bbox
        return image[y : y + h, x : x + w].copy()

    def _estimate_x_axis_bbox(self, plot_bbox: Tuple[int, int, int, int], image_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
        x, y, w, h = plot_bbox
        return self._clip_bbox((x, y + h, w, max(12, int(h * 0.18))), image_shape)

    def _estimate_y_axis_bbox(self, plot_bbox: Tuple[int, int, int, int], image_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
        x, y, w, h = plot_bbox
        axis_width = max(12, int(w * 0.18))
        return self._clip_bbox((x - axis_width, y, axis_width, h), image_shape)

    def run(self, context: PipelineContext) -> None:
        image = self._require_context_value(context, self._get_config_value("input_key", "image"))
        layout_result = self._require_context_value(context, self._get_config_value("layout_key", "layout_result"))
        result = self.extract(image, layout_result)
        self._set_context_value(context, self._get_config_value("result_key", "roi_result"), result)
        self._set_context_value(context, self._get_config_value("plot_key", "plot_roi"), result.plot_roi)
        self._set_context_value(context, self._get_config_value("x_axis_key", "x_axis_roi"), result.x_axis_roi)
        self._set_context_value(context, self._get_config_value("y_axis_key", "y_axis_roi"), result.y_axis_roi)
        self._set_context_value(context, self._get_config_value("legend_key", "legend_roi"), result.legend_roi)
