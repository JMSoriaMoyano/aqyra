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

# --------------------------------------------------------------------------- #
# Slice B (D-RB-5/D-RB-6): estructura de capítulos POR CLASIFICACIÓN. El presupuesto puede         #
# estructurarse por la clasificación que el MODELO ya porta (Uniclass / GuBIMClass) en vez de por  #
# el catálogo del engine. Tabla código-de-grupo→título ANCLADA (semilla embebida, como             #
# CAPITULOS_DEFAULT; la golden GOL-PRE-06 la ancla). El grupo Uniclass es el 2.º nivel EF; el grupo #
# GuBIM es el 1.er segmento del código. FORWARD: mover a un pack `capitulos/<sistema>/vN` y el      #
# nivel fino / Uniclass Ss cuando entre una tabla real completa (regla de tres).                    #
# --------------------------------------------------------------------------- #
_GRUPOS_TITULO = {
    "uniclass": {
        "EF_20": "Estructura",
        "EF_25": "Cerramientos, particiones y carpinteria",
        "EF_30": "Forjados y cubiertas",
    },
    "gubim": {
        "10": "Cimentaciones",
        "20": "Estructura",
        "30": "Cerramientos y particiones",
        "40": "Revestimientos y acabados",
        "50": "Carpinteria y cerrajeria",
    },
}
_CAP_SIN = ("SIN", "Sin clasificacion (seguridad y salud / partidas alzadas)")
_CLAVE_CLASIF = {"uniclass": "clasificacion_uniclass", "gubim": "clasificacion_gubim"}


def _grupo_clasif(codigos, estructura: str):
    """Grupo de clasificación de una partida (2.º nivel EF en Uniclass; 1.er segmento en GuBIM).
    `codigos`: lista de códigos de la partida (p. ej. ["EF_25_10"] o ["30.30.10"]). None si vacía."""
    if not codigos:
        return None
    c = str(codigos[0])
    if estructura == "uniclass":
        parts = c.split("_")
        return "_".join(parts[:2]) if len(parts) >= 2 else c
    return c.split(".")[0] if "." in c else c  # gubim: 1.er segmento


def _catalogo(criterio: dict) -> list:
    cap = criterio.get("capitulos")
    if cap:  # forward-open: el pack puede declararlo (lista de [codigo, descripcion, [partidas]])
        return [(c[0], c[1], list(c[2])) for c in cap]
    return [(c, d, list(p)) for c, d, p in CAPITULOS_DEFAULT]


def _catalogo_por_clasificacion(banco: dict, criterio: dict, estructura: str) -> list:
    """Slice B (D-RB-5): construye el catálogo AGRUPANDO las partidas por su grupo de clasificación
    (Uniclass EF / GuBIM), con la tabla código→título anclada. Las partidas sin clasificación y las
    partidas sin geometría (S&S, ratio) van al capítulo `_CAP_SIN`. El COSTE no cambia: cada partida
    cae en un único capítulo, luego Σ capítulos == PEM (idéntico al modo `catalogo`)."""
    clave = _CLAVE_CLASIF[estructura]
    titulos = _GRUPOS_TITULO.get(estructura, {})
    grupos: "OrderedDict[str, list]" = OrderedDict()
    for p in banco.get("partidas", []):
        g = _grupo_clasif(p.get(clave) or [], estructura) or _CAP_SIN[0]
        grupos.setdefault(g, []).append(p["codigo"])
    for r in criterio.get("reglas_sin_geometria", []):  # S&S y partidas alzadas: sin clasificación
        cod = r.get("codigo")
        if cod:
            grupos.setdefault(_CAP_SIN[0], []).append(cod)
    # orden determinista: grupos clasificados por su código; el capítulo sin clasificación, al final
    orden = sorted(grupos.keys(), key=lambda g: (g == _CAP_SIN[0], g))
    return [(g, (_CAP_SIN[1] if g == _CAP_SIN[0] else titulos.get(g, g)), list(grupos[g]))
            for g in orden]


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


# Orden canónico de etapas del ciclo de vida (EN 15978) para el reparto determinista (E3/D40).
ETAPAS_ORDEN = ("A1A3", "A4A5", "B", "C", "D")


