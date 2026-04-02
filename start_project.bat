@echo off
chcp 65001 >nul
title 深寻觅 AI Coach - 项目启动器

setlocal enabledelayedexpansion

:: 设置路径
set "PROJECT_DIR=%~dp0"
set "VENV_DIR=%PROJECT_DIR%.venv"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "FRONTEND_DIR=%PROJECT_DIR%frontend"
set "DATA_DIR=%PROJECT_DIR%data"

:: 颜色代码
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "RESET=[0m"

echo.
echo %BLUE%========================================%RESET%
echo %BLUE%  深寻觅 AI Coach - 项目启动器%RESET%
echo %BLUE%========================================%RESET%
echo.

:: 检查虚拟环境
if not exist "%VENV_DIR%" (
    echo %RED%[错误] 虚拟环境不存在: %VENV_DIR%%RESET%
    echo %YELLOW%请先创建虚拟环境并安装依赖:%RESET%
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r backend\requirements.txt
    pause
    exit /b 1
)

echo %GREEN%[OK] 虚拟环境已找到%RESET%

:: 检查数据库文件，如不存在则初始化
set "DB_FILE=%DATA_DIR%\ai_coach.db"
set "NEED_INIT_DB=0"

if not exist "%DB_FILE%" (
    echo %YELLOW%[信息] 数据库文件不存在，需要初始化%RESET%
    set "NEED_INIT_DB=1"
) else (
    echo %GREEN%[OK] 数据库文件已存在%RESET%
)

:: 初始化数据库
if "%NEED_INIT_DB%"=="1" (
    echo.
    echo %BLUE%[步骤] 正在初始化数据库...%RESET%
    cd /d "%BACKEND_DIR%"
    "%VENV_DIR%\Scripts\python" -c "from database.connection import init_db; import asyncio; asyncio.run(init_db())"
    if errorlevel 1 (
        echo %RED%[错误] 数据库初始化失败%RESET%
        pause
        exit /b 1
    )
    echo %GREEN%[OK] 数据库初始化完成%RESET%
    cd /d "%PROJECT_DIR%"
)

:: 创建日志目录
if not exist "%PROJECT_DIR%logs" mkdir "%PROJECT_DIR%logs"

echo.
echo %BLUE%========================================%RESET%
echo %BLUE%  正在启动服务...%RESET%
echo %BLUE%========================================%RESET%
echo.

:: 启动后端服务
echo %YELLOW%[启动] 后端服务 (端口: 8081)...%RESET%
start "深寻觅 AI Coach - 后端服务" /min cmd /c "cd /d "%BACKEND_DIR%" && "%VENV_DIR%\Scripts\python" main.py > "%PROJECT_DIR%logs\backend.log" 2>&1"
if errorlevel 1 (
    echo %RED%[错误] 后端服务启动失败%RESET%
    pause
    exit /b 1
)
echo %GREEN%[OK] 后端服务已启动%RESET%
echo   - 访问地址: http://localhost:8081
echo   - API文档:  http://localhost:8081/docs
echo   - 日志文件: logs\backend.log

:: 等待后端服务完全启动
echo %YELLOW%[等待] 等待后端服务就绪...%RESET%
timeout /t 3 /nobreak >nul

:: 启动前端服务
echo.
echo %YELLOW%[启动] 前端服务 (端口: 3001)...%RESET%
start "深寻觅 AI Coach - 前端服务" /min cmd /c "cd /d "%FRONTEND_DIR%" && "%VENV_DIR%\Scripts\python" -m http.server 3001 > "%PROJECT_DIR%logs\frontend.log" 2>&1"
if errorlevel 1 (
    echo %RED%[错误] 前端服务启动失败%RESET%
    pause
    exit /b 1
)
echo %GREEN%[OK] 前端服务已启动%RESET%
echo   - 访问地址: http://localhost:3001
echo   - 日志文件: logs\frontend.log

echo.
echo %GREEN%========================================%RESET%
echo %GREEN%  所有服务启动成功！%RESET%
echo %GREEN%========================================%RESET%
echo.
echo %BLUE%访问地址:%RESET%
echo   - 前端页面: http://localhost:3001
echo   - 后端API:  http://localhost:8081
echo   - API文档:  http://localhost:8081/docs
echo.
echo %YELLOW%提示:%RESET%
echo   - 按任意键停止所有服务
echo   - 日志文件保存在 logs 目录
echo.

pause >nul

:: 停止服务
echo.
echo %YELLOW%[停止] 正在关闭服务...%RESET%
taskkill /FI "WINDOWTITLE eq 深寻觅 AI Coach - 后端服务*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 深寻觅 AI Coach - 前端服务*" /F >nul 2>&1
echo %GREEN%[OK] 所有服务已停止%RESET%

echo.
pause
