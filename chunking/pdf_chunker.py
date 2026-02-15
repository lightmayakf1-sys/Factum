"""Разбиение PDF на чанки по N страниц."""

import io
import tempfile
from pathlib import Path
from dataclasses import dataclass

import fitz  # PyMuPDF


@dataclass
class PdfChunk:
    """Один чанк (фрагмент) PDF-документа."""
    source_file: str
    page_start: int  # 1-based
    page_end: int    # 1-based, inclusive
    chunk_bytes: bytes
    total_pages: int

    @property
    def page_range_display(self) -> str:
        if self.page_start == self.page_end:
            return f"стр. {self.page_start}"
        return f"стр. {self.page_start}–{self.page_end}"


def split_pdf(path: Path, chunk_size: int = 7, overlap: int = 2) -> list[PdfChunk]:
    """Разбить PDF на чанки по chunk_size страниц с перекрытием.

    Перекрытие (overlap) гарантирует, что данные на границе чанков
    не будут потеряны — соседние чанки разделяют общие страницы.

    Пример (chunk_size=7, overlap=2):
        Чанк 1: стр. 1–7
        Чанк 2: стр. 6–12
        Чанк 3: стр. 11–17

    Args:
        path: Путь к PDF-файлу.
        chunk_size: Количество страниц в одном чанке (по умолчанию 7).
        overlap: Количество перекрывающихся страниц (по умолчанию 2).

    Returns:
        Список PdfChunk.
    """
    doc = fitz.open(str(path))
    total_pages = len(doc)
    chunks = []

    # Шаг сдвига: chunk_size минус overlap
    step = max(1, chunk_size - overlap)

    for start_idx in range(0, total_pages, step):
        end_idx = min(start_idx + chunk_size - 1, total_pages - 1)

        chunk_doc = fitz.open()
        chunk_doc.insert_pdf(doc, from_page=start_idx, to_page=end_idx)

        chunk_bytes = chunk_doc.tobytes()
        chunk_doc.close()

        chunks.append(PdfChunk(
            source_file=path.name,
            page_start=start_idx + 1,
            page_end=end_idx + 1,
            chunk_bytes=chunk_bytes,
            total_pages=total_pages,
        ))

        # Если дошли до конца — не создаём лишний чанк
        if end_idx >= total_pages - 1:
            break

    doc.close()
    return chunks
