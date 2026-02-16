# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec для Factum.
#
# Сборка:  cd installer && C:/Python314/python.exe -m PyInstaller factum.spec
# Результат: dist/Factum.exe

import os
import sys

# Корень проекта — на одну папку выше от installer/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(SPECPATH), ''))
# SPECPATH уже указывает на installer/, поэтому:
PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))

a = Analysis(
    # Точка входа
    [os.path.join(PROJECT_ROOT, 'main.py')],

    pathex=[PROJECT_ROOT],

    binaries=[],

    datas=[],

    # Скрытые импорты — модули, которые PyInstaller не обнаруживает автоматически
    hiddenimports=[
        # === Модули проекта ===
        'config',
        'worker',
        'scanner',
        'scanner.folder_scanner',
        'scanner.file_classifier',
        'chunking',
        'chunking.chunk_manager',
        'chunking.pdf_chunker',
        'chunking.image_chunker',
        'gigachat_api',
        'gigachat_api.schema',
        'gigachat_api.prompts',
        'gigachat_api.client',
        'processing',
        'processing.aggregator',
        'processing.conflict_resolver',
        'processing.validator',
        'processing.units',
        'output',
        'output.docx_generator',
        'output.canonical',
        'output.formatter',
        'gui',
        'gui.main_window',
        'gui.settings_dialog',

        # === Зависимости, часто пропускаемые PyInstaller ===
        # gigachat SDK
        'gigachat',
        'gigachat.models',
        'gigachat.exceptions',
        'httpx',
        'httpcore',

        # pydantic
        'pydantic',
        'pydantic.fields',
        'pydantic._internal',
        'pydantic._internal._generate_schema',
        'pydantic._internal._validators',
        'pydantic._internal._decorators',
        'pydantic_core',
        'annotated_types',

        # PyMuPDF
        'fitz',
        'fitz.fitz',

        # python-docx
        'docx',
        'docx.shared',
        'docx.enum',
        'docx.enum.table',
        'docx.enum.text',
        'docx.oxml',
        'docx.oxml.ns',
        'lxml',
        'lxml.etree',
        'lxml._elementpath',

        # charset-normalizer
        'charset_normalizer',
        'charset_normalizer.md',

        # pint (зарезервирован)
        'pint',

        # PyQt6
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.sip',
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],

    excludes=[
        # Исключаем ненужные модули для уменьшения размера
        'tkinter',
        'unittest',
        'test',
        'xmlrpc',
        'multiprocessing',
        'lib2to3',
    ],

    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Factum',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                # GUI-приложение, без консоли
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(PROJECT_ROOT, 'factum.ico'),
)
