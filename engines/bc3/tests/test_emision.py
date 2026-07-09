# -*- coding: utf-8 -*-
"""Golden de ROUND-TRIP de la EMISIÓN BC3 (E0.2) — texto puro, corre en CI y sandbox.

La Llave 1 de E0.2: el `.bc3` EMITIDO desde una `salida-presupuesto`, REIMPORTADO,
reproduce el `estado_mediciones` con IDENTIDAD DE IMPORTES. Consume como entrada la
`salida-presupuesto` ANCLADA de `GOL-PRE-01` (D4: se LEE, no se recalcula — mismo
patrón que el compositor C7). Anclaje SEMÁNTICO (D37): NO por md5 del `.bc3` (lleva
sello de fecha), sino por identidad de importes (±0,01) y cantidades (±0,5%, D3).
Un fallo se corrige en el CÓDIGO del emisor/re-lector, jamás aflojando el golden.
"""
import json
from pathlib import Path

from aqyra_bc3 import emitir_bc3, leer_bc3_presupuesto

REPO = Path(__file__).resolve().parents[3]
GOLDEN = REPO / "packages" / "golden" / "C5" / "GOL-PRE-01" / "expected.json"

# tolerancias.json de GOL-PRE-01 (D3): importes exactos ±0,01; cantidades ±0,5%.
IMPORTE_ABS = 0.01
CANTIDAD_REL = 0.005
FECHA = "20260709"  # sello determinista para el test (reproducible)


def _salida_anclada() -> dict:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))["presupuesto"]


def test_round_trip_identidad_de_importes():
    """emitir -> re-leer reproduce cada importe (±0,01) y cantidad (±0,5%) de GOL-PRE-01."""
    salida = _salida_anclada()
    bc3 = emitir_bc3(salida, fecha=FECHA)
    recon = {p["codigo"]: p for p in leer_bc3_presupuesto(bc3)["estado_mediciones"]}

    orig = salida["estado_mediciones"]
    assert set(recon) == {p["codigo"] for p in orig}, "el round-trip pierde o inventa partidas"
    for p in orig:
        r = recon[p["codigo"]]
        assert abs(r["importe"] - p["importe"]) <= IMPORTE_ABS, (
            f"{p['codigo']}: importe {r['importe']} != {p['importe']} (round-trip)")
        tol_q = max(abs(p["cantidad"]) * CANTIDAD_REL, 1e-9)
        assert abs(r["cantidad"] - p["cantidad"]) <= tol_q, (
            f"{p['codigo']}: cantidad {r['cantidad']} != {p['cantidad']} (>0,5%)")
        assert abs(r["precio_unitario"] - p["precio_unitario"]) <= IMPORTE_ABS


def test_round_trip_conserva_el_PEM():
    """La Σ de importes reconstruidos casa con el PEM anclado (7 022,53)."""
    salida = _salida_anclada()
    recon = leer_bc3_presupuesto(emitir_bc3(salida, fecha=FECHA))["estado_mediciones"]
    pem = round(sum(p["importe"] for p in recon), 2)
    assert abs(pem - salida["resumen"]["PEM"]) <= IMPORTE_ABS, f"PEM {pem} != {salida['resumen']['PEM']}"


def test_emision_determinista_2x():
    """Misma salida + mismo sello de fecha -> mismos bytes (traducción determinista)."""
    salida = _salida_anclada()
    assert emitir_bc3(salida, fecha=FECHA) == emitir_bc3(salida, fecha=FECHA)


def test_el_sello_de_fecha_es_el_unico_no_determinismo():
    """El sello de fecha (~V + fecha de cada ~C) es la ÚNICA variación entre emisiones:
    toda línea que difiere se explica sustituyendo un sello por el otro, y los ~D/~M/~T
    (que no llevan fecha) quedan idénticos."""
    salida = _salida_anclada()
    f1, f2 = "20260101", "20991231"
    a = emitir_bc3(salida, fecha=f1).splitlines()
    b = emitir_bc3(salida, fecha=f2).splitlines()
    assert len(a) == len(b)
    for x, y in zip(a, b):
        if x != y:
            assert x.replace(f1, f2) == y, f"diferencia no atribuible al sello: {x!r} vs {y!r}"
    sin_fecha = lambda ls: [l for l in ls if l[:2] in ("~D", "~M", "~T")]
    assert sin_fecha(a) == sin_fecha(b)


def test_subset_emitido_V_C_D_M_T():
    """El .bc3 lleva ~V (charset UTF-8), ~C (partidas), ~D, ~M y ~T (D35/D38)."""
    bc3 = emitir_bc3(_salida_anclada(), fecha=FECHA)
    assert "~V|" in bc3 and "|UTF-8|" in bc3          # cabecera + juego de caracteres
    assert "~C|FAB010|" in bc3 and "|0|" in bc3        # partida (tipo 0)
    assert "~D|FAB010|" in bc3                          # descomposición
    assert "~M|FAB010|" in bc3                          # medición
    assert "~T|FAB010|" in bc3                          # pliego mínimo


def test_charset_ansi_declara_su_token():
    """--charset cp1252 declara ANSI en el ~V (D36, parametrizable)."""
    bc3 = emitir_bc3(_salida_anclada(), fecha=FECHA, charset="cp1252")
    assert "|ANSI|" in bc3 and "|UTF-8|" not in bc3


def test_desglose_por_objeto_desde_traza_cantidades():
    """D35: con traza_cantidades, cada objeto es una línea ~M con su GUID; round-trip exacto."""
    salida = {
        "proyecto": "SINT",
        "estado_mediciones": [{
            "codigo": "EHL010", "descripcion": "Losa HA-25", "unidad": "m3",
            "cantidad": 16.2, "precio_unitario": 231.75, "importe": 3754.35,
            "origen": "modelo",
            "trazabilidad": ["GUID-SOLADO", "GUID-FORJADO"],
            "traza_cantidades": [
                {"guid": "GUID-SOLADO", "cantidad": 5.4},
                {"guid": "GUID-FORJADO", "cantidad": 10.8},
            ],
        }],
        "cuadro_precios_2": [],
    }
    bc3 = emitir_bc3(salida, fecha=FECHA)
    # dos líneas de detalle con sus GUIDs dentro del ~M
    assert "GUID-SOLADO" in bc3 and "GUID-FORJADO" in bc3
    r = leer_bc3_presupuesto(bc3)["estado_mediciones"][0]
    assert abs(r["cantidad"] - 16.2) <= 1e-9            # 5.4 + 10.8
    assert abs(r["importe"] - 3754.35) <= IMPORTE_ABS
    assert r["trazabilidad"] == ["GUID-SOLADO", "GUID-FORJADO"]


def test_linea_unica_cuando_no_hay_traza():
    """Sin traza_cantidades (p. ej. origen=regla), una sola línea ~M con la cantidad total."""
    salida = _salida_anclada()
    recon = {p["codigo"]: p for p in leer_bc3_presupuesto(emitir_bc3(salida, fecha=FECHA))["estado_mediciones"]}
    sys = recon["SYS010"]                                # S&S, origen=regla, sin geometría
    assert sys["trazabilidad"] == []
    assert abs(sys["cantidad"] - 1.0) <= 1e-9
    assert abs(sys["importe"] - 137.7) <= IMPORTE_ABS
