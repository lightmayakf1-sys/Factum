@echo off
chcp 65001 >nul 2>&1
echo.
echo ============================================
echo   Normocontrol — сборка standalone .exe
echo ============================================
echo.

cd /d "%~dp0"

:: Проверка Python
if not exist "C:\Python314\python.exe" (
    echo ОШИБКА: Python 3.14 не найден в C:\Python314\
    pause
    exit /b 1
)

:: Проверка PyInstaller
C:\Python314\python.exe -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller не найден. Устанавливаю...
    C:\Python314\python.exe -m pip install pyinstaller
    echo.
)

echo Запускаю сборку...
echo Это может занять 2-5 минут.
echo.

C:\Python314\python.exe -m PyInstaller --clean --noconfirm normocontrol.spec

echo.
if %errorlevel% equ 0 (
    echo ============================================
    echo   Сборка завершена успешно!
    echo.
    echo   Файл: %~dp0dist\Normocontrol.exe
    echo ============================================
) else (
    echo ============================================
    echo   ОШИБКА при сборке.
    echo   Проверьте вывод выше.
    echo ============================================
)
echo.
pause
