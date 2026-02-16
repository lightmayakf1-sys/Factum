"""Валидация полноты извлечённых данных (все A.1–H.4 присутствуют)."""

from gemini.schema import ExtractedValue, CHECKLIST_FIELDS


def validate_completeness(
    resolved: dict[str, ExtractedValue | None],
) -> tuple[list[str], list[str], list[str]]:
    """Проверить полноту данных по чек-листу.

    Returns:
        (present, missing, warnings): списки полей
    """
    present = []
    missing = []
    warnings = []

    for field_name, label in CHECKLIST_FIELDS:
        value = resolved.get(field_name)

        if value is None:
            missing.append(label)
        elif value.status in ("нет данных", "не требуется"):
            present.append(label)
        elif value.source.confidence == "low":
            warnings.append(f"{label} — считан с низкой уверенностью")
            present.append(label)
        elif value.note and "OCR" in value.note.upper():
            warnings.append(f"{label} — возможная ошибка OCR, требует проверки")
            present.append(label)
        elif value.status and "конфликт" in value.status.lower():
            warnings.append(f"{label} — расхождение между источниками")
            present.append(label)
        else:
            present.append(label)

    return present, missing, warnings
