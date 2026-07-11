# Diseño · Semilla REAL de carbono por la vía limpia (E5.2)

> El **cómo**. Decisiones **D45–D48 a ratificar por JM** (continúan D1–D44); se anclarán en
> `packages/contracts/C5-presupuesto/DECISIONES.md`. La IA propone; JM firma. El esquema de spec
> **no cambia** (delta NULO): E5.2 sólo añade un pack de datos + su golden.

## 0 · Principio rector

Un motor, varios ejes — y ahora, **dato real y trazable**. E5.2 no añade una línea de motor: reemplaza el
factor **sintético** del pack de demostración por un factor **derivado** de fuentes abiertas. La regla dura:
cada kgCO₂e es convención banco+criterio (estatuto del PEM), **pero no se inventa** — se deriva de dato
abierto real y se documenta su cadena (material → factor → cantidad → kgCO₂e/ud, con etapas EN 15978).

## 1 · Qué YA existe (no se rehace)

- **Motor:** `presupuestar(..., eje="carbono")` reparte `valores.carbono.etapas` con Σ etapas = total (D40);
  `engines/presupuesto` 0.5.0. Un banco-carbono nuevo se consume sin tocar el motor.
- **Forma del pack de carbono** (`banco-carbono/generico/v1`): por partida `precio` (factor unitario total) +
  `etapas` (factores por etapa por unidad, Σ = precio, guarda ±0,01) + **un** `componente` `tipo:"material"`
  (para que el cuadro nº2 conforme sin tocar el esquema, D39). El pack real **imita esta forma exacta**.
- **Loader + anclaje:** `aqyra_packs` (familia `banco-carbono` ya en `FAMILIAS`), `content_sha256` = sha256 del
  bloque `contenido` del `pack.json`; `md5_banco` = md5 de `banco.json`; golden de pack en `test_packs.py`;
  fila `[packs.banco_carbono]` en `versions.lock`.
- **Runner:** `_run_c5_carbono` (dispatch `expected.modo == "carbono"` bajo `run_case_c5`, D43). `GOL-CAR-02`
  reusa este runner sin código nuevo.
- **Criterio (las 7 partidas y su medición):** `IfcWall`→`FAB010`(m²)+`REV010`(m²)+`PIN010`(m²),
  `IfcSlab`→`EHL010`(m³), `IfcColumn`→`EHS010`(m³), `IfcFooting`→`CSZ010`(m³), `IfcDoor`→`PPM010`(ud),
  sin geometría `SYS010` (S&S, 2% PEM, `origen=regla`, sin etapas).

## 2 · D45 · Fuentes abiertas ratificadas + atribución (registro)

**Ratificadas por JM (2026-07-10)** — registro en `Aqyra-Negocio/RECONCILIACION_licencias-carbono.md`:
ADEME Base Empreinte (Licence Ouverte 2.0), ProBas/UBA (dl-de/by-2.0), UK GHG factors (OGL v3.0) como
primarias/complemento; USLCI (NREL) como secundaria **con la licencia por confirmar dataset a dataset antes de
anclar cualquier factor de ella**. Excluidas (permiso escrito): Ökobaudat, INIES, EC3, ICE (Bath).

**Atribución a arrastrar** (en `provenance` del pack y, cuando proceda, en la salida):
- ADEME → «Derivado de ADEME Base Empreinte — Licence Ouverte 2.0».
- ProBas → «Derivado de ProBas (Umweltbundesamt) — dl-de/by-2.0 — modificado por Aqyra» + URI del dataset
  (la licencia alemana exige **marcar el cambio**).
- UK → «Contiene información del sector público bajo Open Government Licence v3.0 (Crown copyright)».
- USLCI → citar el proceso/dataset concreto + su estatuto de dominio público una vez confirmado.

## 3 · D46 · id/version del pack real y estatuto de `generico/v1` (a ratificar)

`generico/v1` es **INTOCABLE** (lo ancla `GOL-CAR-01` por hash). El pack real es **NUEVO**.

| Opción | id/version | `generico/v1` | versions.lock `[packs.banco_carbono]` |
|---|---|---|---|
| **A (recomendada)** | `banco-carbono/generico/v2` | coexiste, **marcado demo** en su `fuente`/metadatos (sin editar el fichero anclado — la marca vive en la doc/DECISIONES) | pasa a `v2` como producción; `v1` sigue anclado por su propio `content_sha256` en la golden de pack y consumido explícitamente por `GOL-CAR-01` (patrón `criterio/AQ/v1`→`v2`) |
| **B** | id nuevo `banco-carbono/abierto/v1` | coexiste intacto | fila apunta a `abierto/v1`; `generico/*` = línea de demostración separada |
| **C** | `banco-carbono/generico/v2`, `v1` deprecado | `v1` marcado deprecado (pero NO borrado — su golden sigue) | pasa a `v2` |

**Recomendación: A** — mantiene la numeración limpia (v1 sintético → v2 real, como `criterio`), deja `v1`
intacto para `GOL-CAR-01`, y el pointer de producción del lock queda en el dato real. `GOL-CAR-01` referencia
`generico/v1` por su `content_sha256` explícito (no por el pointer del lock), así que repuntar el lock a `v2`
no la rompe. (Verificar en el recompute local antes del PR.)

