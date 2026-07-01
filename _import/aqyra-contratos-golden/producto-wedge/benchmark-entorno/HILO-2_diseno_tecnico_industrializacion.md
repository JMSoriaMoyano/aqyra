# Hilo 2 — Diseño técnico: industrializar lo que tenemos + capa 6 (operador IA) + capa 7 (foso)

> **Estado:** diseño técnico preparado por la IA (Ing. BIM-IFC / PM) para que **JM revise, ajuste y firme**. Conforme al gobierno: la IA propone el diseño; **no implementa ni firma**. Los esquemas concretos (F1.1, F1.2, contratos nuevos) son **strawman para aprobación de JM**, no decisiones cerradas.
> **Base:** `TESIS_PRODUCTO.md`, `GOBIERNO_QA_Y_VERSIONES.md`, `SPRINT_0_REENCUADRE_PROPUESTA.md`, `producto-wedge/PRD/B1.1`–`B1.2`, `HILO-1_analisis_construir_entorno.md`, `versions.lock`. **Fecha:** 2026-06-24.
> **Encaja con:** N1.1 (monorepo+tag), F1.1 (esquema del átomo golden), F1.2 (capa de recuperación por OIR) del Sprint 0 reencuadrado.

---

## 0. Qué resuelve este documento

Tres cosas, en este orden de valor (el del reencuadre: foso primero):

1. **Capa 7 — el foso.** Diseño del **átomo de caso golden** (F1.1) y de la **capa de indexado · recuperación · reaplicación por requisito de información** OIR→AIR/PIR→EIR (F1.2). Es lo que no existe ni en Estructurando.
2. **Capa 6 — el operador IA nativo.** Cómo un agente genera el IFC desde lenguaje natural, lo audita, lo enruta al cálculo y mueve incidencias, operando **sobre texto** (IFC, BCF) sin GUI ni binario.
3. **Industrializar los plugins caseros.** Llevar lo artesanal (N0) a producto versionado y certificable (N4–N5): monorepo, contratos, empaquetado SemVer, CI/CD, suite golden y las tres capas de QA.

> El orden de exposición de este documento va de la infraestructura (parte A) al diferencial (partes B y C) por claridad técnica; el orden de **inversión** es el inverso (C y B antes que el pulido de A), según el reencuadre. Se recuerda en §8.

---

## 1. La escalera de industrialización N0→N5

El gobierno nombra la escalera «del nivel artesanal (N0) al de producción certificada (N4–N5)» y fija **N4 = trazable** (dos llaves operativas). Se propone esta articulación concreta de los seis peldaños como criterio común de "industrializado" (strawman, a ratificar por JM):

| Nivel | Nombre | Qué significa, operativamente | Puerta para subir |
|---|---|---|---|
| **N0** | Artesanal | Skill/plugin que funciona en manos de su autor; sin contrato, sin tests, sin versión. *(donde están hoy los plugins caseros)* | — |
| **N1** | Empaquetado | Vive en el monorepo; tiene **contrato declarado** (qué entra/sale), versión **SemVer** y release etiquetada y firmada. | Contrato escrito + primer tag |
| **N2** | Probado | Tiene **suite de tests** propia y al menos **1 caso golden** con su oráculo y tolerancia. | Golden verde en CI |
| **N3** | Integrado | Corre en **CI/CD**; la suite golden completa lo cubre; el consumidor lo ancla en `versions.lock`. | CI verde + pin |
| **N4** | Trazable / certificado | Sus salidas pasan las **tres capas de QA** y la **certificación de dos llaves** (golden verde + Informe QA limpio + firma JM). | Dos llaves |
| **N5** | Producción | Reproducible por alguien que no es el autor; documentado; SLA de mantenimiento; consumido por un piloto E2E. | Prueba E2E sin JM |

"Industrializar lo que tenemos" = mover cada plugin casero de N0 a **al menos N3**, y a **N4–N5** los que entran en la ruta de firma (cálculo) o son críticos para el foso.

---

## 2. Estado de partida: inventario y modelo dual

**Lo que ya existe (N0 artesanal)** y su destino de industrialización:

