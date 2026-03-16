"""
工作树控件模块
"""

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QHeaderView, QFrame
from PySide6.QtCore import Qt


class WorkTreeWidget(QTreeWidget):
    """工作树控件
    
    继承自 QTreeWidget，用于显示图层结构。
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._populate_tree()
        
    def _init_ui(self):
        """初始化 UI"""
        self.setHeaderLabels(["名称", "类型"])
        self.setColumnCount(2)
        self.setFrameShape(QFrame.NoFrame)
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
    def _populate_tree(self):
        """填充树状结构示例数据"""
        # 根节点
        root1 = QTreeWidgetItem(self, ["图层 1", "Curve"])
        root1.setExpanded(True)
        QTreeWidgetItem(root1, ["数据点", "Points"])
        QTreeWidgetItem(root1, ["坐标轴", "Axis"])
        
        root2 = QTreeWidgetItem(self, ["图层 2", "Curve"])
        QTreeWidgetItem(root2, ["数据点", "Points"])
        QTreeWidgetItem(root2, ["坐标轴", "Axis"])
        
        root3 = QTreeWidgetItem(self, ["图层 3", "Scatter"])
        QTreeWidgetItem(root3, ["数据点", "Points"])