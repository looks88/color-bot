@echo off
chcp 65001 >nul
title 达芬奇校色工具 - 开发运行模式

cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 正在检查依赖...
python -c "import PySide6, cv2, numpy" 2>nul
if errorlevel 1 (
    echo 首次运行，正在安装依赖...
    pip install -r requirements.txt
)

echo.
echo 启动达芬奇校色工具...
python main.py

if errorlevel 1 (
    echo.
    echo 程序异常退出，按任意键关闭...
    pause
)
