@echo off
chcp 65001 >nul
setlocal
title aqyra-contratos-golden: commit del reinicio organizativo (reorg 2026-06-29)

REM ============================================================
REM  NOTA: este es el repo de GOBIERNO. Tu norma es "cambios por PR".
REM  El reordenado solo reubica DOCS (no toca versions.lock, contratos
REM  ni golden). Si prefieres respetar la via PR, NO ejecutes este .bat
REM  y mete el reordenado por una rama + PR. Si aceptas commit directo
REM  para esta tarea de higiene, ejecutalo normalmente.
REM ============================================================

set "REPO=C:\Users\jmsor\Documents\Claude\Projects\Estructurando 2.0"
set "URL=https://github.com/JMSoriaMoyano/aqyra-contratos-golden.git"
set "LOG=%REPO%\_operativo\contratos_reorg_resultado.txt"

cd /d "%REPO%" || (echo No se encuentra el repo: %REPO% & pause & exit /b 1)
if not exist "%REPO%\_operativo" mkdir "%REPO%\_operativo"

echo ===== aqyra-contratos-golden: commit del reinicio organizativo =====> "%LOG%"
echo Fecha: %DATE% %TIME%>> "%LOG%"

REM --- 0) Higiene: lock huerfano ---
if exist ".git\index.lock" del /f /q ".git\index.lock"

REM --- 1) .gitattributes + .gitignore, renormalizar EOL y stage de todo ---
git add .gitattributes .gitignore >> "%LOG%" 2>&1
git add --renormalize . >> "%LOG%" 2>&1
git add -A >> "%LOG%" 2>&1

REM --- 1b) GUARDIA: versions.lock NO debe aparecer staged por una reorg de docs ---
echo.>> "%LOG%"
echo --- guardia versions.lock (debe estar vacio) --->> "%LOG%"
git diff --cached --name-only | findstr /I /R "versions\.lock" >> "%LOG%" 2>&1
if errorlevel 1 goto :lock_ok
echo [GUARDIA] versions.lock aparecio staged (solo EOL). Se desestagea para no tocarlo.>> "%LOG%"
git reset -- versions.lock >> "%LOG%" 2>&1
:lock_ok
echo (versions.lock protegido = OK)>> "%LOG%"

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
git commit -m "reorg: reinicio organizativo (opcion B) - hilos/sprints cerrados a _historial/, .bat+logs a _operativo/ (.gitignore); raiz de docs vivos. versions.lock, contratos y corpus golden intactos." >> "%LOG%" 2>&1
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
