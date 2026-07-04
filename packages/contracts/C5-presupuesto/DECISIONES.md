# C5 — Decisiones de contrato (ancladas)

> Resueltas con JM el **2026-07-03** (OK explícito), antes de tocar código. Numeración **propia del
> C5** (no se mezcla con las D1–D30 del C4, D1–D10 del C3 ni V1–V6 del visor). El contrato C5 entra
> por la MISMA puerta contract-first que estrenó el C4 (Fase II·h1) y siguió el C3 (Fase III·h2):
> esquemas + packs + golden con oráculo FIRMADO, ANTES de una sola línea del engine.

## D1 · Artefacto autoritativo — el JSON de presupuesto; el documento lo compone C7

Lo AUTORITATIVO es el **estado de mediciones + cuadros + resumen estructurado** (`salida-presupuesto`
JSON), espejo de C4·D1 (el Maestro es el manifiesto) y C3 (el veredicto, no la memoria). C5 **no
redacta** el Documento de Presupuesto (PDF/Word con formato del despacho) — lo compone **C7** después,
consumiendo este JSON. El golden ancla el JSON.

## D2 · Corte mínimo del criterio — lo difícil de medir, sobre la geometría real

Criterio `AQ/v1`: reglas que ejercitan lo difícil (C5 ADR: el criterio es el 80% del valor), sobre la
geometría real del Maestro (C4-FED-06): **muro** (m² con **descuento de huecos > 1,00 m²**; el muro
M-Fachada tiene un hueco de 2,1 m²) · **losa** (m³) · **pilar** (m³) · **zapata** (m³) · **puerta**
(ud) · y **un objeto → varias partidas** (cada muro → fábrica + enfoscado 2 caras + pintura 2 caras).
El mapeo clase→partida vive en el criterio; el precio, en el banco; el código de partida es la junta.

## D3 · Oráculo y tolerancia — medición manual congelada; cantidades ±0,5%, mapeo e importes exactos

`expected` anclado con la **medición manual** (calculada a mano desde los `Qto` y verificada ×2 con
ifcopenshell). Comparación mixta (`tolerancias.json`): **cantidades** con tolerancia relativa **±0,5%**
(para el recompute del engine); **mapeo clasificación→partida EXACTO**; **importes** derivados del
banco anclado **exactos** (redondeo a 2 decimales, ±0,01). El valor del golden es **consistencia y
no-regresión**, no verdad física (FUNDACION_C6 §5): el PEM es una convención (criterio + banco).

## D4 · Banco de precios v0 — propio mínimo `AQ-DEMO`, anclado por hash

Banco **propio** de demostración `banco/AQ-DEMO/v1` (NO BEDEC/PREOC, licenciados): 7 partidas
descompuestas (MO/materiales/maquinaria + costes indirectos 3%) + mapeo clasificación→partida. Anclado
por hash en `versions.lock [packs.banco]` (patrón `packs.ids`/`packs.normativa`); su golden de pack
(`content_sha256`) impide el drift silencioso. El banco real (licenciado o del despacho) entra como
pack cuando el engine lo consuma. El **criterio** es una **familia de pack NUEVA** (`criterio/AQ/v1`),
añadida al enum de `pack.schema.json` (aditivo, forward-open) junto a `codigos/normativa/banco/ids`.

## D5 · Partidas sin geometría — el esquema las contempla; el golden ancla 1 ejemplo

El esquema contempla `origen ∈ {modelo, regla, manual}` (enum **cerrado**). El golden v0 ancla **1**
partida sin geometría para fijar la forma: **Seguridad y Salud por ratio** (`SYS010`, `origen=regla`,
2% del PEM medible, `trazabilidad: []`). El grueso (ayudas, PA, gestión de residuos) llega con el
engine. Las partidas `origen=regla` **no** exigen respaldo en el banco (su precio es una regla, no un
precio unitario descompuesto).

## D_modelo · La medición LEE Qto — fixture propia con Qto; el QA/IDS de C4 garantiza su presencia

