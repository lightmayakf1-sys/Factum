# ТЕХНИЧЕСКОЕ ЗАДАНИЕ

## Приложение "Factum" — Анализ паспортов промышленного оборудования

**Версия документа:** 2.0
**Дата:** февраль 2026

---

## 1. ОБЩИЕ СВЕДЕНИЯ

### 1.1. Назначение и область применения

**Factum** — настольное GUI-приложение для автоматизированного извлечения технических параметров из документации на промышленное оборудование (паспорта, руководства, чертежи, каталоги, datasheet'ы) и формирования структурированных DOCX-карточек.

**Решаемая проблема:** Ручной нормоконтроль (анализ документации оборудования, заполнение карточек) занимает часы работы инженера. Приложение автоматизирует этот процесс до минут, извлекая 44 технических параметра (чек-лист A.1–H.4) с привязкой к источникам.

**Целевые пользователи:** Инженеры-проектировщики проектных институтов, технические специалисты, занимающиеся подбором и нормоконтролем промышленного оборудования.

**Ключевые возможности:**
- Загрузка документов: PDF, изображения, DOCX, Excel, CSV, TXT (файлы и папки, drag-and-drop)
- Автоматическое разбиение PDF на чанки с перекрытием (overlap) для предотвращения потери данных на границах страниц
- Автоматическое определение контекста оборудования (тип, подсистемы, класс мощности) для повышения точности извлечения
- Извлечение 44 параметров через Google Gemini API с привязкой к страницам и цитатам
- Дедупликация overlap-дублей и разрешение конфликтов между источниками по иерархии приоритетов
- Верификация данных (поиск пропусков, конфликтов, косвенных параметров, логическая непротиворечивость)
- Генерация DOCX-карточки с таблицами, источниками, примечаниями
- Предпросмотр карточки в GUI (HTML) со структурированным отображением конфликтов (✔/✖ цветовое выделение)

### 1.2. Технический стек

| Технология | Версия | Назначение |
|------------|--------|------------|
| Python | 3.14 | Язык разработки |
| PyQt6 | >= 6.6 | GUI-фреймворк |
| google-genai | >= 1.0 | Google Gemini API SDK |
| python-docx | >= 1.0 | Генерация DOCX |
| PyMuPDF (fitz) | >= 1.24 | Разбиение PDF на чанки |
| pydantic | >= 2.0 | Модели данных, валидация JSON |
| pint | >= 0.24 | Единицы измерения (зарезервирован) |
| charset-normalizer | >= 3.0 | Определение кодировки текстовых файлов |

### 1.3. Требования к среде

- **ОС:** Windows 10/11
- **Python 3.14** установлен в `C:\Python314\`
- **Интернет-доступ** для Google Gemini API
- **API-ключ** Google AI Studio (бесплатный или платный)

---

## 2. СТРУКТУРА ПРОЕКТА

### 2.1. Дерево файлов

```
Factum/
├── main.py                      # Точка входа (стандартный запуск)
├── run_console.py               # Запуск через .bat (скрывает консоль)
├── run.pyw                      # Альтернативный запуск (pythonw.exe)
├── config.py                    # Конфигурация (API, фиксированная модель, пути)
├── worker.py                    # QThread-воркер 6-этапного pipeline
├── requirements.txt             # Зависимости Python
├── Factum.bat                   # Запуск двойным кликом
├── install.bat                  # Установка зависимостей (от администратора)
├── factum.ico                   # Иконка приложения
├── .gitignore                   # Правила исключений Git
│
├── installer/                   # Инсталлятор
│   ├── factum.spec              # Конфигурация PyInstaller
│   ├── factum.iss               # Скрипт Inno Setup
│   ├── build.bat                # Скрипт сборки
│   ├── install_deps.bat         # Установка зависимостей сборки
│   ├── generate_icon.py         # Генерация иконки
│   ├── factum_preview.png       # Превью для инсталлятора
│   └── LICENSE.txt              # Лицензия
│
├── scanner/
│   ├── __init__.py              # (пустой)
│   ├── folder_scanner.py        # Сканирование файлов и папок
│   └── file_classifier.py       # Классификация: паспорт/руководство/чертёж
│
├── chunking/
│   ├── __init__.py              # (пустой)
│   ├── chunk_manager.py         # Создание чанков из разных форматов
│   ├── pdf_chunker.py           # Разбиение PDF на чанки (PyMuPDF)
│   └── image_chunker.py         # Placeholder (логика в chunk_manager.py)
│
├── gemini/
│   ├── __init__.py              # (пустой)
│   ├── schema.py                # Pydantic-модели: SourceRef, ExtractedValue, ChunkExtraction
│   ├── prompts.py               # Системные промпты для Gemini API
│   └── client.py                # Обёртка Gemini API: retry, парсинг, fallback
│
├── processing/
│   ├── __init__.py              # (пустой)
│   ├── aggregator.py            # Агрегация, конфликты, верификация
│   ├── conflict_resolver.py     # Разрешение конфликтов по иерархии
│   ├── validator.py             # Проверка полноты A.1–H.4
│   └── units.py                 # Нормализация единиц (давление, числа, размеры)
│
├── output/
│   ├── __init__.py              # (пустой)
│   ├── docx_generator.py        # Генерация DOCX-карточки
│   ├── canonical.py             # Каноническая лексика (отображение источников)
│   └── formatter.py             # Числовое форматирование (СИ, русские правила)
│
└── gui/
    ├── __init__.py              # (пустой)
    ├── main_window.py           # Главное окно (файлы, прогресс, превью)
    ├── settings_dialog.py       # Диалог настроек (API ключ, размер чанка)
    ├── file_list_widget.py      # Placeholder (логика в main_window.py)
    ├── progress_widget.py       # Placeholder (логика в main_window.py)
    └── preview_widget.py        # Placeholder (логика в main_window.py)
```

### 2.2. Граф зависимостей

```
main.py / run_console.py
  └── gui/main_window.py
        ├── config.py
        ├── scanner/folder_scanner.py
        └── worker.py
              ├── config.py
              ├── scanner/folder_scanner.py
              ├── chunking/chunk_manager.py
              │     ├── scanner/folder_scanner.py
              │     ├── scanner/file_classifier.py
              │     └── chunking/pdf_chunker.py
              ├── gemini/client.py
              │     ├── gemini/schema.py
              │     ├── gemini/prompts.py
              │     └── chunking/chunk_manager.py
              ├── processing/aggregator.py
              │     ├── gemini/schema.py
              │     ├── chunking/chunk_manager.py
              │     └── processing/conflict_resolver.py
              ├── processing/validator.py
              │     └── gemini/schema.py
              └── output/docx_generator.py
                    ├── gemini/schema.py
                    ├── output/canonical.py
                    └── output/formatter.py
```

---

## 3. МОДЕЛИ ДАННЫХ

### 3.1. SourceRef — ссылка на источник

```python
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
```

> **КРИТИЧНО:** Двойная защита от None: 1) `default=""` для случая, когда Gemini не возвращает поле; 2) `@model_validator(mode="before")` для случая, когда Gemini возвращает `null` явно (Pydantic `default` не срабатывает, если ключ присутствует со значением None).

### 3.2. ConflictEntry — одна конфликтующая позиция

```python
class ConflictEntry(BaseModel):
    """Одна из конфликтующих позиций."""
    value: str = Field(description="Значение")
    source: SourceRef = Field(description="Ссылка на источник")
    is_selected: bool = Field(default=False, description="Выбран как финальный (по приоритету)")
```

Используется в `ExtractedValue.conflict_values` для структурированного хранения всех вариантов при конфликте. Поле `is_selected=True` помечает вариант, выбранный `resolve_conflict()`.

### 3.3. ExtractedValue — извлечённое значение

```python
class ExtractedValue(BaseModel):
    """Извлечённое значение параметра."""
    value: str = Field(description="Значение параметра (с единицами измерения)")
    source: SourceRef = Field(description="Ссылка на источник")
    status: str = Field(default="", description="Статус")
    note: str = Field(default="", description="Примечание")
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
```

**Допустимые значения `status`:**
- `""` — ОК (по умолчанию)
- `"нет данных"` — параметр отсутствует в документации
- `"не требуется"` — параметр неприменим
- `"справочно"` — справочное значение
- `"конфликт"` — расхождение между источниками
- `"неоднозначно"` — неоднозначное значение
- `"[UPD] верификация"` — добавлено на этапе верификации
- `"[справочно: косвенный вывод]"` — выведено косвенно при верификации

### 3.4. ChunkExtraction — результат извлечения из одного чанка

```python
class ChunkExtraction(BaseModel):
    """Результат извлечения параметров из одного чанка."""

    # A. Идентификация
    a1_name: ExtractedValue | None = Field(default=None, description="A.1. Наименование и назначение")
    a2_model: ExtractedValue | None = Field(default=None, description="A.2. Модель / полный артикул")
    a3_manufacturer: ExtractedValue | None = Field(default=None, description="A.3. Производитель, страна")
    a4_year_serial: ExtractedValue | None = Field(default=None, description="A.4. Год выпуска и серийный номер")

    # B. Габариты и логистика заноса
    b1_dimensions: ExtractedValue | None = Field(default=None, description="B.1. Габариты (Д*Ш*В, мм)")
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
    d4_startup: ExtractedValue | None = Field(default=None, description="D.4. Тип пуска, cos phi, Ки")
    d5_heat: ExtractedValue | None = Field(default=None, description="D.5. Тепловыделения (кВт)")
    d6_protection: ExtractedValue | None = Field(default=None, description="D.6. Степень защиты (IP), класс зоны")
    d7_grounding: ExtractedValue | None = Field(default=None, description="D.7. Тип заземления")
    d8_cable_entry: ExtractedValue | None = Field(default=None, description="D.8. Точка ввода кабеля")

    # E. Сжатый воздух и газы
    e1_pressure: ExtractedValue | None = Field(default=None, description="E.1. Давление на входе (МПа)")
    e2_flow: ExtractedValue | None = Field(default=None, description="E.2. Расход (м3/ч или н.л/мин)")
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
```

### 3.5. CHECKLIST_FIELDS — полный список 44 параметров

```python
CHECKLIST_FIELDS = [
    ("a1_name", "A.1. Наименование и назначение"),
    ("a2_model", "A.2. Модель / полный артикул"),
    ("a3_manufacturer", "A.3. Производитель, страна"),
    ("a4_year_serial", "A.4. Год выпуска и серийный номер"),
    ("b1_dimensions", "B.1. Габариты (Д*Ш*В, мм)"),
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
    ("d4_startup", "D.4. Тип пуска, cos phi, Ки"),
    ("d5_heat", "D.5. Тепловыделения (кВт)"),
    ("d6_protection", "D.6. Степень защиты (IP), класс зоны"),
    ("d7_grounding", "D.7. Тип заземления"),
    ("d8_cable_entry", "D.8. Точка ввода кабеля"),
    ("e1_pressure", "E.1. Давление на входе (МПа)"),
    ("e2_flow", "E.2. Расход (м3/ч или н.л/мин)"),
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
```

### 3.6. SECTION_GROUPS — группировка по разделам

```python
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
```

### 3.7. ScannedFile — информация о файле

```python
@dataclass
class ScannedFile:
    path: Path
    name: str          # Имя файла
    extension: str     # Расширение (без точки, lowercase)
    format_label: str  # Метка формата из SUPPORTED_EXTENSIONS
    size_bytes: int    # Размер в байтах

    @property
    def size_display(self) -> str:
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        else:
            return f"{self.size_bytes / (1024 * 1024):.1f} MB"
```

### 3.8. Chunk — универсальный чанк

```python
@dataclass
class Chunk:
    source_file: str       # Имя исходного файла
    source_type: str       # Тип: Паспорт, Руководство, Чертёж, Каталог, Документ
    file_format: str       # Формат: PDF, Изображение, DOCX, Excel, CSV, Текст
    page_start: int | None # 1-based, None для не-PDF
    page_end: int | None   # 1-based, включительно
    data: bytes | str      # bytes для бинарных, str для текстовых
    mime_type: str          # MIME-тип
    total_pages: int | None = None  # Всего страниц в оригинале

    @property
    def page_range_display(self) -> str:
        if self.page_start is None:
            return "весь файл"
        if self.page_start == self.page_end:
            return f"стр. {self.page_start}"
        return f"стр. {self.page_start}--{self.page_end}"

    @property
    def source_display(self) -> str:
        return f"{self.source_file} ({self.source_type})"
```

### 3.9. PdfChunk — чанк PDF-документа

```python
@dataclass
class PdfChunk:
    source_file: str    # Имя исходного файла
    page_start: int     # Начальная страница (1-based)
    page_end: int       # Конечная страница (1-based, включительно)
    chunk_bytes: bytes   # PDF-данные чанка
    total_pages: int     # Всего страниц в оригинале

    @property
    def page_range_display(self) -> str:
        if self.page_start == self.page_end:
            return f"стр. {self.page_start}"
        return f"стр. {self.page_start}--{self.page_end}"
```

---

## 4. КОНФИГУРАЦИЯ

### 4.1. Пути конфигурации

```python
CONFIG_DIR = Path.home() / ".factum"
CONFIG_FILE = CONFIG_DIR / "config.json"
```

Файл конфигурации: `~/.factum/config.json`

### 4.2. SUPPORTED_EXTENSIONS

```python
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
```

### 4.3. FIXED_MODEL — фиксированная модель Gemini

```python
FIXED_MODEL = "gemini-2.5-pro"
```

Выбор модели убран из интерфейса. Используется единственная фиксированная модель `gemini-2.5-pro` для максимального качества извлечения.

### 4.4. DEFAULT_CONFIG

```python
DEFAULT_CONFIG = {
    "api_key": "",
    "model": FIXED_MODEL,    # Ссылается на FIXED_MODEL = "gemini-2.5-pro"
    "chunk_size": 10,         # Было 7 — увеличено для оптимального баланса
    "overlap": 2,             # Перекрытие чанков (страниц) — предотвращает потерю данных на границах
    "output_dir": "",
}
```

### 4.5. load_config() / save_config()

- **load_config():** Читает JSON из `CONFIG_FILE`. Мержит с `DEFAULT_CONFIG` (хранимые значения перезаписывают дефолты). Если файл не существует — возвращает `DEFAULT_CONFIG`.
- **save_config():** Создаёт `CONFIG_DIR` (с parents=True), пишет JSON с `ensure_ascii=False, indent=2`.

### 4.6. MIME_TYPES

Определён в `chunking/chunk_manager.py`:

```python
MIME_TYPES = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "bmp": "image/bmp",
    "tiff": "image/tiff",
    "tif": "image/tiff",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "doc": "application/msword",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xls": "application/vnd.ms-excel",
    "csv": "text/csv",
    "txt": "text/plain",
}
```

---

## 5. КОНВЕЙЕР ОБРАБОТКИ (6 ЭТАПОВ)

### 5.1. Обзор конвейера

```
Файлы/Папка (от пользователя)
    |
[Этап 1: ПОДГОТОВКА]
    | Сканирование -> Классификация -> Чанкинг (с overlap)
    v
Список чанков (Chunk[])
    |
[Этап 2: КОНТЕКСТ ОБОРУДОВАНИЯ]      <-- НОВЫЙ
    | Первые чанки каждого файла -> Gemini API -> equipment_context
    v
Контекст: тип, подсистемы, класс мощности, тип питания
    |
[Этап 3: ИЗВЛЕЧЕНИЕ]
    | Для каждого чанка: Gemini API + equipment_context -> ChunkExtraction
    v
Список извлечений: (Chunk, ChunkExtraction)[]
    |
[Этап 4: АГРЕГАЦИЯ]
    | Дедупликация overlap-дублей + Объединение + разрешение конфликтов
    v
Финальные данные: dict[field_name -> ExtractedValue | None]
    |
[Этап 5: ВЕРИФИКАЦИЯ]
    | Gemini + equipment_context: полнота, конфликты, косвенные, логика
    v
Обновлённые данные + примечания
    |
[Этап 6: ГЕНЕРАЦИЯ DOCX]
    | Формирование таблиц, источников, примечаний
    v
DOCX-файл + HTML-превью
```

### 5.2. Этап 1: Сканирование, Классификация, Чанкинг

#### 5.2.1. Сканирование (scanner/folder_scanner.py)

**`scan_path(path: Path) -> list[ScannedFile]`:**
- Если `path` — файл: проверяет расширение в `SUPPORTED_EXTENSIONS`, создаёт `ScannedFile`
- Если `path` — папка: итерирует `sorted(path.iterdir())`, создаёт `ScannedFile` для каждого поддерживаемого файла (не рекурсивно)

**`_try_create_scanned_file(path: Path) -> ScannedFile | None`:**
- Извлекает расширение: `path.suffix.lower().lstrip(".")`
- Если расширение в `SUPPORTED_EXTENSIONS`: возвращает `ScannedFile` с `format_label` из словаря
- Иначе: возвращает `None`

#### 5.2.2. Классификация (scanner/file_classifier.py)

**Regex-паттерны по типам документов:**

```python
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
```

**`classify_file(path: Path) -> str`:**
1. Получить расширение: `path.suffix.lower().lstrip(".")`
2. Если расширение в `IMAGE_EXTENSIONS`:
   - Искать паттерны в `path.stem.lower()` (re.IGNORECASE)
   - Если совпадение: вернуть тип
   - Иначе: вернуть `"Чертёж"` (изображения по умолчанию = чертежи)
3. Иначе (не изображение):
   - Искать паттерны в `path.stem.lower()` (re.IGNORECASE)
   - Если совпадение: вернуть тип
   - Иначе: вернуть `"Документ"`

#### 5.2.3. Чанкинг (chunking/)

**`split_pdf(path: Path, chunk_size: int = 7, overlap: int = 2) -> list[PdfChunk]`:**
- Открывает PDF через `fitz.open(str(path))` (PyMuPDF)
- `total_pages = len(doc)`
- **Вычисляет шаг с учётом перекрытия:** `step = max(1, chunk_size - overlap)`
- Итерирует с шагом `step` (start_idx от 0):
  - `end_idx = min(start_idx + chunk_size - 1, total_pages - 1)`
  - Создаёт новый PDF: `chunk_doc = fitz.open()`
  - `chunk_doc.insert_pdf(doc, from_page=start_idx, to_page=end_idx)`
  - `chunk_bytes = chunk_doc.tobytes()`
  - Создаёт `PdfChunk(source_file=path.name, page_start=start_idx+1, page_end=end_idx+1, chunk_bytes=chunk_bytes, total_pages=total_pages)`
  - **Условие остановки:** `if end_idx >= total_pages - 1: break` (предотвращение лишнего чанка)
- Закрывает оригинальный документ

> **Пример:** chunk_size=10, overlap=2 → step=8 → Чанк 1: стр. 1-10, Чанк 2: стр. 9-18, Чанк 3: стр. 17-26. Страницы 9-10 и 17-18 обрабатываются дважды, что предотвращает потерю данных на границах.

**`create_chunks(files: list[ScannedFile], chunk_size: int = 7, overlap: int = 2) -> list[Chunk]`:**

Для каждого файла определяет тип через `classify_file()`, затем:

| Формат | Обработка |
|--------|-----------|
| PDF (`ext == "pdf"`) | `split_pdf()` -> Chunk для каждого PdfChunk, `data=chunk_bytes`, `mime_type="application/pdf"` |
| Текст (`ext in ("txt", "csv")`) | `charset_normalizer.from_path()` для кодировки, fallback `utf-8 errors="replace"`. Один Chunk, `data=text (str)`, `page_start=None` |
| Изображения (`ext in IMAGE_EXTENSIONS`) | `path.read_bytes()`, один Chunk, `page_start=1, page_end=1` |
| Остальные (DOCX, XLS) | `path.read_bytes()`, один Chunk, `page_start=None, page_end=None` |

### 5.3. Этап 2: Определение контекста оборудования

Новый этап, добавленный для повышения точности извлечения параметров. Gemini анализирует начальные страницы всех загруженных файлов и определяет тип оборудования, подсистемы и другие характеристики.

#### 5.3.1. _get_first_chunks(chunks) -> list[Chunk]

Получает первый чанк каждого уникального файла (по `source_file`):

```python
def _get_first_chunks(chunks: list[Chunk]) -> list[Chunk]:
    seen: set[str] = set()
    result: list[Chunk] = []
    for c in chunks:
        if c.source_file not in seen:
            seen.add(c.source_file)
            result.append(c)
    return result
```

#### 5.3.2. GeminiClient.determine_equipment_context(first_chunks)

```python
def determine_equipment_context(self, first_chunks: list[Chunk]) -> dict | None:
```

Алгоритм:
1. Для каждого первого чанка формирует Part (текст или bytes)
2. Добавляет `make_context_prompt(file_names)` последним
3. Вызывает `_call_with_retry(system_prompt=CONTEXT_SYSTEM_PROMPT, parts=parts)`
4. Возвращает dict с 7 полями: `equipment_type`, `equipment_name`, `purpose`, `subsystems`, `power_class`, `supply_type`, `notes`
5. При ошибке возвращает `None`

#### 5.3.3. _format_context(ctx: dict) -> str

Преобразует dict контекста в текстовый блок для передачи в промпты:

```python
def _format_context(ctx: dict) -> str:
    lines = []
    if ctx.get("equipment_type"): lines.append(f"Тип: {ctx['equipment_type']}")
    if ctx.get("equipment_name"): lines.append(f"Наименование: {ctx['equipment_name']}")
    if ctx.get("purpose"): lines.append(f"Назначение: {ctx['purpose']}")
    if ctx.get("subsystems"):
        subs = ctx["subsystems"]
        if isinstance(subs, list):
            lines.append(f"Подсистемы: {', '.join(subs)}")
        else:
            lines.append(f"Подсистемы: {subs}")
    if ctx.get("power_class"): lines.append(f"Класс мощности: {ctx['power_class']}")
    if ctx.get("supply_type"): lines.append(f"Тип питания: {ctx['supply_type']}")
    if ctx.get("notes"): lines.append(f"Примечания: {ctx['notes']}")
    return "\n".join(lines)
```

#### 5.3.4. Graceful fallback

Если Gemini не вернул контекст (None), pipeline продолжает работу **без контекста**: `equipment_context = ""`. Это гарантирует обратную совместимость.

### 5.4. Этап 3: Извлечение параметров через Gemini

#### 5.4.1. GeminiClient

```python
class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.last_error: str = ""  # Для отображения ошибок в GUI
```

> **Примечание:** Дефолтная модель `gemini-2.5-flash` в конструкторе, но `worker.py` всегда передаёт `FIXED_MODEL = "gemini-2.5-pro"`.

#### 5.4.2. extract_from_chunk(chunk: Chunk, equipment_context: str = "") -> ChunkExtraction | None

Алгоритм:

1. Формирует `user_prompt` через `make_extraction_prompt(equipment_context=equipment_context)`
2. Формирует `parts`:
   - Если `chunk.data` — строка (текст): один `Part.from_text(text=f"Содержимое документа:\n\n{chunk.data}\n\n---\n\n{user_prompt}")`
   - Если `chunk.data` — bytes: `Part.from_bytes(data=chunk.data, mime_type=chunk.mime_type)` + `Part.from_text(text=user_prompt)`
3. Вызывает `_call_with_retry(system_prompt=EXTRACTION_SYSTEM_PROMPT, parts=parts)`
4. Если ответ `None` — возвращает `None`
5. **Fallback (список -> словарь):** Если `raw` — list, конвертирует через `_convert_list_to_dict(raw)`
6. **Заполнение source из метаданных чанка:** Для каждого поля в `raw`:
   - Если `source` — dict и `file` пуст: `src["file"] = chunk.source_file`
   - Если `source` — dict и `doc_type` пуст: `src["doc_type"] = chunk.source_type`
   - Если `source` — None: создаёт `{"file": chunk.source_file, "doc_type": chunk.source_type}`
7. Валидирует через `ChunkExtraction.model_validate(raw)`
8. При ошибке валидации: `self.last_error = f"Невалидный JSON от Gemini: {e}"`, возвращает `None`

#### 5.4.3. Маппинг param_id -> field_name

Генерируется автоматически из `CHECKLIST_FIELDS`:

```python
_PARAM_ID_TO_FIELD = {}
for _field_name, _label in CHECKLIST_FIELDS:
    # "A.1. Наименование..." -> "A.1"
    _param_id = _label.split(".")[0] + "." + _label.split(".")[1].split(" ")[0]
    _param_id = _param_id.strip()
    _PARAM_ID_TO_FIELD[_param_id] = _field_name
    _PARAM_ID_TO_FIELD[_param_id.replace(" ", "")] = _field_name
```

Результат: `{"A.1": "a1_name", "A.2": "a2_model", ..., "H.4": "h4_climate"}`

#### 5.4.4. _convert_list_to_dict(raw_list: list) -> dict

Конвертирует `[{param_id: "A.1", value: "...", source: {...}}]` в `{a1_name: {value: "...", source: {...}}}`:

```python
def _convert_list_to_dict(raw_list: list) -> dict:
    result = {}
    for item in raw_list:
        if not isinstance(item, dict): continue
        param_id = item.get("param_id", "").strip()
        field_name = _PARAM_ID_TO_FIELD.get(param_id)
        if field_name:
            entry = {k: v for k, v in item.items() if k != "param_id"}
            result[field_name] = entry
    return result
```

#### 5.4.5. _call_with_retry(system_prompt, parts) -> dict | None

**Константы:**
- `MAX_RETRIES = 3`
- `RETRY_DELAY_BASE = 5` секунд

**Алгоритм:**
1. `self.last_error = ""`
2. Цикл `attempt` от 0 до `MAX_RETRIES - 1`:
   - Вызов `client.models.generate_content()`:
     - `model`: self.model
     - `contents`: `[types.Content(role="user", parts=parts)]`
     - `config`: `types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.1, response_mime_type="application/json")`
   - **ВАЖНО:** НЕ использовать `response_schema`! (Схема слишком сложная для Gemini)
   - Если `response.text` пуст: `self.last_error = "Пустой ответ от Gemini"`, continue
   - Парсинг JSON: `json.loads(response.text)`
   - **Fallback:** Если `JSONDecodeError` — удалить обёртку ` ```json ... ``` `:
     ```python
     text = response.text.strip()
     if text.startswith("```json"): text = text[7:]
     if text.startswith("```"): text = text[3:]
     if text.endswith("```"): text = text[:-3]
     return json.loads(text.strip())
     ```
   - При ошибке: задержка `RETRY_DELAY_BASE * (2 ** attempt)` = 5с, 10с, 20с
   - Сохраняет ошибку в `self.last_error`
3. Если все попытки исчерпаны: возвращает `None`

#### 5.4.6. verify_extraction(aggregated_json, chunks, equipment_context="") -> dict | None

1. Формирует `user_prompt` через `make_verification_prompt(aggregated_json, equipment_context=equipment_context)`
2. Формирует `parts` из всех чанков:
   - Текстовые: `Part.from_text(text=f"--- {chunk.source_file} ({chunk.page_range_display}) ---\n{chunk.data}\n")`
   - Бинарные: `Part.from_bytes(data=chunk.data, mime_type=chunk.mime_type)` (с лимитом `max_upload_size = 40 MB`)
3. Добавляет `Part.from_text(text=user_prompt)` последним
4. Вызывает `_call_with_retry(system_prompt=VERIFICATION_SYSTEM_PROMPT, parts=parts)`

### 5.5. Этап 4: Агрегация и разрешение конфликтов

#### 5.5.1. aggregate_extractions()

```python
def aggregate_extractions(
    extractions: list[tuple[Chunk, ChunkExtraction]]
) -> dict[str, list[ExtractedValue]]:
```

Алгоритм:
1. Инициализирует `aggregated = {field: [] for field, _ in CHECKLIST_FIELDS}`
2. Для каждой пары `(chunk, extraction)`:
   - Для каждого поля из `CHECKLIST_FIELDS`:
     - Получает значение через `getattr(extraction, field_name, None)`
     - Если значение не None:
       - **Пересчёт страницы:** `value.source.page = chunk.page_start + value.source.page - 1` (из чанк-relative в абсолютную)
       - `value.source.file = chunk.source_file`
       - `value.source.doc_type = chunk.source_type`
       - Добавляет в `aggregated[field_name]`

#### 5.5.2. _deduplicate_overlaps(values, overlap=2)

Убирает дубли из перекрывающихся чанков одного файла. Вызывается в `resolve_aggregated()` для каждого параметра **перед** проверкой конфликтов.

**Константа OCR-пар:**

```python
_OCR_DIGIT_PAIRS = {
    ('3', '5'), ('5', '3'), ('3', '8'), ('8', '3'),
    ('5', '8'), ('8', '5'), ('6', '0'), ('0', '6'),
    ('1', '7'), ('7', '1'),
}
```

**Вспомогательная функция:**

```python
def _are_ocr_variants(a: str, b: str) -> bool:
    """Два значения отличаются только OCR-подобными подменами цифр (≤2 различия)."""
    a_s, b_s = a.strip(), b.strip()
    if len(a_s) != len(b_s):
        return False
    diffs = 0
    for ca, cb in zip(a_s, b_s):
        if ca != cb:
            if (ca, cb) in _OCR_DIGIT_PAIRS:
                diffs += 1
            else:
                return False
    return 1 <= diffs <= 2
