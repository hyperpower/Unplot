"""
PropertyTableWidget 测试模块。
"""

import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QLineEdit, QPushButton

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.image_process import ImageLoader, ImageNormalizer
from core.pipeline import Pipeline
from ui.data_panel import DataPanel
from ui.property_table import (
    BoolPropertyEditor,
    ColorPropertyEditor,
    EditablePathLabel,
    FilePropertyEditor,
    PropertyEditorFactory,
    PropertyRow,
    PropertyTableWidget,
)


@pytest.fixture(scope="function")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(scope="function")
def property_table(app):
    return PropertyTableWidget()


class TestPropertyTableWidget:
    def test_factory_returns_item_binding_for_readonly_editor(self, property_table):
        binding = PropertyEditorFactory.create(
            "readonly",
            property_table,
            PropertyRow(
                label="配置.status",
                key=None,
                value="已执行",
                display_text="已执行",
                source="config",
                editable=False,
                editor="readonly",
                editor_options={},
                description="运行状态。",
            ),
            lambda value: None,
        )

        assert binding.item is not None
        assert binding.widget is None

    def test_factory_returns_item_binding_for_text_editor(self, property_table):
        binding = PropertyEditorFactory.create(
            "text",
            property_table,
            PropertyRow(
                label="配置.name",
                key="name",
                value="loader",
                display_text="loader",
                source="config",
                editable=True,
                editor="text",
                editor_options={},
            ),
            lambda value: None,
        )

        assert binding.item is not None
        assert binding.widget is None

    def test_factory_returns_widget_binding_for_widget_editors(self, property_table):
        file_binding = PropertyEditorFactory.create(
            "file",
            property_table,
            PropertyRow(
                label="输入.path",
                key="path",
                value="",
                display_text="",
                source="port",
                editable=True,
                editor="file",
                editor_options={},
            ),
            lambda value: None,
        )
        color_binding = PropertyEditorFactory.create(
            "color",
            property_table,
            PropertyRow(
                label="配置.color",
                key="color",
                value="#112233",
                display_text="#112233",
                source="config",
                editable=True,
                editor="color",
                editor_options={},
            ),
            lambda value: None,
        )
        bool_binding = PropertyEditorFactory.create(
            "bool",
            property_table,
            PropertyRow(
                label="配置.use_clahe",
                key="use_clahe",
                value=True,
                display_text="是",
                source="config",
                editable=True,
                editor="bool",
                editor_options={},
            ),
            lambda value: None,
        )

        assert isinstance(file_binding.widget, FilePropertyEditor)
        assert isinstance(color_binding.widget, ColorPropertyEditor)
        assert isinstance(bool_binding.widget, BoolPropertyEditor)

    def test_file_editor_renders_composite_cell(self, property_table):
        property_table.set_properties(
            [
                PropertyRow(
                    label="配置.path",
                    key="path",
                    value="/tmp/example/image_001.jpg",
                    display_text="image_001.jpg",
                    source="config",
                    editable=True,
                    editor="file",
                    editor_options={},
                )
            ]
        )

        cell_widget = property_table.cellWidget(0, 1)

        assert cell_widget is not None
        assert cell_widget.findChild(EditablePathLabel).text() == "image_001.jpg"
        assert cell_widget.findChild(QPushButton).text() == "浏览"

    def test_file_editor_shows_pending_underline_when_path_missing(self, property_table):
        property_table.set_properties(
            [
                PropertyRow(
                    label="配置.path",
                    key="path",
                    value="",
                    display_text="",
                    source="config",
                    editable=True,
                    editor="file",
                    editor_options={},
                )
            ]
        )

        cell_widget = property_table.cellWidget(0, 1)
        label = cell_widget.findChild(EditablePathLabel)

        assert "border-bottom" in label.styleSheet()

    def test_bool_editor_emits_value_changed(self, property_table):
        captured = []
        property_table.value_changed.connect(lambda key, value: captured.append((key, value)))
        property_table.set_properties(
            [
                PropertyRow(
                    label="配置.use_clahe",
                    key="use_clahe",
                    value=True,
                    display_text="是",
                    source="config",
                    editable=True,
                    editor="bool",
                    editor_options={},
                )
            ]
        )

        checkbox = property_table.cellWidget(0, 1)
        assert isinstance(checkbox, QCheckBox)

        checkbox.setChecked(False)

        assert captured == [("use_clahe", False)]

    def test_unknown_editor_falls_back_to_text_item(self, property_table):
        property_table.set_properties(
            [
                PropertyRow(
                    label="配置.max_dimension",
                    key="max_dimension",
                    value=1600,
                    display_text="1600",
                    source="config",
                    editable=True,
                    editor="number",
                    editor_options={"min": 1},
                )
            ]
        )

        value_item = property_table.item(0, 1)

        assert value_item is not None
        assert property_table.cellWidget(0, 1) is None
        assert bool(value_item.flags() & Qt.ItemIsEditable)

    def test_unknown_editor_fallback_keeps_tooltip_message(self, property_table):
        property_table.set_properties(
            [
                PropertyRow(
                    label="配置.max_dimension",
                    key="max_dimension",
                    value=1600,
                    display_text="1600",
                    source="config",
                    editable=True,
                    editor="number",
                    editor_options={"min": 1},
                    description="最大边长度。",
                )
            ]
        )

        value_item = property_table.item(0, 1)

        assert value_item is not None
        assert "编辑器 number 尚未注册" in value_item.toolTip()

    def test_color_editor_updates_value_after_dialog_selection(self, property_table):
        captured = []
        property_table.value_changed.connect(lambda key, value: captured.append((key, value)))
        property_table.set_properties(
            [
                PropertyRow(
                    label="配置.color",
                    key="color",
                    value="#112233",
                    display_text="#112233",
                    source="config",
                    editable=True,
                    editor="color",
                    editor_options={},
                )
            ]
        )

        cell_widget = property_table.cellWidget(0, 1)
        button = cell_widget.findChild(QPushButton)
        labels = cell_widget.findChildren(QLabel)
        label = labels[1]

        with patch("ui.property_table.QColorDialog.getColor", return_value=QColor("#abcdef")):
            button.click()

        assert label.text() == "#abcdef"
        assert captured == [("color", "#abcdef")]

    def test_file_editor_browse_updates_label_and_removes_underline(self, property_table):
        captured = []
        selected_path = "/tmp/example/loaded.png"
        property_table.value_changed.connect(lambda key, value: captured.append((key, value)))
        property_table.set_properties(
            [
                PropertyRow(
                    label="配置.path",
                    key="path",
                    value="",
                    display_text="",
                    source="config",
                    editable=True,
                    editor="file",
                    editor_options={},
                )
            ]
        )

        cell_widget = property_table.cellWidget(0, 1)
        label = cell_widget.findChild(EditablePathLabel)
        button = cell_widget.findChild(QPushButton)

        with patch("ui.property_table.QFileDialog.getOpenFileName", return_value=(selected_path, "")), patch(
            "ui.property_table._is_valid_file_path", return_value=True
        ):
            button.click()

        assert label.text() == "loaded.png"
        assert label.toolTip() == selected_path
        assert "border-bottom" not in label.styleSheet()
        assert captured == [("path", selected_path)]

    def test_file_editor_double_click_shows_line_edit_with_full_path(self, property_table):
        current_path = "/tmp/example/current.png"
        with patch("ui.property_table._is_valid_file_path", return_value=True):
            property_table.set_properties(
                [
                    PropertyRow(
                        label="配置.path",
                        key="path",
                        value=current_path,
                        display_text="current.png",
                        source="config",
                        editable=True,
                        editor="file",
                        editor_options={},
                    )
                ]
            )

        cell_widget = property_table.cellWidget(0, 1)
        label = cell_widget.findChild(EditablePathLabel)
        line_edit = cell_widget.findChild(QLineEdit)

        label.double_clicked.emit()

        assert line_edit.isHidden() is False
        assert line_edit.text() == current_path

    def test_file_editor_enter_commits_valid_path(self, property_table):
        captured = []
        new_path = "/tmp/example/typed.png"
        property_table.value_changed.connect(lambda key, value: captured.append((key, value)))
        property_table.set_properties(
            [
                PropertyRow(
                    label="配置.path",
                    key="path",
                    value="",
                    display_text="",
                    source="config",
                    editable=True,
                    editor="file",
                    editor_options={},
                )
            ]
        )

        cell_widget = property_table.cellWidget(0, 1)
        label = cell_widget.findChild(EditablePathLabel)
        line_edit = cell_widget.findChild(QLineEdit)

        label.double_clicked.emit()
        line_edit.setText(new_path)
        with patch("ui.property_table._is_valid_file_path", return_value=True):
            line_edit.returnPressed.emit()

        assert label.text() == "typed.png"
        assert label.toolTip() == new_path
        assert line_edit.isVisible() is False
        assert "border-bottom" not in label.styleSheet()
        assert captured == [("path", new_path)]

    def test_file_editor_invalid_manual_input_restores_old_value(self, property_table):
        old_path = "/tmp/example/old.png"
        captured = []
        property_table.value_changed.connect(lambda key, value: captured.append((key, value)))
        with patch("ui.property_table._is_valid_file_path", return_value=True):
            property_table.set_properties(
                [
                    PropertyRow(
                        label="配置.path",
                        key="path",
                        value=old_path,
                        display_text="old.png",
                        source="config",
                        editable=True,
                        editor="file",
                        editor_options={},
                    )
                ]
            )

        cell_widget = property_table.cellWidget(0, 1)
        label = cell_widget.findChild(EditablePathLabel)
        line_edit = cell_widget.findChild(QLineEdit)

        label.double_clicked.emit()
        line_edit.setText("/tmp/example/invalid.png")
        with patch("ui.property_table._is_valid_file_path", return_value=False), patch(
            "ui.property_table.QMessageBox.warning"
        ) as warning:
            line_edit.returnPressed.emit()

        assert warning.called is True
        assert label.text() == "old.png"
        assert label.toolTip() == old_path
        assert line_edit.isVisible() is False
        assert captured == []

    def test_selecting_row_emits_description(self, property_table):
        captured = []
        property_table.description_changed.connect(captured.append)
        property_table.set_properties(
            [
                PropertyRow(
                    label="输入.path",
                    key="path",
                    value="/tmp/example/image_001.jpg",
                    display_text="image_001.jpg",
                    source="port",
                    editable=True,
                    editor="file",
                    editor_options={},
                    description="用户必须直接提供待加载的图像文件路径。",
                )
            ]
        )

        property_table.setCurrentCell(0, 0)

        assert captured[-1] == "用户必须直接提供待加载的图像文件路径。"


