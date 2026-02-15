"""Числовое форматирование (раздел 2.4 роли)."""

import re


def format_value(value: str) -> str:
    """Применить правила числового форматирования к значению."""
    # Замена точки на запятую в десятичных числах
    value = re.sub(r'(\d)\.(\d)', r'\1,\2', value)

    # Добавление пробелов-разделителей тысяч
    def add_thousands_sep(match):
        num_str = match.group(0)
        # Не трогать дроби после запятой
        if "," in num_str:
            integer_part, decimal_part = num_str.split(",", 1)
        else:
            integer_part = num_str
            decimal_part = None

        # Добавить пробелы в целую часть
        result = ""
        for i, ch in enumerate(reversed(integer_part)):
            if i > 0 and i % 3 == 0 and ch != " ":
                result = " " + result
            result = ch + result

        if decimal_part is not None:
            result = result + "," + decimal_part

        return result

    # Находим числа >= 1000
    value = re.sub(r'\b\d{4,}(?:,\d+)?\b', add_thousands_sep, value)

    # Нормализация символа умножения в размерах
    value = re.sub(r'\s*[xXхХ]\s*', ' \u00d7 ', value)

    # Нормализация тире в диапазонах (число–число)
    value = re.sub(r'(\d)\s*[-\u2013\u2014]\s*(\d)', '\\1\u2013\\2', value)

    return value
