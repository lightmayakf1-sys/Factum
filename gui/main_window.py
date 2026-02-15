"""Главное окно приложения Factum."""

import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QProgressBar, QTextBrowser,
    QLabel, QFileDialog, QMessageBox, QSplitter, QTextEdit,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QDragEnterEvent, QDropEvent

from config import load_config, SUPPORTED_EXTENSIONS, FIXED_MODEL
from scanner.folder_scanner import scan_path, ScannedFile
from gui.settings_dialog import SettingsDialog
from worker import PipelineWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Factum - Анализ паспортов оборудования  [{FIXED_MODEL}]")
        self.setMinimumSize(900, 700)
        self.setAcceptDrops(True)

        self.files: list[ScannedFile] = []
        self.worker: PipelineWorker | None = None
        self.last_output_path: str = ""

        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # --- Верхняя панель: кнопки загрузки ---
        top_layout = QHBoxLayout()

        self.btn_files = QPushButton("Выбрать файл(ы)")
        self.btn_files.clicked.connect(self._on_select_files)
        top_layout.addWidget(self.btn_files)

        self.btn_folder = QPushButton("Выбрать папку")
        self.btn_folder.clicked.connect(self._on_select_folder)
        top_layout.addWidget(self.btn_folder)

        self.btn_clear = QPushButton("Очистить")
        self.btn_clear.clicked.connect(self._on_clear)
        top_layout.addWidget(self.btn_clear)

        top_layout.addStretch()

        self.btn_settings = QPushButton("Настройки")
        self.btn_settings.clicked.connect(self._on_settings)
        top_layout.addWidget(self.btn_settings)

        main_layout.addLayout(top_layout)

        # --- Список файлов ---
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(120)
        self.file_list.setMaximumHeight(200)
        main_layout.addWidget(QLabel("Загруженные документы:"))
        main_layout.addWidget(self.file_list)

        # --- Кнопка анализа ---
        action_layout = QHBoxLayout()
        self.btn_analyze = QPushButton("Анализировать")
        self.btn_analyze.setMinimumHeight(40)
        self.btn_analyze.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.btn_analyze.clicked.connect(self._on_analyze)
        self.btn_analyze.setEnabled(False)
        action_layout.addWidget(self.btn_analyze)

        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.setMinimumHeight(40)
        self.btn_cancel.clicked.connect(self._on_cancel)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setVisible(False)
        action_layout.addWidget(self.btn_cancel)

        main_layout.addLayout(action_layout)

        # --- Прогресс ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #555; font-size: 10pt;")
        self.progress_label.setVisible(False)
        main_layout.addWidget(self.progress_label)

        # --- Splitter: лог + превью ---
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Лог
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setPlaceholderText("Лог обработки...")
        splitter.addWidget(self.log_text)

        # Превью
        self.preview = QTextBrowser()
        self.preview.setPlaceholderText("Предпросмотр карточки появится здесь после обработки")
        splitter.addWidget(self.preview)

        splitter.setSizes([150, 300])
        main_layout.addWidget(splitter)

        # --- Нижняя панель ---
        bottom_layout = QHBoxLayout()

        self.btn_save = QPushButton("Сохранить DOCX")
        self.btn_save.clicked.connect(self._on_save)
        self.btn_save.setEnabled(False)
        bottom_layout.addWidget(self.btn_save)

        self.btn_open = QPushButton("Открыть в Word")
        self.btn_open.clicked.connect(self._on_open_word)
        self.btn_open.setEnabled(False)
        bottom_layout.addWidget(self.btn_open)

        bottom_layout.addStretch()

        self.status_label = QLabel("")
        bottom_layout.addWidget(self.status_label)

        main_layout.addLayout(bottom_layout)

    # --- Drag & Drop ---
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_dir():
                self._add_files_from_path(path)
            elif path.is_file():
                self._add_files_from_path(path)

    # --- Обработчики кнопок ---
    def _on_select_files(self):
        exts = " ".join(f"*.{e}" for e in SUPPORTED_EXTENSIONS)
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выбрать файлы", "",
            f"Документы ({exts});;Все файлы (*)"
        )
        for f in files:
            self._add_files_from_path(Path(f))

    def _on_select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выбрать папку")
        if folder:
            self._add_files_from_path(Path(folder))

    def _on_clear(self):
        self.files.clear()
        self.file_list.clear()
        self.btn_analyze.setEnabled(False)
        self.preview.clear()
        self.log_text.clear()
        self.status_label.setText("")

    def _on_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def _on_analyze(self):
        if not self.files:
            return

        config = load_config()
        if not config.get("api_key"):
            QMessageBox.warning(
                self, "API ключ не настроен",
                "Откройте Настройки и введите API ключ Google Gemini."
            )
            return

        # Выбрать путь сохранения
        default_name = "Карточка_оборудования.docx"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить карточку", default_name,
            "Word документ (*.docx)"
        )
        if not save_path:
            return

        self.last_output_path = save_path

        # Запуск pipeline
        self.btn_analyze.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_cancel.setVisible(True)
        self.btn_save.setEnabled(False)
        self.btn_open.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.log_text.clear()
        self.preview.clear()

        self.worker = PipelineWorker(self.files, Path(save_path))
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.log.connect(self._on_log)
        self.worker.preview_ready.connect(self._on_preview)
        self.worker.start()

    def _on_cancel(self):
        if self.worker:
            self.worker.cancel()

    def _on_save(self):
        if not self.last_output_path or not Path(self.last_output_path).exists():
            QMessageBox.warning(self, "Ошибка", "Файл карточки не найден.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить карточку", self.last_output_path,
            "Word документ (*.docx)"
        )
        if not save_path:
            return

        if save_path != self.last_output_path:
            import shutil
            shutil.copy2(str(self.last_output_path), save_path)

        self.last_output_path = save_path
        QMessageBox.information(self, "Сохранено", f"Карточка сохранена:\n{save_path}")

    def _on_open_word(self):
        if self.last_output_path and Path(self.last_output_path).exists():
            os.startfile(self.last_output_path)

    # --- Signals ---
    def _on_progress(self, stage: int, current: int, total: int, message: str):
        if total > 0:
            stage_weight = 100 / 6
            overall = int((stage - 1) * stage_weight + (current / total) * stage_weight)
            self.progress_bar.setValue(min(overall, 100))
        self.progress_label.setText(f"Этап {stage}/6: {message}")

    def _on_finished(self, success: bool, output_path: str, error: str):
        self.btn_analyze.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

        if success:
            self.btn_save.setEnabled(True)
            self.btn_open.setEnabled(True)
            self.status_label.setText(f"Готово: {output_path}")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self._on_log("Обработка завершена успешно!")
        else:
            self.status_label.setText(f"Ошибка: {error}")
            self.status_label.setStyleSheet("color: red;")
            self._on_log(f"ОШИБКА: {error}")

        self.worker = None

    def _on_log(self, message: str):
        self.log_text.append(message)

    def _on_preview(self, html: str):
        self.preview.setHtml(html)

    # --- Helpers ---
    def _add_files_from_path(self, path: Path):
        scanned = scan_path(path)
        existing_paths = {f.path for f in self.files}
        for sf in scanned:
            if sf.path not in existing_paths:
                self.files.append(sf)
                item = QListWidgetItem(f"{sf.name}  ({sf.format_label}, {sf.size_display})")
                self.file_list.addItem(item)

        self.btn_analyze.setEnabled(len(self.files) > 0)
