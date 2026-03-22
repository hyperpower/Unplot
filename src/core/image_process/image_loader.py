"""
图像加载模块
"""

from __future__ import annotations

import os
from typing import Optional, Tuple

import cv2
import numpy as np

from ..pipeline import PipelineContext, StepRegistry
from .base import ImageProcessStep, StepConfigField, StepPort


@StepRegistry.register
class ImageLoader(ImageProcessStep):
    """图像加载器类。"""

    SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif"]
    DEFAULT_OUTPUT_IMAGE_KEY = "image"
    DEFAULT_CONFIG = {
        "path": None,
        "image": DEFAULT_OUTPUT_IMAGE_KEY,
    }

    def __init__(
        self,
        *,
        name: str | None = None,
        enabled: bool = True,
        config: dict | None = None,
    ):
        merged_config = {**self.DEFAULT_CONFIG, **(config or {})}
        super().__init__(name=name, enabled=enabled, config=merged_config)
        self._image: Optional[np.ndarray] = None
        self._image_path: Optional[str] = None

    @property
    def image(self) -> Optional[np.ndarray]:
        return self._image

    @property
    def image_path(self) -> Optional[str]:
        return self._image_path

    @property
    def image_size(self) -> Optional[Tuple[int, int]]:
        if self._image is not None:
            return (self._image.shape[1], self._image.shape[0])
        return None

    @property
    def output_image_key(self) -> str:
        return str(self._get_config_value("image", self.DEFAULT_OUTPUT_IMAGE_KEY))

    @property
    def input_path(self) -> str | None:
        path = self._get_config_value("path")
        if path is None:
            return None
        normalized = str(path).strip()
        return normalized or None

    def describe_inputs(self) -> list[StepPort]:
        return [
            StepPort(
                name="path",
                direction="input",
                required=True,
                editable=True,
                editor="file",
                editor_options={
                    "title": "选择图像文件",
                    "filter": "图像文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.gif);;所有文件 (*)",
                },
                description="用户必须直接提供待加载的图像文件路径。",
            ),
        ]

    def describe_outputs(self) -> list[StepPort]:
        return [
            StepPort(
                name=self.output_image_key,
                direction="output",
                required=True,
                editable=False,
                description="加载后的 RGB 图像数组。",
            ),
        ]

    def describe_config(self) -> list[StepConfigField]:
        image_width, image_height = self.image_size or (None, None)
        status = "已执行" if self.image is not None else "未执行"
        return [
            StepConfigField(
                "status",
                status,
                editable=False,
                editor="readonly",
                description="指示图像加载步骤是否已经执行。",
            ),
            StepConfigField(
                "width",
                image_width,
                editable=False,
                editor="readonly",
                description="当前已加载图像的宽度。",
            ),
            StepConfigField(
                "height",
                image_height,
                editable=False,
                editor="readonly",
                description="当前已加载图像的高度。",
            ),
        ]

    def load(self, path: str) -> bool:
        """加载图像文件。"""
        try:
            self._validate_extension(path)

            image = cv2.imread(path, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("无法读取图像文件")

            self._image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self._image_path = path
            return True
        except Exception as exc:
            print(f"加载图像失败：{exc}")
            self._image = None
            self._image_path = None
            return False

    def unload(self) -> None:
        """卸载当前图像。"""
        self._image = None
        self._image_path = None

    def get_pixel(self, x: int, y: int) -> Optional[Tuple[int, int, int]]:
        """获取指定位置的像素值。"""
        if self._image is None:
            return None

        h, w = self._image.shape[:2]
        if 0 <= x < w and 0 <= y < h:
            return tuple(self._image[y, x].tolist())
        return None

    def format_output_display(self, output_name: str) -> str | None:
        """返回指定输出端口的运行时展示文本。"""
        if output_name != self.output_image_key:
            return None
        if self.image is None:
            return "未加载"
        return f"已加载: {self._format_memory_size(self.image.nbytes)}"

    def is_ready(self) -> bool:
        """判断当前输入是否已经准备好。"""
        path = self.input_path
        if not path:
            return False
        if not os.path.exists(path):
            return False
        if not os.path.isfile(path):
            return False
        if not os.access(path, os.R_OK):
            return False
        return True

    def inputs_check(self) -> list[str]:
        """检查输入是否完整，并返回提示信息。"""
        path = self.input_path
        messages: list[str] = []
        if not path:
            messages.append("请输入图像文件路径")
            return messages
        if not os.path.exists(path):
            messages.append(f"图像文件不存在: {path}")
            return messages
        if not os.path.isfile(path):
            messages.append(f"图像路径不是有效文件: {path}")
            return messages
        if not os.access(path, os.R_OK):
            messages.append(f"图像文件不可读取: {path}")
        return messages

    def run(self, context: PipelineContext) -> None:
        """根据配置中的路径加载图像。"""
        path = self.input_path
        if not path:
            raise ValueError("缺少图像路径，无法执行加载步骤")

        if not self.load(str(path)):
            raise ValueError(f"图像加载失败: {path}")

        self._publish_outputs(context)

    def _validate_extension(self, path: str) -> None:
        """校验输入路径的文件扩展名。"""
        ext = os.path.splitext(path)[1].lower()
        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的图像格式：{ext}")

    def _format_memory_size(self, size_bytes: int) -> str:
        """格式化图像内存占用。"""
        size_kb = size_bytes / 1024.0
        if size_kb > 500:
            return f"{size_kb / 1024.0:.2f} MB"
        return f"{size_kb:.1f} KB"

    def _publish_outputs(self, context: PipelineContext) -> None:
        """将加载结果发布到 PipelineContext。"""
        self._set_context_value(
            context,
            self.output_image_key,
            self._image,
        )