```

**Основная функция:**

```python
def _deduplicate_overlaps(values: list[ExtractedValue], overlap: int = 2) -> list[ExtractedValue]:
    if len(values) <= 1:
        return values

    confidence_order = {"high": 0, "medium": 1, "low": 2}
    kept: list[ExtractedValue] = []
    for v in values:
        is_overlap_dup = False
        for i, existing in enumerate(kept):
            # Общие условия overlap: один файл, обе страницы известны, страницы близки
            if not (existing.source.file == v.source.file
                    and existing.source.file
                    and existing.source.page is not None
                    and v.source.page is not None
                    and abs(existing.source.page - v.source.page) <= overlap):
                continue

            # Точное совпадение — дубль
            if existing.value.strip() == v.value.strip():
                is_overlap_dup = True
                break

            # OCR-вариант — оставить более надёжное, пометить как low
            if _are_ocr_variants(existing.value, v.value):
                is_overlap_dup = True
                existing_conf = confidence_order.get(existing.source.confidence, 99)
                v_conf = confidence_order.get(v.source.confidence, 99)
                if v_conf < existing_conf:
                    # Новое значение надёжнее — заменить
                    v.note = (v.note + "; " if v.note else "") + f"OCR-вариант отброшен: {existing.value!r}"
                    v.source.confidence = "low"
                    kept[i] = v
                else:
                    existing.note = (existing.note + "; " if existing.note else "") + f"OCR-вариант отброшен: {v.value!r}"
                    existing.source.confidence = "low"
                break

        if not is_overlap_dup:
            kept.append(v)
    return kept
