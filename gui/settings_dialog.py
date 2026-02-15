"""Диалог настроек: API ключ, модель, размер чанка."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QPushButton, QGroupBox, QFormLayout,
)
from PyQt6.QtCore import Qt

from config import load_config, save_config, FIXED_MODEL


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(500)

        self.config = load_config()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # --- API ---
        api_group = QGroupBox("Google Gemini API")
        api_layout = QFormLayout()

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Вставьте API ключ из Google AI Studio")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setText(self.config.get("api_key", ""))
        api_layout.addRow("API ключ:", self.api_key_input)

        model_label = QLabel(f"<b>{FIXED_MODEL}</b>")
        model_label.setStyleSheet("color: #333;")
        api_layout.addRow("Модель:", model_label)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # --- Обработка ---
        proc_group = QGroupBox("Обработка документов")
        proc_layout = QFormLayout()

        self.chunk_spin = QSpinBox()
        self.chunk_spin.setRange(3, 20)
        self.chunk_spin.setValue(self.config.get("chunk_size", 7))
        self.chunk_spin.setSuffix(" стр.")
        proc_layout.addRow("Размер чанка:", self.chunk_spin)

        chunk_hint = QLabel(
            "Меньше = точнее извлечение, но больше API-запросов.\n"
            "Рекомендуется: 5–10 страниц."
        )
        chunk_hint.setStyleSheet("color: gray; font-size: 9pt;")
        proc_layout.addRow("", chunk_hint)

        proc_group.setLayout(proc_layout)
        layout.addWidget(proc_group)

        # --- Кнопки ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _save(self):
        self.config["api_key"] = self.api_key_input.text().strip()
        self.config["chunk_size"] = self.chunk_spin.value()
        save_config(self.config)
        self.accept()