| Plugin casero | Capa del entorno | Nivel objetivo | Por qué |
|---|---|---|---|
| `iso19650-openbim` (`ifc-create`, `ifc-validate`, `narracion-a-ifc`, `bsdd-clasificacion`, `cde-audit`, `bep-eir`, `loin-matrix`) | Sustrato + generación + CDE + requisitos | **N4** | Alimenta capa 6 y produce las llaves OIR/EIR de capa 7 |
| `visor-ifc` | Visor | **N3** | Commodity; delgado e integrado (Hilo 1) |
| `estructuras-eurocodigos`, `instalaciones`, `obras-lineales`, `puentes`, `cte-documentos-basicos` | Cálculo / normativa | **N4–N5** | Ruta de firma: exige dos llaves |
| `memoria-calculo-despacho` | Documentación | **N3** | Salida; formato del despacho |
| motores `motor-fem`, `motor-calculo` | Núcleo | **N4–N5** | Oráculo + cálculo certificado |

**Modelo dual (no se toca, gobierna el diseño):** Estructurando = **productor** (desarrolla artesanal, publica releases firmadas `plugin-vX.Y.Z`); Estructurando 2.0 = **consumidor** (ancla en `versions.lock`, nunca «latest»; subir versión = re-correr golden y adoptar solo si verde). **2.0 nunca bifurca el núcleo.**

**Contratos vigentes (superficie de interfaz, SemVer):** `C1` parser/lectura · `C4` red · `C5` motor-fem. Este diseño **propone añadir dos contratos** para las capas nuevas (§5.4 y §6.5): `C6` corpus golden / recuperación, `C7` operador. Crear/cambiar contrato = decisión de JM.

---

## 3. Parte A — Industrializar los plugins caseros

El objetivo de la parte A no es reescribir los plugins, sino **envolverlos en disciplina**: contrato, versión, tests, golden, CI/CD. El código artesanal sigue siendo del productor; lo que se añade es la **maquinaria que lo hace reproducible y certificable**.

### 3.1 Monorepo y empaquetado (N1.1)

Un repositorio único (propiedad de Estructurando) con un paquete por plugin/motor. Cada paquete declara su **contrato** y su **versión SemVer**; «publicar» = *tag + paquete interno versionado y firmado* (`iso19650-vX.Y.Z`, `motor-fem-vX.Y.Z`, …) con changelog y la versión de contrato que satisface. Layout propuesto (strawman):

```
ecosistema/                      (monorepo, productor)
├── nucleo/
│   ├── motor-fem/        · C5
│   └── motor-calculo/
├── plugins/
│   ├── iso19650-openbim/ · C1 (parser), genera llaves OIR/EIR
│   ├── estructuras-eurocodigos/
│   ├── instalaciones/    · C4 (red)
│   ├── obras-lineales/   · C4
│   ├── puentes/
│   ├── cte-documentos-basicos/
│   └── visor-ifc/
├── operador/             · capa 6  · C7   (NUEVO)
├── corpus/               · capa 7  · C6   (NUEVO)
└── contracts/            · C1..C7, versionados
```

El **consumidor** (2.0) no vive aquí: ancla estos paquetes en `versions.lock` (hoy plantilla con `0.0.0`; el primer tag real cierra N1.1).

### 3.2 Contratos como superficie estable

Cada contrato `Cn` especifica **qué entra, qué sale y con qué significado**, con independencia de la implementación. Es lo que permite que la IA y la QA operen contra una interfaz, no contra el código. Regla SemVer del gobierno: **MAJOR** = cambia un contrato (consumidores revalidan) · **MINOR** = añade compatible · **PATCH** = corrige sin cambiar interfaz. *Ejemplo:* si `narracion-a-ifc` cambia el esquema de salida IFC, salta MAJOR de `C1` y el operador (capa 6) y el corpus (capa 7) revalidan sus golden.

### 3.3 CI/CD + las tres capas de QA (reutiliza el gobierno)

Pipeline por cambio, **sin reinventar** lo ya cerrado en `GOBIERNO_QA_Y_VERSIONES.md`:

```
cambio → CI (build+lint+tests) → recálculo de golden por ESPEJO contra ORÁCULO
        → [capa 1 numérica]  [capa 2 normativa]  [capa 3 regresión]
        → ¿regresión? → GATE rojo (lo arregla el productor; NO se afloja tolerancia)
        → verde → CD publica versión SemVer (MAJOR si toca contrato)
        → 2.0 decide subir el pin → re-corre golden → adopta si verde
```

