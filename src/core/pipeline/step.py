"""
Pipeline 步骤基类。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from .context import PipelineContext


@dataclass
class PipelineStep(ABC):
    """单个 pipeline 步骤的抽象定义。"""

    name: str
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)

    def validate(self, context: PipelineContext) -> None:
        """执行前校验，默认不做额外处理。"""

    @abstractmethod
    def run(self, context: PipelineContext) -> None:
        """执行步骤逻辑。"""

    def to_dict(self) -> dict[str, Any]:
        """序列化步骤定义。"""
        return {
            "type": self.__class__.__name__,
            "name": self.name,
            "enabled": self.enabled,
            "config": dict(self.config),
        }
