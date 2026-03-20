#!/bin/bash

APP_NAME=cv-llm-bridge-app
APP_ACTIVE_ENV=local
APP_PORT=8001
APP_CONTAINER_PORT=$1

if [ -z "${APP_CONTAINER_PORT}" ]; then
  APP_CONTAINER_PORT=8001
fi

docker stop $APP_NAME
docker rm $APP_NAME
docker build --no-cache -t $APP_NAME -f ../docker/Dockerfile ../.
docker run -d -e APP_ACTIVE_ENV=$APP_ACTIVE_ENV -e APP_PORT=$APP_PORT -e APP_LOG_LOCATION=/apps/logs/$APP_NAME -p $APP_CONTAINER_PORT:$APP_PORT --name $APP_NAME $APP_NAME
