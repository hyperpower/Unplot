"""
Pipeline 步骤注册表。
"""

from __future__ import annotations

from typing import Type

from .step import PipelineStep


class StepRegistry:
    """根据名称注册和创建 pipeline step。"""

    _registry: dict[str, Type[PipelineStep]] = {}

    @classmethod
    def register(cls, step_cls: Type[PipelineStep]) -> Type[PipelineStep]:
        """注册 step 类，支持装饰器用法。"""
        cls._registry[step_cls.__name__] = step_cls
        return step_cls

    @classmethod
    def unregister(cls, step_type: str) -> None:
        """移除已注册的 step 类。"""
        cls._registry.pop(step_type, None)

    @classmethod
    def is_registered(cls, step_type: str) -> bool:
        """判断 step 类型是否已注册。"""
        return step_type in cls._registry

    @classmethod
    def get_registered_types(cls) -> list[str]:
        """返回当前所有已注册 step 类型。"""
        return sorted(cls._registry.keys())

    @classmethod
    def create(
        cls,
        step_type: str,
        *,
        name: str,
        enabled: bool = True,
        config: dict | None = None,
    ) -> PipelineStep:
        """根据注册信息实例化 step。"""
        if step_type not in cls._registry:
            raise ValueError(f"未注册的 pipeline step 类型: {step_type}")

        step_cls = cls._registry[step_type]
        return step_cls(
            name=name,
            enabled=enabled,
            config=config or {},
        )
