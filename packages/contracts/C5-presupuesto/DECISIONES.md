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

# C5 — Decisiones del WRITE-BACK 5D (Fase IV·h3 — el coste vuelve al modelo)

> Resueltas con JM el **2026-07-04** (OK explícito), antes de tocar código. Continúan la numeración
> del C5 (D11–D15). Materializan el **módulo 6** de `C5_presupuesto.md` («partida e importe al IFC →
> el modelo se vuelve 5D»). ZONA ANCLADA intocable: el contrato/esquemas/`expected` del presupuesto,
> los packs, las fixtures con `Qto` (`0b998513…`/`0d7e7f20…`), el derivado C4-FED-06 (`dcb1e144…`),
> la golden `GOL-PRE-01` (no se re-ancla: el 5D es un caso NUEVO).

## D11 · Casa — módulo `escritura.py` en `engines/presupuesto` (bump 0.2.0)

Nuevo módulo `escritura.py`: `escribir_coste(presupuesto, derivado, salida, fecha=None) → {fichero, md5}`.
Consume el **presupuesto ya calculado** (`presupuestar(...)`) — no re-mide — y el **IFC derivado**
(objetivo). Bump `engines/presupuesto` 0.1.0 → **0.2.0** (aditivo: `medir`/`presupuestar` intactos).

## D12 · Qué se escribe — CANÓNICO OpenBIM (`IfcCostSchedule` + `IfcCostItem`), voto de JM

No un `Pset` (la alternativa ligera): el 5D se representa con el **modelo de coste nativo de IFC**:
`IfcCostSchedule` (PredefinedType=BUDGET) ← `IfcRelNests` ← un `IfcCostItem` **por capítulo** ←
`IfcRelNests` ← un `IfcCostItem` **por partida** (`Identification`=código, `Name`=descripción,
`CostValues`=[`IfcCostValue` con `AppliedValue`=`IfcMonetaryMeasure`(importe)], `CostQuantities`=[la
cantidad medida como `IfcQuantityArea/Volume/Count`]); cada `IfcCostItem` de partida se **asigna a los
elementos** que lo producen por `IfcRelAssignsToControl` (RelatedObjects = elementos del derivado con
GUID en la `trazabilidad`). Moneda con `IfcMonetaryUnit` (EUR) en el `UnitAssignment`. Un `IfcCostItem`
**resumen** lleva PEM/GG/BI/base/IVA/PEC como `IfcCostValue` categorizados. **Auditable hasta el
elemento**, la promesa del C5. GUIDs de todo lo nuevo, deterministas (`uuid5`, patrón `derivar`).

## D13 · Sobre qué modelo se escribe — el DERIVADO FEDERADO (voto de JM)

El coste se escribe sobre el **derivado federado** (el Maestro que abre el visor), no sobre las fixtures
por disciplina. Coherente con D7 (el engine **abre** el derivado, **no** federa): el **runner** federa+
deriva las fixtures C5 (con un `reglas.json` propio de la golden) y `escribir_coste` escribe el cost
schedule sobre ese derivado → un `.ifc` **5D** nuevo. Atribución por **GUID** (la `trazabilidad` del
presupuesto ⊆ GUIDs del derivado). Habilita la opción C (el visor pinta el coste) sin más trabajo de
modelo. Cabecera SPF determinista (firma fija sin versión + `time_stamp` constante, patrón `derivar`).

## D14 · Anclaje — SEMÁNTICO + DETERMINISMO, sin md5 hardcodeado (voto de JM: opción b)

El sandbox no puede correr ifcopenshell (disco 100%) → no se pre-calcula un md5. El runner ancla el 5D
así: (1) **DETERMINISMO** — escribe el 5D **dos veces** y exige **bytes idénticos**; (2) **SEMÁNTICO** —
**parsea** el 5D y comprueba que el cost schedule **casa con el presupuesto**: hay `IfcCostSchedule`; un
`IfcCostItem` por partida con `IfcCostValue`=importe y `CostQuantities`=cantidad; las asignaciones
(`IfcRelAssignsToControl`) apuntan a GUIDs ⊆ `trazabilidad`; Σ de importes de partida = PEM; el item
resumen lleva PEM…PEC coherentes; `IfcMonetaryUnit`=EUR. Todo **verificable en CI** sin bootstrap manual.
Caso NUEVO `GOL-PRE-02` (reusa fixtures+criterio+banco+params de `GOL-PRE-01`, que queda **intacto**).
Un fallo se investiga en el ENGINE, jamás aflojando el check.

## D15 · Versionado y release — 0.2.0; tag FIRMADO `presupuesto-v0.2.0` (Llave 2)

`engines/presupuesto` 0.2.0; `versions.lock [contracts.C5]` sube `engine_version` a `0.2.0` + estado.
`ci.yml` ya cubre `engines/presupuesto` (pytest) — el 5D entra por su golden. RELEASE: tag firmado
`presupuesto-v0.2.0` (Llave 2, firma de JM; el CI nunca certifica).

---

# C5 — Decisiones del MOTOR DE VALORACIÓN MULTI-EJE (Ola 1·E1.1 — `valores{}` en la salida)