```

**Логика (три ветки):**
1. **Точное совпадение** — если два значения из одного файла и их страницы близки (разница ≤ overlap) и значения идентичны — это повторное извлечение с перекрывающихся страниц (дубль). Отбрасывается.
2. **OCR-вариант** — если значения одинаковой длины и отличаются на 1-2 символа из `_OCR_DIGIT_PAIRS` (3↔5, 6↔0 и т.д.) — это вероятные ошибки OCR. Оставляется значение с более высоким confidence, confidence понижается до `"low"`, в `note` добавляется запись об отброшенном варианте.
3. **Разные значения** — если значения различаются существенно (не OCR-вариант) — оба сохраняются (это настоящие разные значения, например, 380В и 220В).

#### 5.5.3. resolve_aggregated()

```python
def resolve_aggregated(
    aggregated: dict[str, list[ExtractedValue]]
) -> dict[str, ExtractedValue | None]:
```

Для каждого поля:
1. **Дедупликация:** `values = _deduplicate_overlaps(values)` — убирает overlap-дубли
2. **0 значений** -> `None`
3. **1 значение** -> берёт как есть
4. **>1 одинаковых** -> `resolve_conflict()` (выбор по приоритету)
5. **>1 разных** -> `resolve_conflict()` + `status="конфликт"`, `note="КОНФЛИКТ: ..."` + **заполняются `conflict_values`:**

```python
entries = []
for v in values:
    entries.append(ConflictEntry(
        value=v.value,
        source=v.source.model_copy(),
        is_selected=(v.value.strip() == best.value.strip()
                     and v.source.file == best.source.file),
    ))
best.conflict_values = entries
```

#### 5.5.4. resolve_conflict()

**Иерархия приоритетов источников:**

```python
SOURCE_PRIORITY = {
    "Паспорт": 0,      # Наивысший приоритет
    "Каталог": 1,
    "Руководство": 2,
    "Чертёж": 3,
    "Документ": 4,      # Наинизший
}
```

**Алгоритм:**

```python
def sort_key(v: ExtractedValue) -> tuple:
    priority = SOURCE_PRIORITY.get(v.source.doc_type, 99)
    confidence = confidence_order.get(v.source.confidence, 99)
    # Штраф для low-confidence: Паспорт low (0+2=2) проигрывает
    # Каталогу high (1+0=1), но бьёт Чертёж high (3+0=3)
    if v.source.confidence == "low":
        priority += 2
    return (priority, confidence)
