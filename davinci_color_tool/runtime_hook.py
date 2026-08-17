# -*- coding: utf-8 -*-
"""
PyInstaller 运行时钩子
确保打包后 PySide6 插件路径正确设置
"""
import os
import sys

def _setup_pyside6_paths():
    """设置PySide6运行时路径"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        base_dir = sys._MEIPASS

        # 设置Qt插件路径
        plugin_path = os.path.join(base_dir, 'PySide6', 'plugins')
        if os.path.exists(plugin_path):
            os.environ['QT_PLUGIN_PATH'] = plugin_path

        # 设置Qt数据路径
        qt_dir = os.path.join(base_dir, 'PySide6')
        if os.path.exists(qt_dir):
            os.environ['QTDIR'] = qt_dir

        # 确保当前目录在PATH中（用于找到ffmpeg等dll）
        os.environ['PATH'] = base_dir + os.pathsep + os.environ.get('PATH', '')

_setup_pyside6_paths()
