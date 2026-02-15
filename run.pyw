"""Factum — запуск приложения.

Этот файл явно добавляет пути к библиотекам,
чтобы приложение запускалось двойным кликом мыши.
"""

import sys
import os
import traceback
from pathlib import Path

# 1. Добавить папку проекта
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# 2. Добавить user site-packages (где установлены PyQt6 и др.)
#    Пробуем несколько способов найти путь:
candidates = []

# Способ A: через Path.home()
home = Path.home()
candidates.append(home / "AppData" / "Roaming" / "Python" / "Python314" / "site-packages")

# Способ B: через APPDATA
appdata = os.environ.get("APPDATA", "")
if appdata:
    candidates.append(Path(appdata) / "Python" / "Python314" / "site-packages")

# Способ C: через USERPROFILE
userprofile = os.environ.get("USERPROFILE", "")
if userprofile:
    candidates.append(Path(userprofile) / "AppData" / "Roaming" / "Python" / "Python314" / "site-packages")

# Способ D: через site модуль
try:
    import site
    user_site_from_module = site.getusersitepackages()
    if user_site_from_module:
        candidates.append(Path(user_site_from_module))
except Exception:
    pass

# Добавить первый существующий путь
for candidate in candidates:
    try:
        if candidate.is_dir():
            s = str(candidate)
            if s not in sys.path:
                sys.path.insert(0, s)
            break
    except Exception:
        continue

# 3. Запустить приложение
try:
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    from PyQt6.QtWidgets import QApplication
    from gui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Factum")
    app.setOrganizationName("Factum")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

except Exception:
    # Записать ошибку в файл рядом с приложением
    error_file = os.path.join(project_dir, "error_log.txt")
    with open(error_file, "w", encoding="utf-8") as f:
        f.write("Factum — ошибка запуска\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Python: {sys.executable}\n\n")
        f.write(f"sys.path:\n")
        for p in sys.path:
            f.write(f"  {p}\n")
        f.write(f"\nПроверенные пути:\n")
        for c in candidates:
            exists = "ДА" if c.is_dir() else "НЕТ"
            f.write(f"  [{exists}] {c}\n")
        f.write(f"\n{traceback.format_exc()}\n")
    os.startfile(error_file)
