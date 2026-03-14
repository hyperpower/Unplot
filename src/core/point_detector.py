"""
数据点检测模块
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class DetectedPoint:
    """检测到的数据点"""
    x_pixel: float
    y_pixel: float
    confidence: float = 1.0


class PointDetector:
    """数据点检测器类
    
    提供手动和自动两种方式检测图像中的数据点。
    """
    
    def __init__(self):
        self._points: List[DetectedPoint] = []
    
    def add_point(self, x: float, y: float, confidence: float = 1.0) -> DetectedPoint:
        """添加一个数据点
        
        Args:
            x: X 像素坐标
            y: Y 像素坐标
            confidence: 置信度
            
        Returns:
            DetectedPoint: 添加的数据点
        """
        point = DetectedPoint(x_pixel=x, y_pixel=y, confidence=confidence)
        self._points.append(point)
        return point
    
    def remove_point(self, index: int) -> bool:
        """移除指定索引的数据点
        
        Args:
            index: 数据点索引
            
        Returns:
            bool: 是否成功移除
        """
        if 0 <= index < len(self._points):
            self._points.pop(index)
            return True
        return False
    
    def clear_points(self) -> None:
        """清除所有数据点"""
        self._points.clear()
    
    def get_points(self) -> List[DetectedPoint]:
        """获取所有数据点
        
        Returns:
            List[DetectedPoint]: 数据点列表
        """
        return self._points.copy()
    
    def get_point_at(self, index: int) -> Optional[DetectedPoint]:
        """获取指定索引的数据点
        
        Args:
            index: 数据点索引
            
        Returns:
            DetectedPoint: 数据点，索引无效时返回 None
        """
        if 0 <= index < len(self._points):
            return self._points[index]
        return None
    
    @property
    def point_count(self) -> int:
        """数据点数量"""
        return len(self._points)
    
    def auto_detect_curve(self, image: np.ndarray, 
                          color_range: Optional[Tuple] = None,
                          min_points: int = 10) -> List[DetectedPoint]:
        """自动检测曲线上的数据点
        
        Args:
            image: RGB 格式的图像数组
            color_range: 颜色范围 (lower, upper)，None 表示自动检测
            min_points: 最小检测点数
            
        Returns:
            List[DetectedPoint]: 检测到的数据点列表
        """
        # 转换为 BGR 用于 OpenCV
        if len(image.shape) == 3:
            bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        else:
            bgr = image
        
        # 转换为灰度图
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        
        # 边缘检测或阈值处理
        if color_range is not None:
            lower, upper = color_range
            mask = cv2.inRange(bgr, np.array(lower), np.array(upper))
        else:
            # 使用 Otsu 阈值
            _, mask = cv2.threshold(gray, 0, 255, 
                                    cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, 
                                        cv2.CHAIN_APPROX_SIMPLE)
        
        points = []
        for contour in contours:
            if len(contour) >= min_points:
                # 获取轮廓上的点
                for point in contour:
                    x, y = point[0]
                    points.append(DetectedPoint(x_pixel=float(x), 
                                                y_pixel=float(y), 
                                                confidence=0.8))
        
        # 按 X 坐标排序
        points.sort(key=lambda p: p.x_pixel)
        
        # 去重（相近的 X 坐标只保留一个）
        if points:
            filtered = [points[0]]
            for point in points[1:]:
                if point.x_pixel - filtered[-1].x_pixel > 2:
                    filtered.append(point)
            points = filtered
        
        self._points = points
        return points
    
    def auto_detect_scatter(self, image: np.ndarray,
                            min_area: float = 10.0,
                            max_area: float = 500.0) -> List[DetectedPoint]:
        """自动检测散点图中的数据点
        
        Args:
            image: RGB 格式的图像数组
            min_area: 最小点面积
            max_area: 最大点面积
            
        Returns:
            List[DetectedPoint]: 检测到的数据点列表
        """
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # 阈值处理
        _, binary = cv2.threshold(gray, 0, 255, 
                                   cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 形态学操作去除噪声
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)
        
        points = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area <= area <= max_area:
                # 计算质心
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = M["m10"] / M["m00"]
                    cy = M["m01"] / M["m00"]
                    points.append(DetectedPoint(x_pixel=cx, y_pixel=cy, 
                                                confidence=0.9))
        
        # 按 X 坐标排序
        points.sort(key=lambda p: p.x_pixel)
        
        self._points = points
        return points
    
    def to_arrays(self) -> Tuple[np.ndarray, np.ndarray]:
        """将数据点转换为 numpy 数组
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: (x_array, y_array)
        """
        if not self._points:
            return np.array([]), np.array([])
        
        x = np.array([p.x_pixel for p in self._points])
        y = np.array([p.y_pixel for p in self._points])
        return x, y