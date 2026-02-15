"""Конфигурация приложения Normocontrol."""

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".normocontrol"
CONFIG_FILE = CONFIG_DIR / "config.json"

SUPPORTED_EXTENSIONS = {
    "pdf": "PDF",
    "jpg": "Изображение",
    "jpeg": "Изображение",
    "png": "Изображение",
    "bmp": "Изображение",
    "tiff": "Изображение",
    "tif": "Изображение",
    "docx": "DOCX",
    "doc": "DOC",
    "xlsx": "Excel",
    "xls": "Excel",
    "csv": "CSV",
    "txt": "Текст",
}

FIXED_MODEL = "gemini-2.5-pro"

DEFAULT_CONFIG = {
    "api_key": "",
    "model": FIXED_MODEL,
    "chunk_size": 10,
    "overlap": 2,
    "output_dir": "",
}


def load_config() -> dict:
    """Загрузить конфигурацию из файла."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            stored = json.load(f)
        config = {**DEFAULT_CONFIG, **stored}
        return config
    return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    """Сохранить конфигурацию в файл."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
