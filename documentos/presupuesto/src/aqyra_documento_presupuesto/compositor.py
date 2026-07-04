# -*- coding: utf-8 -*-
"""componer_documento — compositor DETERMINISTA del Documento de Presupuesto (C5 → .docx).

Convierte la salida AUTORITATIVA de C5 (`salida-presupuesto` JSON) en el documento firmable del
despacho. NO recalcula: formatea datos ya calculados. Determinista: mismo `presupuesto` + mismos
`parametros` (fecha, autor, orden fijos) => mismo CONTENIDO extraíble (texto + tablas).

Secciones (corte mínimo que reproduce el golden GOL-DOC-01):
  0. Carátula          — proyecto, moneda, fecha (inyectable), TOTAL (PEC) destacado.
  1. Estado de mediciones — por capítulo: tabla (código·descr·ud·cant·precio·importe) + PARCIAL.
  2. Cuadro de precios nº 1 — código·descr·ud·precio·precio EN LETRA.
  3. Cuadro de precios nº 2 — descomposición MO/materiales/maquinaria + costes indirectos.
  4. Resumen del presupuesto — capítulos + cadena PEM -> (+GG +BI) base -> (+IVA) PEC.
"""
from __future__ import annotations

from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH as AL

from . import formato as F

# Marcadores estables de sección (los usa el golden para detectar las 5 secciones).
SEC_CARATULA = "EJECUCION POR CONTRATA"     # aparece en la etiqueta del total de la carátula
SEC_MEDICIONES = "Estado de mediciones"
SEC_CP1 = "Cuadro de precios n. 1"
SEC_CP2 = "Cuadro de precios n. 2"
SEC_RESUMEN = "Resumen del presupuesto"

_R = AL.RIGHT
_L = AL.LEFT


def _pct(x) -> str:
    """0.13 -> '13'; 0.065 -> '6,5'."""
    v = float(x) * 100.0
    return F.fmt_num(v, 0) if abs(v - round(v)) < 1e-9 else F.fmt_num(v, 1)


