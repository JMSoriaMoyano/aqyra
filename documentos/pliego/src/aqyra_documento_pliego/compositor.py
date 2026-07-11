# -*- coding: utf-8 -*-
"""componer_pliego — compositor DETERMINISTA del Pliego de Condiciones Tecnicas (C5 -> .docx).

Segundo compositor de la capa de documentos (patron `documento-presupuesto`, operador C7). Toma la
salida AUTORITATIVA de C5 (`salida-presupuesto` JSON: estado de mediciones trazable + valores por eje)
y el `criterio` (mapeo partida->clase->sistema), les anade el texto de prescripcion por partida y
compone el PLIEGO firmable del despacho. NO recalcula: formatea datos ya calculados. Determinista:
mismo presupuesto + mismo criterio + mismo pack de textos + mismos parametros (fecha/orden fijos) =>
mismo CONTENIDO extraible (texto + tablas). Sin LLM.

Cierra el trio coste + carbono + prescripcion sobre la MISMA medicion: por partida, prescripcion +
medicion trazable (cantidad + GUIDs) + coste (importe) + carbono (valores.carbono, forward-open).

Secciones (corte minimo que reproduce el golden GOL-PLI-01):
  0. Caratula                     — proyecto, objeto, fecha (inyectable), nota determinista.
  1. Condiciones generales        — clausulas generales del pliego (del pack de textos base).
  2. Prescripciones tecnicas particulares — por capitulo/sistema: por partida, prescripcion +
                                    medicion (cantidad, criterio, GUIDs) + coste + carbono forward-open.
  3. Cuadro de trazabilidad       — tabla partida -> GUIDs del modelo (el pliego ligado al objeto).
"""
from __future__ import annotations

from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH as AL

from . import formato as F

# Marcadores estables de seccion (los usa el golden para detectar las secciones).
SEC_CARATULA = "PLIEGO DE CONDICIONES TECNICAS"
SEC_GENERALES = "Condiciones generales"
SEC_PARTICULARES = "Prescripciones tecnicas particulares"
SEC_TRAZA = "Cuadro de trazabilidad al modelo"

_R = AL.RIGHT
_L = AL.LEFT

_AVISO_FALLBACK = " (prescripcion base pendiente de completar)"


def _mapas_criterio(criterio: dict) -> tuple[dict, dict, set]:
    """Del `criterio`: codigo_partida -> clase; clase -> (sistema, codigo_ss); codigos sin geometria."""
    cod_clase: dict[str, str] = {}
    for regla in (criterio or {}).get("reglas_por_clase", []):
        clase = regla.get("clase", "")
        for p in regla.get("partidas", []):
            cod = p.get("codigo")
            if cod:
                cod_clase[cod] = clase
    clase_sistema: dict[str, tuple] = {}
    for regla in (criterio or {}).get("reglas_sistema", []):
        clase = regla.get("clase")
        if clase and clase not in clase_sistema:      # primera regla que casa (precedencia)
            clase_sistema[clase] = (regla.get("sistema", ""), regla.get("codigo_ss"))
    sin_geo = {r.get("codigo") for r in (criterio or {}).get("reglas_sin_geometria", []) if r.get("codigo")}
    return cod_clase, clase_sistema, sin_geo


def _sistema_de(codigo, cod_clase, clase_sistema, sin_geo) -> tuple[str, str | None]:
    """Sistema funcional (y su Uniclass Ss) de una partida, del criterio."""
    clase = cod_clase.get(codigo)
    if clase and clase in clase_sistema:
        return clase_sistema[clase]
    if codigo in sin_geo:
        return ("Seguridad y salud", None)
    return ("Sin clasificar", None)


