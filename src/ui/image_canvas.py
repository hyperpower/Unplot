"""
图像画布模块
"""

import numpy as np
from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Signal, QRect, QPointF, Qt
from PySide6.QtGui import QPainter, QImage, QPen, QBrush


class ImageCanvas(QFrame):
    """图像画布组件
    
    用于显示图像并处理用户的鼠标交互。
    """
    
    point_clicked = Signal(float, float)  # 信号：用户点击位置（像素坐标）
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = None
        self._points: list = []  # 存储已添加的点
        self._axis_points: list = []  # 存储坐标轴参考点
        
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.setLineWidth(2)
        self.setMinimumSize(400, 300)
        
    def set_image(self, image: np.ndarray) -> None:
        """设置要显示的图像"""
        self._image = image
        self._points.clear()
        self._axis_points.clear()
        self.update()
        
    def clear_image(self) -> None:
        """清除图像"""
        self._image = None
        self._points.clear()
        self._axis_points.clear()
        self.update()
        
    def add_point(self, x: float, y: float) -> None:
        """添加一个显示点"""
        self._points.append((x, y))
        self.update()
        
    def clear_points(self) -> None:
        """清除所有数据点"""
        self._points.clear()
        self.update()
        
    def set_axis_points(self, points: list) -> None:
        """设置坐标轴参考点"""
        self._axis_points = points
        self.update()
        
    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        if self._image is not None:
            x = event.position().x()
            y = event.position().y()
            self.point_clicked.emit(x, y)
            
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        painter.fillRect(self.rect(), Qt.white)
        
        if self._image is not None:
            # 转换 numpy 数组为 QImage
            h, w, ch = self._image.shape
            bytes_per_line = ch * w
            qimage = QImage(self._image.data, w, h, bytes_per_line, 
                           QImage.Format_RGB888)
            
            # 缩放以适应画布
            scaled_rect = self._get_scaled_rect(w, h)
            painter.drawImage(scaled_rect, qimage)
            
            # 计算缩放比例
            scale_x = scaled_rect.width() / w
            scale_y = scaled_rect.height() / h
            
            # 绘制数据点
            pen = QPen(Qt.red, 3)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QBrush(Qt.red))
            
            for px, py in self._points:
                cx = scaled_rect.left() + px * scale_x
                cy = scaled_rect.top() + py * scale_y
                painter.drawEllipse(QPointF(cx, cy), 5, 5)
            
            # 绘制坐标轴参考点（蓝色）
            pen.setColor(Qt.blue)
            painter.setPen(pen)
            painter.setBrush(QBrush(Qt.blue))
            
            for i, (px, py) in enumerate(self._axis_points):
                cx = scaled_rect.left() + px * scale_x
                cy = scaled_rect.top() + py * scale_y
                painter.drawEllipse(QPointF(cx, cy), 7, 7)
                
    def _get_scaled_rect(self, img_w: int, img_h: int):
        """计算图像缩放的矩形区域"""
        canvas_w = self.width() - 20
        canvas_h = self.height() - 20
        
        if canvas_w <= 0 or canvas_h <= 0:
            return QRect(10, 10, 10, 10)
        
        scale = min(canvas_w / img_w, canvas_h / img_h)
        
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        x = 10 + (canvas_w - new_w) // 2
        y = 10 + (canvas_h - new_h) // 2
        
        return QRect(x, y, new_w, new_h)
