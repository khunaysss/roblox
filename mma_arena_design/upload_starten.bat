@echo off
rem Startet upload_starten_v02.ps1 ohne Probleme mit der Ausfuehrungsrichtlinie; das Fenster bleibt offen.
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -NoExit -File "%~dp0upload_starten_v02.ps1"
