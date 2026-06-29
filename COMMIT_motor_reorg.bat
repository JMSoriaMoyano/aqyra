@echo off
chcp 65001 >nul
setlocal
title aqyra-motor: commit del reinicio organizativo (reorg 2026-06-29)

set "REPO=C:\Users\jmsor\Documents\Claude\Projects\Estructurando"
set "URL=https://github.com/JMSoriaMoyano/aqyra-motor.git"
set "LOG=%REPO%\_operativo\motor_reorg_resultado.txt"

cd /d "%REPO%" || (echo No se encuentra el repo: %REPO% & pause & exit /b 1)
if not exist "%REPO%\_operativo" mkdir "%REPO%\_operativo"

echo ===== aqyra-motor: commit del reinicio organizativo =====> "%LOG%"
echo Fecha: %DATE% %TIME%>> "%LOG%"

REM --- 0) Higiene: lock huerfano ---
if exist ".git\index.lock" del /f /q ".git\index.lock"

REM --- 1) .gitattributes + .gitignore, renormalizar EOL y stage de todo ---
git add .gitattributes .gitignore >> "%LOG%" 2>&1
git add --renormalize . >> "%LOG%" 2>&1
git add -A >> "%LOG%" 2>&1

REM --- 1b) GUARDIA DE LA ZONA FIRMADA: el manifiesto y su .asc NO se tocan ---
echo.>> "%LOG%"
echo --- guardia zona firmada (debe estar vacio) --->> "%LOG%"
git diff --cached --name-only | findstr /I /R "release\.manifest\.json N1\.1\.sha256" >> "%LOG%" 2>&1
if errorlevel 1 goto :firma_ok
echo [GUARDIA] La renormalizacion rozo la zona firmada. Se desestagea y se conserva intacta.>> "%LOG%"
git reset -- release.manifest.json release.manifest.json.asc N1.1.sha256 >> "%LOG%" 2>&1
:firma_ok
echo (zona firmada protegida = OK)>> "%LOG%"

REM --- 2) PUERTA DE SECRETOS sobre lo staged ---
echo.>> "%LOG%"
echo --- chequeo de secretos en staging (debe estar vacio) --->> "%LOG%"
git diff --cached --name-only | findstr /I /R "\.env node_modules/ \.key$ \.pem$ secrets\. token credential" >> "%LOG%" 2>&1
if errorlevel 1 goto :sin_secretos
echo.>> "%LOG%"
echo [ABORTADO] Posible SECRETO en staging. NO se commitea ni sube.>> "%LOG%"
git reset >> "%LOG%" 2>&1
echo.
echo ###############################################################
echo  ABORTADO: posible secreto en staging. Revisa: %LOG%
echo ###############################################################
type "%LOG%"
echo.
pause
exit /b 2

:sin_secretos
echo (sin secretos en staging = OK)>> "%LOG%"

REM --- 3) Que se va a commitear ---
echo.>> "%LOG%"
echo --- staged: git diff --cached --stat --->> "%LOG%"
git diff --cached --stat >> "%LOG%" 2>&1

REM --- 4) Commit ---
git commit -m "reorg: reinicio organizativo (opcion B) - hilos cerrados (INICIO-hilo PT*) a _historial/, .bat+logs a _operativo/ (.gitignore); raiz de docs vivos. Zona firmada (release.manifest.json/.asc, N1.1.sha256) intacta." >> "%LOG%" 2>&1
set "RC=%errorlevel%"

REM --- 5) Push a origin main ---
echo.>> "%LOG%"
echo --- git push origin main --->> "%LOG%"
git push origin main >> "%LOG%" 2>&1
set "RCP=%errorlevel%"

echo.>> "%LOG%"
echo --- estado final --->> "%LOG%"
git status -sb >> "%LOG%" 2>&1
git log -1 --oneline >> "%LOG%" 2>&1

echo.
if not "%RC%"=="0" goto :commit_warn
if not "%RCP%"=="0" goto :push_warn
echo ============================================================
echo  COMMIT + PUSH OK. Revisa: %LOG%
echo ============================================================
goto :fin

:commit_warn
echo ============================================================
echo  AVISO: el commit devolvio codigo %RC% (quiza "nothing to commit"). Revisa: %LOG%
echo ============================================================
goto :fin

:push_warn
echo ============================================================
echo  Commit OK, pero el PUSH devolvio %RCP%. Causas: login o red. Revisa: %LOG%
echo ============================================================

:fin
echo.
type "%LOG%"
echo.
pause
