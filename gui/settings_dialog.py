"""Диалог настроек: GigaChat credentials, scope, размер чанка."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QPushButton, QGroupBox, QFormLayout, QComboBox,
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
        api_group = QGroupBox("GigaChat API")
        api_layout = QFormLayout()

        self.credentials_input = QLineEdit()
        self.credentials_input.setPlaceholderText("base64(client_id:client_secret) из личного кабинета")
        self.credentials_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.credentials_input.setText(self.config.get("credentials", ""))
        api_layout.addRow("Credentials:", self.credentials_input)

        self.scope_combo = QComboBox()
        self.scope_combo.addItems([
            "GIGACHAT_API_PERS",
            "GIGACHAT_API_B2B",
            "GIGACHAT_API_CORP",
        ])
        current_scope = self.config.get("scope", "GIGACHAT_API_PERS")
        idx = self.scope_combo.findText(current_scope)
        if idx >= 0:
            self.scope_combo.setCurrentIndex(idx)
        api_layout.addRow("Scope:", self.scope_combo)

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
        self.config["credentials"] = self.credentials_input.text().strip()
        self.config["scope"] = self.scope_combo.currentText()
        self.config["chunk_size"] = self.chunk_spin.value()
        save_config(self.config)
        self.accept()
