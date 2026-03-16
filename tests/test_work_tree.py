"""
WorkTreeWidget 测试模块。
"""

import sys
from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QApplication, QToolButton

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ui.work_tree import WorkTreeWidget


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
    return WorkTreeWidget()


class TestWorkTreeWidget:
    """工作树组件测试。"""

    def test_has_single_root_node(self, work_tree):
        assert work_tree.topLevelItemCount() == 1
        assert work_tree.root_item.text(0) == "image process"

    def test_default_first_step_is_image_loader(self, work_tree):
        assert work_tree.root_item.childCount() == 1
        assert work_tree.root_item.child(0).text(0) == "image_loader"
        assert work_tree.get_step_names() == ["image_loader"]

    def test_status_button_exists_for_root_and_step(self, work_tree):
        root_button = work_tree.itemWidget(work_tree.root_item, 1)
        step_button = work_tree.itemWidget(work_tree.root_item.child(0), 1)

        assert isinstance(root_button, QToolButton)
        assert isinstance(step_button, QToolButton)
        assert root_button.text() == ""
        assert step_button.text() == ""
        assert root_button.toolTip() == "初始化"
        assert step_button.toolTip() == "初始化"
        assert root_button.toolButtonStyle() == Qt.ToolButtonIconOnly
        assert step_button.toolButtonStyle() == Qt.ToolButtonIconOnly

    def test_status_button_has_borderless_style(self, work_tree):
        step_button = work_tree.itemWidget(work_tree.root_item.child(0), 1)
        stylesheet = step_button.styleSheet()

        assert "border: none" in stylesheet
        assert "background: transparent" in stylesheet

    def test_status_button_inverts_on_hover_and_restores_on_leave(self, work_tree):
        step_button = work_tree.itemWidget(work_tree.root_item.child(0), 1)
        initial_cache_key = step_button.icon().cacheKey()

        work_tree.eventFilter(step_button, QEvent(QEvent.Enter))
        hover_cache_key = step_button.icon().cacheKey()

        assert "background: " in step_button.styleSheet()
        assert "background: transparent" not in step_button.styleSheet()
        assert hover_cache_key != initial_cache_key

        work_tree.eventFilter(step_button, QEvent(QEvent.Leave))
        restored_cache_key = step_button.icon().cacheKey()

        assert "background: transparent" in step_button.styleSheet()
        assert restored_cache_key != hover_cache_key

    def test_add_processing_step_adds_child_under_root(self, work_tree):
        work_tree.add_processing_step("image_normalizer")

        assert work_tree.root_item.childCount() == 2
        assert work_tree.get_step_names() == ["image_loader", "image_normalizer"]

    def test_set_item_status_updates_tooltip(self, work_tree):
        step_item = work_tree.root_item.child(0)

        work_tree.set_item_status(step_item, "done")

        step_button = work_tree.itemWidget(step_item, 1)
        assert step_button.toolTip() == "已完成"

    def test_status_presentation_supports_all_icons(self, work_tree):
        for status, tooltip in {
            "init": "初始化",
            "changed": "已变更",
            "done": "已完成",
            "error": "异常",
        }.items():
            icon_path, actual_tooltip = work_tree._status_presentation(status)
            assert isinstance(icon_path, Path)
            assert icon_path.exists()
            assert actual_tooltip == tooltip

    def test_unknown_status_falls_back_to_init(self, work_tree):
        icon_path, tooltip = work_tree._status_presentation("unknown")

        assert isinstance(icon_path, Path)
        assert icon_path.exists()
        assert icon_path.name == "init.svg"
        assert tooltip == "初始化"
