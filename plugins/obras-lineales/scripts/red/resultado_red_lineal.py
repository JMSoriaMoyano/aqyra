"""
SEMANTICA DE LOS PSETS DE RESULTADO DE RED DE SANEAMIENTO (write-back). Disciplina
`obras-lineales`, PT 6.2 (Ola 6). Frontera C1 §5bis (decision PT 4.4, opcion a): QUE
escribir lo decide la DISCIPLINA (aqui); la MECANICA IFC la aporta la capa
transversal `iso19650-openbim` (skill ifc-create:escribir_psets_resultado.py).
Reutiliza el mismo `Pset_Estructurando_ResultadoRed` que instalaciones (red a
presion), con las propiedades propias de la lamina libre.

A partir del MODELO NEUTRO DE RED (clave `elemento` = Name del IfcFlowSegment por
tramo) y del RESULTADO del solver de Manning, construye el MAPPING JSON
  { "elementos": { "<Name>": { "Pset_Estructurando_ResultadoRed": {prop: val} } } }
Es STDLIB PURA (no abre IFC).

Psets de resultado:
  - por TRAMO (IfcFlowSegment): DN_mm, Caudal_l_s, Velocidad_m_s, Calado_m,
    Llenado_pct, Pendiente_J, Regimen, Sentido_flujo.
  - por VERTIDO (nodo outfall): Caudal_total_l_s.
"""
import json
import sys

_PSET = "Pset_Estructurando_ResultadoRed"


def construir_mapping(modelo, resultado):
    elementos = {}
    tramos_modelo = modelo.get("tramos", {}) or {}
    tramos_res = resultado.get("tramos", {}) or {}
    for tid, to in tramos_res.items():
        meta = tramos_modelo.get(tid, {}) or {}
        nombre = meta.get("elemento") or to.get("elemento") or tid
        props = {
            "DN_mm": to.get("dn"),
            "Caudal_l_s": to.get("caudal_l_s"),
            "Velocidad_m_s": to.get("velocidad_m_s"),
            "Calado_m": to.get("calado_y_m"),
            "Llenado_pct": to.get("llenado_pct"),
            "Pendiente_J": to.get("pendiente_J"),
            "Regimen": to.get("regimen"),
            "Sentido_flujo": to.get("sentido"),
        }
        props = {k: v for k, v in props.items() if v is not None}
        if nombre in elementos:
            prev = elementos[nombre][_PSET]
            if (props.get("Caudal_l_s") or 0) <= (prev.get("Caudal_l_s") or 0):
                continue
        elementos[nombre] = {_PSET: props}

    # vertido(s): caudal total. Clave = Name del elemento IFC del vertido (de
    # modelo["vertidos"]); si no esta, el nombre de nodo del resultado.
    q_tot = resultado.get("caudal_total_vertido_l_s")
    vert_id_por_nodo = {v.get("nodo"): v.get("id")
                        for v in (modelo.get("vertidos") or []) if v.get("nodo")}
    for nm in resultado.get("vertidos", []) or []:
        clave = vert_id_por_nodo.get(nm, nm)
        elementos[clave] = {_PSET: {"Caudal_total_l_s": q_tot}}

    return {"elementos": elementos,
            "_meta": {"pset": _PSET,
                      "fuente": "obras-lineales/red (solver Manning lamina libre)",
                      "nota": "Predimensionado; revisar y firmar por tecnico competente."}}


def main(modelo_path, resultado_path, out_path=None):
    with open(modelo_path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    with open(resultado_path, encoding="utf-8") as fh:
        resultado = json.load(fh)
    mapping = construir_mapping(modelo, resultado)
    out_path = out_path or "mapping_resultado_red.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(mapping, fh, indent=2, ensure_ascii=False)
    print("Mapping de Psets de resultado de red: %d elemento(s) -> %s"
          % (len(mapping["elementos"]), out_path))
    return mapping


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
