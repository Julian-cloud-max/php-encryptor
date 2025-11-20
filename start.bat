@echo off
chcp 65001 > nul
title PHP文件加密工具

echo.
echo ========================================
echo    🔐 PHP文件加密工具
echo ========================================
echo.

echo 正在启动程序...
python run.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 程序启动失败！
    echo 请检查：
    echo 1. 是否已安装Python 3.8+
    echo 2. 是否已安装依赖包
    echo.
    pause
)