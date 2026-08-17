# -*- coding: utf-8 -*-
"""
达芬奇校色工具 - DaVinci Color Studio
专业视频校色、自动场景剪切、风格化滤镜处理工具
"""
import sys
import os

# ========== 打包环境路径修复（必须在导入PySide6之前）==========
def _fix_frozen_paths():
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
        # PySide6插件路径
        plugin_path = os.path.join(base, 'PySide6', 'plugins')
        if os.path.exists(plugin_path):
            os.environ['QT_PLUGIN_PATH'] = plugin_path
        # 确保能找到同目录下的dll
        os.environ['PATH'] = base + os.pathsep + os.environ.get('PATH', '')

_fix_frozen_paths()

# 确保使用高DPI缩放
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from gui import MainWindow


def main():
    # 高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("DaVinci Color Studio")
    app.setOrganizationName("ColorStudio")

    # 设置默认字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
