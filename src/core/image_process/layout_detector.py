"""
图像版面检测模块
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import cv2
import numpy as np

from ..pipeline import PipelineContext, StepRegistry
from .base import ImageProcessStep
from .image_types import LayoutDetectionResult, LayoutRegion


@StepRegistry.register
class LayoutDetector(ImageProcessStep):
    """图像版面检测器。"""

    def __init__(
        self,
        min_region_area_ratio: float = 0.02,
        binary_block_size: int = 31,
        binary_c: int = 15,
        *,
        name: str | None = None,
        enabled: bool = True,
        config: dict | None = None,
    ):
        defaults = {
            "input_key": "image",
            "result_key": "layout_result",
            "debug_image_key": "layout_debug_image",
            "min_region_area_ratio": min_region_area_ratio,
            "binary_block_size": binary_block_size,
            "binary_c": binary_c,
        }
        merged_config = {**defaults, **(config or {})}
        super().__init__(name=name, enabled=enabled, config=merged_config)
        self.min_region_area_ratio = float(merged_config["min_region_area_ratio"])
        self.binary_block_size = int(merged_config["binary_block_size"])
        self.binary_c = int(merged_config["binary_c"])

    def detect(self, image: np.ndarray) -> LayoutDetectionResult:
        if image is None or image.size == 0:
            raise ValueError("输入图像不能为空")

        rgb_image = self._ensure_rgb(image)
        gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            self._normalized_block_size(self.binary_block_size),
            self.binary_c,
        )
        kernel = np.ones((5, 5), np.uint8)
        merged = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(merged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        image_height, image_width = rgb_image.shape[:2]
        image_area = float(image_height * image_width)
        min_region_area = image_area * self.min_region_area_ratio

        candidates: List[Tuple[float, LayoutRegion]] = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = float(w * h)
            if area < min_region_area:
                continue
            fill_ratio = self._compute_fill_ratio(binary, (x, y, w, h))
            confidence = min(1.0, area / image_area + fill_ratio * 0.3)
            candidates.append(
                (
                    area,
                    LayoutRegion(
                        label="chart_candidate",
                        bbox=(x, y, w, h),
                        confidence=confidence,
                        metadata={"fill_ratio": fill_ratio},
                    ),
                )
            )

        candidates.sort(key=lambda item: item[0], reverse=True)
        regions: List[LayoutRegion] = []
        chart_region = candidates[0][1] if candidates else None
        if chart_region is not None:
            chart_region.label = "chart"
            regions.append(chart_region)
            plot_region = self._estimate_plot_region(chart_region)
            if plot_region is not None:
                regions.append(plot_region)
            legend_region = self._estimate_legend_region(chart_region, rgb_image.shape[:2])
            if legend_region is not None:
                regions.append(legend_region)

        debug_image = self._draw_regions(rgb_image, regions)
        success = len(regions) > 0
        confidence = max((region.confidence for region in regions), default=0.0)
        return LayoutDetectionResult(
            image=rgb_image,
            regions=regions,
            success=success,
            confidence=confidence,
            debug_image=debug_image,
            metadata={"candidate_count": len(candidates), "image_shape": tuple(rgb_image.shape)},
        )

    def _normalized_block_size(self, value: int) -> int:
        if value < 3:
            return 3
        if value % 2 == 0:
            return value + 1
        return value

    def _compute_fill_ratio(self, binary: np.ndarray, bbox: Tuple[int, int, int, int]) -> float:
        x, y, w, h = bbox
        region = binary[y : y + h, x : x + w]
        if region.size == 0:
            return 0.0
        return float(np.count_nonzero(region)) / float(region.size)

    def _estimate_plot_region(self, chart_region: LayoutRegion) -> Optional[LayoutRegion]:
        x, y, w, h = chart_region.bbox
        if w < 20 or h < 20:
            return None
        margin_left = int(w * 0.12)
        margin_right = int(w * 0.08)
        margin_top = int(h * 0.08)
        margin_bottom = int(h * 0.15)
        return LayoutRegion(
            label="plot",
            bbox=(
                x + margin_left,
                y + margin_top,
                max(1, w - margin_left - margin_right),
                max(1, h - margin_top - margin_bottom),
            ),
            confidence=max(0.0, chart_region.confidence - 0.1),
            metadata={"source": "heuristic_from_chart"},
        )

    def _estimate_legend_region(
        self,
        chart_region: LayoutRegion,
        image_shape: Tuple[int, int],
    ) -> Optional[LayoutRegion]:
        x, y, w, h = chart_region.bbox
        image_height, image_width = image_shape
        legend_w = int(w * 0.22)
        legend_h = int(h * 0.28)
        if legend_w < 20 or legend_h < 20:
            return None
        legend_x = min(image_width - legend_w, x + w - legend_w - int(w * 0.03))
        legend_y = min(image_height - legend_h, y + int(h * 0.05))
        if legend_x < 0 or legend_y < 0:
            return None
        return LayoutRegion(
            label="legend_candidate",
            bbox=(legend_x, legend_y, legend_w, legend_h),
            confidence=max(0.0, chart_region.confidence - 0.25),
            metadata={"source": "heuristic_from_chart"},
        )

    def _draw_regions(self, image: np.ndarray, regions: List[LayoutRegion]) -> np.ndarray:
        debug_image = image.copy()
        colors = {"chart": (255, 0, 0), "plot": (0, 255, 0), "legend_candidate": (0, 0, 255)}
        for region in regions:
            x, y, w, h = region.bbox
            color = colors.get(region.label, (255, 255, 0))
            cv2.rectangle(debug_image, (x, y), (x + w, y + h), color, 2)
            cv2.putText(debug_image, region.label, (x, max(0, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
        return debug_image

    def run(self, context: PipelineContext) -> None:
        image = self._require_context_value(context, self._get_config_value("input_key", "image"))
        result = self.detect(image)
        self._set_context_value(context, self._get_config_value("result_key", "layout_result"), result)
        self._set_context_value(context, self._get_config_value("debug_image_key", "layout_debug_image"), result.debug_image)
