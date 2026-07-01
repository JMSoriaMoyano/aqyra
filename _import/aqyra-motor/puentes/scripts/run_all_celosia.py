"""
Orquestador e2e del vertical CELOSIA (barras articuladas + IAP-11 + FEM-1 + EC3).

Flujo: celosia -> barras articuladas (C5) -> permanentes (nudos del cordon inferior)
+ LM1 (camino del cordon inferior) -> motor-fem (estatico G + envolventes de axil
LM1 + modal) -> EC3 (traccion / compresion-pandeo curva b / uniones; fatiga = gancho)
-> resultado JSON + mapping write-back.

Consume `motor-fem` (C5). Celosia plana XZ pura: estabilizar_plano=True + se
coacciona RY en todos los nudos (las barras articuladas liberan la flexion -> solo
axil; RY libre seria singular). Fatiga diferida (decision PT 7.2). SI. Predim. (ICCP).
"""
from __future__ import annotations
import os, sys, json, math
_here = os.path.dirname(os.path.abspath(__file__))
for sub in ("idealizacion", "acciones", "comprobacion", "comun"):
    sys.path.insert(0, os.path.join(_here, sub))
import celosia, iap11, ec3_celosia, resultado_ifc_puente
import mallador, fem1   # motor-fem (C5)


def _len(M, bid):
    el = next(e for e in M.elementos if getattr(e, "eid", None) == bid)
    return el.L


def ejecutar(c, nombre="CELOSIA_PUE04"):
    model, meta = celosia.construir_celosia(c)
    M = mallador.desde_modelo_neutro(model, estabilizar_plano=True)
    for nd in M.norden:                       # celosia 2D pura: coacciona RY
        vec = list(M.apoyos.get(nd, [0] * 6)); vec[4] = 1; M.set_apoyo(nd, vec)
    perm = iap11.permanentes_celosia(c, M, meta)
    cm = iap11.lm1_celosia(c, meta)

    est = M.resolver({"G": {"G": 1.0}})["combos"]
    mov = fem1.movil(M, cm)
    try:
        modal = fem1.modal(M, nmodos=4, peso_propio=True, masas_casos={"G": 1.0})
        f1 = modal["frecuencias_Hz"][0]
    except Exception as e:
        f1 = 0.0; modal = {"error": str(e)}

    secs = model["secciones"]; mat = model["materiales"]["ACERO"]
    E = mat["E"]; fy = mat["fy"]
    sec_de = {}
    for grupo, lst in (("CORDON", meta["cordon_inf"] + meta["cordon_sup"]),
                       ("DIAG", meta["diagonales"]), ("MONT", meta["montantes"])):
        for bid in lst:
            sec_de[bid] = grupo

    miembros = []
    for bid in meta["cordon_inf"] + meta["cordon_sup"] + meta["diagonales"] + meta["montantes"]:
        N_G = est["G"]["esfuerzos_barra"][bid]["N_i"]
        env = mov["envolventes"]["N_%s" % bid]
        N_t = 1.35 * N_G + 1.35 * max(env["max"], 0.0)
        N_c = 1.35 * N_G + 1.35 * min(env["min"], 0.0)
        N_Ed = N_t if abs(N_t) >= abs(N_c) else N_c
        sec = secs[sec_de[bid]]
        Imin = min(sec["Iy"], sec["Iz"])
        miembros.append({"nombre": bid, "N_Ed": N_Ed, "A": sec["A"], "Imin": Imin,
                         "L": _len(M, bid), "E": E, "fy": fy, "curva": c.get("curva_pandeo", "b")})
    chk = ec3_celosia.comprobar(c, miembros)
    bc = chk["barra_critica"]

    resultado = {"nombre_tablero": nombre, "tipologia": "celosia", "celosia": c,
                 "permanentes": perm, "f1_Hz": f1,
                 "modal": {k: modal[k] for k in ("frecuencias_Hz",) if k in modal},
                 "barras": chk["barras"], "barra_critica": bc, "fatiga_nota": chk["fatiga_nota"],
                 "aprovechamiento_max": chk["aprovechamiento_max"], "veredicto_global": chk["veredicto"]}
    resultado["mapping_writeback"] = resultado_ifc_puente.construir_mapping(resultado)
    return resultado


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    r = ejecutar(cfg["celosia"], cfg.get("nombre", "CELOSIA_PUE04"))
    out = sys.argv[2] if len(sys.argv) > 2 else "resultado_celosia.json"
    json.dump(r, open(out, "w"), indent=2, ensure_ascii=False)
    bc = r["barra_critica"]
    print("VEREDICTO GLOBAL:", r["veredicto_global"], "| aprov_max=%.3f" % r["aprovechamiento_max"],
          "| f1=%.2f Hz" % r["f1_Hz"], "| critica=%s (%s, aprov=%.3f)" % (bc["nombre"], bc["modo"], bc["aprov"]))
