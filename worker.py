"""QThread-воркер для 6-этапного pipeline обработки документов."""

import json
import logging
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from config import load_config, FIXED_MODEL
from scanner.folder_scanner import ScannedFile, scan_path
from chunking.chunk_manager import create_chunks, Chunk
from gemini.client import GeminiClient
from gemini.schema import ChunkExtraction, CHECKLIST_FIELDS
from processing.aggregator import aggregate_extractions, resolve_aggregated, apply_verification
from processing.validator import validate_completeness
from output.docx_generator import generate_card

logger = logging.getLogger(__name__)


class PipelineWorker(QThread):
    """6-этапный pipeline обработки в фоновом потоке.

    Этапы:
        1. Подготовка чанков
        2. Определение контекста оборудования (NEW)
        3. Извлечение параметров
        4. Агрегация
        5. Верификация
        6. Формирование DOCX

    Signals:
        progress(stage, current, total, message):
            stage: 1-6, current: текущий шаг, total: всего шагов, message: описание
        finished(success, output_path, error_message):
            Результат обработки
        log(message):
            Сообщение для лога
    """

    progress = pyqtSignal(int, int, int, str)
    finished = pyqtSignal(bool, str, str)
    log = pyqtSignal(str)
    preview_ready = pyqtSignal(str)  # HTML-превью карточки

    def __init__(self, files: list[ScannedFile], output_path: Path):
        super().__init__()
        self.files = files
        self.output_path = output_path
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            self._run_pipeline()
        except Exception as e:
            logger.exception("Ошибка pipeline")
            self.finished.emit(False, "", str(e))

    def _run_pipeline(self):
        config = load_config()
        api_key = config.get("api_key", "")
        model = FIXED_MODEL
        chunk_size = config.get("chunk_size", 7)
        overlap = config.get("overlap", 2)

        if not api_key:
            self.finished.emit(False, "", "API ключ не настроен. Откройте Настройки.")
            return

        client = GeminiClient(api_key=api_key, model=model)

        # === ЭТАП 1: ПОДГОТОВКА ЧАНКОВ ===
        self.progress.emit(1, 0, 1, "Подготовка чанков...")
        self.log.emit(f"Этап 1/6: Подготовка. Файлов: {len(self.files)}, чанк: {chunk_size} стр., перекрытие: {overlap} стр.")

        chunks = create_chunks(self.files, chunk_size=chunk_size, overlap=overlap)
        self.log.emit(f"  Создано чанков: {len(chunks)}")

        if self._is_cancelled:
            self.finished.emit(False, "", "Отменено")
            return

        # === ЭТАП 2: ОПРЕДЕЛЕНИЕ КОНТЕКСТА ОБОРУДОВАНИЯ ===
        self.progress.emit(2, 0, 1, "Определение контекста оборудования...")
        self.log.emit("Этап 2/6: Определение типа и подсистем оборудования")

        first_chunks = _get_first_chunks(chunks)
        self.log.emit(f"  Анализ первых чанков: {len(first_chunks)} файл(ов)")

        ctx_dict = client.determine_equipment_context(first_chunks)
        equipment_context = ""
        if ctx_dict:
            equipment_context = _format_context(ctx_dict)
            self.log.emit(f"  Контекст определён:\n{_indent_text(equipment_context)}")
        else:
            self.log.emit("  ⚠ Контекст не определён, продолжаем без него")

        self.progress.emit(2, 1, 1, "Контекст определён")

        if self._is_cancelled:
            self.finished.emit(False, "", "Отменено")
            return

        # === ЭТАП 3: ИЗВЛЕЧЕНИЕ ПАРАМЕТРОВ ===
        total_chunks = len(chunks)
        extractions: list[tuple[Chunk, ChunkExtraction]] = []

        for i, chunk in enumerate(chunks):
            if self._is_cancelled:
                self.finished.emit(False, "", "Отменено")
                return

            self.progress.emit(3, i + 1, total_chunks,
                               f"Извлечение: {chunk.source_file}, {chunk.page_range_display}")
            self.log.emit(
                f"Этап 3/6: Извлечение [{i + 1}/{total_chunks}] "
                f"{chunk.source_file}, {chunk.page_range_display}"
            )

            result = client.extract_from_chunk(chunk, equipment_context=equipment_context)
            if result is not None:
                extractions.append((chunk, result))
                # Подсчитать найденные параметры
                found = sum(1 for f, _ in CHECKLIST_FIELDS if getattr(result, f) is not None)
                self.log.emit(f"  Найдено параметров: {found}")
            else:
                error_detail = client.last_error or "неизвестная ошибка"
                self.log.emit(f"  ОШИБКА: {error_detail}")

        if not extractions:
            error_detail = client.last_error or "неизвестная ошибка"
            self.finished.emit(False, "", f"Не удалось извлечь данные: {error_detail}")
            return

        # === ЭТАП 4: АГРЕГАЦИЯ ===
        self.progress.emit(4, 0, 1, "Агрегация данных...")
        self.log.emit("Этап 4/6: Агрегация данных из всех чанков")

        aggregated = aggregate_extractions(extractions)
        resolved = resolve_aggregated(aggregated)

        present, missing, warnings = validate_completeness(resolved)
        self.log.emit(f"  Найдено: {len(present)}, пропущено: {len(missing)}, предупреждений: {len(warnings)}")

        if self._is_cancelled:
            self.finished.emit(False, "", "Отменено")
            return

        # === ЭТАП 5: ВЕРИФИКАЦИЯ ===
        self.progress.emit(5, 0, 1, "Верификация данных...")
        self.log.emit("Этап 5/6: Верификация — проверка полноты и конфликтов")

        # Формируем JSON для верификации
        aggregated_json = _resolved_to_json(resolved)
        verification = client.verify_extraction(
            aggregated_json, chunks, equipment_context=equipment_context
        )

        notes = []
        if verification:
            resolved, notes = apply_verification(resolved, verification)
            self.log.emit(f"  Верификация завершена. Дополнительных примечаний: {len(notes)}")
        else:
            self.log.emit("  Верификация не удалась, используем данные без доп. проверки")

        if self._is_cancelled:
            self.finished.emit(False, "", "Отменено")
            return

        # === ЭТАП 6: ФОРМИРОВАНИЕ DOCX ===
        self.progress.emit(6, 0, 1, "Формирование DOCX...")
        self.log.emit("Этап 6/6: Генерация DOCX-карточки")

        doc = generate_card(
            resolved=resolved,
            notes=notes,
            output_path=self.output_path,
        )

        # Генерация HTML-превью
        html = _generate_html_preview(resolved, notes)
        self.preview_ready.emit(html)

        self.log.emit(f"Карточка сохранена: {self.output_path}")
        self.finished.emit(True, str(self.output_path), "")


