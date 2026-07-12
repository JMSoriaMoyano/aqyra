# -*- coding: utf-8 -*-
"""Primer CONSUMIDOR del rail de export: el compositor de la PROYECCION de valor (Nivel 2, D-EX-2).

Toma el JSON AUTORITATIVO de proyeccion (shape de GOL-PRE-03: {vistas:[{eje,corte,suma,
grupos:[{grupo,valor_total,fuente,unidad?}]}]}) y lo RENDERIZA a los formatos del entregable
—Word (informe del despacho, reusa el formato comun) y XLSX (proyeccion tabular)—, reproduciendo
EXACTAMENTE las cifras/grupos/Sigma ancladas. NO recalcula: LEE el artefacto ya anclado.
Determinista: mismo artefacto + mismo descriptor + mismo sello => mismo CONTENIDO extraible.

El PDF sellado (el firmable) lo produce `sellado.py`. Este modulo hace los dos entregables humanos.
"""
from __future__ import annotations

from pathlib import Path

from aqyra_documento_comun import formato as F

_UNIDAD_EJE = {"coste": "EUR", "carbono": "kgCO2e"}


def _unidad(vista: dict, grupo: dict | None = None) -> str:
    if grupo and grupo.get("unidad"):
        return str(grupo["unidad"])
    if vista.get("unidad"):
        return str(vista["unidad"])
    return _UNIDAD_EJE.get(vista.get("eje", "coste"), "")


def seleccionar_vistas(artefacto: dict, descriptor: dict) -> list:
    """Las vistas del artefacto, filtradas por eje/corte si el descriptor los fija (si no, todas)."""
    vistas = list(artefacto.get("vistas") or [])
    eje = descriptor.get("eje")
    corte = descriptor.get("corte")
    if eje:
        vistas = [v for v in vistas if v.get("eje") == eje]
    if corte:
        vistas = [v for v in vistas if v.get("corte") == corte]
    return vistas


# ------------------------------------------------------------------ WORD (informe del despacho)
def informe_word(artefacto: dict, descriptor: dict, manifiesto: dict, salida: Path) -> Path:
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    proyecto = str(artefacto.get("proyecto", "Proyeccion de valor"))
    fecha = str(descriptor.get("sello_tiempo") or "-")
    autor = str(descriptor.get("autor") or "[Tecnico competente] ICCP . Col. [____]")
    vistas = seleccionar_vistas(artefacto, descriptor)
    suma_total = float(vistas[0].get("suma", 0.0)) if vistas else 0.0
    unidad_total = _unidad(vistas[0]) if vistas else ""

    doc, sec = F.nuevo_doc()
    F.caratula(
        doc, "INFORME DE PROYECCION DE VALOR", proyecto,
        campos=[("Proyecto", proyecto), ("Fecha", fecha),
                ("Ejes/cortes", ", ".join(sorted({f"{v.get('eje')}/{v.get('corte')}" for v in vistas})) or "-"),
                ("Autor", autor)],
        total_etq="Valor proyectado (Suma):",
        total_val=f"{F.fmt_num(suma_total, 2)} {unidad_total}",
        nota="Informe generado de forma DETERMINISTA a partir de la proyeccion AUTORITATIVA de Aqyra "
             "(consulta, no calculo). Los numeros son los anclados. El firmable es el PDF sellado con "
             "el manifiesto de procedencia; debe ser firmado por tecnico competente antes de su uso.")

    F.H1(doc, "1. Proyeccion de valor por eje y corte")
    F.P(doc, "Cada vista agrupa el mismo valor medido por un corte (espacial, funcional, Uniclass...). "
             "La suma de los grupos reproduce el total del eje (invariante).")
    for i, v in enumerate(vistas, 1):
        eje, corte = v.get("eje", "coste"), v.get("corte", "-")
        F.H2(doc, f"Vista {i}: {eje} por {corte}")
        filas = []
        for g in v.get("grupos", []):
            filas.append([str(g.get("grupo", "")), F.fmt_num(g.get("valor_total", 0), 2),
                          _unidad(v, g), str(g.get("fuente", ""))])
        filas.append([f"SUMA ({corte})", F.fmt_num(v.get("suma", 0), 2), _unidad(v), ""])
        F.tabla(doc, ["Grupo", "Valor", "Unidad", "Fuente"], filas,
                anchos_mm=[86, 34, 20, 24],
                alineaciones=[None, F.WD_ALIGN_PARAGRAPH.RIGHT if hasattr(F, "WD_ALIGN_PARAGRAPH") else None, None, None])

    # 2 · manifiesto de procedencia (la evidencia del sellado, tambien en el .docx)
    F.H1(doc, "2. Manifiesto de procedencia")
    F.P(doc, "Liga este entregable al artefacto autoritativo por su huella y ancla la procedencia. La "
             "firma GPG de JM (Llave 2) se aplica en el release sobre este manifiesto.")
    art = manifiesto.get("artefacto", {})
    filas_m = [
        ["Generador", f"{manifiesto.get('generador')} {manifiesto.get('version_generador')}"],
        ["Sello de tiempo", str(manifiesto.get("sello_tiempo"))],
        ["Artefacto", f"{art.get('tipo')} · {art.get('id')}"],
        ["content_sha256", str(art.get("content_sha256"))],
    ]
    for k, val in (manifiesto.get("versiones_ancladas") or {}).items():
        filas_m.append([f"Version · {k}", str(val)])
    for k, val in (manifiesto.get("modelo_md5") or {}).items():
        filas_m.append([f"md5 modelo · {k}", str(val)])
    inv = manifiesto.get("invariante") or {}
    if inv:
        filas_m.append(["Invariante · suma declarada", F.fmt_num(inv.get("suma_declarada", 0), 2)])
    F.tabla(doc, ["Concepto", "Valor"], filas_m, anchos_mm=[54, 110],
            alineaciones=[None, None])

    F.cabecera_pie(sec, proyecto, autor, doc_label="Proyeccion")
    F.cierre(doc, "Informe de PROYECCION DE VALOR (asistencia). Sujeto a revision y firma por tecnico "
                  "competente. Generado de forma determinista desde la proyeccion autoritativa de Aqyra.")
    doc.save(str(salida))
    return salida


