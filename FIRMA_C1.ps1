# FIRMA_C1.ps1 v2 - sella la evolucion de C1 "apertura familias P1" (dos llaves).
# Idempotente y seguro de RELANZAR: salta lo ya hecho (commit/tag) y continua.
# Llave 1 = golden C1-APERTURA-01 VERDE. Llave 2 = tu firma GPG (tags).
$ErrorActionPreference = 'Continue'   # NO tratar el stderr normal de git como error fatal
$root    = $PSScriptRoot
$motor   = Join-Path $root '..\Estructurando'
$golden  = Join-Path $root '..\Estructurando 2.0'
$entorno = Join-Path $root '..\Entorno'
$entrega = Join-Path $root 'ENTREGA_C1-apertura'
$log     = Join-Path $root 'FIRMA_C1_resultado.txt'
$ver     = '0.10.0'
$fecha   = '2026-06-28'
"FIRMA C1 v2 - $(Get-Date)" | Out-File -FilePath $log -Encoding utf8

function L($m){ $m | Out-File -FilePath $log -Append }
function G([string]$repo,[string[]]$a){ $o = & git -C $repo @a 2>&1; $o | Out-File -FilePath $log -Append; return $LASTEXITCODE }
function Fail($m){ L ("ERROR: " + $m); L 'Si git no encuentra tu gpg: git config --global gpg.program "C:\Program Files\GnuPG\bin\gpg.exe"'; Write-Host ("ERROR: " + $m + "  -> revisa FIRMA_C1_resultado.txt"); exit 1 }

function Seal($repo,[string[]]$addArgs,$commitMsg,$tag,$tagMsg){
  Remove-Item (Join-Path $repo '.git\index.lock') -ErrorAction SilentlyContinue
  if ((G $repo (@('add') + $addArgs)) -ne 0){ Fail ("add fallo en " + $repo) }
  $staged = & git -C $repo diff --cached --name-only
  $staged | Out-File -FilePath $log -Append
  if ($staged -match '\.env|node_modules/|\.key$|\.pem$|secrets'){ & git -C $repo reset | Out-Null; Fail ("SECRETO detectado en " + $repo) }
  & git -C $repo diff --cached --quiet
  if ($LASTEXITCODE -ne 0){ if ((G $repo @('commit','-m',$commitMsg)) -ne 0){ Fail ("commit fallo en " + $repo) } }
  else { L ("(nada nuevo que commitear en " + $repo + ", ya estaba)") }
  if ($tag){
    & git -C $repo rev-parse -q --verify ("refs/tags/" + $tag) *> $null
    if ($LASTEXITCODE -ne 0){ if ((G $repo @('tag','-s',$tag,'-m',$tagMsg)) -ne 0){ Fail ("tag firmado fallo en " + $repo + " (passphrase/gpg?)") } }
    else { L ("(tag " + $tag + " ya existe en " + $repo + ")") }
  }
  if ((G $repo @('push','origin','main')) -ne 0){ Fail ("push main fallo en " + $repo) }
  if ($tag){ if ((G $repo @('push','origin',("refs/tags/" + $tag))) -ne 0){ Fail ("push tag fallo en " + $repo) } }
}

# ---------- 1) aqyra-motor: codigo + contrato C1 ----------
L "===== MOTOR (Estructurando) ====="
Seal $motor @('narracion-ifc','iso19650-openbim/scripts/lineal/generate_test_ifc_lineal.py','iso19650-openbim/.claude-plugin/plugin.json','iso19650-openbim/CHANGELOG.md','Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md') `
  ("C1 apertura familias P1 (iso19650-openbim " + $ver + "): huecos generalizados + catalogo de clases abierto + doble clasificacion bsDD+Uniclass + alineaciones completas + alto.json forward-open; golden C1-APERTURA-01 verde") `
  ("c1-evolucion-" + $fecha) ("C1 apertura familias P1 - iso19650-openbim " + $ver + " - golden C1-APERTURA-01 VERDE")

# ---------- 2) aqyra-contratos-golden: golden de record ----------
L "===== GOLDEN (Estructurando 2.0) ====="
$gdir = Join-Path $golden 'contratos-golden\golden'
if (-not (Test-Path $gdir)){ New-Item -ItemType Directory -Path $gdir | Out-Null }
Copy-Item (Join-Path $entrega 'FICHA_golden_C1-APERTURA-01.md')  $gdir -Force
Copy-Item (Join-Path $entrega 'golden_C1-APERTURA-01.alto.json') $gdir -Force
Copy-Item (Join-Path $entrega 'golden_C1-APERTURA-01.spec.json') $gdir -Force
Copy-Item (Join-Path $entrega 'golden_C1-APERTURA-01.ifc')       $gdir -Force
Copy-Item (Join-Path $entrega 'RESULTADO_oraculo.txt') (Join-Path $gdir 'C1-APERTURA-01_oraculo.txt') -Force
$readme = Join-Path $golden 'contratos-golden\README.md'
if (-not (Select-String -Path $readme -SimpleMatch 'C1-APERTURA-01' -Quiet)){ Add-Content $readme ("`n- " + $fecha + " - Golden **C1-APERTURA-01** registrada (C1 apertura familias P1, iso19650-openbim " + $ver + "): Llave 1 VERDE + firma JM.") }
Seal $golden @('contratos-golden/golden','contratos-golden/README.md') `
  ("Golden de record C1-APERTURA-01 (Llave 1 verde) + registro; C1 apertura familias P1 (iso19650-openbim " + $ver + ")") `
  ("c1-golden-" + $fecha) ("Golden C1-APERTURA-01 VERDE - C1 apertura familias P1 - iso19650-openbim " + $ver)

# ---------- 3) aqyra-entorno: anclar versions.lock ----------
L "===== ENTORNO (versions.lock) ====="
$lock = Join-Path $entorno 'integracion\versions.lock'
$nl = 'iso19650-openbim:     "' + $ver + '"   # C1 v0 apertura familias P1 (huecos/clases/alineaciones/doble clasif/forward-open) - golden C1-APERTURA-01 verde + firma JM ' + $fecha
(Get-Content $lock) -replace 'iso19650-openbim:\s*"0\.8\.2".*', $nl | Set-Content $lock
Seal $entorno @('integracion/versions.lock') ("Anclar iso19650-openbim " + $ver + " (C1 apertura familias P1; golden C1-APERTURA-01 verde + firmada)") $null $null

# ---------- 4) verificar firmas ----------
L "===== VERIFY ====="
(& git -C $motor  tag -v ("c1-evolucion-" + $fecha) 2>&1) | Out-File -FilePath $log -Append
(& git -C $golden tag -v ("c1-golden-" + $fecha)    2>&1) | Out-File -FilePath $log -Append
L ""
L ("OK: motor + contratos-golden firmados y subidos; versions.lock anclado a " + $ver + ".")
Write-Host "LISTO. Revisa FIRMA_C1_resultado.txt"
