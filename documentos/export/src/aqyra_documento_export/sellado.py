# -*- coding: utf-8 -*-
"""Sellado: el PDF firmable con el manifiesto de procedencia EMBEBIDO (D-EX-2/D-EX-3).

El PDF es el ENTREGABLE FIRMABLE (no editable). Se genera por VIA PURE-PYTHON (fpdf2), sin
LibreOffice, para que el gate siga siendo hermetico; se ancla por TEXTO extraido (pypdf), NO por
pixeles (coherente con «sin pixeles anclados» de las D2 de presupuesto/pliego). El manifiesto se
renderiza como una seccion visible del PDF (content_sha256, versiones, sello), de modo que la
procedencia viaja DENTRO del firmable y es verificable por extraccion de texto.

Determinista: la fecha de creacion del PDF se fija desde el sello (parametro, NUNCA now()).
Texto restringido a latin-1 (fuentes core de PDF): sin simbolos fuera de latin-1 (EUR en letras,
'->' en vez de flecha, 'Suma' en vez de sigma).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fpdf import FPDF

from aqyra_documento_comun import formato as F
from .proyeccion import _unidad, seleccionar_vistas


def _sello_dt(descriptor: dict) -> datetime:
    sello = str(descriptor.get("sello_tiempo") or "1970-01-01")
    try:
        return datetime.strptime(sello, "%Y-%m-%d")
    except ValueError:
        return datetime(1970, 1, 1)


def _txt(s: str) -> str:
    """Aplana a latin-1 (fuentes core), sustituyendo lo que no cabe."""
    return (str(s).replace("→", "->").replace("Σ", "Suma").replace("€", "EUR")
            .encode("latin-1", "replace").decode("latin-1"))


def firmable_pdf(artefacto: dict, descriptor: dict, manifiesto: dict, salida: Path) -> Path:
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    proyecto = str(artefacto.get("proyecto", "Proyeccion de valor"))
    vistas = seleccionar_vistas(artefacto, descriptor)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(25, 20, 25)
    pdf.set_creation_date(_sello_dt(descriptor))
    pdf.set_title(_txt(f"Proyeccion de valor - {proyecto}"))
    pdf.set_author(_txt(manifiesto.get("generador", "aqyra-documento-export")))
    pdf.set_producer("aqyra-documento-export")
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(31, 78, 121)
    pdf.multi_cell(0, 10, _txt("PROYECCION DE VALOR (FIRMABLE)"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(89, 89, 89)
    pdf.multi_cell(0, 7, _txt(proyecto), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)

    for i, v in enumerate(vistas, 1):
        eje, corte = v.get("eje", "coste"), v.get("corte", "-")
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(31, 78, 121)
        pdf.multi_cell(0, 8, _txt(f"Vista {i}: {eje} por {corte}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(86, 7, _txt("Grupo"), border=1)
        pdf.cell(34, 7, _txt("Valor"), border=1, align="R")
        pdf.cell(20, 7, _txt("Unidad"), border=1)
        pdf.cell(0, 7, _txt("Fuente"), border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9.5)
        for g in v.get("grupos", []):
            pdf.cell(86, 6, _txt(g.get("grupo", "")), border="LR")
            pdf.cell(34, 6, _txt(F.fmt_num(g.get("valor_total", 0), 2)), border="LR", align="R")
            pdf.cell(20, 6, _txt(_unidad(v, g)), border="LR")
            pdf.cell(0, 6, _txt(g.get("fuente", "")), border="LR", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(86, 6, _txt(f"SUMA ({corte})"), border=1)
        pdf.cell(34, 6, _txt(F.fmt_num(v.get("suma", 0), 2)), border=1, align="R")
        pdf.cell(20, 6, _txt(_unidad(v)), border=1)
        pdf.cell(0, 6, "", border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # manifiesto de procedencia EMBEBIDO (seccion visible => texto extraible)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(31, 78, 121)
    pdf.multi_cell(0, 8, _txt("Manifiesto de procedencia"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9.5)
    art = manifiesto.get("artefacto", {})
    lineas = [
        f"Generador: {manifiesto.get('generador')} {manifiesto.get('version_generador')}",
        f"Sello de tiempo: {manifiesto.get('sello_tiempo')}",
        f"Artefacto: {art.get('tipo')} - {art.get('id')}",
        f"content_sha256: {art.get('content_sha256')}",
    ]
    for k, val in (manifiesto.get("versiones_ancladas") or {}).items():
        lineas.append(f"Version {k}: {val}")
    for k, val in (manifiesto.get("modelo_md5") or {}).items():
        lineas.append(f"md5 modelo {k}: {val}")
    inv = manifiesto.get("invariante") or {}
    if inv:
        lineas.append(f"Invariante suma declarada: {F.fmt_num(inv.get('suma_declarada', 0), 2)}")
    for ln in lineas:
        pdf.multi_cell(0, 5, _txt(ln), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(176, 0, 0)
    pdf.multi_cell(0, 5, _txt("Firmable: preparado para la firma electronica cualificada/PAdES del "
                              "destinatario. La procedencia interna la firma JM con GPG en el release "
                              "(Llave 2). El gate (Llave 1) verifica la integridad, no certifica."),
                   new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(salida))
    return salida
