@echo off
REM === Crea/actualiza el icono "Visor IFC" del Escritorio para la APP de escritorio (Electron) ===
cd /d "%~dp0"
set "TARGET=%~dp0Abrir Visor IFC (app).vbs"
set "ICON=%~dp0assets\icon.ico"
set "HERE=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws=New-Object -ComObject WScript.Shell; $dests=@([Environment]::GetFolderPath('Desktop'), '%HERE%'.TrimEnd('\')); foreach($d in $dests){ $p=Join-Path $d 'Visor IFC.lnk'; $l=$ws.CreateShortcut($p); $l.TargetPath='%TARGET%'; $l.WorkingDirectory='%HERE%'; $l.IconLocation='%ICON%'; $l.Description='Visor IFC (app de escritorio)'; $l.Save(); if(Test-Path $p){ Write-Host (' OK -> ' + $p) } else { Write-Host (' ERROR -> ' + $p) } }"
echo.
echo  Icono "Visor IFC" creado en el Escritorio (y en esta carpeta).
echo  Doble clic en el -> abre la app de escritorio (sin servidor, sin consola).
echo.
pause
