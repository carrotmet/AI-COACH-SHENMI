@echo off
chcp 65001 >nul
title 深寻觅 AI Coach - 开发模式

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
echo %BLUE%  深寻觅 AI Coach - 开发模式%RESET%
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

:: 检查并初始化数据库
echo %BLUE%[步骤] 检查数据库...%RESET%
cd /d "%BACKEND_DIR%"
"%VENV_DIR%\Scripts\python" -c "from database.connection import init_db; import asyncio; asyncio.run(init_db())"
if errorlevel 1 (
    echo %RED%[错误] 数据库初始化失败%RESET%
    pause
    exit /b 1
)
echo %GREEN%[OK] 数据库准备就绪%RESET%

:: 创建日志目录
if not exist "%PROJECT_DIR%logs" mkdir "%PROJECT_DIR%logs"

echo.
echo %BLUE%========================================%RESET%
echo %BLUE%  正在启动服务 (开发模式)...%RESET%
echo %BLUE%========================================%RESET%
echo.

:: 在单独的窗口中启动后端服务（带热重载）
echo %YELLOW%[启动] 后端服务 (端口: 8081, 热重载开启)...%RESET%
start "深寻觅 AI Coach - 后端(开发)" cmd /k "cd /d "%BACKEND_DIR%" && echo 正在启动后端服务... && "%VENV_DIR%\Scripts\python" -m uvicorn main:app --reload --host 0.0.0.0 --port 8081 --log-level info"
echo %GREEN%[OK] 后端服务已在新窗口启动%RESET%

:: 等待后端服务启动
timeout /t 2 /nobreak >nul

:: 在单独的窗口中启动前端服务
echo.
echo %YELLOW%[启动] 前端服务 (端口: 3001)...%RESET%
start "深寻觅 AI Coach - 前端(开发)" cmd /k "cd /d "%FRONTEND_DIR%" && echo 正在启动前端服务... && "%VENV_DIR%\Scripts\python" -m http.server 3001"
echo %GREEN%[OK] 前端服务已在新窗口启动%RESET%

echo.
echo %GREEN%========================================%RESET%
echo %GREEN%  开发服务启动成功！%RESET%
echo %GREEN%========================================%RESET%
echo.
echo %BLUE%访问地址:%RESET%
echo   - 前端页面: http://localhost:3001
echo   - 后端API:  http://localhost:8081
echo   - API文档:  http://localhost:8081/docs
    - 健康检查: http://localhost:8081/health
echo.
echo %YELLOW%说明:%RESET%
echo   - 后端服务已开启热重载，修改代码后会自动重启
echo   - 关闭服务窗口即可停止对应服务
echo   - 所有服务运行在新的命令行窗口中
echo.

pause
