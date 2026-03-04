@echo off
chcp 65001 >nul
echo ========================================
echo    清理相机占用进程
echo ========================================
echo.

echo 正在清理Python进程...
taskkill /F /IM python.exe 2>nul

echo 正在清理海康相机进程...
taskkill /F /IM MvCameraControl.exe 2>nul
taskkill /F /IM MVS.exe 2>nul

echo.
echo 清理完成！按任意键继续...
pause >nul
