"""
core 图像处理模块测试
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.image_process import (
    ImageLoader,
    ImageNormalizer,
    ImageWriter,
    LayoutDetector,
    LayoutDetectionResult,
    LayoutRegion,
    OrientationDetector,
    PageDewarper,
    PerspectiveCorrector,
    ROIExtractor,
)


def create_test_image(width: int = 320, height: int = 240) -> np.ndarray:
    """创建一张简单的测试图像"""
    image = np.full((height, width, 3), 255, dtype=np.uint8)

    # 模拟图表主体
    image[30:210, 40:280] = 245

    # 模拟绘图区边框
    image[60:180, 80:240] = 255
    image[60:180, 80:82] = 0
    image[60:180, 238:240] = 0
    image[60:62, 80:240] = 0
    image[178:180, 80:240] = 0

    # 模拟图例区域
    image[50:95, 250:300] = 235
    image[60:65, 260:280] = [255, 0, 0]
    image[72:77, 260:280] = [0, 255, 0]

    return image


class TestImageFixturesDirectory:
    """测试图片目录约定"""

    def test_images_directory_exists(self):
        """测试测试图片目录存在"""
        images_dir = Path(__file__).parent / "images"
        assert images_dir.exists()
        assert images_dir.is_dir()


class TestImageWriter:
    """图像保存测试"""

    def test_supported_formats(self):
        """测试支持的保存格式"""
        writer = ImageWriter()
        assert ".png" in writer.SUPPORTED_FORMATS
        assert ".jpg" in writer.SUPPORTED_FORMATS
        assert ".jpeg" in writer.SUPPORTED_FORMATS

    def test_save_png(self, tmp_path):
        """测试保存 PNG 图像"""
        writer = ImageWriter()
        image = create_test_image()
        output_path = tmp_path / "output.png"

        result = writer.save(image, str(output_path))

        assert result is True
        assert output_path.exists()

    def test_save_jpg(self, tmp_path):
        """测试保存 JPG 图像"""
        writer = ImageWriter()
        image = create_test_image()
        output_path = tmp_path / "output.jpg"

        result = writer.save(image, str(output_path), quality=90)

        assert result is True
        assert output_path.exists()

    def test_save_empty_image(self, tmp_path):
        """测试保存空图像失败"""
        writer = ImageWriter()
        output_path = tmp_path / "output.png"

        result = writer.save(np.array([]), str(output_path))

        assert result is False

class TestImageNormalizer:
    """图像归一化测试"""

    def test_normalize_returns_expected_structure(self):
        """测试归一化输出结构"""
        image = create_test_image()
        normalizer = ImageNormalizer()

        result = normalizer.normalize(image)

        assert result.original_image.shape == image.shape
        assert result.normalized_image.ndim == 3
        assert result.grayscale_image.ndim == 2
        assert result.enhanced_image.ndim == 2
        assert result.normalized_image.dtype == np.uint8
        assert result.scale_factor > 0


class TestOrientationDetector:
    """方向检测测试"""

    def test_detect_and_correct_returns_result(self):
        """测试方向检测可正常返回结果"""
        image = create_test_image()
        detector = OrientationDetector()

        result = detector.detect_and_correct(image)

        assert result.image.ndim == 3
        assert isinstance(result.success, bool)
        assert isinstance(result.angle, float)
        assert 0.0 <= result.confidence <= 1.0


class TestPerspectiveCorrector:
    """透视校正测试"""

    def test_correct_returns_result(self):
        """测试透视校正可正常返回结果"""
        image = create_test_image()
        corrector = PerspectiveCorrector()

        result = corrector.correct(image)

        assert result.image.ndim == 3
        assert isinstance(result.success, bool)
        assert 0.0 <= result.confidence <= 1.0
        if result.success:
            assert result.corners is not None
            assert len(result.corners) == 4


class TestLayoutDetector:
    """版面检测测试"""

    def test_detect_returns_layout_result(self):
        """测试版面检测返回结果对象"""
        image = create_test_image()
        detector = LayoutDetector()

        result = detector.detect(image)

        assert result.image.ndim == 3
        assert isinstance(result.success, bool)
        assert isinstance(result.regions, list)
        assert result.debug_image is not None
        assert 0.0 <= result.confidence <= 1.0


class TestROIExtractor:
    """ROI 提取测试"""

    def test_extract_with_manual_layout(self):
        """测试基于手工 layout 的 ROI 提取"""
        image = create_test_image()
        layout = LayoutDetectionResult(
            image=image,
            regions=[
                LayoutRegion(label="chart", bbox=(40, 30, 240, 180), confidence=0.9),
                LayoutRegion(label="plot", bbox=(80, 60, 160, 120), confidence=0.85),
                LayoutRegion(
                    label="legend_candidate",
                    bbox=(250, 50, 50, 45),
                    confidence=0.7,
                ),
            ],
            success=True,
            confidence=0.9,
            debug_image=image.copy(),
        )

        extractor = ROIExtractor()
        result = extractor.extract(image, layout)

        assert result.success is True
        assert result.plot_roi is not None
        assert result.x_axis_roi is not None
        assert result.y_axis_roi is not None
        assert result.legend_roi is not None
        assert result.plot_bbox is not None


class TestPageDewarper:
    """页面去弯曲测试"""

    def test_dewarp_returns_result(self):
        """测试去弯曲模块返回结果"""
        image = create_test_image()
        dewarper = PageDewarper()

        result = dewarper.dewarp(image)

        assert result.image.ndim == 3
        assert result.success is True
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.method, str)


class TestRealImagesIfPresent:
    """真实测试图片验证"""

    def test_loader_can_scan_images_directory(self):
        """测试可扫描 tests/images 中的图片"""
        images_dir = Path(__file__).parent / "images"
        image_files = [
            path for path in images_dir.iterdir()
            if path.is_file() and path.suffix.lower() in ImageLoader.SUPPORTED_FORMATS
        ]

        assert isinstance(image_files, list)

    @pytest.mark.skipif(
        not any(
            path.is_file() and path.suffix.lower() in ImageLoader.SUPPORTED_FORMATS
            for path in (Path(__file__).parent / "images").glob("*")
        ),
        reason="tests/images 中暂无可用测试图片",
    )
    def test_pipeline_on_real_images(self):
        """测试真实图片可跑通基础处理流程"""
        images_dir = Path(__file__).parent / "images"
        image_files = [
            path for path in images_dir.iterdir()
            if path.is_file() and path.suffix.lower() in ImageLoader.SUPPORTED_FORMATS
        ]

        loader = ImageLoader()
        normalizer = ImageNormalizer()
        orientation_detector = OrientationDetector()
        perspective_corrector = PerspectiveCorrector()
        layout_detector = LayoutDetector()
        dewarper = PageDewarper()

        for image_file in image_files:
            assert loader.load(str(image_file)) is True
            assert loader.image is not None

            normalized = normalizer.normalize(loader.image)
            assert normalized.normalized_image.ndim == 3

            orientation = orientation_detector.detect_and_correct(
                normalized.normalized_image
            )
            assert orientation.image.ndim == 3

            perspective = perspective_corrector.correct(orientation.image)
            assert perspective.image.ndim == 3

            layout = layout_detector.detect(perspective.image)
            assert layout.image.ndim == 3

            dewarp = dewarper.dewarp(perspective.image)
            assert dewarp.image.ndim == 3
