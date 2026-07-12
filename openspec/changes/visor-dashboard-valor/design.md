# Diseño técnico · Skin del visor · Dashboard de valor (E6.1)

> Complementa `proposal.md`. Fija la superficie de la piel, el **contrato de la vista** (el JSON de proyección
> que consume, sin cálculo en cliente), la aceptación por reproducción de `GOL-PRE-03` y la frontera de
> gobierno (todo `apps/`, «propone»). Gobernado por `docs/frontend-standards.md` (visor `apps/`, TDD, Llave 1).
> No fija hex definitivos (los del design system, Ola 3). Espejo de las skins de disciplina/auditoría.

## 1 · Superficie de la piel (`apps/visor`)

Naturaleza **`apps/` pura**: la UI vive en `apps/visor`; la proyección se **consume** (precomputada). Layout
espejo de las skins existentes (columna izquierda + centro 3D + dock), con el panel de valor:

- **Selectores:** **eje** (Coste `EUR` / Carbono `kgCO2e`) × **corte** (Espacial / Funcional / Uniclass). Cada
  combinación `(eje, corte)` = una vista de la proyección (la que `proyectar` produce).
- **Tabla de proyección:** una fila por grupo — `grupo · valor_total · unidad · n_partidas · fuente`. Orden =
  el de la proyección (primera aparición, determinista). Los grupos residuales (`(sin geometría)`,
  `(sin clasificar)`) se muestran con marca visual (no se ocultan — traza honesta del invariante Σ).
- **Gráfica de barras:** `valor_total` por grupo (misma escala, misma unidad); la barra hereda el chip de
  `fuente` (color/estado). Sin librería de cálculo: la barra es geometría de la fila.
- **Selección → 3D:** al elegir un grupo, se **resaltan sus `guids[]`** en el maestro (reutiliza la selección
  del `Viewer`, como las skins). Bidireccional opcional (seleccionar en 3D → resaltar el grupo) = forward.
- **Pastilla de invariante:** «Σ grupos == total del eje» (verde si casa ±0,01) — es la garantía visible de
  que la vista no inventa (el invariante de `GOL-PRE-03`).
- **Barra de estado:** «El motor proyecta · se siente gratis» · «El muro de cobro es el export firmable (dos
  llaves) — llega». Chip `data-state`: la proyección mostrada es dato firmado aguas arriba; el export = forward.

## 2 · Mapeo a la capacidad real del repo

| Superficie de la piel | Capacidad real | Estado | Naturaleza |
|---|---|---|---|
| Proyección `(eje, corte)` | `proyectar(presupuesto, modelo, eje, corte)` (`engines/presupuesto`, E2.2) | ✅ anclada (`GOL-PRE-03`) | consume (precomputado) |
| Forma de la fila `{grupo, valor_total, unidad, n_partidas, guids[], fuente}` | spec `c5-proyeccion-vista` (C5) | ✅ | contrato de la vista |
| Resaltado de GUIDs en 3D | selección del `Viewer` (`apps/visor`) | ✅ | apps/ |
| Chip de estado de dato | `data-state.ts` (D-021) | ✅ | apps/ |
| Lectura del derivado / patrón de fixture servida | `ifc-loader.ts`, BCF (patrón «el visor consume, no genera») | ✅ | apps/ |
| Export firmable de la proyección (dos llaves) | — (gancho forward) | 🔴 forward | release · muro de cobro |

## 3 · D-DV-3 · Contrato de la vista — JSON de proyección PRECOMPUTADO (el corazón de E6.1)

**Sin cálculo en cliente (N-06).** El visor es TS; `proyectar` es Python. El visor **no** ejecuta el engine:
consume un **JSON de proyección precomputado**, emitido por el engine y servido junto al modelo (mismo patrón
que el visor consume el **derivado federado** de C4 y el **árbol BCF** sin re-generarlos).

| Opción | Fuente de datos | A favor | En contra |
|---|---|---|---|
| **A (recomendada)** | **JSON de proyección precomputado** (el engine emite el índice de vistas `{(eje,corte) → filas de proyectar}`; el visor lo lee) | cero cálculo en cliente; determinista; patrón derivado/BCF ya probado; testeable headless con fixture | el JSON hay que emitirlo/servir (un paso de build/derivación) |
| **B** | el visor **llama a un service** de proyección en vivo (HTTP) | siempre fresco | acopla el visor a un runtime Python; superficie de red; contradice «el visor consume, no genera» en v0 |

**Recomendación: A.** El **contrato de la vista** es la forma que **ya** especifica `c5-proyeccion-vista`:

```jsonc
// índice de proyección (precomputado por el engine; el visor lo LEE)
{
  "presupuesto": "<id/hash de la medición>",
  "totales": { "coste": { "valor": 7022.53, "unidad": "EUR" },
               "carbono": { "valor": <…>, "unidad": "kgCO2e" } },
  "vistas": [
    { "eje": "coste", "corte": "espacial", "suma": 7022.53,
      "grupos": [ { "grupo": "…/Planta Baja", "valor_total": 3815.28, "unidad": "EUR",
                    "n_partidas": 3, "guids": ["…"], "fuente": "ifc" }, … ] },
    { "eje": "coste", "corte": "funcional",  "suma": 7022.53, "grupos": [ … ] },
    { "eje": "coste", "corte": "uniclass",   "suma": 7022.53, "grupos": [ … ] }
  ]
}
```

