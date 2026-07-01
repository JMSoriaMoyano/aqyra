@echo off
REM Lanza la firma de la evolucion de C1 (3 repos). Ejecutar con ENTER.
REM Te pedira la passphrase GPG al firmar los tags.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0FIRMA_C1.ps1"
echo.
pause
