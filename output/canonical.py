"""Каноническая лексика (раздел 2.2 роли)."""


def source_display(file: str, doc_type: str, page: int | None,
                   section: str, quote: str, confidence: str) -> str:
    """Сформировать каноническую строку источника.

    Формат: имя_файла (тип), стр. N, разд. «раздел»: «цитата»
    """
    parts = []

    if file:
        if doc_type:
            parts.append(f"{file} ({doc_type})")
        else:
            parts.append(file)

    if page is not None:
        parts.append(f"стр. {page}")

    if section:
        parts.append(f"разд. \u00ab{section}\u00bb")

    if quote:
        parts.append(f"\u00ab{quote}\u00bb")

    result = ", ".join(parts)

    if confidence == "low":
        result = f"\u26a0 [{result}]"

    return result if result else "\u2014"


def status_display(status: str, note: str = "") -> str:
    """Сформировать каноническую строку статуса."""
    if not status:
        return ""

    canonical = {
        "нет данных": "нет данных",
        "не требуется": "не требуется",
        "справочно": "[справочно]",
        "конфликт": "\u26a0 [КОНФЛИКТ]",
        "неоднозначно": "\u26a0 [НЕОДНОЗНАЧНО]",
    }

    result = canonical.get(status.lower().strip(), status)

    if note:
        result = f"{result} \u2014 {note}"

    return result


def missing_param_note(label: str) -> str:
    """Каноническая фраза для отсутствующего параметра."""
    return f"{label} \u2014 в документации не указан. Запросить у вендора."


def conflict_note(label: str, values: str) -> str:
    """Каноническая фраза для конфликта."""
    return f"{label} \u2014 расхождение: {values}"


def reference_note(label: str, basis: str) -> str:
    """Каноническая фраза для справочного значения."""
    return f"{label} \u2014 принят справочно ({basis})."


def low_quality_note(label: str) -> str:
    """Каноническая фраза для значения с плохого скана."""
    return f"{label} \u2014 считан с чертежа низкого разрешения, требует проверки."
