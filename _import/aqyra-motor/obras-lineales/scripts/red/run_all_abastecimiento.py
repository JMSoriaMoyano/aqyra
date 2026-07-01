"""
RUN_ALL -- ABASTECIMIENTO de agua (red a PRESION, EN 805). Disciplina
`obras-lineales`, PT 6.3 (Ola 6). Gemelo a presion de `run_all_obras_hidraulicas.py`
(saneamiento, lamina libre). Orquesta el flujo de calculo de una red de
DISTRIBUCION a presion sobre el MODELO NEUTRO DE RED (emitido por el parser MEP de
iso19650-openbim, dominio abastecimiento WATERSUPPLY):

  modelo neutro de red (JSON)
    -> bases_abastecimiento.aplicar_demanda  (caudales EN 805 + hidrante + fuente)
    -> solver_presion.resolver               (Darcy-Weisbach; arbol desde la fuente
                                              + Hardy-Cross en mallas; presion/velocidad)
    -> verificacion_red_presion.verificar    (balance nodal + presiones/velocidades)
    -> resultado_red_presion.construir_mapping  (write-back Pset, no bloqueante)

Rellena ademas el GANCHO `red` del propio modelo de salida (resumen del veredicto y
de la presion de la fuente), homogeneo con los ganchos `firme`/`drenaje`/`red`
(saneamiento) del modelo neutro lineal. STDLIB PURA (no abre IFC).

Uso:  python3 run_all_abastecimiento.py modelo_neutro_red.json [outdir]
        [--dotacion 200] [--punta 2.5] [--pmin 250] [--vmax 2.0]
        [--fuente deposito|bombeo] [--pbombeo 500]
        [--incendio 1|0] [--qincendio 16.7] [--kacc 1.2]
Predimensionado/asistencia; revisar y firmar por tecnico competente (ICCP).

NDP de comprobacion (paquete EN 805 por defecto, [confirmar AN]):
  velocidad 0.5-2.0 m/s (anti-estancamiento <-> anti-golpe de ariete/erosion),
  presion dinamica minima 250 kPa en acometida/hidrante, DN minimo del catalogo.
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import bases_abastecimiento       # noqa: E402
import solver_presion            # noqa: E402
import verificacion_red_presion  # noqa: E402
import resultado_red_presion     # noqa: E402

# Bandas de velocidad de abastecimiento (EN 805, NDP [confirmar AN]).
V_MIN_DEF = 0.5   # m/s (anti-estancamiento/sedimentacion)
V_MAX_DEF = 2.0   # m/s (anti-golpe de ariete / erosion)
DN_MIN_DEF_MM = 80.0  # DN minimo de red de distribucion [confirmar AN]


def _comprob_extra(res, v_min, dn_min):
    """Comprobaciones propias del abastecimiento que el solver Darcy (pensado para
    PCI, solo v_max) no incluye: velocidad MINIMA (anti-estancamiento) y DN MINIMO.
    Devuelve (errores, avisos) anadidos al veredicto."""
    errores, avisos = [], []
    for tid, to in res.get("tramos", {}).items():
        v = to.get("velocidad_m_s")
        dn = to.get("dn")
        if v is not None and v > 0 and v < v_min:
            avisos.append("Tramo %s (%s): velocidad %.2f m/s < v_min %.1f m/s "
                          "(riesgo de estancamiento) [confirmar AN]."
                          % (tid, to.get("elemento", tid), v, v_min))
        if dn is not None and float(dn) < dn_min:
            errores.append("Tramo %s (%s): DN %.0f mm < DN minimo %.0f mm."
                           % (tid, to.get("elemento", tid), float(dn), dn_min))
    return errores, avisos


def run(modelo, dotacion=bases_abastecimiento.DOTACION_L_HAB_DIA,
        punta=bases_abastecimiento.COEF_PUNTA,
        pmin=bases_abastecimiento.PRESION_MIN_KPA,
        vmax=V_MAX_DEF, vmin=V_MIN_DEF, dn_min=DN_MIN_DEF_MM,
        tipo_fuente="deposito", pbombeo=bases_abastecimiento.PRESION_BOMBEO_DEF_KPA,
        incendio=True, qincendio=bases_abastecimiento.CAUDAL_INCENDIO_L_S,
        kacc=solver_presion.K_ACC_DEF):
    m = bases_abastecimiento.aplicar_demanda(
        modelo, dotacion=dotacion, coef_punta=punta, presion_min=pmin,
        tipo_fuente=tipo_fuente, presion_bombeo=pbombeo,
        incluir_incendio=incendio, caudal_incendio=qincendio)
    res = solver_presion.resolver(m, k_acc=kacc, v_max=vmax)
    # adjuntar el Name del elemento a cada tramo (write-back/legibilidad)
    for tid, to in res.get("tramos", {}).items():
        to["elemento"] = (m.get("tramos", {}).get(tid, {}) or {}).get("elemento", tid)
    # comprobaciones extra de abastecimiento (v_min, DN minimo)
    err_extra, av_extra = _comprob_extra(res, vmin, dn_min)
    res.setdefault("errores", []).extend(err_extra)
    res.setdefault("avisos", []).extend(av_extra)
    if err_extra and res.get("veredicto") == "CUMPLE":
        res["veredicto"] = "NO CUMPLE"

    ver = verificacion_red_presion.verificar(m, res)
    mapping = resultado_red_presion.construir_mapping(m, res)

    # gancho `red` (resumen) del modelo neutro de salida
    m["red"] = {
        "norma": "EN 805",
        "disciplina": "abastecimiento",
        "metodo": "Darcy-Weisbach a presion (grafo de red)",
        "tipo_fuente": tipo_fuente,
        "veredicto": ver["veredicto"],
        "presion_fuente_disponible_kPa": res.get("presion_fuente_disponible_kPa"),
        "presion_fuente_requerida_kPa": res.get("presion_fuente_requerida_kPa"),
        "margen_fuente_kPa": res.get("margen_fuente_kPa"),
        "velocidad_pico_m_s": res.get("velocidad_pico_m_s"),
        "banda_velocidad_m_s": [vmin, vmax],
        "presion_min_kPa": pmin,
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
    flags_num = {"--dotacion": "dotacion", "--punta": "punta", "--pmin": "pmin",
                 "--vmax": "vmax", "--vmin": "vmin", "--dn-min": "dn_min",
                 "--pbombeo": "pbombeo", "--qincendio": "qincendio", "--kacc": "kacc"}
    while i < len(rest):
        a = rest[i]
        if a in flags_num:
            kw[flags_num[a]] = float(rest[i + 1]); i += 2
        elif a == "--fuente":
            kw["tipo_fuente"] = rest[i + 1]; i += 2
        elif a == "--incendio":
            kw["incendio"] = (str(rest[i + 1]) not in ("0", "no", "false", "False")); i += 2
        else:
            outdir = a; i += 1
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
    print("ABASTECIMIENTO A PRESION (EN 805) --", res.get("topologia"))
    print("=" * 66)
    print(" Topologia:", res["topologia"])
    print(" Fuente (%s): disponible=%s kPa | requerida=%s kPa | margen=%s kPa"
          % (m["red"]["tipo_fuente"], res["presion_fuente_disponible_kPa"],
             res["presion_fuente_requerida_kPa"], res["margen_fuente_kPa"]))
    print(" Velocidad pico: %.3f m/s (banda %s)"
          % (res["velocidad_pico_m_s"], m["red"]["banda_velocidad_m_s"]))
    print(" Solver:", res["veredicto"], "| Verificacion:", ver["veredicto"])
    for w in res.get("avisos", []):
        print("   !", w)
    for e in ver["errores"]:
        print("   X", e)
    print(" Resultados escritos en", outdir)
    print("\nVEREDICTO:", ver["veredicto"])
    return 0 if ver["veredicto"] == "CUMPLE" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
