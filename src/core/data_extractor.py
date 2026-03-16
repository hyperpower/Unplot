"""
数据提取核心模块
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass

from .image_process import ImageLoader
from .coordinate_mapper import CoordinateMapper
from .point_detector import PointDetector, DetectedPoint


@dataclass
class DataPoint:
    """数据点（包含像素坐标和数据坐标）"""
    x_pixel: float
    y_pixel: float
    x_data: float
    y_data: float


class DataExtractor:
    """数据提取器类
    
    整合图像加载、坐标映射和点检测功能，提供完整的数据提取流程。
    """
    
    def __init__(self):
        self._image_loader = ImageLoader()
        self._coordinate_mapper = CoordinateMapper()
        self._point_detector = PointDetector()
        self._extracted_data: List[DataPoint] = []
    
    @property
    def image_loader(self) -> ImageLoader:
        """获取图像加载器"""
        return self._image_loader
    
    @property
    def coordinate_mapper(self) -> CoordinateMapper:
        """获取坐标映射器"""
        return self._coordinate_mapper
    
    @property
    def point_detector(self) -> PointDetector:
        """获取点检测器"""
        return self._point_detector
    
    def load_image(self, path: str) -> bool:
        """加载图像
        
        Args:
            path: 图像文件路径
            
        Returns:
            bool: 加载是否成功
        """
        return self._image_loader.load(path)
    
    def set_axis_calibration(self, x1_pixel: float, x1_data: float,
                             x2_pixel: float, x2_data: float,
                             y1_pixel: float, y1_data: float,
                             y2_pixel: float, y2_data: float) -> None:
        """设置坐标轴校准
        
        Args:
            x1_pixel, x1_data: X 轴第一个参考点的像素和数据值
            x2_pixel, x2_data: X 轴第二个参考点的像素和数据值
            y1_pixel, y1_data: Y 轴第一个参考点的像素和数据值
            y2_pixel, y2_data: Y 轴第二个参考点的像素和数据值
        """
        self._coordinate_mapper.set_x_axis(x1_pixel, x1_data, x2_pixel, x2_data)
        self._coordinate_mapper.set_y_axis(y1_pixel, y1_data, y2_pixel, y2_data)
    
    def add_point(self, x_pixel: float, y_pixel: float) -> DataPoint:
        """添加一个数据点
        
        Args:
            x_pixel: X 像素坐标
            y_pixel: Y 像素坐标
            
        Returns:
            DataPoint: 添加的数据点（包含数据坐标）
        """
        # 添加点到检测器
        self._point_detector.add_point(x_pixel, y_pixel)
        
        # 转换为数据坐标
        x_data, y_data = self._coordinate_mapper.pixel_to_data(x_pixel, y_pixel)
        
        data_point = DataPoint(
            x_pixel=x_pixel,
            y_pixel=y_pixel,
            x_data=x_data,
            y_data=y_data
        )
        self._extracted_data.append(data_point)
        
        return data_point
    
    def remove_point(self, index: int) -> bool:
        """移除指定索引的数据点
        
        Args:
            index: 数据点索引
            
        Returns:
            bool: 是否成功移除
        """
        if 0 <= index < len(self._extracted_data):
            self._extracted_data.pop(index)
            # 重新同步点检测器
            self._sync_points()
            return True
        return False
    
    def clear_points(self) -> None:
        """清除所有数据点"""
        self._extracted_data.clear()
        self._point_detector.clear_points()
    
    def _sync_points(self) -> None:
        """同步提取的数据到点检测器"""
        self._point_detector.clear_points()
        for point in self._extracted_data:
            self._point_detector.add_point(point.x_pixel, point.y_pixel)
    
    def get_data_points(self) -> List[DataPoint]:
        """获取所有提取的数据点
        
        Returns:
            List[DataPoint]: 数据点列表
        """
        return self._extracted_data.copy()
    
    def get_data_arrays(self) -> Tuple[np.ndarray, np.ndarray]:
        """获取数据坐标数组
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: (x_data_array, y_data_array)
        """
        if not self._extracted_data:
            return np.array([]), np.array([])
        
        x = np.array([p.x_data for p in self._extracted_data])
        y = np.array([p.y_data for p in self._extracted_data])
        return x, y
    
    def get_pixel_arrays(self) -> Tuple[np.ndarray, np.ndarray]:
        """获取像素坐标数组
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: (x_pixel_array, y_pixel_array)
        """
        if not self._extracted_data:
            return np.array([]), np.array([])
        
        x = np.array([p.x_pixel for p in self._extracted_data])
        y = np.array([p.y_pixel for p in self._extracted_data])
        return x, y
    
    def auto_extract_curve(self, color_range: Optional[Tuple] = None) -> int:
        """自动提取曲线数据
        
        Args:
            color_range: 颜色范围 (lower, upper)，None 表示自动检测
            
        Returns:
            int: 提取的数据点数量
        """
        image = self._image_loader.image
        if image is None:
            return 0
        
        points = self._point_detector.auto_detect_curve(image, color_range)
        
        # 转换为数据坐标
        self._extracted_data.clear()
        for point in points:
            try:
                x_data, y_data = self._coordinate_mapper.pixel_to_data(
                    point.x_pixel, point.y_pixel
                )
                self._extracted_data.append(DataPoint(
                    x_pixel=point.x_pixel,
                    y_pixel=point.y_pixel,
                    x_data=x_data,
                    y_data=y_data
                ))
            except ValueError:
                continue
        
        return len(self._extracted_data)
    
    def auto_extract_scatter(self, min_area: float = 10.0,
                             max_area: float = 500.0) -> int:
        """自动提取散点图数据
        
        Args:
            min_area: 最小点面积
            max_area: 最大点面积
            
        Returns:
            int: 提取的数据点数量
        """
        image = self._image_loader.image
        if image is None:
            return 0
        
        points = self._point_detector.auto_detect_scatter(image, min_area, max_area)
        
        # 转换为数据坐标
        self._extracted_data.clear()
        for point in points:
            try:
                x_data, y_data = self._coordinate_mapper.pixel_to_data(
                    point.x_pixel, point.y_pixel
                )
                self._extracted_data.append(DataPoint(
                    x_pixel=point.x_pixel,
                    y_pixel=point.y_pixel,
                    x_data=x_data,
                    y_data=y_data
                ))
            except ValueError:
                continue
        
        return len(self._extracted_data)
    
    def reset(self) -> None:
        """重置提取器状态"""
        self._image_loader.unload()
        self._coordinate_mapper.reset()
        self._point_detector.clear_points()
        self._extracted_data.clear()
