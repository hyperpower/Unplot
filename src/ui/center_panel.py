"""
中央面板模块
"""

import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from .center_toolbar import CenterToolBar
from .image_canvas import ImageCanvas


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