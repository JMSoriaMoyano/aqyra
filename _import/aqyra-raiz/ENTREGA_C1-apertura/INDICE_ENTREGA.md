# Entrega C1 — apertura de familias P1 (índice)

Hilo de `Estructurando` (motor / contrato C1), 2026-06-28. **Implementado y probado por la IA;
golden VERDE.** Falta el **paso de JM** (registrar + firmar + anclar). Ver
`FICHA_golden_C1-APERTURA-01.md` y `Aqyra-Raiz/PASO-JM_C1_registro-golden-y-firma.md`.

## 1. Código (en `Estructurando`, zona del motor)

- `narracion-ifc/spec_to_ifc.py` (v0.7) — huecos generalizados (vía única), doble clasificación
  en todos los elementos, catálogo abierto (`ifcClass`), handler `alineaciones[]`.
- `narracion-ifc/clasificacion.py` (NUEVO) — doble clasificación determinista bsDD+Uniclass(EF).
- `narracion-ifc/alineaciones_ifc.py` (NUEVO) — puente alto.json → constructor de la Ola 5.
- `narracion-ifc/catalogo_ifc.py` — `crear_elemento` usa la vía única de doble clasificación.
- `narracion-ifc/compilar_spec.py` — pasa `alineaciones[]` (y `cubiertas`) al spec canónico.
- `narracion-ifc/spec.schema.json` (v0.2) — FORWARD-OPEN documentado.
- `iso19650-openbim/scripts/lineal/generate_test_ifc_lineal.py` — refactor: constructor
  reutilizable `construir_alineacion(...)`; `main` lo reusa (sin regresión en `test_lineal.py`).

## 2. Texto de contrato

- `Estructurando/Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` — nuevo **§7**.

## 3. Versión

- `iso19650-openbim` → **0.10.0** (plugin.json + CHANGELOG). Propuesta; reconciliar skew al anclar.

## 4. Golden (este directorio) — para registrar/firmar en `Estructurando 2.0`

- `FICHA_golden_C1-APERTURA-01.md`, `golden_C1-APERTURA-01.alto.json`,
  `golden_C1-APERTURA-01.spec.json`, `golden_C1-APERTURA-01.ifc`, `RESULTADO_oraculo.txt`.

## Reglas respetadas

- Retrocompatible (consumidores existentes sin regresión: verificado).
- Capacidad completa, no rebanada (clotoide + alzado + peralte + huecos genéricos + clases abiertas YA).
- Reutiliza la maquinaria de la Ola 5 (no reimplementa geometría de alineación).
- Dos llaves: golden verde (Llave 1, hecha) + firma de JM (Llave 2, pendiente). La IA **no** certifica.