Las tres capas (numérica/oráculo, normativa, regresión) y la **jerarquía de oráculos** (analítico → 2.º código FEM → MMS; PyNite por defecto) son las del gobierno §B. La **separación de funciones** se mantiene: el agente que produce **no** es el que verifica (run de QA separado).

### 3.4 Definición de "plugin industrializado" (DoD por plugin)

Un plugin está en **N3** cuando: (a) vive en el monorepo con contrato declarado y SemVer; (b) tiene tests propios y ≥1 golden con oráculo+tolerancia en zona protegida; (c) pasa CI y está anclado en `versions.lock`. Sube a **N4** cuando sus salidas pasan las tres capas y la **certificación de dos llaves**. La zona protegida (`contratos-golden/`) y la regla "solo JM cambia golden/tolerancias vía PR" aplican desde N2.

### 3.5 Lo que NO se industrializa construyendo (Hilo 1)

Coherente con el anexo del Hilo 1: el **visor** se mantiene delgado sobre `visor-ifc`/web-ifc (no se persigue paridad con Solibri); **incidencias** se integran por **BCF** (no servidor propio); **campo** se integra (Dalux/PlanRadar) si un piloto lo exige. La industrialización aquí es *empaquetar e integrar*, no *construir commodity*.

---

## 4. Parte B — Capa 6: el operador IA nativo

La capa 6 es **el agente que opera sobre texto**: convierte lenguaje natural en IFC, lo audita, lo enruta al cálculo certificado y mueve incidencias por BCF — todo sin GUI ni binario. Es lo que el mercado no tiene (Hilo 1). No es un plugin más: es el **orquestador** que consume los plugins industrializados (parte A) por sus contratos y consulta el corpus (parte C).

### 4.1 El pipeline del operador

```
Lenguaje natural ──▶ [1 INTERPRETAR] ─── EIR/PIR provisional (el requisito)
                                          │
                          [2 RECUPERAR] ◀─┴──▶ corpus golden (capa 7, C6)
                                          │     devuelve criterio + caso análogo
                          [3 GENERAR] ────┴──▶ IFC4 texto (C1: narracion-a-ifc)
                                          │     con criterio de ingeniero, no geometría tonta
                          [4 AUDITAR] ────┴──▶ ifc-validate + bsDD + LOIN  (autocomprobación)
                                          │
                          [5 ENRUTAR] ────┴──▶ cálculo (C5 motor-fem / motores) ── ruta de firma
                                          │
                          [6 INCIDENCIAS] ┴──▶ BCF (coordinación/obra)
                                          │
                                          ▼
                              PROPUESTA, sin verificar/sin firmar
                              (hasta las dos llaves → capa 7 acuña golden)
```

Cada paso usa un plugin ya existente; la capa 6 es el **pegamento con criterio**, no funcionalidad nueva dispersa. El paso 2 (recuperar del corpus *antes* de generar) es lo que hace que el modelo nazca con criterio: es la diferencia entre `narracion-a-ifc` a secas (table stakes) y "modelo con criterio de ingeniero recuperado del corpus" (B1.1 §M1).

### 4.2 Propiedades de diseño no negociables

- **Opera sobre el sustrato abierto.** Entrada/salida en texto (IFC, BCF, Markdown). Nunca produce ni depende de binario propietario. Es la materialización de la premisa "IA operador nativo sobre formato abierto".
- **Determinismo trazable.** Misma entrada + mismas versiones ancladas (`versions.lock`) → misma salida. El operador **registra** qué versión de cada contrato usó (para reproducibilidad y QA).
- **Idempotencia y diff.** Reejecutar sobre un IFC existente produce un *diff* legible (texto), no un modelo opaco nuevo. Auditable por humano y por QA.
- **No firma.** El operador emite siempre **propuesta sin verificar**; la certificación es de la capa 7 + dos llaves. La IA nunca marca como válido lo no firmado (B1.2 §4, línea roja).

### 4.3 Separación productor/QA dentro de la capa 6

El operador (productor) y el agente de QA (verificador) son **runs separados con contexto y prompt distintos** (gobierno §B.1). El operador genera; la QA juzga contra su oráculo y devuelve Informe; **no se arreglan el uno al otro**. Esto ya lo soporta la arquitectura de subagentes del ecosistema (p. ej. `ingeniero-estructurista` produce, un run de QA verifica).

