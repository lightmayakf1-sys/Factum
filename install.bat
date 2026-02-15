@echo off
echo ============================================
echo   Factum — установка библиотек
echo   (требуются права администратора)
echo ============================================
echo.

C:\Python314\python.exe -m pip install --force-reinstall PyQt6 pydantic google-genai pint python-docx PyMuPDF charset-normalizer

echo.
if %errorlevel% equ 0 (
    echo ============================================
    echo   Установка завершена успешно!
    echo   Теперь запустите Factum.bat
    echo ============================================
) else (
    echo ============================================
    echo   ОШИБКА при установке.
    echo   Попробуйте запустить этот файл
    echo   от имени администратора:
    echo   Правый клик - Запуск от имени администратора
    echo ============================================
)
echo.
pause
