#!/bin/bash
cd ../../../core-system/docker-compose || exit 1

docker compose -p cv-project -f docker-compose.yml --env-file ./env/.env down
docker compose -p cv-project -f docker-compose.yml --env-file ./env/.env build --no-cache