```

1. `confidence_order = {"high": 0, "medium": 1, "low": 2}`
2. Вычисляется `priority` из `SOURCE_PRIORITY` + штраф `+2` для `confidence == "low"`
3. Сортировка по ключу `(priority, confidence)`
4. Берётся первый (наилучший) элемент

**Пример штрафа:** Паспорт с low confidence: `priority = 0 + 2 = 2`. Каталог с high confidence: `priority = 1 + 0 = 1`. Каталог выигрывает (1 < 2), потому что данные из Паспорта ненадёжны (плохо читаемый скан).

### 5.6. Этап 5: Верификация

#### 5.6.1. _resolved_to_json(resolved) -> str

Для каждого поля из `CHECKLIST_FIELDS`:
- Если `ExtractedValue` есть: `{field_name: {"label": label, "value": ev.value, "source_file": ev.source.file, "source_type": ev.source.doc_type, "page": ev.source.page, "section": ev.source.section, "quote": ev.source.quote}}`
- Если `None`: `{field_name: {"label": label, "value": null}}`

Формат: `json.dumps(data, ensure_ascii=False, indent=2)`

> **Примечание:** `verify_extraction()` теперь принимает `equipment_context` и передаёт в `make_verification_prompt()`.

#### 5.6.2. apply_verification()

Обрабатывает 6 категорий из ответа Gemini (в порядке обработки):

| Категория | Действие |
|-----------|----------|
| `corrections` | **OCR-коррекции.** Если поле существует, не None, и `corrected_value` указано: заменяет `value` на `corrected_value`, добавляет в `note` запись `"[ИСПРАВЛЕНО] {issue} (было: {old_value})"`, устанавливает `confidence="medium"`. Добавляет примечание. |
| `additional_values` | Если поле = None: создаёт `ExtractedValue(value=..., source=SourceRef(confidence="medium"), status="[UPD] верификация")` |
| `missing_params` | Добавляет примечание: `"{label} -- в документации не указан. {suggestion}"` |
| `conflicts` | Добавляет примечание: `"{label} -- расхождение: {values_str}"` |
| `indirect_params` | Если поле = None: создаёт `ExtractedValue(value=suggested, source=SourceRef(confidence="low"), status="[справочно: косвенный вывод]", note=reasoning)`. Добавляет примечание. |

**Блок corrections (OCR-коррекции):**

```python
for item in verification.get("corrections", []):
    field = item.get("field", "")
    corrected_value = item.get("corrected_value")
    issue = item.get("issue", "")
    if field in resolved and resolved[field] is not None and corrected_value:
        old_value = resolved[field].value
        resolved[field].value = corrected_value
        resolved[field].note = (
            (resolved[field].note + "; " if resolved[field].note else "")
            + f"[ИСПРАВЛЕНО] {issue} (было: {old_value})"
        )
        resolved[field].source.confidence = "medium"
        notes.append(f"{label_map.get(field, field)} — исправлено: {issue}")
```

Этот блок обрабатывается **первым** (до `additional_values`), чтобы коррекции применялись к уже существующим значениям до добавления новых.

### 5.7. Этап 6: Генерация DOCX и HTML-превью

**validate_completeness()** (между этапами 3 и 4):
- Подсчитывает `(present, missing, warnings)`
- Логирует: `"Найдено: {len(present)}, пропущено: {len(missing)}, предупреждений: {len(warnings)}"`

Генерация описана в разделах 9 (DOCX) и 11 (HTML-превью).

---

## 6. ПРОМПТЫ GEMINI API (ДОСЛОВНО)

> **Это ключевой раздел.** Промпты определяют качество извлечения. Воспроизводить ДОСЛОВНО.

### 6.0. CONTEXT_SYSTEM_PROMPT (Этап 2)

```
Ты — ведущий технический аналитик проектного института. Тебе предоставлены
начальные страницы документов на единицу оборудования.

Определи:
1. equipment_type: Тип оборудования (токарный станок, компрессор, насос и т.д.)
2. equipment_name: Полное наименование/модель
3. purpose: Назначение (обработка металла, перекачка жидкости и т.д.)
4. subsystems: Список основных подсистем (электропривод, пневматика, гидравлика,
   охлаждение, ЧПУ и т.д.)
5. power_class: Ориентировочный класс мощности (бытовое <1кВт / лёгкое 1-10кВт /
   среднее 10-50кВт / тяжёлое 50-200кВт / крупное >200кВт)
6. supply_type: Предполагаемый тип питания (1-фазное 220В / 3-фазное 380В /
   3-фазное 400-690В / постоянный ток / пневматическое / другое)
7. notes: Любые особенности, важные для интерпретации параметров

Ответ — строго JSON-объект с этими 7 полями. Если не удаётся определить — пиши "не определено".
```

### 6.0a. make_context_prompt()

```python
def make_context_prompt(file_list: list[str]) -> str:
    files_str = ", ".join(f"«{f}»" for f in file_list)
    return f"""Определи тип и характеристики оборудования на основании
начальных страниц этих документов: {files_str}.
Заполни все 7 полей JSON."""
```

### 6.1. EXTRACTION_SYSTEM_PROMPT

```
Ты — ведущий технический аналитик проектного института. Твоя задача — извлечь ВСЕ технические параметры оборудования из предоставленного фрагмента документации.

ПРАВИЛА:
1. Извлекай ТОЛЬКО данные, которые явно присутствуют в документе. Не домысливай.
2. Для каждого найденного параметра укажи:
   - value: значение с единицами измерения
   - page: номер страницы в этом фрагменте (1 = первая страница фрагмента)
   - section: название раздела/заголовка документа, где найдено значение
   - quote: цитата из оригинала (до 50 символов) — фрагмент текста, откуда взято значение
   - confidence: "high" если значение чёткое, "medium" если текст/скан среднего качества, "low" если плохо читается
3. Если параметр НЕ найден в этом фрагменте — НЕ включай его (оставь null).
4. Единицы измерения приводи к СИ. Оригинальные единицы — в скобках: "0,6 МПа (6 бар)".
5. Размеры: формат Д × Ш × В через " × " с пробелами. Единица в конце: "3 429 × 1 890 × 2 010 мм".
6. Десятичный разделитель: запятая. Разделитель тысяч: пробел. Пример: "5 800 кг".
7. Диапазоны: тире без пробелов. Пример: "0,3–0,5 МПа".
8. Давление: МПа, в скобках бар. Пример: "0,6 МПа (6 бар)".
9. Если есть режимы работы (пуск/работа/промывка) — перечисли через ";": "Пуск: 2,5 м³/ч; Работа: 1,8 м³/ч".
10. Перевод терминов: "[Переведённый термин] (Original Term)".
11. МНОЖЕСТВЕННЫЕ ЗНАЧЕНИЯ: Если для одного параметра есть несколько значений
    (например, напряжение питания 380 В И напряжение управления 220 В, или
    несколько двигателей с разной мощностью) — перечисляй ВСЕ через ";":
    "380 В (силовое питание); 220 В (цепи управления)".
    Для D.1 (мощность) — если в документе перечислены мощности отдельных приводов,
    укажи каждый И рассчитай суммарную: "Σ ≈ 42,6 кВт (шпиндель 30 + подачи 4,3+4,5 + ...)".
12. КРОСС-СЕКЦИОННЫЙ ПОИСК: Параметры групп D–H часто разбросаны по разным
    разделам документа. Например:
    - Давление сжатого воздуха (E.1) может быть в разделах «Смазка», «Охлаждение», «Пневмосистема»
    - Расход воды (F.3) может быть в разделах «Охлаждение», «СОЖ»
    - Мощности двигателей (D.1) могут быть в «Электрооборудование», «Приводы», «Спецификация»
    Ищи данные ВО ВСЁМ фрагменте, не только в разделе с подходящим заголовком.
13. ТОЧНОСТЬ СИМВОЛОВ ПРИ ЧТЕНИИ СКАНОВ:
    a) Путаница цифр и кириллицы: 0↔О, 1↔l↔I, П↔11, Б↔6, В↔8, З↔3
    b) Путаница ЦИФР на старых/нечётких сканах: 3↔5↔8, 6↔0, 1↔7.
       Особенно проверяй цифровые диапазоны (например, "30–80%", "3–5 МПа"):
       если первая цифра диапазона плохо читается — перечитай её внимательно.
    c) При подозрении — установи confidence="low" и добавь в note:
       "возможна ошибка OCR: символ [X] мог быть прочитан как [Y]"
       с указанием конкретных подозрительных символов.
    d) Индексы моделей: кириллическая буква среди цифр — вероятно ошибка распознавания.
14. КОНТЕКСТ ИЗВЛЕЧЕНИЯ: Группы B–H описывают ТРЕБОВАНИЯ К ПЛОЩАДКЕ/ЗДАНИЮ
    для размещения и подключения оборудования. Это данные, нужные ПРОЕКТИРОВЩИКУ
    (архитектору, электрику, сантехнику) для подготовки помещения:
    - D: Что подать от ВНЕШНЕЙ электросети на вводной щит оборудования
    - E: Что подать от ВНЕШНЕЙ пневмосети на вход оборудования
    - F: Что подать от ВНЕШНЕЙ водопроводной сети
    Если документ содержит и внешние (подключение к сетям здания), и внутренние
    (параметры внутренних узлов) значения — извлекай ВНЕШНИЕ, т.к. они нужны проектировщику.

ЧЕК-ЛИСТ ПАРАМЕТРОВ (A.1–H.4):

### A. Идентификация
A.1. Наименование и назначение
A.2. Модель / полный артикул
A.3. Производитель, страна, ссылка на сайт
A.4. Год выпуска и серийный номер. Если год выпуска не указан явно — ищи дату издания документации (на обложке, титульном листе) как приближение, с пометкой "дата издания документации" в note

### B. Габариты и логистика заноса
B.1. Габариты (Д×Ш×В, мм) — в рабочем и транспортном положении
B.2. Минимальный монтажный проём (Ш×В, мм)
B.3. Масса нетто и масса с жидкостями (кг). При наличии нескольких модификаций/комплектаций — указать вес КАЖДОЙ. Если вес указан по частям (корпус + конвейер + бак) — рассчитай суммарный
B.4. Масса тяжелейшей части при транспортировке (кг)
B.5. Точки строповки и центр тяжести

### C. Строительные требования (АС)
C.1. Тип установки: фундамент / виброопоры / анкерное крепление
C.2. Размеры фундамента или опорной рамы (Д×Ш×Г, мм)
C.3. Глубина приямков или высота подиума
C.4. Статические и динамические нагрузки
C.5. Зона обслуживания: мин. расстояния от стен / соседнего оборудования
C.6. Требования к полу: ровность, допуски, нагрузка на перекрытие
C.7. Требования к строительным конструкциям / отделке

### D. Электроснабжение и тепло (ЭМ / ОВ)
D.1. Суммарная установленная мощность P_уст (кВт) — сумма ВСЕХ двигателей/приводов, включая вспомогательные (АСИ, насосы СОЖ, гидростанция, конвейер стружки и т.д.). Если перечислены отдельные приводы — укажи КАЖДЫЙ и рассчитай Σ. Проверь таблицы полностью — не пропускай строки. Отдельно P_потр если указана.
D.2. ВСЕ напряжения внешнего питания: силовое (380 В) И управление (220 В) если различаются; фазность (3ф/1ф), частота (Гц), ток (А)
D.3. Категория надёжности электроснабжения (I, II, III), ИБП
D.4. Тип пуска, cos φ, Ки, компенсация реактивной мощности
D.5. Тепловыделения (кВт) — в воздух и в систему охлаждения
D.6. Степень защиты (IP), класс зоны
D.7. Тип заземления (TN-S, TN-C-S), точка подключения контура
D.8. Точка ввода кабеля: направление, координаты

