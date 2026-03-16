"""
Pipeline 定义与执行逻辑。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .context import PipelineContext
from .registry import StepRegistry
from .step import PipelineStep


@dataclass
class PipelineExecutionRecord:
    """单个步骤的执行记录。"""

    step_name: str
    step_type: str
    success: bool
    skipped: bool = False
    error: str | None = None


@dataclass
class PipelineResult:
    """Pipeline 执行结果。"""

    success: bool
    pipeline_name: str
    context: PipelineContext
    records: list[PipelineExecutionRecord] = field(default_factory=list)


class Pipeline:
    """可编辑、可序列化的线性 pipeline。"""

    def __init__(self, name: str, steps: list[PipelineStep] | None = None):
        self.name = name
        self._steps: list[PipelineStep] = list(steps or [])

    @property
    def steps(self) -> list[PipelineStep]:
        """返回步骤列表副本。"""
        return list(self._steps)

    def add_step(self, step: PipelineStep) -> None:
        """在末尾添加步骤。"""
        self._steps.append(step)

    def insert_step(self, index: int, step: PipelineStep) -> None:
        """在指定位置插入步骤。"""
        self._steps.insert(index, step)

    def remove_step(self, index: int) -> PipelineStep:
        """移除并返回指定位置的步骤。"""
        return self._steps.pop(index)

    def clear_steps(self) -> None:
        """清空所有步骤。"""
        self._steps.clear()

    def move_step(self, old_index: int, new_index: int) -> None:
        """移动步骤顺序。"""
        step = self._steps.pop(old_index)
        self._steps.insert(new_index, step)

    def get_step(self, index: int) -> PipelineStep:
        """读取指定位置的步骤。"""
        return self._steps[index]

    def run(self, context: PipelineContext | None = None) -> PipelineResult:
        """按顺序执行所有启用的步骤。"""
        active_context = context or PipelineContext()
        records: list[PipelineExecutionRecord] = []

        for step in self._steps:
            if not step.enabled:
                records.append(
                    PipelineExecutionRecord(
                        step_name=step.name,
                        step_type=step.__class__.__name__,
                        success=True,
                        skipped=True,
                    )
                )
                continue

            try:
                step.validate(active_context)
                step.run(active_context)
                records.append(
                    PipelineExecutionRecord(
                        step_name=step.name,
                        step_type=step.__class__.__name__,
                        success=True,
                    )
                )
            except Exception as exc:
                records.append(
                    PipelineExecutionRecord(
                        step_name=step.name,
                        step_type=step.__class__.__name__,
                        success=False,
                        error=str(exc),
                    )
                )
                return PipelineResult(
                    success=False,
                    pipeline_name=self.name,
                    context=active_context,
                    records=records,
                )

        return PipelineResult(
            success=True,
            pipeline_name=self.name,
            context=active_context,
            records=records,
        )

    def to_dict(self) -> dict[str, Any]:
        """序列化 pipeline 定义。"""
        return {
            "name": self.name,
            "steps": [step.to_dict() for step in self._steps],
        }

    def load_from_dict(self, payload: dict[str, Any]) -> None:
        """从字典载入 pipeline 定义。"""
        self.name = payload.get("name", self.name)
        self.clear_steps()

        for item in payload.get("steps", []):
            step_type = item["type"]
            step_name = item.get("name", step_type)
            step = StepRegistry.create(
                step_type,
                name=step_name,
                enabled=item.get("enabled", True),
                config=item.get("config", {}),
            )
            self.add_step(step)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Pipeline":
        """从字典构建 pipeline。"""
        pipeline = cls(name=payload.get("name", "pipeline"))
        pipeline.load_from_dict(payload)
        return pipeline
