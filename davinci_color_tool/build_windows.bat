@echo off
chcp 65001 >nul
echo ========================================
echo   达芬奇校色工具 - Windows EXE 打包脚本
echo ========================================
echo.

echo [1/4] 检查 Python 环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

echo.
echo [2/4] 安装依赖...
pip install -r requirements.txt
pip install pyinstaller
if errorlevel 1 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)

echo.
echo [3/4] 开始打包（单文件模式）...
pyinstaller --clean --noconfirm build.spec
if errorlevel 1 (
    echo 错误: 打包失败
    pause
    exit /b 1
)

echo.
echo [4/4] 打包完成！
echo.
echo 可执行文件位置: dist\达芬奇校色工具.exe
echo.
echo ========================================
echo   打包完成，按任意键打开输出目录
echo ========================================
pause
explorer dist
