"""Motor de presupuesto del C5 (módulos 2–6, D7/D8) — `presupuestar(...)`.

Compone, sobre el modelo neutro de medición y los packs criterio+banco:
  · mapeo a partida(s) (un objeto → varias partidas) por el CRITERIO (primitivas finitas, D8);
  · motor económico: medición × precio del BANCO → importe → PEM → (+GG +BI) → base → (+IVA) → PEC;
  · justificación de mediciones (trazabilidad a los GUIDs) y de precios (cuadros nº1/nº2);
  · partidas sin geometría (origen=regla, D5): S&S = ratio × PEM medible.

Contract-first: reproduce la golden GOL-PRE-01 (PEM 7022.53 → PEC 10111.74). Determinista dado
criterio + banco. La salida conforma `salida-presupuesto.schema.json` (D1).
"""
from __future__ import annotations

from collections import OrderedDict
from decimal import ROUND_HALF_UP, Decimal

from .primitivas import PRIMITIVAS

__all__ = ["presupuestar", "CAPITULOS_DEFAULT", "num_a_letra"]


# --------------------------------------------------------------------------- #
# Catálogo de capítulos (WBS) — DEFAULT del engine, PACK-overridable (forward-open).             #
# El pack `criterio/AQ/v1` está anclado y no declara capítulos; el engine aporta un catálogo por  #
# DEFECTO (como `CLASES_ESTRUCTURALES` en el engine C3), que un criterio futuro podrá sobrescribir #
# (clave `capitulos`). Define capítulo, descripción y ORDEN de presentación de las partidas.       #
# --------------------------------------------------------------------------- #
CAPITULOS_DEFAULT = [
    ("C01", "Cimentacion", ["CSZ010"]),
    ("C02", "Estructura", ["EHS010", "EHL010"]),
    ("C03", "Albanileria", ["FAB010"]),
    ("C04", "Revestimientos", ["REV010", "PIN010"]),
    ("C05", "Carpinteria", ["PPM010"]),
    ("C06", "Seguridad y Salud", ["SYS010"]),
]
_CAP_OTROS = ("C99", "Otros")


def _catalogo(criterio: dict) -> list:
    cap = criterio.get("capitulos")
    if cap:  # forward-open: el pack puede declararlo (lista de [codigo, descripcion, [partidas]])
        return [(c[0], c[1], list(c[2])) for c in cap]
    return [(c, d, list(p)) for c, d, p in CAPITULOS_DEFAULT]


# --------------------------------------------------------------------------- #
# Aritmética monetaria: redondeo HALF-UP a 2 decimales (como el cálculo a mano del oráculo).      #
# --------------------------------------------------------------------------- #
def _d(x) -> Decimal:
    return Decimal(str(x))