La medición de producción **lee `Qto`** (no adivina geometría). El derivado anclado del C4-FED-06 **no
trae `Qto`** y **no se puede tocar** (rompería su md5 y el de C3/visor). Solución: **fixture propia de
C5** = copias de `ARQ.ifc`/`EST.ifc` con `Qto_*` **inyectados** (calculados de la geometría real,
verificados ×2), con **md5 propios** (`0b998513…` / `0d7e7f20…`); los originales anclados quedan
**intactos**. La **garantía** de que un modelo apto para presupuesto declara `Qto` en los elementos
medibles es del **QA/IDS de C4** aguas arriba (precondición de conformidad, forward-open: cuando el IDS
del proyecto lo exija, C4 lo bloquea antes de llegar a C5).

## D_scope · Alcance del hilo — contract-first ESTRICTO; el engine en un hilo posterior

Este hilo entrega **2 esquemas forward-open + packs criterio/AQ/v1 y banco/AQ-DEMO/v1 + golden
`GOL-PRE-01` anclada** (presupuesto calculado a mano y verificado ×2) + **runner** (`CASE_RUNNERS` gana
`"C5": run_case_c5` en **modo ANCLADO**). El **engine** (`engines/presupuesto`, su casa por PLAN §1/§2)
llega en un hilo posterior y **antepondrá** el recompute (parser de `Qto` + motor de presupuesto)
contra el MISMO expected (misma costura que cerró C1 en Fase I, C4 en Fase II·h2 y C3 en Fase III·h3).

**Modo anclado (oráculo sin engine):** verifica lo verificable — conformidad de los 2 esquemas;
identidad por hash de las fixtures con `Qto`; y coherencia interna (importe = cantidad × precio;
precio == cuadro nº1 == cuadro nº2 (Σ componentes + indirectos); PEM = Σ importes = Σ capítulos;
GG/BI/IVA/base/PEC según `parametros`; partidas `origen=modelo` ⊆ banco con precio == banco; criterio y
banco anclados en `versions.lock`; `trazabilidad` ⊆ GUIDs del modelo; taxonomía de `origen` cerrada;
S&S = 2% del PEM medible). **Más checks que hoy, nunca menos** (D10 del C4). **SIN release:** la Llave
2 del C5 espera al engine (como la del C4 esperó a la tarea 1.2 y la del C3 a la 3.3).

---

# C5 — Decisiones del ENGINE (Fase IV·h2 — `engines/presupuesto`)

> Resueltas con JM el **2026-07-04** (OK explícito), antes de tocar código del engine. Numeración
> **propia del C5**, continúa D1–D5 + D_modelo + D_scope. El engine hace VIVO el contrato del 4.1: se
> dobla al `expected` de `GOL-PRE-01`, jamás al revés (misma puerta que cerró C1 en Fase I, C4 en
> Fase II·h2 y C3 en Fase III·h3). ZONA ANCLADA intocable: el contrato/esquemas/`expected`, los packs
> `criterio/AQ/v1` y `banco/AQ-DEMO/v1` (identidad por hash), las fixtures con `Qto`.

## D6 · Casa y empaquetado — paquete uv en `engines/`, releaseable (espejo de `engines/cumplimiento`)

`engines/presupuesto/` con la estructura de paquete de `engines/cumplimiento` (D6 del C3): `pyproject.toml`
(hatchling, `aqyra-presupuesto` 0.1.0, dep `ifcopenshell`, script CLI) + `src/aqyra_presupuesto/` + `tests/`
+ miembro de `[tool.uv.workspace]`. El runner lo importa **por path** (patrón `engines/ifc` y
`_recompute_c3`/`_recompute_c4`); `DEFAULT_ENGINE_C5 = engines/presupuesto/src` ya está cableado en
`run_golden.py`. SemVer; releaseable (Llave 2, D10).

## D7 · Qué consume el engine — el parser abre el IFC(+`Qto`); la magnitud NETA contabiliza los huecos

El engine hace VIVO el módulo 1 (parser de medición): `medir(ifcs) → modelo` **abre las fixtures IFC
con `Qto`** (`ARQ.ifc`/`EST.ifc`, que llevan `IfcClassificationReference` + `IfcElementQuantity` +
estructura espacial, verificado) y produce el **modelo neutro de medición**; `presupuestar(modelo,
criterio, banco, parametros) → presupuesto` (módulos 2–6). En el golden el runner llama a `medir()`
sobre las fixtures congeladas (la joya: *la medición nace del modelo*) y luego `presupuestar()`. En
producción, el Maestro federado de C4.

