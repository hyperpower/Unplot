"""
图像处理 step 基类。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

from ..pipeline import PipelineContext, PipelineStep


@dataclass(frozen=True)
class StepPort:
    """Step 输入/输出端口的描述。"""

    name: str
    direction: str
    required: bool = True
    editable: bool = False
    editor: str = "text"
    editor_options: dict[str, Any] | None = None
    description: str = ""


@dataclass(frozen=True)
class StepConfigField:
    """Step 配置项的描述。"""

    name: str
    default: Any = None
    editable: bool = False
    editor: str = "text"
    editor_options: dict[str, Any] | None = None
    description: str = ""


class ImageProcessStep(PipelineStep):
    """为图像处理步骤提供统一的配置与上下文辅助方法。"""

    def __init__(
        self,
        *,
        name: str | None = None,
        enabled: bool = True,
        config: dict[str, Any] | None = None,
    ):
        super().__init__(
            name=name or self.__class__.__name__,
            enabled=enabled,
            config=dict(config or {}),
        )

    def describe_inputs(self) -> list[StepPort]:
        """返回 step 的输入描述。"""
        return []

    def describe_outputs(self) -> list[StepPort]:
        """返回 step 的输出描述。"""
        return []

    def describe_config(self) -> list[StepConfigField]:
        """返回 step 的配置描述。"""
        return []

    def on_config_changed(self, key: str, value: Any) -> None:
        """当配置被 UI 修改后，同步运行时缓存。"""
        del key, value

    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """读取配置值。"""
        return self.config.get(key, default)

    def _require_context_value(
        self,
        context: PipelineContext,
        key: str,
    ) -> Any:
        """读取上下文中的必填值。"""
        value = context.get(key)
        if value is None:
            raise ValueError(f"上下文中缺少必需字段: {key}")
        return value

    def _set_context_value(
        self,
        context: PipelineContext,
        key: str,
        value: Any,
    ) -> None:
        """写入上下文值。"""
        context.set(key, value)

    def _ensure_rgb(self, image: np.ndarray) -> np.ndarray:
        """确保输入图像为 RGB。"""
        if image.ndim == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        if image.ndim == 3 and image.shape[2] == 3:
            return image.copy()
        if image.ndim == 3 and image.shape[2] == 4:
            return cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        raise ValueError("不支持的图像格式")

    def _convert_to_uint8(self, image: np.ndarray) -> np.ndarray:
        """将图像转换为 uint8。"""
        clipped = np.clip(image, 0, None)
        if clipped.size == 0:
            raise ValueError("输入图像不能为空")

        max_value = float(np.max(clipped))
        if max_value <= 1.0:
            clipped = clipped * 255.0
        elif max_value > 255.0:
            clipped = clipped / max_value * 255.0

        return clipped.astype(np.uint8)

    def _ensure_rgb_uint8(self, image: np.ndarray) -> np.ndarray:
        """确保输入图像为 RGB uint8。"""
        if image.dtype != np.uint8:
            image = self._convert_to_uint8(image)
        return self._ensure_rgb(image)
