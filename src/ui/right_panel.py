"""
右侧面板模块
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QScrollArea, QLabel
)
from PySide6.QtCore import Qt

from .settings_sections import SettingsSection


class RightPanel(QFrame):
    """右侧面板组件
    
    位于窗口最右侧，包含多个设置区域。
    不可收起，但有最小宽度限制。
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sections = {}
        self._init_ui()
        
    def _init_ui(self):
        """初始化 UI"""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setLineWidth(1)
        self.setMinimumWidth(280)
        self.setMaximumWidth(450)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 标题栏
        title_label = QLabel("  设置")
        title_label.setFixedHeight(42)
        main_layout.addWidget(title_label)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 内容容器
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(8, 8, 8, 8)
        self._content_layout.setSpacing(8)
        self._content_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(self._content_widget)
        main_layout.addWidget(scroll_area)
        
    def add_section(self, name: str, section: SettingsSection):
        """添加一个设置区域
        
        Args:
            name: 设置区域的唯一标识名
            section: 设置区域实例
        """
        self._sections[name] = section
        self._content_layout.addWidget(section)
        
    def get_section(self, name: str) -> SettingsSection:
        """获取指定名称的设置区域
        
        Args:
            name: 设置区域名称
            
        Returns:
            设置区域实例，如果不存在则返回 None
        """
        return self._sections.get(name)
        
    def remove_section(self, name: str):
        """移除一个设置区域
        
        Args:
            name: 设置区域名称
        """
        if name in self._sections:
            section = self._sections.pop(name)
            section.setParent(None)
            section.deleteLater()
            
    def get_all_values(self) -> dict:
        """获取所有设置区域的值
        
        Returns:
            包含所有设置值的字典
        """
        values = {}
        for name, section in self._sections.items():
            values[name] = section.get_values()
        return values
        
    def set_all_values(self, values: dict):
        """设置所有设置区域的值
        
        Args:
            values: 包含设置值的字典，格式为 {section_name: {key: value}}
        """
        for name, section_values in values.items():
            if name in self._sections:
                self._sections[name].set_values(section_values)