# ------------------------------------------------------------------ XLSX (proyeccion tabular)
def proyeccion_xlsx(artefacto: dict, descriptor: dict, manifiesto: dict, salida: Path) -> Path:
    from datetime import datetime
    from openpyxl import Workbook

    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    vistas = seleccionar_vistas(artefacto, descriptor)

    # sello determinista en las propiedades (nunca now())
    sello = str(descriptor.get("sello_tiempo") or "1970-01-01")
    try:
        dt = datetime.strptime(sello, "%Y-%m-%d")
    except ValueError:
        dt = datetime(1970, 1, 1)

    wb = Workbook()
    wb.properties.created = dt
    wb.properties.modified = dt
    wb.properties.creator = manifiesto.get("generador", "aqyra-documento-export")
    ws = wb.active
    ws.title = "Proyeccion"
    ws.append(["Vista", "Eje", "Corte", "Grupo", "Valor", "Unidad", "Fuente"])
    for i, v in enumerate(vistas, 1):
        eje, corte = v.get("eje", "coste"), v.get("corte", "-")
        for g in v.get("grupos", []):
            ws.append([f"V{i}", eje, corte, str(g.get("grupo", "")),
                       round(float(g.get("valor_total", 0)), 2), _unidad(v, g), str(g.get("fuente", ""))])
        ws.append([f"V{i}", eje, corte, f"SUMA ({corte})",
                   round(float(v.get("suma", 0)), 2), _unidad(v), ""])

    wm = wb.create_sheet("Manifiesto")
    wm.append(["Concepto", "Valor"])
    art = manifiesto.get("artefacto", {})
    wm.append(["content_sha256", str(art.get("content_sha256"))])
    wm.append(["sello_tiempo", str(manifiesto.get("sello_tiempo"))])
    wm.append(["artefacto", f"{art.get('tipo')} · {art.get('id')}"])
    for k, val in (manifiesto.get("versiones_ancladas") or {}).items():
        wm.append([f"version.{k}", str(val)])
    for k, val in (manifiesto.get("modelo_md5") or {}).items():
        wm.append([f"md5.{k}", str(val)])
    wb.save(str(salida))
    return salida


# registro de formatos del consumidor de PROYECCION (gestion, secundario). El PDF vive en sellado.py.
def _proyeccion_pdf(artefacto, descriptor, manifiesto, salida):
    from . import sellado as SE
    return SE.firmable_pdf(artefacto, descriptor, manifiesto, salida)


FORMATOS = {
    "word": ("informe-proyeccion.docx", informe_word),
    "xlsx": ("proyeccion.xlsx", proyeccion_xlsx),
    "pdf":  ("proyeccion-firmable.pdf", _proyeccion_pdf),
}
