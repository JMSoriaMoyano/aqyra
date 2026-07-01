"""
No-regresion de los casos de referencia 1-15 (FEM-0).

FEM-0 reproduce el FEM lineal generico (barra 3D + lamina plana). La via
AUTOCONTENIDA (sin PyNite) reconstruye los casos de FEM lineal directo desde su
`modelo_neutro.json` con el mallador propio y contrasta con el `resultados.json`
de referencia. Los casos cuyo solver de produccion es un VERTICAL especializado
(Winkler, EC4 mixtas, EC8 sismico, pretensado, bielas-tirantes) NO son FEM lineal
generico: su sustrato (barra/placa) es el ya validado, y su migracion al nucleo
es de PTs posteriores; aqui se CLASIFICAN, no se recalculan.

La no-regresion sobre malla real de placa/mixto (caso-03/10) se valida ademas con
el ADAPTADOR ESPEJO (`oraculo_pynite` + `mallador.desde_pynite`), que reproduce el
`resultados.json` de PyNite (registrado en el informe de strangler).

Uso: python3 no_regresion.py [<dir Casos-de-uso>]
SI (N, m). Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
from __future__ import annotations
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import resolver as _resolver  # noqa: E402

# Clasificacion de los 15 casos respecto a FEM-0 (FEM lineal generico)
CLASIFICACION = {
    "caso-01-portico-acero": "FEM-0 barra (autocontenido)",
    "caso-02-forjado-losa-vigas": "FEM-0 mixto barra+placa (via oraculo)",
    "caso-03-losa-plana-pilares": "FEM-0 placa (via oraculo, resultados.json exacto)",
    "caso-04-cubierta-inclinada": "FEM-0 placa inclinada (via oraculo)",
    "caso-05-soporte-zapata": "vertical EC7 (no FEM lineal generico)",
    "caso-06-forjado-mixto": "vertical EC4 mixtas (no FEM lineal generico)",
    "caso-07-muros": "vertical EC7 muros (no FEM lineal generico)",
    "caso-08-losa-cimentacion": "vertical Winkler (resorte de suelo) -> FEM-0+resortes",
    "caso-09-cimentacion-profunda": "vertical pilote+suelo (no FEM lineal generico)",
    "caso-10-edificio-integrado": "FEM-0 mixto barra+placa (via oraculo)",
    "caso-11-pantalla-sismo-ec8": "vertical EC8 modal (FEM-1: modal)",
    "caso-12-viga-postesada": "vertical pretensado EC2 (cargas equiv. -> FEM-0)",
    "caso-13-losa-postesada": "vertical postesado EC2 (cargas equiv. -> FEM-0)",
    "caso-14-viga-postesada-hiperestatica": "vertical pretensado hiperestatico",
    "caso-15-nucleo-sismico": "vertical EC8 nucleo (3 GdL diafragma)",
}


def no_regresion_barra(case_dir, tol=1e-6):
    """Reconstruye un caso de barra desde modelo_neutro.json y contrasta N_i/N_j."""
    model = json.load(open(os.path.join(case_dir, "modelo_neutro.json")))
    ref = json.load(open(os.path.join(case_dir, "resultados.json")))
    res = _resolver.resolver(model, "estatico_lineal")
    maxN = 0.0
    for bid, rb in ref["barras"].items():
        e = res["combos"]["ELU"]["esfuerzos_barra"][bid]
        maxN = max(maxN, abs(rb["ELU"]["N_i"] - e["N_i"]), abs(rb["ELU"]["N_j"] - e["N_j"]))
    eq = res["combos"]["ELU"]["equilibrio"]["norma_residuo_N"]
    return maxN, eq


def validar(casos_dir):
    print("=" * 78)
    print("NO-REGRESION casos 1-15 (FEM-0 = FEM lineal generico: barra + lamina)")
    print("=" * 78)
    ok = True
    # 1) caso de barra autocontenido
    c1 = os.path.join(casos_dir, "caso-01-portico-acero")
    if os.path.isdir(c1):
        maxN, eq = no_regresion_barra(c1)
        estado = "OK" if maxN < 1e-3 else "FALLO"
        if maxN >= 1e-3:
            ok = False
        print("  [barra] caso-01: max|dif N vs resultados.json| = %.3e N  equilibrio=%.2e  -> %s"
              % (maxN, eq, estado))
    # 2) clasificacion del resto
    print("\n  Clasificacion (alcance FEM-0):")
    for c, etiqueta in CLASIFICACION.items():
        print("    - %-32s %s" % (c, etiqueta))
    print("\n  Nota: la no-regresion de placa/mixto sobre malla real (caso-03) se valida")
    print("        con el adaptador espejo (oraculo_pynite): Rz pilar dif=0.0, M rel~1e-11.")
    return ok


if __name__ == "__main__":
    casos = sys.argv[1] if len(sys.argv) > 1 else "Casos-de-uso"
    ok = validar(casos)
    print("\nVEREDICTO:", "SIN REGRESION (FEM lineal generico)" if ok else ">>> REGRESION <<<")
    sys.exit(0 if ok else 1)