def _get_first_chunks(chunks: list[Chunk]) -> list[Chunk]:
    """Получить первый чанк каждого уникального файла."""
    seen: set[str] = set()
    result: list[Chunk] = []
    for c in chunks:
        if c.source_file not in seen:
            seen.add(c.source_file)
            result.append(c)
    return result


def _format_context(ctx: dict) -> str:
    """Преобразовать dict контекста оборудования в текст для промпта."""
    lines = []
    if ctx.get("equipment_type"):
        lines.append(f"Тип: {ctx['equipment_type']}")
    if ctx.get("equipment_name"):
        lines.append(f"Наименование: {ctx['equipment_name']}")
    if ctx.get("purpose"):
        lines.append(f"Назначение: {ctx['purpose']}")
    if ctx.get("subsystems"):
        subs = ctx["subsystems"]
        if isinstance(subs, list):
            lines.append(f"Подсистемы: {', '.join(subs)}")
        else:
            lines.append(f"Подсистемы: {subs}")
    if ctx.get("power_class"):
        lines.append(f"Класс мощности: {ctx['power_class']}")
    if ctx.get("supply_type"):
        lines.append(f"Тип питания: {ctx['supply_type']}")
    if ctx.get("notes"):
        lines.append(f"Примечания: {ctx['notes']}")
    return "\n".join(lines)


