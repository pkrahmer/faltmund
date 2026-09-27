@echo off
rem faltmund foto – GPU-Render unter Windows
rem   render.bat            Probebild 150  -> probe_150.png  (Setup-Check, zeigt Geraet und Sekunden)
rem   render.bat alle       alle Bilder nach frames\ (setzt fort) + Filmlook -> faltfrosch_film.mp4
rem   render.bat film       nur Nachbearbeitung aus vorhandenen frames\
rem Uebersteuern: set SAMPLES=128   /   set GERAET=CPU
setlocal
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
  py -3.11 --version >nul 2>&1 || (
    echo bpy 4.5.4 braucht Python 3.11. Installieren mit:
    echo   winget install Python.Python.3.11
    exit /b 1
  )
  echo Lege .venv mit Python 3.11 an und installiere bpy ^(~400 MB^) ...
  py -3.11 -m venv .venv || exit /b 1
  .venv\Scripts\python -m pip install -q --upgrade pip
  .venv\Scripts\python -m pip install bpy==4.5.4 scipy numpy pillow imageio imageio-ffmpeg || exit /b 1
)
set PY=.venv\Scripts\python.exe

if not exist frosch_buntstift.png (
  echo frosch_buntstift.png fehlt - erst buntstift.py laufen lassen ^(braucht cairosvg^).
  exit /b 1
)

if /i "%1"=="alle" goto alle
if /i "%1"=="film" goto film
%PY% szene.py test 150
exit /b %errorlevel%

:alle
%PY% szene.py alle || exit /b 1
:film
%PY% nachbearbeitung.py
