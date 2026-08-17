# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 - 达芬奇校色工具
在 Windows 上执行: pyinstaller --clean --noconfirm build.spec
"""
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

# ========== 收集隐式导入 ==========
hiddenimports = [
    'cv2',
    'numpy',
    'numpy.core._methods',
    'numpy.lib.format',
    'scipy',
    'scipy._lib._ccallback',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtSvg',
    'PySide6.QtSvgWidgets',
    'imageio',
    'imageio_ffmpeg',
    'imageio.plugins.ffmpeg',
    'PIL',
    'PIL.Image',
]

# 收集PySide6子模块
hiddenimports += collect_submodules('PySide6.QtCore')
hiddenimports += collect_submodules('PySide6.QtGui')
hiddenimports += collect_submodules('PySide6.QtWidgets')

# ========== 收集数据文件和动态库 ==========
datas = []
binaries = []

# OpenCV相关
datas += collect_data_files('cv2')
binaries += collect_dynamic_libs('cv2')

# imageio-ffmpeg
datas += collect_data_files('imageio_ffmpeg')
binaries += collect_dynamic_libs('imageio_ffmpeg')

# PySide6插件（平台插件、样式等）
pyside6_plugins = os.path.join(os.path.dirname(__import__('PySide6').__file__), 'plugins')
if os.path.exists(pyside6_plugins):
    # 平台插件
    platforms_dir = os.path.join(pyside6_plugins, 'platforms')
    if os.path.exists(platforms_dir):
        for f in os.listdir(platforms_dir):
            if f.endswith('.dll'):
                binaries.append((os.path.join(platforms_dir, f), 'PySide6/plugins/platforms'))
    # 样式插件
    styles_dir = os.path.join(pyside6_plugins, 'styles')
    if os.path.exists(styles_dir):
        for f in os.listdir(styles_dir):
            if f.endswith('.dll'):
                binaries.append((os.path.join(styles_dir, f), 'PySide6/plugins/styles'))
    # 图片格式插件
    imageformats_dir = os.path.join(pyside6_plugins, 'imageformats')
    if os.path.exists(imageformats_dir):
        for f in os.listdir(imageformats_dir):
            if f.endswith('.dll'):
                binaries.append((os.path.join(imageformats_dir, f), 'PySide6/plugins/imageformats'))

# ========== Analysis ==========
a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[
        'tkinter',
        'matplotlib',
        'pandas',
        'sympy',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuick3D',
        'PySide6.QtWebEngine',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtBluetooth',
        'PySide6.QtPositioning',
        'PySide6.QtSensors',
        'PySide6.QtSerialPort',
        'PySide6.QtTest',
        'PySide6.QtSql',
        'PySide6.QtOpenGL',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DRender',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DAnimation',
        'PySide6.Qt3DExtras',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtNetwork',
        'PySide6.QtNetworkAuth',
        'PySide6.QtMqtt',
        'PySide6.QtCoap',
        'PySide6.QtOpcua',
        'PySide6.QtTextToSpeech',
        'PySide6.QtVirtualKeyboard',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'PySide6.QtPrintSupport',
        'PySide6.QtDesigner',
        'PySide6.QtHelp',
        'PySide6.QtUiTools',
        'PySide6.QtXml',
        'PySide6.QtXmlPatterns',
        'PySide6.QtStateMachine',
        'PySide6.QtScxml',
        'PySide6.QtRemoteObjects',
        'PySide6.QtNfc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ========== EXE ==========
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='达芬奇校色工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        'Qt6Core.dll',
        'Qt6Gui.dll',
        'Qt6Widgets.dll',
        'opencv_world*.dll',
        'ffmpeg*.dll',
        'python311.dll',
    ],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)
