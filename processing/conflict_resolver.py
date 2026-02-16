"""Разрешение конфликтов по иерархии источников (раздел 6 роли)."""

from gemini.schema import ExtractedValue

# Иерархия: чем ниже индекс, тем выше приоритет
SOURCE_PRIORITY = {
    "Паспорт": 0,
    "Каталог": 1,
    "Руководство": 2,
    "Чертёж": 3,
    "Документ": 4,
}


def resolve_conflict(values: list[ExtractedValue]) -> ExtractedValue:
    """Выбрать значение с наивысшим приоритетом источника.

    При одинаковом приоритете — выбрать с наивысшей уверенностью.
    """
    if not values:
        raise ValueError("Пустой список значений")

    if len(values) == 1:
        return values[0]

    confidence_order = {"high": 0, "medium": 1, "low": 2}

    def sort_key(v: ExtractedValue) -> tuple:
        priority = SOURCE_PRIORITY.get(v.source.doc_type, 99)
        confidence = confidence_order.get(v.source.confidence, 99)
        # Штраф для low-confidence: Паспорт low (0+2=2) проигрывает
        # Каталогу high (1+0=1), но бьёт Чертёж high (3+0=3)
        if v.source.confidence == "low":
            priority += 2
        return (priority, confidence)

    sorted_values = sorted(values, key=sort_key)
    return sorted_values[0]
