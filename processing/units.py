"""Конверсия и нормализация единиц измерения."""

import re


def normalize_pressure(value: str) -> str:
    """Нормализовать давление: МПа, в скобках бар."""
    bar_match = re.search(r'(\d+[.,]?\d*)\s*бар', value, re.IGNORECASE)
    bar_match_en = re.search(r'(\d+[.,]?\d*)\s*bar', value, re.IGNORECASE)

    if bar_match or bar_match_en:
        match = bar_match or bar_match_en
        bar_val = float(match.group(1).replace(",", "."))
        mpa_val = bar_val / 10
        mpa_str = f"{mpa_val:.1f}".replace(".", ",")
        bar_str = f"{bar_val:.0f}".replace(".", ",")
        return f"{mpa_str} МПа ({bar_str} бар)"

    return value


def format_number(value: float, decimals: int = 0) -> str:
    """Отформатировать число: запятая, пробел тысяч."""
    if decimals > 0:
        formatted = f"{value:,.{decimals}f}"
    else:
        formatted = f"{value:,.0f}"

    # Заменить запятые-разделители тысяч на пробелы, точку на запятую
    formatted = formatted.replace(",", " ")
    formatted = formatted.replace(".", ",")
    return formatted


def format_dimensions(value: str) -> str:
    """Нормализовать формат размеров: Д × Ш × В через ' × '."""
    # Заменить различные разделители на стандартный " × "
    result = re.sub(r'\s*[xXхХ×]\s*', ' × ', value)
    return result
