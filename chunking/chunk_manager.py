"""Управление чанками: создание из разных форматов, метаинформация."""

from pathlib import Path
from dataclasses import dataclass, field

from scanner.folder_scanner import ScannedFile
from scanner.file_classifier import classify_file
from chunking.pdf_chunker import split_pdf, PdfChunk


@dataclass
class Chunk:
    """Универсальный чанк для отправки в Gemini API."""
    source_file: str
    source_type: str  # Паспорт, Руководство, Чертёж, Документ
    file_format: str  # PDF, Изображение, DOCX, Excel, CSV, Текст
    page_start: int | None  # 1-based, None для не-PDF
    page_end: int | None
    data: bytes | str  # bytes для бинарных файлов, str для текстовых
    mime_type: str
    total_pages: int | None = None

    @property
    def page_range_display(self) -> str:
        if self.page_start is None:
            return "весь файл"
        if self.page_start == self.page_end:
            return f"стр. {self.page_start}"
        return f"стр. {self.page_start}–{self.page_end}"

    @property
    def source_display(self) -> str:
        return f"{self.source_file} ({self.source_type})"


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


def create_chunks(files: list[ScannedFile], chunk_size: int = 7, overlap: int = 2) -> list[Chunk]:
    """Создать чанки из списка файлов.

    PDF-файлы разбиваются на чанки по chunk_size страниц с перекрытием overlap.
    Изображения — каждое как отдельный чанк.
    Текстовые файлы — целиком.
    """
    chunks = []

    for sf in files:
        doc_type = classify_file(sf.path)
        ext = sf.extension

        if ext == "pdf":
            pdf_chunks = split_pdf(sf.path, chunk_size, overlap)
            for pc in pdf_chunks:
                chunks.append(Chunk(
                    source_file=sf.name,
                    source_type=doc_type,
                    file_format="PDF",
                    page_start=pc.page_start,
                    page_end=pc.page_end,
                    data=pc.chunk_bytes,
                    mime_type="application/pdf",
                    total_pages=pc.total_pages,
                ))
        elif ext in ("txt", "csv"):
            from charset_normalizer import from_path
            result = from_path(sf.path)
            best = result.best()
            text = str(best) if best else sf.path.read_text(encoding="utf-8", errors="replace")
            chunks.append(Chunk(
                source_file=sf.name,
                source_type=doc_type,
                file_format=sf.format_label,
                page_start=None,
                page_end=None,
                data=text,
                mime_type=MIME_TYPES.get(ext, "application/octet-stream"),
            ))
        else:
            data = sf.path.read_bytes()
            chunks.append(Chunk(
                source_file=sf.name,
                source_type=doc_type,
                file_format=sf.format_label,
                page_start=1 if ext in ("jpg", "jpeg", "png", "bmp", "tiff", "tif") else None,
                page_end=1 if ext in ("jpg", "jpeg", "png", "bmp", "tiff", "tif") else None,
                data=data,
                mime_type=MIME_TYPES.get(ext, "application/octet-stream"),
            ))

    return chunks
