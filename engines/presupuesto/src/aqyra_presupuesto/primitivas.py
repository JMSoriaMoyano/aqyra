"""Librería FINITA de primitivas de medición del C5 (D8).

Espejo del registro de evaluadores del C3: el CRITERIO (pack anclado) es la tabla de verdad; el
engine sólo mapea a una primitiva. Añadir una partida de método conocido = sólo pack; un método
genuinamente nuevo = una primitiva nueva aquí (honesto, raro). Es lo que hace real el lema
"el código es un PACK anclado, no un `if`".

Selección ESTRUCTURAL (D8): el pack `criterio/AQ/v1` está anclado por hash y NO lleva un campo
`primitiva` explícito (añadirlo obligaría a re-anclarlo). Por tanto la primitiva se elige por la
FORMA del criterio: `reglas_por_clase` → `leer-cantidad`; `reglas_sin_geometria` → `partida-por-ratio`
(y los campos presentes lo confirman: `magnitud` vs `ratio`/`base`).

  leer-cantidad(objeto, pdef)         → {cantidad, criterio_aplicado, aviso?}
  partida-por-ratio(base, pdef)       → {cantidad(=1), importe, criterio_aplicado}
"""
from __future__ import annotations


def _valor_magnitud(objeto: dict, magnitud: str) -> float | None:
    """Valor de la cantidad `magnitud` del objeto (de sus Qto). `conteo` → 1."""
    if magnitud == "conteo":
        return 1.0
    for c in objeto.get("cantidades", []):
        if c.get("magnitud") == magnitud:
            return float(c.get("valor"))
    return None


def leer_cantidad(objeto: dict, pdef: dict) -> dict:
    """Primitiva de medición geométrica: lee la magnitud declarada por el criterio y aplica el
    `factor_caras`. Cuando `descuento_huecos` es cierto, la magnitud es la NETA (p. ej.
    `NetSideArea`), que por definición IFC ya descuenta los huecos → los huecos quedan
    contabilizados por el propio `Qto` (D7, no re-deriva geometría).

    Para que el hueco se tenga en cuenta de forma AUDITABLE: si el objeto tiene huecos y el `Qto`
    trae bruto y neto, se registra el descuento observado (`bruto − neto`) y se comprueba que
    supera el `umbral`; si el descuento no cuadra con la existencia de huecos, se emite un aviso.
    """
    magnitud = pdef.get("magnitud", "conteo")
    factor = float(pdef.get("factor_caras", 1))
    valor = _valor_magnitud(objeto, magnitud)
    aviso = None
    if valor is None:
        return {"cantidad": 0.0, "criterio_aplicado": f"{magnitud}: sin dato en el modelo", "aviso":
                {"codigo": pdef.get("codigo"), "nivel": "error",
                 "mensaje": f"El objeto {objeto.get('guid')} no declara {magnitud} en su Qto."}}

    cantidad = valor * factor
    caras = "1 cara" if factor == 1 else f"{int(factor)} caras (factor {int(factor)})"
    partes = [magnitud, caras]

    if pdef.get("descuento_huecos"):
        umbral = float(pdef.get("umbral_hueco_m2", 0.0))
        n_huecos = int(objeto.get("_huecos", 0))
        bruto = _valor_magnitud(objeto, "GrossSideArea")
        if n_huecos and bruto is not None:
            descuento = round(bruto - valor, 4)
            partes.append(
                f"descuento de huecos = {descuento:.2f} m2 (bruto {bruto:.2f} - neto {valor:.2f}), "
                f"{n_huecos} hueco/s > umbral {umbral:.2f} m2")
            # guarda de consistencia: el descuento observado debe corresponder a hueco(s) > umbral
            if descuento <= 0:
                aviso = {"codigo": pdef.get("codigo"), "nivel": "aviso",
                         "mensaje": (f"El objeto {objeto.get('guid')} tiene {n_huecos} hueco/s pero "
                                     f"su Qto no refleja descuento (bruto {bruto} == neto {valor}).")}
        elif n_huecos and bruto is None:
            partes.append(f"con descuento de huecos (umbral {umbral:.2f} m2) segun Qto neto")
        else:
            partes.append("sin huecos > umbral")

    return {"cantidad": cantidad, "criterio_aplicado": ", ".join(partes), "aviso": aviso}


def partida_por_ratio(base: float, pdef: dict) -> dict:
    """Primitiva de partida sin geometría (origen=regla, D5): importe = `ratio` × base (p. ej. el
    PEM medible). Cantidad = 1 (partida alzada); precio_unitario = importe."""
    ratio = float(pdef.get("ratio", 0.0))
    importe = ratio * float(base)
    nombre_base = pdef.get("base", "PEM_medible")
    return {"cantidad": 1, "importe": importe,
            "criterio_aplicado": f"regla sin geometria: {ratio:.0%} del {nombre_base} "
                                 f"({round(float(base), 2)} x {ratio})"}


# Registro (nombre → función). La única "tabla" del engine; el pack decide (por su forma) cuál.
PRIMITIVAS = {
    "leer-cantidad": leer_cantidad,
    "partida-por-ratio": partida_por_ratio,
}
