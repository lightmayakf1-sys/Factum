"""Pydantic-модели для structured output GigaChat API (чек-лист A.1–H.4)."""

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
        """Модель может вернуть null для строковых полей — заменяем на ''."""
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
        """Модель может вернуть null для строковых полей — заменяем на ''."""
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
    f5_drainage: ExtractedValue | None = Field(default=None, description="F.5. Канализация")
    f6_drain_point: ExtractedValue | None = Field(default=None, description="F.6. Точка слива")
    f7_coolant: ExtractedValue | None = Field(default=None, description="F.7. СОЖ")
    f8_periodicity: ExtractedValue | None = Field(default=None, description="F.8. Периодичность потребления")

    # G. Вентиляция, экология и шум
    g1_exhaust: ExtractedValue | None = Field(default=None, description="G.1. Локальные отсосы")
    g2_emissions: ExtractedValue | None = Field(default=None, description="G.2. Состав выбросов")
    g3_noise: ExtractedValue | None = Field(default=None, description="G.3. Уровень шума (дБА)")
    g4_vibration: ExtractedValue | None = Field(default=None, description="G.4. Вибрация")

    # H. Автоматизация и безопасность
    h1_it: ExtractedValue | None = Field(default=None, description="H.1. IT-инфраструктура")
    h2_safety: ExtractedValue | None = Field(default=None, description="H.2. Интеграция в систему безопасности")
    h3_signaling: ExtractedValue | None = Field(default=None, description="H.3. Световая/звуковая сигнализация")
    h4_climate: ExtractedValue | None = Field(default=None, description="H.4. Микроклимат в зоне установки")


CHECKLIST_FIELDS = [
    ("a1_name", "A.1. Наименование и назначение"),
    ("a2_model", "A.2. Модель / полный артикул"),
    ("a3_manufacturer", "A.3. Производитель, страна"),
    ("a4_year_serial", "A.4. Год выпуска и серийный номер"),
    ("b1_dimensions", "B.1. Габариты (Д×Ш×В, мм)"),
    ("b2_opening", "B.2. Минимальный монтажный проём"),
    ("b3_weight", "B.3. Масса нетто / с жидкостями"),
    ("b4_heaviest_part", "B.4. Масса тяжелейшей части"),
    ("b5_rigging", "B.5. Точки строповки и ЦТ"),
    ("c1_installation", "C.1. Тип установки"),
    ("c2_foundation", "C.2. Размеры фундамента"),
    ("c3_pits", "C.3. Приямки / подиум"),
    ("c4_loads", "C.4. Статические/динамические нагрузки"),
    ("c5_service_zone", "C.5. Зона обслуживания"),
    ("c6_floor", "C.6. Требования к полу"),
    ("c7_construction", "C.7. Требования к конструкциям"),
    ("d1_power", "D.1. P_уст и P_потр (кВт)"),
    ("d2_voltage", "D.2. Напряжение, фазность, частота, ток"),
    ("d3_reliability", "D.3. Категория надёжности, ИБП"),
    ("d4_startup", "D.4. Тип пуска, cos φ, Ки"),
    ("d5_heat", "D.5. Тепловыделения (кВт)"),
    ("d6_protection", "D.6. Степень защиты (IP), класс зоны"),
    ("d7_grounding", "D.7. Тип заземления"),
    ("d8_cable_entry", "D.8. Точка ввода кабеля"),
    ("e1_pressure", "E.1. Давление на входе (МПа)"),
    ("e2_flow", "E.2. Расход (м³/ч или н.л/мин)"),
    ("e3_quality", "E.3. Качество среды"),
    ("e4_connection", "E.4. Точка подключения"),
    ("f1_purpose", "F.1. Назначение воды"),
    ("f2_quality", "F.2. Требования к качеству воды"),
    ("f3_flow", "F.3. Расход, давление, температура воды"),
    ("f4_connection", "F.4. Точка подключения воды"),
    ("f5_drainage", "F.5. Канализация"),
    ("f6_drain_point", "F.6. Точка слива"),
    ("f7_coolant", "F.7. СОЖ"),
    ("f8_periodicity", "F.8. Периодичность потребления"),
    ("g1_exhaust", "G.1. Локальные отсосы"),
    ("g2_emissions", "G.2. Состав выбросов"),
    ("g3_noise", "G.3. Уровень шума (дБА)"),
    ("g4_vibration", "G.4. Вибрация"),
    ("h1_it", "H.1. IT-инфраструктура"),
    ("h2_safety", "H.2. Интеграция в систему безопасности"),
    ("h3_signaling", "H.3. Световая/звуковая сигнализация"),
    ("h4_climate", "H.4. Микроклимат в зоне установки"),
]


SECTION_GROUPS = {
    "A": ("A. Идентификация", ["a1_name", "a2_model", "a3_manufacturer", "a4_year_serial"]),
    "B": ("B. Габариты и логистика заноса", ["b1_dimensions", "b2_opening", "b3_weight", "b4_heaviest_part", "b5_rigging"]),
    "C": ("C. Строительные требования (АС)", ["c1_installation", "c2_foundation", "c3_pits", "c4_loads", "c5_service_zone", "c6_floor", "c7_construction"]),
    "D": ("D. Электроснабжение и тепло (ЭМ / ОВ)", ["d1_power", "d2_voltage", "d3_reliability", "d4_startup", "d5_heat", "d6_protection", "d7_grounding", "d8_cable_entry"]),
    "E": ("E. Сжатый воздух и газы (ТХ)", ["e1_pressure", "e2_flow", "e3_quality", "e4_connection"]),
    "F": ("F. Водоснабжение и канализация (ВК)", ["f1_purpose", "f2_quality", "f3_flow", "f4_connection", "f5_drainage", "f6_drain_point", "f7_coolant", "f8_periodicity"]),
    "G": ("G. Вентиляция, экология и шум (ОВ)", ["g1_exhaust", "g2_emissions", "g3_noise", "g4_vibration"]),
    "H": ("H. Автоматизация и безопасность (АТХ / СС)", ["h1_it", "h2_safety", "h3_signaling", "h4_climate"]),
}
