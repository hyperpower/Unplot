"""
图像加载模块
"""

import cv2
import numpy as np
from typing import Optional, Tuple


class ImageLoader:
    """图像加载器类
    
    负责加载和处理图像文件，支持常见格式如 PNG, JPG, BMP 等。
    """
    
    SUPPORTED_FORMATS = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.gif']
    
    def __init__(self):
        self._image: Optional[np.ndarray] = None
        self._image_path: Optional[str] = None
    
    @property
    def image(self) -> Optional[np.ndarray]:
        """获取当前加载的图像"""
        return self._image
    
    @property
    def image_path(self) -> Optional[str]:
        """获取当前图像路径"""
        return self._image_path
    
    @property
    def image_size(self) -> Optional[Tuple[int, int]]:
        """获取图像尺寸 (宽，高)"""
        if self._image is not None:
            return (self._image.shape[1], self._image.shape[0])
        return None
    
    def load(self, path: str) -> bool:
        """加载图像文件
        
        Args:
            path: 图像文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            # 检查文件扩展名
            import os
            ext = os.path.splitext(path)[1].lower()
            if ext not in self.SUPPORTED_FORMATS:
                raise ValueError(f"不支持的图像格式：{ext}")
            
            # 使用 OpenCV 加载图像
            image = cv2.imread(path, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("无法读取图像文件")
            
            # 转换为 RGB 格式
            self._image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self._image_path = path
            return True
            
        except Exception as e:
            print(f"加载图像失败：{e}")
            self._image = None
            self._image_path = None
            return False
    
    def unload(self) -> None:
        """卸载当前图像"""
        self._image = None
        self._image_path = None
    
    def get_pixel(self, x: int, y: int) -> Optional[Tuple[int, int, int]]:
        """获取指定位置的像素值
        
        Args:
            x: X 坐标
            y: Y 坐标
            
        Returns:
            Tuple[int, int, int]: RGB 像素值，如果坐标无效则返回 None
        """
        if self._image is None:
            return None
        
        h, w = self._image.shape[:2]
        if 0 <= x < w and 0 <= y < h:
            return tuple(self._image[y, x].tolist())
        return None