def _etapas_eje(bp: dict, cantidad, total) -> dict | None:
    """E3 (D39/D40). Reparte el total del eje en etapas del ciclo de vida (EN 15978) a partir de los
    factores POR ETAPA que declara el banco por unidad (`bp["etapas"]`, p. ej. carbono A1A3/A4A5).
    etapa_total = factor_etapa × cantidad (redondeo 2 dec); la ÚLTIMA etapa presente ABSORBE el
    residuo de redondeo -> invariante Σ etapas = total EXACTO (D18). Sin factores -> None (sin etapas,
    forward-open: p. ej. origen=regla). Orden determinista: ETAPAS_ORDEN + claves extra ordenadas."""
    fac = bp.get("etapas") if bp else None
    if not fac:
        return None
    presentes = [k for k in ETAPAS_ORDEN if k in fac] + sorted(k for k in fac if k not in ETAPAS_ORDEN)
    if not presentes:
        return None
    et: dict = {}
    acc = Decimal("0")
    for k in presentes[:-1]:
        et[k] = mul2(fac[k], cantidad)
        acc += _d(et[k])
    et[presentes[-1]] = r2(_d(total) - acc)   # residuo -> Σ etapas = total exacto (D18)
    return et


def _valor_eje(unitario, total, unidad, banco_ref, origen, etapas=None) -> dict:
    """Valor de UN eje para UNA partida (E1.2, D19; E3/D40 etapas): unitario × cantidad = total, en su
    unidad, con el banco de origen (ausente para origen=regla) y, si el banco declara factores por
    etapa, el desglose `etapas` (EN 15978) con Σ etapas = total. Conforma `$defs.valor_eje` del C5."""
    v: dict = {"unitario": unitario, "total": total, "unidad": unidad}
    if banco_ref:
        v["banco"] = banco_ref
    v["origen"] = origen
    if etapas:
        v["etapas"] = etapas
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

    # Slice B (D-RB-5): estructura de capítulos. `catalogo` (default) = WBS del engine/criterio; con
    # `uniclass`/`gubim` se AGRUPA por el grupo de clasificación que el modelo porta (coste intacto:
    # cada partida cae en un capítulo, Σ capítulos == PEM). Default -> salida byte-idéntica (GOL-PRE-01..05).
    estructura = str(parametros.get("estructura_capitulos", "catalogo"))
    if estructura in _CLAVE_CLASIF:
        catalogo = _catalogo_por_clasificacion(banco, criterio, estructura)
    else:
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
                     "detalle": [], "contrib": OrderedDict()}
                acc[cod] = a
            a["cantidad"] += _d(res["cantidad"])
            g = obj.get("guid")
            if g and g not in a["trazabilidad"]:
                a["trazabilidad"].append(g)
            # E2.2 (D26): contribución de CANTIDAD por objeto a esta partida — habilita el reparto por
            # magnitud EXACTA de proyectar() sin re-medir. Se acumula por GUID (un objeto puede entrar
            # más de una vez en la misma partida) y se emite como `traza_cantidades` (origen=modelo).
            if g:
                a["contrib"][g] = a["contrib"].get(g, Decimal("0")) + _d(res["cantidad"])
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
            # Slice A (D-RB-1): la descripcion de tabla = `resumen` del banco (corto); compatibilidad:
            # si el banco no declara `resumen`, se usa la `descripcion` de siempre (bancos v0).
            "descripcion": banco_partida[cod].get("resumen") or banco_partida[cod].get("descripcion", cod),
            "unidad": a["unidad"] or banco_partida[cod].get("unidad"),
            "cantidad": cantidad,
            "precio_unitario": precio,
            "importe": importe,
            "criterio_aplicado": crit,
            "origen": "modelo",
            "trazabilidad": a["trazabilidad"],
        }
        # Slice A (D-RB-1): el TEXTO ampliado de la unidad de obra (especificacion del banco, patron
        # BEDEC/BCCA/CYPE) viaja a la partida (aditivo, forward-open). Los compositores lo renderizan
        # bajo la partida; el ~T del BC3 ya lo transporta. Invisible al recompute (GOL-PRE-01 intacta).
        texto = banco_partida[cod].get("texto")
        if texto:
            p["texto"] = texto
        # E2.2 (D26): desglose de cantidad por objeto (aditivo, forward-open). Habilita el reparto por
        # magnitud EXACTA de la proyección; Σ traza_cantidades == cantidad de la partida. GOL-PRE-01
        # sigue verde (el recompute compara claves nombradas — esta clave nueva le es invisible).
        if a.get("contrib"):
            p["traza_cantidades"] = [{"guid": gg, "cantidad": r4(c)} for gg, c in a["contrib"].items()]
        if not es_coste:  # eje NO-coste: valor etiquetado (D19) + etapas del banco (E3/D40).
            et = _etapas_eje(banco_partida[cod], cantidad, importe)
            p["valores"] = {eje: _valor_eje(precio, importe, unidad_eje, banco_ref, "modelo", et)}
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
