@echo off
chcp 65001 >nul 2>&1
echo.
echo ============================================
echo   Factum — установка библиотек Python
echo ============================================
echo.

:: Проверяем наличие Python
if not exist "C:\Python314\python.exe" (
    echo ОШИБКА: Python 3.14 не найден в C:\Python314\
    echo.
    echo Установите Python 3.14 в папку C:\Python314\
    echo Скачать: https://www.python.org/downloads/
    echo.
    echo При установке Python выберите:
    echo   [x] Install for all users
    echo   Customize installation path: C:\Python314\
    echo.
    pause
    exit /b 1
)

echo Python найден: C:\Python314\python.exe
echo.
echo Устанавливаю зависимости...
echo.

C:\Python314\python.exe -m pip install --force-reinstall PyQt6 pydantic gigachat pint python-docx PyMuPDF charset-normalizer

echo.
if %errorlevel% equ 0 (
    echo ============================================
    echo   Установка завершена успешно!
    echo ============================================
) else (
    echo ============================================
    echo   ОШИБКА при установке библиотек.
    echo.
    echo   Попробуйте запустить этот файл
    echo   от имени администратора.
    echo ============================================
)
echo.
pause