**Huecos (matiz de JM, 2026-07-04).** Procedimiento: el engine lee la **magnitud que declara el
criterio**; cuando `descuento_huecos:true` esa magnitud es la **neta** (`NetSideArea`), que por
definición IFC ya es *bruto − huecos* → **los huecos quedan contabilizados por el propio `Qto`**, no por
una re-derivación geométrica (respeta D_modelo: no adivina geometría). Y para que el hueco se tenga en
cuenta **explícita y auditablemente**, la primitiva `leer-cantidad`: (1) usa el valor NETO como cantidad;
(2) **detecta los huecos** del elemento (`IfcRelVoidsElement`) y con el `umbral_hueco_m2` registra el
descuento aplicado en la justificación (p. ej. *"descuento de huecos = 2,10 m² (bruto 18,00 − neto 15,90),
hueco > umbral 1,00 m²"*); (3) **guarda de consistencia**: si el `Qto` trae bruto y neto, verifica que el
descuento observado (`Gross − Net`) corresponde a hueco(s) > umbral; si no cuadra, lo marca como fallo de
dato (no lo silencia). Reproduce el golden: M-Fachada 15,90 (18,00 − 2,10>1,00) + M-Interior 18,00 (sin
hueco) = 33,90 m² → FAB010.

## D8 · Cómo aplica el criterio — registro finito de primitivas; selección ESTRUCTURAL (criterio anclado)

Espíritu del registro de evaluadores del C3 (D8): librería FINITA de primitivas — `leer-cantidad` (por
`magnitud` + `factor_caras` + descuento/umbral) y `partida-por-ratio` (`origen=regla`, `base=PEM_medible`
× `ratio`) — y el pack es la tabla de verdad ("el código es un PACK anclado, no un `if`"). **Diferencia
respecto al C3 (anclaje):** el pack `criterio/AQ/v1` está **anclado por hash** y **no** lleva campo
`primitiva`/`evaluador` explícito; añadirlo obligaría a re-anclarlo (fuera de alcance). Por tanto la
**selección de primitiva es ESTRUCTURAL** sobre el criterio tal cual está anclado: `reglas_por_clase` →
`leer-cantidad`; `reglas_sin_geometria` → `partida-por-ratio` (y los campos presentes lo confirman:
`magnitud` vs `ratio/base`). El registro finito existe (método nuevo = primitiva nueva, raro); la
"declaración" del pack es su forma, no un string literal. `un objeto → varias partidas` (muro → fábrica +
enfoscado 2 caras + pintura 2 caras) sale del criterio; el precio, del banco; el `codigo` es la junta.

## D9 · Costura del runner — recompute ANTEPUESTO; los 17 checks del 4.1 íntegros

`run_case_c5` antepone el **check 0 (RECOMPUTE)**: `_recompute_c5` → `medir(fixtures)` → `presupuestar(...)`
comparado contra el MISMO `expected["presupuesto"]`, **normalizando el texto libre** (`descripcion`,
`criterio_aplicado`, `precio_en_letra`, `nota`, claves `_*`) y comparando **literal** lo semántico
(`codigo`/`capitulo`/`unidad`/`cantidad`/`precio_unitario`/`importe`/`origen`/`trazabilidad` + cuadros
nº1/nº2 (estructura y números) + `resumen` PEM…PEC). **Conserva ÍNTEGROS los 17 checks anclados del 4.1**
(D10 del C4: más checks, nunca menos). Un fallo se investiga en el ENGINE (parser/motor), **jamás** en el
`expected`.

## D10 · Versionado y release — 0.1.0; tag FIRMADO `presupuesto-v0.1.0` (Llave 2)

`engines/presupuesto` 0.1.0. `versions.lock [contracts.C5]` gana `engine_version = "0.1.0"` + estado;
`ci.yml` Paso 1 añade `engines/presupuesto` al `pytest`; nuevo miembro en `[tool.uv.workspace]` (edición
quirúrgica). `release.yml` ya dispara `presupuesto-v*`. RELEASE: **primer tag firmado del C5**
`presupuesto-v0.1.0` (Llave 2, firma de JM en local; el CI nunca certifica) — patrón `cumplimiento-v0.1.0`
(D10 del C3).

---
*Regla de oro heredada: un fallo NO se arregla aflojando la golden. Contract-first de verdad — si al
calcular el presupuesto a mano el esquema cojea, se corrige el esquema AHORA. El CI nunca certifica
(Llave 2 = JM).*
