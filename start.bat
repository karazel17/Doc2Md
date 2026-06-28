@echo off
chcp 65001 >nul 2>&1
REM ============================================================
REM  Doc2Md 启动脚本 (Windows)
REM  双击此文件即可启动
REM ============================================================

if not exist "venv\" (
    echo 首次使用，正在安装依赖...
    call install.bat
)

call venv\Scripts\activate.bat

echo.
echo ==================================================
echo   Doc2Md 正在启动...
echo   桌面窗口即将显示
echo   关闭此窗口即可停止程序
echo ==================================================
echo.

python app.py
pause
