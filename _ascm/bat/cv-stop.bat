@echo off
setlocal

set ROOT=%~dp0

echo =========================
echo CV STOP SCRIPT
echo =========================

echo.
echo [3] Stop core-system

cd /d "%~dp0core-system"
call cv-docker-compose-down.bat

echo.
echo [4] Stop desktop

cd /d "%~dp0desktop"

taskkill /FI "WINDOWTITLE eq cv-desktop-1*" /F
taskkill /FI "WINDOWTITLE eq cv-desktop-2*" /F
taskkill /FI "WINDOWTITLE eq pc-gui*" /F
taskkill /FI "WINDOWTITLE eq webbot*" /F

@REM echo.
@REM echo [-] python 
@REM @REM taskkill /IM python.exe /F
@REM @REM taskkill /IM pythonw.exe /F

echo.
echo [5] Selenium 
taskkill /IM chromedriver.exe /F
taskkill /IM msedgedriver.exe /F

echo.
echo =========================
echo ALL SERVICES STOPED
echo =========================

@REM pause