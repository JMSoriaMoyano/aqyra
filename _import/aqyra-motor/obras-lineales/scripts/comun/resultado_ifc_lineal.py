"""
SEMANTICA DEL PSET DE RESULTADO DE OBRA LINEAL (write-back). Plugin obras-lineales.
PT 5.2 (Ola 5). stdlib pura.

Construye el MAPPING JSON que la skill `iso19650-openbim:ifc-create`
(`escribir_psets_resultado.py`) vuelca al IFC. Frontera C1 §5bis (decision PT 4.4,
opcion a): la MECANICA de escritura IFC es de la capa transversal (iso19650); la
SEMANTICA (que Pset y que propiedades) la fija esta disciplina.

Pset de resultado: `Pset_Estructurando_ResultadoLineal`, asociado al EJE
(IfcAlignment, por Name o GlobalId del modelo neutro). Propiedades:
  - Trazado: Vp_kmh, Trazado_veredicto, Trazado_n_no_cumple, Trazado_norma.
  - Firme:   Firme_codigo_seccion, Firme_categoria_trafico, Firme_explanada,
             Firme_espesor_total_cm, Firme_norma.
  - Drenaje: Drenaje_veredicto, Drenaje_n_cunetas, Drenaje_n_odt,
             Drenaje_n_no_cumple, Drenaje_Q_max_m3_s, Drenaje_norma (5.2-IC).

Uso (programatico):  mapping(modelo, res_trazado=None, res_firme=None,
                             res_drenaje=None) -> dict
       (CLI)        :  python3 resultado_ifc_lineal.py modelo.json [outdir]
                        [--trazado resultados_trazado.json] [--firme resultados_firme.json]
                        [--drenaje resultados_drenaje.json]
Predimensionado; revisar/firmar por tecnico competente (ICCP).
"""
import json
import os
import sys

PSET = "Pset_Estructurando_ResultadoLineal"


def _clave_eje(modelo):
    """Localiza el eje por Name (preferente) y, si no, por GlobalId."""
    eje = modelo.get("eje") or {}
    return eje.get("nombre") or eje.get("global_id")


def mapping(modelo, res_trazado=None, res_firme=None, res_drenaje=None):
    """Construye el mapping {elementos: {<eje>: {Pset: {prop: val}}}}."""
    clave = _clave_eje(modelo)
    if not clave:
        raise ValueError("El modelo neutro no identifica el eje (eje.nombre/global_id).")
    props = {}

    if res_trazado:
        props["Trazado_norma"] = "3.1-IC"
        props["Vp_kmh"] = res_trazado.get("vp_kmh")
        props["Trazado_veredicto"] = res_trazado.get("veredicto")
        props["Trazado_n_no_cumple"] = len(res_trazado.get("no_cumplen", []))

    firme = (res_firme or {}).get("firme") or modelo.get("firme")
    if firme:
        props["Firme_norma"] = firme.get("norma", "6.1-IC")
        props["Firme_codigo_seccion"] = firme.get("codigo_seccion")
        props["Firme_categoria_trafico"] = firme.get("categoria_trafico")
        props["Firme_explanada"] = firme.get("explanada")
        props["Firme_espesor_total_cm"] = firme.get("espesor_total_cm")

    # Drenaje: resumen del veredicto y del caudal gobernante (5.2-IC).
    dre = res_drenaje or {}
    ver = dre.get("verificacion") or {}
    cunetas = dre.get("cunetas") or (modelo.get("drenaje") or {}).get("cunetas") or []
    odts = dre.get("odt") or (modelo.get("drenaje") or {}).get("odt") or []
    caudales = dre.get("caudales") or (modelo.get("drenaje") or {}).get("cuencas") or []
    if cunetas or odts:
        props["Drenaje_norma"] = "5.2-IC"
        props["Drenaje_veredicto"] = ver.get("veredicto")
        props["Drenaje_n_cunetas"] = len(cunetas)
        props["Drenaje_n_odt"] = len(odts)
        props["Drenaje_n_no_cumple"] = (ver.get("n_cunetas_no_cumple", 0)
                                        + ver.get("n_odt_no_cumple", 0))
        if caudales:
            props["Drenaje_Q_max_m3_s"] = round(
                max(float(q.get("caudal_m3_s", 0.0)) for q in caudales), 4)

    # descarta None
    props = {k: v for k, v in props.items() if v is not None}
    return {"elementos": {clave: {PSET: props}}}


def _load(path):
    if not path:
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    modelo_path = argv[0]
    outdir, traz, firme, drena = None, None, None, None
    rest = argv[1:]
    i = 0
    while i < len(rest):
        if rest[i] == "--trazado": traz = rest[i + 1]; i += 2
        elif rest[i] == "--firme": firme = rest[i + 1]; i += 2
        elif rest[i] == "--drenaje": drena = rest[i + 1]; i += 2
        else: outdir = rest[i]; i += 1

    modelo = _load(modelo_path)
    m = mapping(modelo, _load(traz), _load(firme), _load(drena))
    print(json.dumps(m, indent=2, ensure_ascii=False))

    outdir = outdir or "."
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "mapping_resultado_lineal.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(m, fh, indent=2, ensure_ascii=False)
    print("\nMapping escrito en", out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
