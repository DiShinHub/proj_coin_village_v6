@echo off

set APP_NAME=cv-cv-llm-bridge-hub-app
set APP_ACTIVE_ENV=local
set APP_PORT=8001
set APP_CONTAINER_PORT=%1

IF "%APP_CONTAINER_PORT%"=="" (
    set APP_CONTAINER_PORT=8001
)

docker stop %APP_NAME%
docker rm %APP_NAME%
docker build --no-cache -t %APP_NAME% -f ../docker/Dockerfile ../.
docker run -d -e APP_ACTIVE_ENV=%APP_ACTIVE_ENV% -e APP_PORT=%APP_PORT% -e APP_LOG_LOCATION=/apps/logs/%APP_LOG_LOCATION% -p %APP_CONTAINER_PORT%:%APP_PORT% --name %APP_NAME% %APP_NAME%
