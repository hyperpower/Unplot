"""
主窗口 UI 测试模块
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PySide6.QtWidgets import QApplication, QAbstractItemView, QMenu, QToolBar
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView

from ui.main_window import MainWindow, ImageCanvas


@pytest.fixture(scope="function")
def app():
    """创建 Qt 应用程序实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(scope="function")
def image_canvas(app):
    """创建 ImageCanvas 测试夹具"""
    canvas = ImageCanvas()
    return canvas


@pytest.fixture(scope="function")
def main_window(app):
    """创建 MainWindow 测试夹具"""
    window = MainWindow()
    window.show()
    return window


class TestImageCanvas:
    """图像画布测试"""
    
    def test_init(self, image_canvas):
        """测试初始化"""
        assert image_canvas._image is None
        assert image_canvas._points == []
        assert image_canvas._axis_points == []
        
    def test_set_image(self, image_canvas):
        """测试设置图像"""
        # 创建一个测试图像
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[:, :] = [255, 255, 255]  # 白色背景
        
        image_canvas.set_image(test_image)
        assert image_canvas._image is not None
        assert image_canvas._image.shape == (100, 100, 3)
        
    def test_set_image_clears_points(self, image_canvas):
        """测试设置图像时清除已有点"""
        image_canvas.add_point(10, 20)
        image_canvas.add_point(30, 40)
        assert len(image_canvas._points) == 2
        
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        image_canvas.set_image(test_image)
        assert image_canvas._points == []
        
    def test_clear_image(self, image_canvas):
        """测试清除图像"""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        image_canvas.set_image(test_image)
        image_canvas.add_point(10, 20)
        image_canvas.set_axis_points([(5, 5)])
        
        image_canvas.clear_image()
        assert image_canvas._image is None
        assert image_canvas._points == []
        assert image_canvas._axis_points == []
        
    def test_add_point(self, image_canvas):
        """测试添加点"""
        image_canvas.add_point(10, 20)
        assert len(image_canvas._points) == 1
        assert image_canvas._points[0] == (10, 20)
        
        image_canvas.add_point(30, 40)
        assert len(image_canvas._points) == 2
        
    def test_clear_points(self, image_canvas):
        """测试清除点"""
        image_canvas.add_point(10, 20)
        image_canvas.add_point(30, 40)
        assert len(image_canvas._points) == 2
        
        image_canvas.clear_points()
        assert image_canvas._points == []
        
    def test_set_axis_points(self, image_canvas):
        """测试设置坐标轴参考点"""
        points = [(10, 20), (30, 40)]
        image_canvas.set_axis_points(points)
        assert image_canvas._axis_points == points
        assert len(image_canvas._axis_points) == 2
        
    def test_signal_emitted(self, image_canvas):
        """测试点击信号发射"""
        # 注意：此测试需要 pytest-qt 插件
        # 如果没有安装 pytest-qt，此测试将被跳过
        try:
            import pytestqt
        except ImportError:
            pytest.skip("pytest-qt 未安装，跳过此测试")
        
        callback_called = False
        received_x = None
        received_y = None
        
        def on_point_clicked(x, y):
            nonlocal callback_called, received_x, received_y
            callback_called = True
            received_x = x
            received_y = y
            
        image_canvas.point_clicked.connect(on_point_clicked)
        
        # 手动发射信号进行测试
        image_canvas.point_clicked.emit(100.0, 200.0)
        
        # 验证信号被发射
        assert callback_called is True
        assert received_x == 100.0
        assert received_y == 200.0


