"""
SEMANTICA DE LOS PSETS DE RESULTADO DE RED ELECTRICA (write-back). Disciplina
`instalaciones`, PT 4.5 (Ola 4). Reutiliza el frente 3 del PT 4.4: la MECANICA IFC
(abrir/localizar/escribir/guardar) la aporta la capa transversal `iso19650-openbim`
(skill ifc-create:escribir_psets_resultado.py); aqui se aporta solo la SEMANTICA
(que Pset y que propiedades). Mismo Pset que la red hidraulica
(`Pset_Estructurando_ResultadoRed`) con las propiedades ELECTRICAS.

A partir del MODELO NEUTRO DE RED (clave `elemento` = Name del IfcFlowSegment por
tramo) y del RESULTADO del solver electrico, construye el MAPPING JSON
  { "elementos": { "<Name>": { "Pset_Estructurando_ResultadoRed": {prop: val} } } }
que la utilidad de iso19650 vuelca al IFC. Es STDLIB PURA (no abre IFC).

Psets de resultado (electrico):
  - por TRAMO (IfcFlowSegment): Seccion_mm2, Intensidad_A, I_admisible_A,
    Caida_tension_pct, Potencia_W, Fases, Material_conductor.
  - por TERMINAL (IfcFlowTerminal): Potencia_W, Tension_V, Caida_tension_acum_pct,
    Cumple.

Uso (CLI):  python3 resultado_ifc_electrico.py modelo_neutro.json resultado.json mapping.json
Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
import json
import sys

_PSET = "Pset_Estructurando_ResultadoRed"


def construir_mapping(modelo, resultado):
    """Devuelve el mapping {elementos: {Name: {Pset: {prop: val}}}} para el
    write-back electrico. La clave de cada tramo es su `elemento` (Name del
    IfcFlowSegment) del modelo neutro; la de cada terminal, su `id`."""
    elementos = {}

    tramos_modelo = modelo.get("tramos", {}) or {}
    tramos_res = resultado.get("tramos", {}) or {}
    for tid, to in tramos_res.items():
        if to.get("intensidad_A") is None:   # chord ignorado en red radial
            continue
        meta = tramos_modelo.get(tid, {}) or {}
        nombre = meta.get("elemento") or tid
        props = {
            "Seccion_mm2": to.get("seccion_mm2"),
            "Intensidad_A": to.get("intensidad_A"),
            "I_admisible_A": to.get("I_admisible_A"),
            "Caida_tension_pct": to.get("caida_tension_pct"),
            "Potencia_W": to.get("potencia_W"),
            "Fases": to.get("fases"),
            "Material_conductor": to.get("material"),
        }
        # si el grafo troceo un segmento, varios tramos comparten Name -> agrega
        # el de mayor intensidad (gobernante) para no machacar con un valor menor.
        if nombre in elementos:
            prev = elementos[nombre][_PSET]
            if (props.get("Intensidad_A") or 0) <= (prev.get("Intensidad_A") or 0):
                continue
        elementos[nombre] = {_PSET: props}

    for term in resultado.get("terminales", []) or []:
        nombre = term.get("id")
        if not nombre:
            continue
        elementos[nombre] = {_PSET: {
            "Potencia_W": term.get("potencia_W"),
            "Tension_V": term.get("tension_V"),
            "Caida_tension_acum_pct": term.get("caida_acum_pct"),
            "Cumple": term.get("cumple"),
        }}

    return {"elementos": elementos,
            "_meta": {"pset": _PSET,
                      "fuente": "instalaciones/electrico (solver de red electrica REBT)",
                      "nota": "Predimensionado; revisar y firmar por tecnico competente."}}


def main(modelo_path, resultado_path, out_path=None):
    with open(modelo_path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    with open(resultado_path, encoding="utf-8") as fh:
        resultado = json.load(fh)
    mapping = construir_mapping(modelo, resultado)
    out_path = out_path or "mapping_resultado_electrico.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(mapping, fh, indent=2, ensure_ascii=False)
    n = len(mapping["elementos"])
    print("Mapping de Psets de resultado electrico: %d elemento(s) -> %s" % (n, out_path))
    return mapping


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
