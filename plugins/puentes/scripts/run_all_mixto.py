"""
Orquestador e2e del vertical TABLERO MIXTO acero-hormigon (lamina rigidizada
MITC4 + viga de acero como rigidizador offset = interaccion completa + IAP-11 +
FEM-2 + EC3/EC4). PT 7.5 (Ola 7).

Flujo: mixto -> idealizacion (losa de laminas + vigas de acero como rigidizadores
con offset rigido) -> permanentes (g1 losa+acero, g2 pavimento) + LM1 estatico +
modelo de fatiga FLM3 -> motor-fem (estatico por casos + modal informativo) ->
recuperacion del MOMENTO MIXTO de la seccion (|N_acero|*lever + M_acero) ->
EC3 (clase de seccion, abolladura EN 1993-1-5) + EC4 (M_pl,Rd mixto, conexion) +
fatiga basica (EC3-1-9) -> resultado JSON + mapping write-back.

Consume `motor-fem` (C5, FEM-2) por PYTHONPATH; el motor NO se toca. SI (N, m).
Predimensionado/asistencia; revisar y firmar por tecnico competente (ICCP).
"""
from __future__ import annotations
import os, sys, json
_here = os.path.dirname(os.path.abspath(__file__))
for sub in ("idealizacion", "acciones", "comprobacion", "comun", "lectura"):
    sys.path.insert(0, os.path.join(_here, sub))
import mixto as MX
import ec3ec4_mixto
import resultado_ifc_puente
import fem1   # motor-fem (C5)

FLM3_AXLES = [120e3, 120e3, 120e3, 120e3]    # EN 1991-2 FLM3 (480 kN, 4 ejes)


def _aplicar_flm3(M, meta, caso="FAT", vano=0, carril=1):
    """Modelo de fatiga FLM3 (camion de 4 ejes de 120 kN) centrado en el vano,
    sobre el carril indicado. Carga nodal -Z (predim)."""
    xs = meta["xs"]; L = meta["L"]
    xc = (vano + 0.5) * L
    ixc = min(range(len(xs)), key=lambda i: abs(xs[i] - xc))
    cam = meta["caminos"][min(carril - 1, len(meta["caminos"]) - 1)]
    # 4 ejes en torno al centro (~1.2 m de paso) -> nudos vecinos
    for di in (-2, -1, 1, 2):
        ix = min(max(ixc + di, 0), len(xs) - 1)
        M.add_carga_nodal(caso, cam["camino"][ix], [0, 0, -120e3, 0, 0, 0])
    return {"vano": vano, "carril": carril, "Q_total_N": sum(FLM3_AXLES)}