def _indent_text(text: str, prefix: str = "    ") -> str:
    """Добавить отступ к каждой строке текста (для лога)."""
    return "\n".join(f"{prefix}{line}" for line in text.split("\n"))


def _resolved_to_json(resolved: dict) -> str:
    """Преобразовать resolved в JSON для верификации."""
    data = {}
    for field_name, label in CHECKLIST_FIELDS:
        ev = resolved.get(field_name)
        if ev is not None:
            data[field_name] = {
                "label": label,
                "value": ev.value,
                "source_file": ev.source.file,
                "source_type": ev.source.doc_type,
                "page": ev.source.page,
                "section": ev.source.section,
                "quote": ev.source.quote,
            }
        else:
            data[field_name] = {"label": label, "value": None}
    return json.dumps(data, ensure_ascii=False, indent=2)


def _generate_html_preview(resolved: dict, notes: list[str]) -> str:
    """Сгенерировать HTML-превью для отображения в GUI."""
    from gemini.schema import SECTION_GROUPS
    from output.canonical import source_display, missing_param_note
    from output.formatter import format_value

    html = ["<html><body style='font-family: Arial; font-size: 10pt;'>"]

    model = ""
    manufacturer = ""
    ev_model = resolved.get("a2_model")
    ev_manuf = resolved.get("a3_manufacturer")
    if ev_model:
        model = ev_model.value
    if ev_manuf:
        manufacturer = ev_manuf.value

    html.append(f"<h2 align='center'>КАРТОЧКА ОБОРУДОВАНИЯ: {model} — {manufacturer}</h2>")

    for group_key in ["A", "B", "C", "D", "E", "F", "G", "H"]:
        group_title, field_names = SECTION_GROUPS[group_key]
        html.append(f"<h3>{group_title}</h3>")
        html.append("<table border='1' cellpadding='4' cellspacing='0' width='100%'>")

        if group_key == "A":
            html.append("<tr><th>Параметр</th><th>Значение</th></tr>")
        else:
            html.append("<tr><th>Параметр</th><th>Значение</th><th>Источник</th></tr>")

        for field_name in field_names:
            label = dict(CHECKLIST_FIELDS).get(field_name, field_name)
            ev = resolved.get(field_name)

            if ev is None:
                val = "<i>нет данных</i>"
                src = "—"
            elif ev.status and "конфликт" in ev.status.lower():
                # Конфликтное значение — структурированное отображение
                val = _html_conflict_value(ev)
                src = source_display(
                    ev.source.file, ev.source.doc_type, ev.source.page,
                    ev.source.section, ev.source.quote, ev.source.confidence,
                )
            else:
                val = format_value(ev.value)
                if ev.status and ev.status.strip():
                    val += f" <span style='color:orange'>[{ev.status}]</span>"
                src = source_display(
                    ev.source.file, ev.source.doc_type, ev.source.page,
                    ev.source.section, ev.source.quote, ev.source.confidence,
                )

            if group_key == "A":
                html.append(f"<tr><td>{label}</td><td>{val}</td></tr>")
            else:
                html.append(f"<tr><td>{label}</td><td>{val}</td><td>{src}</td></tr>")

        html.append("</table>")

    # --- ПРИМЕЧАНИЯ ---
    _html_notes_section(html, resolved, notes)

    html.append("</body></html>")
    return "\n".join(html)


