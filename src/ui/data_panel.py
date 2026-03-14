"""
数据面板模块
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTreeWidget, QTreeWidgetItem, QTableWidget, 
    QTableWidgetItem, QFrame, QSplitter, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Qt


class DataPanel(QFrame):
    """数据面板组件
    
    位于左侧导航栏右侧，包含树状结构和属性列表。
    支持展开/收起状态切换。
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_expanded = True
        self._init_ui()
        
    def _init_ui(self):
        """初始化 UI"""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setLineWidth(1)
        self.setMinimumWidth(200)
        self.setMaximumWidth(400)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建垂直分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 上半部分：树状结构
        tree_widget = self._create_tree_widget()
        splitter.addWidget(tree_widget)
        
        # 下半部分：属性列表
        prop_widget = self._create_property_widget()
        splitter.addWidget(prop_widget)
        
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
    def _create_tree_widget(self) -> QWidget:
        """创建树状结构组件"""
        # 标题栏
        title_label = QLabel("图层结构")
        # title_label.setFixedHeight(36)
        
        # 树状控件
        tree = QTreeWidget()
        tree.setHeaderLabels(["名称", "类型"])
        tree.setColumnCount(2)
        tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        # 添加示例数据
        self._populate_tree(tree)
        
        # 容器
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(title_label)
        layout.addWidget(tree)
        
        # 设置容器宽度策略为撑满父控件
        container.setSizePolicy(container.sizePolicy().horizontalPolicy(),
                               QSizePolicy.Expanding)
        
        return container
        
    def _create_property_widget(self) -> QWidget:
        """创建属性列表组件"""
        # 标题栏
        title_label = QLabel("属性")
        # title_label.setFixedHeight(36)
        
        # 属性表格
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["属性", "值"])
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        
        # 添加示例数据
        self._populate_table(table)
        
        # 容器
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(title_label)
        layout.addWidget(table)
        
        # 设置容器宽度策略为撑满父控件
        container.setSizePolicy(container.sizePolicy().horizontalPolicy(),
                               QSizePolicy.Expanding)
        
        return container
        
    def _populate_tree(self, tree: QTreeWidget):
        """填充树状结构示例数据"""
        # 根节点
        root1 = QTreeWidgetItem(tree, ["图层 1", "Curve"])
        root1.setExpanded(True)
        QTreeWidgetItem(root1, ["数据点", "Points"])
        QTreeWidgetItem(root1, ["坐标轴", "Axis"])
        
        root2 = QTreeWidgetItem(tree, ["图层 2", "Curve"])
        QTreeWidgetItem(root2, ["数据点", "Points"])
        QTreeWidgetItem(root2, ["坐标轴", "Axis"])
        
        root3 = QTreeWidgetItem(tree, ["图层 3", "Scatter"])
        QTreeWidgetItem(root3, ["数据点", "Points"])
        
    def _populate_table(self, table: QTableWidget):
        """填充属性表示例数据"""
        properties = [
            ("名称", "图层 1"),
            ("类型", "Curve"),
            ("颜色", "#FF5722"),
            ("线宽", "2"),
            ("可见", "是"),
            ("数据点数", "0"),
        ]
        
        table.setRowCount(len(properties))
        for i, (prop, value) in enumerate(properties):
            table.setItem(i, 0, QTableWidgetItem(prop))
            table.setItem(i, 1, QTableWidgetItem(value))
            
    def set_expanded(self, expanded: bool):
        """设置面板展开/收起状态"""
        self._is_expanded = expanded
        self.setVisible(expanded)
        
    def is_expanded(self) -> bool:
        """返回当前展开状态"""
        return self._is_expanded
    
    def toggle(self):
        """切换展开/收起状态"""
        self._is_expanded = not self._is_expanded
        self.setVisible(self._is_expanded)