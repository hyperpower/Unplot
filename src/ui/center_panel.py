"""
中央面板模块
"""

import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
    QLabel, QToolButton
)
from PySide6.QtCore import Signal, Slot, QRect, QPointF, QRectF, Qt
from PySide6.QtGui import QPainter, QImage, QPen, QBrush


class CenterToolBar(QFrame):
    """中央区域顶部工具栏
    
    包含工具图标按钮。
    """
    
    # 信号：工具按钮点击
    tool_clicked = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        """初始化 UI"""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setFixedHeight(44)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # 标题标签
        title = QLabel("  工具")
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # 工具按钮
        self._btn_select = self._create_button("🖱️", "选择工具")
        self._btn_select.clicked.connect(lambda: self.tool_clicked.emit("select"))
        
        self._btn_point = self._create_button("➕", "添加点")
        self._btn_point.clicked.connect(lambda: self.tool_clicked.emit("add_point"))
        
        layout.addWidget(self._btn_select)
        layout.addWidget(self._btn_point)
        
        # 弹性空间
        layout.addStretch()
        
    def _create_button(self, text: str, tooltip: str) -> QToolButton:
        """创建工具按钮"""
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tooltip)
        btn.setAutoRaise(True)
        return btn


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


class CenterPanel(QWidget):
    """中央面板组件
    
    包含顶部工具栏和图像画布。
    """
    
    # 信号：画布点击
    canvas_clicked = Signal(float, float)
    # 信号：工具点击
    tool_clicked = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 顶部工具栏
        self._toolbar = CenterToolBar()
        self._toolbar.tool_clicked.connect(self.tool_clicked.emit)
        layout.addWidget(self._toolbar)
        
        # 画布
        self._canvas = ImageCanvas()
        self._canvas.point_clicked.connect(self.canvas_clicked.emit)
        layout.addWidget(self._canvas)
        
    @property
    def canvas(self) -> ImageCanvas:
        """获取画布组件"""
        return self._canvas
    
    @property
    def toolbar(self) -> CenterToolBar:
        """获取工具栏组件"""
        return self._toolbar
    
    def set_image(self, image: np.ndarray) -> None:
        """设置画布图像"""
        self._canvas.set_image(image)
        
    def clear_image(self) -> None:
        """清除画布图像"""
        self._canvas.clear_image()