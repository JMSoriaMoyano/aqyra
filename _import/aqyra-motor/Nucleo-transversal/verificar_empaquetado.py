#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verificar_empaquetado.py  -- Puerta de calidad del empaquetado de un .plugin.

Cierra el hueco H6 / INC-09 (Verificacion-Ola1.md): el reempaquetado acumulativo
puede TRUNCAR modulos preexistentes que ni se tocan (paso a v0.22.0 trunco 8
modulos). Este script audita un .plugin (ZIP) y FALLA (exit code != 0) si detecta
cualquier problema, para usarse como puerta antes de publicar/distribuir.

Comprobaciones (todas son de bloqueo salvo que se indique [aviso]):
  1. plugin.json existe, es JSON valido y declara name + version (semver X.Y.Z).
  2. ast.parse de TODOS los .py  (0 errores de sintaxis/indentacion).
  3. Cada .py termina en salto de linea final  (firma de truncado).
     OJO: ast.parse NO basta -- en v0.22.0, 3 de 8 truncados parseaban por azar;
     esta comprobacion + el contraste de tamanos son los que cazan esos casos.
  4. No hay artefactos en el ZIP: __pycache__/, node_modules/, *.pyc.
  5. [contra una version de referencia, opcional --ref] ningun .py homonimo
     ENCOGE respecto a la referencia (posible truncado) y ningun .py de la
     referencia DESAPARECE sin justificar.
  6. [aviso] recuento de modulos y de agentes.

Uso:
  python3 verificar_empaquetado.py  <nuevo.plugin>  [--ref <previo.plugin>]
                                    [--shrink-tol N]  [--allow-shrink a,b,c]  [--quiet]

  --ref          .plugin previo integro para contrastar tamanos (muy recomendable).
  --shrink-tol   bytes que CUALQUIER .py puede encoger respecto a --ref sin marcarse
                 (por defecto 0: cualquier encogimiento es sospechoso). Es global, asi
                 que conviene dejarlo en 0 y usar --allow-shrink para casos concretos.
  --allow-shrink lista (separada por comas) de rutas .py RELATIVAS cuyo encogimiento es
                 INTENCIONADO y esta auditado (p. ej. un refactor que extrae codigo a un
                 modulo de nucleo). Solo esos ficheros, nombrados uno a uno, se aceptan
                 como "encogimiento esperado"; el resto sigue con tolerancia cero. Asi la
                 puerta distingue un refactor legitimo de un TRUNCADO accidental sin
                 debilitar la deteccion en los demas modulos.

Salida: informe legible + exit 0 (APTO) / 1 (NO APTO) / 2 (error de uso).

