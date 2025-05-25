import numpy as np
import cv2


def extract_polygons(mask: np.ndarray) -> list:
    """
    Извлекает полигоны из маски сегментации.

    Args:
        mask (np.ndarray): Маска сегментации (H x W), с integer-метками классов.
        min_area (int): Минимальная площадь для фильтрации шумов.

    Returns:
        List[Dict]: [{'class': int, 'polygon': [x1, y1, ..., xn, yn]}, ...] с нормализованными координатами
    """
    height, width = mask.shape
    results = []

    classes = np.unique(mask)
    classes = classes[classes != 0]  # пропускаем фон

    for cls in classes:
        binary = np.uint8(mask == cls) * 255

        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        for cnt in contours:

            polygon = cnt.squeeze().astype(float)

            if polygon.ndim != 2 or polygon.shape[0] < 3:
                continue  # игнорируем "плохие" контуры

            # нормализация координат
            norm_polygon = []
            for x, y in polygon:
                norm_x = x / width
                norm_y = y / height
                norm_polygon.extend([round(norm_x, 6), round(norm_y, 6)])

            results.append({"class": int(cls), "polygon": norm_polygon})

    return results
