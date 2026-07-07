# C3 — Decisiones de contrato (ancladas)

> Resueltas con JM el **2026-07-03** (OK explícito), antes de tocar código. Numeración
> **propia del C3** (no se mezcla con las D1–D30 del C4 ni las V1–V5 del visor). Estas cinco
> decisiones resuelven las preguntas **N1–N5** del INICIO del hilo (Fase III·h2). El contrato
> C3 entra por la MISMA puerta contract-first que estrenó el C4 (Fase II·h1, PR #16): esquema +
> pack + golden con checklist FIRMADO como oráculo, ANTES de una sola línea del engine.

## D1 · Primer pack y primer corte de exigencias — CTE/2019 mínimo, 4 estados (N1)

Pack `data/packs/normativa/CTE/2019` (familia `normativa`, identidad por hash — patrón
`packs.ids`). Corte **mínimo y honesto** de **5 exigencias** que ejercita los **cuatro estados**
del veredicto sobre el edificio del C4-FED-06, todas derivables del IFC/Maestro **sin motor de
cálculo**:

| id | DB | apartado | estado en GOL-CTE-01 | por qué |
|---|---|---|---|---|
| `E-SUA-ACCESO` | DB-SUA | SUA 9 §1.1.2 | **cumple** | el Maestro trae `IfcTransportElement`/ELEVATOR (Ascensor-01) |
| `E-SI-RF-DECL` | DB-SI | SI6 Tabla 3.1 | **no-cumple** (adrede) | 0/10 elementos estructurales declaran `FireRating` |
| `E-SI-EVAC` | DB-SI | SI3 | **no-verificable** | ocupación + recorridos de evacuación → motor futuro |
| `E-HE1-DEMANDA` | DB-HE | HE1 | **no-verificable** | demanda energética → motor térmico |
| `E-RSCIEI` | RSCIEI (concurrente) | RD 2267/2004 | **no-aplica** | uso declarado Residencial Vivienda (no industrial) |

El `no-cumple` es un **fallo adrede documentado** (patrón C4-FED-01): la golden nace con materia
para que el checklist tenga cumple Y no-cumple. `GOL-URB-01` (urbanística) se **difiere** a un
hilo posterior — el PLAN 2.1 la siembra pero no obliga a la vez.

**Principio de escala (PLAN §2.2):** el código es un **PACK anclado, no un `if`**. Cambiar de
año/mercado/localidad = cambiar de pack, no de engine. El .ids no aplica aquí: el CTE se expresa
como lista de exigencias del pack (`exigencias.json`), con su md5 y su golden de contenido.

## D2 · Entrada del contrato — el MAESTRO federado, uso y localización DECLARADOS (N2)

`modelo` = el **Maestro federado** que produce C4 (manifiesto D1 + `base_dir`, con el **derivado
como vista**), no un IFC suelto: la fase es "cumplimiento **sobre federado**", C3 consume lo que
C4 produce (regla de dependencias PLAN §1). La golden **reutiliza el C4-FED-06 byte a byte**
(patrón D14/D21): mismas `ARQ.ifc` + `EST.ifc` (md5 `653a359…` / `b84cb79…`) y el derivado
anclado (`dcb1e14460f3556107ce35d6dade16c3`) como vista — **cero entradas de diseño nuevas**.
`uso` y `localizacion` son claves **DECLARADAS** de la entrada (ADR, heredado de C4: nunca se
adivinan del IFC; `declarado_por` deja constancia).

## D3 · Forma del veredicto y del checklist — 2 esquemas forward-open; checklist = oráculo (N3)

Dos esquemas propios (`schema_version 0.1.0`), *forward-open* (se AÑADEN claves, nunca se cambia
la semántica — regla sagrada heredada de C1/C4):

- `entrada-cumplimiento.schema.json` — `(modelo=maestro-federado + uso + localizacion + pack_normativo)`.
- `veredicto-cumplimiento.schema.json` — veredicto **POR EXIGENCIA**
  `{id, exigencia, documento_basico, referencia (pack+apartado), resultado, motivo_no_verificable?, evidencia?, por_modelo?}`
  + `resumen` agregado (conteo por resultado) + `veredicto` global.

El **checklist esperado** de la golden (`expected.json → veredicto_cumplimiento`) es el
**ORÁCULO**. **"Firmado"** = vive en la golden y queda cubierto por el **tag GPG del cierre**
(Llave 2), como los expected de C4 — **no** una firma por fichero. `$defs` compartidos donde
proceda.

## D4 · Lo no-verificable se DECLARA — taxonomía CERRADA de 4 estados (N4)

`resultado ∈ {cumple, no-cumple, no-aplica, no-verificable}` — **enum cerrado** en el esquema.
`no-verificable` es la esencia multi-código **honesta** del C3: muchas exigencias reales exigen
motores (C9/C10) o datos que el IFC no trae. Es **forward-open**: un engine futuro convierte un
`no-verificable` en `cumple`/`no-cumple` **sin romper el esquema**. El esquema **exige**
`motivo_no_verificable` cuando `resultado = no-verificable` (condicional `if/then`: qué
motor/dato lo cerraría). `no-aplica` cuando la exigencia no rige para el `uso` declarado.

**Veredicto agregado (regla anclada):** hay ≥1 `no-cumple` → **`no-conforme`**; si no hay
`no-cumple` pero hay ≥1 `no-verificable` → **`conforme-con-reservas`**; si todas son
`cumple`/`no-aplica` → **`conforme`**. En GOL-CTE-01 domina el `no-cumple` → `no-conforme`.

## D5 · Alcance del hilo — contract-first ESTRICTO; el engine en 3.3 (N5)

Este hilo entrega **esquemas + pack CTE + golden `GOL-CTE-01` anclada** (checklist calculado A
MANO y verificado **×2** contra el Maestro del 06 con ifcopenshell) + **runner** (`CASE_RUNNERS`
gana `"C3": run_case_c3` en **modo ANCLADO**). El **engine** (`engines/cumplimiento`, su casa por
PLAN §1/§2) llega en **3.3**, y **antepondrá** el recompute contra el MISMO expected (misma
costura que cerró C1 en Fase I y C4 en Fase II·h2).

**Modo anclado (oráculo sin engine, D4 del C4 como precedente):** verifica lo verificable —
conformidad de los dos esquemas; identidad por hash (entradas del 06 reutilizadas + derivado
`dcb1e144…` + pack CTE); y coherencia interna (exigencias del veredicto ⊆ pack; taxonomía cerrada
de resultados; `motivo` presente en cada `no-verificable`; `resumen` == recuento real; veredicto
agregado según la regla D4; `uso`/`localizacion` coherentes entrada↔veredicto; modelos de
`por_modelo` ⊆ modelos de la entrada). **Más checks que hoy, nunca menos** (D10 del C4). SIN
release: la Llave 2 del C3 espera al engine (como la del C4 esperó a la tarea 1.2).

---

# C3·h3 — El engine vivo (`engines/cumplimiento`)

> Decisiones **D6–D10**, resueltas con JM el **2026-07-03** (OK explícito) antes de tocar código.
> Resuelven las preguntas **E1–E5** del INICIO de Fase III·h3. El engine hace vivo el C3: DA el
> veredicto, y el runner **antepone** su recompute contra el MISMO `expected` (misma costura que
> cerró C1 en Fase I y C4 en Fase II·h2). No reabren D1–D5.

## D6 · Casa del engine — `engines/cumplimiento`, empaquetado como el service (E1)

El engine vive en `engines/cumplimiento/` (taxonomía PLAN §1/§2: los motores deterministas de
dominio van en `engines/`), pero con la **estructura de paquete de `services/federacion`**:
`pyproject.toml` + `src/aqyra_cumplimiento/` + `tests/` + CLI, y **miembro del workspace uv**
(`[tool.uv.workspace]`). Motivo: a diferencia de `engines/ifc` (import-de-path puro, sin versión
de paquete, anclado por md5), el C3 debe **versionarse** (SemVer 0.1.0) y **releasearse**
(tag `cumplimiento-v*`, Llave 2) y necesita `ifcopenshell` resuelto por `uv sync`. El runner lo
**importa por path** (patrón `_recompute_c4`), pero el paquete existe para sync/pytest/release.

## D7 · Consumo del Maestro — el engine ABRE el derivado; el runner lo REGENERA (E2)

Desacople de capas honesto (PLAN §1: C3 consume lo que C4 produce, no lo re-ejecuta):

- El **engine** `verificar(maestro, uso, localizacion, pack)` depende **solo de `ifcopenshell`** y
  **abre el IFC derivado** (la vista del Maestro, D26/D30 de C4) que le señala el manifiesto +
  `base_dir`. **No importa ni re-ejecuta `services/federacion`.**
- La **costura del runner** regenera el Maestro (`federar_fichero(reglas.json)` + `derivar()`,
  reutilizando el camino de `_recompute_c4`) y le entrega al engine el manifiesto + el derivado.

En producción C7 federa una vez y llama a C3; en la golden el runner lo regenera para probar
reproducibilidad. El engine queda desacoplado del service (no hay dependencia de paquete C3→C4).

## D8 · Cómo evalúa — registro de evaluadores por MÉTODO declarado en el PACK (E3)

Para que "el código sea un **PACK anclado, no un `if`**" (D1, PLAN §2.2), el engine tiene una
**librería finita de primitivas deterministas** y el **pack declara** qué primitiva usa cada
exigencia. Se **enriquece `exigencias.json`** (forward-open: se AÑADEN claves `evaluador` +
`parametros`, sin tocar las existentes) con las **4 primitivas** que GOL-CTE-01 ejercita:

| evaluador | qué mira | resultado |
|---|---|---|
| `presencia-tipo-ifc` | ≥1 `IfcTransportElement` con `PredefinedType=ELEVATOR` (parametrizable) | cumple / no-cumple |
| `presencia-propiedad-pset` | propiedad (`FireRating`) en el Pset de cada elemento de las clases estructurales | cumple / no-cumple + `por_modelo` |
| `aplica-solo-uso` | el `uso` declarado ∈ usos objetivo (industrial) | no-aplica si no rige |
| `requiere-motor` | nada (declara la frontera) | no-verificable + `motivo` (del pack) |

El engine mapea `evaluador`→función; añadir una exigencia de método conocido = **solo pack**; un
método nuevo = **evaluador nuevo** (honesto, raro). **Consecuencia de anclaje:** al cambiar
`exigencias.json` se re-anclan en el MISMO PR `md5_exigencias` (`pack.json`) y el `content_sha256`
del golden de pack (`data/packs/normativa/CTE/2019/golden/expected.json`). El **`expected.json` del
C3 (el oráculo: veredicto por exigencia) NO se toca** — el veredicto es byte a byte idéntico; solo
gana estructura la declaración del pack, no cambia ningún resultado.

## D9 · Costura del runner — recompute antepuesto contra el MISMO `expected` (E4)

`run_case_c3` **antepone** el recompute: regenera el Maestro (federar+derivar con el service) →
`engine.verificar()` → compara el veredicto recomputado contra `expected.json`, **normalizando el
texto libre** (`evidencia`, `motivo_no_verificable`, la descripción humana `exigencia`) igual que
`_CAMPOS_LIBRES` en C4. Se comparan literal: `id`, `documento_basico`, `referencia`, `resultado`,
`por_modelo` (resultado + conteos), `resumen` y `veredicto`. Los **18 checks anclados del 3.2 se
conservan íntegros** (D10 del C4: **más checks, nunca menos**). Un fallo se investiga en el
engine, **jamás** en el `expected`.

## D10 · Versionado y release — `cumplimiento-v0.1.0`, primer release del C3 (E5)

`engines/cumplimiento` **0.1.0**. Primer tag FIRMADO del C3: **`cumplimiento-v0.1.0`** (Llave 2,
patrón `federacion-v0.2.0`/D15 del C4). `release.yml` amplía su disparo en UNA línea
(`tags: [..., "cumplimiento-v*"]`); `versions.lock [contracts.C3]` gana `engine_version = "0.1.0"`
+ estado; `ci.yml` Paso 1 añade `engines/cumplimiento` al pytest; nuevo miembro en
`[tool.uv.workspace]`. La firma la hace JM en local (el CI nunca certifica).

---
*Regla de oro heredada: un fallo NO se arregla aflojando la golden. Contract-first de verdad —
si al redactar el checklist a mano el esquema cojea, se corrige el esquema AHORA. El CI nunca
certifica (Llave 2 = JM).*

---

## Bloque 6D · write-back del veredicto al modelo (D-6D-1..3)

> Ratificadas con JM el **2026-07-07** (OK explícito), antes del código. Vertical
> `visor-cumplimiento-6d` (épica Jira AQYRAALL-1). Análogas a las D11–D15 de C5 (write-back 5D):
> el resultado se ESCRIBE en el derivado para que el visor lo LEA y pinte. No crean esquema de
> contrato nuevo (Pset OpenBIM, como el 5D usó `IfcCostSchedule` canónico).

### D-6D-1 · Pset de cumplimiento — `Pset_Aqyra_Cumplimiento`

`engines/cumplimiento.escribir_cumplimiento(veredicto, maestro, salida)` escribe en cada elemento
del derivado un `IfcPropertySet` **`Pset_Aqyra_Cumplimiento`** (vía `IfcRelDefinesByProperties`)
con propiedades `IfcPropertySingleValue`: `Resultado` (IfcLabel ∈ {cumple, no-cumple, no-aplica,
no-verificable}), `Exigencia` (id dominante), `DocumentoBasico`, `Apartado`, `Pack`,
`MotivoNoVerificable` (IfcText, solo si Resultado=no-verificable, D4). Determinista (cabecera SPF
fija + GUIDs `uuid5`, patrón `escribir_coste`): escribir 2× → bytes idénticos.

### D-6D-2 · Granularidad — por elemento, peor caso agregado

El veredicto es por exigencia con `por_modelo` (sub-modelo federado). El write-back atribuye el
`resultado` de cada sub-modelo a **todos sus elementos** (vía `modelo.guid_a_modelo` del
manifiesto C4). Si varias exigencias tocan un elemento, `Resultado` = **peor caso**:
`no-cumple` ≻ `no-verificable` ≻ `cumple`; `no-aplica` es **neutro** (solo queda `no-aplica` si
todas lo son). Invariante: todo elemento del derivado recibe exactamente un `Resultado`.

### D-6D-3 · Alcance v0 — las 5 exigencias del pack `CTE/2019` de `GOL-CTE-01`

El primer corte escribe solo las 5 exigencias ya ancladas en `GOL-CTE-01` (los 4 estados). El
golden 6D ancla por **determinismo** (2×=bytes) + **semántica** (el Pset casa con el veredicto de
`GOL-CTE-01` proyectado a elementos por la regla del peor caso), sin md5 hardcodeado si es frágil
por EOL (patrón D14 opción b de C5). Un fallo se corrige en el código, jamás aflojando la golden.