### E. Сжатый воздух и газы (ТХ)
E.1. Давление сжатого воздуха на входе (МПа) — рабочее и пиковое. Искать во ВСЕХ разделах: пневматика, смазка, охлаждение, зажим
E.2. Расход (м³/ч или н.л/мин) — средний и максимальный
E.3. Качество среды: класс чистоты, масло, точка росы
E.4. Точка подключения: Ø, тип резьбы/фланца, координаты

### F. Водоснабжение и канализация (ВК)
F.1. Назначение воды (охлаждение, промывка, технологическая)
F.2. Требования к качеству воды
F.3. Расход воды, давление, температура
F.4. Точка подключения: Ø, тип соединения, координаты
F.5. Канализация: расход стоков, температура, состав
F.6. Точка слива: самотёк/давление, высота, Ø
F.7. СОЖ: объём системы, марка, сепарация
F.8. Периодичность потребления

### G. Вентиляция, экология и шум (ОВ)
G.1. Локальные отсосы: Ø патрубков, объём, разрежение
G.2. Состав выбросов: ПДК, температура газов, взрывоопасность
G.3. Уровень звукового давления (дБА) на расстоянии 1 м
G.4. Вибрация: уровни, виброизоляция

### H. Автоматизация и безопасность (АТХ / СС)
H.1. IT-инфраструктура: порты, протоколы
H.2. Интеграция в систему безопасности (E-Stop, блокировка)
H.3. Световая и звуковая сигнализация
H.4. Микроклимат: ВСЕ режимы — рабочий, рекомендуемый, хранение. Формат: "Рабочая: T°C, W% RH; Хранение: T°C, W% RH". Если один диапазон — уточни тип

ФОРМАТ ОТВЕТА — строго JSON-объект (НЕ массив!) с ключами ниже.
Для каждого найденного параметра — объект с полями value и source.
Ненайденные параметры — не включай (или null).

Ключи: a1_name, a2_model, a3_manufacturer, a4_year_serial,
b1_dimensions, b2_opening, b3_weight, b4_heaviest_part, b5_rigging,
c1_installation, c2_foundation, c3_pits, c4_loads, c5_service_zone, c6_floor, c7_construction,
d1_power, d2_voltage, d3_reliability, d4_startup, d5_heat, d6_protection, d7_grounding, d8_cable_entry,
e1_pressure, e2_flow, e3_quality, e4_connection,
f1_purpose, f2_quality, f3_flow, f4_connection, f5_drainage, f6_drain_point, f7_coolant, f8_periodicity,
g1_exhaust, g2_emissions, g3_noise, g4_vibration,
h1_it, h2_safety, h3_signaling, h4_climate.

Пример ответа:
{
  "a1_name": {
    "value": "Токарный станок с ЧПУ",
    "source": {"file": "passport.pdf", "doc_type": "Паспорт", "page": 1, "section": "Введение", "quote": "CNC Lathe", "confidence": "high"}
  },
  "a2_model": {
    "value": "CTX 450",
    "source": {"file": "passport.pdf", "doc_type": "Паспорт", "page": 1, "section": "Введение", "quote": "Model: CTX 450", "confidence": "high"}
  },
  "b3_weight": {
    "value": "5 800 кг",
    "source": {"file": "passport.pdf", "doc_type": "Паспорт", "page": 3, "section": "Характеристики", "quote": "Weight: 5800 kg", "confidence": "high"}
  }
}
```

### 6.2. make_extraction_prompt()

```python
def make_extraction_prompt(source_file: str, source_type: str,
                           page_start: int | None, page_end: int | None,
                           equipment_context: str = "") -> str:
    # Формирует page_info:
    # - "Это страница {N} файла <<{file}>>."            (page_start == page_end)
    # - "Это страницы {N}--{M} файла <<{file}>>."       (page_start != page_end)
    # - "Это файл <<{file}>>."                           (page_start is None)

    context_block = ""
    if equipment_context:
        context_block = f"""
КОНТЕКСТ ОБОРУДОВАНИЯ (определён предварительным анализом):
{equipment_context}

Используй этот контекст для разрешения неоднозначностей при интерпретации параметров.
Например, если оборудование питается от 3-фазной сети 380В, а в документе встречается
напряжение 12В или 24В -- это скорее всего внутренний источник питания (для управления,
датчиков), а НЕ параметр электроснабжения площадки (D.2).
Аналогично: если оборудование подключается к пневмосети, а в документе указан редуктор
с выходным давлением 0,2 МПа -- это внутренний параметр; для D/E групп нужно давление
НА ВХОДЕ в оборудование (от магистрали здания).
Не пропускай параметры, явно указанные в документе -- контекст лишь помогает
отличить внешние требования к подключению от внутренних параметров узлов.
"""

    return f"""{page_info}
Тип документа: {source_type}.
{context_block}
Извлеки ВСЕ технические параметры оборудования из этого фрагмента по чек-листу A.1--H.4.
Для каждого найденного параметра заполни: value, page (номер страницы в ЭТОМ фрагменте, начиная с 1), section, quote, confidence.
Параметры, которых НЕТ в этом фрагменте -- оставь null.
Помни: номер страницы в поле "page" -- это номер страницы ВНУТРИ этого фрагмента (1 = первая страница фрагмента)."""
```

### 6.3. VERIFICATION_SYSTEM_PROMPT

```
Ты — ведущий технический аналитик проектного института. Тебе предоставлены:
1. Агрегированные данные из карточки оборудования (JSON).
2. Исходные документы.

Твои задачи:
1. ПРОВЕРКА ПОЛНОТЫ: Какие параметры из чек-листа A.1–H.4 отсутствуют? Есть ли данные, которые были пропущены при первичном извлечении?
2. ПРОВЕРКА КОНФЛИКТОВ: Есть ли противоречия между значениями из разных источников?
3. КОСВЕННЫЕ ПАРАМЕТРЫ: Есть ли параметры, которые можно вывести косвенно? Например:
   - "охлаждение шпинделя" → требуется водоснабжение (группа F)
   - "гидравлическая станция" → требуется слив масла (группа F)
   - "ЧПУ" → требуется IT-подключение (группа H)
4. ПРОВЕРКА ССЫЛОК: Корректны ли привязки значений к страницам документов?
5. ПРОВЕРКА ЛОГИЧЕСКОЙ НЕПРОТИВОРЕЧИВОСТИ:
   - Мощность (D.1) и напряжение (D.2) должны быть совместимы (энергетически реалистичны).
   - Параметры групп D–F должны описывать ВНЕШНИЕ подключения к сетям здания
     (что подать от сети), а не внутренние узлы оборудования (блоки питания,
     внутренние редукторы и т.п.). Если обнаружена путаница — найди и предложи
     правильное значение через additional_values.
6. ПРОВЕРКА ПОЛНОТЫ ЗНАЧЕНИЙ:
   - D.1: Если указана только мощность одного привода, а в документах перечислены
     несколько двигателей — рассчитай суммарную установленную мощность и добавь
     через additional_values.
   - D.2: Если указано одно напряжение, но в документе есть несколько питающих
     цепей (силовое + управление) — добавь все через additional_values.
   - E.1: Если указано «нет данных», но в документе есть давление воздуха
     в разделах смазки/охлаждения/пневмоаппаратуры — извлеки и добавь.
   - H.4: Если указан только один диапазон влажности — проверь, нет ли в документе
     другого (рабочий vs. рекомендуемый vs. хранение). Приоритет — рабочий диапазон.
7. ПРОВЕРКА ВОЗМОЖНЫХ ОШИБОК OCR:
   - Для значений с confidence="low" или note, содержащим "OCR" — перечитай
     соответствующее место в документе и сравни с извлечённым значением.
   - Для числовых диапазонов (X–Y): проверь, что нижняя граница < верхней
     и обе правдоподобны для данного параметра.
   - Если найдена вероятная ошибка — добавь исправление в corrections:
     {"field": "h4_climate", "issue": "OCR: '5' вероятно '3' (50→30)", "corrected_value": "..."}
8. ПРОВЕРКА ПОЛНОТЫ СУММИРОВАНИЯ:
   - D.1: Пересчитай суммарную мощность по ВСЕМ строкам таблицы двигателей,
     включая вспомогательные приводы (АСИ, насосы, конвейеры). Сравни с извлечённой Σ.
   - B.3: Если есть модификации — проверь, что указан полный вес (не только корпус).

Формат ответа — JSON:
{
  "missing_params": [{"field": "d5_heat", "suggestion": "Возможно указано на стр. 15 руководства"}],
  "conflicts": [{"field": "b3_weight", "values": ["5800 кг (паспорт)", "5750 кг (руководство)"]}],
  "indirect_params": [{"field": "f1_purpose", "reasoning": "Указано охлаждение шпинделя → нужна вода", "suggested_value": "Охлаждение шпинделя"}],
  "corrections": [{"field": "d2_voltage", "issue": "Номер страницы некорректен", "corrected_page": 14}, {"field": "h4_climate", "issue": "OCR: '5' вероятно '3' (50→30)", "corrected_value": "Рабочая: 20°C, 30–80% RH"}],
  "additional_values": [{"field": "e3_quality", "value": "Класс 1.4.1 по ISO 8573-1", "page": 18, "section": "Пневмосистема", "quote": "Air quality class 1.4.1", "file": "passport.pdf"}]
}
```

### 6.4. make_verification_prompt()

```python
def make_verification_prompt(aggregated_json: str,
                             equipment_context: str = "") -> str:
    context_block = ""
    if equipment_context:
        context_block = f"""
КОНТЕКСТ ОБОРУДОВАНИЯ:
{equipment_context}

Используй контекст для проверки логической непротиворечивости:
- Параметры D--F должны описывать ВНЕШНИЕ подключения (от сетей здания),
  а не внутренние узлы оборудования.
- Если тип питания -- 3-фазное 380В, а в D.2 указано 12В -- это ошибка.
- Если оборудование подключается к пневмосети, а в E.1 указано давление
  внутреннего редуктора -- нужно найти входное давление магистрали.
"""

    return f"""Вот агрегированные данные карточки оборудования:

{aggregated_json}
{context_block}
Проверь эти данные по исходным документам (приложены).
Выполни все 8 задач: полнота, конфликты, косвенные параметры, проверка ссылок,
логическая непротиворечивость, полнота значений, ошибки OCR, полнота суммирования.
Если нашёл дополнительные значения -- добавь в additional_values с полной ссылкой на источник."""
```

---

## 7. ВАЛИДАЦИЯ ПОЛНОТЫ

### 7.1. validate_completeness()

```python
def validate_completeness(
    resolved: dict[str, ExtractedValue | None]
) -> tuple[list[str], list[str], list[str]]:
    # Возвращает (present, missing, warnings)
