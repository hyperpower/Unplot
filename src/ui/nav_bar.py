"""
导航栏模块
"""

from PySide6.QtWidgets import QToolBar, QToolButton, QWidgetAction, QSpacerItem, QWidget, QSizePolicy
from PySide6.QtCore import Signal, Qt, QSize, QByteArray, QEvent
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPalette
from PySide6.QtSvg import QSvgRenderer

from pathlib import Path


class NavBar(QToolBar):
    """导航栏组件
    
    位于窗口最左侧，包含垂直排列的图标按钮。
    点击图标可控制数据面板的展开/收起状态。
    """
    
    # 信号：请求切换数据面板状态
    toggle_data_panel = Signal()
    
    # 信号：请求切换图像面板
    toggle_image_panel = Signal()
    
    # 信号：请求打开设置
    open_settings = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 获取图标目录路径
        self._icon_dir = Path(__file__).parent.parent.parent / "assets" / "icons"
        
        # QToolBar 默认设置
        self.setOrientation(Qt.Vertical)  # 垂直排列
        self.setFixedWidth(60)
        self.setMovable(False)  # 不可移动
        self.setFloatable(False)  # 不可浮动
        self._icon_size = QSize(32, 32)
        self.setIconSize(self._icon_size)
        
        # 设置工具栏内容居中
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        
        # 记录按钮，便于主题变化时更新图标
        self._buttons = {}

        # 添加按钮
        self._btn_home = self._add_button("home", "主页")
        self._btn_home.setCheckable(True)
        self._btn_home.setChecked(True)
        self._btn_home.clicked.connect(self._on_home_clicked)
        
        self._btn_image = self._add_button("image", "图像")
        self._btn_image.clicked.connect(self.toggle_image_panel.emit)
        
        # 添加弹性空间，将设置按钮推到底部
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().horizontalPolicy(),
                            QSizePolicy.Expanding)
        spacer_action = QWidgetAction(self)
        spacer_action.setDefaultWidget(spacer)
        self.addAction(spacer_action)
        
        # 设置按钮在底部
        self._btn_settings = self._add_button("settings", "设置")
        self._btn_settings.clicked.connect(self.open_settings.emit)

    def _add_button(self, icon_name: str, tooltip: str) -> QToolButton:
        """添加按钮到工具栏"""
        btn = QToolButton()
        
        # 加载图标
        icon_path = self._icon_dir / f"{icon_name}.svg"
        if icon_path.exists():
            self._set_button_icon(btn, icon_path)
            btn.setIconSize(self._icon_size)
        
        btn.setToolTip(tooltip)
        # 按钮宽度与工具栏一致，高度 48px
        btn.setFixedSize(60, 48)
        btn.setAutoRaise(True)
        
        # 设置只显示图标
        btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
        
        action = QWidgetAction(self)
        action.setDefaultWidget(btn)
        self.addAction(action)

        self._buttons[icon_name] = btn
        
        return btn

    def _current_icon_color(self) -> QColor:
        """获取当前主题下图标颜色"""
        return self.palette().color(QPalette.ButtonText)

    def _set_button_icon(self, btn: QToolButton, icon_path: Path):
        """根据当前主题颜色渲染 SVG 图标"""
        try:
            svg_text = icon_path.read_text(encoding="utf-8")
        except OSError:
            btn.setIcon(QIcon(str(icon_path)))
            return

        color = self._current_icon_color()
        svg_text = svg_text.replace("currentColor", color.name())
        renderer = QSvgRenderer(QByteArray(svg_text.encode("utf-8")))
        dpr = self.devicePixelRatioF()
        pixel_size = QSize(
            max(1, int(self._icon_size.width() * dpr)),
            max(1, int(self._icon_size.height() * dpr)),
        )
        pixmap = QPixmap(pixel_size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        renderer.render(painter)
        painter.end()

        pixmap.setDevicePixelRatio(dpr)
        btn.setIcon(QIcon(pixmap))

    def _update_icons(self):
        """主题变化时更新所有按钮图标"""
        for icon_name, btn in self._buttons.items():
            icon_path = self._icon_dir / f"{icon_name}.svg"
            if icon_path.exists():
                self._set_button_icon(btn, icon_path)

    def changeEvent(self, event):
        """处理主题/调色板变化"""
        if event.type() in (QEvent.PaletteChange, QEvent.ApplicationPaletteChange):
            self._update_icons()
        super().changeEvent(event)
    
    def _on_home_clicked(self):
        """处理主页按钮点击
        
        行为逻辑：
        - 如果主页按钮已选中（数据面板展开），再次点击则收回数据面板，按钮保持选中
        - 如果主页按钮未选中（数据面板收起），点击则展开数据面板，按钮变为选中
        """
        # 发送切换信号，由 main_window 处理实际的面板展开/收起
        self.toggle_data_panel.emit()
        
    def set_panel_expanded(self, expanded: bool):
        """设置面板展开状态"""
        self._btn_home.setChecked(expanded)
