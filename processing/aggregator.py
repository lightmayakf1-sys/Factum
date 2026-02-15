"""Агрегация частичных извлечений из чанков в единую карточку."""

import logging
from gemini.schema import ChunkExtraction, ExtractedValue, ConflictEntry, SourceRef, CHECKLIST_FIELDS
from chunking.chunk_manager import Chunk
from processing.conflict_resolver import resolve_conflict

logger = logging.getLogger(__name__)


def aggregate_extractions(
    extractions: list[tuple[Chunk, ChunkExtraction]],
) -> dict[str, list[ExtractedValue]]:
    """Агрегировать извлечения из всех чанков.

    Args:
        extractions: Список пар (чанк, извлечение).

    Returns:
        dict: field_name -> список ExtractedValue (может быть несколько из разных чанков).
    """
    aggregated: dict[str, list[ExtractedValue]] = {
        field: [] for field, _ in CHECKLIST_FIELDS
    }

    for chunk, extraction in extractions:
        for field_name, label in CHECKLIST_FIELDS:
            value: ExtractedValue | None = getattr(extraction, field_name, None)
            if value is None:
                continue

            # Пересчитать номер страницы: page в чанке → page в оригинале
            if value.source.page is not None and chunk.page_start is not None:
                value.source.page = chunk.page_start + value.source.page - 1

            # Установить имя файла и тип из метаданных чанка
            value.source.file = chunk.source_file
            value.source.doc_type = chunk.source_type

            aggregated[field_name].append(value)

    return aggregated


def _deduplicate_overlaps(values: list[ExtractedValue], overlap: int = 2) -> list[ExtractedValue]:
    """Убрать дубли из перекрывающихся чанков одного файла.

    При overlap чанков одни и те же страницы обрабатываются Gemini дважды.
    Gemini недетерминистичен — может извлечь РАЗНЫЕ значения с одних страниц.
    Если два значения из одного файла и страницы близки (разница ≤ overlap) —
    это повторное извлечение, а не настоящий конфликт.
    Оставляем первое (из более раннего чанка — у него эта страница «основная»).
    """
    if len(values) <= 1:
        return values

    kept: list[ExtractedValue] = []
    for v in values:
        is_overlap_dup = False
        for existing in kept:
            # Условия overlap-дубля:
            # 1. Один и тот же файл
            # 2. Обе страницы известны
            # 3. Страницы близки (в пределах overlap)
            if (existing.source.file == v.source.file
                    and existing.source.file
                    and existing.source.page is not None
                    and v.source.page is not None
                    and abs(existing.source.page - v.source.page) <= overlap):
                is_overlap_dup = True
                logger.debug(
                    f"Overlap-дубль отброшен для {v.source.file}: "
                    f"{v.value!r} (стр.{v.source.page}) "
                    f"≈ {existing.value!r} (стр.{existing.source.page})"
                )
                break
        if not is_overlap_dup:
            kept.append(v)
    return kept


def resolve_aggregated(
    aggregated: dict[str, list[ExtractedValue]],
) -> dict[str, ExtractedValue | None]:
    """Разрешить конфликты и выбрать финальное значение для каждого параметра.

    Returns:
        dict: field_name -> одно финальное ExtractedValue или None.
    """
    result: dict[str, ExtractedValue | None] = {}
    notes: list[str] = []

    for field_name, label in CHECKLIST_FIELDS:
        values = aggregated.get(field_name, [])

        # Дедупликация overlap-дублей (из перекрывающихся чанков одного файла)
        values = _deduplicate_overlaps(values)

        if not values:
            result[field_name] = None
            continue

        if len(values) == 1:
            result[field_name] = values[0]
            continue

        # Несколько значений — проверяем конфликт
        unique_values = set(v.value.strip() for v in values)
        if len(unique_values) == 1:
            # Все одинаковые — берём с наивысшим приоритетом источника
            best = resolve_conflict(values)
            result[field_name] = best
        else:
            # Конфликт — разрешаем по иерархии, отмечаем
            best = resolve_conflict(values)
            # Собираем все конфликтующие значения
            entries = []
            for v in values:
                entries.append(ConflictEntry(
                    value=v.value,
                    source=v.source.model_copy(),
                    is_selected=(v.value.strip() == best.value.strip()
                                 and v.source.file == best.source.file),
                ))
            best.conflict_values = entries
            conflict_details = "; ".join(
                f"{v.value} ({v.source.file}, {v.source.doc_type})"
                for v in values
            )
            best.note = f"КОНФЛИКТ: {conflict_details}"
            best.status = "конфликт"
            result[field_name] = best
            notes.append(f"{label} — расхождение: {conflict_details}")
            logger.warning(f"Конфликт в {label}: {conflict_details}")

    return result


def apply_verification(
    resolved: dict[str, ExtractedValue | None],
    verification: dict | None,
) -> tuple[dict[str, ExtractedValue | None], list[str]]:
    """Применить результаты верификации к агрегированным данным.

    Returns:
        (обновлённые данные, список примечаний)
    """
    notes = []

    if verification is None:
        return resolved, notes

    # Добавить дополнительные значения
    for item in verification.get("additional_values", []):
        field = item.get("field", "")
        if field in resolved and resolved[field] is None:
            resolved[field] = ExtractedValue(
                value=item.get("value", ""),
                source=SourceRef(
                    file=item.get("file", ""),
                    doc_type="",
                    page=item.get("page"),
                    section=item.get("section", ""),
                    quote=item.get("quote", ""),
                    confidence="medium",
                ),
                status="[UPD] верификация",
            )

    # Собрать примечания о пропусках
    for item in verification.get("missing_params", []):
        field = item.get("field", "")
        suggestion = item.get("suggestion", "")
        label = dict(CHECKLIST_FIELDS).get(field, field)
        notes.append(f"{label} — в документации не указан. {suggestion}")

    # Собрать конфликты из верификации
    for item in verification.get("conflicts", []):
        field = item.get("field", "")
        values_str = ", ".join(item.get("values", []))
        label = dict(CHECKLIST_FIELDS).get(field, field)
        notes.append(f"{label} — расхождение: {values_str}")

    # Косвенные параметры
    for item in verification.get("indirect_params", []):
        field = item.get("field", "")
        reasoning = item.get("reasoning", "")
        suggested = item.get("suggested_value", "")
        label = dict(CHECKLIST_FIELDS).get(field, field)
        if field in resolved and resolved[field] is None:
            resolved[field] = ExtractedValue(
                value=suggested,
                source=SourceRef(
                    file="", doc_type="", page=None,
                    section="", quote="", confidence="low",
                ),
                status="[справочно: косвенный вывод]",
                note=reasoning,
            )
        notes.append(f"{label} — {reasoning}")

    return resolved, notes