> Resueltas con JM el **2026-07-08** (OK explícito vía ratificación), antes de tocar código. Numeración
> **propia del C5**, continúa D1–D15. Materializan **E1.1** del handoff negocio→desarrollo
> (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md`) y son coherentes con **D-025** del
> registro del ecosistema (carbono = extensión forward-open de C5, no contrato nuevo). Change SDD:
> `openspec/changes/c5-salida-valores-multieje/`. ZONA ANCLADA intocable: el eje coste
> (`precio_unitario`/`importe`), los packs, las fixtures con `Qto`, la golden `GOL-PRE-01`
> (byte-idéntica; `valores` es opcional y no aparece en su `expected`).

## D16 · El eje coste NO se duplica — `valores{}` es el canal de los ejes NO-coste

El eje **coste** canónico permanece **exclusivamente** en `precio_unitario` / `importe` (fuente de
verdad). La nueva propiedad **opcional** `valores{}` de `partida_medida` (mapa `id-de-eje → valor_eje`)
**no** obliga a contener `coste`; se reserva para los ejes que llegan después (carbono, agua,
energía embebida…). Un productor **puede** reflejar `valores.coste` como espejo informativo, pero el
golden **no** lo exige y el engine (E1.2) **no** lo emite por defecto → `GOL-PRE-01` sigue **verde y
byte-idéntica** (PEM 7 022,53 → PEC 10 111,74), su `expected` sin editar. Se **rechaza** la alternativa
de mover el coste dentro de `valores` (rompería la golden y la compatibilidad de C7).

## D17 · `id de eje` = string libre con convención, NO enum cerrado

La clave de `valores{}` es un `string` **libre** (convención: `coste`, `carbono`, `agua`,
`energia_embebida`, …). **No** se cierra en enum: añadir un eje nuevo **no** debe re-anclar el contrato
ni su golden — a diferencia de `origen` (enum cerrado, D5, taxonomía semántica fija). La disciplina de
nombres reservados se documenta en `contrato.md`; la gobierna el pack/criterio, no el esquema.

## D18 · `etapas` (EN 15978) = objeto opcional `clave→número`, invariante Σ etapas = total

El desglose por ciclo de vida es un objeto **opcional** dentro de cada `valor_eje`, con claves
convencionales `A1A3`, `A4A5`, `B`, `C`, `D` (EN 15978). Cuando se declaran etapas, la suma de las
presentes **debe** igualar el `total` del eje (invariante que el engine y el golden de carbono
comprobarán en la Ola 2; en E1.1 solo se fija la **forma**). Se admite desglose **parcial** (p. ej.
solo `A1A3`+`A4A5`) sin exigir el ciclo completo.

---

# C5 — Decisión del ENGINE GENERALIZADO A UN EJE (Ola 1·E1.2 — `parametros.eje`)

> Ratificada con JM el **2026-07-08** (OK explícito vía la pregunta de arranque), antes de tocar código.
> Numeración **propia del C5**, continúa D1–D18. Materializa **E1.2** del handoff negocio→desarrollo
> (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E1) y hace VIVO el `valores{}` que
> abrió E1.1 (D16–D18). Change SDD: `openspec/changes/c5-engine-eje-generalizado/`. ZONA ANCLADA
> intocable: el esquema, los packs, las fixtures con `Qto`, la golden `GOL-PRE-01` (byte-idéntica; el
> eje coste sigue en `precio_unitario`/`importe` y **no** emite `valores`).

## D19 · Un run con eje NO-coste: espejo + `valores[eje]` etiquetado

`presupuestar(modelo, criterio, banco, parametros)` gana `parametros.eje` (default `"coste"`). El
**mapeo clase→partida del criterio NO cambia entre ejes** (se mide una vez, se valora en el eje
pedido). Dos ramas:

- **`eje == "coste"` (default):** rama del C5 previo **byte a byte** — el coste vive
  **exclusivamente** en `precio_unitario` / `importe` (D16) y **no** se emite `valores` →
  `GOL-PRE-01` intacta (PEM 7 022,53 → PEC 10 111,74), su `expected` sin editar.
- **`eje != "coste"`:** cada partida gana `valores[eje]` — el valor del eje **etiquetado** con su
  `unidad` (la declara el banco: `unidad_eje`, *fallback* `moneda`), su `banco` de origen
  (`banco.ref`/`banco`; ausente en `origen=regla`) y su `origen`. Los campos requeridos por esquema
  `precio_unitario` / `importe` **reflejan la magnitud del eje** (espejo), de modo que la verdad
  etiquetada del eje es `valores[eje]` (con unidad y banco) y el `resumen` totaliza el eje. D16 se
  mantiene: en el run de coste esos campos son coste; en un run no-coste no hay coste, y el hueco lo
  ocupa —espejado— la única magnitud que el run computa.

**Alternativa rechazada (por JM):** dejar `precio_unitario=0`/`importe=0` en el run no-coste (D16
literal, coste a cero). Se descarta por dar un `resumen` en cero y romper la simetría con el
presupuesto de coste; el espejo es más útil (resumen del eje) y de un solo camino de código (mínimo
riesgo de regresión para `GOL-PRE-01`).

**Sin release:** la salida multi-eje se libera cuando el eje carbono aporte valor (Ola 2), o según
decida JM. `engines/presupuesto` sube a **0.3.0** (aditivo: `medir`/`presupuestar`/`escribir_coste`
intactos para el coste).

---

# C5 — Decisiones de los CORTES (Ola 1·E2.1 — los cortes nacen del IFC)

> Ratificadas con JM el **2026-07-08** (OK explícito vía la pregunta de arranque), antes de tocar
> código. Numeración **propia del C5**, continúan D1–D19. Materializan **E2.1** del handoff
> negocio→desarrollo (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E2) y hacen
> ejecutable la decisión de negocio **N-06 / D-028** (cortes = agrupaciones nativas del IFC; frontera
> 50/50; criterio como *fallback*). Change SDD: `openspec/changes/c5-cortes-agrupaciones-nativas/`.
> ZONA ANCLADA intocable: el eje coste (`precio_unitario`/`importe`), el pack `criterio/AQ/v1` y su
> hash, el pack `banco/AQ-DEMO/v1`, las fixtures con `Qto` de `GOL-PRE-01` (`0b998513…`/`0d7e7f20…`),
> la golden `GOL-PRE-01` (byte-idéntica; su medición no mira `cortes`).

## D20 · Forma de `cortes{}` — **lista de pertenencias**, no string

Cada `objeto_medicion` gana la propiedad **opcional** `cortes` (aditiva, forward-open). Cada eje
(`espacial`, `funcional`, `uniclass`, `gubim`) es una **lista de pertenencias**
`[{grupo, fraccion, fuente}]`, **no** un string único. Justificación: solo la lista con `fraccion`
puede representar (i) el **reparto 50/50** ratificado (N-06) de un elemento de frontera compartido, y
(ii) la **pertenencia múltiple** (un objeto en varios `IfcSystem`/`IfcZone`). La suma de `fraccion`
de un objeto atribuido a un eje es **1.0** (invariante que E2.2 usa para `Σ proyección == Σ
estado_mediciones`). Un eje sin agrupación conocida se **omite** (nunca error). **Rechazada** (por
JM) la alternativa «string simple + mapa de fracciones aparte» por asimétrica.

## D21 · Reparto de frontera — **50/50 fijo, materializado en el parser**

No reabre N-06 (que ya firmó el 50/50, opción b); ancla su **materialización** a nivel C5: el reparto
se resuelve **al construir el modelo neutro** (en el parser), **no** en `proyectar` (el corte sigue
siendo consulta). **Regla de atribución** espacio→elemento vía `IfcRelSpaceBoundary`: un elemento que
delimita `N` espacios distintos recibe `fraccion = 1/N` a cada espacio, **agregada por zona** (tabique
entre 2 aulas → 0,5/0,5; frontera de 1 solo espacio → 1,0; 2 espacios de la misma zona → 1,0). El
refinamiento (c) «por superficie de frontera» queda como **gancho forward**, sin implementar en v0
(el objetivo es valoración *rápida*: 50/50 es barato, determinista y golden-able). Precondición de
calidad del modelo (espacios+zonas+fronteras) = competencia del **QA/IDS de C4** aguas arriba.

## D22 · *Fallback* funcional — **`criterio/AQ/v2` nuevo** (no re-anclar v1)

Cuando el modelo no declara agrupación funcional nativa (ni `IfcSystem` ni `IfcZone`/espacios), el eje
`funcional` se deriva de la tabla **`reglas_sistema`** (clase/uso → sistema grueso) con
`fuente = "criterio"`. Como `reglas_sistema` no existe y `criterio/AQ/v1` está **anclado por hash**
(lo referencian `GOL-PRE-01/02`), se materializa como **nueva versión anclada `criterio/AQ/v2`** =
`v1` + `reglas_sistema` (mapeo clase→partida **idéntico** a v1; v2 solo añade la tabla de *fallback*).
`v1` y sus goldens quedan **intactos** (precedente de la inyección de `Qto`, D_modelo: no se edita lo
anclado, se crea nuevo con su propia ancla). Taxonomía del sistema grueso anclada a la tabla *Systems*
de **Uniclass (`Ss`)** (residual N-06). **Rechazadas** (por JM): re-anclar `v1` in situ; y diferir el
*fallback* (incumpliría el criterio de aceptación de E2.1).

**Refinamiento ratificado por JM (2026-07-08): el *fallback* casa POR JERARQUÍA de tipos IFC.** Una
regla de `reglas_sistema` casa si su `clase` es la clase del elemento **o cualquiera de sus
SUPERTIPOS** (el parser pasa la ascendencia de tipos IFC del elemento). Así **~10 familias por
dominio** —Estructura, Envolvente, Particiones, Instalaciones, Carpintería, Acabados, Cimentación,
Urbanización, Mobiliario y equipamiento, + catch-all «Elementos constructivos»— cubren el **centenar
de clases** del estándar **sin enumerarlas una a una** (p. ej. una sola regla `IfcDistributionElement`
cubre toda la MEP; una clase no listada como `IfcPipeSegment` casa por ese supertipo). El orden de la
tabla es la precedencia (específico→general); `reglas_sistema_default` = «Sin clasificar» cubre lo no
mapeado (nunca error). Nota honesta: el *fallback* solo aplica a objetos **medidos** (los que llevan
partida); su universo real es el conjunto que el criterio mide, no las 100+ clases IFC.

## D23 · Fixtures y golden — **aumentar las de `GOL-PRE-01`** + caso NUEVO en E2.2

Las fixtures de cortes se obtienen **aumentando** las de `GOL-PRE-01` (copias de `ARQ.ifc`/`EST.ifc`
con `IfcSystem` + `IfcZone`+espacios+`IfcRelSpaceBoundary` + árbol 4.3 **inyectados**), con **md5
propios** (patrón de la inyección de `Qto`); las originales ancladas (`0b998513…`/`0d7e7f20…`) quedan
**intactas**. E2.1 entrega un **test de parser** que verifica los cortes completos, el *fallback* por
criterio (`fuente=criterio`) y el **50/50 en un tabique compartido**. La **golden de vista**
(invariante `Σ`, 5 vistas) es un caso **NUEVO `GOL-PRE-03`** (patrón `GOL-PRE-02`) y se entrega en
**E2.2**, nunca editando `GOL-PRE-01`. **Sin release** (los cortes son consulta).

---

# C5 — Decisiones de la PROYECCIÓN (Ola 1·E2.2 — `proyectar(presupuesto, modelo, eje, corte)`)

> Ratificadas con JM el **2026-07-08** (OK explícito vía la pregunta de arranque), antes de tocar
> código. Numeración **propia del C5**, continúan D1–D23. Materializan **E2.2** del handoff
> negocio→desarrollo (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E2) y cierran, junto
> a E2.1 (`cortes`), la pieza «valor a tiempo real por clasificación». Change SDD:
> `openspec/changes/c5-proyeccion-vista/`. **La proyección es consulta, no cálculo**: `proyectar` AGRUPA
> lo que ya existe (el reparto 50/50 lo resolvió el parser en E2.1). ZONA ANCLADA intocable: el eje coste
> (`precio_unitario`/`importe`), los packs, las fixtures con `Qto` de `GOL-PRE-01` (`0b998513…`/
> `0d7e7f20…`), las goldens `GOL-PRE-01`/`GOL-PRE-02`/`GOL-DOC-01` (byte-idénticas).

## D24 · Firma de `proyectar` — recibe el presupuesto **y el modelo**

`proyectar(presupuesto, modelo, eje, corte) → [{grupo, valor_total, unidad, n_partidas, guids[],
fuente}]`. Recibe **el modelo además del presupuesto**: el valor vive por partida
(`estado_mediciones[]`), pero los `cortes` viven por objeto (`modelo.objetos[].cortes`, E2.1) → hay que
leerlos del modelo. `corte ∈ {espacial, funcional, uniclass, gubim}`; `eje` = string libre (D17). Salida
ordenada por **primera aparición** del grupo (determinista); `fuente` del grupo = la de sus pertenencias
(un grupo alimentado por `ifc` y `criterio` declara `criterio`, traza honesta del *fallback*).
**Group-by puro:** no re-mide ni re-valora.

## D25 · Lectura del eje — coste = `importe`; no-coste = `valores[eje].total`

El valor de una partida es **`importe`** cuando `eje == "coste"` (canónico, D16), con `unidad` = la
`moneda` del `resumen` (EUR); y **`valores[eje].total`** en otro caso, con `unidad` = `valores[eje].unidad`
(una partida sin `valores[eje]` en ese run aporta **0**, forward-open). La `unidad` de salida es
**homogénea** en una proyección (todo EUR o todo kgCO₂e…): el valor proyectado es dinero/magnitud del eje,
no la unidad de medición (m²/m³) de la partida.

## D26 · Atribución partida→objeto — **por magnitud EXACTA** (el engine emite el desglose)

El valor de una partida se reparte entre sus objetos **en proporción a la magnitud realmente medida** de
cada uno en esa partida: `share_O = cantidad_O / Σ cantidad_O`. Como el precio unitario es **uniforme
dentro de la partida**, el reparto de cantidad = reparto de valor para **cualquier** eje. Para que
`proyectar` no re-mida (sigue siendo consulta), **el motor emite** `traza_cantidades:[{guid, cantidad}]`
por partida `origen=modelo` (la contribución que ya computa en su bucle). Un objeto aporta a varias
partidas con cantidades distintas (muro → fábrica m², enfoscado/pintura m²×2caras): cada partida guarda
la contribución a ELLA. `Σ cantidad_O == 0` → degrada a equitativo `1/n`. **Alternativas rechazadas por
JM:** *proxy del modelo* (peso = cantidad que casa la unidad; coincide con la exacta salvo factor de caras
no uniforme, pero es aproximación) y *equitativa por nº de objetos* (reparto por cabezas, desvía en
partidas con objetos de tamaños dispares). La exacta es fiel y honesta con «no recálculo» (lee lo que el
motor ya calculó); coste = una clave aditiva (bump 0.4.0; `GOL-PRE-01` verde, el recompute compara claves
nombradas). El *proxy* queda como nota, no como gancho (la exacta lo cubre).

## D27 · Conservación de Σ — residuales deterministas

`Σ proyección == Σ estado_mediciones` es **EXACTO** (salvo redondeo declarado): nada se pierde. Una
partida sin `trazabilidad` (`origen=regla`, p. ej. S&S `SYS010` al 2 %) va entera al grupo
**`"(sin geometría)"`** (`fuente="regla"`); un objeto sin el eje de corte pedido (o GUID ausente del
modelo) va al grupo **`"(sin clasificar)"`** (`fuente="—"`). Los residuales son grupos como cualquier
otro (auditables) e integran el invariante.

## D28 · Anclaje de `GOL-PRE-03` — DETERMINISMO + SEMÁNTICA + INVARIANTE (patrón D14)

El sandbox no corre ifcopenshell → **sin md5 de salida hardcodeado** (voto de JM, opción b de D14).
`_run_c5_proyeccion` ancla: (1) **identidad** por md5 de las fixtures aumentadas (`entradas_md5`); (2)
**DETERMINISMO** — `proyectar` 2× = misma salida; (3) **INVARIANTE** — `Σ valor_total == Σ
estado_mediciones[eje]` (±`importe_abs`) por cada `(eje, corte)`; (4) **SEMÁNTICA** — las CINCO vistas del
`expected` casan con la proyección recomputada: (i) por planta, (ii) por `IfcFacilityPart` 4.3, (iii) por
`IfcSystem`, (iv) por `IfcZone` 50/50 (atribución fraccionaria → Σ por zonas == total), (v) *fallback*
criterio (`fuente=criterio`). Caso **NUEVO** `GOL-PRE-03` (reusa banco/params de `GOL-PRE-01`, que queda
intacto). Un fallo se investiga en el ENGINE, jamás aflojando el check.

## D29 · Fixtures aumentadas + `criterio/AQ/v2`

Las fixtures de vista se obtienen **aumentando** las de `GOL-PRE-01`: `gen_fixtures.py` (conda `mcp-bim`)
inyecta de forma determinista un **árbol 4.3** (`IfcFacility`/`IfcFacilityPart`), `IfcSpace`+
`IfcRelSpaceBoundary` (para el 50/50 de un tabique entre dos zonas), `IfcZone` (2 zonas) e `IfcSystem`,
con **md5 propios**; las ancladas (`0b998513…`/`0d7e7f20…`) quedan **intactas** (precedente de la inyección
de `Qto`, D_modelo). `GOL-PRE-03` usa **`criterio/AQ/v2`** (v1 + `reglas_sistema`, D22) para la vista
*fallback*; `v1` y `GOL-PRE-01` intactos. La rama `proyeccion` ancla `v2` por su `content_sha256`
(`079c28e9…`, golden de pack de E2.1), **no** por `[packs.criterio]` (que sigue en `v1`). **Sin release**
(la proyección es consulta).

---

# C5 — Decisiones de la INGESTA BC3 (Ola 1·E0.1 — FIEBDC-3/2024 `.bc3` → pack `banco`)

> Ratificadas con JM el **2026-07-08** (OK explícito por delegación: «elige las opciones con mayor
> recorrido futuro»), antes de tocar código. Numeración **propia del C5**, continúan D1–D29.
> Materializan **E0.1** del handoff negocio→desarrollo
> (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E0) y hacen ejecutable la decisión de
> negocio **N-04 / D-026** (política de datos 3+2; el `.bc3` de muestra es PROPIO; redistribuir bases
> públicas espera a la verificación de licencia por JM). Change SDD: `openspec/changes/c5-bc3-ingesta/`.
> **La ingesta es traducción determinista, no cálculo:** el mismo `.bc3` → el mismo `banco.json` byte a
> byte. **NO toca ningún esquema de contrato** (reutiliza el esquema de banco tal cual). ZONA ANCLADA
> intocable: el eje coste, los packs `criterio/AQ/v1`+`v2` y `banco/AQ-DEMO/v1` (identidad por hash), las
> golden `GOL-PRE-01/02/03` y `GOL-DOC-01` (byte-idénticas).

## D30 · Casa y API — `engines/bc3` releaseable (la de mayor recorrido futuro)

El adaptador vive en `engines/bc3/` como **paquete uv `aqyra-bc3`** (espejo estructural de
`engines/presupuesto`, D6): `pyproject.toml` (hatchling, **sin dependencias** — stdlib pura) +
`src/aqyra_bc3/` + `tests/` + miembro de `[tool.uv.workspace]`. Hogar cohesivo para las **dos**
direcciones de la frontera: `ingerir_bc3(path, *, banco, titulo=None, costes_indirectos_pct="0.03") →
dict` (E0.1) y `emitir_bc3(salida) → .bc3` (E0.2, gancho forward). Releaseable (tag `aqyra-bc3-v*` =
Llave 2 de JM) cuando la interoperabilidad cierre; **v0 SIN release** (como `presupuesto` 0.3/0.4).
Texto puro → **corre en CI y en el sandbox** (no necesita ifcopenshell). **Rechazadas por JM (menor
recorrido):** `packages/packs` (módulo `aqyra_packs.bc3`, más mínimo pero mezcla ingesta con el cargador
y no da hogar releaseable a la emisión); `tools/bc3` CLI (exento de la guardia SDD y **fuera** del pytest
de CI → el golden no correría en la Llave 1).

## D31 · Subset FIEBDC-3 v0 — `~V/~C/~D/~T`; charset del `~V` → UTF-8

Subset soportado en v0: **`~V`** (cabecera + **juego de caracteres**: `ANSI`→cp1252 por defecto,
`850`/`437`, `UTF-8`, `ISO-8859-1`; se normaliza a **UTF-8**; separador campo `|`, subcampo `\`, decimal
`.`), **`~C`** (conceptos: `codigo`, `unidad`, `resumen`→`descripcion`, `precio`, `tipo`→naturaleza
`1`=`mano_obra`/`2`=`maquinaria`/`3`=`material`, `0`/vacío=partida), **`~D`** (descomposiciones: tripletes
`hijo\factor\rendimiento` → `componentes`), **`~T`** (texto de pliego: **se parsea** pero **NO se emite**
al banco v0 — el esquema de banco no lo lleva; gancho forward E4-pliego/E0.2, sin añadir clave nueva:
forward-open). El **`~M`** (mediciones) queda **fuera de v0**: pertenece a un presupuesto/obra, es del
flujo de E0.2 (emisión/round-trip); se ignora si aparece.

## D32 · Precio de partida y costes indirectos — Σsub + CI(3% param) con guarda ±0,01 vs el `~C`

`subtotal = precio_hijo × factor × rendimiento` (**Decimal**, `ROUND_HALF_UP`, 2 decimales — dinero sin
float); `costes_indirectos = Σ subtotales × costes_indirectos_pct`; `precio = Σ subtotales +
costes_indirectos`. `costes_indirectos_pct` **v0 = 3%** (parámetro; **gancho forward** para leerlo de los
coeficientes del propio BC3, que varían entre emisores — se difiere para no abrir superficie de parser).
**Guarda de consistencia:** el precio compuesto debe casar (**±0,01**) con el precio declarado en el `~C`;
si no, aviso auditable (`_avisos_ingesta`), **nunca se silencia** (espíritu de D7, la guarda de huecos).
**Rechazadas por JM:** precio del `~C` literal con CI residual (rompe la homogeneidad de
`costes_indirectos_pct` global del banco); leer el `%CI` del BC3 ya en v0 (superficie heterogénea).

## D33 · Anclaje del pack de muestra — `banco/AQ-BC3-DEMO/v1` + `[packs.banco_bc3]`, doble golden

Pack **`banco/AQ-BC3-DEMO/v1`** con `fuente/muestra.bc3` como **provenance** auditable (el `.bc3`
PROPIO/sintético que lo produce, D-026). Sección NUEVA **`[packs.banco_bc3]`** en `versions.lock`
(espejo de `[packs.banco]`); `[packs.banco]=AQ-DEMO/v1` **intacto**. **Doble golden** contra el drift:
(1) golden **de pack** (`packages/packs/tests/test_packs.py`): `content_sha256` del `contenido` +
`md5(banco.json)` + `md5(muestra.bc3)`; (2) golden **del parser** (`engines/bc3/tests/test_bc3.py`):
`ingerir_bc3(fuente/muestra.bc3)` **reproduce** el `banco.json` anclado byte a byte (determinismo del
adaptador). Un fallo se corrige en el **código**, jamás editando el banco anclado. **Rechazada por JM:**
anclar solo por golden de pack sin fila en `versions.lock` (menor recorrido; un banco «adoptable» encaja
mejor con su fila propia). **Sin release** (la ingesta es interop; el tag de `aqyra-bc3` = Llave 2 cuando
JM lo decida, probablemente al cerrar E0.2).

---

# C5 — Decisiones de la EMISIÓN BC3 (Ola 1·E0.2 — `salida-presupuesto` → FIEBDC-3/2024 `.bc3`)

> Ratificadas con JM el **2026-07-09** (OK explícito por opciones), antes de tocar código. Numeración
> **propia del C5**, continúan D1–D33. Materializan **E0.2** del handoff negocio→desarrollo
> (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E0) y **cierran la Ola 1** (coste
> conectado). Change SDD: `openspec/changes/c5-bc3-emision/`. **La emisión es traducción determinista, no
> cálculo:** la misma `salida-presupuesto` → el mismo `.bc3` salvo el sello de fecha del `~V`. **ADITIVA**
> sobre `engines/bc3` (E0.1); **NO toca ningún esquema de contrato** (LEE `salida-presupuesto`). ZONA
> ANCLADA intocable: el eje coste, los packs `criterio/AQ/v1`+`v2`, `banco/AQ-DEMO/v1` y `banco/AQ-BC3-DEMO/v1`
> (identidad por hash), las golden `GOL-PRE-01/02/03` y `GOL-DOC-01` (byte-idénticas; `GOL-PRE-01` se
> **consume** como entrada del round-trip, no se re-ancla), y `ingerir_bc3` (intacto).

## D34 · Emisión: API `emitir_bc3` + re-lector `leer_bc3_presupuesto` en `aqyra_bc3` (la de mayor recorrido)

La emisión es ADITIVA sobre `engines/bc3` (D30), la dirección inversa de la ingesta.
`emitir_bc3(salida, *, fecha=None, charset="utf-8", programa="AQYRA", autor="Aqyra", titulo=None) → str`
devuelve el texto `.bc3` (simétrico de `serializar_banco`); el CLI lo escribe con el `charset`. El
**re-lector del round-trip** `leer_bc3_presupuesto(origen) → {"estado_mediciones": […]}` vive **en el
paquete** (no en el test): reconstruye `estado_mediciones` (cantidad de las `~M`, precio del `~C`,
`importe = cantidad × precio_unitario`, trazabilidad de GUIDs) y es capacidad reutilizable (E5/importación
lo reusan). `ingerir_bc3` **no se toca**. **Rechazada por JM (menor recorrido):** el re-lector como función
privada del test.

## D35 · Subset EMITIDO v0 `~V/~C/~D/~M/~T`; las `~M` por DESGLOSE POR OBJETO

Se emiten `~V` (cabecera + charset + sello de fecha), `~C` (partidas `tipo 0` + componentes del cuadro nº2
con naturaleza `1`/`2`/`3`; el hijo se codifica `⟨codigo⟩.⟨n⟩`, determinista), `~D` (descomposiciones:
`hijo\factor(=1)\rendimiento`, tal que `precio_hijo × 1 × rendimiento = subtotal`), `~M` (mediciones) y `~T`
(§D38). Las líneas de `~M` van por **desglose por objeto** desde `traza_cantidades` (una línea por objeto,
con el **GUID en el comentario** — preserva la trazabilidad, la joya) y por **línea única** con la cantidad
total cuando la partida no tiene `traza_cantidades` (p. ej. `origen=regla` como S&S, o las partidas de
`GOL-PRE-01`, que llevan `trazabilidad` pero no `traza_cantidades`). El total del `~M` = Σ de las líneas.
**Rechazada por JM:** una sola línea con la cantidad total siempre (perdería el desglose por objeto/GUID).

## D36 · Codificación de salida UTF-8 (parametrizable) + sello de fecha determinista del `~V`

Salida en **UTF-8** por defecto (FIEBDC-3/2024 lo admite; sin pérdida de acentos; el `~V` declara `UTF-8`),
**parametrizable a ANSI/cp1252** (`--charset cp1252` → token `ANSI`) para destinos legacy
(Presto/Arquímedes/TCQ). El **sello de fecha** del `~V` es el parámetro `fecha` (AAAAMMDD), con valor por
defecto **determinista y documentado** (`_FECHA_DEFAULT`), **nunca** `date.today()`: es el ÚNICO
no-determinismo del emisor (misma salida + mismo `fecha` → mismos bytes). El sello sella también la fecha de
precio de cada `~C` (comportamiento FIEBDC); toda diferencia entre dos emisiones se explica por sustitución
del sello. **Rechazada por JM:** ANSI por defecto.

## D37 · Anclaje del round-trip por IDENTIDAD DE IMPORTES (semántico), NO md5 del `.bc3`

El golden vive como pytest en `engines/bc3/tests/test_emision.py` (texto puro → CI + sandbox) que **consume**
la `salida-presupuesto` ANCLADA de `GOL-PRE-01` (`expected.json → presupuesto`; se LEE, no se recalcula —
D4). Ancla **SEMÁNTICA**: el `.bc3` emitido, REIMPORTADO por `leer_bc3_presupuesto`, reproduce cada
`importe` (**±0,01**) y `cantidad` (**±0,5%**, D3) del `estado_mediciones`, y la Σ casa con el **PEM
7 022,53**. **NO** por `md5` del `.bc3` (el sello de fecha lo haría inestable) — patrón semántico heredado
(D14/D28). `packages/golden` **no se toca** (GOL-PRE-01 se consume como entrada, no se re-ancla).

## D38 · Pliego `~T` mínimo desde la descripción (gancho E4-pliego)

Se emite un `~T` por partida con **su descripción** como pliego mínimo. La `salida-presupuesto` v0 no porta
un pliego estructurado; el `~T` mínimo deja el `.bc3` más completo para el receptor y es el **gancho** para
**E4-pliego** (cuando el pliego real entre en la salida o se resuelva del banco/criterio, el `~T` se
enriquece). El re-lector **ignora** el `~T` para los importes (no afecta al round-trip). **Rechazada por
JM:** no emitir `~T` en v0.

---

# C5 — Decisiones del EJE CARBONO (Ola 2·E3 — `valores.carbono` + etapas + `banco-carbono` + `GOL-CAR-01`)

> Ratificadas con JM el **2026-07-09** (OK explícito por opciones, A/A/A/A), antes de tocar código.
> Numeración **propia del C5**, continúan D1–D38. Materializan **E3.1+E3.2+E3.3** del handoff
> negocio→desarrollo (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E3) y **abren la Ola 2**
> (carbono). Hacen ejecutable **D-025/N-03** (carbono = extensión forward-open de C5, Opción A),
> **D-027/N-05** (genéricos v0 + EPD premium) y **D-026/N-04** (el banco-carbono v0 es PROPIO/sintético;
> las semillas reales esperan a la verificación de licencia por JM = E5.2). Change SDD:
> `openspec/changes/c5-eje-carbono/`. **La valoración de carbono es traducción determinista, no cálculo:**
> el kgCO₂e sale del factor del banco-carbono anclado (convención banco+criterio, no verdad física,
> estatuto del PEM). **NO toca el esquema de SALIDA C5** (E1.1/D16–D18 ya fijaron `valores`+`etapas`). ZONA
> ANCLADA intocable: el eje coste (`precio_unitario`/`importe`), los packs `criterio/AQ/v1`+`v2`,
> `banco/AQ-DEMO/v1`, `banco/AQ-BC3-DEMO/v1` (identidad por hash), las golden `GOL-PRE-01/02/03` y
> `GOL-DOC-01` (byte-idénticas; E3 sólo AÑADE `GOL-CAR-01`).

## D39 · Pack `banco-carbono` — factor por CÓDIGO de partida + factores por etapa (Opción A)

Familia de pack **NUEVA `banco-carbono`** (aditiva al enum `codigos/normativa/banco/criterio/ids` de
`pack.schema.json`; `aqyra_packs.FAMILIAS` la gana). El factor se ancla **por código de partida** (la misma
junta que el precio en el banco de coste; el mapeo clase→partida del criterio no cambia entre ejes, D19).
Cada partida del `banco-carbono` declara: `precio` = factor **unitario** total (kgCO₂e por unidad de
medición), `etapas` = factores **por etapa por unidad** (EN 15978: `A1A3` producto, `A4A5` construcción)
cuya suma = `precio` (guarda de consistencia ±0,01, estilo D32; si no casa, aviso auditable). **Hallazgo de
diseño:** como el esquema de salida exige `cuadro_precios_2[].componentes` con `minItems:1` y el motor emite
el cuadro nº2 en todo run, cada partida del `banco-carbono` declara **un** `componente` `tipo:"material"`
(el factor embebido) para que la salida de carbono conforme **sin tocar el esquema**; el desglose real vive
en `valores.carbono.etapas`. **Rechazadas por JM:** C (factor por material del componente — es la capa
EPD-premium por producto, N-05, no el genérico v0). El pack `banco-carbono/generico/v1` es **PROPIO/
sintético** (D-026): factores alineados en **forma** con EN 15804 / Level(s), NO copiados de Ökobaudat/
INIES/EC3.

## D40 · Reparto de etapas en el motor — última etapa = residuo → Σ etapas = total EXACTO (Opción A)

`presupuestar(..., eje="carbono")` emite, por partida `origen=modelo`, `valores.carbono.etapas`:
`etapa_total = factor_etapa × cantidad` (redondeo 2 dec, `ROUND_HALF_UP`); la **última etapa presente**
(orden canónico `A1A3`, `A4A5`, `B`, `C`, `D`) **absorbe el residuo de redondeo** → invariante **Σ etapas =
total** exacto (D18), verificado en las 7 partidas de la medición de `GOL-PRE-01`. El eje **coste** (default)
sigue **sin** emitir `valores` (D16/D19) → `GOL-PRE-01` byte-idéntica. Una partida sin factor de banco
(`origen=regla`, S&S) lleva `valores.carbono` etiquetado **sin** `etapas` (forward-open). `engines/presupuesto`
sube **0.4.0 → 0.5.0** (aditivo; `medir`/`presupuestar` coste/`escribir_coste`/`proyectar` intactos).
**Rechazada por JM:** B (factor total + reparto por ratio fijo — inventaría el reparto en vez de leerlo del
dato por etapa).

## D41 · Convención del eje — `id="carbono"`, `unidad="kgCO2e"`, etapas mínimas A1A3+A4A5; esquema de salida intacto

El eje se identifica `carbono` (string libre, D17), unidad `kgCO2e`, etapas mínimas `A1A3` (producto) +
`A4A5` (construcción) con Σ etapas = total (D18). **El esquema de SALIDA C5 no cambia** (la forma de
`valores`/`etapas` ya la fijó E1.1). El delta del contrato en E3 es sólo el enum de familia de
`pack.schema.json` (D39) + esta anclada + la nota de `contrato.md`. Verificado: la salida de carbono
**conforma `salida-presupuesto.schema.json` sin editarlo**.

## D42 · Trazabilidad del origen del factor (`epd`/`generico`) — DIFERIDA (Opción A)

No se añade clave en v0. El campo `banco` de cada `valores.carbono` ya dice `banco-carbono/generico/v1` (y
dirá `.../epd/vN` cuando exista el pack premium), así que el origen del factor **ya es trazable sin tocar el
esquema de salida**. La clave dedicada `origen_factor` se materializa cuando el motor mezcle EPD+genérico
(N-05, capa premium posterior). **Rechazada por JM:** B (añadir ya la clave aditiva `origen_factor` en
`valor_eje`).

## D43 · Runner del golden — rama de modo `_run_c5_carbono` bajo `run_case_c5` (Opción A)

Nueva rama `expected.modo == "carbono"` → `_run_c5_carbono(...)`, igual que las ramas `5d`/`documento`/
`proyeccion`. El contrato sigue siendo `"C5"` en `CASE_RUNNERS` (sin entrada nueva). **Rechazada por JM:** B
(`run_case_car` nuevo en `CASE_RUNNERS` — duplica el andamiaje de despacho y se aparta del patrón de
`GOL-PRE-02/03`/`GOL-DOC-01`).

## D44 · Anclaje de `GOL-CAR-01` — fixtures aumentadas de `GOL-PRE-03` + `criterio/AQ/v2`; determinismo+semántica+invariante (Opción A)

`GOL-CAR-01` valora la MISMA medición anclada de `GOL-PRE-01` en carbono, reusando las **fixtures
aumentadas** de `GOL-PRE-03` (misma medición + cortes `IfcSystem`/`IfcZone`/árbol 4.3 inyectados, md5 ya
anclados `19a272a5…`/`f1d25192…`) + `criterio/AQ/v2` → valoración carbono por partida + etapas **y** una
proyección de carbono **real** por planta (`proyectar`, invariante Σ). **Modo anclado (D14/D28, sin md5 de
salida):** el sandbox no corre ifcopenshell → el recompute del golden corre en el conda `mcp-bim` de JM.
Anclaje por DETERMINISMO (presupuestar/proyectar 2× idéntico) + SEMÁNTICA (`valores.carbono` por partida:
unitario×cantidad=total, unidad kgCO₂e, banco, etapas A1A3/A4A5, Σ etapas=total; resumen del eje) +
INVARIANTE (Σ proyección == PEM del eje). Oráculo del eje calculado a mano y verificado ×2 (PEM eje **8 032,40
kgCO₂e** = A1A3 7 422,36 + A4A5 452,54 + S&S 157,50; proyección espacial Nivel 00 631,36 · Planta Baja
4 003,54 · Nivel 01 3 240,00 · sin geometría 157,50). `GOL-PRE-01/02/03`/`GOL-DOC-01` byte-idénticas. Un
fallo se investiga en el ENGINE, jamás aflojando el check. **Rechazada por JM:** B (fixtures llanas de
`GOL-PRE-01` + `criterio/AQ/v1`, autocontenido pero con proyección trivial en residuales).

---
*Regla de oro heredada: un fallo NO se arregla aflojando la golden. Contract-first de verdad — si al
calcular el presupuesto a mano el esquema cojea, se corrige el esquema AHORA. El CI nunca certifica
(Llave 2 = JM).*


## D45 · Fuentes abiertas ratificadas + atribucion (E5.2, via limpia) (ratificada por JM 2026-07-10)

Para derivar la semilla REAL de carbono (E5.2), JM ratifica cuatro fuentes con licencia EXPLICITAMENTE ABIERTA
(uso comercial + obra derivada + redistribucion con atribucion): **ADEME Base Carbone** (Licence Ouverte/Etalab
2.0), **ProBas/Umweltbundesamt** (dl-de/by-2.0), **UK GHG Conversion Factors** (OGL v3.0) como primarias/
complemento, y **USLCI/NREL** (dominio publico probable, **licencia por confirmar dataset a dataset antes de
anclar**) como secundaria. **Excluidas** (permiso escrito, verificado 2026-07-09/10): Okobaudat, INIES, EC3, ICE
(Bath). Registro de verificacion: `Aqyra-Negocio/RECONCILIACION_licencias-carbono.md`. Atribucion arrastrada al
pack (`banco.json>atribucion` y `>provenance`) y, cuando proceda, a la salida: ADEME->"Licence Ouverte 2.0";
ProBas->"dl-de/by-2.0, modificado por Aqyra" + URI (la licencia alemana exige marcar el cambio); UK->"Open
Government Licence v3.0 (Crown copyright)". **La IA propuso; JM firmo.**

## D46 · id/version del pack real — `generico/v2`, `v1` coexiste demo (Opcion A ratificada)

El pack REAL es `banco-carbono/generico/v2` (NUEVO). `generico/v1` (sintetico, E3) es INTOCABLE (lo ancla
`GOL-CAR-01` por su `content_sha256 44d0cd3f...` + `md5_banco 47fb4787...`) y **coexiste** marcado como demo (la
marca vive en la doc/`fuente`/DECISIONES, sin editar el fichero anclado). El pointer de produccion en
`versions.lock [packs.banco_carbono]` pasa a **v2** (patron `criterio/AQ v1->v2`); `GOL-CAR-01` referencia `v1`
por su `content_sha256` explicito (repuntar el lock a v2 no la rompe; verificado en el recompute). **Rechazadas
por JM:** B (id nuevo `abierto/v1`) y C (marcar `v1` deprecado).

## D47 · Metodo de derivacion — material x factor x cantidad + `provenance` por partida (Opcion A ratificada)

Cada factor por partida se DERIVA (EN 15804 modular / EN 15978): `A1A3 = Sum_material (masa_material_por_unidad x
factor_A1A3_material)` de fuente abierta; `A4A5 = transporte` (masa x 50 km x 0,086 kgCO2e/t.km, UK GHG, OGL) +
residuo A5 (0 en v0); `precio = A1A3 + A4A5` (Sum etapas = precio, guarda +-0,01, D39). Cada partida lleva un
bloque **`provenance`** aditivo (composicion de material por unidad = hipotesis de despacho documentada; fuente +
licencia + URI + calculo por material). El motor solo lee `precio`/`etapas`/`componentes` -> `provenance` es
documentacion inerte para el engine (esquema de salida intacto). Factores anclados (v2): hormigon 0,088 (ADEME
20719), acero reciclado 0,938 (ADEME 26730), ladrillo 0,20 (ProBas2 f472c5b1), cemento 0,866 (ADEME 20723) ->
mortero 0,173 (20% cemento), pintura 1,51 (ADEME 24255, proxy barniz acrilico), madera 0,0367 (ADEME 20721, neto
biogenico -> PPM010 candidato a refinar en v3/epd). **Rechazada por JM:** B (factor por partida sin composicion,
menos trazable). **Cada factor es DERIVABLE y TRAZABLE; el kgCO2e no se inventa** (convencion banco+criterio).

## D48 · Golden — golden de pack + `GOL-CAR-02` (Opcion A ratificada)

E5.2 ancla (i) el **golden de pack** de v2 (identidad de contenido: `content_sha256` + `md5_banco`, en
`test_packs.py`) y (ii) **`GOL-CAR-02`**: valora la MISMA medicion anclada de `GOL-PRE-01` con el banco REAL v2
por el runner `_run_c5_carbono` (D43), **generalizado** para leer la version del `banco_ref` del caso (sirve v1+v2; unico fichero de codigo tocado en E5.2, GOL-CAR-01 sigue verde), reusando las fixtures de
`GOL-CAR-01`/`GOL-PRE-03` (mismos md5 `19a272a5...`/`f1d25192...`) + `criterio/AQ/v2`. Anclaje por DETERMINISMO +
SEMANTICA + INVARIANTE (patron D14/D28/D44, sin md5 de salida): por partida `origen=modelo` `valores.carbono`
(unitario x cantidad = total, unidad kgCO2e, banco `banco-carbono/generico/v2`, etapas A1A3/A4A5, Sum etapas =
total); S&S (`origen=regla`) etiquetado sin etapas; proyeccion espacial con `Sum proyeccion == PEM del eje`.
**Oraculo del eje calculado a mano y verificado x2: PEM carbono = 7 117,69 kgCO2e** (Sum modelo 6 978,13 + S&S 2%
139,56; proyeccion Nivel 00 731,10 + Planta Baja 2 938,66 + Nivel 01 3 308,37 + sin geometria 139,56). El
recompute pasa por `medir()` (ifcopenshell) -> corre en el conda `mcp-bim` de JM (como `GOL-CAR-01`), NO en el
sandbox. `GOL-CAR-01` (sintetico v1) y `GOL-PRE-01/02/03` y `GOL-DOC-01` INTACTAS. **Rechazada por JM:** B (solo
golden de pack, sin ejercitar el banco end-to-end). El MOTOR no se toca (`engines/presupuesto` 0.5.0 ya emite
etapas); el esquema de salida C5 no se toca.


## D49 - Fuente abierta ratificada: BCCA (Junta de Andalucia) CC-BY 3.0 (primaria); Extremadura fuera de v0

El banco de coste REAL se deriva de la Base de Costes de la Construccion de Andalucia (BCCA), Consejeria de
Fomento, Articulacion del Territorio y Vivienda (Junta de Andalucia), edicion BCCA2023_V02 (FIEBDC-3/2020,
01-11-2023, ~6.600 precios), bajo Creative Commons Reconocimiento 3.0 (CC-BY 3.0) via el aviso legal del portal
(la ficha de la BCCA no fija restriccion propia -> hereda el regimen general: uso comercial + obra derivada +
redistribucion en producto, con atribucion). Atribucion a arrastrar en provenance/fuente: "Informacion obtenida
del Portal de la Junta de Andalucia" (sin logotipos/escudos) + el codigo BCCA de origen de cada partida + su
edicion/URI. Extremadura (GOBEX) = licencia por confirmar -> fuera de v0 (contraste/forward). BEDEC/CYPE/PREOC/IVE
fuera (el cliente aporta). Registro: Aqyra-Negocio/RECONCILIACION_licencias-coste.md. Gobierna N-04/D-026 (via
limpia). La IA propuso; JM firmo (2026-07-11).

## D50 - id/version del pack real: banco/BCCA/v1 + fila [packs.banco_bcca] (Opcion A ratificada)

El pack real es banco/BCCA/v1 (NUEVO), con su propia fila [packs.banco_bcca] en versions.lock (espejo de
[packs.banco_bc3]). [packs.banco]=AQ-DEMO/v1 y [packs.banco_bc3]=AQ-BC3-DEMO/v1 INTOCABLES (los anclan
GOL-PRE-01/02/03 + golden de pack). La fuente es un tercero (BCCA), no el despacho -> su propio id (BCCA) y su
propia fila; el pointer de coste real explicito = esta fila. El motor elige el banco por banco_ref del caso, no
por el pointer del lock -> anadir la fila no rompe ninguna golden anclada. Rechazada: B (AQ-DEMO/v2, mezcla banco
propio con derivado de tercero bajo el mismo id). La IA propuso; JM firmo (2026-07-11).

## D51 - Alcance: las 7 partidas del criterio con precio REAL BCCA + provenance (Opcion A ratificada)

v0 ancla las 7 partidas del criterio (FAB010, REV010, PIN010, EHL010, EHS010, CSZ010, PPM010), cada una con el
precio y la descomposicion REALES (MO/material/maquinaria + rendimientos + precios) de la unidad de obra BCCA
equivalente, materializado el NUCLEO por ingerir_bc3 de un .bc3 semilla (7 unidades recodificadas a los codigos
del criterio). Equivalencias ancladas: FAB010<-06LPC80000 (citara l/perf. para revestir, 28,94), REV010<-10CEE00001
(enfoscado sin maestrear, 12,98), PIN010<-13IPP90016 (pintura plastica lisa, 4,60), EHL010<-05HRL80010 (losa HA-25
i/enc.madera+acero, 418,01), EHS010<-05HRP80010 (pilar HA-25 i/enc.metalico+acero, 433,17), CSZ010<-03HRZ80000
(zapata HA-25 armada B400S, 164,18), PPM010<-11MPP00151 (puerta paso pintar 1H, valorada por BCCA en m2 de hueco a
125,37 EUR/m2; PPM010 es ud -> se adopta la superficie de hueco de la puerta del modelo 1,00x2,10=2,10 m2, con los
rendimientos escalados x2,10 -> 263,29 EUR/ud). El criterio y el adaptador quedan INTACTOS; delta de spec NULO (el
codigo del criterio es un alias documentado en provenance: derivacion por Aqyra, via limpia). La base BCCA completa
con codigos nativos exige criterio/AQ/v3 = gancho FORWARD, no v0. Rechazada: B (base completa). La IA propuso; JM
firmo (2026-07-11).

## D52 - Golden: pack + parser (nucleo presupuestable) + GOL-PRE-04 (Opcion A; encaje provenance Opcion B)

E5.1 ancla (i) el golden de pack de banco/BCCA/v1 (content_sha256 9c790ffe15f4f3751ee3a5b6dfdcdbfb7c326805ea0902f21a3c3fa6357045d1 + md5_banco 82e2a445e5daeb85878f401ee607d396 + md5_bc3 f9dededaaac14a3f75005dc1bffd118f, en
test_packs.py), (ii) el golden del PARSER (engines/bc3/tests/test_bc3.py, texto puro, sandbox) y (iii) GOL-PRE-04:
valora la MISMA medicion anclada de GOL-PRE-01 con banco/BCCA/v1 + criterio/AQ/v1 por run_case_c5 (modo coste),
con el runner GENERALIZADO para anclar el banco_ref del caso contra su clave de lock correcta (busca en
[packs.banco]/[packs.banco_bc3]/[packs.banco_bcca] la que casa id+version -> sirve AQ-DEMO y BCCA; unico fichero de
codigo tocado; GOL-PRE-01/02/03 siguen verdes), reusando las fixtures de GOL-PRE-01 (mismos entradas_md5). Oraculo
calculado a mano y verificado x2: importes = cantidad x precio del banco BCCA (HALF_UP 2 dec); PEM 10261.97 ->
(+13% GG 1334.06 +6% BI 615.72) base 12211.75 -> (+21% IVA 2564.47) PEC 14776.22 EUR (S&S = 2% del PEM medible
10060.75 = 201.22). El recompute pasa por medir() (ifcopenshell) -> corre en el conda mcp-bim de JM y en el gate CI.
GOL-PRE-01/02/03, GOL-CAR-01/02, GOL-DOC-01, GOL-PLI-01 INTACTAS.

Encaje provenance <-> golden del parser (Opcion B ratificada 2026-07-11): el tasks/design pedian provenance por
partida EN banco.json + descripcion honesta, pero el adaptador ingerir_bc3 (0.2.0, INTOCABLE) NO emite provenance y
codifica una descripcion fija ("de muestra, sintetico... demostracion"), falsa para un banco BCCA real. Resolucion:
banco.json se REDACTA (forma AQ-DEMO + provenance por partida + descripcion honesta); el golden del parser verifica
que ingerir_bc3(fuente/BCCA.bc3, costes_indirectos_pct=0) reproduce el SUBCONJUNTO PRESUPUESTABLE de cada partida
(codigo/unidad/componentes/costes_indirectos/precio) -la sustancia determinista del numero, que sale del .bc3, no se
inventa- mientras provenance/descripcion son metadatos aditivos (el motor solo lee codigo/unidad/componentes/precio
-> son documentacion inerte para el engine). costes_indirectos_pct=0 (el precio BCCA declarado = suma de la
descomposicion, sin CI a nivel de unidad). El adaptador engines/bc3 NO se toca. Rechazadas: extender ingerir_bc3
(tocaria el adaptador anclado) y provenance solo en pack.json (dejaria la descripcion "sintetico" falsa dentro de
banco.json, contra el diseno). La IA propuso; JM firmo (2026-07-11). Ref cruzada: Aqyra-Negocio/RECONCILIACION_
licencias-coste.md.

## D53 - Alcance e identidad del banco nativo: subconjunto NATIVO curado + banco/BCCA-nativo/v1 (Opcion A ratificada)

E5.1b materializa el coste REAL con codigos BCCA NATIVOS. Hallazgo del Paso 0: ingerir el .bc3 completo de la BCCA
(BCCA2023_V02, ~6.600 precios) con aqyra_bc3.ingerir_bc3 da 8.426 partidas pero el 34,5% NO cuadra (precio recompuesto
!= declarado) + 845 sin componentes, porque el fichero completo usa registros FIEBDC (AUX#, parametricos, coeficientes)
que el subset v0 del parser (~V/~C/~D/~T, un nivel) no resuelve. Un banco completo LIMPIO exigiria EXTENDER engines/bc3
(INTOCABLE por guardarrail). Por tanto v0 = SUBCONJUNTO NATIVO CURADO (patron semilla): un .bc3 curado (aplanado, sin
AUX, extraido verbatim del original) de las 6 unidades de obra BCCA nativas, cada precio verificado cuadra +-0,01;
el codigo de partida ES el codigo BCCA (06LPC80000...). id/version: banco/BCCA-nativo/v1 con su propia fila
[packs.banco_bcca_nativo] (NUEVA). La semilla banco/BCCA/v1 (alias del criterio) queda INTACTA bajo [packs.banco_bcca]
(la ancla GOL-PRE-04 por su banco_ref explicito). El .bc3 curado se ancla en fuente/ (procedencia auditable). La base
BCCA completa (~6.600 con codigos nativos) = FORWARD (exige extender engines/bc3 al subset FIEBDC de auxiliares/
parametricos). Rechazadas: B (banco completo tal cual, sucio) y C (extender el engine ahora, rompe guardarrail). La IA
propuso; JM firmo (2026-07-12).

## D54 - Estrategia del criterio nativo: corte de 4 clases, puerta = forward (Opcion A ratificada)

criterio/AQ/v3 (NUEVO) mapea IfcWall/IfcSlab/IfcColumn/IfcFooting a los codigos BCCA nativos (IfcWall->06LPC80000+
10CEE00001+13IPP90016; IfcSlab->05HRL80010; IfcColumn->05HRP80010; IfcFooting->03HRZ80000) con la MISMA medicion que
v1 (unidad, magnitud, descuento de huecos por umbral, factor de caras). Declara su propio bloque `capitulos` nativo
(el motor es pack-overridable: criterio.get("capitulos"); el catalogo DEFAULT mapea los codigos alias). SYS010 (S&S por
ratio, origen=regla) se conserva. La PUERTA (IfcDoor->11MPP00151) queda FUERA de v0: su unidad nativa BCCA es m2 de
HUECO (125,37 EUR/m2) y el modelo neutro anclado no expone el area del hueco (2,10) - mide conteo + area de HOJA
(1,845); una puerta nativa exige la medicion del hueco = forward explicito. v1/v2 INTACTOS; [packs.criterio] sigue en
v1 (GOL-PRE-01/02/03/04 intactas); v3 se ancla por su content_sha256. Rechazadas: B (puerta nativa m2 con area de hoja,
semanticamente la hoja no el hueco) y C (puerta con convencion ud x2,10, no nativa). La IA propuso; JM firmo (2026-07-12).

## D55 - Golden GOL-PRE-05 + identidad de anclaje (Opcion A ratificada)

GOL-PRE-05 (NUEVO) valora la MISMA medicion anclada de GOL-PRE-01 con criterio/AQ/v3 + banco/BCCA-nativo/v1 por
run_case_c5 (modo coste), reusando las fixtures de GOL-PRE-01 (mismos entradas_md5). 6 partidas nativas (concreto/
albanileria) + S&S; la puerta AUSENTE (D54). Oraculo calculado a mano y verificado x2 (coincide con el recompute del
engine): importes = cantidad x precio del banco nativo (HALF_UP 2 dec); PEM medible 9.797,46; S&S 2% = 195,95;
PEM 9.993,41 -> (+13% GG 1.299,14 +6% BI 599,60) base 11.892,15 -> (+21% IVA 2.497,35) PEC 14.389,50 EUR. Anclaje sin
romper GOL-PRE-04: el banco nativo va en clave de lock NUEVA [packs.banco_bcca_nativo] (un bump de [packs.banco_bcca]->
v2 romperia GOL-PRE-04, que casa por id+version exactos); el criterio v3, que NO es el pointer, se ancla por su
content_sha256 (patron AQ/v2 de la ruta de carbono). Unico fichero de codigo tocado: run_golden.py (2 retoques
aditivos: banco_bcca_nativo en la tupla de _banco_anclado_en_lock; criterio no-pointer por content_sha256). El recompute
pasa por medir() (ifcopenshell) -> conda mcp-bim de JM + gate CI. GOL-PRE-01/02/03/04, GOL-CAR-01/02, GOL-DOC-01,
GOL-PLI-01 INTACTAS. La IA propuso; JM firmo (2026-07-12).
