@echo off
setlocal

set CONTAINER_NAME=postgres
set DB_USER=postgres
set DB_PASSWORD=postgres
set DB_NAME=postgres

set BACKUP_FILE=%1

if "%BACKUP_FILE%"=="" (
    echo Usage: restore-postgres.bat backup\db_file.sql
    exit /b
)

echo =========================
echo PostgreSQL Restore Start
echo =========================

type %BACKUP_FILE% | docker exec -i -e PGPASSWORD=%DB_PASSWORD% %CONTAINER_NAME% ^
psql -U %DB_USER% -d %DB_NAME%

echo Restore completed.

endlocal