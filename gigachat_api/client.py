"""Обёртка GigaChat API: загрузка файлов, запросы с retry, structured output."""

import json
import os
import tempfile
import time
import logging

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from gigachat.exceptions import GigaChatException

from gigachat_api.schema import ChunkExtraction, CHECKLIST_FIELDS
from gigachat_api.prompts import (
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
            entry = {k: v for k, v in item.items() if k != "param_id"}
            result[field_name] = entry
        else:
            logger.warning(f"Неизвестный param_id: {param_id}")
    return result


class GigaChatClient:
    """Клиент для работы с GigaChat API."""

    def __init__(self, credentials: str, model: str = "GigaChat-Max",
                 scope: str = "GIGACHAT_API_PERS"):
        self.giga = GigaChat(
            credentials=credentials,
            scope=scope,
            model=model,
            verify_ssl_certs=False,
        )
        self.model = model
        self.last_error: str = ""  # Последняя ошибка для отображения в GUI

    def _upload_bytes(self, data: bytes, mime_type: str) -> str | None:
        """Загрузить бинарные данные в хранилище GigaChat, вернуть file_id.

        Сохраняет bytes во временный файл, загружает через SDK, удаляет файл.
        """
        suffix_map = {
            "application/pdf": ".pdf",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/bmp": ".bmp",
            "image/tiff": ".tiff",
        }
        suffix = suffix_map.get(mime_type, ".bin")

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name

            with open(tmp_path, "rb") as f:
                uploaded = self.giga.upload_file(f, purpose="general")
            return uploaded.id
        except Exception as e:
            logger.error(f"Ошибка загрузки файла в хранилище GigaChat: {e}")
            self.last_error = f"Ошибка загрузки файла: {e}"
            return None
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def determine_equipment_context(self, first_chunks: list[Chunk]) -> dict | None:
        """Определить контекст оборудования по первым чанкам каждого файла.

        GigaChat принимает только 1 документ на запрос.
        Стратегия: загружаем первый PDF-чанк как attachment,
        текстовые описания остальных файлов добавляем в промпт.
        """
        file_names = [c.source_file for c in first_chunks]
        user_prompt = make_context_prompt(file_names)

        # Найти первый бинарный чанк для attachment
        file_id = None
        text_parts = []

        for chunk in first_chunks:
            if isinstance(chunk.data, str):
                text_parts.append(
                    f"--- Файл: {chunk.source_file} ({chunk.source_type}) ---\n{chunk.data}"
                )
            elif file_id is None:
                # Загружаем только первый бинарный чанк
                file_id = self._upload_bytes(chunk.data, chunk.mime_type)
            else:
                # Остальные бинарные чанки — описание в тексте
                text_parts.append(
                    f"--- Файл: {chunk.source_file} ({chunk.source_type}) [бинарный, не загружен] ---"
                )

        # Собираем финальный промпт
        full_prompt = ""
        if text_parts:
            full_prompt = "\n\n".join(text_parts) + "\n\n---\n\n"
        full_prompt += user_prompt

        return self._call_with_retry(
            system_prompt=CONTEXT_SYSTEM_PROMPT,
            user_content=full_prompt,
            file_id=file_id,
        )

    def extract_from_chunk(self, chunk: Chunk,
                           equipment_context: str = "") -> ChunkExtraction | None:
        """Извлечь параметры из одного чанка.

        Для бинарных чанков (PDF): загружаем в хранилище → attachments.
        Для текстовых чанков: отправляем содержимое в промпте.
        """
        user_prompt = make_extraction_prompt(
            source_file=chunk.source_file,
            source_type=chunk.source_type,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            equipment_context=equipment_context,
        )

        file_id = None
        if isinstance(chunk.data, str):
            full_prompt = f"Содержимое документа:\n\n{chunk.data}\n\n---\n\n{user_prompt}"
        else:
            file_id = self._upload_bytes(chunk.data, chunk.mime_type)
            if file_id is None:
                return None
            full_prompt = user_prompt

        raw = self._call_with_retry(
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_content=full_prompt,
            file_id=file_id,
        )

        if raw is None:
            return None

        # Fallback: если модель вернула список вместо словаря
        if isinstance(raw, list):
            logger.info("GigaChat вернул список — конвертируем в словарь")
            raw = _convert_list_to_dict(raw)

        # Заполнить file и doc_type из метаданных чанка, если модель не вернула
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
                        val["source"] = {
                            "file": chunk.source_file,
                            "doc_type": chunk.source_type,
                        }

        try:
            return ChunkExtraction.model_validate(raw)
        except Exception as e:
            logger.error(f"Ошибка валидации ответа: {e}")
            self.last_error = f"Невалидный JSON от GigaChat: {e}"
            return None

    def verify_extraction(self, aggregated_json: str,
                          chunks: list[Chunk],
                          equipment_context: str = "") -> dict | None:
        """Верификация агрегированных данных по исходным документам.

        GigaChat — 1 файл за раз. Загружаем первый PDF-чанк как attachment,
        текстовые чанки и агрегированные данные — в промпте.
        """
        user_prompt = make_verification_prompt(aggregated_json,
                                               equipment_context=equipment_context)

        file_id = None
        text_parts = []
        uploaded_size = 0
        max_upload_size = 40 * 1024 * 1024  # 40 MB

        for chunk in chunks:
            if isinstance(chunk.data, str):
                text_parts.append(
                    f"--- {chunk.source_file} ({chunk.page_range_display}) ---\n{chunk.data}"
                )
            else:
                chunk_size = len(chunk.data)
                if file_id is None and uploaded_size + chunk_size <= max_upload_size:
                    # Загружаем первый бинарный чанк как attachment
                    file_id = self._upload_bytes(chunk.data, chunk.mime_type)
                    uploaded_size += chunk_size
                else:
                    logger.info(
                        f"Чанк {chunk.source_file} {chunk.page_range_display} "
                        f"передан только текстом (лимит: 1 файл на запрос)"
                    )

        # Собираем промпт: текстовые чанки + агрегированные данные + задание
        full_prompt = ""
        if text_parts:
            full_prompt = "\n\n".join(text_parts) + "\n\n---\n\n"
        full_prompt += user_prompt

        return self._call_with_retry(
            system_prompt=VERIFICATION_SYSTEM_PROMPT,
            user_content=full_prompt,
            file_id=file_id,
        )

    def _call_with_retry(self, system_prompt: str, user_content: str,
                         file_id: str | None = None) -> dict | None:
        """Выполнить запрос к GigaChat API с retry при ошибках.

        Всегда запрашивает JSON, парсит вручную.
        """
        self.last_error = ""

        for attempt in range(MAX_RETRIES):
            try:
                # Формируем сообщения
                messages = [
                    Messages(role=MessagesRole.SYSTEM, content=system_prompt),
                ]

                user_msg_kwargs = {
                    "role": MessagesRole.USER,
                    "content": user_content,
                }
                if file_id:
                    user_msg_kwargs["attachments"] = [file_id]

                messages.append(Messages(**user_msg_kwargs))

                # Формируем запрос
                chat_kwargs = {
                    "messages": messages,
                    "model": self.model,
                    "temperature": 0.1,
                }
                if file_id:
                    chat_kwargs["function_call"] = "auto"

                chat = Chat(**chat_kwargs)
                response = self.giga.chat(chat)

                # Извлекаем текст ответа
                text = response.choices[0].message.content if response.choices else None

                if not text:
                    logger.warning(f"Пустой ответ от GigaChat (попытка {attempt + 1})")
                    self.last_error = "Пустой ответ от GigaChat"
                    continue

                # Парсим JSON
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    # Попробуем извлечь JSON из markdown-блока
                    cleaned = text.strip()
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[7:]
                    if cleaned.startswith("```"):
                        cleaned = cleaned[3:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    return json.loads(cleaned.strip())

            except GigaChatException as e:
                error_msg = str(e)
                # 422 — PDF слишком большой, не повторять
                if "422" in error_msg:
                    logger.error(f"GigaChat 422: контент превышает контекстное окно: {error_msg}")
                    self.last_error = "PDF слишком большой для контекстного окна GigaChat"
                    return None

                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.error(
                    f"Ошибка GigaChat API (попытка {attempt + 1}/{MAX_RETRIES}): {error_msg}. "
                    f"Повтор через {delay} сек."
                )
                self.last_error = error_msg
                if attempt < MAX_RETRIES - 1:
                    time.sleep(delay)

            except Exception as e:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                error_msg = str(e)
                logger.error(
                    f"Ошибка GigaChat (попытка {attempt + 1}/{MAX_RETRIES}): {error_msg}. "
                    f"Повтор через {delay} сек."
                )
                self.last_error = error_msg
                if attempt < MAX_RETRIES - 1:
                    time.sleep(delay)

        logger.error("Все попытки исчерпаны")
        return None
