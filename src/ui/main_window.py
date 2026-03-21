"""
主窗口模块
"""

import sys
from pathlib import Path
from typing import Optional, List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QToolBar, QStatusBar,
    QSplitter, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QFileDialog,
    QApplication, QHeaderView, QFrame, QScrollArea,
    QInputDialog
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QKeySequence

import numpy as np

# 添加父目录到路径以便导入核心模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data_extractor import DataExtractor, DataPoint

# 导入新的 UI 组件
from .nav_bar import NavBar
from .data_panel import DataPanel
from .center_panel import CenterPanel, ImageCanvas
from .right_panel import RightPanel
from .settings_sections import (
    AxisSettingsSection,
    CurveSettingsSection,
    ExportSettingsSection
)

class MainWindow(QMainWindow):
    """主窗口类
    """
    
    def __init__(self, *, auto_load_image: bool = False, image_path: str | Path | None = None):
        super().__init__()
        
        self._extractor = DataExtractor()
        self._is_setting_axis = False
        self._axis_step = 0  # 0: X1, 1: X2, 2: Y1, 3: Y2
        self._axis_values = {}
        self._data_panel_expanded = True
        self._startup_image_path = image_path
        
        self._init_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._connect_signals()
        
        self.setWindowTitle("Unplot - 从图像提取数据")
        self.resize(1100, 700)

        if auto_load_image:
            self._load_startup_image()
        
    def _init_ui(self):
        """初始化 UI"""
        # 创建中央 widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局 - 水平排列
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. 最左侧导航栏
        self._nav_bar = NavBar()
        main_layout.addWidget(self._nav_bar)
        
        # 2. 创建左侧面板和中央区域之间的分割器
        left_center_splitter = QSplitter(Qt.Horizontal)
        left_center_splitter.setHandleWidth(1)
        
        # 数据面板（树状结构 + 属性列表）
        self._data_panel = DataPanel()
        left_center_splitter.addWidget(self._data_panel)
        
        # 中央区域（工具栏 + 画布）
        self._center_panel = CenterPanel()
        left_center_splitter.addWidget(self._center_panel)
        
        # 设置分割器初始大小
        left_center_splitter.setSizes([250, 800])
        left_center_splitter.setStretchFactor(1, 1)  # 中央区域可伸缩
        
        main_layout.addWidget(left_center_splitter)
        
        # 3. 创建中央区域和右侧面板之间的分割器
        center_right_splitter = QSplitter(Qt.Horizontal)
        center_right_splitter.setHandleWidth(1)
        center_right_splitter.addWidget(left_center_splitter)
        
        # 右侧面板（设置区域）
        self._right_panel = self._create_right_panel()
        center_right_splitter.addWidget(self._right_panel)
        
        # 设置分割器初始大小
        center_right_splitter.setSizes([1050, 300])
        center_right_splitter.setStretchFactor(0, 1)  # 左侧区域可伸缩
        
        main_layout.addWidget(center_right_splitter)
        
    def _create_right_panel(self) -> RightPanel:
        """创建右侧设置面板并添加默认设置区域"""
        panel = RightPanel()
        
        # 添加坐标轴设置区域
        axis_section = AxisSettingsSection()
        panel.add_section("axis", axis_section)
        
        # 添加曲线样式设置区域
        curve_section = CurveSettingsSection()
        panel.add_section("curve", curve_section)
        
        # 添加导出设置区域
        export_section = ExportSettingsSection()
        panel.add_section("export", export_section)
        
        return panel
        
    def _setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件 (&F)")
        
        open_action = QAction("打开图像 (&O)", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._open_image)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出 (&X)", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑 (&E)")
        
        clear_action = QAction("清除所有点 (&C)", self)
        clear_action.setShortcut(QKeySequence.Delete)
        clear_action.triggered.connect(self._clear_points)
        edit_menu.addAction(clear_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图 (&V)")
        
        toggle_data_panel_action = QAction("切换数据面板 (&L)", self)
        toggle_data_panel_action.setShortcut("Ctrl+L")
        toggle_data_panel_action.triggered.connect(self._toggle_data_panel)
        view_menu.addAction(toggle_data_panel_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助 (&H)")
        
        about_action = QAction("关于 (&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _setup_statusbar(self):
        """设置状态栏"""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("就绪")
        
    def _connect_signals(self):
        """连接信号和槽"""
        # 左侧导航栏信号
        self._nav_bar.toggle_data_panel.connect(self._toggle_data_panel)
        
        # 中央面板信号
        self._center_panel.canvas_clicked.connect(self._on_canvas_clicked)
        self._center_panel.tool_clicked.connect(self._on_tool_clicked)
        
        # 右侧设置区域信号
        axis_section = self._right_panel.get_section("axis")
        if axis_section:
            axis_section.btn_calibrate.clicked.connect(self._start_calibration)
            
        export_section = self._right_panel.get_section("export")
        if export_section:
            export_section.btn_export.clicked.connect(self._export_data)
            
    @Slot()
    def _toggle_data_panel(self):
        """切换数据面板展开/收起状态"""
        self._data_panel_expanded = not self._data_panel_expanded
        self._data_panel.set_expanded(self._data_panel_expanded)
        self._nav_bar.set_panel_expanded(self._data_panel_expanded)
        
        if self._data_panel_expanded:
            self._statusbar.showMessage("数据面板已展开")
        else:
            self._statusbar.showMessage("数据面板已收起")
        
    @Slot(str)
    def _on_tool_clicked(self, tool_name: str):
        """处理工具栏按钮点击"""
        if tool_name == "select":
            self._statusbar.showMessage("当前工具：选择")
        elif tool_name == "add_point":
            self._statusbar.showMessage("当前工具：添加点 - 请在画布上点击")
            
    @Slot(float, float)
    def _on_canvas_clicked(self, x: float, y: float):
        """处理画布点击事件"""
        if self._is_setting_axis:
            self._handle_calibration_click(x, y)
        else:
            # 添加数据点
            self._add_data_point(x, y)
            
    @Slot()
    def _open_image(self):
        """打开图像文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开图像", "",
            "图像文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.tif);;所有文件 (*)"
        )
        
        if file_path:
            self.load_image_from_path(file_path)

    def load_image_from_path(self, file_path: str | Path) -> bool:
        """使用 ImageLoader 加载图像并显示到中心画布。"""
        if self._extractor.load_image(str(file_path)):
            image = self._extractor.image_loader.image
            self._center_panel.set_image(image)
            self._statusbar.showMessage(f"已加载：{file_path}")
            return True

        QMessageBox.critical(self, "错误", f"无法加载图像文件：{file_path}")
        return False

    def _load_startup_image(self) -> None:
        """加载启动时的默认测试图像。"""
        image_path = self._startup_image_path or self._resolve_default_image_path()
        if image_path is None:
            self._statusbar.showMessage("未找到默认测试图像")
            return

        self.load_image_from_path(image_path)

    def _resolve_default_image_path(self) -> Path | None:
        """解析默认测试图像路径。"""
        repo_root = Path(__file__).resolve().parents[2]
        image_dir = repo_root / "tests" / "images"

        candidates = [
            image_dir / "image_001.jpg",
            image_dir / "image001.jpg",
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None
                
    @Slot()
    def _start_calibration(self):
        """开始坐标轴校准"""
        # 获取当前图像
        canvas = self._center_panel.canvas
        if canvas._image is None:
            QMessageBox.warning(self, "警告", "请先加载图像")
            return
            
        self._is_setting_axis = True
        self._axis_step = 0
        self._axis_values = {}
        canvas.set_axis_points([])
        self._update_calibration_label()
        self._statusbar.showMessage("请点击 X 轴最小值位置")
        
    def _update_calibration_label(self):
        """更新校准状态标签"""
        steps = ["X 轴最小值", "X 轴最大值", "Y 轴最小值", "Y 轴最大值"]
        if self._axis_step < 4:
            self._statusbar.showMessage(f"状态：请点击 {steps[self._axis_step]}")
        else:
            self._statusbar.showMessage("状态：已校准")
            
    def _handle_calibration_click(self, x: float, y: float):
        """处理校准过程中的点击"""
        steps = ["x1", "x2", "y1", "y2"]
        current_step = steps[self._axis_step]
        
        # 存储像素坐标
        self._axis_values[f"{current_step}_pixel"] = x
        
        # 添加点到画布显示
        points = self._center_panel.canvas._axis_points
        points.append((x, y))
        self._center_panel.canvas.set_axis_points(points)
        
        # 请求用户输入数据值
        if self._axis_step == 0:  # X1
            value, ok = QInputDialog.getDouble(
                self, "X 轴最小值", "请输入 X 轴最小值对应的数据值:", 0.0
            )
            if ok:
                self._axis_values["x1_data"] = value
                self._axis_step += 1
                self._update_calibration_label()
            else:
                self._cancel_calibration()
                return
                
        elif self._axis_step == 1:  # X2
            value, ok = QInputDialog.getDouble(
                self, "X 轴最大值", "请输入 X 轴最大值对应的数据值:", 100.0
            )
            if ok:
                self._axis_values["x2_data"] = value
                self._axis_step += 1
                self._update_calibration_label()
            else:
                self._cancel_calibration()
                return
                
        elif self._axis_step == 2:  # Y1
            value, ok = QInputDialog.getDouble(
                self, "Y 轴最小值", "请输入 Y 轴最小值对应的数据值:", "0"
            )
            if ok:
                self._axis_values["y1_data"] = value
                self._axis_step += 1
                self._update_calibration_label()
            else:
                self._cancel_calibration()
                return
                
        elif self._axis_step == 3:  # Y2
            value, ok = QInputDialog.getDouble(
                self, "Y 轴最大值", "请输入 Y 轴最大值对应的数据值:", 100.0
            )
            if ok:
                self._axis_values["y2_data"] = value
                self._finish_calibration()
            else:
                self._cancel_calibration()
                return
    
    def _cancel_calibration(self):
        """取消校准"""
        self._is_setting_axis = False
        self._axis_step = 0
        self._axis_values = {}
        self._center_panel.canvas.set_axis_points([])
        self._statusbar.showMessage("校准已取消")
        
    def _finish_calibration(self):
        """完成校准"""
        self._extractor.set_axis_calibration(
            self._axis_values["x1_pixel"], self._axis_values["x1_data"],
            self._axis_values["x2_pixel"], self._axis_values["x2_data"],
            self._axis_values["y1_pixel"], self._axis_values["y1_data"],
            self._axis_values["y2_pixel"], self._axis_values["y2_data"]
        )
        
        self._is_setting_axis = False
        self._axis_step = 0
        self._center_panel.canvas.set_axis_points([])
        self._statusbar.showMessage("坐标轴校准完成")
        
    def _add_data_point(self, x: float, y: float):
        """添加数据点"""
        if not self._extractor.coordinate_mapper.is_configured():
            QMessageBox.warning(self, "警告", "请先设置坐标轴")
            return
            
        try:
            point = self._extractor.add_point(x, y)
            self._center_panel.canvas.add_point(x, y)
            self._statusbar.showMessage(f"已添加点：X={point.x_pixel:.2f}, Y={point.y_pixel:.2f}")
        except ValueError as e:
            QMessageBox.warning(self, "警告", str(e))
            
    @Slot()
    def _clear_points(self):
        """清除所有数据点"""
        self._extractor.clear_points()
        self._center_panel.canvas.clear_points()
        self._statusbar.showMessage("已清除所有数据点")
        
    @Slot()
    def _export_data(self):
        """导出数据"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出数据", "",
            "CSV 文件 (*.csv);;Excel 文件 (*.xlsx);;所有文件 (*)"
        )
        
        if file_path:
            try:
                x_data, y_data = self._extractor.get_data_arrays()
                
                import pandas as pd
                df = pd.DataFrame({"X": x_data, "Y": y_data})
                
                if file_path.endswith(".csv"):
                    df.to_csv(file_path, index=False)
                elif file_path.endswith(".xlsx"):
                    df.to_excel(file_path, index=False)
                else:
                    df.to_csv(file_path + ".csv", index=False)
                    
                self._statusbar.showMessage(f"数据已导出到：{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败：{e}")
                
    @Slot()
    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, "关于 Unplot",
            "Unplot - 从图像中提取数据点\n\n"
            "版本：0.2.0\n"
            "使用 PySide6 开发"
        )
        
    # 属性访问器
    @property
    def nav_bar(self) -> NavBar:
        """获取导航栏"""
        return self._nav_bar
    
    @property
    def data_panel(self) -> DataPanel:
        """获取数据面板"""
        return self._data_panel
    
    @property
    def center_panel(self) -> CenterPanel:
        """获取中央面板"""
        return self._center_panel
    
    @property
    def right_panel(self) -> RightPanel:
        """获取右侧面板"""
        return self._right_panel
    
    @property
    def canvas(self) -> ImageCanvas:
        """获取画布"""
        return self._center_panel.canvas
    
    @property
    def statusbar(self) -> QStatusBar:
        """获取状态栏"""
        return self._statusbar
