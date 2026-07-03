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
*Regla de oro heredada: un fallo NO se arregla aflojando la golden. Contract-first de verdad —
si al redactar el checklist a mano el esquema cojea, se corrige el esquema AHORA. El CI nunca
certifica (Llave 2 = JM).*
