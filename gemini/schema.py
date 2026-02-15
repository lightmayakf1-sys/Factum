"""Pydantic-модели для structured output Gemini API (чек-лист A.1–H.4)."""

from pydantic import BaseModel, Field, model_validator


class SourceRef(BaseModel):
    """Ссылка на источник значения."""
    file: str = Field(default="", description="Имя исходного файла")
    doc_type: str = Field(default="", description="Тип документа: Паспорт, Руководство, Чертёж, Каталог, Документ")
    page: int | None = Field(default=None, description="Номер страницы (1-based)")
    section: str = Field(default="", description="Название раздела/заголовка в документе")
    quote: str = Field(default="", description="Цитата из оригинала (до 50 символов)")
    confidence: str = Field(default="high", description="Уровень уверенности: high, medium, low")

    @model_validator(mode="before")
    @classmethod
    def _nulls_to_defaults(cls, data):
        """Gemini может вернуть null для строковых полей — заменяем на ''."""
        if isinstance(data, dict):
            for key in ("file", "doc_type", "section", "quote", "confidence"):
                if key in data and data[key] is None:
                    data[key] = ""
        return data


class ConflictEntry(BaseModel):
    """Одна из конфликтующих позиций."""
    value: str = Field(description="Значение")
    source: SourceRef = Field(description="Ссылка на источник")
    is_selected: bool = Field(default=False, description="Выбран как финальный (по приоритету)")


class ExtractedValue(BaseModel):
    """Извлечённое значение параметра."""
    value: str = Field(description="Значение параметра (с единицами измерения)")
    source: SourceRef = Field(description="Ссылка на источник")
    status: str = Field(
        default="",
        description="Статус: пусто=ОК, 'нет данных', 'не требуется', 'справочно', 'конфликт', 'неоднозначно'"
    )
    note: str = Field(default="", description="Примечание (для конфликтов, справочных значений и т.д.)")
    conflict_values: list[ConflictEntry] = Field(default_factory=list, description="Конфликтующие значения (если status=конфликт)")

    @model_validator(mode="before")
    @classmethod
    def _nulls_to_defaults(cls, data):
        """Gemini может вернуть null для строковых полей — заменяем на ''."""
        if isinstance(data, dict):
            for key in ("value", "status", "note"):
                if key in data and data[key] is None:
                    data[key] = ""
        return data


class ChunkExtraction(BaseModel):
    """Результат извлечения параметров из одного чанка."""

    # A. Идентификация
    a1_name: ExtractedValue | None = Field(default=None, description="A.1. Наименование и назначение")
    a2_model: ExtractedValue | None = Field(default=None, description="A.2. Модель / полный артикул")
    a3_manufacturer: ExtractedValue | None = Field(default=None, description="A.3. Производитель, страна")
    a4_year_serial: ExtractedValue | None = Field(default=None, description="A.4. Год выпуска и серийный номер")

    # B. Габариты и логистика заноса
    b1_dimensions: ExtractedValue | None = Field(default=None, description="B.1. Габариты (Д×Ш×В, мм)")
    b2_opening: ExtractedValue | None = Field(default=None, description="B.2. Минимальный монтажный проём")
    b3_weight: ExtractedValue | None = Field(default=None, description="B.3. Масса нетто / с жидкостями")
    b4_heaviest_part: ExtractedValue | None = Field(default=None, description="B.4. Масса тяжелейшей части")
    b5_rigging: ExtractedValue | None = Field(default=None, description="B.5. Точки строповки и ЦТ")

    # C. Строительные требования
    c1_installation: ExtractedValue | None = Field(default=None, description="C.1. Тип установки")
    c2_foundation: ExtractedValue | None = Field(default=None, description="C.2. Размеры фундамента")
    c3_pits: ExtractedValue | None = Field(default=None, description="C.3. Приямки / подиум")
    c4_loads: ExtractedValue | None = Field(default=None, description="C.4. Статические/динамические нагрузки")
    c5_service_zone: ExtractedValue | None = Field(default=None, description="C.5. Зона обслуживания")
    c6_floor: ExtractedValue | None = Field(default=None, description="C.6. Требования к полу")
    c7_construction: ExtractedValue | None = Field(default=None, description="C.7. Требования к конструкциям")

    # D. Электроснабжение и тепло
    d1_power: ExtractedValue | None = Field(default=None, description="D.1. P_уст и P_потр (кВт)")
    d2_voltage: ExtractedValue | None = Field(default=None, description="D.2. Напряжение, фазность, частота, ток")
    d3_reliability: ExtractedValue | None = Field(default=None, description="D.3. Категория надёжности, ИБП")
    d4_startup: ExtractedValue | None = Field(default=None, description="D.4. Тип пуска, cos φ, Ки")
    d5_heat: ExtractedValue | None = Field(default=None, description="D.5. Тепловыделения (кВт)")
    d6_protection: ExtractedValue | None = Field(default=None, description="D.6. Степень защиты (IP), класс зоны")
    d7_grounding: ExtractedValue | None = Field(default=None, description="D.7. Тип заземления")
    d8_cable_entry: ExtractedValue | None = Field(default=None, description="D.8. Точка ввода кабеля")

    # E. Сжатый воздух и газы
    e1_pressure: ExtractedValue | None = Field(default=None, description="E.1. Давление на входе (МПа)")
    e2_flow: ExtractedValue | None = Field(default=None, description="E.2. Расход (м³/ч или н.л/мин)")
    e3_quality: ExtractedValue | None = Field(default=None, description="E.3. Качество среды")
    e4_connection: ExtractedValue | None = Field(default=None, description="E.4. Точка подключения")

    # F. Водоснабжение и канализация
    f1_purpose: ExtractedValue | None = Field(default=None, description="F.1. Назначение воды")
    f2_quality: ExtractedValue | None = Field(default=None, description="F.2. Требования к качеству воды")
    f3_flow: ExtractedValue | None = Field(default=None, description="F.3. Расход, давление, температура воды")
    f4_connection: ExtractedValue | None = Field(default=None, description="F.4. Точка подключения воды")