@echo off
setlocal

set CONTAINER_NAME=postgres
set DB_USER=postgres
set DB_PASSWORD=postgres
set DB_NAME=postgres

set BACKUP_DIR=backup
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

if not exist %BACKUP_DIR% mkdir %BACKUP_DIR%

echo =========================
echo PostgreSQL Backup Start
echo =========================

docker exec -e PGPASSWORD=%DB_PASSWORD% %CONTAINER_NAME% ^
pg_dump -U %DB_USER% -d %DB_NAME% > %BACKUP_DIR%\db_%TIMESTAMP%.sql

echo Backup completed: %BACKUP_DIR%\db_%TIMESTAMP%.sql

endlocal