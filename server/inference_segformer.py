import torch
import numpy as np
import cv2
from PIL import Image
from transformers import SegformerFeatureExtractor, SegformerForSemanticSegmentation
import os
from typing import Tuple

# ---------------------------
# 🔧 Конфигурация
# ---------------------------
BASE_MODEL = "nvidia/segformer-b4-finetuned-ade-512-512"  # базовая архитектура
WEIGHTS_PATH = "segformer_output/segformer_best_checkpoint.pth"  # путь к .pth файлу
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

NUM_CLASSES = 14  # ⚠️ Замените на нужное вам число классов
TILE_SIZE = 512
OVERLAP_X = 100
OFFSET_Y_TOP = 200
OFFSET_Y_BOTTOM = 440
CLAHE_CLIP = 3.0
CLAHE_GRID = (8, 8)

SHARPEN_KERNEL = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])

# ---------------------------
# 🧠 Инициализация модели
# ---------------------------
print("Инициализация модели...")
feature_extractor = SegformerFeatureExtractor.from_pretrained(BASE_MODEL)

# ⚠️ id2label и label2id можно подставить из вашей задачи
id2label = {i: f"class_{i}" for i in range(NUM_CLASSES)}
label2id = {v: k for k, v in id2label.items()}

model = SegformerForSemanticSegmentation.from_pretrained(
    BASE_MODEL,
    num_labels=NUM_CLASSES,
    id2label=id2label,
    label2id=label2id,
    ignore_mismatched_sizes=True,
)

print(f"Загрузка весов из {WEIGHTS_PATH}...")
checkpoint = torch.load(WEIGHTS_PATH, map_location=DEVICE, weights_only=False)
model.load_state_dict(checkpoint["model_state_dict"])
model.to(DEVICE)
model.eval()


# ---------------------------
# 🖼️ Подготовка изображения
# ---------------------------
def prepare_input_image(pil_img: Image.Image) -> Image.Image:
    gray = np.array(pil_img.convert("L"))
    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=CLAHE_GRID)
    clahe_gray = clahe.apply(gray)
    sharpened_gray = cv2.filter2D(gray, -1, SHARPEN_KERNEL)
    merged = cv2.merge([gray, clahe_gray, sharpened_gray])
    return Image.fromarray(merged)


# ---------------------------
# 🔪 Нарезка тайлов
# ---------------------------
def generate_tiles(img: Image.Image) -> Tuple[list, list]:
    width, height = img.size
    tiles, positions = [], []
    for y0 in [OFFSET_Y_TOP, OFFSET_Y_BOTTOM]:
        y1 = y0 + TILE_SIZE
        if y1 > height:
            continue
        x = 0
        while x + TILE_SIZE <= width:
            box = (x, y0, x + TILE_SIZE, y1)
            tile = img.crop(box)
            tiles.append(tile)
            positions.append((x, y0))
            x += TILE_SIZE - OVERLAP_X
    return tiles, positions


# ---------------------------
# 🤖 Предсказание одного тайла
# ---------------------------
def predict_tile(tile: Image.Image) -> np.ndarray:
    tile_rgb = prepare_input_image(tile)
    encoding = feature_extractor(images=tile_rgb, return_tensors="pt")
    pixel_values = encoding["pixel_values"].to(DEVICE)

    with torch.no_grad():
        outputs = model(pixel_values)
        logits = outputs.logits
        logits = torch.nn.functional.interpolate(
            logits, size=(TILE_SIZE, TILE_SIZE), mode="bilinear", align_corners=False
        )
        pred_mask = torch.argmax(logits, dim=1).squeeze().cpu().numpy()

    return pred_mask


# ---------------------------
# 🧩 Сборка финальной маски
# ---------------------------
def reconstruct_mask(tiles_preds, positions, img_size):
    full_mask = np.zeros(img_size[::-1], dtype=np.int32)
    count_mask = np.zeros_like(full_mask, dtype=np.int32)

    for tile, (x, y) in zip(tiles_preds, positions):
        full_mask[y : y + TILE_SIZE, x : x + TILE_SIZE] += tile
        count_mask[y : y + TILE_SIZE, x : x + TILE_SIZE] += 1

    count_mask[count_mask == 0] = 1
    averaged_mask = full_mask / count_mask
    return averaged_mask.astype(np.uint8)


# ---------------------------
# 🚀 Главная функция
# ---------------------------
def segment_large_image(image_path: str) -> np.ndarray:
    original_image = Image.open(image_path).convert("RGB")
    tiles, positions = generate_tiles(original_image)

    print(f"Processing {len(tiles)} tiles...")

    predictions = [predict_tile(tile) for tile in tiles]
    final_mask = reconstruct_mask(predictions, positions, original_image.size)
    return final_mask


# ---------------------------
# 📦 Точка входа
# ---------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python segment_script.py path_to_image.jpg")
    else:
        input_path = sys.argv[1]
        result_mask = segment_large_image(input_path)
        output_path = os.path.splitext(input_path)[0] + "_mask.png"
        cv2.imwrite(output_path, result_mask)
        print(f"Saved segmentation mask to {output_path}")
