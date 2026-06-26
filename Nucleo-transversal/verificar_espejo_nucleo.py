#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verificar_espejo_nucleo.py -- Puerta de IDENTIDAD del nucleo transversal espejado.

El nucleo (`scripts/nucleo/`: ifc_utils.py + grafo_red.py [+ test/README]) es
CANONICO en el motor (motor-calculo-estructural) y se ESPEJA, byte a byte, a cada
plugin que lo consume (iso19650-openbim, instalaciones). Como el aislamiento de
runtime impide importarlo entre plugins, los espejos DEBEN ser identicos al canonico
(decision nº4 / INC-10). Esta puerta lo verifica por hash y FALLA (exit!=0) si algun
espejo DIVERGE, FALTA o SOBRA un .py respecto al canonico.

Acepta .plugin (ZIP) o carpetas. Compara el subarbol `scripts/nucleo/`.

Uso:
  python3 verificar_espejo_nucleo.py --canonico <motor.plugin|dir> <espejo1> [espejo2 ...]
  (opcional) --solo-py   : ignora ficheros no .py (README, etc.) en el contraste.

Salida: informe + exit 0 (espejos identicos) / 1 (divergencia) / 2 (error de uso).
Solo stdlib. Ejecutar en sandbox con PYTHONPATH=/tmp/pylibs (no usa libs externas).
"""
import argparse
import hashlib
import os
import sys
import tempfile
import zipfile

SUBDIR = "scripts/nucleo"


def _abrir(path, dest):
    """Devuelve la ruta a un arbol en disco: si es .plugin/zip lo extrae a dest."""
    if os.path.isdir(path):
        return path
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            z.extractall(dest)
        return dest
    raise ValueError("ni carpeta ni ZIP: %s" % path)


def _nucleo_files(raiz, solo_py=False):
    """{ruta_relativa_a_scripts/nucleo: md5} de los ficheros del nucleo."""
    base = None
    for r, _d, _f in os.walk(raiz):
        if r.replace(os.sep, "/").endswith(SUBDIR):
            base = r
            break
    out = {}
    if base is None:
        return out, None
    for r, _d, files in os.walk(base):
        for f in files:
            if solo_py and not f.endswith(".py"):
                continue
            if f.endswith(".pyc") or "__pycache__" in r:
                continue
            ab = os.path.join(r, f)
            rel = os.path.relpath(ab, base).replace(os.sep, "/")
            out[rel] = hashlib.md5(open(ab, "rb").read()).hexdigest()
    return out, base


def main():
    ap = argparse.ArgumentParser(description="Puerta de identidad del nucleo espejado.")
    ap.add_argument("--canonico", required=True, help=".plugin o carpeta con el nucleo canonico")
    ap.add_argument("espejos", nargs="+", help=".plugin(s) o carpeta(s) con espejos a verificar")
    ap.add_argument("--solo-py", action="store_true", help="contrasta solo ficheros .py")
    a = ap.parse_args()

    tmps = []

    def abrir(p):
        d = tempfile.mkdtemp(prefix="esp_nuc_")
        tmps.append(d)
        return _abrir(p, d)

    try:
        can_root = abrir(a.canonico)
        can, can_base = _nucleo_files(can_root, a.solo_py)
        print("=" * 70)
        print("VERIFICACION DE IDENTIDAD DEL NUCLEO ESPEJADO")
        print("=" * 70)
        if not can:
            print("  X  canonico sin %s: %s" % (SUBDIR, a.canonico))
            sys.exit(2)
        print("  canonico (%s): %d ficheros" % (a.canonico, len(can)))
        for rel, h in sorted(can.items()):
            print("     %s  %s" % (h, rel))

        errores = []
        for esp in a.espejos:
            root = abrir(esp)
            files, _b = _nucleo_files(root, a.solo_py)
            if not files:
                errores.append("espejo SIN %s: %s" % (SUBDIR, esp))
                continue
            faltan = sorted(set(can) - set(files))
            sobran = sorted(set(files) - set(can))
            difieren = sorted(r for r in (set(can) & set(files)) if can[r] != files[r])
            estado = "IDENTICO" if not (faltan or sobran or difieren) else "DIVERGE"
            print("\n  espejo %s -> %s" % (esp, estado))
            for r in difieren:
                errores.append("%s : %s DIFIERE (canonico %s vs espejo %s)"
                               % (esp, r, can[r][:8], files[r][:8]))
                print("     X DIFIERE   %s" % r)
            for r in faltan:
                errores.append("%s : falta %s" % (esp, r))
                print("     X FALTA     %s" % r)
            for r in sobran:
                errores.append("%s : sobra %s" % (esp, r))
                print("     ! SOBRA     %s" % r)

        print("\nVEREDICTO:", "ESPEJOS IDENTICOS" if not errores else ">>> DIVERGENCIA <<<")
        if errores:
            print("PROBLEMAS (%d):" % len(errores))
            for e in errores:
                print("  X ", e)
        sys.exit(1 if errores else 0)
    finally:
        pass


if __name__ == "__main__":
    main()
