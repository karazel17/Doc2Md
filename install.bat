@echo off
chcp 65001 >nul 2>&1
REM ============================================================
REM  Doc2Md 一键安装脚本 (Windows)
REM ============================================================

echo.
echo ==================================================
echo   Doc2Md 安装程序
echo ==================================================
echo.

REM 检查 Python
echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo   未找到 Python
    echo   请从 https://www.python.org/downloads/ 下载安装 Python 3.9-3.12
    echo   安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

python --version

REM 创建虚拟环境
echo.
echo [2/3] 创建虚拟环境...
if exist "venv\" (
    echo   虚拟环境已存在
) else (
    python -m venv venv
    echo   虚拟环境已创建
)

REM 激活并安装依赖
echo.
echo [3/3] 安装依赖...
call venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo.
echo ==================================================
echo   安装完成！
echo ==================================================
echo.
echo   启动方法: 双击 start.bat
echo.
pause
