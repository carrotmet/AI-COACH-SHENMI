@echo off
chcp 65001 >nul
title 深寻觅 AI Coach - 停止服务

:: 颜色代码
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "RESET=[0m"

echo.
echo %BLUE%========================================%RESET%
echo %BLUE%  深寻觅 AI Coach - 停止服务%RESET%
echo %BLUE%========================================%RESET%
echo.

echo %YELLOW%[停止] 正在关闭后端服务...%RESET%
taskkill /FI "WINDOWTITLE eq 深寻觅 AI Coach - 后端服务*" /F >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%[信息] 后端服务未运行或已停止%RESET%
) else (
    echo %GREEN%[OK] 后端服务已停止%RESET%
)

echo %YELLOW%[停止] 正在关闭前端服务...%RESET%
taskkill /FI "WINDOWTITLE eq 深寻觅 AI Coach - 前端服务*" /F >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%[信息] 前端服务未运行或已停止%RESET%
) else (
    echo %GREEN%[OK] 前端服务已停止%RESET%
)

:: 也尝试停止开发模式的服务窗口
taskkill /FI "WINDOWTITLE eq 深寻觅 AI Coach - 后端(开发)*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 深寻觅 AI Coach - 前端(开发)*" /F >nul 2>&1

echo.
echo %GREEN%========================================%RESET%
echo %GREEN%  所有服务已停止！%RESET%
echo %GREEN%========================================%RESET%
echo.

pause
