"""
主窗口模块
"""

import sys
from pathlib import Path
from typing import Optional, List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QAction, QToolBar, QStatusBar,
    QSplitter, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QFileDialog,
    QApplication, QHeaderView, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QKeySequence

import numpy as np

# 添加父目录到路径以便导入核心模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data_extractor import DataExtractor, DataPoint
from core.image_loader import ImageLoader


class ImageCanvas(QFrame):
    """图像画布组件
    
    用于显示图像并处理用户的鼠标交互。
    """
    
    point_clicked = Signal(float, float)  # 信号：用户点击位置（像素坐标）
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = None
        self._points: List[tuple] = []  # 存储已添加的点
        self._axis_points: List[tuple] = []  # 坐标轴参考点
        
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.setLineWidth(2)
        self.setMinimumSize(400, 300)
        
    def set_image(self, image: np.ndarray) -> None:
        """设置要显示的图像"""
        self._image = image
        self._points.clear()
        self._axis_points.clear()
        self.update()
        
    def clear_image(self) -> None:
        """清除图像"""
        self._image = None
        self._points.clear()
        self._axis_points.clear()
        self.update()
        
    def add_point(self, x: float, y: float) -> None:
        """添加一个显示点"""
        self._points.append((x, y))
        self.update()
        
    def clear_points(self) -> None:
        """清除所有数据点"""
        self._points.clear()
        self.update()
        
    def set_axis_points(self, points: List[tuple]) -> None:
        """设置坐标轴参考点"""
        self._axis_points = points
        self.update()
        
    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        if self._image is not None:
            x = event.position().x()
            y = event.position().y()
            self.point_clicked.emit(x, y)
            
    def paintEvent(self, event):
        """绘制事件"""
        from PySide6.QtGui import QPainter, QImage, QPen, QBrush
        from PySide6.QtCore import QRectF
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        painter.fillRect(self.rect(), Qt.white)
        
        if self._image is not None:
            # 转换 numpy 数组为 QImage
            h, w, ch = self._image.shape
            bytes_per_line = ch * w
            qimage = QImage(self._image.data, w, h, bytes_per_line, 
                           QImage.Format_RGB888)
            
            # 缩放以适应画布
            scaled_rect = self._get_scaled_rect(w, h)
            painter.drawImage(scaled_rect, qimage)
            
            # 计算缩放比例
            scale_x = scaled_rect.width() / w
            scale_y = scaled_rect.height() / h
            
            # 绘制数据点
            pen = QPen(Qt.red, 3)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QBrush(Qt.red))
            
            for px, py in self._points:
                cx = scaled_rect.left() + px * scale_x
                cy = scaled_rect.top() + py * scale_y
                painter.drawEllipse(QPointF(cx, cy), 5, 5)
            
            # 绘制坐标轴参考点（蓝色）
            pen.setColor(Qt.blue)
            painter.setPen(pen)
            painter.setBrush(QBrush(Qt.blue))
            
            for i, (px, py) in enumerate(self._axis_points):
                cx = scaled_rect.left() + px * scale_x
                cy = scaled_rect.top() + py * scale_y
                painter.drawEllipse(QPointF(cx, cy), 7, 7)
                
    def _get_scaled_rect(self, img_w: int, img_h: int):
        """计算图像缩放的矩形区域"""
        from PySide6.QtCore import QRect
        
        canvas_w = self.width() - 20
        canvas_h = self.height() - 20
        
        if canvas_w <= 0 or canvas_h <= 0:
            return QRect(10, 10, 10, 10)
        
        scale = min(canvas_w / img_w, canvas_h / img_h)
        
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        x = 10 + (canvas_w - new_w) // 2
        y = 10 + (canvas_h - new_h) // 2
        
        return QRect(x, y, new_w, new_h)


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        self._extractor = DataExtractor()
        self._is_setting_axis = False
        self._axis_step = 0  # 0: X1, 1: X2, 2: Y1, 3: Y2
        self._axis_values = {}
        
        self._init_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        
        self.setWindowTitle("Unplot - 从图像提取数据")
        self.resize(1200, 800)
        
    def _init_ui(self):
        """初始化 UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧：图像画布
        self._canvas = ImageCanvas()
        self._canvas.point_clicked.connect(self._on_canvas_clicked)
        splitter.addWidget(self._canvas)
        
        # 右侧：控制面板和数据表
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(right_widget)
        
        # 控制面板
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.StyledPanel)
        control_layout = QVBoxLayout(control_frame)
        
        # 坐标轴校准按钮
        self._btn_calibrate = QPushButton("设置坐标轴")
        self._btn_calibrate.clicked.connect(self._start_calibration)
        control_layout.addWidget(self._btn_calibrate)
        
        self._lbl_calibration = QLabel("状态：未校准")
        control_layout.addWidget(self._lbl_calibration)
        
        # 自动检测按钮
        self._btn_auto_detect = QPushButton("自动检测曲线")
        self._btn_auto_detect.clicked.connect(self._auto_detect)
        self._btn_auto_detect.setEnabled(False)
        control_layout.addWidget(self._btn_auto_detect)
        
        # 清除点按钮
        self._btn_clear = QPushButton("清除所有点")
        self._btn_clear.clicked.connect(self._clear_points)
        control_layout.addWidget(self._btn_clear)
        
        # 导出按钮
        self._btn_export = QPushButton("导出数据")
        self._btn_export.clicked.connect(self._export_data)
        self._btn_export.setEnabled(False)
        control_layout.addWidget(self._btn_export)
        
        right_layout.addWidget(control_frame)
        
        # 数据表格
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["X 像素", "Y 像素", "X 数据", "Y 数据"])
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self._table)
        
        splitter.setSizes([800, 400])
        
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
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助 (&H)")
        
        about_action = QAction("关于 (&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _setup_toolbar(self):
        """设置工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        open_action = QAction("打开", self)
        open_action.triggered.connect(self._open_image)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        self._toolbar_calibrate = QAction("设置坐标轴", self)
        self._toolbar_calibrate.triggered.connect(self._start_calibration)
        toolbar.addAction(self._toolbar_calibrate)
        
    def _setup_statusbar(self):
        """设置状态栏"""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("就绪")
        
    @Slot()
    def _open_image(self):
        """打开图像文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开图像", "",
            "图像文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.tif);;所有文件 (*)"
        )
        
        if file_path:
            if self._extractor.load_image(file_path):
                image = self._extractor.image_loader.image
                self._canvas.set_image(image)
                self._statusbar.showMessage(f"已加载：{file_path}")
                self._btn_auto_detect.setEnabled(True)
            else:
                QMessageBox.critical(self, "错误", "无法加载图像文件")
                
    @Slot()
    def _start_calibration(self):
        """开始坐标轴校准"""
        if self._extractor.image_loader.image is None:
            QMessageBox.warning(self, "警告", "请先加载图像")
            return
            
        self._is_setting_axis = True
        self._axis_step = 0
        self._axis_values = {}
        self._canvas.set_axis_points([])
        self._update_calibration_label()
        self._statusbar.showMessage("请点击 X 轴最小值位置")
        
    def _update_calibration_label(self):
        """更新校准状态标签"""
        steps = ["X 轴最小值", "X 轴最大值", "Y 轴最小值", "Y 轴最大值"]
        if self._axis_step < 4:
            self._lbl_calibration.setText(f"状态：请点击 {steps[self._axis_step]}")
        else:
            self._lbl_calibration.setText("状态：已校准")
            
    @Slot(float, float)
    def _on_canvas_clicked(self, x: float, y: float):
        """处理画布点击事件"""
        if self._is_setting_axis:
            self._handle_calibration_click(x, y)
        else:
            # 添加数据点
            self._add_data_point(x, y)
            
    def _handle_calibration_click(self, x: float, y: float):
        """处理校准过程中的点击"""
        steps = ["x1", "x2", "y1", "y2"]
        current_step = steps[self._axis_step]
        
        # 存储像素坐标
        self._axis_values[f"{current_step}_pixel"] = x
        
        # 添加点到画布显示
        points = self._canvas._axis_points
        points.append((x, y))
        self._canvas.set_axis_points(points)
        
        # 请求用户输入数据值
        if self._axis_step == 0:  # X1
            value, ok = QFileDialog.getTextInput(
                self, "X 轴最小值", "请输入 X 轴最小值对应的数据值:", "0"
            )
            # 由于 PySide6 没有 getTextInput，使用自定义对话框
            from PySide6.QtWidgets import QInputDialog
            value, ok = QInputDialog.getDouble(
                self, "X 轴最小值", "请输入 X 轴最小值对应的数据值:", 0.0
            )
            if ok:
                self._axis_values["x1_data"] = value
                self._axis_step += 1
                self._update_calibration_label()
                self._statusbar.showMessage("请点击 X 轴最大值位置")
            else:
                self._cancel_calibration()
                return
                
        elif self._axis_step == 1:  # X2
            from PySide6.QtWidgets import QInputDialog
            value, ok = QInputDialog.getDouble(
                self, "X 轴最大值", "请输入 X 轴最大值对应的数据值:", 100.0
            )
            if ok:
                self._axis_values["x2_data"] = value
                self._axis_step += 1
                self._update_calibration_label()
                self._statusbar.showMessage("请点击 Y 轴最小值位置")
            else:
                self._cancel_calibration()
                return
                
        elif self._axis_step == 2:  # Y1
            from PySide6.QtWidgets import QInputDialog
            value, ok = QInputDialog.getDouble(
                self, "Y 轴最小值", "请输入 Y 轴最小值对应的数据值:", "0"
            )
            if ok:
                self._axis_values["y1_data"] = value
                self._axis_step += 1
                self._update_calibration_label()
                self._statusbar.showMessage("请点击 Y 轴最大值位置")
            else:
                self._cancel_calibration()
                return
                
        elif self._axis_step == 3:  # Y2
            from PySide6.QtWidgets import QInputDialog
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
        self._canvas.set_axis_points([])
        self._lbl_calibration.setText("状态：未校准")
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
        self._canvas.set_axis_points([])
        self._lbl_calibration.setText("状态：已校准")
        self._statusbar.showMessage("坐标轴校准完成")
        
    def _add_data_point(self, x: float, y: float):
        """添加数据点"""
        if not self._extractor.coordinate_mapper.is_configured():
            QMessageBox.warning(self, "警告", "请先设置坐标轴")
            return
            
        try:
            point = self._extractor.add_point(x, y)
            self._canvas.add_point(x, y)
            self._update_table()
            self._btn_export.setEnabled(True)
            self._statusbar.showMessage(f"已添加点：X={point.x_data:.4f}, Y={point.y_data:.4f}")
        except ValueError as e:
            QMessageBox.warning(self, "警告", str(e))
            
    def _update_table(self):
        """更新数据表格"""
        points = self._extractor.get_data_points()
        self._table.setRowCount(len(points))
        
        for i, point in enumerate(points):
            self._table.setItem(i, 0, QTableWidgetItem(f"{point.x_pixel:.2f}"))
            self._table.setItem(i, 1, QTableWidgetItem(f"{point.y_pixel:.2f}"))
            self._table.setItem(i, 2, QTableWidgetItem(f"{point.x_data:.6f}"))
            self._table.setItem(i, 3, QTableWidgetItem(f"{point.y_data:.6f}"))
            
    @Slot()
    def _clear_points(self):
        """清除所有数据点"""
        self._extractor.clear_points()
        self._canvas.clear_points()
        self._table.setRowCount(0)
        self._btn_export.setEnabled(False)
        self._statusbar.showMessage("已清除所有数据点")
        
    @Slot()
    def _auto_detect(self):
        """自动检测数据点"""
        if not self._extractor.coordinate_mapper.is_configured():
            QMessageBox.warning(self, "警告", "请先设置坐标轴")
            return
            
        count = self._extractor.auto_extract_curve()
        
        # 更新画布显示
        self._canvas.clear_points()
        for point in self._extractor.get_data_points():
            self._canvas.add_point(point.x_pixel, point.y_pixel)
            
        self._update_table()
        self._btn_export.setEnabled(True)
        self._statusbar.showMessage(f"自动检测到 {count} 个数据点")
        
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
            "版本：0.1.0\n"
            "使用 PySide6 开发"
        )