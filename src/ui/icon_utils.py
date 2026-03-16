"""
UI 图标工具函数。
"""

from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QToolButton


ICON_DIR = Path(__file__).resolve().parents[2] / "assets" / "icons"


def get_icon_path(icon_name: str) -> Path:
    """返回图标文件路径。"""
    return ICON_DIR / f"{icon_name}.svg"


def set_button_icon(
    button: QToolButton,
    icon_path: Path,
    icon_size: QSize,
    color: QColor | None = None,
) -> None:
    """根据当前主题颜色渲染 SVG 图标并设置到按钮。"""
    try:
        svg_text = icon_path.read_text(encoding="utf-8")
    except OSError:
        button.setIcon(QIcon(str(icon_path)))
        button.setIconSize(icon_size)
        return

    icon_color = color or button.palette().buttonText().color()
    svg_text = svg_text.replace("currentColor", icon_color.name())
    renderer = QSvgRenderer(QByteArray(svg_text.encode("utf-8")))
    dpr = button.devicePixelRatioF()
    pixel_size = QSize(
        max(1, int(icon_size.width() * dpr)),
        max(1, int(icon_size.height() * dpr)),
    )

    pixmap = QPixmap(pixel_size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()

    pixmap.setDevicePixelRatio(dpr)
    button.setIcon(QIcon(pixmap))
    button.setIconSize(icon_size)
