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


# ============================================================================
# E0.2 · EMISIÓN — `salida-presupuesto` (C5) -> FIEBDC-3/2024 (.bc3)
# ============================================================================
# Dirección INVERSA de la ingesta (D34). Traducción DETERMINISTA: la misma
# `salida-presupuesto` produce el mismo .bc3 salvo el SELLO DE FECHA del ~V
# (parámetro `fecha`, el ÚNICO no-determinismo — D36). No inventa precios ni
# mediciones: LEE la salida tal cual (mismo patrón consumidor que el compositor C7).

# naturaleza del componente -> campo `tipo` del ~C (inverso de NATURALEZA, D31)
_TIPO = {"mano_obra": "1", "maquinaria": "2", "material": "3"}

# códec de Python -> token del juego de caracteres del ~V (inverso de CHARSETS, D36)
_CHARSET_TOKEN = {
    "utf-8": "UTF-8", "cp1252": "ANSI", "latin-1": "ISO-8859-1",
    "cp850": "850", "cp437": "437",
}

# sello de fecha por defecto del ~V (AAAAMMDD): DETERMINISTA y documentado
# (parametrizable con `fecha`; NUNCA date.today(), que rompería la reproducibilidad).
_FECHA_DEFAULT = "20260709"

_SEP_CAMPO = "|"
_SEP_SUB = "\\"


def _num(x) -> str:
    """Número -> cadena decimal canónica, sin float ni notación científica.
    1.0 -> '1'; 0.40 -> '0.4'; 16.2 -> '16.2'; 178.19 -> '178.19'."""
    d = Decimal(str(x)).normalize()
    if d == d.to_integral_value():
        d = d.quantize(Decimal("1"))
    return format(d, "f")


def _limpiar(s) -> str:
    """Neutraliza en un texto libre los separadores FIEBDC (no deben partir el
    registro) y los saltos de línea: `~|\\` -> `-//`, CR/LF -> espacio."""
    return (str(s if s is not None else "")
            .replace("~", "-").replace(_SEP_CAMPO, "/").replace(_SEP_SUB, "/")
            .replace("\r", " ").replace("\n", " ").strip())


def _rec(letra: str, *campos) -> str:
    """Un registro FIEBDC: `~<letra>|campo1|campo2|...|` (termina en separador)."""
    return "~" + letra + _SEP_CAMPO + _SEP_CAMPO.join(str(c) for c in campos) + _SEP_CAMPO


def emitir_bc3(salida: dict, *, fecha: str | None = None, charset: str = "utf-8",
               programa: str = "AQYRA", autor: str = "Aqyra",
               titulo: str | None = None) -> str:
    """Emite una `salida-presupuesto` (C5) como texto FIEBDC-3/2024 (.bc3).

    salida  -- dict `salida-presupuesto` (estado_mediciones + cuadro_precios_2 + …).
               Se LEE tal cual; no se recalcula (patrón C7).
    fecha   -- sello del ~V (AAAAMMDD). Por defecto `_FECHA_DEFAULT` (determinista).
    charset -- códec de salida ('utf-8' por defecto, D36; 'cp1252'/ANSI si el destino
               legacy lo exige). Fija el token del ~V; el CLI escribe con ese códec.
    Devuelve el texto .bc3 canónico (líneas CRLF, salto final).

    Subset EMITIDO v0 (D35/D38): `~V` (cabecera + charset + sello de fecha), `~C`
    (partidas tipo 0 + componentes del cuadro nº2 con su naturaleza), `~D`
    (descomposiciones), `~M` (mediciones: **desglose por objeto** desde
    `traza_cantidades` con el GUID en el comentario; **línea única** con la cantidad
    total cuando no hay traza — p. ej. `origen=regla`) y `~T` (pliego mínimo = la
    descripción de la partida).
    """
    fecha = fecha or _FECHA_DEFAULT
    token = _CHARSET_TOKEN.get(charset.lower().replace("_", "-"), "UTF-8")
    tit = _limpiar(titulo or salida.get("proyecto") or "Presupuesto Aqyra")
    cp2 = {c["codigo"]: c for c in salida.get("cuadro_precios_2", [])}

    v = _rec("V", programa, f"FIEBDC-3/2024{_SEP_SUB}{fecha}", _limpiar(autor), tit,
             token, "Emitido por Aqyra (engines/bc3.emitir_bc3); traduccion determinista salida-presupuesto -> FIEBDC-3/2024")

    c_hijos: list[str] = []
    c_part: list[str] = []
    d_recs: list[str] = []
    m_recs: list[str] = []
    t_recs: list[str] = []

    for p in salida.get("estado_mediciones", []):
        cod = p["codigo"]
        # --- componentes (cuadro nº2) -> conceptos hijo + descomposición ~D ---
        hijos = []
        for i, comp in enumerate(cp2.get(cod, {}).get("componentes", []), start=1):
            hcod = f"{cod}.{i}"
            c_hijos.append(_rec("C", hcod, comp.get("unidad", ""),
                                _limpiar(comp.get("descripcion", "")),
                                _num(comp.get("precio", 0)), fecha,
                                _TIPO.get(comp.get("tipo", ""), "3")))
            hijos.append((hcod, comp.get("rendimiento", 0)))
        # --- partida (tipo 0): precio = precio_unitario (eje coste canónico D16) ---
        c_part.append(_rec("C", cod, p.get("unidad", ""),
                           _limpiar(p.get("descripcion", "")),
                           _num(p.get("precio_unitario", 0)), fecha, "0"))
        if hijos:
            sub = _SEP_SUB.join(f"{h}{_SEP_SUB}1{_SEP_SUB}{_num(r)}" for h, r in hijos) + _SEP_SUB
            d_recs.append(_rec("D", cod, sub))
        # --- mediciones ~M (D35): desglose por objeto o línea única ---
        total = _num(p.get("cantidad", 0))
        traza = p.get("traza_cantidades") or []
        if traza:
            det = []
            for t in traza:  # grupo de 5: comentario(GUID) \ N \ longitud \ latitud \ altura
                det += [_limpiar(t.get("guid", "")), _num(t.get("cantidad", 0)), "", "", ""]
            m_recs.append(_rec("M", cod, "", total, _SEP_SUB.join(det)))
        else:
            m_recs.append(_rec("M", cod, "", total, ""))
        # --- pliego ~T mínimo (D38): la descripción de la partida ---
        t_recs.append(_rec("T", cod, _limpiar(p.get("descripcion", ""))))

    lineas = [v] + c_hijos + c_part + d_recs + m_recs + t_recs
    return "\r\n".join(lineas) + "\r\n"


