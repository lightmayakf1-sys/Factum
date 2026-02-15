"""Обёртка Gemini API: загрузка файлов, запросы с retry, structured output."""

import json
import time
import logging
from pathlib import Path

from google import genai
from google.genai import types

from gemini.schema import ChunkExtraction, CHECKLIST_FIELDS
from gemini.prompts import (
    CONTEXT_SYSTEM_PROMPT,
    EXTRACTION_SYSTEM_PROMPT,
    VERIFICATION_SYSTEM_PROMPT,
    make_context_prompt,
    make_extraction_prompt,
    make_verification_prompt,
)
from chunking.chunk_manager import Chunk

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_BASE = 5  # seconds

# Маппинг param_id → имя поля в ChunkExtraction (для fallback-конвертации)
_PARAM_ID_TO_FIELD = {}
for _field_name, _label in CHECKLIST_FIELDS:
    # "A.1. Наименование..." → "A.1"
    _param_id = _label.split(".")[0] + "." + _label.split(".")[1].split(" ")[0] if "." in _label else ""
    _param_id = _param_id.strip()
    _PARAM_ID_TO_FIELD[_param_id] = _field_name
    # Также без пробелов
    _PARAM_ID_TO_FIELD[_param_id.replace(" ", "")] = _field_name


def _convert_list_to_dict(raw_list: list) -> dict:
    """Конвертировать список [{param_id: 'A.1', value: ...}] в словарь {a1_name: ...}."""
    result = {}
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        param_id = item.get("param_id", "").strip()
        field_name = _PARAM_ID_TO_FIELD.get(param_id)
        if field_name:
            # Убираем param_id из объекта, оставляем value и source
            entry = {k: v for k, v in item.items() if k != "param_id"}
            result[field_name] = entry
        else:
            logger.warning(f"Неизвестный param_id: {param_id}")
    return result


