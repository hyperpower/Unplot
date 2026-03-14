"""
具体设置区域类模块
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDoubleSpinBox, QSpinBox, QCheckBox,
    QColorDialog, QComboBox
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, Signal

from .base import SettingsSection


class AxisSettingsSection(SettingsSection):
    """坐标轴设置区域
    
    包含坐标轴校准相关的设置控件。
    """
    
    def __init__(self, parent=None):
        super().__init__("坐标轴设置", parent)
        self._init_controls()
        
    def _init_controls(self):
        """初始化控制控件"""
        # X 轴范围
        x_range_layout = QHBoxLayout()
        x_range_layout.addWidget(QLabel("X 范围:"))
        self._x_min = QDoubleSpinBox()
        self._x_min.setRange(-1e9, 1e9)
        self._x_min.setValue(0.0)
        self._x_min.setPrefix("Min: ")
        x_range_layout.addWidget(self._x_min)
        self._x_max = QDoubleSpinBox()
        self._x_max.setRange(-1e9, 1e9)
        self._x_max.setValue(100.0)
        self._x_max.setPrefix("Max: ")
        x_range_layout.addWidget(self._x_max)
        self.content_layout.addLayout(x_range_layout)
        
        # Y 轴范围
        y_range_layout = QHBoxLayout()
        y_range_layout.addWidget(QLabel("Y 范围:"))
        self._y_min = QDoubleSpinBox()
        self._y_min.setRange(-1e9, 1e9)
        self._y_min.setValue(0.0)
        self._y_min.setPrefix("Min: ")
        y_range_layout.addWidget(self._y_min)
        self._y_max = QDoubleSpinBox()
        self._y_max.setRange(-1e9, 1e9)
        self._y_max.setValue(100.0)
        self._y_max.setPrefix("Max: ")
        y_range_layout.addWidget(self._y_max)
        self.content_layout.addLayout(y_range_layout)
        
        # 对数坐标
        self._log_x = QCheckBox("X 轴对数坐标")
        self.content_layout.addWidget(self._log_x)
        self._log_y = QCheckBox("Y 轴对数坐标")
        self.content_layout.addWidget(self._log_y)
        
        # 校准按钮
        self._btn_calibrate = QPushButton("重新校准坐标轴")
        self.content_layout.addWidget(self._btn_calibrate)
        
    @property
    def x_min(self) -> QDoubleSpinBox:
        return self._x_min
    
    @property
    def x_max(self) -> QDoubleSpinBox:
        return self._x_max
    
    @property
    def y_min(self) -> QDoubleSpinBox:
        return self._y_min
    
    @property
    def y_max(self) -> QDoubleSpinBox:
        return self._y_max
    
    @property
    def btn_calibrate(self) -> QPushButton:
        return self._btn_calibrate
    
    def get_values(self) -> dict:
        return {
            "x_min": self._x_min.value(),
            "x_max": self._x_max.value(),
            "y_min": self._y_min.value(),
            "y_max": self._y_max.value(),
            "log_x": self._log_x.isChecked(),
            "log_y": self._log_y.isChecked(),
        }
        
    def set_values(self, values: dict):
        if "x_min" in values:
            self._x_min.setValue(values["x_min"])
        if "x_max" in values:
            self._x_max.setValue(values["x_max"])
        if "y_min" in values:
            self._y_min.setValue(values["y_min"])
        if "y_max" in values:
            self._y_max.setValue(values["y_max"])
        if "log_x" in values:
            self._log_x.setChecked(values["log_x"])
        if "log_y" in values:
            self._log_y.setChecked(values["log_y"])


class CurveSettingsSection(SettingsSection):
    """曲线设置区域
    
    包含曲线样式相关的设置控件。
    """
    
    # 信号：颜色改变
    color_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__("曲线样式", parent)
        self._current_color = "#FF5722"
        self._init_controls()
        
    def _init_controls(self):
        """初始化控制控件"""
        # 颜色选择
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("曲线颜色:"))
        self._color_button = QPushButton()
        self._color_button.setFixedSize(60, 30)
        self._update_color_button()
        self._color_button.clicked.connect(self._choose_color)
        color_layout.addWidget(self._color_button)
        color_layout.addStretch()
        self.content_layout.addLayout(color_layout)
        
        # 线宽
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("线宽:"))
        self._line_width = QSpinBox()
        self._line_width.setRange(1, 10)
        self._line_width.setValue(2)
        self._line_width.setSuffix(" px")
        width_layout.addWidget(self._line_width)
        width_layout.addStretch()
        self.content_layout.addLayout(width_layout)
        
        # 点样式
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("点样式:"))
        self._point_style = QComboBox()
        self._point_style.addItems(["无", "圆点", "方块", "三角"])
        style_layout.addWidget(self._point_style)
        style_layout.addStretch()
        self.content_layout.addLayout(style_layout)
        
        # 点大小
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("点大小:"))
        self._point_size = QSpinBox()
        self._point_size.setRange(3, 20)
        self._point_size.setValue(6)
        self._point_size.setSuffix(" px")
        size_layout.addWidget(self._point_size)
        size_layout.addStretch()
        self.content_layout.addLayout(size_layout)
        
        # 线型
        line_style_layout = QHBoxLayout()
        line_style_layout.addWidget(QLabel("线型:"))
        self._line_style = QComboBox()
        self._line_style.addItems(["实线", "虚线", "点线", "点划线"])
        line_style_layout.addWidget(self._line_style)
        line_style_layout.addStretch()
        self.content_layout.addLayout(line_style_layout)
        
    def _update_color_button(self):
        """更新颜色按钮样式"""
        # 使用内联样式表仅用于颜色按钮显示当前颜色
        self._color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._current_color};
                border: 2px solid #333;
                border-radius: 4px;
            }}
        """)
        
    def _choose_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(QColor(self._current_color), self, "选择曲线颜色")
        if color.isValid():
            self._current_color = color.name()
            self._update_color_button()
            self.color_changed.emit(self._current_color)
        
    @property
    def current_color(self) -> str:
        return self._current_color
    
    @property
    def line_width(self) -> QSpinBox:
        return self._line_width
    
    @property
    def point_style(self) -> QComboBox:
        return self._point_style
    
    @property
    def point_size(self) -> QSpinBox:
        return self._point_size
    
    @property
    def line_style(self) -> QComboBox:
        return self._line_style
    
    def get_values(self) -> dict:
        return {
            "color": self._current_color,
            "line_width": self._line_width.value(),
            "point_style": self._point_style.currentText(),
            "point_size": self._point_size.value(),
            "line_style": self._line_style.currentText(),
        }
        
    def set_values(self, values: dict):
        if "color" in values:
            self._current_color = values["color"]
            self._update_color_button()
        if "line_width" in values:
            self._line_width.setValue(values["line_width"])
        if "point_size" in values:
            self._point_size.setValue(values["point_size"])


