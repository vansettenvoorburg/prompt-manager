@echo off
setlocal
chcp 65001 >nul
title Prompt Sessie Manager

set "INSTALLDIR=%LOCALAPPDATA%\PromptSessieManager"

:: Controleer of de app geïnstalleerd is
if not exist "%INSTALLDIR%\app.py" (
    echo.
    echo [FOUT] Prompt Sessie Manager is niet gevonden op:
    echo        %INSTALLDIR%
    echo.
    echo        Voer eerst installeer.bat uit.
    pause & exit /b 1
)

:: Controleer of Ollama draait, zo niet: start het op de achtergrond
tasklist /FI "IMAGENAME eq ollama.exe" 2>nul | find /I "ollama.exe" >nul
if %errorlevel% neq 0 (
    start "" /B "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
    timeout /t 2 >nul
)

:: Browser openen
start "" "http://localhost:3000"

:: App starten
cd /d "%INSTALLDIR%"
python app.py

endlocal
