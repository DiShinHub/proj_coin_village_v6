@echo off

cd ../../docker-compose/env

REM .env 로드
set ENV_FILE=.\.env

for /f "usebackq tokens=1,* delims==" %%A in ("%ENV_FILE%") do (
    if not "%%A"=="" set %%A=%%B
)

REM db 설정
cd ../../_ascm/sql
set PGHOST="localhost"
set PGPORT=%POSTGRES_CONTAINER_PORT%
set PGUSER=%POSTGRES_USER%
set PGPASSWORD=%POSTGRES_PASSWORD%

docker exec -it CV-db-postgres-compose bash -c "psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -f './sql/create_tables.sql'"
docker exec -it CV-db-postgres-compose bash -c "psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -f './sql/insert_cols_runnable_services.sql'"
docker exec -it CV-db-postgres-compose bash -c "psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -f './sql/insert_cols_runnable_service_options.sql'"

set PGHOST=
set PGPORT=
set PGUSER=
set PGPASSWORD=
exit

echo All scripts executed.