def _prescripcion(partida: dict, pack_textos: dict) -> str:
    """Cadena de fuente del texto (D4), con fallback determinista:
    (1) texto del banco por partida (bancos reales / ~T del BC3) -> (2) pack de textos base por partida
    -> (3) pack por clasificacion Uniclass -> (4) descripcion + aviso.
    """
    cod = partida.get("codigo", "")
    # (1) el texto que porte la propia partida (banco real / ~T ingerido)
    txt = partida.get("prescripcion") or partida.get("texto_pliego")
    if txt:
        return str(txt)
    por_part = (pack_textos or {}).get("por_partida", {})
    entrada = por_part.get(cod, {})
    # (2) pack de textos base, por codigo de partida (tipo de unidad de obra)
    if entrada.get("prescripcion"):
        return str(entrada["prescripcion"])
    # (3) fallback por clasificacion Uniclass (la que declare la partida o el propio pack)
    clasif = partida.get("clasificacion_uniclass") or entrada.get("clasificacion_uniclass")
    por_clasif = (pack_textos or {}).get("por_clasificacion_uniclass", {})
    if clasif and por_clasif.get(clasif):
        return str(por_clasif[clasif])
    # (4) fallback ultimo: descripcion + aviso
    return str(partida.get("descripcion", "")) + _AVISO_FALLBACK


