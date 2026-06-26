@echo off
REM Convierte un .ifc a fragments + indice por GlobalId en la carpeta models\.
REM Uso:  convertir_ifc.bat  ruta\al\modelo.ifc  [nombre_base]
REM Requiere haber ejecutado antes instalar_dependencias.bat una vez.
cd /d "%~dp0"
if "%~1"=="" (
  echo Uso: convertir_ifc.bat ruta\al\modelo.ifc [nombre_base]
  pause & exit /b 1
)
set "BASE=%~2"
if "%BASE%"=="" set "BASE=%~n1"
echo Convirtiendo "%~1"  ->  models\%BASE%.frag  +  models\%BASE%.props.json
node pipeline.mjs "%~1" "models" "%BASE%"
echo.
echo Si es un modelo nuevo, anade una linea en models\manifest.json:
echo   { "id":"%BASE%", "label":"%BASE%", "frag":"models/%BASE%.frag", "props":"models/%BASE%.props.json" }
pause
