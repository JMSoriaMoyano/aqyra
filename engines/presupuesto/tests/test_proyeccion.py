"""Tests PUROS de la proyección (E2.2, D24-D29) — sin ifcopenshell, corren en el sandbox.

Ejercitan `proyectar` sobre un presupuesto + modelo SINTÉTICOS que reproducen la forma de GOL-PRE-01:
dos muros a la misma partida (FAB010) con magnitudes distintas (15,90 / 18,00), una partida sin
geometría (S&S, origen=regla), un objeto sin corte, un tabique 50/50 y una pertenencia por *fallback*
del criterio. Verifican: el invariante Σ (D27), el reparto por magnitud EXACTA (D26), los residuales
(D27), el determinismo (D28) y la lectura de un eje no-coste (D25).
"""
from __future__ import annotations

from aqyra_presupuesto import proyectar, suma_proyeccion
from aqyra_presupuesto.proyeccion import SIN_CLASIFICAR, SIN_GEOMETRIA

# --- presupuesto sintético (PEM = 409,00): FAB010 (2 muros) + PPM010 (puerta) + SYS010 (S&S regla) ---
PRES = {
    "resumen": {"moneda": "EUR", "PEM": 409.00},
    "estado_mediciones": [
        {"codigo": "FAB010", "importe": 339.00, "origen": "modelo",
         "trazabilidad": ["W1", "W2"],
         "traza_cantidades": [{"guid": "W1", "cantidad": 15.90}, {"guid": "W2", "cantidad": 18.00}],
         "valores": {"carbono": {"total": 100.0, "unidad": "kgCO2e"}}},
        {"codigo": "PPM010", "importe": 50.00, "origen": "modelo",
         "trazabilidad": ["D1"], "traza_cantidades": [{"guid": "D1", "cantidad": 1}],
         "valores": {"carbono": {"total": 10.0, "unidad": "kgCO2e"}}},
        {"codigo": "SYS010", "importe": 20.00, "origen": "regla", "trazabilidad": [],
         "valores": {"carbono": {"total": 5.0, "unidad": "kgCO2e"}}},
    ],
}

# --- modelo sintético: cortes por objeto (E2.1) ---
MODELO = {"objetos": [
    {"guid": "W1", "cortes": {
        "espacial": [{"grupo": "Planta-01", "fraccion": 1.0, "fuente": "ifc"}],
        "funcional": [{"grupo": "Aulas", "fraccion": 0.5, "fuente": "ifc"},
                      {"grupo": "Admin", "fraccion": 0.5, "fuente": "ifc"}],   # tabique 50/50
        "uniclass": [{"grupo": "EF_25_10", "fraccion": 1.0, "fuente": "ifc"}]}},
    {"guid": "W2", "cortes": {
        "espacial": [{"grupo": "Planta-02", "fraccion": 1.0, "fuente": "ifc"}],
        "funcional": [{"grupo": "Aulas", "fraccion": 1.0, "fuente": "ifc"}],
        "uniclass": [{"grupo": "EF_25_10", "fraccion": 1.0, "fuente": "ifc"}]}},
    {"guid": "D1", "cortes": {
        "espacial": [{"grupo": "Planta-01", "fraccion": 1.0, "fuente": "ifc"}],
        "funcional": [{"grupo": "Carpintería", "fraccion": 1.0, "fuente": "criterio"}]}},
        # D1 sin `uniclass` → residual en esa vista
]}


def _grupos(filas):
    return {f["grupo"]: f for f in filas}


def test_invariante_suma_por_corte():
    """Σ proyección == PEM para cada corte (D27), incluidas las partidas sin geometría."""
    for corte in ("espacial", "funcional", "uniclass"):
        filas = proyectar(PRES, MODELO, "coste", corte)
        assert suma_proyeccion(filas) == 409.00, (corte, filas)


def test_reparto_por_magnitud_exacta():
    """El importe de FAB010 se reparte 15,90/33,90 y 18,00/33,90 (D26), no 50/50."""
    g = _grupos(proyectar(PRES, MODELO, "coste", "espacial"))
    # FAB010 339 → W1 159,00 (Planta-01, + puerta 50) ; W2 180,00 (Planta-02)
    assert g["Planta-01"]["valor_total"] == 209.00      # 159,00 (muro) + 50,00 (puerta)
    assert g["Planta-02"]["valor_total"] == 180.00
    assert g[SIN_GEOMETRIA]["valor_total"] == 20.00     # S&S (origen=regla)
    assert g["Planta-01"]["fuente"] == "ifc"


def test_zona_5050():
    """El tabique reparte su valor 50/50 entre zonas; Σ por zonas == total (D26/E2.1)."""
    g = _grupos(proyectar(PRES, MODELO, "coste", "funcional"))
    # W1 (159,00) → Aulas 79,50 + Admin 79,50 ; W2 (180,00) → Aulas 180,00
    assert g["Aulas"]["valor_total"] == 259.50
    assert g["Admin"]["valor_total"] == 79.50
    assert g["Carpintería"]["fuente"] == "criterio"     # *fallback* del criterio visible (D22)
    assert g["Carpintería"]["valor_total"] == 50.00


def test_residual_sin_clasificar():
    """Un objeto sin el eje de corte pedido cae en (sin clasificar), conservando Σ (D27)."""
    g = _grupos(proyectar(PRES, MODELO, "coste", "uniclass"))
    assert g["EF_25_10"]["valor_total"] == 339.00       # los dos muros
    assert g[SIN_CLASIFICAR]["valor_total"] == 50.00    # la puerta (sin uniclass)
    assert g[SIN_GEOMETRIA]["valor_total"] == 20.00


def test_eje_no_coste():
    """Eje no-coste: lee valores[eje].total y su unidad; invariante Σ sobre el eje (D25)."""
    filas = proyectar(PRES, MODELO, "carbono", "espacial")
    g = _grupos(filas)
    assert all(f["unidad"] == "kgCO2e" for f in filas)
    assert suma_proyeccion(filas) == 115.0              # 100 + 10 + 5
    assert g["Planta-01"]["valor_total"] == 56.90       # 100*15,90/33,90 (=46,90) + puerta 10
    assert g["Planta-02"]["valor_total"] == 53.10


def test_determinismo():
    """proyectar 2× → misma salida (D28)."""
    a = proyectar(PRES, MODELO, "coste", "funcional")
    b = proyectar(PRES, MODELO, "coste", "funcional")
    assert a == b


def test_degenerado_equitativo():
    """Sin traza_cantidades (Σpeso=0), reparto equitativo 1/n conservando Σ."""
    pres = {"resumen": {"moneda": "EUR"}, "estado_mediciones": [
        {"codigo": "EHL010", "importe": 100.00, "origen": "modelo", "trazabilidad": ["S1", "S2"]}]}
    modelo = {"objetos": [
        {"guid": "S1", "cortes": {"espacial": [{"grupo": "P1", "fraccion": 1.0, "fuente": "ifc"}]}},
        {"guid": "S2", "cortes": {"espacial": [{"grupo": "P2", "fraccion": 1.0, "fuente": "ifc"}]}}]}
    g = _grupos(proyectar(pres, modelo, "coste", "espacial"))
    assert g["P1"]["valor_total"] == 50.00 and g["P2"]["valor_total"] == 50.00


def test_corte_desconocido():
    import pytest
    with pytest.raises(ValueError):
        proyectar(PRES, MODELO, "coste", "inexistente")


if __name__ == "__main__":   # ejecución directa en el sandbox (sin pytest)
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and name != "test_corte_desconocido":
            fn()
            print(f"OK {name}")
    print("PURE OK")
