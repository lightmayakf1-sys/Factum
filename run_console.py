"""Factum — запуск через python.exe.

Скрывает консольное окно сразу после старта,
принудительно подключает user site-packages (путь передаётся из .bat),
затем запускает GUI-приложение.
"""

import sys
import os
import ctypes
import traceback

# Скрыть консольное окно
try:
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE = 0
except Exception:
    pass

# Добавить папку проекта
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Подключить локальные зависимости (_libs) — без кириллицы, всегда доступны
_libs_dir = os.path.join(project_dir, "_libs")
if os.path.isdir(_libs_dir) and _libs_dir not in sys.path:
    sys.path.insert(0, _libs_dir)

# Принудительно подключить user site-packages
# Проблема: при запуске через `start /min` из .bat Windows не может обратиться
# к папкам с кириллицей в пути. Решение — конвертировать путь в короткий (8.3) формат.
def _get_short_path(long_path: str) -> str:
    """Конвертировать путь в короткий (8.3) формат Windows для обхода проблем с кириллицей."""
    try:
        buf = ctypes.create_unicode_buffer(500)
        r = ctypes.windll.kernel32.GetShortPathNameW(long_path, buf, 500)
        if r > 0:
            return buf.value
    except Exception:
        pass
    return long_path

try:
    import site as _site
    _user_site = _site.getusersitepackages()
    if _user_site:
        _user_site_short = _get_short_path(_user_site)
        if _user_site_short not in sys.path and _user_site not in sys.path:
            sys.path.insert(0, _user_site_short)
except Exception:
    pass

# Запустить приложение
try:
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    from PyQt6.QtWidgets import QApplication
    from gui.main_window import MainWindow

    app = QApplication(sys.argv[:1])  # Без лишних аргументов
    app.setApplicationName("Factum")
    app.setOrganizationName("Factum")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

except Exception:
    # Показать консоль с ошибкой
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW
    except Exception:
        pass

    error_file = os.path.join(project_dir, "error_log.txt")
    with open(error_file, "w", encoding="utf-8") as f:
        f.write("Factum — ошибка запуска\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Python: {sys.executable}\n\n")
        f.write(f"argv: {sys.argv}\n\n")
        f.write(f"sys.path:\n")
        for p in sys.path:
            f.write(f"  {p}\n")
        f.write(f"\n{traceback.format_exc()}\n")
    os.startfile(error_file)