def componer_pliego(presupuesto: dict, criterio: dict, parametros: dict | None = None) -> Path:
    """Compone el .docx del pliego y devuelve su ruta. `parametros`:
        salida       : ruta del .docx (por defecto ./Documento_Pliego.docx)
        pack_textos  : dict del pack de textos base (por_partida / por_clasificacion / generales)
        fecha        : str (determinista; por defecto '-')
        autor        : str (por defecto '[Tecnico competente] ICCP')
        titulo       : str (por defecto 'PLIEGO DE CONDICIONES TECNICAS')
        objeto       : str (alcance del pliego; por defecto el proyecto)
    """
    par = dict(parametros or {})
    pack_textos = par.get("pack_textos") or {}
    proyecto = str(presupuesto.get("proyecto", "Pliego"))
    fecha = str(par.get("fecha") or "-")
    autor = str(par.get("autor") or "[Tecnico competente] ICCP . Col. [____]")
    titulo = str(par.get("titulo") or SEC_CARATULA)
    objeto = str(par.get("objeto") or "Condiciones tecnicas de las unidades de obra del proyecto")
    salida = Path(par.get("salida") or (Path.cwd() / "Documento_Pliego.docx"))
    salida.parent.mkdir(parents=True, exist_ok=True)

    cod_clase, clase_sistema, sin_geo = _mapas_criterio(criterio)
    partidas = presupuesto.get("estado_mediciones", [])

    # capitulos: descripcion desde el resumen (si existe); orden = 1a aparicion en estado_mediciones
    resumen = presupuesto.get("resumen", {})
    desc_cap = {c.get("codigo", ""): c.get("descripcion", "") for c in resumen.get("capitulos", [])}
    orden_cap: list[str] = []
    por_cap: dict[str, list] = {}
    for p in partidas:
        cap = p.get("capitulo", "") or "-"
        if cap not in por_cap:
            por_cap[cap] = []
            orden_cap.append(cap)
        por_cap[cap].append(p)

    doc, sec = F.nuevo_doc()

    # ---------------------------------------------------------------- 0 · caratula
    F.caratula(
        doc, titulo, proyecto,
        campos=[("Proyecto", proyecto),
                ("Objeto", objeto),
                ("Fecha", fecha),
                ("Autor", autor)],
        total_etq="Cierra el trio:",
        total_val="coste + carbono + prescripcion",
        nota="Pliego de condiciones tecnicas generado de forma DETERMINISTA a partir de la salida "
             "autoritativa de C5 (medicion trazable + valores por eje) y del criterio. NO recalcula. "
             "Debe ser revisado y firmado por tecnico competente antes de su uso.")

    # ---------------------------------------------------------------- 1 · condiciones generales
    F.H1(doc, "1. " + SEC_GENERALES)
    generales = pack_textos.get("generales") or [
        "Condiciones generales no provistas por el pack de textos base."]
    for i, clausula in enumerate(generales, 1):
        F.P(doc, f"{i}. {clausula}")

    # ---------------------------------------------------------------- 2 · prescripciones particulares
    F.H1(doc, "2. " + SEC_PARTICULARES)
    F.P(doc, "Por cada unidad de obra: prescripcion tecnica, medicion trazable al modelo (cantidad y "
             "GUIDs), coste e (cuando consta) huella de carbono. Todo sobre la misma medicion.")
    for cap in orden_cap:
        F.H2(doc, f"Capitulo {cap} . {desc_cap.get(cap, '')}".rstrip(" ."))
        for p in por_cap[cap]:
            cod = p.get("codigo", "")
            sistema, ss = _sistema_de(cod, cod_clase, clase_sistema, sin_geo)
            etq_sist = f"  [Sistema: {sistema}" + (f" / {ss}]" if ss else "]")
            enc = doc.add_paragraph()
            renc = enc.add_run(f"{cod} . {p.get('descripcion', '')}{etq_sist}")
            renc.bold = True
            # prescripcion
            F.P(doc, "Prescripcion. " + _prescripcion(p, pack_textos))
            # medicion + valores (tabla concepto/valor)
            unidad = p.get("unidad", "")
            filas = [
                ["Partida", cod],
                ["Unidad de obra", unidad],
                ["Cantidad medida", f"{F.fmt_num(p.get('cantidad', 0), 3)} {unidad}"],
                ["Criterio de medicion", p.get("criterio_aplicado", "")],
                ["Origen", p.get("origen", "")],
                ["Precio unitario (coste)", F.fmt_eur(p.get("precio_unitario", 0))],
                ["Importe (coste)", F.fmt_eur(p.get("importe", 0))],
            ]
            carbono = (p.get("valores") or {}).get("carbono")
            if carbono:  # forward-open: solo si el presupuesto trae el eje carbono
                unidad_c = carbono.get("unidad", "kgCO2e")
                filas.append(["Huella de carbono", f"{F.fmt_num(carbono.get('total', 0), 2)} {unidad_c}"])
                for etapa, val in (carbono.get("etapas") or {}).items():
                    filas.append([f"  Carbono {etapa}", f"{F.fmt_num(val, 2)} {unidad_c}"])
            F.tabla(doc, ["Concepto", "Valor"], filas, anchos_mm=[60, 104], alineaciones=[_L, _L])
            # trazabilidad de la partida
            guids = p.get("trazabilidad") or []
            if guids:
                F.P(doc, "Trazabilidad al modelo (GUIDs): " + ", ".join(guids))
            else:
                F.P(doc, "Trazabilidad al modelo (GUIDs): sin geometria (origen regla).")

    # ---------------------------------------------------------------- 3 · cuadro de trazabilidad
    doc.add_page_break()
    F.H1(doc, "3. " + SEC_TRAZA)
    F.P(doc, "Ligazon partida -> objeto del modelo (GUIDs). La prescripcion queda trazable al objeto.")
    filas_tz = []
    for p in partidas:
        guids = p.get("trazabilidad") or []
        filas_tz.append([p.get("codigo", ""), p.get("descripcion", ""),
                         p.get("unidad", ""), F.fmt_num(p.get("cantidad", 0), 3),
                         ", ".join(guids) if guids else "(sin geometria)"])
    F.tabla(doc, ["Codigo", "Descripcion", "Ud", "Cantidad", "GUIDs"], filas_tz,
            anchos_mm=[20, 46, 12, 20, 66], alineaciones=[_L, _L, _L, _R, _L])

    F.cabecera_pie(sec, proyecto, autor, doc_label="Pliego")
    F.cierre(doc, "Documento de PLIEGO (predimensionado / asistencia). Sujeto a revision y firma por "
                  "tecnico competente. Generado de forma determinista desde la salida C5 y el criterio.")
    doc.save(str(salida))
    return salida
