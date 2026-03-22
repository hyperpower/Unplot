"""
图像画布模块

使用matplotlib作为backend实现图像显示和交互功能。
"""

import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class ImageCanvas(QWidget):
    """图像画布组件
    
    使用matplotlib作为backend，用于显示图像并处理用户的鼠标交互。
    """
    
    point_clicked = Signal(float, float)  # 信号：用户点击位置（像素坐标）
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化matplotlib图表
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # 布局设置
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        # 数据存储
        self._image = None
        self._points: list = []  # 存储已添加的点
        self._axis_points: list = []  # 存储坐标轴参考点
        
        # 设置最小尺寸
        self.setMinimumSize(400, 300)
        
        # 连接鼠标点击事件
        self.canvas.mpl_connect('button_press_event', self._on_canvas_click)
        self.clear_image()
        
    def set_image(self, image: np.ndarray) -> None:
        """设置要显示的图像
        
        Args:
            image: numpy数组格式的图像 (H, W, C)
        """
        if image is None:
            self.clear_image()
            return
            
        self._image = np.copy(image)
        self._points.clear()
        self._axis_points.clear()
        self._render()
        
    def clear_image(self) -> None:
        """清除图像和所有标记点"""
        self._image = None
        self._points.clear()
        self._axis_points.clear()
        
        # 清空matplotlib轴
        self.ax.clear()
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw_idle()
        
    def add_point(self, x: float, y: float) -> None:
        """添加一个显示点
        
        Args:
            x: 点的x坐标（像素坐标）
            y: 点的y坐标（像素坐标）
        """
        if self._image is not None:
            self._points.append((x, y))
            self._render()
        
    def clear_points(self) -> None:
        """清除所有数据点"""
        self._points.clear()
        if self._image is not None:
            self._render()

    def has_image(self) -> bool:
        """返回当前是否已加载图像。"""
        return self._image is not None
        
    def set_axis_points(self, points: list) -> None:
        """设置坐标轴参考点
        
        Args:
            points: 坐标轴参考点列表 [(x1, y1), (x2, y2), ...]
        """
        self._axis_points = points if points is not None else []
        if self._image is not None:
            self._render()
        
    def _on_canvas_click(self, event) -> None:
        """处理matplotlib画布的点击事件"""
        if event.inaxes == self.ax and self._image is not None:
            if event.xdata is not None and event.ydata is not None:
                self.point_clicked.emit(float(event.xdata), float(event.ydata))
                
    def _render(self) -> None:
        """重新渲染画布"""
        self.ax.clear()
        
        if self._image is None:
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.canvas.draw_idle()
            return
        
        # 显示图像
        # 处理不同格式的图像
        if len(self._image.shape) == 2:
            # 灰度图
            self.ax.imshow(self._image, cmap='gray')
        elif len(self._image.shape) == 3:
            if self._image.shape[2] == 3:
                # RGB图
                # 确保值在0-255范围内
                img_display = self._image.astype(np.uint8) if self._image.dtype == np.uint8 else \
                              (self._image * 255).astype(np.uint8)
                self.ax.imshow(img_display)
            elif self._image.shape[2] == 4:
                # RGBA图
                img_display = self._image.astype(np.uint8) if self._image.dtype == np.uint8 else \
                              (self._image * 255).astype(np.uint8)
                self.ax.imshow(img_display)
        
        # 绘制数据点（红色）
        if self._points:
            points_array = np.array(self._points)
            self.ax.plot(points_array[:, 0], points_array[:, 1], 'ro', 
                        markersize=8, label='Data Points')
        
        # 绘制坐标轴参考点（蓝色）
        if self._axis_points:
            axis_array = np.array(self._axis_points)
            self.ax.plot(axis_array[:, 0], axis_array[:, 1], 'bs', 
                        markersize=10, label='Axis Points')
        
        # 设置坐标轴
        self.ax.set_xlabel('X (pixels)')
        self.ax.set_ylabel('Y (pixels)')
        
        if self._points or self._axis_points:
            self.ax.legend(loc='upper right')
        
        self.figure.tight_layout()
        self.canvas.draw_idle()
