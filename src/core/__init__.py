"""
核心功能模块
"""

from .image_loader import ImageLoader
from .image_writer import ImageWriter
from .image_types import (
    DewarpResult,
    ImageTransformResult,
    LayoutDetectionResult,
    LayoutRegion,
    NormalizationResult,
    OrientationResult,
    PerspectiveCorrectionResult,
    ROIExtractionResult,
)
from .image_normalizer import ImageNormalizer
from .orientation_detector import OrientationDetector
from .perspective_corrector import PerspectiveCorrector
from .layout_detector import LayoutDetector
from .roi_extractor import ROIExtractor
from .page_dewarper import PageDewarper

# 兼容旧模块导出，后续可逐步移除
from .data_extractor import DataExtractor
from .coordinate_mapper import CoordinateMapper
from .point_detector import PointDetector

__all__ = [
    "ImageLoader",
    "ImageWriter",
    "NormalizationResult",
    "ImageTransformResult",
    "OrientationResult",
    "PerspectiveCorrectionResult",
    "LayoutRegion",
    "LayoutDetectionResult",
    "ROIExtractionResult",
    "DewarpResult",
    "ImageNormalizer",
    "OrientationDetector",
    "PerspectiveCorrector",
    "LayoutDetector",
    "ROIExtractor",
    "PageDewarper",
    "DataExtractor",
    "CoordinateMapper",
    "PointDetector",
]