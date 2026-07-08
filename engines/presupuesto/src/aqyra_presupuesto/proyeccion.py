"""Proyección del C5 (E2.2, D24-D29): group-by determinista del valor por eje y corte.

`proyectar(presupuesto, modelo, eje, corte)` AGRUPA lo que ya existe — **no re-mide ni re-valora**
(la proyección es consulta, N-06). El valor vive por PARTIDA (`estado_mediciones[]`), el corte por
OBJETO (`modelo.objetos[].cortes`, E2.1). Dos saltos:

    partida ──(D26: magnitud EXACTA)──▶ objeto ──(D20/D21: fraccion de E2.1)──▶ grupo
     valor_P     share_O = q_O / Σq_O          valor_O            valor_O × fraccion

`Σ grupos == Σ partidas` por construcción (`Σ share_O = 1`, `Σ fraccion ≤ 1`); lo no atribuible cae en
RESIDUALES deterministas (D27) para que el invariante sea EXACTO. Sin ifcopenshell: puro y testeable en
el sandbox sobre un presupuesto + modelo sintéticos.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

CORTES = ("espacial", "funcional", "uniclass", "gubim")

# Grupos residuales (D27): conservan Σ cuando el valor no es atribuible a un grupo real.
SIN_GEOMETRIA = "(sin geometría)"   # partida origen=regla (sin trazabilidad): S&S, ayudas, PA…
SIN_CLASIFICAR = "(sin clasificar)"  # objeto sin el eje de corte pedido (o atribución parcial)

_EPS = Decimal("0.0000001")


def _d(x) -> Decimal:
    return Decimal(str(x))


def _r2(x) -> float:
    return float(_d(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _valor_partida(p: dict, eje: str) -> tuple[Decimal, str | None]:
    """Valor de la partida en el `eje` pedido (D25) + su unidad. coste → importe; otro → valores[eje]."""
    if eje == "coste":
        return _d(p.get("importe", 0)), None  # la unidad (moneda) se fija fuera, del resumen
    v = (p.get("valores") or {}).get(eje)
    if not v:
        return Decimal("0"), None
    return _d(v.get("total", 0)), v.get("unidad")


def proyectar(presupuesto: dict, modelo: dict, eje: str = "coste", corte: str = "espacial") -> list[dict]:
    """Proyecta el valor del `eje` por los grupos del `corte` (D24-D27). Group-by determinista.

    Devuelve `[{grupo, valor_total, unidad, n_partidas, guids[], fuente}]`, ordenado por primera
    aparición del grupo. `fuente` del grupo = la de sus pertenencias (`criterio` gana sobre `ifc`:
    traza honesta del *fallback* D22; `—` en residuales). No re-mide (usa `traza_cantidades`, D26).
    """
    if corte not in CORTES:
        raise ValueError(f"corte desconocido: {corte!r} (∈ {CORTES})")

    objetos = {o.get("guid"): o for o in modelo.get("objetos", [])}
    moneda = (presupuesto.get("resumen") or {}).get("moneda", "EUR")

    acc: dict[str, dict] = {}
    orden: list[str] = []

    def _aporta(grupo, valor, unidad, fuente, guid, cod):
        b = acc.get(grupo)
        if b is None:
            b = {"valor": Decimal("0"), "unidad": unidad, "fuente": fuente,
                 "guids": [], "partidas": set()}
            acc[grupo] = b
            orden.append(grupo)
        b["valor"] += valor
        if b["unidad"] is None and unidad is not None:
            b["unidad"] = unidad
        if fuente == "criterio":       # el fallback del criterio marca el grupo (D22, traza honesta)
            b["fuente"] = "criterio"
        if guid and guid not in b["guids"]:
            b["guids"].append(guid)
        b["partidas"].add(cod)

    for p in presupuesto.get("estado_mediciones", []):
        cod = p.get("codigo")
        valor_p, unidad = _valor_partida(p, eje)
        if eje == "coste":
            unidad = moneda
        if valor_p == 0:               # sin valor en este eje → no aporta (forward-open, Σ intacto)
            continue

        guids = p.get("trazabilidad") or []
        if not guids:                  # origen=regla (S&S…): sin objetos → residual (D27)
            _aporta(SIN_GEOMETRIA, valor_p, unidad, "regla", None, cod)
            continue

        # reparto partida→objeto por magnitud EXACTA (D26): share_O = q_O / Σq_O, de traza_cantidades
        pesos = {t.get("guid"): _d(t.get("cantidad", 0)) for t in (p.get("traza_cantidades") or [])}
        total = sum((pesos.get(g, Decimal("0")) for g in guids), Decimal("0"))
        n = len(guids)
        for g in guids:
            share = (pesos.get(g, Decimal("0")) / total) if total > 0 else (Decimal("1") / n)
            valor_o = valor_p * share
            obj = objetos.get(g)
            membresias = ((obj or {}).get("cortes") or {}).get(corte) or []
            sfr = Decimal("0")
            for m in membresias:       # objeto→grupo por la fraccion de E2.1 (incl. 50/50 ya resuelto)
                fr = _d(m.get("fraccion", 1.0))
                sfr += fr
                _aporta(m.get("grupo"), valor_o * fr, unidad, m.get("fuente", "ifc"), g, cod)
            resto = valor_o * (Decimal("1") - sfr)   # sin corte / atribución parcial → residual (D27)
            if resto > _EPS:
                _aporta(SIN_CLASIFICAR, resto, unidad, "—", g, cod)

    salida: list[dict] = []
    for grupo in orden:
        b = acc[grupo]
        salida.append({
            "grupo": grupo,
            "valor_total": _r2(b["valor"]),
            "unidad": b["unidad"] or moneda,
            "n_partidas": len(b["partidas"]),
            "guids": list(b["guids"]),
            "fuente": b["fuente"],
        })
    return salida


def suma_proyeccion(filas: list[dict]) -> float:
    """Σ de `valor_total` de una proyección (para el invariante Σ == estado_mediciones)."""
    return _r2(sum((_d(f["valor_total"]) for f in filas), Decimal("0")))
