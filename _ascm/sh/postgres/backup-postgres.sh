#!/bin/bash

# 1. 환경 설정
CONTAINER_NAME="postgres"
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_NAME="postgres"

BACKUP_DIR="backup"
# 날짜 포맷: YYYYMMDD_HHMMSS (리눅스 date 명령어로 간단히 처리)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 2. 백업 디렉토리 생성 (-p 옵션은 폴더가 없으면 만들고 있으면 무시함)
mkdir -p "$BACKUP_DIR"

echo "========================="
echo "PostgreSQL Backup Start"
echo "========================="

# 3. Docker 내에서 pg_dump 실행
# 팁: 이전 질문에서 말씀하신 'INSERT' 형태가 필요하다면 pg_dump 뒤에 --column-inserts 를 추가하세요.
docker exec -e PGPASSWORD="$DB_PASSWORD" "$CONTAINER_NAME" \
pg_dump -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_DIR/db_$TIMESTAMP.sql"

echo "Backup completed: $BACKUP_DIR/db_$TIMESTAMP.sql"