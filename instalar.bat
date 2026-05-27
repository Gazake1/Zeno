@echo off
title MC AutoClicker - Instalador
echo ================================================
echo   MC AutoClicker - Instalacao de dependencias
echo ================================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado. Instale o Python em https://www.python.org/downloads/
    echo        Marque "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

echo Instalando dependencias...
echo.
pip install customtkinter pynput pillow pyinstaller

echo.
echo ================================================
echo   Instalacao concluida!
echo   - Para rodar:   execute iniciar.bat
echo   - Para buildar: execute build.bat
echo ================================================
pause
