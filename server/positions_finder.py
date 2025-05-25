# positions_finder.py

def find_positions(image_path: str):
    """
    MOCK: Возвращает фиксированные координаты начала и конца линейки.
    """
    start_pos = 0
    end_pos = 3000
    return start_pos, end_pos


def match_intervals(start_pos: int, end_pos: int, polygons: list):
    """
    Сопоставляет дефекты интервалам по оси X.

    Интервалы по 300мм: от start_pos до end_pos (или наоборот если start > end)
    Пример: "0-300", "300-600", ..., "2700-3000"

    Возвращает: словарь { "интервал": [индексы дефектов] }
    """
    # Убедимся, что интервалы возрастают
    reverse = start_pos > end_pos
    step = 300
    intervals = []

    if reverse:
        for x in range(start_pos, end_pos - step, -step):
            intervals.append((x, x - step))
    else:
        for x in range(start_pos, end_pos, step):
            intervals.append((x, x + step))

    # Преобразуем интервалы в строки
    interval_strs = [f"{i[0]}-{i[1]}" for i in intervals]
    interval_map = {k: [] for k in interval_strs}

    for idx, item in enumerate(polygons):
        coords = item.get("polygon", [])
        if not coords or len(coords) < 2:
            continue

        x_coords = coords[0::2]  # Только x координаты
        min_x = min(x_coords)
        max_x = max(x_coords)

        # Де-нормализуем координаты
        if reverse:
            min_x = start_pos - (start_pos - end_pos) * min_x
            max_x = start_pos - (start_pos - end_pos) * max_x
        else:
            min_x = start_pos + (end_pos - start_pos) * min_x
            max_x = start_pos + (end_pos - start_pos) * max_x

        for (lo, hi) in intervals:
            in_interval = (
                (min(min_x, max_x) <= hi and max(min_x, max_x) >= lo)
                if not reverse
                else (min(min_x, max_x) <= lo and max(min_x, max_x) >= hi)
            )

            if in_interval:
                key = f"{lo}-{hi}"
                interval_map[key].append(idx)

    return interval_map