Es **exactamente** `expected.json` de `GOL-PRE-03` (mismo shape: `vistas[].{eje,corte,suma,grupos[]}`), más
`n_partidas`/`guids`/`unidad` que `proyectar` ya devuelve. → **No hace falta contrato nuevo**: el JSON es la
salida ya especificada de `proyectar`, serializada. El emisor del JSON (un script/derivación en `engines/` o
`tools/`) es determinista; **no** vive en el visor.

> **Emisor del JSON (v0):** un pequeño emisor determinista (Python, junto al engine) que llama a `proyectar`
> por cada `(eje, corte)` de v0 y vuelca el índice. Corre en la máquina de JM (donde corre el engine); para el
> **test del visor** se ancla una **fixture** (el índice de la muestra), igual que `fixtures/federado.ifc` es
> el derivado congelado. Cuál es el modelo de la muestra (el federado de la demo vs. la medición de
> `GOL-PRE-03`) se fija en el apply; la aceptación exige que **la fixture reproduzca `GOL-PRE-03`**.

## 4 · D-DV-4 · Golden / aceptación — reproducir `GOL-PRE-03` (tests-first, Vitest)

El dashboard **no** añade golden de engine (`proyectar` ya está anclada por `GOL-PRE-03`). Su Llave 1 es un
**E2E TS** que, cargando la fixture de proyección, **reproduce** lo que `GOL-PRE-03` ancló:

1. **Invariante Σ** — para cada vista, `Σ valor_total(grupos) == suma == total del eje` (±0,01). Es la garantía
   de que la presentación no pierde ni inventa valor.
2. **Semántica de los grupos** — para la vista `coste × espacial`, los grupos/`valor_total`/`fuente` casan con
   `GOL-PRE-03.vistas[i-planta]` (p. ej. `…/Planta Baja` = 3.815,28 `ifc`, `(sin geometría)` = 137,70 `regla`);
   ídem `coste × uniclass` (`ii-uniclass`) y `coste × funcional` (`iii-v-funcional`, con `fuente=criterio` en
   el *fallback*).
3. **Determinismo de la presentación** — dos renders del mismo JSON → mismas filas, mismo orden.
4. **Selección → GUIDs** — seleccionar un grupo expone exactamente sus `guids[]` (doble contra la fixture).
5. **Regla dura «propone»** — la vista nunca marca `isCertified` (reutiliza `data-state.ts`); el export queda
   como acción forward, no como certificación.

El **loop TS corre en la máquina de JM** (Vitest; pnpm/symlinks no van por el mount). Verifica el afectado
localmente antes del PR (patrón de las skins).

## 5 · D-DV-1 · Casa (a ratificar) · D-DV-2 · Alcance v0 · D-DV-5 · Muro de cobro

- **D-DV-1 · Casa: skin/vista del visor (`apps/visor`)** — espejo de las skins existentes. *(recomendada)*
  Alternativa: app aparte (más superficie, rompe el «un shell, varias pieles»). **Recomendación: skin.**
- **D-DV-2 · Qué expone v0:** ejes {**coste, carbono**} × cortes {**espacial, funcional, uniclass**}; **tabla +
  gráfica** de la proyección; **selección → GUIDs** en 3D; pastilla de invariante Σ + chip de fuente.
  **Comparar dos ofertas** (dos presupuestos) y **cortes GuBIM/avanzados** = **post-v0** (forward).
- **D-DV-5 · Muro de cobro:** en v0 **sólo la vista** (gratis); el **export firmable** de la proyección (dos
  llaves) = **gancho forward**. La skin no certifica.

## 6 · Frontera de gobierno (todo `apps/`, «propone»)

- **apps/ (revisión normal, Llave 1 del visor):** UI, `dashboard.ts` (presentación pura), fixtures, demo, test
  E2E. No tocan `packages/contracts` ni `packages/golden`.
- **No es contract-first:** `proyectar` ya es contrato anclado (`c5-proyeccion-vista` + `GOL-PRE-03`). El
  dashboard lo **consume**; su forma de fila es el contrato de la vista (ya especificado).
- **release · dos llaves (muro de cobro):** el **export firmable de la proyección** — **fuera de v0** (forward).

## 7 · Riesgos y mitigación

- **Tentación de calcular en cliente** (re-sumar/re-proyectar en TS). *Mitigación:* D-DV-3, el visor **lee** el
  JSON precomputado; el test de invariante Σ ancla que la presentación no altera el valor; un desajuste se
  corrige en el emisor/engine, no en el cliente.
- **Deriva entre la fixture del visor y `GOL-PRE-03`.** *Mitigación:* la aceptación reproduce los grupos/valores
  de `GOL-PRE-03` (no un oráculo propio); si el engine cambia, la fixture se re-emite del engine, no se edita a
  mano.
- **La UI podría dar sensación de certificar.** *Mitigación:* barra de estado + `data-state` (regla
  `isCertified`): la proyección es dato firmado aguas arriba; el export firmable (dos llaves) llega como
  acción, no como estado de la vista.
- **Carbono sin proyección anclada en v0.** `GOL-PRE-03` ancla proyecciones de **coste**; el carbono está
  anclado por `GOL-CAR-02` (valoración) pero no como proyección. *Mitigación:* la aceptación dura reproduce
  `GOL-PRE-03` (coste, 3 cortes); el eje carbono se muestra desde su JSON de proyección (emitido igual) con
  aceptación por invariante Σ; anclar una proyección de carbono como `GOL-PRE-03` = forward si JM lo pide.
