"""
数据面板模块
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, 
    QFrame, QSplitter, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

from core.image_process import StepConfigField, StepPort
from core.image_process.image_loader import ImageLoader
from core.pipeline import Pipeline
from core.pipeline.step import PipelineStep

from .property_table import PropertyRow, PropertyTableWidget
from .work_tree import WorkTreeWidget


class DataPanel(QFrame):
    """数据面板组件
    
    位于左侧导航栏右侧，包含树状结构和属性列表。
    支持展开/收起状态切换。
    """

    property_description_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_expanded = True
        self._tree: WorkTreeWidget | None = None
        self._prop_table: PropertyTableWidget | None = None
        self._current_object = None
        self._init_ui()
        self.tree_widget.currentItemChanged.connect(self._on_current_item_changed)
        self.tree_widget.step_run_finished.connect(self._on_step_run_finished)
        self.prop_widget.description_changed.connect(self.property_description_changed.emit)
        self.prop_widget.value_changed.connect(self._on_property_value_changed)
        
    def _init_ui(self):
        """初始化 UI"""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setLineWidth(1)
        self.setMinimumWidth(200)
        self.setMaximumWidth(400)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建垂直分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 上半部分：树状结构
        tree_widget = self._create_tree_widget()
        splitter.addWidget(tree_widget)
        
        # 下半部分：属性列表
        prop_widget = self._create_property_widget()
        splitter.addWidget(prop_widget)
        
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
    def _create_tree_widget(self) -> QWidget:
        """创建树状结构组件"""
        # 标题栏
        title_label = QLabel("图层结构")
        # title_label.setFixedHeight(36)
        
        # 树状控件
        self._tree = WorkTreeWidget()
        
        # 容器
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(title_label)
        layout.addWidget(self._tree)
        
        # 设置容器尺寸策略为撑满父控件（水平和垂直方向都扩展）
        container.setSizePolicy(QSizePolicy.Expanding,
                               QSizePolicy.Expanding)
        
        return container
        
    def _create_property_widget(self) -> QWidget:
        """创建属性列表组件"""
        # 标题栏
        title_label = QLabel("属性")
        # title_label.setFixedHeight(36)
        
        # 属性表格
        self._prop_table = PropertyTableWidget()
        self._set_properties(
            [
                PropertyRow(
                    label="名称",
                    key=None,
                    value="未选择节点",
                    display_text="未选择节点",
                    source="basic",
                    editable=False,
                    editor="readonly",
                    editor_options={},
                )
            ]
        )
        
        # 容器
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(title_label)
        layout.addWidget(self._prop_table)
        
        # 设置容器尺寸策略为撑满父控件（水平和垂直方向都扩展）
        container.setSizePolicy(QSizePolicy.Expanding,
                               QSizePolicy.Expanding)
        
        return container
        
    @property
    def tree_widget(self) -> WorkTreeWidget:
        """返回工作树控件。"""
        if self._tree is None:
            raise RuntimeError("工作树尚未初始化")
        return self._tree

    @property
    def prop_widget(self) -> PropertyTableWidget:
        """返回属性表格控件。"""
        if self._prop_table is None:
            raise RuntimeError("属性表格尚未初始化")
        return self._prop_table

    def set_pipeline(self, pipeline: Pipeline) -> None:
        """绑定 pipeline 并刷新工作树与属性面板。"""
        self.tree_widget.set_pipeline(pipeline)

        root_item = self.tree_widget.root_item
        if root_item is not None:
            self.tree_widget.setCurrentItem(root_item)
            self._show_object_properties(self.tree_widget.get_item_payload(root_item))

    def _on_current_item_changed(self, current, previous) -> None:
        """根据当前选中节点刷新属性。"""
        del previous
        self._show_object_properties(self.tree_widget.get_item_payload(current))

    def _show_object_properties(self, obj) -> None:
        """将 pipeline 或 step 的属性展示到表格。"""
        self._current_object = obj
        if isinstance(obj, Pipeline):
            properties = [
                self._readonly_row("类型", "Pipeline", source="basic"),
                self._readonly_row("名称", obj.name, source="basic"),
                self._readonly_row("步骤数", len(obj.steps), source="basic"),
            ]
            self._set_properties(properties)
            return

        if isinstance(obj, PipelineStep):
            properties: list[PropertyRow] = [
                self._readonly_row("类型", obj.__class__.__name__, source="basic"),
                self._readonly_row("名称", obj.name, source="basic"),
                self._readonly_row("启用", obj.enabled, source="basic"),
            ]

            input_ports = obj.describe_inputs()
            output_ports = obj.describe_outputs()
            config_fields = obj.describe_config()

            if input_ports:
                for port in input_ports:
                    properties.append(self._port_row(obj, port))

            if output_ports:
                for port in output_ports:
                    properties.append(self._output_row(obj, port))

            if config_fields:
                for field in config_fields:
                    properties.append(self._config_row(obj, field))
            else:
                for key, value in obj.config.items():
                    properties.append(
                        self._readonly_row(
                            f"配置.{key}",
                            value,
                            source="config",
                        )
                    )
            self._set_properties(properties)
            return

        self._set_properties(
            [
                PropertyRow(
                    label="名称",
                    key=None,
                    value="未选择节点",
                    display_text="未选择节点",
                    source="basic",
                    editable=False,
                    editor="readonly",
                    editor_options={},
                )
            ]
        )

    def _set_properties(self, properties: list[PropertyRow]) -> None:
        """刷新属性表格。"""
        self.prop_widget.set_properties(properties)

    def _readonly_row(
        self,
        label: str,
        value,
        *,
        source: str,
        description: str = "",
    ) -> PropertyRow:
        return PropertyRow(
            label=label,
            key=None,
            value=value,
            display_text=self._format_value(value),
            source=source,
            editable=False,
            editor="readonly",
            editor_options={},
            description=description,
        )

    def _config_row(self, step: PipelineStep, field: StepConfigField) -> PropertyRow:
        active_value = step.config.get(field.name, field.default)
        editor = field.editor if field.editable else "readonly"
        return PropertyRow(
            label=f"配置.{field.name}",
            key=field.name,
            value=active_value,
            display_text=self._format_value_for_editor(active_value, editor),
            source="config",
            editable=field.editable,
            editor=editor,
            editor_options=dict(field.editor_options or {}),
            description=field.description,
        )

    def _port_row(self, step: PipelineStep, port: StepPort) -> PropertyRow:
        if not port.editable:
            return self._readonly_row(
                f"{'输入' if port.direction == 'input' else '输出'}.{port.name}",
                self._format_port(port),
                source="port",
                description=port.description,
            )

        active_value = step.config.get(port.name)
        return PropertyRow(
            label=f"{'输入' if port.direction == 'input' else '输出'}.{port.name}",
            key=port.name,
            value=active_value,
            display_text=self._format_value_for_editor(active_value, port.editor),
            source="port",
            editable=True,
            editor=port.editor,
            editor_options=dict(port.editor_options or {}),
            description=port.description,
        )

    def _output_row(self, step: PipelineStep, port: StepPort) -> PropertyRow:
        value = self._format_output_value(step, port)
        return self._readonly_row(
            f"输出.{port.name}",
            value,
            source="port",
            description=port.description,
        )

    def _format_value(self, value) -> str:
        """统一格式化属性值。"""
        if isinstance(value, bool):
            return "是" if value else "否"
        if value is None:
            return "None"
        return str(value)

    def _format_port(self, port: StepPort) -> str:
        """格式化 step 输入/输出端口描述。"""
        return "必需" if port.required else "可选"

    def _format_output_value(self, step: PipelineStep, port: StepPort) -> str:
        if isinstance(step, ImageLoader) and port.name == step.output_image_key:
            output_text = step.format_output_display(port.name)
            if output_text is not None:
                return output_text
        return self._format_port(port)

    def _format_value_for_editor(self, value, editor: str) -> str:
        if editor == "file":
            return Path(str(value)).name if value else ""
        if editor == "color":
            return str(value or "")
        return self._format_value(value)

    def _on_property_value_changed(self, key: str, value) -> None:
        if not isinstance(self._current_object, PipelineStep):
            return
        self._current_object.config[key] = value
        self._current_object.on_config_changed(key, value)
        self._sync_current_step_status()
        self._show_object_properties(self._current_object)

    def _sync_current_step_status(self) -> None:
        """根据当前 step 的输入准备情况更新工作树状态。"""
        current_item = self.tree_widget.currentItem()
        if current_item is None:
            return
        current_step = self.tree_widget.get_item_payload(current_item)
        if current_step is not self._current_object:
            return

        is_ready = getattr(self._current_object, "is_ready", None)
        if callable(is_ready):
            status = "ready" if is_ready() else "init"
            self.tree_widget.set_item_status(current_item, status)

    def _on_step_run_finished(self, step, context) -> None:
        """在 step 执行完成后刷新当前属性面板。"""
        del context
        if step is self._current_object:
            self._show_object_properties(step)

    def _apply_property_column_widths(self, first_width: int, *, total_width: int | None = None) -> None:
        """兼容旧接口，代理到属性表控件。"""
        self.prop_widget.apply_column_widths(first_width, total_width=total_width)

    def _property_total_width(self) -> int:
        """兼容旧接口，返回属性表当前两列可分配的总宽度。"""
        return self.prop_widget.property_total_width()
            
    def set_expanded(self, expanded: bool):
        """设置面板展开/收起状态"""
        self._is_expanded = expanded
        self.setVisible(expanded)
        
    def is_expanded(self) -> bool:
        """返回当前展开状态"""
        return self._is_expanded
    
    def toggle(self):
        """切换展开/收起状态"""
        self._is_expanded = not self._is_expanded
        self.setVisible(self._is_expanded)