```

Категоризация для каждого поля из CHECKLIST_FIELDS:

| Условие | Результат | Текст предупреждения |
|---------|-----------|----------------------|
| `value is None` | -> `missing` | -- |
| `status in ("нет данных", "не требуется")` | -> `present` | -- |
| `confidence == "low"` | -> `warnings` + `present` | `"{label} — считан с низкой уверенностью"` |
| `note` содержит `"OCR"` (case-insensitive) | -> `warnings` + `present` | `"{label} — возможная ошибка OCR, требует проверки"` |
| `"конфликт" in status` | -> `warnings` + `present` | `"{label} — расхождение между источниками"` |
| Все остальные | -> `present` | -- |

> **Новое:** Ветка проверки OCR добавлена между `confidence=="low"` и `"конфликт" in status`. Если в `note` параметра (после upper()) содержится подстрока `"OCR"`, генерируется предупреждение о возможной ошибке распознавания.

---

## 8. ФОРМАТИРОВАНИЕ ЗНАЧЕНИЙ

### 8.1. format_value() (output/formatter.py)

Последовательность 4 regex-трансформаций:

```python
def format_value(value: str) -> str:
    # 1. Десятичная точка -> запятая
    value = re.sub(r'(\d)\.(\d)', r'\1,\2', value)

    # 2. Разделители тысяч (пробел) для чисел >= 1000
    #    Regex: r'\b\d{4,}(?:,\d+)?\b'
    #    Алгоритм: reversed integer_part, вставка пробела каждые 3 цифры
    value = re.sub(r'\b\d{4,}(?:,\d+)?\b', add_thousands_sep, value)

    # 3. Символ умножения: x, X, х, Х -> " * " (Unicode \u00d7)
    value = re.sub(r'\s*[xXхХ]\s*', ' \u00d7 ', value)

    # 4. Тире в диапазонах: дефис/тире -> en-dash (Unicode \u2013)
    #    ВАЖНО: НЕ использовать raw string в replacement!
    value = re.sub(r'(\d)\s*[-\u2013\u2014]\s*(\d)', '\\1\u2013\\2', value)

    return value
```

> **КРИТИЧНО (Python 3.14):** В строке 4 replacement ДОЛЖЕН быть `'\\1\u2013\\2'` (обычная строка), а НЕ `r'\1\u2013\2'` (raw string). Raw string с `\u` вызывает `re.error: bad escape \u` в Python 3.12+.

### 8.2. Модуль units.py (processing/units.py)

```python
def normalize_pressure(value: str) -> str:
    """Нормализовать давление: МПа, в скобках бар."""
    # Ищет "N бар" или "N bar" (re.IGNORECASE)
    # bar_val / 10 = mpa_val
    # Формат: "X,X МПа (Y бар)" (русская запятая)

def format_number(value: float, decimals: int = 0) -> str:
    """Отформатировать число: запятая десятичная, пробел тысяч."""
    # f"{value:,.{decimals}f}" -> replace(",", " ") -> replace(".", ",")
    # Пример: 5800.5 -> "5 800,5"

def format_dimensions(value: str) -> str:
    """Нормализовать формат размеров: ' x ' через Unicode multiply."""
    # re.sub(r'\s*[xXхХ*]\s*', ' * ', value) с Unicode *
```

---

## 9. ВЫХОДНЫЕ ДОКУМЕНТЫ

### 9.1. DOCX-карточка (output/docx_generator.py)

#### 9.1.1. Структура документа

```python
def generate_card(resolved, notes, overview="", output_path=None) -> Document:
```

1. **Стиль по умолчанию:** Times New Roman 10pt
2. **Заголовок:** Heading level 1, центр, 14pt bold чёрный
   - Текст: `"КАРТОЧКА ОБОРУДОВАНИЯ: {model} -- {manufacturer}"`
   - model = `resolved["a2_model"].value` или "--"
   - manufacturer = `resolved["a3_manufacturer"].value` или "--"
3. **Подзаголовок:** Paragraph, центр, 9pt серый (100,100,100)
   - Текст: `"Ревизия: 1 * Дата формирования: {dd.mm.yyyy}"`
4. **Инженерный обзор** (если overview не пуст): Heading 2 + Paragraph
5. **Группы A-H:** Heading 2 + Table для каждой группы
6. **Примечания:** Heading 2 "ПРИМЕЧАНИЯ" + нумерованные абзацы

#### 9.1.2. Таблицы

| Группа | Столбцы | Ширины |
|--------|---------|--------|
| A (Идентификация) | 2: Параметр, Значение | 6 cm + 11 cm |
| B-H (остальные) | 3: Параметр, Значение, Источник / Статус | 5 cm + 5 cm + 7 cm |

- Стиль таблицы: `"Table Grid"`
- Выравнивание: `WD_TABLE_ALIGNMENT.CENTER`
- Шрифт ячеек: Times New Roman 9pt
- Заголовки: bold
- Отсутствующие значения: `"нет данных"` курсивом, источник = "--"
- Если есть `status`: значение + ` [{status}]`
- Если `confidence == "low"`: цвет источника `RGBColor(180, 0, 0)` (красный)

#### 9.1.3. Сбор примечаний (_collect_notes)

Порядок:
1. Конфликты (`"конфликт" in status`) -> `note` или `"{label} -- расхождение между источниками."`
2. Низкая уверенность (`confidence == "low"`) -> `"{label} -- считан с низким качеством, требует проверки."`
3. Пропуски (`value is None`) -> `missing_param_note(label)`
4. Дополнительные из верификации (`extra_notes`) без дублей

#### 9.1.4. Сохранение

```python
output_path.parent.mkdir(parents=True, exist_ok=True)
doc.save(str(output_path))
```

### 9.2. HTML-превью (_generate_html_preview в worker.py)

- Контейнер: `<html><body style='font-family: Arial; font-size: 10pt;'>`
- Заголовок: `<h2 align='center'>КАРТОЧКА ОБОРУДОВАНИЯ: {model} -- {manufacturer}</h2>`
- Для каждой группы A-H:
  - `<h3>{group_title}</h3>`
  - `<table border='1' cellpadding='4' cellspacing='0' width='100%'>`
  - Группа A: 2 столбца (Параметр, Значение)
  - Группы B-H: 3 столбца (Параметр, Значение, Источник)
  - Отсутствующие: `"<i>нет данных</i>"`, источник = "—"
  - Если `status` содержит «конфликт»: используется `_html_conflict_value(ev)` (структурированное отображение)
  - Иначе: `format_value(ev.value)` + `" <span style='color:orange'>[{status}]</span>"` при наличии status

#### 9.2.1. _html_conflict_value(ev)

Формирует HTML со структурированным цветовым отображением конфликта:

```python
def _html_conflict_value(ev) -> str:
    parts = []
    # Выбранное значение — зелёным
    parts.append(f"<b style='color:#008000;'>✔ {format_value(ev.value)}</b>"
                 f" <span style='color:#c87800; font-size:8pt;'>[конфликт]</span>")
    # Отклонённые варианты — серым
    if ev.conflict_values:
        for entry in ev.conflict_values:
            if entry.is_selected: continue
            src_text = entry.source.file
            if entry.source.doc_type: src_text += f", {entry.source.doc_type}"
            if entry.source.page: src_text += f", стр. {entry.source.page}"
            parts.append(f"<span style='color:#828282;'>✖ {format_value(entry.value)}</span>"
                         f" <span style='color:#a0a0a0; font-size:7pt;'>({src_text})</span>")
    return "<br>".join(parts)
```

#### 9.2.2. _html_notes_section(html, resolved, extra_notes)

Секция ПРИМЕЧАНИЯ в HTML-превью — 4 категории с непрерывной нумерацией:

1. **Конфликты** → блок «⚠ РАСХОЖДЕНИЯ МЕЖДУ ИСТОЧНИКАМИ» (оранжевый заголовок):
   - Для каждого конфликтного параметра: нумерованный заголовок + таблица
   - В таблице: `<tr style='background:#e6ffe6;'>` для выбранного (✔ зелёным), остальные серым
   - Используется `source_display()` для полной ссылки на источник
   - Если `conflict_values` пуст: текстовое примечание из `ev.note`

2. **Низкая уверенность** (`confidence == "low"`) → текст: `"{label} -- считан с низким качеством, требует проверки."`

3. **Пропуски** (`ev is None`) → `missing_param_note(label)`: `"{label} -- в документации не указан. Запросить у вендора."`

4. **Дополнительные примечания** (`extra_notes`) → без дублей с уже добавленными

Нумерация: `note_num` начинается с 1 и продолжается через все категории. Остальные примечания (2-4) выводятся через `<ol start='{note_num}'>` для непрерывной нумерации.

---

## 10. КАНОНИЧЕСКАЯ ЛЕКСИКА (output/canonical.py)

### 10.1. source_display()

```python
def source_display(file, doc_type, page, section, quote, confidence) -> str:
```

Формат: `"{file} ({doc_type}), стр. {page}, разд. <<{section}>>, <<{quote}>>"`

- Части соединяются через `", "`
- Если `confidence == "low"`: оборачивается в `"WARNING [{...}]"` (символ предупреждения)
- Если пустой результат: возвращает `"--"` (тире)

### 10.2. Канонические фразы

```python
def missing_param_note(label: str) -> str:
    return f"{label} -- в документации не указан. Запросить у вендора."

def conflict_note(label: str, values: str) -> str:
    return f"{label} -- расхождение: {values}"

def reference_note(label: str, basis: str) -> str:
    return f"{label} -- принят справочно ({basis})."

def low_quality_note(label: str) -> str:
    return f"{label} -- считан с чертежа низкого разрешения, требует проверки."
