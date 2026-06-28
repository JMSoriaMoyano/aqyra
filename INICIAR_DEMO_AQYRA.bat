@echo off
setlocal
title Aqyra - demo visor OpenBIM
cd /d "%~dp0publico"

where node >nul 2>nul
if errorlevel 1 (
  echo [Aqyra] No se encuentra Node.js. Instala Node 22+ desde https://nodejs.org y vuelve a ejecutar.
  pause
  exit /b 1
)

echo [Aqyra] Asegurando pnpm...
call npm install -g pnpm >nul 2>nul

set "PNPM=%APPDATA%\npm\pnpm.cmd"
if not exist "%PNPM%" set "PNPM=pnpm"

echo [Aqyra] Instalando dependencias (la primera vez tarda un poco)...
call "%PNPM%" install
if errorlevel 1 (
  echo [Aqyra] Fallo en pnpm install. Revisa el mensaje de arriba.
  pause
  exit /b 1
)

echo [Aqyra] El navegador se abrira en http://localhost:5173 en unos segundos.
start "" cmd /c "timeout /t 14 >nul & start "" http://localhost:5173"

echo [Aqyra] Arrancando el visor. Cuando cargue, ARRASTRA un archivo .ifc sobre la ventana.
call "%PNPM%" --filter @aqyra/demo dev

pause