class ExportSettingsSection(SettingsSection):
    """导出设置区域
    
    包含数据导出相关的设置控件。
    """
    
    def __init__(self, parent=None):
        super().__init__("数据导出", parent)
        self._init_controls()
        
    def _init_controls(self):
        """初始化控制控件"""
        # 导出格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("导出格式:"))
        self._format_combo = QComboBox()
        self._format_combo.addItems(["CSV", "Excel (.xlsx)", "JSON", "TXT"])
        format_layout.addWidget(self._format_combo)
        format_layout.addStretch()
        self.content_layout.addLayout(format_layout)
        
        # 分隔符选择（仅 CSV）
        sep_layout = QHBoxLayout()
        sep_layout.addWidget(QLabel("分隔符:"))
        self._separator = QComboBox()
        self._separator.addItems([",", ";", "\t", "空格"])
        sep_layout.addWidget(self._separator)
        sep_layout.addStretch()
        self.content_layout.addLayout(sep_layout)
        
        # 包含表头
        self._include_header = QCheckBox("包含列名表头")
        self._include_header.setChecked(True)
        self.content_layout.addWidget(self._include_header)
        
        # 小数位数
        precision_layout = QHBoxLayout()
        precision_layout.addWidget(QLabel("小数位数:"))
        self._precision = QSpinBox()
        self._precision.setRange(1, 15)
        self._precision.setValue(6)
        precision_layout.addWidget(self._precision)
        precision_layout.addStretch()
        self.content_layout.addLayout(precision_layout)
        
        # 导出按钮
        self._btn_export = QPushButton("导出数据")
        self.content_layout.addWidget(self._btn_export)
        
    @property
    def format_combo(self) -> QComboBox:
        return self._format_combo
    
    @property
    def separator(self) -> QComboBox:
        return self._separator
    
    @property
    def include_header(self) -> QCheckBox:
        return self._include_header
    
    @property
    def precision(self) -> QSpinBox:
        return self._precision
    
    @property
    def btn_export(self) -> QPushButton:
        return self._btn_export
    
    def get_values(self) -> dict:
        return {
            "format": self._format_combo.currentText(),
            "separator": self._separator.currentText(),
            "include_header": self._include_header.isChecked(),
            "precision": self._precision.value(),
        }
        
    def set_values(self, values: dict):
        if "format" in values:
            index = self._format_combo.findText(values["format"])
            if index >= 0:
                self._format_combo.setCurrentIndex(index)
        if "separator" in values:
            index = self._separator.findText(values["separator"])
            if index >= 0:
                self._separator.setCurrentIndex(index)
        if "include_header" in values:
            self._include_header.setChecked(values["include_header"])
        if "precision" in values:
            self._precision.setValue(values["precision"])