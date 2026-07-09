# -*- coding: utf-8 -*-
"""Adaptador FIEBDC-3/2024 (.bc3) -> pack `banco` de Aqyra.

E0.1 (ingesta): `ingerir_bc3(path) -> dict` con el MISMO esquema que
`data/packs/banco/AQ-DEMO/v1/banco.json`. Traducción DETERMINISTA (no cálculo):
el mismo .bc3 produce el mismo banco.json byte a byte.

Subset v0 (D31): ~V (cabecera + juego de caracteres), ~C (conceptos), ~D
(descomposiciones), ~T (texto de pliego, se parsea; NO se emite al banco v0).
~M (mediciones) es de E0.2 (emisión/round-trip): aquí se ignora si aparece.

Precio/CI (D32): subtotal = precio_hijo * factor * rendimiento (Decimal, HALF_UP,
2 dec); precio_partida = Σ subtotales + costes_indirectos (pct v0 = 3%, parámetro;
gancho forward para leerlo de los coeficientes del BC3), con GUARDA de consistencia
±0,01 contra el precio declarado en el ~C (aviso auditable, nunca se silencia).

Texto PURO: corre en el sandbox y en CI (no necesita ifcopenshell).
"""
from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_UP

# naturaleza del concepto (campo "tipo" del ~C) -> componente del banco (D31):
#   0/vacío = partida (tiene ~D) · 1 = mano de obra · 2 = maquinaria · 3 = material
NATURALEZA = {"1": "mano_obra", "2": "maquinaria", "3": "material"}

# token del juego de caracteres del ~V -> códec de Python (D31: ANSI por defecto)
CHARSETS = {
    "ANSI": "cp1252", "ANSI-1252": "cp1252", "1252": "cp1252",
    "850": "cp850", "437": "cp437",
    "UTF-8": "utf-8", "UTF8": "utf-8",
    "ISO-8859-1": "latin-1", "ISO8859-1": "latin-1", "LATIN1": "latin-1",
}

_CI_DEFAULT = "0.03"


def _q2(x: Decimal) -> Decimal:
    """Redondeo monetario a 2 decimales, HALF_UP (determinista, sin float)."""
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _partir_registros(texto: str) -> list[str]:
    """Un registro FIEBDC empieza en '~' y sigue hasta el próximo '~' (los saltos de
    línea internos son válidos). Devuelve los cuerpos SIN el '~', normalizando CRLF."""
    out = []
    for trozo in texto.split("~"):
        cuerpo = trozo.strip("\r\n").rstrip()
        if cuerpo:
            out.append(cuerpo)
    return out


def _detectar_charset(raw: bytes) -> str:
    """Lee el juego de caracteres del ~V decodificando en latin-1 (superset seguro)."""
    for rec in _partir_registros(raw.decode("latin-1", errors="replace")):
        if rec[:1] == "V":
            campos = rec.split("|")
            token = (campos[5] if len(campos) > 5 else "").strip().upper()
            return CHARSETS.get(token, "cp1252")
    return "cp1252"


def ingerir_bc3(path, *, banco: str, titulo: str | None = None,
                costes_indirectos_pct: str = _CI_DEFAULT) -> dict:
    """Lee un .bc3 (FIEBDC-3/2024) y devuelve el dict `banco` (esquema AQ-DEMO).

    banco   -- identidad del pack destino, p. ej. "AQ-BC3-DEMO/v1".
    titulo  -- si None, se toma de la cabecera del ~V.
    costes_indirectos_pct -- % de costes indirectos v0 (str -> Decimal exacto).
    """
    with open(path, "rb") as f:
        raw = f.read()
    texto = raw.decode(_detectar_charset(raw))
    registros = _partir_registros(texto)

    ci_pct = Decimal(costes_indirectos_pct)
    conceptos: dict[str, dict] = {}
    descomp: dict[str, list] = {}
    textos: dict[str, str] = {}
    cabecera = ""

    for rec in registros:
        letra = rec[:1]
        c = rec.split("|")
        if letra == "V":
            cabecera = c[4].strip() if len(c) > 4 else ""
        elif letra == "C":
            codigo = c[1].strip()
            conceptos[codigo] = {
                "unidad": (c[2].strip() if len(c) > 2 else ""),
                "resumen": (c[3].strip() if len(c) > 3 else ""),
                "precio": (c[4].split("\\")[0].strip() if len(c) > 4 and c[4].strip() else ""),
                "tipo": (c[6].strip() if len(c) > 6 else ""),
            }
        elif letra == "D":
            padre = c[1].strip()
            partes = [p for p in (c[2].split("\\") if len(c) > 2 else []) if p != ""]
            triples = [(partes[i].strip(), partes[i + 1].strip(), partes[i + 2].strip())
                       for i in range(0, len(partes) - 2, 3)]
            descomp[padre] = triples
        elif letra == "T":
            textos[c[1].strip()] = (c[2].strip() if len(c) > 2 else "")
        # ~M y demás: ignorados en v0 (gancho forward E0.2)

    partidas = []
    avisos = []
    for codigo, triples in descomp.items():  # dict preserva orden de aparición (~D)
        cpto = conceptos.get(codigo, {})
        componentes = []
        suma = Decimal("0")
        for hijo, factor, rend in triples:
            hc = conceptos.get(hijo)
            if hc is None:
                avisos.append(f"{codigo}: hijo {hijo} sin concepto ~C")
                continue
            precio_h = Decimal(hc["precio"] or "0")
            rend_efectivo = Decimal(factor or "1") * Decimal(rend or "0")
            subtotal = _q2(precio_h * rend_efectivo)
            componentes.append({
                "tipo": NATURALEZA.get(hc["tipo"], "material"),
                "descripcion": hc["resumen"],
                "unidad": hc["unidad"],
                "rendimiento": float(rend_efectivo),
                "precio": float(precio_h),
                "subtotal": float(subtotal),
            })
            suma += subtotal
        ci = _q2(suma * ci_pct)
        precio = _q2(suma + ci)
        declarado = cpto.get("precio", "")
        if declarado and abs(Decimal(declarado) - precio) > Decimal("0.01"):
            avisos.append(f"{codigo}: precio ~C {declarado} != compuesto {precio} "
                          f"(sub {suma} + CI {ci})")
        partidas.append({
            "codigo": codigo,
            "unidad": cpto.get("unidad", ""),
            "descripcion": cpto.get("resumen", ""),
            "clasificacion_uniclass": [],  # FIEBDC-3 no porta Uniclass nativa (gancho forward)
            "componentes": componentes,
            "costes_indirectos": float(ci),
            "precio": float(precio),
        })

    resultado = {
        "banco": banco,
        "titulo": titulo or cabecera or banco,
        "descripcion": ("Banco ingerido de un .bc3 FIEBDC-3/2024 de muestra (PROPIO, sintético). "
                        "Traducción determinista .bc3 -> pack banco; precios de demostración, no de mercado."),
        "moneda": "EUR",
        "costes_indirectos_pct": float(ci_pct),
        "partidas": partidas,
    }
    if avisos:
        resultado["_avisos_ingesta"] = avisos
    return resultado


def serializar_banco(banco: dict) -> str:
    """Serialización CANÓNICA del banco.json (indent 2, UTF-8, salto final). Única
    fuente de verdad para el md5 del pack: el mismo dict -> los mismos bytes."""
    return json.dumps(banco, ensure_ascii=False, indent=2) + "\n"
