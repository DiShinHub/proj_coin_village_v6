@echo off

cd ../../

git pull origin master

git add .

git commit -m "."

git push -u origin master

REM 작업 완료 메시지 출력
echo Git Pushed!