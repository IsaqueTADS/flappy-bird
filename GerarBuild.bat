@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Crie o ambiente virtual e instale requirements-build.txt conforme o README.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" build_windows.py
if errorlevel 1 (
    echo Falha ao gerar o executavel.
    pause
    exit /b 1
)
echo Executavel disponivel em dist\FlappyBird.exe
pause
