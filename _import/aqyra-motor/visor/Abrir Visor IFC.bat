@echo off
REM === Visor IFC — arranque de un clic, auto-reparable (servidor limpio + ventana app) ===
cd /d "%~dp0"
set "URL=http://localhost:8007/visor-ifc-v1.0.html"

REM 1) matar cualquier servidor anterior colgado en el 8007 (evita ERR_EMPTY_RESPONSE)
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8007 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { try { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } catch {} }" >nul 2>&1

REM 2) arrancar un servidor fresco, oculto (pythonw) o minimizado (py/python)
where pythonw >nul 2>nul
if "%errorlevel%"=="0" ( start "" pythonw -m http.server 8007 & goto wait )
where py >nul 2>nul
if "%errorlevel%"=="0" ( start "Visor IFC servidor (no cerrar)" /min py -m http.server 8007 & goto wait )
where python >nul 2>nul
if "%errorlevel%"=="0" ( start "Visor IFC servidor (no cerrar)" /min python -m http.server 8007 & goto wait )
echo No se encontro Python. Instalalo o sirve esta carpeta en el puerto 8007.
pause
exit /b

:wait
REM 3) esperar a que el servidor RESPONDA de verdad (200), no solo a que el puerto abra
powershell -NoProfile -Command "for($i=0;$i -lt 40;$i++){ try{ $r=Invoke-WebRequest -UseBasicParsing -Uri '%URL%' -TimeoutSec 1; if($r.StatusCode -eq 200){ exit 0 } }catch{}; Start-Sleep -Milliseconds 200 }; exit 1" >nul 2>&1

:open
REM 4) abrir en modo aplicacion (ventana limpia)
set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if exist "%CHROME%" ( start "" "%CHROME%" --app=%URL% ) else ( start "" %URL% )
