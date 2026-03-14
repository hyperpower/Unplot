"""
设置区域基类模块
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Signal


class SettingsSection(QFrame):
    """设置区域基类
    
    所有设置区域组件的基类，提供统一的标题和样式。
    子类应实现具体的设置控件。
    """
    
    # 信号：设置值改变
    value_changed = Signal(str, object)
    
    def __init__(self, title: str = "设置", parent=None):
        super().__init__(parent)
        self._title = title
        self._init_ui()
        
    def _init_ui(self):
        """初始化 UI"""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题
        self._title_label = QLabel("  " + self._title)
        layout.addWidget(self._title_label)
        
        # 内容区域（由子类填充）
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(12, 12, 12, 12)
        self._content_layout.setSpacing(8)
        layout.addWidget(self._content_widget)
        
    @property
    def content_layout(self) -> QVBoxLayout:
        """获取内容布局，供子类使用"""
        return self._content_layout
    
    def add_widget(self, widget: QWidget):
        """添加控件到内容区域"""
        self._content_layout.addWidget(widget)
        
    def get_values(self) -> dict:
        """获取所有设置值
        
        子类应重写此方法返回设置值字典。
        """
        return {}
        
    def set_values(self, values: dict):
        """设置所有值
        
        子类应重写此方法以设置值。
        """
        pass