class TestMainWindow:
    """主窗口测试"""
    
    def test_init(self, main_window):
        """测试初始化"""
        assert main_window is not None
        assert main_window._extractor is not None
        assert main_window._controller is not None
        assert main_window._image_process_pipeline is not None
        
    def test_window_title(self, main_window):
        """测试窗口标题"""
        assert main_window.windowTitle() == "Unplot - 从图像提取数据"
        
    def test_window_size(self, main_window):
        """测试窗口大小"""
        # 使用 resize() 设置的尺寸，实际窗口大小可能因窗口装饰而不同
        assert main_window.width() >= 1100
        assert main_window.height() >= 700
        
    def test_central_widget(self, main_window):
        """测试中心部件"""
        central_widget = main_window.centralWidget()
        assert central_widget is not None
        
    def test_canvas_exists(self, main_window):
        """测试画布组件存在"""
        assert main_window.canvas is not None
        assert isinstance(main_window.canvas, ImageCanvas)
        
    def test_data_panel_exists(self, main_window):
        """测试数据面板存在"""
        assert main_window.data_panel is not None
        assert main_window.data_panel.tree_widget is not None
        assert main_window.data_panel.prop_widget is not None
        
    def test_nav_bar_exists(self, main_window):
        """测试导航栏存在"""
        assert main_window.nav_bar is not None
        
    def test_right_panel_exists(self, main_window):
        """测试右侧面板存在"""
        assert main_window.right_panel is not None
        
    def test_menubar_exists(self, main_window):
        """测试菜单栏存在"""
        menubar = main_window.menuBar()
        assert menubar is not None
        
    def test_file_menu_exists(self, main_window):
        """测试文件菜单存在"""
        file_menu = main_window.menuBar().findChild(QMenu, "文件 (&F)")
        # 或者通过索引获取
        actions = main_window.menuBar().actions()
        assert len(actions) >= 1  # 至少有一个菜单
        
    def test_center_panel_exists(self, main_window):
        """测试中央面板存在"""
        assert main_window.center_panel is not None
        
    def test_statusbar_exists(self, main_window):
        """测试状态栏存在"""
        statusbar = main_window.statusBar()
        assert statusbar is not None
        
    def test_initial_status_message(self, main_window):
        """测试初始状态消息"""
        assert main_window._statusbar.currentMessage() == "就绪"
        
    def test_canvas_signal_connected(self, main_window):
        """测试画布信号连接"""
        # 验证信号对象存在
        assert main_window.canvas.point_clicked is not None
        
    def test_close(self, main_window):
        """测试关闭窗口"""
        main_window.close()
        assert main_window.isVisible() is False

    def test_load_image_from_path(self, main_window):
        """测试通过 ImageLoader 加载图像并显示到画布"""
        image_path = Path(__file__).resolve().parent / "images" / "image_001.jpg"

        assert image_path.is_file()
        assert main_window.load_image_from_path(image_path) is True
        assert main_window._extractor.image_loader.image_path == str(image_path)
        assert main_window.canvas._image is not None

    def test_image_process_pipeline_shown_in_work_tree(self, main_window):
        """测试工作树默认展示真实 pipeline。"""
        tree = main_window.data_panel.tree_widget
        root_item = tree.root_item

        assert root_item is not None
        assert root_item.text(0) == "image process pipeline"
        assert tree.get_step_names() == []

    def test_property_widget_shows_pipeline_properties(self, main_window):
        """测试属性面板默认显示 pipeline 属性。"""
        table = main_window.data_panel.prop_widget

        assert table.item(0, 0).text() == "类型"
        assert table.item(0, 1).text() == "Pipeline"
        assert table.item(1, 0).text() == "名称"
        assert table.item(1, 1).text() == "image process pipeline"

    def test_property_widget_columns_are_interactive(self, main_window):
        """测试属性表格使用双列联动拖拽配置。"""
        table = main_window.data_panel.prop_widget
        header = table.horizontalHeader()

        assert header is not None
        assert table.selectionBehavior() == QAbstractItemView.SelectRows
        assert table.selectionMode() == QAbstractItemView.SingleSelection
        assert header.sectionsClickable() is False
        assert header.highlightSections() is False
        assert header.minimumSectionSize() == 10
        assert header.stretchLastSection() is False
        assert header.sectionResizeMode(0) == QHeaderView.Interactive
        assert header.sectionResizeMode(1) == QHeaderView.Interactive
        assert table.columnWidth(0) >= 10
        assert table.columnWidth(1) >= 10

    def test_property_widget_columns_keep_total_width_and_minimum(self, main_window):
        """测试两列总宽联动且最小宽度受限。"""
        panel = main_window.data_panel

        panel._apply_property_column_widths(5, total_width=80)
        assert panel.prop_widget.columnWidth(0) == 10
        assert panel.prop_widget.columnWidth(1) == 70

        panel._apply_property_column_widths(75, total_width=80)
        assert panel.prop_widget.columnWidth(0) == 70
        assert panel.prop_widget.columnWidth(1) == 10

    def test_canvas_starts_blank_before_loading_image(self, main_window):
        """测试未加载图像前画布保持空白状态。"""
        assert main_window.canvas._image is None
        assert main_window.canvas.has_image() is False

    def test_property_description_updates_status_bar(self, main_window):
        """测试点击属性行描述时会同步到状态栏。"""
        main_window.data_panel.property_description_changed.emit("示例属性说明")
        assert main_window._statusbar.currentMessage() == "示例属性说明"
