@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title 达芬奇校色工具 - 一键打包EXE（全自动）

echo ============================================================
echo    达芬奇校色工具 - 全自动 Windows EXE 打包
echo    无需预先安装 Python，脚本将自动下载便携版环境
echo ============================================================
echo.

:: 设置工作目录
set "WORK_DIR=%~dp0"
set "PYTHON_DIR=%WORK_DIR%python_portable"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"
set "PYTHON_VERSION=3.11.9"
set "PYTHON_ARCH=amd64"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-%PYTHON_ARCH%.zip"
set "GET_PIP_URL=https://bootstrap.pypa.io/get-pip.py"
set "PYTHON_ZIP=%WORK_DIR%python_embed.zip"
set "GET_PIP=%WORK_DIR%get-pip.py"

:: 检查是否已有便携Python
if exist "%PYTHON_EXE%" (
    echo [√] 检测到已有便携版 Python，跳过下载
    goto :install_deps
)

echo [1/6] 正在下载便携版 Python %PYTHON_VERSION% ...
echo      下载地址: %PYTHON_URL%
echo.

:: 使用PowerShell下载
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_ZIP%' -UseBasicParsing}"
if not exist "%PYTHON_ZIP%" (
    echo [×] Python 下载失败，请检查网络连接
    echo     也可以手动下载后放到脚本同目录: %PYTHON_URL%
    pause
    exit /b 1
)

echo [2/6] 正在解压 Python ...
powershell -Command "Expand-Archive -Path '%PYTHON_ZIP%' -DestinationPath '%PYTHON_DIR%' -Force"
if not exist "%PYTHON_EXE%" (
    echo [×] Python 解压失败
    pause
    exit /b 1
)
del "%PYTHON_ZIP%" /q 2>nul

:: 配置pip（embeddable版本需要特殊处理）
echo [3/6] 正在配置 pip ...

:: 下载get-pip.py
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%GET_PIP_URL%' -OutFile '%GET_PIP%' -UseBasicParsing}"

:: 修改python311._pth文件以启用site-packages
set "PTH_FILE=%PYTHON_DIR%\python311._pth"
if exist "%PTH_FILE%" (
    echo import site>> "%PTH_FILE%"
)

"%PYTHON_EXE%" "%GET_PIP%" --no-warn-script-location
del "%GET_PIP%" /q 2>nul

:install_deps
echo.
echo [4/6] 正在安装项目依赖（首次运行较慢，请耐心等待）...
"%PYTHON_EXE%" -m pip install --upgrade pip --no-warn-script-location >nul 2>&1
"%PYTHON_EXE%" -m pip install -r "%WORK_DIR%requirements.txt" --no-warn-script-location
"%PYTHON_EXE%" -m pip install pyinstaller --no-warn-script-location

if errorlevel 1 (
    echo [×] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo [5/6] 正在生成应用图标...
"%PYTHON_EXE%" -m pip install pillow --no-warn-script-location >nul 2>&1
"%PYTHON_EXE%" -c "from PIL import Image; img=Image.open(r'%WORK_DIR%assets\icon.png'); img.save(r'%WORK_DIR%assets\icon.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])" 2>nul
if exist "%WORK_DIR%assets\icon.ico" (
    echo [√] 图标已生成
) else (
    echo [!] 图标生成跳过，将使用默认图标
)

echo.
echo [6/6] 正在打包 EXE（这一步可能需要 2-5 分钟）...
cd /d "%WORK_DIR%"
"%PYTHON_EXE%" -m PyInstaller --clean --noconfirm build.spec

if errorlevel 1 (
    echo [×] 打包失败
    pause
    exit /b 1
)

echo.
echo [6/6] 打包完成！
echo.
echo ============================================================
echo    √ EXE 文件位置: %WORK_DIR%dist\达芬奇校色工具.exe
echo ============================================================
echo.
echo 正在打开输出目录...
explorer "%WORK_DIR%dist"
echo.
pause
