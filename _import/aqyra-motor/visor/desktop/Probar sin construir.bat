@echo off
REM === Probar la app de escritorio SIN construir el .exe (modo desarrollo) ===
REM Lanza Electron directamente cargando el visor de la carpeta de al lado.
cd /d "%~dp0"
echo Instalando Electron si falta (la 1a vez tarda)...
call npm install
if errorlevel 1 ( echo ERROR en "npm install". Revisa Node.js. & pause & exit /b )
echo Abriendo el visor (ventana de la app)...
call npm start
