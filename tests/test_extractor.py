"""
数据提取器测试模块
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.image_loader import ImageLoader
from core.coordinate_mapper import CoordinateMapper
from core.point_detector import PointDetector
from core.data_extractor import DataExtractor
from utils.export_data import DataExporter


class TestImageLoader:
    """图像加载器测试"""
    
    def test_init(self):
        """测试初始化"""
        loader = ImageLoader()
        assert loader.image is None
        assert loader.image_path is None
        
    def test_supported_formats(self):
        """测试支持的格式"""
        loader = ImageLoader()
        formats = loader.SUPPORTED_FORMATS
        assert '.png' in formats
        assert '.jpg' in formats
        assert '.jpeg' in formats


class TestCoordinateMapper:
    """坐标映射器测试"""
    
    def test_init(self):
        """测试初始化"""
        mapper = CoordinateMapper()
        assert not mapper.is_configured()
        
    def test_set_x_axis(self):
        """测试设置 X 轴"""
        mapper = CoordinateMapper()
        mapper.set_x_axis(0, 0, 100, 10)
        assert mapper.is_configured() is False  # 只设置了 X 轴
        
    def test_set_y_axis(self):
        """测试设置 Y 轴"""
        mapper = CoordinateMapper()
        mapper.set_y_axis(0, 0, 100, 10)
        assert mapper.is_configured() is False  # 只设置了 Y 轴
        
    def test_pixel_to_data(self):
        """测试像素到数据的转换"""
        mapper = CoordinateMapper()
        mapper.set_x_axis(0, 0, 100, 10)
        mapper.set_y_axis(0, 0, 100, 10)
        
        x_data, y_data = mapper.pixel_to_data(50, 50)
        assert abs(x_data - 5.0) < 0.001
        assert abs(y_data - 5.0) < 0.001
        
    def test_data_to_pixel(self):
        """测试数据到像素的转换"""
        mapper = CoordinateMapper()
        mapper.set_x_axis(0, 0, 100, 10)
        mapper.set_y_axis(0, 0, 100, 10)
        
        x_pixel, y_pixel = mapper.data_to_pixel(5, 5)
        assert abs(x_pixel - 50) < 0.001
        assert abs(y_pixel - 50) < 0.001
        
    def test_reset(self):
        """测试重置"""
        mapper = CoordinateMapper()
        mapper.set_x_axis(0, 0, 100, 10)
        mapper.set_y_axis(0, 0, 100, 10)
        mapper.reset()
        assert not mapper.is_configured()


class TestPointDetector:
    """点检测器测试"""
    
    def test_init(self):
        """测试初始化"""
        detector = PointDetector()
        assert detector.point_count == 0
        
    def test_add_point(self):
        """测试添加点"""
        detector = PointDetector()
        detector.add_point(10, 20)
        assert detector.point_count == 1
        
    def test_remove_point(self):
        """测试移除点"""
        detector = PointDetector()
        detector.add_point(10, 20)
        detector.add_point(30, 40)
        assert detector.remove_point(0) is True
        assert detector.point_count == 1
        
    def test_clear_points(self):
        """测试清除点"""
        detector = PointDetector()
        detector.add_point(10, 20)
        detector.add_point(30, 40)
        detector.clear_points()
        assert detector.point_count == 0
        
    def test_to_arrays(self):
        """测试转换为数组"""
        detector = PointDetector()
        detector.add_point(10, 20)
        detector.add_point(30, 40)
        
        x, y = detector.to_arrays()
        assert len(x) == 2
        assert len(y) == 2
        assert x[0] == 10
        assert y[0] == 20


class TestDataExtractor:
    """数据提取器测试"""
    
    def test_init(self):
        """测试初始化"""
        extractor = DataExtractor()
        assert extractor.image_loader is not None
        assert extractor.coordinate_mapper is not None
        assert extractor.point_detector is not None
        
    def test_set_axis_calibration(self):
        """测试设置坐标轴校准"""
        extractor = DataExtractor()
        extractor.set_axis_calibration(
            0, 0, 100, 10,
            0, 0, 100, 10
        )
        assert extractor.coordinate_mapper.is_configured()
        
    def test_add_point(self):
        """测试添加数据点"""
        extractor = DataExtractor()
        extractor.set_axis_calibration(
            0, 0, 100, 10,
            0, 0, 100, 10
        )
        point = extractor.add_point(50, 50)
        assert point.x_pixel == 50
        assert point.y_pixel == 50
        assert abs(point.x_data - 5.0) < 0.001
        assert abs(point.y_data - 5.0) < 0.001


class TestDataExporter:
    """数据导出器测试"""
    
    def test_init(self):
        """测试初始化"""
        exporter = DataExporter()
        assert exporter is not None
        
    def test_export_csv(self, tmp_path):
        """测试导出 CSV"""
        exporter = DataExporter()
        file_path = tmp_path / "test.csv"
        
        x = [1, 2, 3]
        y = [4, 5, 6]
        
        result = exporter.export(x, y, str(file_path))
        assert result is True
        assert file_path.exists()
        
    def test_export_txt(self, tmp_path):
        """测试导出文本"""
        exporter = DataExporter()
        file_path = tmp_path / "test.txt"
        
        x = [1, 2, 3]
        y = [4, 5, 6]
        
        result = exporter.export(x, y, str(file_path))
        assert result is True
        assert file_path.exists()
        
    def test_export_empty_data(self, tmp_path):
        """测试导出空数据"""
        exporter = DataExporter()
        file_path = tmp_path / "test.csv"
        
        with pytest.raises(ValueError):
            exporter.export([], [], str(file_path))
            
    def test_export_mismatched_data(self, tmp_path):
        """测试导出长度不匹配的数据"""
        exporter = DataExporter()
        file_path = tmp_path / "test.csv"
        
        with pytest.raises(ValueError):
            exporter.export([1, 2], [1, 2, 3], str(file_path))