def _html_conflict_value(ev) -> str:
    """HTML-отображение конфликтного значения с цветовым выделением."""
    from output.formatter import format_value

    parts = []
    # Выбранное значение — зелёным
    parts.append(
        f"<b style='color:#008000;'>✔ {format_value(ev.value)}</b>"
        f" <span style='color:#c87800; font-size:8pt;'>[конфликт]</span>"
    )

    # Остальные варианты — серым
    if ev.conflict_values:
        for entry in ev.conflict_values:
            if entry.is_selected:
                continue
            src_text = entry.source.file
            if entry.source.doc_type:
                src_text += f", {entry.source.doc_type}"
            if entry.source.page:
                src_text += f", стр. {entry.source.page}"
            parts.append(
                f"<span style='color:#828282;'>✖ {format_value(entry.value)}</span>"
                f" <span style='color:#a0a0a0; font-size:7pt;'>({src_text})</span>"
            )

    return "<br>".join(parts)


def _html_notes_section(html: list, resolved: dict, extra_notes: list[str]):
    """Секция ПРИМЕЧАНИЯ в HTML-превью с структурированными конфликтами."""
    from gemini.schema import CHECKLIST_FIELDS as CK_FIELDS
    from output.canonical import source_display, missing_param_note
    from output.formatter import format_value

    conflict_notes = []
    other_notes = []

    # 1. Конфликты
    for field_name, label in CK_FIELDS:
        ev = resolved.get(field_name)
        if ev and ev.status and "конфликт" in ev.status.lower():
            conflict_notes.append((label, ev))

    # 2. Низкая уверенность
    for field_name, label in CK_FIELDS:
        ev = resolved.get(field_name)
        if ev and ev.source.confidence == "low":
            other_notes.append(f"{label} — считан с низким качеством, требует проверки.")

    # 3. Пропуски
    for field_name, label in CK_FIELDS:
        ev = resolved.get(field_name)
        if ev is None:
            other_notes.append(missing_param_note(label))

    # 4. Дополнительные примечания
    for note in extra_notes:
        if note not in other_notes:
            other_notes.append(note)

    has_content = conflict_notes or other_notes
    if not has_content:
        return

    html.append("<h3>ПРИМЕЧАНИЯ</h3>")
    note_num = 1

    # --- Конфликты ---
    if conflict_notes:
        html.append(
            "<p><b style='color:#c87800;'>⚠ РАСХОЖДЕНИЯ МЕЖДУ ИСТОЧНИКАМИ</b></p>"
        )
        for label, ev in conflict_notes:
            html.append(f"<p><b>{note_num}. {label}</b></p>")
            note_num += 1

            if ev.conflict_values:
                html.append(
                    "<table border='1' cellpadding='3' cellspacing='0' "
                    "style='margin-left:20px; margin-bottom:8px; width:95%;'>"
                )
                html.append("<tr><th>№</th><th>Значение</th><th>Источник</th></tr>")

                for idx, entry in enumerate(ev.conflict_values, 1):
                    marker = "✔" if entry.is_selected else str(idx)
                    src = source_display(
                        file=entry.source.file,
                        doc_type=entry.source.doc_type,
                        page=entry.source.page,
                        section=entry.source.section,
                        quote=entry.source.quote,
                        confidence=entry.source.confidence,
                    )

                    if entry.is_selected:
                        html.append(
                            f"<tr style='background:#e6ffe6;'>"
                            f"<td><b style='color:#008000;'>{marker}</b></td>"
                            f"<td><b style='color:#008000;'>{format_value(entry.value)}</b></td>"
                            f"<td>{src}</td></tr>"
                        )
                    else:
                        html.append(
                            f"<tr>"
                            f"<td>{marker}</td>"
                            f"<td style='color:#828282;'>{format_value(entry.value)}</td>"
                            f"<td>{src}</td></tr>"
                        )

                html.append("</table>")
            else:
                # Нет структурированных данных — текстовое примечание
                note_text = ev.note or "Расхождение между источниками."
                html.append(f"<p style='margin-left:20px;'>{note_text}</p>")

    # --- Остальные примечания ---
    if other_notes:
        html.append("<ol" + (f" start='{note_num}'" if note_num > 1 else "") + ">")
        for note in other_notes:
            html.append(f"<li>{note}</li>")
        html.append("</ol>")
