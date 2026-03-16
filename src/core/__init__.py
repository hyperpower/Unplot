"""
核心功能模块
"""

from .image_process import (
    ImageLoader,
    ImageNormalizer,
    ImageProcessStep,
    ImageWriter,
    LayoutDetector,
    OrientationDetector,
    PageDewarper,
    PerspectiveCorrector,
    ROIExtractor,
)
from .image_process.image_types import (
    DewarpResult,
    LayoutDetectionResult,
    LayoutRegion,
    NormalizationResult,
    OrientationResult,
    PerspectiveCorrectionResult,
    ROIExtractionResult,
)
from .pipeline import (
    Pipeline,
    PipelineContext,
    PipelineExecutionRecord,
    PipelineResult,
    PipelineStep,
    StepRegistry,
)

# 兼容旧模块导出，后续可逐步移除
from .data_extractor import DataExtractor
from .coordinate_mapper import CoordinateMapper
from .point_detector import PointDetector

__all__ = [
    "ImageLoader",
    "ImageWriter",
    "ImageProcessStep",
    "NormalizationResult",
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
    "Pipeline",
    "PipelineContext",
    "PipelineExecutionRecord",
    "PipelineResult",
    "PipelineStep",
    "StepRegistry",
    "DataExtractor",
    "CoordinateMapper",
    "PointDetector",
]
