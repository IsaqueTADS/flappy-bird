@echo off
setlocal
cd /d "%~dp0"
set "GAME_PYTHON=%LocalAppData%\Programs\Python\Python314\python.exe"
if exist "%GAME_PYTHON%" goto run
set "GAME_PYTHON=%UserProfile%\AppData\Local\Programs\Python\Python314\python.exe"
if exist "%GAME_PYTHON%" goto run
where py >nul 2>nul
if not errorlevel 1 (
    py -3 game.py
    if errorlevel 1 pause
    exit /b
)
echo Python nao encontrado. Instale Python com o componente Tcl/Tk.
pause
exit /b 1
:run
"%GAME_PYTHON%" game.py
if errorlevel 1 pause
