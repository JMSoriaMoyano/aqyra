# -*- coding: utf-8 -*-
"""Consumidor CONTRACTUAL del rail firmable: el PLIEGO de condiciones tecnicas (Slice C, D-PL-1..3).

Tercera y ultima pieza del conjunto contractual firmable (junto al presupuesto, `presupuesto_doc`). Hace
FIRMABLE el pliego por el MISMO rail de export que ya firma el presupuesto (E6.2): ENVUELVE el compositor
que ya existe (`documentos/pliego.componer_pliego`) — NO re-renderiza — y anade el PDF sellado + el
manifiesto de procedencia. El artefacto AUTORITATIVO es el mismo `salida-presupuesto` (C5); el DESCRIPTOR
PORTA el `criterio` (mapeo partida->sistema) y el `pack_textos` (prescripcion), en la clave forward-open
`descriptor["pliego"] = {criterio, pack_textos}` (el descriptor-export.schema.json es abierto). El nucleo
`componer_export` sigue siendo VERTICAL-AGNOSTICO: se registra este consumidor SIN tocar manifiesto/firma.

SIN BC3 ni XLSX (D-PL-1): el texto de prescripcion ya viaja en el registro `~T` del BC3 del PRESUPUESTO
(interop); el firmable del pliego = Word + PDF sellado + manifiesto. Determinista, sin LLM (LEE el
artefacto ya anclado; no recalcula). Espejo de `presupuesto_doc.py`.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from aqyra_documento_comun import formato as F

_TITULO = "PLIEGO DE CONDICIONES TECNICAS"


def _fecha(descriptor: dict) -> str:
    return str(descriptor.get("sello_tiempo") or "-")


def _dt(descriptor: dict) -> datetime:
    try:
        return datetime.strptime(_fecha(descriptor), "%Y-%m-%d")
    except ValueError:
        return datetime(1970, 1, 1)


def _txt(s) -> str:
    return (str(s).replace("→", "->").replace("€", "EUR")
            .encode("latin-1", "replace").decode("latin-1"))


def _pliego_refs(descriptor: dict) -> tuple[dict, dict]:
    """`criterio` + `pack_textos` que el CALLER porta en el descriptor (dicts YA resueltos; patron
    vertical-agnostico: el nucleo/consumidor no lee versions.lock ni el repo, igual que las
    versiones_ancladas)."""
    pl = descriptor.get("pliego") or {}
    return dict(pl.get("criterio") or {}), dict(pl.get("pack_textos") or {})


# ------------------------------------------------------------------ WORD (envuelve el compositor firmado)
def pliego_word(artefacto: dict, descriptor: dict, manifiesto: dict, salida: Path) -> Path:
    """Envuelve documentos/pliego.componer_pliego (NO re-renderiza: reusa el .docx del despacho)."""
    import aqyra_documento_pliego as APL
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    criterio, pack_textos = _pliego_refs(descriptor)
    return APL.componer_pliego(artefacto, criterio, {
        "salida": salida, "fecha": _fecha(descriptor), "pack_textos": pack_textos,
        "titulo": _TITULO,
    })


# ------------------------------------------------------------------ PDF firmable (el sellado contractual)
def _h1(pdf, t):
    pdf.set_font("Helvetica", "B", 13); pdf.set_text_color(31, 78, 121)
    pdf.multi_cell(0, 8, _txt(t), new_x="LMARGIN", new_y="NEXT"); pdf.set_text_color(0, 0, 0)


def _row(pdf, cols, widths, bold=False, align=None):
    pdf.set_font("Helvetica", "B" if bold else "", 8.5)
    align = align or ["L"] * len(cols)
    for i, (c, w) in enumerate(zip(cols, widths)):
        last = i == len(cols) - 1
        pdf.cell(w, 5, _txt(c), border=1, align=align[i],
                 new_x="LMARGIN" if last else "RIGHT", new_y="NEXT" if last else "TOP")


def pliego_pdf(artefacto: dict, descriptor: dict, manifiesto: dict, salida: Path) -> Path:
    """PDF firmable del pliego (sellado): por partida, prescripcion + medicion trazable + coste + GUIDs +
    carbono forward-open, un cuadro de trazabilidad y el manifiesto de procedencia EMBEBIDO. VIA
    PURE-PYTHON (fpdf2), anclado por TEXTO extraido (pypdf), NO por pixeles. Reusa la MISMA cadena de
    prescripcion del compositor de pliego (sin re-implementarla): el firmable dice lo mismo que el Word."""
    from fpdf import FPDF
    from aqyra_documento_pliego import compositor as CP

    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    criterio, pack_textos = _pliego_refs(descriptor)
    cod_clase, clase_sistema, sin_geo = CP._mapas_criterio(criterio)

    partidas = artefacto.get("estado_mediciones", [])
    resumen = artefacto.get("resumen", {})
    desc_cap = {c.get("codigo", ""): c.get("descripcion", "") for c in resumen.get("capitulos", [])}
    orden_cap: list[str] = []
    por_cap: dict[str, list] = {}
    for p in partidas:
        cap = p.get("capitulo", "") or "-"
        if cap not in por_cap:
            por_cap[cap] = []
            orden_cap.append(cap)
        por_cap[cap].append(p)

    pdf = FPDF(format="A4"); pdf.set_auto_page_break(True, 18); pdf.set_margins(20, 18, 20)
    pdf.set_creation_date(_dt(descriptor)); pdf.set_producer("aqyra-documento-export")
    pdf.set_title(_txt(f"{_TITULO} - {artefacto.get('proyecto', '')}"))
    pdf.set_author(_txt(manifiesto.get("generador", "aqyra-documento-export")))
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22); pdf.set_text_color(31, 78, 121)
    pdf.multi_cell(0, 10, _txt(f"{_TITULO} (FIRMABLE)"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11); pdf.set_text_color(89, 89, 89)
    pdf.multi_cell(0, 6, _txt(artefacto.get("proyecto", "")), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 10); pdf.set_text_color(46, 125, 50)
    pdf.multi_cell(0, 6, _txt("Cierra el conjunto contractual firmable: coste + carbono + prescripcion "
                              "sobre la misma medicion."), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0); pdf.ln(2)

    # 1 · condiciones generales
    _h1(pdf, "1. Condiciones generales")
    generales = pack_textos.get("generales") or [
        "Condiciones generales no provistas por el pack de textos base."]
    pdf.set_font("Helvetica", "", 9)
    for i, clausula in enumerate(generales, 1):
        pdf.multi_cell(0, 4.5, _txt(f"{i}. {clausula}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    # 2 · prescripciones tecnicas particulares (por partida: prescripcion + medicion + coste + GUIDs)
    _h1(pdf, "2. Prescripciones tecnicas particulares")
    for cap in orden_cap:
        pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(31, 78, 121)
        pdf.multi_cell(0, 6, _txt(f"Capitulo {cap} - {desc_cap.get(cap, '')}"),
                       new_x="LMARGIN", new_y="NEXT"); pdf.set_text_color(0, 0, 0)
        for p in por_cap[cap]:
            cod = p.get("codigo", "")
            unidad = p.get("unidad", "")
            sistema, ss = CP._sistema_de(cod, cod_clase, clase_sistema, sin_geo)
            etq = f"  [Sistema: {sistema}" + (f" / {ss}]" if ss else "]")
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.multi_cell(0, 5, _txt(f"{cod} . {p.get('descripcion', '')}{etq}"),
                           new_x="LMARGIN", new_y="NEXT")
            # prescripcion (MISMA cadena que el compositor: en las 8 partidas de AQ-DEMO, sin fallback)
            pdf.set_font("Helvetica", "", 8.5)
            pdf.multi_cell(0, 4.3, _txt("Prescripcion. " + CP._prescripcion(p, pack_textos)),
                           new_x="LMARGIN", new_y="NEXT")
            # medicion trazable + coste (justificacion; texto extraible sin overflow de tabla)
            pdf.set_font("Helvetica", "I", 7.8); pdf.set_text_color(90, 90, 90)
            med = (f"    Medicion: {F.fmt_num(p.get('cantidad', 0), 3)} {unidad}"
                   f" | Criterio: {p.get('criterio_aplicado', '-')} | Origen: {p.get('origen', '-')}")
            pdf.multi_cell(0, 4, _txt(med), new_x="LMARGIN", new_y="NEXT")
            cost = (f"    Coste: precio unitario {F.fmt_eur(p.get('precio_unitario', 0))}"
                    f" -> importe {F.fmt_eur(p.get('importe', 0))}")
            pdf.multi_cell(0, 4, _txt(cost), new_x="LMARGIN", new_y="NEXT")
            carbono = (p.get("valores") or {}).get("carbono")
            if carbono:  # forward-open: solo si el presupuesto trae el eje carbono
                unidad_c = carbono.get("unidad", "kgCO2e")
                pdf.multi_cell(0, 4, _txt(f"    Huella de carbono: "
                                          f"{F.fmt_num(carbono.get('total', 0), 2)} {unidad_c}"),
                               new_x="LMARGIN", new_y="NEXT")
            guids = p.get("trazabilidad") or []
            tz = ("    Trazabilidad al modelo (GUIDs): " + ", ".join(guids)) if guids \
                else "    Trazabilidad al modelo (GUIDs): sin geometria (origen regla)."
            pdf.multi_cell(0, 4, _txt(tz), new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0); pdf.ln(1)

    # 3 · cuadro de trazabilidad al modelo
    pdf.add_page(); _h1(pdf, "3. Cuadro de trazabilidad al modelo")
    _row(pdf, ["Codigo", "Descripcion", "Ud", "Cantidad", "GUIDs"],
         [20, 52, 12, 22, 48], bold=True, align=["L", "L", "L", "R", "L"])
    for p in partidas:
        guids = p.get("trazabilidad") or []
        _row(pdf, [p.get("codigo", ""), p.get("descripcion", "")[:40], p.get("unidad", ""),
                   F.fmt_num(p.get("cantidad", 0), 3),
                   (", ".join(guids)[:40] if guids else "(sin geometria)")],
             [20, 52, 12, 22, 48], align=["L", "L", "L", "R", "L"])
    pdf.ln(2)

    # 4 · manifiesto de procedencia embebido
    _h1(pdf, "4. Manifiesto de procedencia")
    art = manifiesto.get("artefacto", {})
    pdf.set_font("Helvetica", "", 8.5)
    lineas = [f"Generador: {manifiesto.get('generador')} {manifiesto.get('version_generador')}",
              f"Sello: {manifiesto.get('sello_tiempo')}  |  Artefacto: {art.get('tipo')} - {art.get('id')}",
              f"content_sha256: {art.get('content_sha256')}"]
    for k, v in (manifiesto.get("versiones_ancladas") or {}).items():
        lineas.append(f"Version {k}: {v}")
    for ln in lineas:
        pdf.multi_cell(0, 4.5, _txt(ln), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 8); pdf.set_text_color(176, 0, 0)
    pdf.multi_cell(0, 4.5, _txt("Documento contractual firmable. Integridad verificada en el gate "
                                "(Llave 1); procedencia firmada por JM (GPG, Llave 2). Preparado para la "
                                "firma cualificada/PAdES del destinatario. Debe ser revisado y firmado "
                                "por tecnico competente antes de su uso."),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(salida))
    return salida


# registro de formatos del consumidor (lo consume el nucleo export.py). Sin BC3/XLSX (D-PL-1): el texto
# de prescripcion viaja en el ~T del BC3 del presupuesto; el firmable del pliego = Word + PDF sellado.
FORMATOS = {
    "word": ("Pliego.docx", pliego_word),
    "pdf":  ("Pliego-firmable.pdf", pliego_pdf),
}
