"""
属性表控件模块
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QColorDialog,
    QFileDialog,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedLayout,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)


@dataclass(frozen=True)
class PropertyRow:
    """属性表中的单行描述。"""

    label: str
    key: str | None
    value: Any
    display_text: str
    source: str
    editable: bool
    editor: str
    editor_options: dict[str, Any]
    description: str = ""


@dataclass(frozen=True)
class PropertyEditorBinding:
    """单元格编辑器渲染结果。"""

    item: QTableWidgetItem | None = None
    widget: QWidget | None = None


EditorBuilder = Callable[[QWidget, PropertyRow, Callable[[Any], None]], PropertyEditorBinding]


class EditablePathLabel(QLabel):
    """支持双击进入编辑态的路径标签。"""

    double_clicked = Signal()

    def mouseDoubleClickEvent(self, event) -> None:
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)


class ReadonlyPropertyEditor:
    """只读属性编辑器。"""

    @classmethod
    def build(
        cls,
        parent: QWidget,
        row: PropertyRow,
        on_value_changed: Callable[[Any], None],
    ) -> PropertyEditorBinding:
        del cls, parent, on_value_changed
        item = QTableWidgetItem(row.display_text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        if row.description:
            item.setToolTip(row.description)
        return PropertyEditorBinding(item=item)


class TextPropertyEditor:
    """文本属性编辑器。"""

    @classmethod
    def build(
        cls,
        parent: QWidget,
        row: PropertyRow,
        on_value_changed: Callable[[Any], None],
    ) -> PropertyEditorBinding:
        del cls, parent, on_value_changed
        tooltip = row.description
        if row.editor not in {"text", "readonly"} and row.description:
            tooltip = f"{row.description}\n编辑器 {row.editor} 尚未注册，已回退为文本输入。"
        elif row.editor not in {"text", "readonly"}:
            tooltip = f"编辑器 {row.editor} 尚未注册，已回退为文本输入。"

        item = QTableWidgetItem(row.display_text)
        if not row.editable:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        if tooltip:
            item.setToolTip(tooltip)
        return PropertyEditorBinding(item=item)


class FilePropertyEditor(QWidget):
    """文件路径属性编辑器。"""

    def __init__(
        self,
        parent: QWidget,
        row: PropertyRow,
        on_value_changed: Callable[[Any], None],
    ) -> None:
        super().__init__(parent)
        self._row = row
        self._on_value_changed = on_value_changed
        self._current_path = str(row.value or "")
        self._last_valid_path = self._current_path if _is_valid_file_path(self._current_path) else ""
        self._is_finishing_edit = False

        self._layout = _create_editor_layout(self)

        self._display_stack = QWidget(self)
        self._stack_layout = QStackedLayout(self._display_stack)
        self._stack_layout.setContentsMargins(0, 0, 0, 0)

        self._label = EditablePathLabel("", self._display_stack)
        self._label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._stack_layout.addWidget(self._label)

        self._line_edit = QLineEdit(self._display_stack)
        self._line_edit.hide()
        self._stack_layout.addWidget(self._line_edit)
        self._layout.addWidget(self._display_stack, 1)

        self._button = _create_editor_button("浏览", self, enabled=row.editable)
        self._layout.addWidget(self._button, 0)

        self._label.double_clicked.connect(self._enter_edit_mode)
        self._line_edit.returnPressed.connect(self._finish_editing)
        self._line_edit.editingFinished.connect(self._finish_editing)
        self._button.clicked.connect(self._choose_file)

        self._restore_display(self._last_valid_path or self._current_path, valid=bool(self._last_valid_path))

    @classmethod
    def build(
        cls,
        parent: QWidget,
        row: PropertyRow,
        on_value_changed: Callable[[Any], None],
    ) -> PropertyEditorBinding:
        return PropertyEditorBinding(widget=cls(parent, row, on_value_changed))

    def _restore_display(self, path: str, *, valid: bool) -> None:
        self._label.setText(_display_file_text(path))
        self._label.setToolTip(path or self._row.description)
        _set_label_pending(self._label, not valid)
        self._stack_layout.setCurrentWidget(self._label)

    def _enter_edit_mode(self) -> None:
        if not self._row.editable:
            return
        self._line_edit.setText(self._last_valid_path or self._current_path)
        self._stack_layout.setCurrentWidget(self._line_edit)
        self._line_edit.setFocus()
        self._line_edit.selectAll()

    def _commit_path(self, path: str) -> None:
        self._current_path = path
        if _is_valid_file_path(path):
            self._last_valid_path = path
            self._restore_display(path, valid=True)
            self._on_value_changed(path)
            return

        QMessageBox.warning(self, "路径无效", "请输入有效且可读取的文件路径。")
        self._restore_display(self._last_valid_path, valid=bool(self._last_valid_path))

    def _finish_editing(self) -> None:
        if self._is_finishing_edit:
            return
        self._is_finishing_edit = True
        new_path = self._line_edit.text().strip()
        self._stack_layout.setCurrentWidget(self._label)
        if not new_path:
            QMessageBox.warning(self, "路径无效", "请输入有效且可读取的文件路径。")
            self._restore_display(self._last_valid_path, valid=bool(self._last_valid_path))
        else:
            self._commit_path(new_path)
        self._is_finishing_edit = False

    def _selected_path_from_dialog(self) -> str:
        options = dict(self._row.editor_options)
        title = str(options.get("title", "选择文件"))
        file_filter = str(options.get("filter", "所有文件 (*)"))
        mode = str(options.get("mode", "open_file"))

        if mode == "directory":
            return QFileDialog.getExistingDirectory(self, title, self._current_path)
        if mode == "save_file":
            selected, _ = QFileDialog.getSaveFileName(self, title, self._current_path, file_filter)
            return selected
        selected, _ = QFileDialog.getOpenFileName(self, title, self._current_path, file_filter)
        return selected

    def _choose_file(self) -> None:
        selected = self._selected_path_from_dialog()
        if selected:
            self._commit_path(selected)


class ColorPropertyEditor(QWidget):
    """颜色属性编辑器。"""

    def __init__(
        self,
        parent: QWidget,
        row: PropertyRow,
        on_value_changed: Callable[[Any], None],
    ) -> None:
        super().__init__(parent)
        self._row = row
        self._on_value_changed = on_value_changed
        self._layout = _create_editor_layout(self)

        self._swatch = QLabel(self)
        self._swatch.setFixedWidth(18)
        self._swatch.setFrameShape(QFrame.StyledPanel)
        self._swatch.setLineWidth(1)
        self._layout.addWidget(self._swatch)

        self._label = QLabel(_display_color_text(row.value), self)
        self._label.setToolTip(_display_color_text(row.value) or row.description)
        self._label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._layout.addWidget(self._label, 1)

        self._button = _create_editor_button("选择", self, enabled=row.editable)
        self._button.clicked.connect(self._choose_color)
        self._layout.addWidget(self._button, 0)
        self._update_swatch(row.value)

    @classmethod
    def build(
        cls,
        parent: QWidget,
        row: PropertyRow,
        on_value_changed: Callable[[Any], None],
    ) -> PropertyEditorBinding:
        return PropertyEditorBinding(widget=cls(parent, row, on_value_changed))

    def _update_swatch(self, color_value: Any) -> None:
        color = QColor(str(color_value or ""))
        if color.isValid():
            self._swatch.setStyleSheet(f"background-color: {color.name(QColor.HexArgb)};")
        else:
            self._swatch.setStyleSheet("")

    def _choose_color(self) -> None:
        options = dict(self._row.editor_options)
        allow_alpha = bool(options.get("allow_alpha", False))
        initial = QColor(str(self._row.value or ""))
        if not initial.isValid():
            initial = QColor("#000000")

        chosen = QColorDialog.getColor(initial, self, str(options.get("title", "选择颜色")))
        if not chosen.isValid():
            return

        color_text = chosen.name(QColor.HexArgb if allow_alpha else QColor.HexRgb)
        self._update_swatch(color_text)
        self._label.setText(color_text)
        self._label.setToolTip(color_text)
        self._on_value_changed(color_text)


class BoolPropertyEditor(QCheckBox):
    """布尔属性编辑器。"""

    def __init__(
        self,
        parent: QWidget,
        row: PropertyRow,
        on_value_changed: Callable[[Any], None],
    ) -> None:
        super().__init__(parent)
        self.setChecked(bool(row.value))
        self.setEnabled(row.editable)
        if row.description:
            self.setToolTip(row.description)
        self.stateChanged.connect(lambda state: on_value_changed(state == Qt.Checked))

    @classmethod
    def build(
        cls,
        parent: QWidget,
        row: PropertyRow,
        on_value_changed: Callable[[Any], None],
    ) -> PropertyEditorBinding:
        return PropertyEditorBinding(widget=cls(parent, row, on_value_changed))


class PropertyEditorFactory:
    """按编辑器类型创建属性编辑控件。"""

    _builders: dict[str, EditorBuilder] = {}

    @classmethod
    def register(cls, editor_type: str, builder: EditorBuilder) -> None:
        cls._builders[editor_type] = builder

    @classmethod
    def create(
        cls,
        editor_type: str,
        parent: QWidget,
        row: PropertyRow,
        on_value_changed: Callable[[Any], None],
    ) -> PropertyEditorBinding:
        builder = cls._builders.get(editor_type)
        if builder is None:
            fallback_type = "text" if row.editable else "readonly"
            builder = cls._builders[fallback_type]
        return builder(parent, row, on_value_changed)


def _display_file_text(path_value: Any) -> str:
    if not path_value:
        return ""
    return Path(str(path_value)).name


def _display_color_text(color_value: Any) -> str:
    if not color_value:
        return ""
    return str(color_value)


def _create_editor_layout(container: QWidget) -> QHBoxLayout:
    layout = QHBoxLayout(container)
    layout.setContentsMargins(6, 0, 0, 0)
    layout.setSpacing(6)
    return layout

def _create_editor_button(text: str, parent: QWidget, *, enabled: bool) -> QPushButton:
    button = QPushButton(text, parent)
    button.setEnabled(enabled)
    button_font_metrics = QFontMetrics(button.font())
    button.setFixedWidth(button_font_metrics.horizontalAdvance("三个字") + 16)
    button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
    button.setMinimumHeight(0)
    return button


def _set_label_pending(label: QLabel, pending: bool) -> None:
    if pending:
        label.setStyleSheet("border: none; border-bottom: 1px solid palette(text);")
    else:
        label.setStyleSheet("border: none;")


def _is_valid_file_path(path: str) -> bool:
    return bool(path) and Path(path).exists() and Path(path).is_file() and os.access(path, os.R_OK)


PropertyEditorFactory.register("readonly", ReadonlyPropertyEditor.build)
PropertyEditorFactory.register("text", TextPropertyEditor.build)
PropertyEditorFactory.register("file", FilePropertyEditor.build)
PropertyEditorFactory.register("color", ColorPropertyEditor.build)
PropertyEditorFactory.register("bool", BoolPropertyEditor.build)


class PropertyTableWidget(QTableWidget):
    """展示属性键值对的表格控件。"""

    value_changed = Signal(str, object)
    description_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._prop_column_ratio = 100 / 250
        self._syncing_prop_columns = False
        self._is_refreshing = False
        self._rows: list[PropertyRow] = []
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化表格外观与交互。"""
        self.setColumnCount(2)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalHeaderLabels(["属性", "值"])
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)

        header = self.horizontalHeader()
        header.setSectionsClickable(False)
        header.setHighlightSections(False)
        header.setMinimumSectionSize(10)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.sectionResized.connect(self._on_prop_section_resized)

        self.itemChanged.connect(self._on_item_changed)
        self.currentCellChanged.connect(self._on_current_cell_changed)
        self.viewport().installEventFilter(self)

    def set_properties(self, properties: list[PropertyRow]) -> None:
        """刷新表格属性内容。"""
        self._rows = list(properties)
        self._is_refreshing = True
        try:
            self.clearContents()
            self.setRowCount(len(self._rows))

            for row_index, row in enumerate(self._rows):
                self._set_name_item(row_index, row)
                self._set_value_cell(row_index, row)
        finally:
            self._is_refreshing = False

    def eventFilter(self, watched: QObject, event: QEvent):
        """在表格尺寸变化时同步两列总宽。"""
        if watched is self.viewport() and event.type() == QEvent.Resize:
            self.sync_columns_to_width()
        row_index = watched.property("property_row_index") if isinstance(watched, QObject) else None
        if isinstance(row_index, int) and event.type() == QEvent.MouseButtonPress:
            self.selectRow(row_index)
            self._emit_description_for_row(row_index)
        return super().eventFilter(watched, event)

    def _set_name_item(self, row_index: int, row: PropertyRow) -> None:
        prop_item = QTableWidgetItem(row.label)
        prop_item.setFlags(prop_item.flags() & ~Qt.ItemIsEditable)
        if row.description:
            prop_item.setToolTip(row.description)
        self.setItem(row_index, 0, prop_item)

    def _set_value_cell(self, row_index: int, row: PropertyRow) -> None:
        def handle_value_changed(value: Any) -> None:
            if self._is_refreshing or not row.key:
                return
            self.value_changed.emit(row.key, value)

        binding = PropertyEditorFactory.create(row.editor, self, row, handle_value_changed)
        if binding.item is not None:
            self.setItem(row_index, 1, binding.item)
        elif binding.widget is not None:
            binding.widget.installEventFilter(self)
            binding.widget.setProperty("property_row_index", row_index)
            for child in binding.widget.findChildren(QWidget):
                child.installEventFilter(self)
                child.setProperty("property_row_index", row_index)
            self.setCellWidget(row_index, 1, binding.widget)
        else:
            self.setItem(row_index, 1, QTableWidgetItem(row.display_text))

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._is_refreshing:
            return
        if item.column() != 1:
            return
        row_index = item.row()
        if not 0 <= row_index < len(self._rows):
            return

        row = self._rows[row_index]
        if not row.editable or not row.key:
            return
        self.value_changed.emit(row.key, item.text())

    def _on_current_cell_changed(
        self,
        current_row: int,
        current_column: int,
        previous_row: int,
        previous_column: int,
    ) -> None:
        del current_column, previous_row, previous_column
        self._emit_description_for_row(current_row)

    def _emit_description_for_row(self, row_index: int) -> None:
        if not 0 <= row_index < len(self._rows):
            self.description_changed.emit("")
            return
        self.description_changed.emit(self._rows[row_index].description)

    def _on_prop_section_resized(self, logical_index: int, old_size: int, new_size: int) -> None:
        """拖动任一列表头时，同步另一列宽度。"""
        del old_size
        if self._syncing_prop_columns:
            return

        total_width = self.property_total_width()
        if total_width < 20:
            return

        if logical_index == 0:
            first_width = new_size
        elif logical_index == 1:
            first_width = total_width - new_size
        else:
            return

        self.apply_column_widths(first_width, total_width=total_width)

    def sync_columns_to_width(self) -> None:
        """在表格宽度变化时按当前比例重算两列宽度。"""
        total_width = self.property_total_width()
        if total_width < 20:
            return

        desired_first_width = round(total_width * self._prop_column_ratio)
        self.apply_column_widths(desired_first_width, total_width=total_width)

    def apply_column_widths(self, first_width: int, *, total_width: int | None = None) -> None:
        """按总宽和最小宽度约束，统一设置两列宽度。"""
        active_total_width = total_width if total_width is not None else self.property_total_width()
        if active_total_width < 20:
            return

        clamped_first_width = max(10, min(first_width, active_total_width - 10))
        second_width = active_total_width - clamped_first_width

        self._syncing_prop_columns = True
        try:
            self.setColumnWidth(0, clamped_first_width)
            self.setColumnWidth(1, second_width)
        finally:
            self._syncing_prop_columns = False

        self._prop_column_ratio = clamped_first_width / active_total_width

    def property_total_width(self) -> int:
        """返回当前两列可分配的总宽度。"""
        return self.viewport().width()
