"""
工作树控件模块
"""

import re
from pathlib import Path

from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHeaderView,
    QMenu,
    QMessageBox,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
)

from core.pipeline import Pipeline, PipelineContext, StepRegistry
from core.pipeline.step import PipelineStep

from .icon_utils import get_icon_path, set_button_icon


class WorkTreeWidget(QTreeWidget):
    """图像处理工作树控件。"""

    step_run_finished = Signal(object, object)

    STATUS_COLUMN_WIDTH = 32
    TREE_INDENTATION = 10
    STATUS_ICON_SIZE = QSize(16, 16)
    STATUS_TOOLTIPS = {
        "init": "初始化",
        "ready": "已完成准备",
        "changed": "已变更",
        "done": "已完成",
        "error": "异常",
    }

    AVAILABLE_STEPS = [
        ("ImageLoader", "image_loader"),
        ("ImageNormalizer", "image_normalizer"),
        ("OrientationDetector", "orientation_detector"),
        ("PerspectiveCorrector", "perspective_corrector"),
        ("LayoutDetector", "layout_detector"),
        ("ROIExtractor", "roi_extractor"),
        ("PageDewarper", "page_dewarper"),
        ("ImageWriter", "image_writer"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pipeline: Pipeline | None = None
        self._root_item: QTreeWidgetItem | None = None
        self._runtime_context = PipelineContext()
        self._init_ui()

    @property
    def root_item(self) -> QTreeWidgetItem:
        """返回 image process 根节点。"""
        return self._root_item

    @property
    def pipeline(self) -> Pipeline | None:
        """返回当前绑定的 pipeline。"""
        return self._pipeline

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

    def set_pipeline(self, pipeline: Pipeline) -> None:
        """使用真实 pipeline 重建树结构。"""
        self._pipeline = pipeline
        self._runtime_context = PipelineContext()
        self.clear()
        self._root_item = QTreeWidgetItem(self, [pipeline.name, ""])
        self._root_item.setExpanded(True)
        self._root_item.setData(0, Qt.UserRole, "pipeline")
        self._root_item.setData(0, Qt.UserRole + 1, pipeline)
        self._set_status_button(self._root_item, "init")

        for step in pipeline.steps:
            self._create_step_item(step)

    def _show_context_menu(self, pos):
        """显示右键菜单，仅允许在根节点下添加处理步骤。"""
        item = self.itemAt(pos)
        if item is None or item is not self._root_item:
            return

        menu = QMenu(self)
        add_menu = menu.addMenu("添加图像处理步骤")
        for step_type, label in self.AVAILABLE_STEPS:
            action = add_menu.addAction(label)
            action.triggered.connect(
                lambda checked=False, key=step_type, name=label: self.add_processing_step(
                    key,
                    step_name=name,
                )
            )

        menu.exec(self.viewport().mapToGlobal(pos))

    def add_processing_step(
        self,
        step_type: str,
        *,
        step_name: str | None = None,
    ) -> QTreeWidgetItem:
        """在根节点下添加一个图像处理步骤。"""
        if self._root_item is None or self._pipeline is None:
            raise RuntimeError("工作树根节点尚未初始化")

        step = StepRegistry.create(
            step_type,
            name=step_name or self._default_step_name(step_type),
        )
        self._pipeline.add_step(step)
        return self._create_step_item(step)

    def _create_step_item(self, step: PipelineStep) -> QTreeWidgetItem:
        """为 pipeline step 创建树节点。"""
        if self._root_item is None:
            raise RuntimeError("工作树根节点尚未初始化")

        item = QTreeWidgetItem(self._root_item, [step.name, ""])
        item.setData(0, Qt.UserRole, "step")
        item.setData(0, Qt.UserRole + 1, step)
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

    def get_item_payload(self, item: QTreeWidgetItem | None):
        """返回树节点关联的数据对象。"""
        if item is None:
            return None
        return item.data(0, Qt.UserRole + 1)

    def set_item_status(self, item: QTreeWidgetItem, status: str) -> None:
        """统一更新节点状态。"""
        self._set_status_button(item, status)

    def _set_status_button(self, item: QTreeWidgetItem, status: str) -> None:
        """为节点设置状态按钮。"""
        button = QToolButton(self)
        button.setAutoRaise(True)
        button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        normalized_status = status if status in self.STATUS_TOOLTIPS else "init"
        icon_path, tooltip = self._status_presentation(normalized_status)
        button.setProperty("status", normalized_status)
        button.setProperty("status_icon_path", str(icon_path))
        self._apply_status_button_visual(button, inverted=False)
        button.setText("")
        button.setToolTip(tooltip)
        button.installEventFilter(self)
        button.clicked.connect(lambda checked=False, current_item=item: self._on_status_button_clicked(current_item))
        self.setItemWidget(item, 1, button)

    def _on_status_button_clicked(self, item: QTreeWidgetItem) -> None:
        """处理状态按钮点击。"""
        step = self.get_item_payload(item)
        if not isinstance(step, PipelineStep):
            return

        button = self.itemWidget(item, 1)
        current_status = button.property("status") if button is not None else "init"
        if current_status == "init":
            if not self._prepare_step(item, step):
                return

        self._run_step(item, step)

    def _prepare_step(self, item: QTreeWidgetItem, step: PipelineStep) -> bool:
        """执行 step 的输入准备检查。"""
        inputs_check = getattr(step, "inputs_check", None)
        if callable(inputs_check):
            messages = inputs_check()
            if messages:
                QMessageBox.warning(self, "输入检查", "\n".join(messages))
                self.set_item_status(item, "init")
                return False

        is_ready = getattr(step, "is_ready", None)
        if callable(is_ready):
            ready = bool(is_ready())
            self.set_item_status(item, "ready" if ready else "init")
            return ready

        self.set_item_status(item, "ready")
        return True

    def _run_step(self, item: QTreeWidgetItem, step: PipelineStep) -> None:
        """执行单个 step 并同步状态。"""
        try:
            step.validate(self._runtime_context)
            step.run(self._runtime_context)
        except Exception as exc:
            self.set_item_status(item, "error")
            QMessageBox.warning(self, "执行失败", str(exc))
            return

        self.set_item_status(item, "done")
        self.step_run_finished.emit(step, self._runtime_context)

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

    def _default_step_name(self, step_type: str) -> str:
        """从步骤类型推导默认节点名。"""
        normalized = re.sub(r"(?<!^)(?=[A-Z])", "_", step_type).lower()
        return normalized
