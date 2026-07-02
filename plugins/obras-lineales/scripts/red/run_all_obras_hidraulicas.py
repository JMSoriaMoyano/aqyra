"""
RUN_ALL -- OBRAS HIDRAULICAS DE RED (saneamiento, lamina libre). Disciplina
`obras-lineales`, PT 6.2 (Ola 6). Orquesta el flujo de calculo de una red de
COLECTORES sobre el MODELO NEUTRO DE RED (emitido por el parser MEP de
iso19650-openbim, dominio saneamiento):

  modelo neutro de red (JSON)
    -> bases_saneamiento.aplicar_demanda  (caudales de aguas residuales, EN 752)
    -> solver_lamina_libre.resolver       (Manning, calado/velocidad/llenado por tramo)
    -> verificacion_red_lineal.verificar  (balance nodal + comprobaciones)
    -> resultado_red_lineal.construir_mapping  (write-back Pset, no bloqueante)

Rellena ademas el GANCHO `red` del propio modelo de salida (resumen del veredicto y
del caudal vertido), homogeneo con los ganchos `firme`/`drenaje` del modelo neutro
lineal. STDLIB PURA (no abre IFC).

Uso:  python3 run_all_obras_hidraulicas.py modelo_neutro_red.json [outdir]
        [--dotacion 200] [--punta 2.5] [--retorno 0.8] [--infiltracion 0]
        [--fill-max 0.75] [--vmin 0.6] [--vmax 5.0] [--dn-min 300]
Predimensionado/asistencia; revisar y firmar por tecnico competente (ICCP).
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import bases_saneamiento        # noqa: E402
import solver_lamina_libre      # noqa: E402
import verificacion_red_lineal  # noqa: E402
import resultado_red_lineal     # noqa: E402


def run(modelo, dotacion=bases_saneamiento.DOTACION_L_HAB_DIA,
        punta=bases_saneamiento.COEF_PUNTA, retorno=bases_saneamiento.COEF_RETORNO,
        infiltracion=bases_saneamiento.Q_INFILTRACION_L_S,
        fill_max=solver_lamina_libre.FILL_MAX_DEF,
        vmin=solver_lamina_libre.V_MIN_DEF, vmax=solver_lamina_libre.V_MAX_DEF,
        dn_min=solver_lamina_libre.DN_MIN_DEF_MM):
    m = bases_saneamiento.aplicar_demanda(modelo, regimen="residuales",
                                          dotacion=dotacion, retorno=retorno,
                                          coef_punta=punta, q_infiltracion=infiltracion)
    res = solver_lamina_libre.resolver(m, fill_max=fill_max, v_min=vmin,
                                       v_max=vmax, dn_min_mm=dn_min)
    for tid, to in res.get("tramos", {}).items():
        to["elemento"] = (m.get("tramos", {}).get(tid, {}) or {}).get("elemento", tid)
    ver = verificacion_red_lineal.verificar(m, res)
    mapping = resultado_red_lineal.construir_mapping(m, res)

    # gancho `red` (resumen) del modelo neutro de salida
    m["red"] = {
        "norma": "EN 752",
        "regimen": (m.get("sistema", {}).get("demanda") or {}).get("regimen"),
        "metodo": "Manning lamina libre (grafo de red)",
        "veredicto": ver["veredicto"],
        "caudal_total_vertido_l_s": res.get("caudal_total_vertido_l_s"),
        "velocidad_pico_m_s": res.get("velocidad_pico_m_s"),
        "llenado_pico_pct": res.get("llenado_pico_pct"),
        "n_tramos_no_cumple": ver.get("n_tramos_no_cumple"),
        "topologia": res.get("topologia"),
    }
    return m, res, ver, mapping


def main(argv):
    if not argv:
        print(__doc__); return 2
    modelo_path = argv[0]
    outdir = None
    kw = {}
    rest = argv[1:]; i = 0
    flags = {"--dotacion": "dotacion", "--punta": "punta", "--retorno": "retorno",
             "--infiltracion": "infiltracion", "--fill-max": "fill_max",
             "--vmin": "vmin", "--vmax": "vmax", "--dn-min": "dn_min"}
    while i < len(rest):
        if rest[i] in flags:
            kw[flags[rest[i]]] = float(rest[i + 1]); i += 2
        else:
            outdir = rest[i]; i += 1
    with open(modelo_path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    m, res, ver, mapping = run(modelo, **kw)

    outdir = outdir or "."
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(modelo_path))[0]
    for nombre, obj in (("modelo_red_resuelto", m), ("resultado_red", res),
                        ("verificacion_red", ver), ("mapping_resultado_red", mapping)):
        with open(os.path.join(outdir, "%s_%s.json" % (base, nombre)), "w",
                  encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False)

    print("=" * 66)
    print("OBRAS HIDRAULICAS DE RED (SANEAMIENTO) --", res.get("sistema"))
    print("=" * 66)
    print(" Topologia:", res["topologia"])
    print(" Caudal total vertido: %.3f l/s" % res["caudal_total_vertido_l_s"])
    print(" Velocidad pico: %.3f m/s | llenado pico: %.1f %%"
          % (res["velocidad_pico_m_s"], res["llenado_pico_pct"]))
    print(" Solver:", res["veredicto"], "| Verificacion:", ver["veredicto"])
    for e in ver["errores"]:
        print("   X", e)
    print(" Resultados escritos en", outdir)
    print("\nVEREDICTO:", ver["veredicto"])
    return 0 if ver["veredicto"] == "CUMPLE" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