class TestDataPanelPropertyEditing:
    def test_data_panel_writes_back_bool_config_and_syncs_step(self, app):
        panel = DataPanel()
        step = ImageNormalizer()

        panel._show_object_properties(step)

        target_row = next(
            row for row in range(panel.prop_widget.rowCount())
            if panel.prop_widget.item(row, 0).text() == "配置.use_clahe"
        )
        checkbox = panel.prop_widget.cellWidget(target_row, 1)
        assert isinstance(checkbox, QCheckBox)

        checkbox.setChecked(False)

        assert step.config["use_clahe"] is False
        assert step.use_clahe is False

    def test_image_loader_path_row_uses_file_editor(self, app):
        panel = DataPanel()
        step = ImageLoader(config={"path": "/tmp/example/input.png"})

        panel._show_object_properties(step)

        target_row = next(
            row for row in range(panel.prop_widget.rowCount())
            if panel.prop_widget.item(row, 0).text() == "输入.path"
        )
        cell_widget = panel.prop_widget.cellWidget(target_row, 1)

        assert cell_widget is not None
        assert cell_widget.findChild(QLabel).text() == "input.png"
        assert cell_widget.findChild(QPushButton).text() == "浏览"

    def test_image_loader_input_row_does_not_show_description_in_value_column(self, app):
        panel = DataPanel()
        step = ImageLoader(config={"path": "/tmp/example/input.png"})

        panel._show_object_properties(step)

        target_row = next(
            row for row in range(panel.prop_widget.rowCount())
            if panel.prop_widget.item(row, 0).text() == "输出.image"
        )

        assert panel.prop_widget.item(target_row, 1).text() == "未加载"

    def test_image_loader_path_change_updates_work_tree_status_to_ready(self, app):
        panel = DataPanel()
        image_path = Path(__file__).parent / "images" / "image_001.jpg"
        step = ImageLoader(name="image_loader")
        pipeline = Pipeline(name="image process pipeline", steps=[step])

        panel.set_pipeline(pipeline)
        step_item = panel.tree_widget.root_item.child(0)
        panel.tree_widget.setCurrentItem(step_item)

        panel._on_property_value_changed("path", str(image_path))

        step_button = panel.tree_widget.itemWidget(step_item, 1)
        assert step_button.toolTip() == "已完成准备"

    def test_image_loader_run_refreshes_property_table_config_values(self, app):
        panel = DataPanel()
        image_path = Path(__file__).parent / "images" / "image_001.jpg"
        step = ImageLoader(name="image_loader", config={"path": str(image_path)})
        pipeline = Pipeline(name="image process pipeline", steps=[step])

        panel.set_pipeline(pipeline)
        step_item = panel.tree_widget.root_item.child(0)
        panel.tree_widget.setCurrentItem(step_item)

        panel.tree_widget.itemWidget(step_item, 1).click()

        rows = {
            panel.prop_widget.item(row, 0).text(): panel.prop_widget.item(row, 1).text()
            for row in range(panel.prop_widget.rowCount())
            if panel.prop_widget.item(row, 0) is not None and panel.prop_widget.item(row, 1) is not None
        }

        assert rows["输出.image"].startswith("已加载: ")
        assert rows["配置.status"] == "已执行"
        assert rows["配置.width"] != "None"
        assert rows["配置.height"] != "None"

    def test_image_loader_output_memory_display_uses_mb_for_large_images(self, app):
        step = ImageLoader()
        step._image = np.zeros((600, 600, 3), dtype=np.uint8)

        assert step.format_output_display("image").endswith("MB")
