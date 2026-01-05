@echo off
cd ../../docker-compose
docker-compose -p cv-project -f docker-compose.yml --env-file ./env/.env down
docker-compose -p cv-project -f docker-compose.yml --env-file ./env/.env up -d