### 4.4 Handoff al cálculo certificado

El modelo abierto mantiene el *handoff sin fricción de formato* hacia los motores (B1.2 §3): el IFC texto con su dominio de análisis entra al `motor-fem`/`motor-calculo` por `C5`. El cálculo de firma vive bajo dos llaves igual que cualquier golden. La frontera no es funcional sino **de confianza**.

### 4.5 Contrato C7 (operador) — propuesto

`C7` especifica la interfaz del operador: **entrada** (texto NL + contexto de proyecto + EIR provisional) → **salida** (IFC4 + registro de procedencia: versiones de contrato usadas, casos golden recuperados, estado = `propuesta_sin_firmar`). Versionar el operador permite que la QA y el corpus sepan exactamente qué generó cada artefacto. *Propuesta a aprobar por JM.*

---

## 5. Parte C — Capa 7: el foso (corpus golden + recuperación por OIR)

Aquí está el grueso del valor y lo que **no existe ni en Estructurando**. Dos piezas: **F1.1** el átomo (qué se guarda) y **F1.2** la recuperación (cómo se recupera y reaplica). Sin F1.2, F1.1 es un cementerio de casos (B1.2 §2, caso frontera). Lo que sigue son **strawman concretos para que JM los apruebe** (cierran el DoD de F1.1 y F1.2 del reencuadre: "esquema escrito y aprobado por JM").

### 5.1 F1.1 — El átomo de caso golden

**Unidad de valor** (tesis §5): *una respuesta verificada a un requisito de información, en una fase*. No es "el proyecto Decopak HQ"; es la respuesta reusable. Esquema propuesto (extiende la ficha mínima de `contratos-golden/README.md` con la cascada ISO 19650 y la procedencia de firma):

```yaml
# golden-atom · v0 (strawman F1.1)
id:            DEC-EST-VOL-0001            # estable, único
titulo:        "Voladizo 4 m + planta diáfana → forjado ligero CLT/cassette + S355"
fase:          diseño                       # diseño|cálculo|obra|mantenimiento

requisito:                                  # la cascada ISO 19650 = las LLAVES
  OIR:         "minimizar coste y plazo en oficinas con plantas flexibles"   # objetivo (prioriza)
  AIR_PIR:     "entrega de estructura de oficina, planta libre"              # requisito de fase
  EIR:                                       # LLAVE TÉCNICA de recuperación (estructurada)
    tipo_elemento:   forjado_voladizo
    luz_voladizo_m:  4.0
    resistencia_fuego: R60
    restriccion:     planta_diafana
    material_pref:    [CLT, acero_S355]

respuesta:                                  # el conocimiento reusable
  criterio:    "voladizo grande → forjado ligero para reducir peso propio; acero S355 + optimización EC3"
  solucion:    {seccion: "...", canto_mm: 320, cuantia: "...", ...}
  artefactos:  [modelo/DEC-...-S1-v0.0.ifc, calculo/..., memoria/...]

procedencia:                                # lo que lo hace GOLDEN, no una nota
  oraculo:     analitico                     # analitico|pynite|mms|mano-JM (+fuente)
  tolerancia:  {flecha: "L/300", aprov: "≤1.0"}
  informe_QA:  qa/informes/QA-DEC-EST-VOL-0001.md   # 3 capas, limpio
  contrato:    {C1: v0, C5: v0}              # versiones ancladas que lo validan
  firma_JM:    {estado: pendiente, fecha: null}     # la 2.ª llave
  estado:      candidato                     # candidato|certificado  (certificado solo con 2 llaves)
```

Claves de diseño: **se indexa a dos niveles** (EIR/PIR = llave de búsqueda; OIR = objetivo que prioriza, tesis §5). El átomo **no es golden hasta `estado: certificado`** (golden verde + Informe QA limpio + `firma_JM`). Vive en zona protegida; solo JM cambia valores/tolerancias vía PR.

### 5.2 F1.2 — La capa de recuperación y reaplicación

El flywheel: ante un **EIR/PIR nuevo**, recuperar el átomo pertinente y reaplicarlo. Cuatro etapas (strawman):

