"""
图像处理公共数据类型
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


BBox = Tuple[int, int, int, int]
PointList = List[Tuple[float, float]]


@dataclass
class NormalizationResult:
    """图像归一化结果"""

    original_image: np.ndarray
    normalized_image: np.ndarray
    grayscale_image: np.ndarray
    enhanced_image: np.ndarray
    scale_factor: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrientationResult:
    """方向检测与校正结果"""

    image: np.ndarray
    angle: float
    success: bool
    confidence: float = 0.0
    method: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerspectiveCorrectionResult:
    """透视校正结果"""

    image: np.ndarray
    success: bool
    corners: Optional[PointList] = None
    transform_matrix: Optional[np.ndarray] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LayoutRegion:
    """版面区域"""

    label: str
    bbox: BBox
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LayoutDetectionResult:
    """版面检测结果"""

    image: np.ndarray
    regions: List[LayoutRegion]
    success: bool
    confidence: float = 0.0
    debug_image: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ROIExtractionResult:
    """ROI 提取结果"""

    source_image: np.ndarray
    plot_roi: Optional[np.ndarray] = None
    x_axis_roi: Optional[np.ndarray] = None
    y_axis_roi: Optional[np.ndarray] = None
    legend_roi: Optional[np.ndarray] = None
    plot_bbox: Optional[BBox] = None
    x_axis_bbox: Optional[BBox] = None
    y_axis_bbox: Optional[BBox] = None
    legend_bbox: Optional[BBox] = None
    success: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DewarpResult:
    """页面去弯曲结果"""

    image: np.ndarray
    success: bool
    confidence: float = 0.0
    method: str = "identity"
    metadata: Dict[str, Any] = field(default_factory=dict)
