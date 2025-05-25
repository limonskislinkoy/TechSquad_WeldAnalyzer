from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from typing import List
import os
import shutil
import uuid
import cv2
import numpy as np  # Добавлен импорт numpy
import json
import logging
import time
import traceback
from datetime import datetime
from inference_segformer import segment_large_image
from report_formater import create_report
from positions_finder import find_positions, match_intervals
from polygon_extractor import extract_polygons
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Настройка логирования
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Настройка форматирования логов
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logger = logging.getLogger("image_processor_api")

app = FastAPI()
origins = [
#    "http://localhost:8000",
#   "http://127.0.0.1:8000",  # Optional, in case you're accessing via 127.0.0.1
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Frontend origin(s)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)
BASE_DIR = "data"

# Убедимся, что базовая директория существует
os.makedirs(BASE_DIR, exist_ok=True)
app.mount("/data", StaticFiles(directory="data"), name="data")


def get_user_data_path(user_id: str, image_name: str, reset: bool = True) -> str:
    logger.debug(
        f"Создание директории для пользователя {user_id}, изображение {image_name}, reset={reset}"
    )
    if user_id == "0":
        path = os.path.join(BASE_DIR, "general_user", image_name)
    else:
        path = os.path.join(BASE_DIR, user_id, image_name)
    if os.path.exists(path) and reset:
        logger.info(f"Удаление существующего каталога: {path}")
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)
    logger.debug(f"Создан путь: {path}")
    return path


@app.post("/upload")
async def upload_image(user_id: str = Form(...), file: UploadFile = File(...)):
    start_time = time.time()
    logger.info(
        f"Запрос на загрузку файла от пользователя {user_id}, файл: {file.filename}"
    )

    try:
        logger.debug("Чтение содержимого файла")
        image_bytes = await file.read()
        logger.debug(f"Прочитано {len(image_bytes)} байт")

        logger.debug("Декодирование изображения")
        image_np = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)

        if image_np is None:
            logger.error("Не удалось декодировать изображение")
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Не удалось декодировать изображение",
                },
            )

        logger.info(f"Изображение успешно декодировано, размер: {image_np.shape}")

        # Получаем имя файла безопасным способом
        original_filename = file.filename or "unnamed"
        image_name = os.path.splitext(original_filename)[0]
        logger.debug(f"Используется имя изображения: {image_name}")

        save_dir = get_user_data_path(user_id, image_name)
        input_path = os.path.join(save_dir, "input.png")
        mask_path = os.path.join(save_dir, "mask.png")
        polygon_path = os.path.join(save_dir, "polygons.json")

        # Сохраняем оригинальное изображение
        logger.debug(f"Сохранение оригинального изображения в {input_path}")
        cv2.imwrite(input_path, image_np)

        # Запускаем сегментацию и извлечение полигонов
        logger.info("Запуск сегментации изображения")
        try:
            mask = segment_large_image(input_path)
            logger.debug(
                f"Сегментация завершена, размер маски: {mask.shape if mask is not None else 'None'}"
            )
        except Exception as seg_error:
            logger.error(f"Ошибка в процессе сегментации: {str(seg_error)}")
            logger.error(traceback.format_exc())
            raise

        if mask is None:
            logger.error("Результат сегментации - None")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Ошибка сегментации изображения",
                },
            )

        logger.info("Извлечение полигонов из маски")
        try:
            polygons = extract_polygons(mask)
            logger.debug(f"Извлечено полигонов: {len(polygons) if polygons else 0}")
        except Exception as poly_error:
            logger.error(f"Ошибка при извлечении полигонов: {str(poly_error)}")
            logger.error(traceback.format_exc())
            raise

        logger.debug(f"Сохранение маски в {mask_path}")
        cv2.imwrite(mask_path, mask)

        logger.debug(f"Сохранение полигонов в {polygon_path}")
        with open(polygon_path, "w") as f:
            json.dump(polygons, f)

        elapsed_time = time.time() - start_time
        logger.info(f"Обработка изображения завершена за {elapsed_time:.2f} секунд")
        return {"status": "ok", "polygons": polygons}

    except Exception as e:
        logger.error(f"Необработанное исключение в upload_image: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Произошла ошибка: {str(e)}"},
        )


@app.post("/confirm")
async def confirm_polygons(
    user_id: str = Form(...),
    image_name: str = Form(...),
    polygons_json: str = Form(...),
):
    logger.info(
        f"Запрос на подтверждение полигонов от пользователя {user_id}, изображение {image_name}"
    )

    try:
        save_dir = get_user_data_path(user_id, image_name, reset=False)
        polygon_path = os.path.join(save_dir, "polygons.json")

        # Проверяем валидность JSON перед сохранением
        try:
            logger.debug("Парсинг JSON полигонов")
            polygons_data = json.loads(polygons_json)
            logger.debug(
                f"JSON успешно разобран, содержит {len(polygons_data) if isinstance(polygons_data, list) else 'неизвестное количество'} элементов"
            )
        except json.JSONDecodeError as json_err:
            logger.error(f"Ошибка декодирования JSON: {str(json_err)}")
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Некорректный формат JSON для полигонов",
                },
            )

        logger.debug(f"Сохранение полигонов в {polygon_path}")
        with open(polygon_path, "w") as f:
            json.dump(polygons_data, f)

        logger.info("Полигоны успешно подтверждены и сохранены")
        return {"status": "confirmed"}

    except Exception as e:
        logger.error(f"Ошибка при подтверждении полигонов: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Произошла ошибка: {str(e)}"},
        )