```
EIR nuevo ─▶ [A INDEXAR]   normaliza el EIR a features tipadas (tipo_elemento, luz, R, restricción, material)
          ─▶ [B RECUPERAR] busca en el corpus por similitud de features  +  prioriza por OIR
                           → ranking de átomos candidatos (k mejores)
          ─▶ [C REAPLICAR] adapta el criterio/solución del átomo al parámetro nuevo
                           (p. ej. luz 4 m → 5 m: reescala, NO copia ciego)
          ─▶ [D RE-VERIFICAR] el resultado pasa otra vez por dos llaves antes de reusarse
                           → si verde+firma → nuevo átomo certificado (el corpus crece)
```

**Índice propuesto (doble, strawman):**
- **Estructurado (la llave técnica):** los campos `EIR.*` como índice consultable por igualdad/rango (tipo_elemento exacto; luz, R por rango). Determinista y auditable — es la columna vertebral.
- **Semántico (apoyo):** *embedding* del `titulo`+`criterio` para casos donde la llave estructurada no capte analogía ("planta diáfana" ≈ "planta libre"). Solo **desempata/sugiere**; nunca decide sin la llave estructurada.
- **OIR como prioridad:** entre candidatos con EIR parecido, el OIR ordena cuál es más pertinente al objetivo del proyecto (no es llave de búsqueda, es ranking — tesis §5).

**Regla anti-cementerio (B1.2):** un caso no entra al corpus si no trae sus llaves `EIR`+`OIR` rellenas. "Guardar para indexar luego" está prohibido por diseño.

### 5.3 La acuñación de dos llaves (M3) — la fábrica del foso

La capa 7 **no acuña sola**. Un átomo pasa de `candidato` a `certificado` solo con: (a) suite golden verde, (b) Informe de QA limpio (3 capas), (c) **firma de JM** registrada en `firma_JM`. Cada certificación "mina" un activo defendible (tesis §7). El operador (capa 6) produce candidatos; la QA juzga; **JM firma**. La IA nunca firma.

### 5.4 Contrato C6 (corpus) — propuesto

`C6` especifica la interfaz del corpus: `guardar(átomo_candidato)`, `recuperar(EIR) → ranking`, `reaplicar(átomo, parámetros) → propuesta`, `certificar(átomo, informe_QA, firma_JM)`. Versionado SemVer: cambiar el esquema del átomo o la llave de recuperación = MAJOR (revalida todo el corpus). *Propuesta a aprobar por JM.*

### 5.5 La métrica que prueba que el foso gira

El KPI estrella del reencuadre: **coste marginal del caso N+1 vs N**. Operativamente, la capa 7 instrumenta: por cada caso de una familia (mismo `EIR.tipo_elemento`), registrar horas/retrabajo. El **segundo voladizo debe costar medible­mente menos** que Decopak HQ porque recuperó y reaplicó su átomo. Si N+1 **no** baja → el flywheel no gira → es archivo, no foso (señal de alarma de diseño).

---

## 6. Cómo encaja todo con el gobierno

Las tres capas comparten una sola disciplina, la del gobierno ya cerrado:

| Mecanismo del gobierno | Capa A (plugins) | Capa 6 (operador) | Capa 7 (corpus) |
|---|---|---|---|
| Contratos SemVer | C1–C5 | C7 (nuevo) | C6 (nuevo) |
| Versions.lock (consumidor ancla) | sí | registra versiones usadas | valida átomo contra versiones |
| 3 capas de QA | tests+golden | QA de la salida | re-verificación al reaplicar |
| Dos llaves (firma JM) | en ruta de cálculo | nunca firma | `firma_JM` acuña el átomo |
| Zona protegida / PR de JM | golden+tolerancias | — | átomos+llaves |
| Separación productor/QA | runs separados | opera, no verifica | candidato→certificado |

**Una sola fuente de verdad:** el corpus golden es propiedad de QA/JM (zona protegida), igual que los contratos y los golden de cálculo. El operador y los plugins lo *consumen*; solo el proceso de dos llaves lo *escribe*.

---

## 7. Plan por fases y orden de prioridad

> **Orden de inversión = el del reencuadre, no el de exposición.** Lo defendible antes que lo copiable. La trampa a evitar: pulir el operador NL→IFC (vistoso, copiable) y descuidar F1.1/F1.2 (aburrido, defendible).

