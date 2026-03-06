@echo off
setlocal

set ROOT=%~dp0

echo =========================
echo CV START SCRIPT
echo =========================

echo.
echo [1] Git Pull
call git-pull.bat

echo.
echo [2] Check Docker

docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker not running. Starting Docker Desktop...

    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

    echo Waiting for Docker to start...
    :docker_wait
    timeout /t 5 >nul
    docker info >nul 2>&1
    if %errorlevel% neq 0 goto docker_wait
)

echo Docker is running.


echo.
echo [3] Start core-system

cd /d "%~dp0core-system"
call cv-docker-compose-reload.bat

echo.
echo [4] Start desktop

cd /d "%~dp0desktop"

start "cv-desktop-1" cmd /k cv-pc-gui-load.bat
start "cv-desktop-2" cmd /k cv-webbot-load.bat


echo.
echo =========================
echo ALL SERVICES STARTED
echo =========================

@REM pause