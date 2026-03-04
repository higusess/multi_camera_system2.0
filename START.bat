@echo off
chcp 65001 >nul
echo ========================================
echo    多相机采集系统 - 快速启动
echo ========================================
echo.
echo 按任意键启动程序...
pause >nul

python multi_camera_capture.py

echo.
echo 程序已退出，按任意键关闭...
pause >nul