def leer_bc3_presupuesto(origen) -> dict:
    """Re-lee un .bc3 FIEBDC-3/2024 (el emitido por `emitir_bc3`) y RECONSTRUYE el
    `estado_mediciones` (D34) — el cierre semántico del round-trip.

    Por cada partida con `~M`: la `cantidad` (suma de las líneas de medición, o el
    total declarado cuando no hay detalle), el `precio_unitario` (del `~C`), el
    `importe = cantidad × precio_unitario` (Decimal, HALF_UP, 2 dec) y la
    `trazabilidad` (los GUIDs de las líneas de detalle). NO recalcula el precio: lo
    LEE del concepto. El round-trip conserva los importes (D3: ±0,01; cant. ±0,5%).

    origen -- ruta a un .bc3, o el propio texto FIEBDC-3 (str que contenga '~').
    Devuelve `{"estado_mediciones": [...]}` (subconjunto de `salida-presupuesto`).
    """
    if isinstance(origen, str) and "~" in origen:
        texto = origen
    else:
        with open(origen, "rb") as f:
            raw = f.read()
        texto = raw.decode(_detectar_charset(raw))
    registros = _partir_registros(texto)

    conceptos: dict[str, dict] = {}
    descomp: dict[str, list] = {}
    mediciones: dict[str, dict] = {}
    orden: list[str] = []

    for rec in registros:
        letra = rec[:1]
        c = rec.split("|")
        if letra == "C":
            conceptos[c[1].strip()] = {
                "unidad": (c[2].strip() if len(c) > 2 else ""),
                "descripcion": (c[3].strip() if len(c) > 3 else ""),
                "precio": (c[4].split("\\")[0].strip() if len(c) > 4 and c[4].strip() else "0"),
                "tipo": (c[6].strip() if len(c) > 6 else ""),
            }
        elif letra == "D":
            partes = [p for p in (c[2].split("\\") if len(c) > 2 else []) if p != ""]
            descomp[c[1].strip()] = [
                (partes[i].strip(), partes[i + 1].strip(), partes[i + 2].strip())
                for i in range(0, len(partes) - 2, 3)
            ]
        elif letra == "M":
            codigo = c[1].strip()
            total = c[3].strip() if len(c) > 3 else ""
            campos = (c[4].split("\\") if len(c) > 4 and c[4] else [])
            objetos = []
            for i in range(0, len(campos) - 4, 5):  # grupos de 5
                guid, n = campos[i].strip(), campos[i + 1].strip()
                if not guid and not n:
                    continue
                objetos.append((guid, Decimal(n or "0")))
            cantidad = (sum((q for _, q in objetos), Decimal("0"))
                        if objetos else Decimal(total or "0"))
            if codigo not in mediciones:
                orden.append(codigo)
            mediciones[codigo] = {"cantidad": cantidad, "objetos": objetos}

    estado = []
    for codigo in orden:
        m = mediciones[codigo]
        cpto = conceptos.get(codigo, {})
        precio = Decimal(cpto.get("precio", "0") or "0")
        cantidad = m["cantidad"]
        componentes = []
        for hijo, factor, rend in descomp.get(codigo, []):
            hc = conceptos.get(hijo, {})
            ph = Decimal(hc.get("precio", "0") or "0")
            rend_ef = Decimal(factor or "1") * Decimal(rend or "0")
            componentes.append({
                "tipo": NATURALEZA.get(hc.get("tipo", ""), "material"),
                "descripcion": hc.get("descripcion", ""),
                "unidad": hc.get("unidad", ""),
                "rendimiento": float(rend_ef),
                "precio": float(ph),
                "subtotal": float(_q2(ph * rend_ef)),
            })
        estado.append({
            "codigo": codigo,
            "descripcion": cpto.get("descripcion", ""),
            "unidad": cpto.get("unidad", ""),
            "cantidad": float(cantidad),
            "precio_unitario": float(precio),
            "importe": float(_q2(cantidad * precio)),
            "trazabilidad": [g for g, _ in m["objetos"] if g],
            "componentes": componentes,
        })
    return {"estado_mediciones": estado}
