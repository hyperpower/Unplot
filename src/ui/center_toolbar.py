"""
中央工具栏模块
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolButton
from PySide6.QtCore import Signal


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
