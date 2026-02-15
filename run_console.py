"""Normocontrol — запуск через python.exe.

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

# Принудительно подключить user site-packages
# Путь передаётся как аргумент из .bat файла (Windows раскрывает %APPDATA% корректно)
if len(sys.argv) > 1:
    user_site = sys.argv[1]
    if user_site not in sys.path:
        sys.path.insert(0, user_site)

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
    app.setApplicationName("Normocontrol")
    app.setOrganizationName("Normocontrol")

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
        f.write("Normocontrol — ошибка запуска\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Python: {sys.executable}\n\n")
        f.write(f"argv: {sys.argv}\n\n")
        f.write(f"sys.path:\n")
        for p in sys.path:
            f.write(f"  {p}\n")
        f.write(f"\n{traceback.format_exc()}\n")
    os.startfile(error_file)
