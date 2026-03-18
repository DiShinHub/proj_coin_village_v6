# PostgreSQL Backup & Restore (Docker)
PostgreSQL 데이터를 Docker 컨테이너에서 **Batch Script로 백업 / 복원**하는 간단한 도구입니다.

# Environment
HOST=localhost
PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

PostgreSQL은 Docker 컨테이너에서 실행됩니다.

# Files
backup-postgres.bat
restore-postgres.bat

| Script               | Description |
| -------------------- | ----------- |
| backup-postgres.bat  | DB 전체 백업  |
| restore-postgres.bat | SQL 파일 복원 |

# Backup
backup-postgres.bat
실행하면 `backup` 폴더에 SQL 파일이 생성됩니다.

backup/
 ├ db_20260306_170500.sql
 ├ db_20260305_230210.sql

파일 형식
db_YYYYMMDD_HHMMSS.sql

# Restore
restore-postgres.bat backup\db_20260306_170500.sql
지정한 SQL 파일을 데이터베이스에 복원합니다.

# Requirements
* Docker
* PostgreSQL container running
docker ps

# Workflow
# backup
backup-postgres.bat

# move file
다른 PC, 혹은 서버에서 작업일 때 물리적으로 이관 필요

# Directory Example
_ascm
 ├ bat
 │   ├ backup-postgres.bat
 │   ├ restore-postgres.bat
 │
 └ backup
     └ postgres

# Notes
* 아직 테스팅 전으로 안돌아갈 수 있습니다.