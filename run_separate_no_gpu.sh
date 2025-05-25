#!/bin/bash

get_ip_addresses() {
    ip -4 addr show | grep -w inet | awk '{print $2}' | cut -d/ -f1
}

echo "Получение списка IP-адресов..."
echo
echo "Доступные IP-адреса:"
echo "------------------"

mapfile -t ip_addresses < <(get_ip_addresses)

for i in "${!ip_addresses[@]}"; do
    echo "$((i+1)). ${ip_addresses[$i]}"
done

echo "------------------"

validate_input() {
    local input=$1
    if [[ ! $input =~ ^[0-9]+$ ]] || [ "$input" -lt 1 ] || [ "$input" -gt ${#ip_addresses[@]} ]; then
        return 1
    fi
    return 0
}

while true; do
    read -p "Выберите номер IP-адреса (1-${#ip_addresses[@]}): " choice
    
    if validate_input "$choice"; then
        selected_ip=${ip_addresses[$((choice-1))]}
        break
    else
        echo "Неверный выбор. Пожалуйста, выберите номер из списка."
    fi
done

echo
echo "Выбран IP-адрес: $selected_ip"
echo

cd ./server/

echo "Сборка Docker-образа бэкенда..."
docker build -t backend:latest . --quiet

echo "Запуск контейнера..."
docker run -d --name backend_no_gpu -p 8002:8000 backend:latest

echo "Готово! Бэкенд запущен на порту 8002"

cd ../web/
echo "Сборка Docker-образов веб-интерфейса..."
docker build -t frontend:latest . --quiet

echo "Запуск контейнера..."
docker run -d --name frontend   -e BACKEND_URL="http://$selected_ip:8002" -p 8001:8001 -p 7999:8000  frontend:latest

echo "Готово! Веб-интерфейс запущен на порту 7999"
echo "Для доступа к веб-интерфейсу перейдите по одной из ссылок:"
echo "http://localhost:7999"
echo "http://$selected_ip:7999"
read -p "Нажмите Enter для выхода..." 