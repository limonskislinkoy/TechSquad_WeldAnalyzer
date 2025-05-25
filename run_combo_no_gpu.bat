@echo off
chcp 65001 > nul

echo Сборка Docker-образа...
docker build -t combo:latest .

echo Запуск контейнера...
docker run -d --name combo -p 8000:8000 combo:latest

echo.
echo Готово! Контейнер запущен на порту 8000
echo Для доступа к веб-интерфейсу перейдите по одной из ссылок:
echo http://localhost:8000
echo http://%IP%:8000
pause 