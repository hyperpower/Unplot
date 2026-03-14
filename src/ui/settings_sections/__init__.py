"""
设置区域模块
"""

from .base import SettingsSection
from .sections import (
    AxisSettingsSection,
    CurveSettingsSection,
    ExportSettingsSection
)

__all__ = [
    "SettingsSection",
    "AxisSettingsSection",
    "CurveSettingsSection",
    "ExportSettingsSection"
]