def componer_documento(presupuesto: dict, parametros: dict | None = None) -> Path:
    """Compone el .docx y devuelve su ruta. `parametros`:
        salida  : ruta del .docx (por defecto ./<proyecto>.docx)
        fecha   : str (determinista; por defecto '-')
        autor   : str (por defecto '[Técnico competente] ICCP')
        titulo  : str (por defecto 'PRESUPUESTO')
    """
    par = dict(parametros or {})
    proyecto = str(presupuesto.get("proyecto", "Presupuesto"))
    resumen = presupuesto.get("resumen", {})
    moneda = resumen.get("moneda", "EUR")
    fecha = str(par.get("fecha") or "-")
    autor = str(par.get("autor") or "[Tecnico competente] ICCP . Col. [____]")
    titulo = str(par.get("titulo") or "PRESUPUESTO")
    salida = Path(par.get("salida") or (Path.cwd() / "Documento_Presupuesto.docx"))
    salida.parent.mkdir(parents=True, exist_ok=True)

    doc, sec = F.nuevo_doc()

    # ---------------------------------------------------------------- 0 · carátula
    pec = float(resumen.get("PEC", 0))
    F.caratula(
        doc, titulo, proyecto,
        campos=[("Proyecto", proyecto),
                ("Moneda", moneda),
                ("Fecha", fecha),
                ("Autor", autor)],
        total_etq="PRESUPUESTO DE EJECUCION POR CONTRATA (PEC):",
        total_val=F.fmt_eur(pec))

    # ---------------------------------------------------------------- 1 · mediciones
    F.H1(doc, "1. " + SEC_MEDICIONES)
    F.P(doc, "Medición trazable al modelo (origen: modelo / regla / manual). Importe = cantidad x "
             "precio unitario. Parcial por capítulo.")
    em = {p["codigo"]: p for p in presupuesto.get("estado_mediciones", [])}
    capitulos = resumen.get("capitulos", [])
    cab_med = ["Código", "Descripción", "Ud", "Cantidad", "Precio (" + moneda + ")",
               "Importe (" + moneda + ")"]
    anchos_med = [22, 66, 12, 22, 24, 26]
    alin_med = [_L, _L, _L, _R, _R, _R]
    for cap in capitulos:
        cod_cap = cap.get("codigo", "")
        F.H2(doc, f"Capítulo {cod_cap} · {cap.get('descripcion', '')}")
        filas = []
        for cod in cap.get("partidas", []):
            p = em.get(cod)
            if not p:
                continue
            filas.append([cod, p.get("descripcion", ""), p.get("unidad", ""),
                          F.fmt_num(p.get("cantidad", 0), 3),
                          F.fmt_num(p.get("precio_unitario", 0), 2),
                          F.fmt_num(p.get("importe", 0), 2)])
        # fila de PARCIAL del capítulo (la lee el golden: Sigma capítulos == PEM)
        filas.append([f"PARCIAL {cod_cap}", cap.get("descripcion", ""), "", "", "",
                      F.fmt_num(cap.get("importe", 0), 2)])
        F.tabla(doc, cab_med, filas, anchos_mm=anchos_med, alineaciones=alin_med)

    # ---------------------------------------------------------------- 2 · cuadro nº1
    doc.add_page_break()
    F.H1(doc, "2. " + SEC_CP1)
    F.P(doc, "Precio unitario en cifra y EN LETRA de cada partida.")
    filas1 = []
    for c in presupuesto.get("cuadro_precios_1", []):
        filas1.append([c.get("codigo", ""), c.get("descripcion", ""), c.get("unidad", ""),
                       F.fmt_num(c.get("precio", 0), 2), c.get("precio_en_letra", "")])
    F.tabla(doc, ["Código", "Descripción", "Ud", "Precio (" + moneda + ")", "Precio en letra"],
            filas1, anchos_mm=[20, 50, 10, 22, 70], alineaciones=[_L, _L, _L, _R, _L])

    # ---------------------------------------------------------------- 3 · cuadro nº2
    doc.add_page_break()
    F.H1(doc, "3. " + SEC_CP2)
    F.P(doc, "Descomposición del precio unitario: mano de obra, materiales, maquinaria y costes "
             "indirectos.")
    TIPO = {"mano_obra": "Mano de obra", "material": "Material", "maquinaria": "Maquinaria"}
    for c in presupuesto.get("cuadro_precios_2", []):
        cod = c.get("codigo", "")
        F.H2(doc, f"{cod} ({c.get('unidad', '')}) · Precio unitario: "
                  f"{F.fmt_eur(c.get('precio_total', 0))}")
        filas2 = []
        for comp in c.get("componentes", []):
            filas2.append([TIPO.get(comp.get("tipo"), comp.get("tipo", "")),
                           comp.get("descripcion", ""), comp.get("unidad", ""),
                           F.fmt_num(comp.get("rendimiento", 0), 3),
                           F.fmt_num(comp.get("precio", 0), 2),
                           F.fmt_num(comp.get("subtotal", 0), 2)])
        filas2.append(["Costes indirectos", "", "", "", "",
                       F.fmt_num(c.get("costes_indirectos", 0), 2)])
        filas2.append(["PRECIO TOTAL", "", "", "", "", F.fmt_num(c.get("precio_total", 0), 2)])
        F.tabla(doc, ["Tipo", "Descripción", "Ud", "Rend.", "Precio (" + moneda + ")",
                      "Subtotal (" + moneda + ")"],
                filas2, anchos_mm=[26, 60, 12, 18, 24, 26],
                alineaciones=[_L, _L, _L, _R, _R, _R])

    # ---------------------------------------------------------------- 4 · resumen
    doc.add_page_break()
    F.H1(doc, "4. " + SEC_RESUMEN)
    # 4a · resumen por capítulos (el golden lee estos importes: Sigma capítulos == PEM)
    F.H2(doc, "Resumen por capítulos")
    filas_cap = [[cap.get("codigo", ""), cap.get("descripcion", ""),
                  F.fmt_num(cap.get("importe", 0), 2)] for cap in capitulos]
    F.tabla(doc, ["Capítulo", "Descripción", "Importe (" + moneda + ")"], filas_cap,
            anchos_mm=[24, 100, 30], alineaciones=[_L, _L, _R])
    # 4b · cadena económica PEM -> ... -> PEC
    F.H2(doc, "Cadena PEM → PEC")
    gg_pct, bi_pct, iva_pct = resumen.get("gg_pct", 0), resumen.get("bi_pct", 0), resumen.get("iva_pct", 0)
    filas_res = [
        ["Presupuesto de Ejecución Material (PEM)", F.fmt_num(resumen.get("PEM", 0), 2)],
        [f"Gastos generales ({_pct(gg_pct)} %)", F.fmt_num(resumen.get("gg", 0), 2)],
        [f"Beneficio industrial ({_pct(bi_pct)} %)", F.fmt_num(resumen.get("bi", 0), 2)],
        ["Base imponible", F.fmt_num(resumen.get("base", 0), 2)],
        [f"IVA ({_pct(iva_pct)} %)", F.fmt_num(resumen.get("iva", 0), 2)],
        ["Presupuesto de Ejecución por Contrata (PEC)", F.fmt_num(resumen.get("PEC", 0), 2)],
    ]
    F.tabla(doc, ["Concepto", "Importe (" + moneda + ")"], filas_res,
            anchos_mm=[124, 30], alineaciones=[_L, _R])

    F.cabecera_pie(sec, proyecto, autor)
    F.cierre(doc, "Documento de PRESUPUESTO (predimensionado / asistencia). Sujeto a revisión y "
                  "firma por técnico competente. Generado de forma determinista desde la salida C5.")
    doc.save(str(salida))
    return salida