def r2(x) -> float:
    return float(_d(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def r4(x) -> float:
    return float(_d(x).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def mul2(a, b) -> float:
    return float((_d(a) * _d(b)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _valor_eje(unitario, total, unidad, banco_ref, origen) -> dict:
    """Valor de UN eje para UNA partida (E1.2, D19): unitario × cantidad = total, en su unidad,
    con el banco de origen (ausente para origen=regla). Conforma `$defs.valor_eje` del contrato C5."""
    v: dict = {"unitario": unitario, "total": total, "unidad": unidad}
    if banco_ref:
        v["banco"] = banco_ref
    v["origen"] = origen
    return v


# --------------------------------------------------------------------------- #
# Número → letra (español, mayúsculas) para el cuadro de precios nº1.                             #
# --------------------------------------------------------------------------- #
_UNIDADES = ["", "UNO", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE", "DIEZ",
             "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISEIS", "DIECISIETE", "DIECIOCHO",
             "DIECINUEVE", "VEINTE", "VEINTIUNO", "VEINTIDOS", "VEINTITRES", "VEINTICUATRO",
             "VEINTICINCO", "VEINTISEIS", "VEINTISIETE", "VEINTIOCHO", "VEINTINUEVE"]
_DECENAS = ["", "", "", "TREINTA", "CUARENTA", "CINCUENTA", "SESENTA", "SETENTA", "OCHENTA", "NOVENTA"]
_CENTENAS = ["", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS", "SEISCIENTOS",
             "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"]


def _centenas_a_letra(n: int) -> str:
    if n == 0:
        return ""
    if n < 30:
        return _UNIDADES[n]
    if n < 100:
        d, u = divmod(n, 10)
        return _DECENAS[d] + (f" Y {_UNIDADES[u]}" if u else "")
    if n == 100:
        return "CIEN"
    c, r = divmod(n, 100)
    return _CENTENAS[c] + (f" {_centenas_a_letra(r)}" if r else "")


def _entero_a_letra(n: int) -> str:
    if n == 0:
        return "CERO"
    if n < 1000:
        return _centenas_a_letra(n)
    miles, resto = divmod(n, 1000)
    pref = "MIL" if miles == 1 else f"{_centenas_a_letra(miles)} MIL"
    return pref + (f" {_centenas_a_letra(resto)}" if resto else "")


def num_a_letra(precio: float) -> str:
    """'CIENTO SETENTA Y OCHO CON DIECINUEVE CENTIMOS' para 178.19 (cuadro de precios nº1)."""
    centimos = int((_d(precio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 100) % 100)
    entero = int(_d(precio))
    return f"{_entero_a_letra(entero)} CON {_entero_a_letra(centimos)} CENTIMOS"


# --------------------------------------------------------------------------- #
# Motor                                                                                            #
# --------------------------------------------------------------------------- #
def presupuestar(modelo: dict, criterio: dict, banco: dict, parametros: dict) -> dict:
    """Presupuesto trazable a partir del modelo neutro de medición + criterio + banco + parámetros.

    Determinista: mismo modelo + mismo criterio + mismo banco → mismo presupuesto. La salida
    conforma `salida-presupuesto.schema.json`.

    Eje de valor multi-eje (E1.2, D16-D19). `parametros.eje` (default ``"coste"``) selecciona el
    eje que representa el `banco` (cuyo valor unitario no es forzosamente €). El **mapeo
    clase→partida del criterio no cambia entre ejes**: se mide una vez y se valora en el eje pedido.
    - ``eje == "coste"`` (default): el coste vive en ``precio_unitario`` / ``importe`` (fuente de
      verdad canónica, D16); **no** se emite ``valores`` → salida byte-idéntica al C5 previo
      (GOL-PRE-01 intacta).
    - ``eje != "coste"``: además del cálculo, cada partida gana ``valores[eje]`` — el valor del eje
      ETIQUETADO con su unidad y su banco (D19, espejo + valor etiquetado). La unidad del eje la
      declara el banco (``unidad_eje``; fallback ``moneda``); su ref anclada, ``banco.ref``/``banco``.
    """
    objetos = modelo.get("objetos", [])
    reglas_clase = {r["clase"]: r.get("partidas", []) for r in criterio.get("reglas_por_clase", [])}
    reglas_sg = criterio.get("reglas_sin_geometria", [])

    banco_partida = {p["codigo"]: p for p in banco.get("partidas", [])}
    precio_banco = {c: p["precio"] for c, p in banco_partida.items()}

    # --- eje de valor (E1.2, D19). El eje coste (default) NO toca nada de lo de abajo: su rama es
    # el código C5 previo, byte a byte. Un eje NO-coste refleja el valor etiquetado en valores[eje].
    eje = str(parametros.get("eje", "coste"))
    es_coste = eje == "coste"
    unidad_eje = banco.get("unidad_eje") or banco.get("moneda") or parametros.get("moneda", "EUR")
    banco_ref = banco.get("ref") or banco.get("banco")

    catalogo = _catalogo(criterio)
    cap_de_codigo: dict[str, str] = {}
    orden_partida: dict[str, int] = {}
    idx = 0
    for cap_cod, _desc, partidas in catalogo:
        for cod in partidas:
            cap_de_codigo[cod] = cap_cod
            orden_partida[cod] = idx
            idx += 1

    # --- mapeo + medición (primitiva leer-cantidad, seleccionada por reglas_por_clase, D8) ---
    acc: "OrderedDict[str, dict]" = OrderedDict()
    avisos: list[dict] = []
    for obj in objetos:
        for pdef in reglas_clase.get(obj.get("clase"), []):
            res = PRIMITIVAS["leer-cantidad"](obj, pdef)
            if res.get("aviso"):
                avisos.append(res["aviso"])
            cod = pdef["codigo"]
            a = acc.get(cod)
            if a is None:
                a = {"codigo": cod, "unidad": pdef.get("unidad"), "cantidad": Decimal("0"),
                     "trazabilidad": [], "criterio_aplicado": res["criterio_aplicado"],
                     "detalle": []}
                acc[cod] = a
            a["cantidad"] += _d(res["cantidad"])
            g = obj.get("guid")
            if g and g not in a["trazabilidad"]:
                a["trazabilidad"].append(g)
            nombre = obj.get("nombre")
            if res.get("cantidad"):
                a["detalle"].append(f"{nombre} {res['cantidad']:.2f}" if nombre
                                    else f"{res['cantidad']:.2f}")

    # --- partidas origen=modelo → estado de mediciones (importe = cantidad × precio del banco) ---
    partidas_modelo: list[dict] = []
    for cod, a in acc.items():
        precio = precio_banco.get(cod)
        if precio is None:
            avisos.append({"codigo": cod, "nivel": "error",
                           "mensaje": f"La partida {cod} no tiene precio en el banco."})
            continue
        cantidad = r4(a["cantidad"])
        importe = mul2(cantidad, precio)
        crit = a["criterio_aplicado"]
        if a["detalle"]:
            crit = f"{crit} ({' + '.join(a['detalle'])})"
        p = {
            "codigo": cod,
            "capitulo": cap_de_codigo.get(cod, _CAP_OTROS[0]),
            "descripcion": banco_partida[cod].get("descripcion", cod),
            "unidad": a["unidad"] or banco_partida[cod].get("unidad"),
            "cantidad": cantidad,
            "precio_unitario": precio,
            "importe": importe,
            "criterio_aplicado": crit,
            "origen": "modelo",
            "trazabilidad": a["trazabilidad"],
        }
        if not es_coste:  # eje NO-coste: valor etiquetado (D19). El coste (default) no lo emite.
            p["valores"] = {eje: _valor_eje(precio, importe, unidad_eje, banco_ref, "modelo")}
        partidas_modelo.append(p)

    pem_medible = r2(sum(_d(p["importe"]) for p in partidas_modelo))

    # --- partidas sin geometría (origen=regla, primitiva partida-por-ratio, D5) ---
    partidas_regla: list[dict] = []
    for pdef in reglas_sg:
        res = PRIMITIVAS["partida-por-ratio"](pem_medible, pdef)
        importe = r2(res["importe"])
        p = {
            "codigo": pdef["codigo"],
            "capitulo": cap_de_codigo.get(pdef["codigo"], _CAP_OTROS[0]),
            "descripcion": pdef.get("descripcion", "Seguridad y salud (partida alzada)"),
            "unidad": pdef.get("unidad", "PA"),
            "cantidad": res["cantidad"],
            "precio_unitario": importe,
            "importe": importe,
            "criterio_aplicado": res["criterio_aplicado"],
            "origen": "regla",
            "trazabilidad": [],
        }
        if not es_coste:  # partida sin geometría: valor etiquetado del eje, sin banco (origen=regla).
            p["valores"] = {eje: _valor_eje(importe, importe, unidad_eje, None, "regla")}
        partidas_regla.append(p)

    # --- estado de mediciones ordenado por el catálogo (capítulo → orden de partida) ---
    todas = partidas_modelo + partidas_regla
    estado_mediciones = sorted(todas, key=lambda p: orden_partida.get(p["codigo"], 999))

    pem = r2(sum(_d(p["importe"]) for p in estado_mediciones))

    # --- resumen económico: PEM → (+GG +BI) → base → (+IVA) → PEC ---
    gg_pct, bi_pct, iva_pct = (float(parametros.get(k, 0)) for k in ("gg_pct", "bi_pct", "iva_pct"))
    gg = mul2(gg_pct, pem)
    bi = mul2(bi_pct, pem)
    base = r2(_d(pem) + _d(gg) + _d(bi))
    iva = mul2(iva_pct, base)
    pec = r2(_d(base) + _d(iva))

    # --- capítulos (parciales) ---
    imp_por_cod = {p["codigo"]: p["importe"] for p in estado_mediciones}
    capitulos = []
    for cap_cod, cap_desc, partidas in catalogo:
        presentes = [c for c in partidas if c in imp_por_cod]
        if not presentes:
            continue
        capitulos.append({
            "codigo": cap_cod,
            "descripcion": cap_desc,
            "partidas": presentes,
            "importe": r2(sum(_d(imp_por_cod[c]) for c in presentes)),
        })

    # --- cuadros de precios (justificación de precios) ---
    orden_banco = {p["codigo"]: i for i, p in enumerate(banco.get("partidas", []))}

    def _clave_cuadro(cod: str) -> tuple:
        return (0, orden_banco[cod]) if cod in orden_banco else (1, orden_partida.get(cod, 999))

    cuadro_1 = []
    for p in sorted(estado_mediciones, key=lambda p: _clave_cuadro(p["codigo"])):
        cuadro_1.append({
            "codigo": p["codigo"],
            "descripcion": p["descripcion"],
            "unidad": p["unidad"],
            "precio": p["precio_unitario"],
            "precio_en_letra": num_a_letra(p["precio_unitario"]),
        })

    cuadro_2 = []
    for cod in sorted((p["codigo"] for p in partidas_modelo), key=lambda c: _clave_cuadro(c)):
        bp = banco_partida[cod]
        cuadro_2.append({
            "codigo": cod,
            "unidad": bp.get("unidad"),
            "componentes": [
                {k: comp.get(k) for k in ("tipo", "descripcion", "unidad", "rendimiento",
                                          "precio", "subtotal") if k in comp}
                for comp in bp.get("componentes", [])
            ],
            "costes_indirectos": bp.get("costes_indirectos", 0),
            "precio_total": bp.get("precio"),
        })

    salida: dict = {
        "proyecto": modelo.get("proyecto") or "Presupuesto (C5)",
        "estado_mediciones": estado_mediciones,
        "cuadro_precios_1": cuadro_1,
        "cuadro_precios_2": cuadro_2,
        "resumen": {
            "moneda": parametros.get("moneda", "EUR"),
            "capitulos": capitulos,
            "PEM": pem,
            "gg_pct": gg_pct, "gg": gg,
            "bi_pct": bi_pct, "bi": bi,
            "base": base,
            "iva_pct": iva_pct, "iva": iva,
            "PEC": pec,
        },
    }
    if avisos:
        salida["avisos"] = avisos
    return salida
