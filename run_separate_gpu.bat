@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo Получение списка IP-адресов...
echo.
echo Доступные IP-адреса:
echo ------------------

set "tempfile=%TEMP%\ip_list.txt"
ipconfig | findstr /R /C:"IPv4" > "%tempfile%"

set /a counter=1

for /f "tokens=2 delims=:" %%a in ('type "%tempfile%"') do (
    set "IP[!counter!]=%%a"
    echo !counter!. %%a
    set /a counter+=1
)

del "%tempfile%" 2>nul

echo ------------------

:choice
set /p choice="Выберите номер IP-адреса (1-%counter%): "
if %choice% LSS 1 goto invalid
if %choice% GTR %counter% goto invalid
set IP=!IP[%choice%]!
set IP=%IP:~1%
goto continue

:invalid
echo Неверный выбор. Пожалуйста, выберите номер из списка.
goto choice

:continue
echo.
echo Выбран IP-адрес: %IP%
echo.
cd ./server/
echo Сборка Docker-образа бэкенда...
docker build -t backend:latest . --quiet

echo Запуск контейнера...
docker run -d --gpus=all --name backend -p 8002:8000 backend:latest 
cd ../web/
echo Сборка Docker-образа веб-интерфейса...
docker build -t frontend:latest . --quiet

echo Запуск контейнера...
docker run -d --name frontend -p 8001:8001 -p 7999:8000 -e BACKEND_URL="http://%IP%:8002" frontend:latest 
echo.
echo Готово! Контейнер запущен на порту 7999
echo Для доступа к веб-интерфейсу перейдите по одной из ссылок:
echo http://localhost:7999
pause 