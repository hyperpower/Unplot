"""
Pipeline 运行上下文。
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineContext:
    """在 pipeline 各步骤之间传递共享数据。"""

    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """读取上下文数据。"""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """写入上下文数据。"""
        self.data[key] = value

    def update(self, values: dict[str, Any]) -> None:
        """批量更新上下文数据。"""
        self.data.update(values)

    def to_dict(self) -> dict[str, Any]:
        """序列化上下文。"""
        return {
            "data": dict(self.data),
            "metadata": dict(self.metadata),
        }