@app.post("/generate-report")
async def generate_report(user_id: str = Form(...), image_name: str = Form(...)):
    start_time = time.time()
    logger.info(
        f"Запрос на генерацию отчета от пользователя {user_id}, изображение {image_name}"
    )

    try:
        save_dir = get_user_data_path(user_id, image_name, reset=False)
        input_path = os.path.join(save_dir, "input.png")
        polygon_path = os.path.join(save_dir, "polygons.json")

        # Проверяем существование необходимых файлов
        if not os.path.exists(input_path):
            logger.error(f"Исходное изображение не найдено: {input_path}")
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": "Исходное изображение не найдено",
                },
            )

        if not os.path.exists(polygon_path):
            logger.error(f"Данные о полигонах не найдены: {polygon_path}")
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "Данные о полигонах не найдены"},
            )

        logger.debug(f"Загрузка полигонов из {polygon_path}")
        try:
            with open(polygon_path) as f:
                polygons = json.load(f)
            logger.debug(
                f"Загружено {len(polygons) if isinstance(polygons, list) else 'неизвестное количество'} полигонов"
            )
        except json.JSONDecodeError as json_err:
            logger.error(f"Ошибка при чтении файла полигонов: {str(json_err)}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Некорректный формат файла полигонов",
                },
            )

        # Находим позиции линейки
        logger.info("Поиск позиций линейки")
        try:
            start_pos, end_pos = find_positions(input_path)
            logger.debug(f"Найдены позиции: начало={start_pos}, конец={end_pos}")
        except Exception as pos_error:
            logger.error(f"Ошибка при поиске позиций: {str(pos_error)}")
            logger.error(traceback.format_exc())
            raise

        # Сопоставляем интервалы
        logger.info("Сопоставление интервалов")
        try:
            intervals = match_intervals(start_pos, end_pos, polygons)
            logger.debug(f"Получено {len(intervals) if intervals else 0} интервалов")
        except Exception as int_error:
            logger.error(f"Ошибка при сопоставлении интервалов: {str(int_error)}")
            logger.error(traceback.format_exc())
            raise

        # Создаем отчет
        logger.info("Создание отчета")
        try:
            report_path = create_report(
                image_name, user_id, polygons, intervals, save_dir
            )
            logger.debug(f"Отчет создан по пути: {report_path}")
        except Exception as rep_error:
            logger.error(f"Ошибка при создании отчета: {str(rep_error)}")
            logger.error(traceback.format_exc())
            raise

        final_path = os.path.join(save_dir, "report.docx")
        logger.debug(f"Копирование отчета в {final_path}")
        shutil.copy(report_path, final_path)

        if not os.path.exists(final_path):
            logger.error(f"Файл отчета не существует после копирования: {final_path}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Не удалось создать файл отчета",
                },
            )

        elapsed_time = time.time() - start_time
        logger.info(
            f"Генерация отчета завершена за {elapsed_time:.2f} секунд, возвращается файл: {final_path}"
        )
        return FileResponse(
            final_path,
            filename="report.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    except Exception as e:
        logger.error(f"Необработанное исключение в generate_report: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Произошла ошибка при генерации отчета: {str(e)}",
            },
        )


# Добавляем тестовый эндпоинт для проверки работоспособности
@app.get("/health")
async def health_check():
    logger.info("Запрос проверки здоровья сервиса")
    return {"status": "ok", "message": "Сервис работает"}


# Обработчик для стартовой страницы
@app.get("/")
async def root():
    logger.info("Запрос к корневому эндпоинту")
    return {
        "message": "API для обработки изображений и генерации отчетов",
        "version": "1.0",
    }


# Обработчик событий запуска приложения
@app.on_event("startup")
async def startup_event():
    logger.info("=============================================")
    logger.info("     Запуск сервиса обработки изображений    ")
    logger.info("=============================================")
    # Убедимся, что базовая директория существует
    os.makedirs(BASE_DIR, exist_ok=True)
    logger.info(f"Базовая директория данных: {os.path.abspath(BASE_DIR)}")
    logger.info(f"Директория логов: {os.path.abspath(LOG_DIR)}")
    logger.info("Сервис успешно запущен и готов к обработке запросов")


# Обработчик событий завершения работы приложения
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Завершение работы сервиса")


# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()

    # Логирование запроса
    logger.info(f"Входящий запрос: {request.method} {request.url.path}")

    # Обработка запроса
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        # Логирование ответа
        logger.info(
            f"Ответ: {response.status_code} - обработан за {process_time:.4f} сек"
        )
        return response
    except Exception as e:
        logger.error(f"Необработанное исключение в middleware: {str(e)}")
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    import uvicorn

    logger.info("Запуск сервера uvicorn")
    uvicorn.run(app, host="0.0.0.0", port=8001, timeout_keep_alive=65)
