# -----------------------------------------------------------------------------
# PROCEDENCIA (PT 6.3, Ola 6): COPIA de la semantica de write-back de red a
#   presion de `instalaciones` (`instalaciones/scripts/red/resultado_ifc.py`,
#   PT 4.4), renombrada a `resultado_red_presion.py` para el vertical de
#   ABASTECIMIENTO de `obras-lineales`. Mismo Pset_Estructurando_ResultadoRed.
#   Gemelo a presion de `resultado_red_lineal.py` (saneamiento, lamina libre).
# -----------------------------------------------------------------------------
"""
SEMANTICA DE LOS PSETS DE RESULTADO DE RED (write-back). Frontera C1 (decision
PT 4.4, opcion a): QUE escribir lo decide la DISCIPLINA (aqui); la MECANICA IFC
(abrir/localizar/escribir/guardar) la aporta la capa transversal `iso19650-openbim`
(skill ifc-create:escribir_psets_resultado.py).

A partir del MODELO NEUTRO DE RED (con la clave `elemento` = Name del IfcFlowSegment
por tramo) y del RESULTADO del solver Darcy a presion, construye el MAPPING JSON
  { "elementos": { "<Name>": { "Pset_Estructurando_ResultadoRed": {prop: val} } } }
que la utilidad de iso19650 vuelca al IFC. Es STDLIB PURA (no abre IFC).

Psets de resultado:
  - por TRAMO (IfcFlowSegment): DN_dimensionado_mm, Caudal_l_s, Velocidad_m_s,
    Perdida_carga_kPa, Sentido_flujo.
  - por TERMINAL (IfcFlowTerminal): Caudal_l_s, Presion_disponible_kPa,
    Presion_min_kPa, Margen_kPa, Cumple.

Uso (CLI):  python3 resultado_red_presion.py modelo_neutro.json resultado.json mapping.json
Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
import json
import sys

_PSET = "Pset_Estructurando_ResultadoRed"


def construir_mapping(modelo, resultado):
    """Devuelve el mapping {elementos: {Name: {Pset: {prop: val}}}} para el
    write-back. La clave de cada tramo es su `elemento` (Name del IfcFlowSegment)
    del modelo neutro; la de cada terminal, su `id` (Name del IfcFlowTerminal)."""
    elementos = {}

    tramos_modelo = modelo.get("tramos", {}) or {}
    tramos_res = resultado.get("tramos", {}) or {}
    for tid, to in tramos_res.items():
        meta = tramos_modelo.get(tid, {}) or {}
        nombre = meta.get("elemento") or tid
        props = {
            "DN_dimensionado_mm": to.get("dn"),
            "Caudal_l_s": to.get("caudal_l_s"),
            "Velocidad_m_s": to.get("velocidad_m_s"),
            "Perdida_carga_kPa": to.get("dp_kPa"),
            "Sentido_flujo": to.get("sentido"),
        }
        # si el grafo troceo un segmento, varios tramos comparten Name -> agrega
        # el de mayor caudal (gobernante) para no machacar con un valor menor.
        if nombre in elementos:
            prev = elementos[nombre][_PSET]
            if (props.get("Caudal_l_s") or 0) <= (prev.get("Caudal_l_s") or 0):
                continue
        elementos[nombre] = {_PSET: props}

    for term in resultado.get("terminales", []) or []:
        nombre = term.get("id")
        if not nombre:
            continue
        elementos[nombre] = {_PSET: {
            "Caudal_l_s": term.get("caudal_l_s"),
            "Presion_disponible_kPa": term.get("presion_disponible_kPa"),
            "Presion_min_kPa": term.get("presion_min_kPa"),
            "Margen_kPa": term.get("margen_kPa"),
            "Cumple": term.get("cumple"),
        }}

    return {"elementos": elementos,
            "_meta": {"pset": _PSET,
                      "fuente": "obras-lineales/red (solver Darcy a presion, abastecimiento EN 805)",
                      "nota": "Predimensionado; revisar y firmar por tecnico competente."}}


def main(modelo_path, resultado_path, out_path=None):
    with open(modelo_path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    with open(resultado_path, encoding="utf-8") as fh:
        resultado = json.load(fh)
    mapping = construir_mapping(modelo, resultado)
    out_path = out_path or "mapping_resultado.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(mapping, fh, indent=2, ensure_ascii=False)
    n = len(mapping["elementos"])
    print("Mapping de Psets de resultado: %d elemento(s) -> %s" % (n, out_path))
    return mapping


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