```

### 10.3. status_display()

```python
# Маппинг статусов:
"нет данных"    -> "нет данных"
"не требуется"  -> "не требуется"
"справочно"     -> "[справочно]"
"конфликт"      -> "WARNING [КОНФЛИКТ]"
"неоднозначно"  -> "WARNING [НЕОДНОЗНАЧНО]"
# Если есть note: "{status} -- {note}"
```

---

## 11. ГРАФИЧЕСКИЙ ИНТЕРФЕЙС

### 11.1. MainWindow (gui/main_window.py)

**Класс:** `MainWindow(QMainWindow)`

**Параметры окна:**
- Заголовок: `"Factum - Анализ паспортов оборудования"`
- Минимальный размер: `900 x 700`
- Drag-and-drop: включён (`setAcceptDrops(True)`)

**Иерархия виджетов:**

```
QVBoxLayout (main)
|
+-- QHBoxLayout (top)
|   +-- QPushButton "Выбрать файл(ы)"
|   +-- QPushButton "Выбрать папку"
|   +-- QPushButton "Очистить"
|   +-- Stretch
|
+-- QLabel "Загруженные документы:"
+-- QListWidget (min 120px, max 200px)
|
+-- QHBoxLayout (action)
|   +-- QPushButton "Анализировать" (min height 40, bold 14px, изначально disabled)
|   +-- QPushButton "Отмена" (min height 40, изначально скрыт)
|
+-- QProgressBar (изначально скрыт)
+-- QLabel (прогресс, color: #555, font-size: 10pt, изначально скрыт)
|
+-- QSplitter (Vertical, sizes [150, 300])
|   +-- QTextEdit (лог, readonly, max height 150px)
|   +-- QTextBrowser (превью)
|
+-- QHBoxLayout (bottom)
    +-- QPushButton "Сохранить DOCX" (disabled)
    +-- QPushButton "Открыть в Word" (disabled)
    +-- Stretch
    +-- QLabel (статус)
```

**Формат элемента списка файлов:**
`"{name}  ({format_label}, {size_display})"`

**Расчёт прогресса (6 этапов):**
```python
stage_weight = 100 / 6  # ~16.7% на этап
overall = int((stage - 1) * stage_weight + (current / total) * stage_weight)
progress_bar.setValue(min(overall, 100))
```

Текст прогресса: `"Этап {stage}/6: {message}"`

**Состояния UI:**
- Перед анализом: btn_analyze=enabled, btn_cancel=hidden, progress=hidden
- Во время анализа: btn_analyze=disabled, btn_cancel=visible+enabled, progress=visible
- После успеха: btn_analyze=enabled, btn_cancel=hidden, btn_save/btn_open=enabled, status зелёный bold
- После ошибки: btn_analyze=enabled, status красный

**Кнопка "Анализировать":**
1. Проверяет наличие файлов и API-ключа (при отсутствии ключа — `QMessageBox.warning` с текстом: `"Укажите API ключ Google Gemini в файле конфигурации\n(~/.factum/config.json, поле \"api_key\")."`)
2. Показывает `QFileDialog.getSaveFileName()` (по умолчанию `"Карточка_оборудования.docx"`)
3. Если пользователь отменил — возврат
4. Создаёт `PipelineWorker(self.files, Path(save_path))` и запускает

**Кнопка "Сохранить DOCX" (_on_save):**
1. Если `last_output_path` не задан или файл не существует — предупреждение
2. Показывает `QFileDialog.getSaveFileName()` для выбора нового пути
3. Если новый путь отличается от текущего: `shutil.copy2(str(src), save_path)`
4. Обновляет `last_output_path`, показывает `QMessageBox.information()`

**Drag & Drop:**
- `dragEnterEvent`: проверяет `mimeData().hasUrls()`, принимает
- `dropEvent`: для каждого URL -> Path -> `_add_files_from_path()`

**Кнопка "Открыть в Word":**
- `os.startfile(self.last_output_path)`

### 11.2. SettingsDialog (gui/settings_dialog.py)

> **Примечание:** Диалог настроек сохранён в файле `gui/settings_dialog.py`, но **не доступен из UI** — кнопка «Настройки» удалена. API ключ настраивается через файл `~/.factum/config.json`. Код диалога сохранён для возможного будущего использования.

**Класс:** `SettingsDialog(QDialog)`
- Заголовок: `"Настройки"`, minWidth=500
- Импорт: `from config import load_config, save_config, FIXED_MODEL`

**Группа "Google Gemini API":**
- API ключ: `QLineEdit`, EchoMode.Password, placeholder `"Вставьте API ключ из Google AI Studio"`
- Модель: `QLabel(f"<b>{FIXED_MODEL}</b>")` (нередактируемая — выбор модели убран из интерфейса)

**Группа "Обработка документов":**
- Размер чанка: `QSpinBox`, range 3-20, default 7, suffix " стр."
- Подсказка: `QLabel`, серый 9pt: `"Меньше = точнее извлечение, но больше API-запросов.\nРекомендуется: 5--10 страниц."`

**Кнопки:** "Сохранить" + "Отмена"

**Сохранение (_save):** Сохраняет только `api_key` и `chunk_size` → `save_config(config)` → `accept()`. Модель НЕ сохраняется (используется `FIXED_MODEL`).

### 11.3. PipelineWorker (worker.py)

**Класс:** `PipelineWorker(QThread)` — 6-этапный pipeline обработки в фоновом потоке.

**Импорт:** `from config import load_config, FIXED_MODEL`

**Сигналы:**
```python
progress = pyqtSignal(int, int, int, str)  # (stage, current, total, message)
finished = pyqtSignal(bool, str, str)      # (success, output_path, error)
log = pyqtSignal(str)                      # (message)
preview_ready = pyqtSignal(str)            # (html)
```

**Атрибуты:**
- `files: list[ScannedFile]`
- `output_path: Path`
- `_is_cancelled: bool = False`

**Метод `cancel()`:** устанавливает `_is_cancelled = True`

**Метод `_run_pipeline()`:** выполняет 6 этапов (см. раздел 5), между каждым проверяет `_is_cancelled`.

Конфигурация:
```python
model = FIXED_MODEL
chunk_size = config.get("chunk_size", 7)
overlap = config.get("overlap", 2)
```

**Вспомогательные функции (модульные, вне класса):**
- `_get_first_chunks(chunks)` — первый чанк каждого уникального файла
- `_format_context(ctx: dict)` — dict контекста → текст для промпта
- `_indent_text(text, prefix="    ")` — отступ каждой строки (для лога)
- `_resolved_to_json(resolved)` — resolved → JSON для верификации
- `_generate_html_preview(resolved, notes)` — формирование HTML-превью
- `_html_conflict_value(ev)` — конфликтное значение (✔/✖)
- `_html_notes_section(html, resolved, extra_notes)` — секция ПРИМЕЧАНИЯ

**Логирование этапов:**
- Этап 1: `"Этап 1/6: Подготовка. Файлов: {N}, чанк: {M} стр., перекрытие: {K} стр."`
- Этап 2: `"Этап 2/6: Определение типа и подсистем оборудования"`
  - Успех: `"  Контекст определён:\n{indented_context}"`
  - Неудача: `"  ⚠ Контекст не определён, продолжаем без него"`
- Этап 3: `"Этап 3/6: Извлечение [{i}/{total}] {file}, {pages}"`
  - Успех: `"  Найдено параметров: {N}"`
  - Ошибка: `"  ОШИБКА: {client.last_error}"`
- Этап 4: `"Этап 4/6: Агрегация данных из всех чанков"` → `"  Найдено: {N}, пропущено: {M}, предупреждений: {K}"`
- Этап 5: `"Этап 5/6: Верификация -- проверка полноты и конфликтов"` → `"  Верификация завершена. Дополнительных примечаний: {N}"`
- Этап 6: `"Этап 6/6: Генерация DOCX-карточки"` → `"Карточка сохранена: {path}"`

---

## 12. ТОЧКИ ВХОДА И СКРИПТЫ ЗАПУСКА

### 12.1. main.py

```python
import sys, logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Factum")
    app.setOrganizationName("Factum")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

### 12.2. run_console.py

Запуск через `python.exe` (не `pythonw.exe`) с ручным скрытием консоли:

```python
import sys, os, ctypes, traceback

# 1. Скрыть консольное окно
hwnd = ctypes.windll.kernel32.GetConsoleWindow()
if hwnd: ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE

# 2. Добавить папку проекта в sys.path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# 3. Принять user site-packages как argv[1] (из .bat)
if len(sys.argv) > 1:
    user_site = sys.argv[1]
    if user_site not in sys.path:
        sys.path.insert(0, user_site)

# 4. Запустить GUI (QApplication получает sys.argv[:1] без лишних аргументов)
try:
    logging.basicConfig(...)
    app = QApplication(sys.argv[:1])
    app.setApplicationName("Factum")
    app.setOrganizationName("Factum")
    ...
except Exception:
    # Показать консоль: ShowWindow(hwnd, 5)  # SW_SHOW
    # Записать error_log.txt: "Factum — ошибка запуска" + Python path, argv, sys.path, traceback
    # Открыть error_log.txt через os.startfile()
```

### 12.3. Factum.bat

```bat
@echo off
cd /d "%~dp0"
start "" /min C:\Python314\python.exe run_console.py "%APPDATA%\Python\Python314\site-packages"
```

### 12.4. install.bat

```bat
@echo off
echo ============================================
echo   Factum — установка библиотек
echo   (требуются права администратора)
echo ============================================
echo.

C:\Python314\python.exe -m pip install --force-reinstall PyQt6 pydantic google-genai pint python-docx PyMuPDF charset-normalizer

echo.
if %errorlevel% equ 0 (
    echo ============================================
    echo   Установка завершена успешно!
    echo   Теперь запустите Factum.bat
    echo ============================================
) else (
    echo ============================================
    echo   ОШИБКА при установке.
    echo   Попробуйте запустить этот файл
    echo   от имени администратора:
    echo   Правый клик - Запуск от имени администратора
    echo ============================================
)
echo.
pause
```

> **ВАЖНО:** Флаг `--force-reinstall` без `--user` — устанавливает в системный Python (`C:\Python314\Lib\site-packages`), минуя проблему с кириллическими путями пользователя.

### 12.5. Сборка standalone EXE и инсталлятора

Проект поддерживает два способа распространения:

1. **Standalone EXE** (`Factum.exe`) — один файл ~96 МБ, не требует установленного Python
2. **Инсталлятор** (`Factum_Setup_2.0.exe`) — устанавливает исходники + bat-лаунчер, требует Python 3.14

#### 12.5.1. PyInstaller (standalone EXE)

**Конфигурация:** `installer/factum.spec`

| Параметр | Значение |
|----------|----------|
| Точка входа | `main.py` |
| Имя EXE | `Factum` |
| Иконка | `factum.ico` |
| Режим | GUI (`console=False`) |
| Сжатие | UPX включён |
| Результат | `installer/dist/Factum.exe` |

**Hidden imports** (54 модуля): все модули проекта (`config`, `worker`, `scanner.*`, `chunking.*`, `gemini.*`, `processing.*`, `output.*`, `gui.*`), зависимости Google Gemini API (`google.genai.*`, `google.auth.*`), Pydantic v2, PyMuPDF (`fitz`), python-docx (`docx.*`, `lxml.*`), charset-normalizer, pint, PyQt6.

**Excluded** (для уменьшения размера): `tkinter`, `unittest`, `test`, `xmlrpc`, `multiprocessing`, `lib2to3`.

**Сборка:**

```
cd installer
C:\Python314\python.exe -m PyInstaller --clean --noconfirm factum.spec
```

Или через `build.bat`, который дополнительно проверяет наличие Python 3.14 и PyInstaller.

#### 12.5.2. Inno Setup (инсталлятор)

**Конфигурация:** `installer/factum.iss`

| Параметр | Значение |
|----------|----------|
| AppName | Factum |
| AppVersion | 2.0 |
| AppId | `{B7E3F2A1-5C4D-4E6F-8A9B-1D2E3F4A5B6C}` |
| Мин. Windows | 10.0 |
| Архитектура | x64 |
| Привилегии | Lowest (без админа) |
| Лицензия | `installer/LICENSE.txt` |
| Результат | `installer/Output/Factum_Setup_2.0.exe` |

Инсталлятор копирует все .py-модули, bat-лаунчер, иконку и install_deps.bat. Создаёт ярлыки в меню Пуск и опционально на рабочем столе. Проверяет наличие Python 3.14 при установке.

**Сборка:** Открыть `factum.iss` в Inno Setup Compiler → Build → Compile (Ctrl+F9).

#### 12.5.3. Артефакты сборки (не в git)

```
installer/
├── build/factum/    # Временные файлы PyInstaller (автогенерация)
├── dist/Factum.exe  # Standalone EXE (автогенерация, ~96 МБ)
└── Output/          # Инсталлятор Inno Setup (автогенерация)
```

Все артефакты исключены из git через `.gitignore`.

---

## 13. ИЗВЕСТНЫЕ ПРОБЛЕМЫ И ОБХОДНЫЕ ПУТИ

### 13.1. response_schema слишком сложная для Gemini

**Проблема:** `ChunkExtraction` с 44 nullable полями и вложенными моделями вызывает `400 INVALID_ARGUMENT: too many states` при использовании `response_schema` в Gemini API.

**Решение:** Использовать ТОЛЬКО `response_mime_type="application/json"` БЕЗ `response_schema`. Формат JSON задаётся в промпте, валидация через Pydantic.

### 13.2. Gemini возвращает список вместо словаря

**Проблема:** Иногда Gemini возвращает `[{param_id: "A.1", value: ...}]` вместо `{a1_name: ...}`.

**Решение:** Функция `_convert_list_to_dict()` с маппингом `_PARAM_ID_TO_FIELD`.

### 13.3. Gemini не заполняет file и doc_type в source

**Проблема:** Поля `source.file` и `source.doc_type` часто пустые в ответе.

**Решение:**
1. `SourceRef.file` и `doc_type` имеют `default=""`
2. В `extract_from_chunk()`: заполняются из метаданных чанка (`chunk.source_file`, `chunk.source_type`)
3. В `aggregate_extractions()`: перезаписываются из метаданных чанка

### 13.4. Raw string с Unicode в Python 3.14

**Проблема:** `r'\1\u2013\2'` в replacement для `re.sub()` вызывает `re.error: bad escape \u` в Python 3.12+.

**Решение:** Использовать обычную строку `'\\1\u2013\\2'` — `\\1` = обратная ссылка, `\u2013` = символ Unicode en-dash.

### 13.5. Кириллический путь пользователя в Windows

**Проблема:** `pip install --user` устанавливает в `%APPDATA%\Python\Python314\site-packages`. Если имя пользователя содержит кириллицу (например, `C:\Users\Факел\...`), Python не может найти этот путь при запуске из .bat (`os.path.isdir()` возвращает False).

**Решение:**
1. `install.bat` устанавливает в системный Python `C:\Python314\Lib\site-packages` (без кириллицы)
2. `Factum.bat` передаёт путь `%APPDATA%\...` как аргумент (Windows раскрывает переменную корректно)
3. `run_console.py` добавляет этот путь в `sys.path`

### 13.6. JSON обёрнут в markdown-блок

**Проблема:** Gemini иногда оборачивает JSON в ` ```json ... ``` `.

**Решение:** Fallback-парсинг: удаление ` ```json ` и ` ``` ` обёрток перед `json.loads()`.

### 13.7. Pydantic падает при null от Gemini (string_type validation)

**Проблема:** Gemini возвращает `null` для строковых полей (например, `"section": null`). Pydantic `default=""` не срабатывает, т.к. ключ ПРИСУТСТВУЕТ в JSON со значением `None`. Результат: `ValidationError: Input should be a valid string [type=string_type]`.

**Решение:** `@model_validator(mode="before")` в `SourceRef` и `ExtractedValue`:
```python
@model_validator(mode="before")
@classmethod
def _nulls_to_defaults(cls, data):
    if isinstance(data, dict):
        for key in ("file", "doc_type", "section", "quote", "confidence"):
            if key in data and data[key] is None:
                data[key] = ""
    return data
```

Двойная защита: 1) `default=""` — если поле отсутствует; 2) `model_validator` — если поле = `null`.

