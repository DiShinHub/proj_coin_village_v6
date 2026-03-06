@echo off
cd ../../../core-system/docker-compose
docker-compose -p cv-project -f docker-compose.yml --env-file ./env/.env down