**Fase 1 — cerrar los rieles (Sprint 0).** N1.1 (monorepo + primer tag + `versions.lock` real); aprobar los strawman **F1.1** (§5.1) y **F1.2** (§5.2) → cierra su DoD. Diseño, no implementación todavía.

**Fase 2 — el foso mínimo viable (capa 7 primero).** Implementar el átomo y la recuperación estructurada (la semántica puede esperar). Acuñar **1 átomo certificado de Decopak HQ** por dos llaves (B2.1). Es la prueba de que la unidad + recuperación + acuñación funcionan.

**Fase 3 — el operador sobre el foso (capa 6).** Industrializar `narracion-a-ifc` a N3–N4 y enchufar el paso 2 (recuperar antes de generar). Que el modelo nazca con criterio recuperado, no geometría tonta.

**Fase 4 — industrializar el resto a N3–N4** según ruta de firma (motores y plugins de cálculo a N4–N5; visor/CDE/incidencias delgados e integrados).

**Fase 5 — prueba del flywheel (M2).** Reaplicar el átomo de Decopak HQ a un **segundo caso** de la misma familia y **medir si N+1 cuesta menos**. Primera evidencia del foso girando, y por alguien que no es JM (→ producto, no conversación brillante).

---

## 8. Riesgos técnicos y decisiones abiertas para JM

**Riesgos técnicos**
- **R1 · Fidelidad del *roundtrip* IFC** (capa 6). Generar/editar IFC con geometría y Psets correctos y re-exportables sin pérdida es el corazón duro. *Mitigación:* `ifc-validate` en el paso 4 + dos llaves; Decopak HQ como prueba.
- **R2 · Esquema del EIR demasiado rígido o demasiado laxo** (capa 7). Si las features son pocas, no recupera; si son muchas, nada casa. *Mitigación:* empezar con el set mínimo del §5.1 y dejar el esquema versionado (C6) para evolucionarlo con casos reales.
- **R3 · Reaplicación que copia en vez de adaptar.** Reescalar un criterio fuera de su rango de validez produce un resultado peligroso. *Mitigación:* la etapa D (re-verificar por dos llaves) es obligatoria; un átomo recuperado nunca se reusa sin re-verificar.
- **R4 · Sobre-ingeniería del índice semántico.** Es apoyo, no columna. *Mitigación:* la llave estructurada decide; la semántica solo sugiere.
- **R5 · La trampa del reencuadre** (el de gobierno, no técnico). *Mitigación:* el orden de §7 y la métrica N+1.

**Decisiones abiertas para JM** (la IA propone; JM cierra)
1. Ratificar la **escalera N0→N5** del §1 (o ajustarla a la del `Backlog_Fase0_operativo.xlsx`).
2. Aprobar los **strawman F1.1 y F1.2** (§5.1–§5.2) o pedir cambios — cierra el DoD del Sprint 0.
3. Aceptar crear los **contratos C6 (corpus) y C7 (operador)** o mantener las capas nuevas sin contrato propio por ahora.
4. Confirmar el **orden de prioridad** del §7 (foso antes que pulido del operador).
5. Elegir, cuando toque, **Speckle como capa de datos** o Git+web-ifc puro (decisión heredada del Hilo 1).

---

## 9. Definición de "Hilo 2 terminado"

- [ ] Escalera N0→N5 (§1) revisada por JM.
- [ ] Plan de industrialización de plugins (parte A) revisado: monorepo, contratos, CI/CD, DoD por plugin.
- [ ] Diseño de la **capa 6** (operador, §4) y del **contrato C7** revisado.
- [ ] **Strawman F1.1 (átomo, §5.1) y F1.2 (recuperación, §5.2) aprobados por JM** → cierra el DoD de F1.1/F1.2 del Sprint 0 reencuadrado.
- [ ] Contratos **C6/C7** aceptados o aplazados (decisión registrada).
- [ ] Orden de prioridad (§7) confirmado.
- [ ] Aprobación de JM registrada (la IA prepara; JM firma).

---

*Procedencia: Hilo 2, diseño técnico preparado por la IA (PM / Ing. BIM-IFC) de Estructurando 2.0 · 2026-06-24 · propuesta para revisión, ajuste y firma de JM. Strawman (F1.1, F1.2, C6, C7, N0–N5) sujetos a aprobación. No implementa ni firma.*

