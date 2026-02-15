"""Сканирование папки и определение форматов файлов."""

from pathlib import Path
from dataclasses import dataclass

from config import SUPPORTED_EXTENSIONS


@dataclass
class ScannedFile:
    """Информация о найденном файле."""
    path: Path
    name: str
    extension: str
    format_label: str
    size_bytes: int

    @property
    def size_display(self) -> str:
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        else:
            return f"{self.size_bytes / (1024 * 1024):.1f} MB"


def scan_path(path: Path) -> list[ScannedFile]:
    """Сканировать файл или папку. Возвращает список поддерживаемых файлов."""
    results = []

    if path.is_file():
        sf = _try_create_scanned_file(path)
        if sf:
            results.append(sf)
    elif path.is_dir():
        for item in sorted(path.iterdir()):
            if item.is_file():
                sf = _try_create_scanned_file(item)
                if sf:
                    results.append(sf)

    return results


def _try_create_scanned_file(path: Path) -> ScannedFile | None:
    """Создать ScannedFile если формат поддерживается."""
    ext = path.suffix.lower().lstrip(".")
    if ext not in SUPPORTED_EXTENSIONS:
        return None

    return ScannedFile(
        path=path,
        name=path.name,
        extension=ext,
        format_label=SUPPORTED_EXTENSIONS[ext],
        size_bytes=path.stat().st_size,
    )
