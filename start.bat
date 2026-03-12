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
echo   浏览器将自动打开
echo   如未自动打开，请访问: http://127.0.0.1:7860
echo   关闭此窗口即可停止程序
echo ==================================================
echo.

python app.py
pause
