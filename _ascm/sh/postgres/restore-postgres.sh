#!/bin/bash

# 1. 환경 설정
CONTAINER_NAME="postgres"
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_NAME="postgres"

# 첫 번째 인자($1)를 백업 파일 경로로 설정
BACKUP_FILE=$1

# 2. 입력값 검증 (인자가 없는 경우 사용법 출력)
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./restore.sh backup/db_file.sql"
    exit 1
fi

echo "========================="
echo "PostgreSQL Restore Start"
echo "========================="

# 3. 데이터 복구 실행
# 'cat'으로 파일을 읽어 도커 컨테이너의 psql로 표준 입력을 전달합니다.
cat "$BACKUP_FILE" | docker exec -i -e PGPASSWORD="$DB_PASSWORD" "$CONTAINER_NAME" \
psql -U "$DB_USER" -d "$DB_NAME"

echo "Restore completed."