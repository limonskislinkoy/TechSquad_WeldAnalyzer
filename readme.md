# Tech.Squad -| Wallcreepers |- AI Анализатор снимнов сварных швов

Веб-приложение для обработки изображений с использованием искусственного интеллекта. Поддерживает запуск как в едином контейнере, так и с разделением на фронтенд и бэкенд для масштабирования.

## 📥 Получение проекта

Сначала клонируйте репозиторий:

```bash
git clone https://github.com/limonskislinkoy/TechSquad_WeldAnalyzer
cd TechSquad_WeldAnalyzer
```

## 🚀 Быстрый старт

После сборки образа и запуска контейнера веб-интерфейс будет доступен по адресу `http://localhost:8000`. 

⚠️ **Важно**: После запуска необходимо подождать инициализации модуля ИИ. В это время обработка изображений будет недоступна.

## 📋 Требования

- Docker
- NVIDIA Docker (для GPU-версии)

## 🐳 Варианты запуска

### 1. Единый контейнер (рекомендуется для локального использования)

#### Windows

**С поддержкой GPU** (готовый скрипт `run_combo_gpu.bat`):
```bash
run_combo_gpu.bat
```

**Без GPU** (готовый скрипт `run_combo_no_gpu.bat`):
```bash
run_combo_no_gpu.bat
```

#### Linux

**С поддержкой GPU** (готовый скрипт `run_combo_gpu.sh`):
```bash
chmod +x run_combo_gpu.sh
./run_combo_gpu.sh
```

**Без GPU** (готовый скрипт `run_combo_no_gpu.sh`):
```bash
chmod +x run_combo_no_gpu.sh
./run_combo_no_gpu.sh
```

### 2. Раздельные контейнеры (для распределенного развертывания)

Этот вариант позволяет запустить тяжелый бэкенд на мощном сервере, а фронтенд - на отдельной машине.
При выборе IP-адреса следует выбирать адрес, по которому ПК доступен в локальной сети.

#### Windows

**С поддержкой GPU** (готовый скрипт `run_separate_gpu.bat`):
```bash
run_separate_gpu.bat
```

**Без GPU** (готовый скрипт `run_separate_no_gpu.bat`):
```bash
run_separate_no_gpu.bat
```

#### Linux

**С поддержкой GPU** (готовый скрипт `run_separate_gpu.sh`):
```bash
chmod +x run_separate_gpu.sh
./run_separate_gpu.sh
```

**Без GPU** (готовый скрипт `run_separate_no_gpu.sh`):
```bash
chmod +x run_separate_no_gpu.sh
./run_separate_no_gpu.sh
```

## 🌐 Доступ к приложению

### Единый контейнер
- Веб-интерфейс: `http://localhost:8000`

### Раздельные контейнеры
- Веб-интерфейс: `http://localhost:7999`
- API бэкенда: `http://localhost:8002`

## 🔧 Конфигурация

### Переменные окружения

При использовании раздельных контейнеров автоматически настраивается:
- `BACKEND_URL` - URL бэкенда для фронтенда

### Порты

#### Единый контейнер:
- `8000` - веб-интерфейс

#### Раздельные контейнеры:
- `7999` - веб-интерфейс фронтенда
- `8001` - внутренний порт фронтенда
- `8002` - API бэкенда

#### Режим разработки:
- `8000` - веб-интерфейс
- `8001` - API бэкенда

## 💻 Системные требования

### Минимальные требования:
- RAM: 4GB
- Свободное место: 2GB
- CPU: 2 ядра

### Рекомендуемые требования с GPU:
- RAM: 8GB+
- VRAM: 4GB+
- NVIDIA GPU с поддержкой CUDA 12.6 и новее
- Свободное место: 5GB

## 🐛 Устранение неполадок

### Проблемы с запуском

1. **Контейнер не запускается:**
   ```bash
   docker logs combo
   # или для раздельных контейнеров
   docker logs backend
   docker logs frontend
   ```

2. **Ошибка "порт уже используется":**
   ```bash
   # Остановка всех контейнеров
   docker stop $(docker ps -q)
   
   # Удаление контейнеров
   docker rm combo backend frontend
   ```

3. **Проблемы с GPU:**
   - Убедитесь, что установлен NVIDIA Docker
   - Проверьте драйверы NVIDIA
   ```bash
   nvidia-docker run --rm nvidia/cuda:11.0-base nvidia-smi
   ```

### Проблемы с обработкой изображений

1. **Обработка не работает после запуска:**
   - Подождите 2-5 минут для инициализации ИИ-модуля
   - Проверьте логи контейнера

2. **Медленная обработка:**
   - Используйте версию с GPU
   - Увеличьте выделенную память Docker

## 🔄 Обновление

1. Остановите контейнеры:
   ```bash
   docker stop combo backend frontend
   docker rm combo backend frontend
   ```

2. Удалите старые образы:
   ```bash
   docker rmi combo:latest backend:latest frontend:latest
   ```

3. Запустите заново нужный скрипт

## 📚 Структура проекта

```
├── server/          # Бэкенд с ИИ-моделью
├── web/            # Фронтенд веб-интерфейса
├── requirements.txt # Зависимости Python
├── run_*.bat       # Скрипты запуска для Windows
└── run_*.sh        # Скрипты запуска для Linux
```

## 🤝 Поддержка

При возникновении проблем:

1. Проверьте логи контейнеров
2. Убедитесь, что все порты свободны
3. Для GPU-версии проверьте корректность установки NVIDIA Docker