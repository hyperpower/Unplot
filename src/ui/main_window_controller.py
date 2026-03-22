"""
主窗口控制器模块
"""

from __future__ import annotations

from collections.abc import Callable

from core.data_extractor import DataExtractor


CalibrationValueProvider = Callable[[str, str, float], float | None]
StatusCallback = Callable[[str], None]
WarningCallback = Callable[[str, str], None]
AxisPointsCallback = Callable[[list[tuple[float, float]]], None]
DataPointCallback = Callable[[float, float], None]
HasImageCallback = Callable[[], bool]


class MainWindowController:
    """协调主窗口中的标定与加点流程。"""

    _CALIBRATION_STEPS = (
        ("x1", "X 轴最小值", "请输入 X 轴最小值对应的数据值:", 0.0, "x"),
        ("x2", "X 轴最大值", "请输入 X 轴最大值对应的数据值:", 100.0, "x"),
        ("y1", "Y 轴最小值", "请输入 Y 轴最小值对应的数据值:", 0.0, "y"),
        ("y2", "Y 轴最大值", "请输入 Y 轴最大值对应的数据值:", 100.0, "y"),
    )

    def __init__(
        self,
        extractor: DataExtractor,
        *,
        show_status: StatusCallback,
        show_warning: WarningCallback,
        request_calibration_value: CalibrationValueProvider,
        set_axis_points: AxisPointsCallback,
        add_canvas_point: DataPointCallback,
        has_image: HasImageCallback,
    ) -> None:
        self._extractor = extractor
        self._show_status = show_status
        self._show_warning = show_warning
        self._request_calibration_value = request_calibration_value
        self._set_axis_points = set_axis_points
        self._add_canvas_point = add_canvas_point
        self._has_image = has_image

        self._is_setting_axis = False
        self._axis_step = 0
        self._axis_values: dict[str, float] = {}
        self._axis_points: list[tuple[float, float]] = []

    @property
    def is_setting_axis(self) -> bool:
        return self._is_setting_axis

    def start_calibration(self) -> None:
        """开始坐标轴校准。"""
        if not self._has_image():
            self._show_warning("警告", "请先加载图像")
            return

        self._is_setting_axis = True
        self._axis_step = 0
        self._axis_values = {}
        self._axis_points = []
        self._set_axis_points([])
        self._update_calibration_status()

    def handle_canvas_click(self, x: float, y: float) -> None:
        """处理画布点击。"""
        if self._is_setting_axis:
            self._handle_calibration_click(x, y)
            return

        self._add_data_point(x, y)

    def clear_calibration_overlay(self) -> None:
        """清除标定叠加点。"""
        self._axis_points = []
        self._set_axis_points([])

    def _update_calibration_status(self) -> None:
        _, label, _, _, _ = self._CALIBRATION_STEPS[self._axis_step]
        self._show_status(f"状态：请点击 {label}")

    def _handle_calibration_click(self, x: float, y: float) -> None:
        step_key, label, prompt, default, axis = self._CALIBRATION_STEPS[self._axis_step]
        pixel_value = x if axis == "x" else y

        self._axis_values[f"{step_key}_pixel"] = pixel_value
        self._axis_points.append((x, y))
        self._set_axis_points(self._axis_points.copy())

        value = self._request_calibration_value(label, prompt, default)
        if value is None:
            self._cancel_calibration()
            return

        self._axis_values[f"{step_key}_data"] = value

        if self._axis_step == len(self._CALIBRATION_STEPS) - 1:
            self._finish_calibration()
            return

        self._axis_step += 1
        self._update_calibration_status()

    def _cancel_calibration(self) -> None:
        self._is_setting_axis = False
        self._axis_step = 0
        self._axis_values = {}
        self.clear_calibration_overlay()
        self._show_status("校准已取消")

    def _finish_calibration(self) -> None:
        self._extractor.set_axis_calibration(
            self._axis_values["x1_pixel"], self._axis_values["x1_data"],
            self._axis_values["x2_pixel"], self._axis_values["x2_data"],
            self._axis_values["y1_pixel"], self._axis_values["y1_data"],
            self._axis_values["y2_pixel"], self._axis_values["y2_data"],
        )

        self._is_setting_axis = False
        self._axis_step = 0
        self._axis_values = {}
        self.clear_calibration_overlay()
        self._show_status("坐标轴校准完成")

    def _add_data_point(self, x: float, y: float) -> None:
        if not self._extractor.coordinate_mapper.is_configured():
            self._show_warning("警告", "请先设置坐标轴")
            return

        try:
            point = self._extractor.add_point(x, y)
            self._add_canvas_point(x, y)
            self._show_status(
                f"已添加点：X={point.x_pixel:.2f}, Y={point.y_pixel:.2f}"
            )
        except ValueError as exc:
            self._show_warning("警告", str(exc))
