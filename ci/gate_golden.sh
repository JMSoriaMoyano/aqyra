#!/usr/bin/env bash
# gate_golden.sh — PUERTA DE COMPATIBILIDAD. Corre la suite golden (C5 v0) contra el oraculo PyNite.
# Uso: antes de adoptar cualquier bump de version. exit 0 = VERDE (adoptar permitido) ; 1 = ROJO (bloquear).
# La golden vive en el lado de gobierno (Estructurando 2.0). Se puede sobreescribir con GOLDEN_RUNNER.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="${GOLDEN_RUNNER:-$HERE/../../Estructurando 2.0/qa/run_golden.py}"
if [ ! -f "$RUNNER" ]; then
  echo "ERROR: no encuentro el runner de la golden en: $RUNNER"
  echo "Define GOLDEN_RUNNER=/ruta/a/run_golden.py y reintenta."
  exit 2
fi
PY="${PYTHON:-python}"
echo ">> Comprobando dependencias (PyNiteFEA, numpy, scipy)…"
"$PY" - <<'PYCHK' || { echo "Falta PyNiteFEA. Instala:  pip install PyNiteFEA --break-system-packages"; exit 2; }
import importlib,sys
for m in ("Pynite","numpy","scipy"):
    importlib.import_module(m)
print("   deps OK")
PYCHK
echo ">> Ejecutando la golden…"
if "$PY" "$RUNNER"; then
  echo "PUERTA: VERDE — adopcion permitida."
  exit 0
else
  echo "PUERTA: ROJO — NO adoptar. Corrige el build hasta que la golden pase (no aflojes tolerancia)."
  exit 1
fi
