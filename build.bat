@echo off
title Zeno - Build
cd /d "%~dp0"
echo ================================================
echo   Zeno AutoClicker - Gerando executavel (.exe)
echo ================================================
echo.

where pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] PyInstaller nao encontrado. Execute instalar.bat primeiro.
    pause
    exit /b 1
)

set ADD_DATA=
set ADD_ICON=
if exist logo.png (
    set ADD_DATA=--add-data "logo.png;."
    echo [OK] logo.png encontrada.
)
if exist logo.ico (
    set ADD_DATA=%ADD_DATA% --add-data "logo.ico;."
    set ADD_ICON=--icon "logo.ico"
    echo [OK] logo.ico encontrada - sera usada como icone do .exe.
)
for %%F in (*.mp3) do (
    set ADD_DATA=%ADD_DATA% --add-data "%%F;."
    echo [OK] Som: %%F
)

echo.
echo Compilando...
echo.

pyinstaller --onefile --windowed --name "Zeno" %ADD_DATA% %ADD_ICON% autoclicker.py

echo.
if exist "dist\Zeno.exe" (
    echo ================================================
    echo   Build concluido!
    echo   Arquivo: dist\Zeno.exe
    echo.
    echo   Envie o Zeno.exe para seus amigos.
    echo   Nao precisa de Python instalado!
    echo ================================================
) else (
    echo [ERRO] Build falhou. Verifique as mensagens acima.
)

pause
