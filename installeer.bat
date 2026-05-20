@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title Prompt Sessie Manager — Installatie

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║       Prompt Sessie Manager — Installatie        ║
echo ╚══════════════════════════════════════════════════╝
echo.

:: ── Installatiemap ────────────────────────────────────
set "INSTALLDIR=%LOCALAPPDATA%\PromptSessieManager"
set "PYTHON_INSTALLER=%TEMP%\python_installer.exe"
set "OLLAMA_INSTALLER=%TEMP%\ollama_installer.exe"
set "MODEL=llama3.2"

:: ══════════════════════════════════════════════════════
:: STAP 1 — Python controleren / installeren
:: ══════════════════════════════════════════════════════
echo [1/5] Python controleren...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo       Python niet gevonden. Wordt gedownload ^(~25 MB^)...
    echo       Dit kan een minuut duren.
    curl -L -o "%PYTHON_INSTALLER%" "https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe"
    if %errorlevel% neq 0 (
        echo.
        echo [FOUT] Download van Python mislukt.
        echo        Controleer je internetverbinding en probeer opnieuw.
        pause & exit /b 1
    )
    echo       Python installeren...
    "%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
    del "%PYTHON_INSTALLER%" >nul 2>&1
    :: PATH vernieuwen in huidige sessie
    for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "PATH=%%B;%PATH%"
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo [FOUT] Python installatie mislukt of PATH niet bijgewerkt.
        echo        Start dit script opnieuw na een herstart van je computer.
        pause & exit /b 1
    )
    echo       Python geinstalleerd.
) else (
    for /f "tokens=*" %%V in ('python --version 2^>^&1') do echo       %%V gevonden. OK.
)

:: ══════════════════════════════════════════════════════
:: STAP 2 — Ollama controleren / installeren
:: ══════════════════════════════════════════════════════
echo.
echo [2/5] Ollama controleren...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo       Ollama niet gevonden. Wordt gedownload ^(~50 MB^)...
    curl -L -o "%OLLAMA_INSTALLER%" "https://ollama.com/download/OllamaSetup.exe"
    if %errorlevel% neq 0 (
        echo.
        echo [FOUT] Download van Ollama mislukt.
        echo        Controleer je internetverbinding en probeer opnieuw.
        pause & exit /b 1
    )
    echo       Ollama installeren...
    "%OLLAMA_INSTALLER%" /S
    del "%OLLAMA_INSTALLER%" >nul 2>&1
    :: Ollama aan PATH toevoegen
    set "PATH=%LOCALAPPDATA%\Programs\Ollama;%PATH%"
    timeout /t 3 >nul
    echo       Ollama geinstalleerd.
) else (
    echo       Ollama gevonden. OK.
)

:: ══════════════════════════════════════════════════════
:: STAP 3 — AI-model downloaden
:: ══════════════════════════════════════════════════════
echo.
echo [3/5] AI-model "%MODEL%" controleren...
echo       Dit is een eenmalige download van ~2 GB.
echo       Afhankelijk van je verbinding duurt dit 5-15 minuten.
echo.
ollama pull %MODEL%
if %errorlevel% neq 0 (
    echo.
    echo [WAARSCHUWING] Model kon niet worden gedownload.
    echo               De app werkt wel, maar offline gebruik is niet beschikbaar
    echo               totdat het model is gedownload via: ollama pull %MODEL%
)

:: ══════════════════════════════════════════════════════
:: STAP 4 — App installeren
:: ══════════════════════════════════════════════════════
echo.
echo [4/5] Prompt Sessie Manager installeren...

if not exist "%INSTALLDIR%" mkdir "%INSTALLDIR%"

:: Bestanden kopiëren vanuit dezelfde map als dit script
xcopy /E /I /Y "%~dp0app" "%INSTALLDIR%\app" >nul 2>&1
xcopy /E /I /Y "%~dp0static" "%INSTALLDIR%\static" >nul 2>&1
copy /Y "%~dp0app.py" "%INSTALLDIR%\" >nul 2>&1
copy /Y "%~dp0requirements.txt" "%INSTALLDIR%\" >nul 2>&1

if exist "%~dp0.env.example" (
    if not exist "%INSTALLDIR%\.env" (
        copy "%~dp0.env.example" "%INSTALLDIR%\.env" >nul
    )
)

:: Mappen aanmaken als ze nog niet bestaan
if not exist "%INSTALLDIR%\sessions" mkdir "%INSTALLDIR%\sessions"
if not exist "%INSTALLDIR%\outputs" mkdir "%INSTALLDIR%\outputs"
if not exist "%INSTALLDIR%\logs" mkdir "%INSTALLDIR%\logs"

:: Python dependencies installeren
echo       Python-pakketten installeren...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r "%INSTALLDIR%\requirements.txt"
if %errorlevel% neq 0 (
    echo.
    echo [FOUT] Installatie van Python-pakketten mislukt.
    echo        Probeer: pip install -r requirements.txt
    pause & exit /b 1
)
echo       Pakketten geinstalleerd.

:: ══════════════════════════════════════════════════════
:: STAP 5 — Snelkoppeling aanmaken op bureaublad
:: ══════════════════════════════════════════════════════
echo.
echo [5/5] Snelkoppeling aanmaken...

:: start.bat schrijven in installatiemap (alleen als nog niet aanwezig via installer)
if not exist "%INSTALLDIR%\start.bat" (
    (
        echo @echo off
        echo setlocal
        echo chcp 65001 ^>nul
        echo title Prompt Sessie Manager
        echo.
        echo set "INSTALLDIR=%LOCALAPPDATA%\PromptSessieManager"
        echo.
        echo :: Controleer of de app geinstalleerd is
        echo if not exist "%%INSTALLDIR%%\app.py" ^(
        echo     echo.
        echo     echo [FOUT] Prompt Sessie Manager is niet gevonden op:
        echo     echo        %%INSTALLDIR%%
        echo     echo.
        echo     echo        Voer eerst installeer.bat uit.
        echo     pause ^& exit /b 1
        echo ^)
        echo.
        echo :: Start Ollama op de achtergrond als het nog niet draait
        echo tasklist /FI "IMAGENAME eq ollama.exe" 2^>nul ^| find /I "ollama.exe" ^>nul
        echo if %%errorlevel%% neq 0 ^(
        echo     start "" /B "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
        echo     timeout /t 2 ^>nul
        echo ^)
        echo.
        echo :: Browser openen en app starten
        echo start "" "http://localhost:3000"
        echo cd /d "%%INSTALLDIR%%"
        echo python app.py
        echo endlocal
    ) > "%INSTALLDIR%\start.bat"
)

:: Snelkoppeling op bureaublad via PowerShell
powershell -NoProfile -Command ^
  "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\Prompt Sessie Manager.lnk');" ^
  "$s.TargetPath='%INSTALLDIR%\start.bat';" ^
  "$s.WorkingDirectory='%INSTALLDIR%';" ^
  "$s.Description='Start de Prompt Sessie Manager';" ^
  "$s.Save()"

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║   Installatie voltooid!                          ║
echo ║                                                  ║
echo ║   Dubbelklik op het bureaublad-icoon om          ║
echo ║   de app te starten.                             ║
echo ║                                                  ║
echo ║   De app opent automatisch in je browser op      ║
echo ║   http://localhost:3000                          ║
echo ╚══════════════════════════════════════════════════╝
echo.

set /p START="Nu direct starten? (j/n): "
if /i "!START!"=="j" (
    start "" "http://localhost:3000"
    python "%INSTALLDIR%\app.py"
)

endlocal