def ejecutar(mixto, nombre_tablero="MIXTO_PUE18"):
    M, meta = MX.construir_mixto(mixto)
    MX.aplicar_peso_propio(M, meta, "G1")
    if mixto.get("g2_N_m2"):
        MX.aplicar_carga_muerta(M, meta, mixto["g2_N_m2"], "G2")
    lm1 = MX.aplicar_lm1_estatico(M, meta, "Q", vano=0)
    flm3 = _aplicar_flm3(M, meta, "FAT", vano=0, carril=1)

    casos = {"ELU": {"G1": 1.35, "Q": 1.35}, "ELS": {"G1": 1.0, "Q": 1.0},
             "FAT": {"FAT": 1.0}}
    if mixto.get("g2_N_m2"):
        casos["ELU"]["G2"] = 1.35; casos["ELS"]["G2"] = 1.0
    est = M.resolver(casos)["combos"]

    try:
        modal = fem1.modal(M, nmodos=8, peso_propio=True)
        fis = [fr for fr in modal["frecuencias_Hz"] if fr > 0.5]
        f1 = fis[0] if fis else (modal["frecuencias_Hz"][-1] if modal["frecuencias_Hz"] else 0.0)
    except Exception as e:
        f1 = 0.0; modal = {"error": str(e)}

    # recuperacion del momento mixto por seccion critica
    secciones = []
    ms = mixto["material_s"]; mh = mixto["material_h"]
    be = ec3ec4_mixto.b_eff_losa(mixto["L"], meta["sep_vigas"]); be = min(be, meta["sep_vigas"])
    pm = MX._seccion_mixta_props(meta["steel"], mixto["t_losa"], be, mh, ms)
    pm["steel"] = meta["steel"]
    mixto_chk = dict(mixto); mixto_chk["sep_vigas"] = meta["sep_vigas"]
    for sc in meta["sec_crit"]:
        ru = MX.esfuerzos_viga_central(est["ELU"], meta, sc["vano"])
        rf = MX.esfuerzos_viga_central(est["FAT"], meta, sc["vano"])
        # fatiga: tension de fibra en la viga MAS cargada (no la suma) -> I_comp por viga
        M_fat_viga = max((pv["M_mixto_Nm"] for pv in rf["por_viga"]), default=0.0)
        esf = {"M_Ed_Nm": ru["M_Ed_Nm"], "V_Ed_N": ru["V_Ed_N"],
               "M_fat_Nm": M_fat_viga}
        chk = ec3ec4_mixto.comprobar(mixto_chk, esf, pm)
        secciones.append({"vano": sc["vano"], "x": sc["x"], "esfuerzos": esf,
                          "veredicto": chk["veredicto"], "aprov_max": chk["aprovechamiento_max"],
                          "checks": chk["checks"], "clasificacion": chk["clasificacion"],
                          "M_Rd_total_Nm": chk["M_Rd_total_Nm"], "PNA_zona": chk["PNA_zona"],
                          "conexion": chk["conexion"], "fatiga": chk["fatiga"],
                          "abolladura": chk["abolladura_EN1993_1_5"]})

    s_crit = max(secciones, key=lambda s: s["aprov_max"])
    veredicto = "CUMPLE" if all(s["veredicto"] == "CUMPLE" for s in secciones) else "NO CUMPLE"
    resultado = {"nombre_tablero": nombre_tablero, "tipologia": "mixto",
                 "mixto": mixto, "lm1": lm1, "flm3": flm3,
                 "seccion_props": {"A_acero_m2": meta["steel"]["A"], "Iy_acero_m4": meta["steel"]["Iy"],
                                   "I_comp_m4": pm["I_comp_m4"], "b_eff_losa_m": be,
                                   "z_na_desde_losa_m": pm["z_na_desde_losa"], "n0": pm["n0"]},
                 "n_nodos": len(M.norden), "n_elementos": len(M.elementos),
                 "carriles": [c["id"] for c in meta["caminos"]],
                 "f1_Hz": f1, "modal": {k: modal[k] for k in ("frecuencias_Hz",) if k in modal},
                 "secciones": secciones, "seccion_critica": s_crit["vano"],
                 "clasificacion_seccion": s_crit["clasificacion"]["clase"],
                 "aprovechamiento_max": s_crit["aprov_max"], "veredicto_global": veredicto}
    try:
        resultado["mapping_writeback"] = resultado_ifc_puente.construir_mapping(resultado)
    except Exception as e:
        resultado["mapping_writeback"] = {"_error": str(e)}
    return resultado


if __name__ == "__main__":
    src = sys.argv[1]
    if src.lower().endswith(".ifc"):
        import desde_ifc
        cfg = desde_ifc.leer(src)
    else:
        cfg = json.load(open(src))
    r = ejecutar(cfg["mixto"], cfg.get("nombre", "MIXTO_PUE18"))
    out = sys.argv[2] if len(sys.argv) > 2 else "resultado_mixto.json"
    json.dump(r, open(out, "w"), indent=2, ensure_ascii=False)
    print("VEREDICTO GLOBAL:", r["veredicto_global"],
          "| aprov_max=%.3f" % r["aprovechamiento_max"],
          "| clase=%s" % r["clasificacion_seccion"],
          "| f1=%.2f Hz" % r["f1_Hz"], "| seccion critica vano=%s" % r["seccion_critica"])
