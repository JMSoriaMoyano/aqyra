"""
Orquestador e2e del vertical ESTRIBO (PT 7.3).

Flujo: estribo (muro con cargas de tablero) -> empuje activo Ka (o reposo K0) +
sobrecarga + reacciones del tablero (vertical en coronacion, horizontal de frenado)
-> fuste (alzado) por motor-fem (C5) + empujes/pesos (reuso muros) -> verificacion
EC7 (vuelco/deslizamiento/hundimiento) + EC2 (alzado/puntera/talon) reusando
`verificacion_muro` -> resultado JSON + mapping write-back.

Reutiliza muros-contension (EC7+EC2). El fuste consume motor-fem; PyNite no se usa.
SI. Predim. (ICCP).
"""
from __future__ import annotations
import os, sys, json
_here = os.path.dirname(os.path.abspath(__file__))
for sub in ("idealizacion", "acciones", "comprobacion", "comun"):
    sys.path.insert(0, os.path.join(_here, sub))
sys.path.insert(0, "/tmp/mc/scripts/muros-contencion")    # verificacion_muro (dev)
import estribo, ec7ec2_estribo, resultado_ifc_puente


def ejecutar(p, nombre="ESTRIBO_PUE06", resultado_tablero=None, apoyo_id=None):
    # modo acoplado: reacciones desde un resultado de tablero
    if resultado_tablero is not None:
        import aparatos_apoyo
        r = aparatos_apoyo.reacciones_desde_tablero(resultado_tablero, apoyo_id)
        p.setdefault("reacciones", {})
        p["reacciones"].update({"N_G_N": r["N_G_N"], "N_LM1_N": r["N_LM1_N"],
                                "H_frenado_N": r.get("H_frenado_N", p["reacciones"].get("H_frenado_N", 0.0))})
    model = estribo.construir_modelo_muro(p)
    emp = estribo.empujes(model)
    pes, gc = estribo.pesos(model)
    alz = estribo.solve_fuste_fem(model)
    H_fren = model["coronacion"].get("H_Q_N", 0.0)
    chk = ec7ec2_estribo.comprobar(model, emp, pes, alz, H_frenado_N=H_fren)

    resultado = {"nombre_tablero": nombre, "tipologia": "estribo", "estribo": p,
                 "Ka": emp["Ka"], "metodo_empuje": model["terreno"].get("metodo_empuje", "activo"),
                 "H_total_m": emp["H"], "reacciones": model["coronacion"],
                 "vuelco": chk["vuelco"], "deslizamiento": chk["deslizamiento"],
                 "hundimiento": chk["hundimiento"], "alzado": chk["alzado"],
                 "puntera": chk["puntera"], "talon": chk["talon"],
                 "aprovechamientos": chk["aprovechamientos"],
                 "aprovechamiento_max": chk["aprovechamiento_max"],
                 "veredicto_global": chk["veredicto_global"]}
    resultado["mapping_writeback"] = resultado_ifc_puente.construir_mapping(resultado)
    return resultado


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    r = ejecutar(cfg["estribo"], cfg.get("nombre", "ESTRIBO_PUE06"),
                 resultado_tablero=cfg.get("resultado_tablero"), apoyo_id=cfg.get("apoyo_id"))
    out = sys.argv[2] if len(sys.argv) > 2 else "resultado_estribo.json"
    json.dump(r, open(out, "w"), indent=2, ensure_ascii=False)
    print("VEREDICTO GLOBAL:", r["veredicto_global"], "| aprov_max=%.3f" % r["aprovechamiento_max"],
          "| Ka=%.3f" % r["Ka"], "| empuje=%s" % r["metodo_empuje"],
          "| vuelco u=%.2f desl u=%.2f hund u=%.2f" % (r["vuelco"]["u"], r["deslizamiento"]["u"], r["hundimiento"]["u"]))