class GeminiClient:
    """Клиент для работы с Gemini API."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.last_error: str = ""  # Последняя ошибка для отображения в GUI

    def determine_equipment_context(self, first_chunks: list[Chunk]) -> dict | None:
        """Определить контекст оборудования по первым чанкам каждого файла.

        Args:
            first_chunks: Первый чанк каждого уникального файла.

        Returns:
            dict с полями equipment_type, equipment_name, purpose,
            subsystems, power_class, supply_type, notes. Или None при ошибке.
        """
        parts = []
        file_names = []

        for chunk in first_chunks:
            file_names.append(chunk.source_file)
            if isinstance(chunk.data, str):
                parts.append(types.Part.from_text(
                    text=f"--- Файл: {chunk.source_file} ({chunk.source_type}) ---\n{chunk.data}"
                ))
            else:
                parts.append(types.Part.from_bytes(
                    data=chunk.data,
                    mime_type=chunk.mime_type,
                ))

        parts.append(types.Part.from_text(text=make_context_prompt(file_names)))

        return self._call_with_retry(
            system_prompt=CONTEXT_SYSTEM_PROMPT,
            parts=parts,
        )

    def extract_from_chunk(self, chunk: Chunk,
                           equipment_context: str = "") -> ChunkExtraction | None:
        """Извлечь параметры из одного чанка.

        Args:
            chunk: Чанк для обработки.
            equipment_context: Текстовый контекст оборудования (тип, подсистемы и т.д.)

        Returns:
            ChunkExtraction с извлечёнными параметрами, или None при ошибке.
        """
        user_prompt = make_extraction_prompt(
            source_file=chunk.source_file,
            source_type=chunk.source_type,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            equipment_context=equipment_context,
        )

        # Формируем содержимое запроса
        parts = []

        if isinstance(chunk.data, str):
            parts.append(types.Part.from_text(
                text=f"Содержимое документа:\n\n{chunk.data}\n\n---\n\n{user_prompt}"
            ))
        else:
            parts.append(types.Part.from_bytes(
                data=chunk.data,
                mime_type=chunk.mime_type,
            ))
            parts.append(types.Part.from_text(text=user_prompt))

        # НЕ используем response_schema — схема слишком сложная для Gemini.
        # Вместо этого просим JSON в промпте и парсим через Pydantic.
        raw = self._call_with_retry(
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            parts=parts,
        )

        if raw is None:
            return None

        # Fallback: если Gemini вернул список вместо словаря
        if isinstance(raw, list):
            logger.info("Gemini вернул список — конвертируем в словарь")
            raw = _convert_list_to_dict(raw)

        # Заполнить file и doc_type из метаданных чанка, если Gemini не вернул
        if isinstance(raw, dict):
            for field_name in raw:
                val = raw[field_name]
                if isinstance(val, dict):
                    src = val.get("source")
                    if isinstance(src, dict):
                        if not src.get("file"):
                            src["file"] = chunk.source_file
                        if not src.get("doc_type"):
                            src["doc_type"] = chunk.source_type
                    elif src is None:
                        # source отсутствует — создаём из метаданных чанка
                        val["source"] = {
                            "file": chunk.source_file,
                            "doc_type": chunk.source_type,
                        }

        try:
            return ChunkExtraction.model_validate(raw)
        except Exception as e:
            logger.error(f"Ошибка валидации ответа: {e}")
            self.last_error = f"Невалидный JSON от Gemini: {e}"
            return None

    def verify_extraction(self, aggregated_json: str,
                          chunks: list[Chunk],
                          equipment_context: str = "") -> dict | None:
        """Верификация агрегированных данных по исходным документам."""
        user_prompt = make_verification_prompt(aggregated_json,
                                               equipment_context=equipment_context)

        parts = []

        uploaded_size = 0
        max_upload_size = 40 * 1024 * 1024  # 40 MB

        for chunk in chunks:
            if isinstance(chunk.data, str):
                text_part = f"--- {chunk.source_file} ({chunk.page_range_display}) ---\n{chunk.data}\n"
                parts.append(types.Part.from_text(text=text_part))
            else:
                chunk_size = len(chunk.data)
                if uploaded_size + chunk_size > max_upload_size:
                    logger.warning(
                        f"Пропущен чанк {chunk.source_file} {chunk.page_range_display} "
                        f"из-за лимита размера при верификации"
                    )
                    continue
                parts.append(types.Part.from_bytes(
                    data=chunk.data,
                    mime_type=chunk.mime_type,
                ))
                uploaded_size += chunk_size

        parts.append(types.Part.from_text(text=user_prompt))

        return self._call_with_retry(
            system_prompt=VERIFICATION_SYSTEM_PROMPT,
            parts=parts,
        )

    def _call_with_retry(self, system_prompt: str, parts: list) -> dict | None:
        """Выполнить запрос к Gemini API с retry при ошибках.

        Всегда запрашивает JSON, парсит вручную.
        """
        self.last_error = ""

        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[types.Content(role="user", parts=parts)],
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.1,
                        response_mime_type="application/json",
                    ),
                )

                if not response.text:
                    logger.warning(f"Пустой ответ от Gemini (попытка {attempt + 1})")
                    self.last_error = "Пустой ответ от Gemini"
                    continue

                # Парсим JSON
                try:
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    # Попробуем извлечь JSON из markdown-блока
                    text = response.text.strip()
                    if text.startswith("```json"):
                        text = text[7:]
                    if text.startswith("```"):
                        text = text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    return json.loads(text.strip())

            except Exception as e:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                error_msg = str(e)
                logger.error(
                    f"Ошибка Gemini API (попытка {attempt + 1}/{MAX_RETRIES}): {error_msg}. "
                    f"Повтор через {delay} сек."
                )
                self.last_error = error_msg
                if attempt < MAX_RETRIES - 1:
                    time.sleep(delay)

        logger.error("Все попытки исчерпаны")
        return None
