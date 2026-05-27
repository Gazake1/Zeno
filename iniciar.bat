@echo off
cd /d "%~dp0"
python autoclicker.py
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha ao iniciar. Execute instalar.bat primeiro.
    pause
)
