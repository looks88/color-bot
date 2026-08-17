@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title 达芬奇校色工具 - Nuitka编译（高性能EXE）

echo ============================================================
echo    达芬奇校色工具 - Nuitka 高性能编译
echo    编译为原生机器码，运行更快、体积更小
echo    注意：需要安装 MinGW64 或 Visual Studio Build Tools
echo ============================================================
echo.

set "WORK_DIR=%~dp0"
cd /d "%WORK_DIR%"

:: 检查Python
where python >nul 2>&1
if errorlevel 1 (
    echo [×] 未找到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

echo [1/4] 安装依赖...
pip install -r requirements.txt
pip install nuitka ordered-set zstandard

echo.
echo [2/4] 生成ICO图标...
python -c "from PIL import Image; img=Image.open('assets/icon.png'); img.save('assets/icon.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])" 2>nul
if not exist "assets/icon.ico" (
    echo   图标生成跳过（将使用默认图标）
    set "ICON_ARG="
) else (
    set "ICON_ARG=--windows-icon-from-ico=assets/icon.ico"
)

echo.
echo [3/4] 开始编译（首次编译较慢，约5-15分钟）...
python -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-console-mode=disable ^
    --enable-plugin=pyside6 ^
    --include-package=cv2 ^
    --include-package=numpy ^
    --include-data-dir=assets=assets ^
    --output-filename=达芬奇校色工具.exe ^
    --output-dir=dist_nuitka ^
    --remove-output ^
    --assume-yes-for-downloads ^
    %ICON_ARG% ^
    main.py

if errorlevel 1 (
    echo.
    echo [×] 编译失败
    echo   提示：Nuitka需要C编译器，请安装 MinGW-w64 或 Visual Studio Build Tools
    pause
    exit /b 1
)

echo.
echo [4/4] 编译完成！
echo.
echo ============================================================
echo    √ EXE 文件位置: %WORK_DIR%dist_nuitka\达芬奇校色工具.exe
echo ============================================================
echo.
explorer "dist_nuitka"
pause
