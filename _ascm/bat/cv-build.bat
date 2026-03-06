@echo off
setlocal

set ROOT=%~dp0

echo =========================
echo CV BUILD SCRIPT
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
echo [3] build core-system

cd /d "%~dp0core-system"
call cv-docker-compose-build.bat


echo.
echo [4] build desktop

cd /d "%~dp0desktop"
call cv-pc-gui-build.bat
call cv-webbot-build.bat


echo.
echo =========================
echo ALL SERVICES BUILT
echo =========================

@REM pause