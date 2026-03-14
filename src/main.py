"""
Unplot - 从图像中提取数据点的 PySide6 应用程序

主程序入口
"""

import sys
import os

# 添加 src 目录到路径
src_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, src_path)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


def main():
    """主函数"""
    # 启用高 DPI 支持
    Qt.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("Unplot")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Unplot Team")
    
    # 导入并创建主窗口
    from ui.main_window import MainWindow
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()