## 4 · D47 · Método de derivación de los factores (a ratificar) — el corazón de E5.2

Para cada partida, el factor por unidad se **deriva** así (EN 15804 modular / EN 15978 por etapas):

```
factor_A1A3(partida) = Σ_material [ cantidad_material_por_unidad × factor_A1A3_material(fuente abierta) ]
factor_A4A5(partida) = transporte_A4 [ masa × distancia × factor_flete(UK GHG) ]
                       + construccion/residuo_A5 [ % sobre A1A3 o masa de residuo × factor ]
precio(partida)      = factor_A1A3 + factor_A4A5     (Σ etapas = precio; guarda ±0,01, D39)
```

Cada partida lleva un bloque **`provenance`** (aditivo; `pack.schema.json` admite `additionalProperties`, y el
motor sólo lee `precio`/`etapas`/`componentes`, así que `provenance` es documentación inerte para el engine):

```jsonc
"provenance": {
  "unidad_partida": "m3",
  "composicion": [
    { "material": "hormigon C25/30 (ready-mix)", "cantidad": 1.0, "unidad": "m3",
      "factor_A1A3": 265.0, "unidad_factor": "kgCO2e/m3",
      "fuente": "ADEME Base Empreinte", "licencia": "Licence Ouverte 2.0", "ref": "<id/URI del dato>" },
    { "material": "acero corrugado B500S", "cantidad": 90.0, "unidad": "kg",
      "factor_A1A3": 0.85, "unidad_factor": "kgCO2e/kg",
      "fuente": "ProBas (UBA)", "licencia": "dl-de/by-2.0", "ref": "<URI>", "modificado_por_Aqyra": true } ],
  "A4A5": { "masa_kg": 2610, "distancia_km": 50, "factor_flete": 0.107, "unidad_factor": "kgCO2e/t·km",
            "fuente_transporte": "UK GHG Conversion Factors", "licencia": "OGL v3.0",
            "residuo_pct": 0.0 },
  "calculo": "A1A3 = 1×265 + 90×0.85 = 341.5 ; A4A5 = 2.61 t × 50 km × 0.107 = 13.96 ; total = 355.46",
  "nota": "Cantidades de material por unidad de partida = hipótesis de despacho documentada (no medición del modelo)."
}
```

- **Trazabilidad:** cada número del `precio`/`etapas` es reproducible desde `provenance` (material × factor ×
  cantidad). La composición por unidad de partida (kg de acero/m³, kg de ladrillo/m², etc.) es una **hipótesis
  de despacho** explícita y documentada, no un dato del modelo — es lo que convierte un factor por material en
  un factor por partida.
- **Determinismo:** los factores son constantes ancladas; el motor no recalcula la derivación (vive en la doc).
- **Reparto A1A3/A4A5:** A1A3 = producto (materiales); A4A5 = transporte (UK) + construcción/residuo. Coherente
  con EN 15978; la última etapa absorbe el residuo de redondeo en el motor (D40), pero en el **pack** Σ etapas =
  precio con guarda ±0,01 (D39).
- **Opción rechazable:** inventar (como en v1) — descartado, es justo lo que E5.2 elimina.

> Los **valores numéricos concretos** (los factores de ADEME/ProBas/UK por material) se fijan en `opsx:apply`,
> documentando cada uno con su fuente/licencia/URI; este diseño fija el **método y la estructura**, no los
> números (que requieren consultar los datasets ratificados uno a uno).

## 5 · D48 · Golden (a ratificar)

| Opción | Qué ancla | Recompute |
|---|---|---|
| **A (recomendada)** | golden de pack (identidad de contenido, `content_sha256` + md5) **+** `GOL-CAR-02` = valora la medición de `GOL-PRE-01` con el pack REAL por `_run_c5_carbono`; oráculo del eje a mano ×2 (determinismo + semántica + invariante Σ, patrón `GOL-CAR-01`, sin md5 de salida) | `GOL-CAR-02` pasa por `medir()` → **recompute en el conda `mcp-bim` de JM** (ifcopenshell), NO en el sandbox |
| **B** | sólo golden de pack (identidad de contenido) | todo en el sandbox (texto puro) |

**Recomendación: A** — cierra el eje con una golden que **usa** el pack real end-to-end (no sólo su hash),
igual que `GOL-CAR-01` cerró el sintético. `GOL-CAR-01` queda **intacta**. Nuevo oráculo del eje (PEM carbono
real) calculado a mano y verificado ×2 en el apply, con los factores derivados.

## 6 · Versionado y no-regresión

- **Sin bump de engine** (el motor no se toca). `versions.lock [packs.banco_carbono]` según D46.
- **Sin release** (Llave 2 del carbono real espera decisión de JM).
- El golden de pack (hash/md5) y la derivación (aritmética) se unit-testean en el **sandbox** (texto puro).
  Si D48 = A, el recompute de `GOL-CAR-02` (pasa por `medir()`/ifcopenshell) corre en el conda `mcp-bim` local
  de JM antes del PR — como `GOL-CAR-01`/`GOL-PRE-03`. `GOL-PRE-01/02/03`, `GOL-DOC-01` y `GOL-CAR-01`
  byte-idénticas/intactas.
