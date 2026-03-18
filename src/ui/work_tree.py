"""
工作树控件模块
"""

from pathlib import Path

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHeaderView,
    QMenu,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
)

from .icon_utils import get_icon_path, set_button_icon


class WorkTreeWidget(QTreeWidget):
    """图像处理工作树控件。"""

    STATUS_COLUMN_WIDTH = 32
    TREE_INDENTATION = 10
    STATUS_ICON_SIZE = QSize(16, 16)
    STATUS_TOOLTIPS = {
        "init": "初始化",
        "changed": "已变更",
        "done": "已完成",
        "error": "异常",
    }

    AVAILABLE_STEPS = [
        ("image_loader", "image_loader"),
        ("image_normalizer", "image_normalizer"),
        ("orientation_detector", "orientation_detector"),
        ("perspective_corrector", "perspective_corrector"),
        ("layout_detector", "layout_detector"),
        ("roi_extractor", "roi_extractor"),
        ("page_dewarper", "page_dewarper"),
        ("image_writer", "image_writer"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._root_item: QTreeWidgetItem | None = None
        self._init_ui()
        self._populate_tree()

    @property
    def root_item(self) -> QTreeWidgetItem:
        """返回 image process 根节点。"""
        return self._root_item

    def _init_ui(self):
        """初始化 UI。"""
        self.setColumnCount(2)
        self.setHeaderLabels(["名称", "状态"])
        self.setIndentation(self.TREE_INDENTATION)
        self.setFrameShape(QFrame.NoFrame)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.setEditTriggers(QTreeWidget.NoEditTriggers)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.header().resizeSection(1, self.STATUS_COLUMN_WIDTH)

    def set_tree_indentation(self, indentation: int) -> None:
        """设置每一级的缩进像素"""
        self.setIndentation(max(0, indentation))

    def _populate_tree(self):
        """初始化 image process 树结构。"""
        self.clear()
        self._root_item = QTreeWidgetItem(self, ["image process", ""])
        self._root_item.setExpanded(True)
        self._root_item.setData(0, Qt.UserRole, "root")
        self._set_status_button(self._root_item, "init")

        self.add_processing_step("image_loader")

    def _show_context_menu(self, pos):
        """显示右键菜单，仅允许在根节点下添加处理步骤。"""
        item = self.itemAt(pos)
        if item is None or item is not self._root_item:
            return

        menu = QMenu(self)
        add_menu = menu.addMenu("添加图像处理步骤")
        for step_key, label in self.AVAILABLE_STEPS:
            action = add_menu.addAction(label)
            action.triggered.connect(
                lambda checked=False, key=step_key: self.add_processing_step(key)
            )

        menu.exec(self.viewport().mapToGlobal(pos))

    def add_processing_step(self, step_name: str) -> QTreeWidgetItem:
        """在根节点下添加一个图像处理步骤。"""
        if self._root_item is None:
            raise RuntimeError("工作树根节点尚未初始化")

        item = QTreeWidgetItem(self._root_item, [step_name, ""])
        item.setData(0, Qt.UserRole, "step")
        item.setData(0, Qt.UserRole + 1, step_name)
        self._set_status_button(item, "init")
        self._root_item.setExpanded(True)
        return item

    def get_step_names(self) -> list[str]:
        """返回当前树中的步骤名称列表。"""
        if self._root_item is None:
            return []

        step_names: list[str] = []
        for index in range(self._root_item.childCount()):
            step_names.append(self._root_item.child(index).text(0))
        return step_names

    def set_item_status(self, item: QTreeWidgetItem, status: str) -> None:
        """统一更新节点状态。"""
        self._set_status_button(item, status)

    def _set_status_button(self, item: QTreeWidgetItem, status: str) -> None:
        """为节点设置状态按钮。"""
        button = QToolButton(self)
        button.setAutoRaise(True)
        button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        icon_path, tooltip = self._status_presentation(status)
        button.setProperty("status_icon_path", str(icon_path))
        self._apply_status_button_visual(button, inverted=False)
        button.setText("")
        button.setToolTip(tooltip)
        button.installEventFilter(self)
        self.setItemWidget(item, 1, button)

    def _status_presentation(self, status: str):
        """返回状态图标与文本。"""
        normalized_status = status if status in self.STATUS_TOOLTIPS else "init"
        return (get_icon_path(normalized_status), self.STATUS_TOOLTIPS[normalized_status])

    def _apply_status_button_visual(self, button: QToolButton, inverted: bool) -> None:
        """根据交互状态更新按钮的背景和图标颜色。"""
        icon_path = button.property("status_icon_path")
        if not icon_path:
            return

        foreground = button.palette().buttonText().color()
        background = button.palette().base().color()
        icon_color = background if inverted else foreground
        background_color = foreground.name() if inverted else "transparent"

        button.setStyleSheet(
            f"""
            QToolButton {{
                border: none;
                background: {background_color};
                padding: 0;
                margin: 0;
            }}
            QToolButton:hover {{
                border: none;
            }}
            QToolButton:pressed {{
                border: none;
            }}
            QToolButton:disabled {{
                border: none;
                background: {background_color};
            }}
            """
        )
        set_button_icon(button, Path(icon_path), self.STATUS_ICON_SIZE, color=icon_color)

    def eventFilter(self, watched, event):
        """在 hover/pressed 状态下切换为反色显示。"""
        if isinstance(watched, QToolButton) and watched.property("status_icon_path"):
            if event.type() in (QEvent.Enter, QEvent.MouseButtonPress):
                self._apply_status_button_visual(watched, inverted=True)
            elif event.type() in (QEvent.Leave, QEvent.MouseButtonRelease):
                self._apply_status_button_visual(watched, inverted=False)
        return super().eventFilter(watched, event)