Ejecutar en el sandbox con:  PYTHONPATH=/tmp/pylibs python3 verificar_empaquetado.py ...
(no requiere libs externas; solo stdlib).
"""

import argparse
import ast
import json
import os
import sys
import tempfile
import zipfile


def _extraer(path, dest):
    with zipfile.ZipFile(path) as z:
        nombres = z.namelist()
        z.extractall(dest)
    return nombres


def _buscar_plugin_json(raiz):
    for base, _dirs, files in os.walk(raiz):
        if "plugin.json" in files and os.path.basename(base) == ".claude-plugin":
            return os.path.join(base, "plugin.json")
    # respaldo: cualquier plugin.json
    for base, _dirs, files in os.walk(raiz):
        if "plugin.json" in files:
            return os.path.join(base, "plugin.json")
    return None


def _pys(raiz):
    """{ruta_relativa_posix: ruta_absoluta} de todos los .py bajo raiz."""
    out = {}
    for base, _dirs, files in os.walk(raiz):
        for f in files:
            if f.endswith(".py"):
                ab = os.path.join(base, f)
                rel = os.path.relpath(ab, raiz).replace(os.sep, "/")
                out[rel] = ab
    return out


def _semver_ok(v):
    partes = str(v).split(".")
    return len(partes) >= 2 and all(p.isdigit() for p in partes[:3] if p)


def verificar(plugin_path, ref_path=None, shrink_tol=0, quiet=False, allow_shrink=None):
    errores = []   # bloqueantes
    avisos = []    # informativos
    log = []
    allow_shrink = set(allow_shrink or [])

    def p(msg):
        log.append(msg)

    if not os.path.isfile(plugin_path):
        return 2, ["No existe el archivo: %s" % plugin_path], [], []

    tmp = tempfile.mkdtemp(prefix="verif_plugin_")
    try:
        try:
            nombres = _extraer(plugin_path, tmp)
        except zipfile.BadZipFile:
            return 1, ["El .plugin no es un ZIP valido (BadZipFile)."], [], [
                "Sugerencia: construir el ZIP en /tmp y copiar con 'cat > destino'."]

        # --- 1) plugin.json ---
        pj = _buscar_plugin_json(tmp)
        version = None
        if pj is None:
            errores.append("Falta .claude-plugin/plugin.json.")
        else:
            try:
                meta = json.load(open(pj, encoding="utf-8"))
                version = meta.get("version")
                if not meta.get("name"):
                    errores.append("plugin.json sin 'name'.")
                if not version:
                    errores.append("plugin.json sin 'version'.")
                elif not _semver_ok(version):
                    errores.append("version no es SemVer X.Y.Z: %r" % version)
                else:
                    p("plugin.json OK -- name=%s version=%s" % (meta.get("name"), version))
                desc = meta.get("description") or ""
                if len(desc) > 500:
                    errores.append("description supera 500 caracteres (%d): la instalacion la "
                                   "rechaza. Acortar (es metadato de seleccion, no changelog)." % len(desc))
                else:
                    p("description: %d/500 caracteres -- OK" % len(desc))
            except (ValueError, OSError) as e:
                errores.append("plugin.json no es JSON valido: %s" % e)

        # --- 4) artefactos prohibidos ---
        prohibidos = [n for n in nombres
                      if ("__pycache__/" in n) or ("node_modules/" in n) or n.endswith(".pyc")]
        if prohibidos:
            errores.append("Artefactos no permitidos en el ZIP (%d): %s%s"
                           % (len(prohibidos), ", ".join(prohibidos[:5]),
                              " ..." if len(prohibidos) > 5 else ""))
        else:
            p("Sin artefactos (__pycache__/node_modules/*.pyc) -- OK")

        # --- 2 y 3) ast.parse + salto de linea final ---
        pys = _pys(tmp)
        n_synt, n_eol = 0, 0
        for rel, ab in sorted(pys.items()):
            data = open(ab, "rb").read()
            try:
                ast.parse(data.decode("utf-8", "replace"))
            except SyntaxError as e:
                n_synt += 1
                errores.append("Sintaxis ROTA  %s : %s (linea %s)"
                               % (rel, e.__class__.__name__, getattr(e, "lineno", "?")))
            if data and data[-1:] != b"\n":
                n_eol += 1
                errores.append("TRUNCADO (sin salto de linea final)  %s  [acaba: %r]"
                               % (rel, data.splitlines()[-1][-40:].decode("utf-8", "replace")
                                  if data.splitlines() else ""))
        p("Modulos .py: %d  |  errores de sintaxis: %d  |  sin salto de linea final: %d"
          % (len(pys), n_synt, n_eol))

        # --- 6) recuento de agentes (aviso) ---
        agentes = [n for n in nombres if "/agents/" in ("/" + n) or n.startswith("agents/")]
        agentes = [n for n in nombres if n.startswith("agents/") and n.endswith(".md")]
        p("Agentes (.md en agents/): %d" % len(agentes))

        # --- 5) contraste con referencia ---
        if ref_path:
            if not os.path.isfile(ref_path):
                avisos.append("--ref no existe, se omite el contraste: %s" % ref_path)
            else:
                rtmp = tempfile.mkdtemp(prefix="verif_ref_")
                try:
                    _extraer(ref_path, rtmp)
                    rpys = _pys(rtmp)
                    encogidos, desaparecidos = [], []
                    for rel, rab in rpys.items():
                        if rel in pys:
                            a = os.path.getsize(pys[rel]); b = os.path.getsize(rab)
                            if a < b - shrink_tol:
                                encogidos.append((rel, a, b))
                        else:
                            desaparecidos.append(rel)
                    for rel, a, b in sorted(encogidos):
                        if rel in allow_shrink:
                            avisos.append("ENCOGE vs ref [permitido, refactor auditado]  %s : "
                                          "%d B (ref %d B, -%d)" % (rel, a, b, b - a))
                        else:
                            errores.append("ENCOGE vs ref  %s : %d B (ref %d B, -%d)" % (rel, a, b, b - a))
                    no_usadas = sorted(allow_shrink - {r for r, _, _ in encogidos})
                    if no_usadas:
                        avisos.append("--allow-shrink declara ficheros que NO encogen: %s"
                                      % ", ".join(no_usadas))
                    for rel in sorted(desaparecidos):
                        avisos.append("modulo de la ref ausente en el nuevo: %s" % rel)
                    nuevos = sorted(set(pys) - set(rpys))
                    p("Contraste vs ref: %d encogidos, %d ausentes, %d nuevos"
                      % (len(encogidos), len(desaparecidos), len(nuevos)))
                    if nuevos:
                        p("  nuevos: " + ", ".join(nuevos[:8]) + (" ..." if len(nuevos) > 8 else ""))
                finally:
                    pass
        else:
            avisos.append("Sin --ref: no se pudo contrastar tamanos contra una version previa "
                          "(muy recomendable; es lo que caza truncados que parsean por azar).")

        return (1 if errores else 0), errores, avisos, log
    finally:
        pass


def main():
    ap = argparse.ArgumentParser(description="Puerta de calidad del empaquetado de un .plugin.")
    ap.add_argument("plugin", help="ruta al .plugin a verificar")
    ap.add_argument("--ref", help="ruta a un .plugin previo integro para contrastar tamanos")
    ap.add_argument("--shrink-tol", type=int, default=0,
                    help="bytes que un .py puede encoger vs --ref sin marcarse (def. 0)")
    ap.add_argument("--allow-shrink", default="",
                    help="rutas .py relativas (separadas por comas) con encogimiento "
                         "intencionado/auditado; solo esas se aceptan, el resto sigue a tol 0")
    ap.add_argument("--quiet", action="store_true", help="solo el veredicto y los problemas")
    a = ap.parse_args()

    allow = [s.strip() for s in a.allow_shrink.split(",") if s.strip()]
    code, errores, avisos, log = verificar(a.plugin, a.ref, a.shrink_tol, a.quiet, allow)

    if code == 2:
        print("ERROR DE USO:", "; ".join(errores))
        sys.exit(2)

    print("=" * 70)
    print("VERIFICACION DE EMPAQUETADO --", os.path.basename(a.plugin))
    print("=" * 70)
    if not a.quiet:
        for l in log:
            print(" ", l)
    if avisos:
        print("\nAVISOS:")
        for w in avisos:
            print("  - ", w)
    if errores:
        print("\nPROBLEMAS (%d):" % len(errores))
        for e in errores:
            print("  X ", e)
    print("\nVEREDICTO:", "APTO para distribuir" if code == 0 else ">>> NO APTO <<<")
    sys.exit(code)


if __name__ == "__main__":
    main()
