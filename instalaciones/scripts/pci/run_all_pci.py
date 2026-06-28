"""
ORQUESTADOR PCI (extremo a extremo). Disciplina `instalaciones`, PT 4.3 (Ola 4).

Encadena la receta de la disciplina sobre el MODELO NEUTRO DE RED (emitido por el
parser MEP de iso19650-openbim, PT 4.2):
  modelo neutro  ->  bases_demanda.aplicar (H3, CN-3)  ->  solver_red.resolver
                 ->  verificacion_red.verificar  ->  artefactos JSON.

NO lee IFC (eso es C1, en iso19650-openbim). Entrada: modelo_neutro_mep.json.
Salidas: <base>_demanda.json, <base>_resultado.json, <base>_verificacion.json.

Predimensionado/asistencia; revisar y firmar por tecnico competente.
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "red"))
sys.path.insert(0, _HERE)
import bases_demanda          # noqa: E402
import solver_red             # noqa: E402
import verificacion_red       # noqa: E402


def run(modelo_path, outdir=None):
    with open(modelo_path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    outdir = outdir or os.path.dirname(os.path.abspath(modelo_path))
    base = os.path.splitext(os.path.basename(modelo_path))[0]

    # 1) bases de demanda (H3): dispatcher BIE / rociadores (UNE-EN 12845)
    m_dem = bases_demanda.aplicar_demanda(modelo)
    p_dem = os.path.join(outdir, base + "_demanda.json")
    with open(p_dem, "w", encoding="utf-8") as fh:
        json.dump(m_dem, fh, indent=2, ensure_ascii=False)

    # 2) solver hidraulico
    resultado = solver_red.resolver(m_dem)
    p_res = os.path.join(outdir, base + "_resultado.json")
    with open(p_res, "w", encoding="utf-8") as fh:
        json.dump(resultado, fh, indent=2, ensure_ascii=False)

    # 3) verificacion (arnes)
    verif = verificacion_red.verificar(m_dem, resultado)
    p_ver = os.path.join(outdir, base + "_verificacion.json")
    with open(p_ver, "w", encoding="utf-8") as fh:
        json.dump(verif, fh, indent=2, ensure_ascii=False)

    print("PCI e2e -> demanda=%s solver=%s verif=%s"
          % (resultado["veredicto"], resultado["veredicto"], verif["veredicto"]))
    print("  Fuente: disp %s / req %s kPa (margen %s) | v_pico %s m/s"
          % (resultado["presion_fuente_disponible_kPa"],
             resultado["presion_fuente_requerida_kPa"],
             resultado["margen_fuente_kPa"], resultado["velocidad_pico_m_s"]))
    print("  Balance global %.4f %% | residuo nudo %.4f %%"
          % (verif["balance_global_pct"], verif["residuo_nudo_max_pct"]))
    print("  Artefactos:", p_dem, p_res, p_ver)
    return {"demanda": m_dem, "resultado": resultado, "verificacion": verif,
            "veredicto": verif["veredicto"]}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    r = run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    sys.exit(0 if r["veredicto"] == "CUMPLE" else 1)