### 13.8. Overlap-дубли (ложные конфликты)

**Проблема:** Overlap (перекрытие чанков) приводит к тому, что Gemini обрабатывает одни и те же страницы дважды. Результат: идентичные значения с близких страниц одного файла попадают в агрегацию как «разные» извлечения, создавая ложные конфликты.

**Решение:** `_deduplicate_overlaps(values, overlap=2)` в `resolve_aggregated()` — если два значения из одного файла и их страницы близки (разница ≤ overlap):
- При точном совпадении — отбрасывает дубль (оставляется первое).
- При OCR-варианте (значения одной длины, 1-2 различия из `_OCR_DIGIT_PAIRS`: 3↔5, 6↔0 и т.д.) — оставляет значение с более высоким confidence, понижает confidence до `"low"`, записывает отброшенный вариант в `note`.

---

## 14. ЗАВИСИМОСТИ (requirements.txt)

```
google-genai>=1.0
PyQt6>=6.6
python-docx>=1.0
PyMuPDF>=1.24
pint>=0.24
pydantic>=2.0
charset-normalizer>=3.0
```

---

## 15. PLACEHOLDER-МОДУЛИ

Файлы, зарезервированные для будущего расширения (содержат только комментарий):

| Файл | Комментарий |
|------|------------|
| `chunking/image_chunker.py` | Вся логика реализована в chunk_manager.py |
| `gui/file_list_widget.py` | Логика интегрирована в gui/main_window.py (QListWidget) |
| `gui/progress_widget.py` | Логика интегрирована в gui/main_window.py (QProgressBar + QLabel) |
| `gui/preview_widget.py` | Логика интегрирована в gui/main_window.py (QTextBrowser) |

Все `__init__.py` файлы пустые (только маркер пакета).

---

## ПРИЛОЖЕНИЕ А. ПОЛНАЯ ТАБЛИЦА ПАРАМЕТРОВ

| Код | Имя поля | Название параметра | Группа |
|-----|----------|-------------------|--------|
| A.1 | a1_name | Наименование и назначение | A. Идентификация |
| A.2 | a2_model | Модель / полный артикул | A. Идентификация |
| A.3 | a3_manufacturer | Производитель, страна | A. Идентификация |
| A.4 | a4_year_serial | Год выпуска и серийный номер | A. Идентификация |
| B.1 | b1_dimensions | Габариты (Д*Ш*В, мм) | B. Габариты и логистика |
| B.2 | b2_opening | Минимальный монтажный проём | B. Габариты и логистика |
| B.3 | b3_weight | Масса нетто / с жидкостями | B. Габариты и логистика |
| B.4 | b4_heaviest_part | Масса тяжелейшей части | B. Габариты и логистика |
| B.5 | b5_rigging | Точки строповки и ЦТ | B. Габариты и логистика |
| C.1 | c1_installation | Тип установки | C. Строительные требования |
| C.2 | c2_foundation | Размеры фундамента | C. Строительные требования |
| C.3 | c3_pits | Приямки / подиум | C. Строительные требования |
| C.4 | c4_loads | Статические/динамические нагрузки | C. Строительные требования |
| C.5 | c5_service_zone | Зона обслуживания | C. Строительные требования |
| C.6 | c6_floor | Требования к полу | C. Строительные требования |
| C.7 | c7_construction | Требования к конструкциям | C. Строительные требования |
| D.1 | d1_power | P_уст и P_потр (кВт) | D. Электроснабжение |
| D.2 | d2_voltage | Напряжение, фазность, частота, ток | D. Электроснабжение |
| D.3 | d3_reliability | Категория надёжности, ИБП | D. Электроснабжение |
| D.4 | d4_startup | Тип пуска, cos phi, Ки | D. Электроснабжение |
| D.5 | d5_heat | Тепловыделения (кВт) | D. Электроснабжение |
| D.6 | d6_protection | Степень защиты (IP), класс зоны | D. Электроснабжение |
| D.7 | d7_grounding | Тип заземления | D. Электроснабжение |
| D.8 | d8_cable_entry | Точка ввода кабеля | D. Электроснабжение |
| E.1 | e1_pressure | Давление на входе (МПа) | E. Сжатый воздух |
| E.2 | e2_flow | Расход (м3/ч или н.л/мин) | E. Сжатый воздух |
| E.3 | e3_quality | Качество среды | E. Сжатый воздух |
| E.4 | e4_connection | Точка подключения | E. Сжатый воздух |
| F.1 | f1_purpose | Назначение воды | F. Водоснабжение |
| F.2 | f2_quality | Требования к качеству воды | F. Водоснабжение |
| F.3 | f3_flow | Расход, давление, температура воды | F. Водоснабжение |
| F.4 | f4_connection | Точка подключения воды | F. Водоснабжение |
| F.5 | f5_drainage | Канализация | F. Водоснабжение |
| F.6 | f6_drain_point | Точка слива | F. Водоснабжение |
| F.7 | f7_coolant | СОЖ | F. Водоснабжение |
| F.8 | f8_periodicity | Периодичность потребления | F. Водоснабжение |
| G.1 | g1_exhaust | Локальные отсосы | G. Вентиляция и экология |
| G.2 | g2_emissions | Состав выбросов | G. Вентиляция и экология |
| G.3 | g3_noise | Уровень шума (дБА) | G. Вентиляция и экология |
| G.4 | g4_vibration | Вибрация | G. Вентиляция и экология |
| H.1 | h1_it | IT-инфраструктура | H. Автоматизация |
| H.2 | h2_safety | Интеграция в систему безопасности | H. Автоматизация |
| H.3 | h3_signaling | Световая/звуковая сигнализация | H. Автоматизация |
| H.4 | h4_climate | Микроклимат в зоне установки | H. Автоматизация |

---

## ПРИЛОЖЕНИЕ Б. ПОЛНАЯ КАРТА MIME-ТИПОВ

| Расширение | MIME-тип | Формат |
|------------|----------|--------|
| pdf | application/pdf | PDF |
| jpg | image/jpeg | Изображение |
| jpeg | image/jpeg | Изображение |
| png | image/png | Изображение |
| bmp | image/bmp | Изображение |
| tiff | image/tiff | Изображение |
| tif | image/tiff | Изображение |
| docx | application/vnd.openxmlformats-officedocument.wordprocessingml.document | DOCX |
| doc | application/msword | DOC |
| xlsx | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | Excel |
| xls | application/vnd.ms-excel | Excel |
| csv | text/csv | CSV |
| txt | text/plain | Текст |

---

## ПРИЛОЖЕНИЕ В. ИЕРАРХИЯ ИСТОЧНИКОВ И ПРИОРИТЕТЫ

### Приоритет типов документов (меньше = выше)

| Приоритет | Тип документа | Описание |
|-----------|--------------|----------|
| 0 | Паспорт | Наивысший приоритет (основной документ) |
| 1 | Каталог | Каталожные данные производителя |
| 2 | Руководство | Руководство по эксплуатации |
| 3 | Чертёж | Инженерный чертёж |
| 4 | Документ | Любой неклассифицированный документ |

### Приоритет уверенности (меньше = выше)

| Приоритет | Уровень | Описание |
|-----------|---------|----------|
| 0 | high | Чёткое значение, хорошо читается |
| 1 | medium | Среднее качество скана/текста |
| 2 | low | Плохо читается, требует проверки |

При конфликте: сортировка по `(приоритет_типа + штраф, приоритет_уверенности)`, берётся первый. Штраф: `+2` к приоритету типа для `confidence == "low"` (т.е. Паспорт low = 0+2 = 2 проигрывает Каталогу high = 1+0 = 1).

---

## ПРИЛОЖЕНИЕ Г. REGEX-ПАТТЕРНЫ КЛАССИФИКАЦИИ ДОКУМЕНТОВ

```python
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
```

**Правила классификации:**
- Поиск по `path.stem.lower()` с `re.IGNORECASE`
- Изображения без совпадения -> `"Чертёж"`
- Остальные файлы без совпадения -> `"Документ"`

---

*Конец технического задания.*
