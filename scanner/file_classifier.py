"""Классификация файлов по типу документа (паспорт, руководство, чертёж и т.д.)."""

import re
from pathlib import Path


DOC_TYPE_PATTERNS = {
    "Паспорт": [
        r"passport", r"паспорт", r"datasheet", r"data\s*sheet",
        r"спецификация", r"specification", r"spec\b",
    ],
    "Руководство": [
        r"manual", r"руководство", r"инструкция", r"instruction",
        r"guide", r"handbook", r"эксплуатаци",
    ],
    "Чертёж": [
        r"drawing", r"чертёж", r"чертеж", r"dwg", r"layout",
        r"план", r"схема", r"diagram",
    ],
    "Каталог": [
        r"catalog", r"каталог", r"brochure", r"брошюра",
    ],
}

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "tiff", "tif"}


def classify_file(path: Path) -> str:
    """Определить тип документа по имени файла и расширению.

    Returns:
        Тип документа: Паспорт, Руководство, Чертёж, Каталог или Документ.
    """
    ext = path.suffix.lower().lstrip(".")

    if ext in IMAGE_EXTENSIONS:
        name_lower = path.stem.lower()
        for doc_type, patterns in DOC_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, name_lower, re.IGNORECASE):
                    return doc_type
        return "Чертёж"

    name_lower = path.stem.lower()
    for doc_type, patterns in DOC_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, name_lower, re.IGNORECASE):
                return doc_type

    return "Документ"
