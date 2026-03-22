"""
WorkTreeWidget 测试模块。
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QApplication, QToolButton

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ui.work_tree import WorkTreeWidget
from core.image_process import ImageLoader, ImageNormalizer  # noqa: F401
from core.pipeline import Pipeline


@pytest.fixture(scope="function")
def app():
    """创建 Qt 应用程序实例。"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(scope="function")
def work_tree(app):
    """创建 WorkTreeWidget。"""
    widget = WorkTreeWidget()
    widget.set_pipeline(Pipeline(name="image process"))
    return widget


class TestWorkTreeWidget:
    """工作树组件测试。"""

    def test_has_single_root_node(self, work_tree):
        assert work_tree.topLevelItemCount() == 1
        assert work_tree.root_item.text(0) == "image process"

    def test_default_pipeline_has_no_steps(self, work_tree):
        assert work_tree.root_item.childCount() == 0
        assert work_tree.get_step_names() == []

    def test_status_button_exists_for_root(self, work_tree):
        root_button = work_tree.itemWidget(work_tree.root_item, 1)

        assert isinstance(root_button, QToolButton)
        assert root_button.text() == ""
        assert root_button.toolTip() == "初始化"
        assert root_button.toolButtonStyle() == Qt.ToolButtonIconOnly

    def test_status_button_has_borderless_style(self, work_tree):
        root_button = work_tree.itemWidget(work_tree.root_item, 1)
        stylesheet = root_button.styleSheet()

        assert "border: none" in stylesheet
        assert "background: transparent" in stylesheet

    def test_status_button_inverts_on_hover_and_restores_on_leave(self, work_tree):
        root_button = work_tree.itemWidget(work_tree.root_item, 1)
        initial_cache_key = root_button.icon().cacheKey()

        work_tree.eventFilter(root_button, QEvent(QEvent.Enter))
        hover_cache_key = root_button.icon().cacheKey()

        assert "background: " in root_button.styleSheet()
        assert "background: transparent" not in root_button.styleSheet()
        assert hover_cache_key != initial_cache_key

        work_tree.eventFilter(root_button, QEvent(QEvent.Leave))
        restored_cache_key = root_button.icon().cacheKey()

        assert "background: transparent" in root_button.styleSheet()
        assert restored_cache_key != hover_cache_key

    def test_add_processing_step_adds_child_under_root(self, work_tree):
        work_tree.add_processing_step("ImageNormalizer")

        assert work_tree.root_item.childCount() == 1
        assert work_tree.get_step_names() == ["image_normalizer"]

    def test_set_item_status_updates_tooltip(self, work_tree):
        step_item = work_tree.add_processing_step("ImageNormalizer")

        work_tree.set_item_status(step_item, "done")

        step_button = work_tree.itemWidget(step_item, 1)
        assert step_button.toolTip() == "已完成"

    def test_status_presentation_supports_all_icons(self, work_tree):
        for status, tooltip in {
            "init": "初始化",
            "ready": "已完成准备",
            "changed": "已变更",
            "done": "已完成",
            "error": "异常",
        }.items():
            icon_path, actual_tooltip = work_tree._status_presentation(status)
            assert isinstance(icon_path, Path)
            assert icon_path.exists()
            assert actual_tooltip == tooltip

    def test_set_item_status_supports_ready(self, work_tree):
        step_item = work_tree.add_processing_step("ImageNormalizer")

        work_tree.set_item_status(step_item, "ready")

        step_button = work_tree.itemWidget(step_item, 1)
        assert step_button.toolTip() == "已完成准备"

    def test_clicking_init_status_runs_image_loader_to_done(self, app):
        image_path = Path(__file__).parent / "images" / "image_001.jpg"
        work_tree = WorkTreeWidget()
        loader = ImageLoader(name="image_loader", config={"path": str(image_path)})
        work_tree.set_pipeline(Pipeline(name="image process", steps=[loader]))

        step_item = work_tree.root_item.child(0)
        step_button = work_tree.itemWidget(step_item, 1)
        step_button.click()

        updated_button = work_tree.itemWidget(step_item, 1)
        assert updated_button.toolTip() == "已完成"

    def test_clicking_init_status_runs_inputs_check_before_execution(self, app):
        work_tree = WorkTreeWidget()
        loader = ImageLoader(name="image_loader")
        work_tree.set_pipeline(Pipeline(name="image process", steps=[loader]))

        step_item = work_tree.root_item.child(0)
        step_button = work_tree.itemWidget(step_item, 1)

        with patch("ui.work_tree.QMessageBox.warning") as warning:
            step_button.click()

        updated_button = work_tree.itemWidget(step_item, 1)
        assert warning.called is True
        assert updated_button.toolTip() == "初始化"

    def test_unknown_status_falls_back_to_init(self, work_tree):
        icon_path, tooltip = work_tree._status_presentation("unknown")

        assert isinstance(icon_path, Path)
        assert icon_path.exists()
        assert icon_path.name == "init.svg"
        assert tooltip == "初始化"
