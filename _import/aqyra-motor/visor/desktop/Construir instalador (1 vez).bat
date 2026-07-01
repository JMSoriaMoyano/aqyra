@echo off
REM === Construir el INSTALADOR (Setup) y el PORTABLE de Visor IFC ===
REM electron-builder necesita crear enlaces simbolicos al preparar sus herramientas,
REM y Windows exige permisos de administrador para eso. Por eso este .bat se auto-eleva.

net session >nul 2>&1
if errorlevel 1 (
  echo Solicitando permisos de administrador ^(UAC^)...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

cd /d "%~dp0"
set CSC_IDENTITY_AUTO_DISCOVERY=false

echo === Construir Visor IFC (instalador + portable) ===
echo.
echo 1/3 Copiando los archivos del visor a .\app ...
if not exist app mkdir app
copy /Y "..\visor-ifc-v1.2.html" "app\" >nul
copy /Y "..\visor-ifc-v1.1.html" "app\" >nul 2>nul
copy /Y "..\visor-ifc-v1.0.html" "app\" >nul 2>nul
copy /Y "..\sw.js" "app\" >nul 2>nul
copy /Y "..\visor.webmanifest" "app\" >nul 2>nul
if exist "app\models" rmdir /S /Q "app\models"
xcopy /Y /E /I "..\models" "app\models" >nul
if exist "app\icons" rmdir /S /Q "app\icons"
xcopy /Y /E /I "..\icons" "app\icons" >nul

echo 2/3 Instalando dependencias (la 1a vez tarda unos minutos)...
call npm install
if errorlevel 1 ( echo. & echo ERROR en "npm install". Revisa Node.js. & pause & exit /b )

echo 3/3 Construyendo instalador y portable...
call npm run dist
if errorlevel 1 ( echo. & echo ERROR en la construccion. Mira el mensaje de arriba. & pause & exit /b )

echo.
echo  LISTO. En la carpeta  %~dp0dist\  tienes:
echo    - "Visor IFC Setup 1.2.0.exe"   ^<- INSTALADOR para ti y tus companeros
echo    - "Visor IFC portable.exe"      ^<- version portable (sin instalar)
echo.
echo  El instalador crea el acceso directo "Visor IFC" y se puede repartir a tus companeros.
echo  La 1a vez Windows SmartScreen puede avisar: "Mas informacion" -^> "Ejecutar de todos modos".
echo.
pause
