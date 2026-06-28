"""
ORQUESTADOR ELECTRICO (extremo a extremo). Disciplina `instalaciones`, PT 4.5
(Ola 4). Analogo a `pci/run_all_pci.py` para el vertical REBT.

Encadena la receta de la disciplina sobre el MODELO NEUTRO DE RED (emitido por el
parser MEP de iso19650-openbim, PT 4.2, sistema ELECTRICAL):
  modelo neutro  ->  bases_demanda_electrica.aplicar_demanda_electrica (CN-3)
                 ->  solver_electrico.resolver  ->  verificacion_electrico.verificar
                 ->  resultado_ifc_electrico.construir_mapping (write-back)
                 ->  artefactos JSON.

NO lee IFC (eso es C1, en iso19650-openbim). Entrada: modelo_neutro_mep.json.
Salidas: <base>_demanda.json, <base>_resultado.json, <base>_verificacion.json,
         <base>_mapping.json.

Predimensionado/asistencia; revisar y firmar por tecnico competente.
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import bases_demanda_electrica   # noqa: E402
import solver_electrico          # noqa: E402
import verificacion_electrico    # noqa: E402
import resultado_ifc_electrico   # noqa: E402


def run(modelo_path, outdir=None, modo=None, grado=None,
        aislamiento="PVC", material="Cu"):
    with open(modelo_path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    outdir = outdir or os.path.dirname(os.path.abspath(modelo_path))
    base = os.path.splitext(os.path.basename(modelo_path))[0]

    # 1) bases de demanda electrica (CN-3): dispatcher vivienda / receptores
    m_dem = bases_demanda_electrica.aplicar_demanda_electrica(modelo, modo, grado)
    p_dem = os.path.join(outdir, base + "_demanda.json")
    with open(p_dem, "w", encoding="utf-8") as fh:
        json.dump(m_dem, fh, indent=2, ensure_ascii=False)

    # 2) solver electrico
    resultado = solver_electrico.resolver(m_dem, aislamiento=aislamiento, material=material)
    p_res = os.path.join(outdir, base + "_resultado.json")
    with open(p_res, "w", encoding="utf-8") as fh:
        json.dump(resultado, fh, indent=2, ensure_ascii=False)

    # 3) verificacion (arnes)
    verif = verificacion_electrico.verificar(m_dem, resultado)
    p_ver = os.path.join(outdir, base + "_verificacion.json")
    with open(p_ver, "w", encoding="utf-8") as fh:
        json.dump(verif, fh, indent=2, ensure_ascii=False)

    # 4) mapping de write-back (semantica electrica; la mecanica IFC es de iso19650)
    mapping = resultado_ifc_electrico.construir_mapping(m_dem, resultado)
    p_map = os.path.join(outdir, base + "_mapping.json")
    with open(p_map, "w", encoding="utf-8") as fh:
        json.dump(mapping, fh, indent=2, ensure_ascii=False)

    print("REBT e2e -> solver=%s verif=%s"
          % (resultado["veredicto"], verif["veredicto"]))
    print("  P cabecera %s W | caida max %s %% (gobernante %s)"
          % (verif["potencia_cabecera_W"], verif["caida_tension_max_pct"],
             verif["terminal_gobernante"]))
    print("  Balance de potencias %.4f %%" % verif["balance_potencias_pct"])
    print("  Artefactos:", p_dem, p_res, p_ver, p_map)
    return {"demanda": m_dem, "resultado": resultado, "verificacion": verif,
            "mapping": mapping, "veredicto": verif["veredicto"]}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    r = run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    sys.exit(0 if r["veredicto"] == "CUMPLE" else 1)
