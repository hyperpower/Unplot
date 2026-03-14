"""
坐标映射模块
"""

from typing import Tuple, Optional, List
import numpy as np


class CoordinateMapper:
    """坐标映射器类
    
    负责在像素坐标和数据坐标之间进行转换。
    用户需要设置坐标轴的参考点来完成映射配置。
    """
    
    def __init__(self):
        # X 轴参考点 (x1_pixel, x1_data) 和 (x2_pixel, x2_data)
        self._x1_pixel: Optional[float] = None
        self._x2_pixel: Optional[float] = None
        self._x1_data: Optional[float] = None
        self._x2_data: Optional[float] = None
        
        # Y 轴参考点 (y1_pixel, y1_data) 和 (y2_pixel, y2_data)
        self._y1_pixel: Optional[float] = None
        self._y2_pixel: Optional[float] = None
        self._y1_data: Optional[float] = None
        self._y2_data: Optional[float] = None
        
        # 缩放和偏移参数
        self._x_scale: float = 1.0
        self._x_offset: float = 0.0
        self._y_scale: float = 1.0
        self._y_offset: float = 0.0
    
    def set_x_axis(self, x1_pixel: float, x1_data: float, 
                   x2_pixel: float, x2_data: float) -> None:
        """设置 X 轴映射
        
        Args:
            x1_pixel: 第一个参考点的像素 X 坐标
            x1_data: 第一个参考点对应的数据值
            x2_pixel: 第二个参考点的像素 X 坐标
            x2_data: 第二个参考点对应的数据值
        """
        self._x1_pixel = x1_pixel
        self._x2_pixel = x2_pixel
        self._x1_data = x1_data
        self._x2_data = x2_data
        
        # 计算缩放和偏移
        if x2_pixel != x1_pixel:
            self._x_scale = (x2_data - x1_data) / (x2_pixel - x1_pixel)
            self._x_offset = x1_data - self._x_scale * x1_pixel
    
    def set_y_axis(self, y1_pixel: float, y1_data: float,
                   y2_pixel: float, y2_data: float) -> None:
        """设置 Y 轴映射
        
        Args:
            y1_pixel: 第一个参考点的像素 Y 坐标
            y1_data: 第一个参考点对应的数据值
            y2_pixel: 第二个参考点的像素 Y 坐标
            y2_data: 第二个参考点对应的数据值
        """
        self._y1_pixel = y1_pixel
        self._y2_pixel = y2_pixel
        self._y1_data = y1_data
        self._y2_data = y2_data
        
        # 计算缩放和偏移
        if y2_pixel != y1_pixel:
            self._y_scale = (y2_data - y1_data) / (y2_pixel - y1_pixel)
            self._y_offset = y1_data - self._y_scale * y1_pixel
    
    def pixel_to_data(self, x_pixel: float, y_pixel: float) -> Tuple[float, float]:
        """将像素坐标转换为数据坐标
        
        Args:
            x_pixel: 像素 X 坐标
            y_pixel: 像素 Y 坐标
            
        Returns:
            Tuple[float, float]: 数据坐标 (x_data, y_data)
            
        Raises:
            ValueError: 如果坐标映射未配置
        """
        if self._x1_pixel is None or self._y1_pixel is None:
            raise ValueError("坐标映射未配置，请先设置坐标轴")
        
        x_data = self._x_scale * x_pixel + self._x_offset
        y_data = self._y_scale * y_pixel + self._y_offset
        
        return (x_data, y_data)
    
    def data_to_pixel(self, x_data: float, y_data: float) -> Tuple[float, float]:
        """将数据坐标转换为像素坐标
        
        Args:
            x_data: 数据 X 坐标
            y_data: 数据 Y 坐标
            
        Returns:
            Tuple[float, float]: 像素坐标 (x_pixel, y_pixel)
            
        Raises:
            ValueError: 如果坐标映射未配置
        """
        if self._x1_pixel is None or self._y1_pixel is None:
            raise ValueError("坐标映射未配置，请先设置坐标轴")
        
        if self._x_scale != 0:
            x_pixel = (x_data - self._x_offset) / self._x_scale
        else:
            x_pixel = 0
            
        if self._y_scale != 0:
            y_pixel = (y_data - self._y_offset) / self._y_scale
        else:
            y_pixel = 0
        
        return (x_pixel, y_pixel)
    
    def is_configured(self) -> bool:
        """检查坐标映射是否已配置
        
        Returns:
            bool: 是否已配置
        """
        return (self._x1_pixel is not None and self._y1_pixel is not None)
    
    def reset(self) -> None:
        """重置坐标映射配置"""
        self._x1_pixel = None
        self._x2_pixel = None
        self._x1_data = None
        self._x2_data = None
        self._y1_pixel = None
        self._y2_pixel = None
        self._y1_data = None
        self._y2_data = None
        self._x_scale = 1.0
        self._x_offset = 0.0
        self._y_scale = 1.0
        self._y_offset = 0.0
    
    def get_x_range(self) -> Optional[Tuple[float, float]]:
        """获取 X 轴数据范围
        
        Returns:
            Tuple[float, float]: X 轴最小值和最大值，未配置时返回 None
        """
        if self._x1_data is not None and self._x2_data is not None:
            return (min(self._x1_data, self._x2_data), 
                    max(self._x1_data, self._x2_data))
        return None
    
    def get_y_range(self) -> Optional[Tuple[float, float]]:
        """获取 Y 轴数据范围
        
        Returns:
            Tuple[float, float]: Y 轴最小值和最大值，未配置时返回 None
        """
        if self._y1_data is not None and self._y2_data is not None:
            return (min(self._y1_data, self._y2_data), 
                    max(self._y1_data, self._y2_data))
        return None