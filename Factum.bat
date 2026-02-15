@echo off
cd /d "%~dp0"
start "" /min C:\Python314\python.exe run_console.py "%APPDATA%\Python\Python314\site-packages"
