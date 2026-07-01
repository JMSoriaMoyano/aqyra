# C7 — Contrato de interfaz: encargo ↔ operador IA

**Tipo:** contrato de interfaz (SemVer) · **zona protegida** (`contratos-golden/contratos/`)
**Versión:** v0.1.0 (DRAFT, pre-1.0 → interfaz aún inestable) · **Fecha:** 2026-06-26
**Estado:** PROPUESTA — borrador IA, pendiente de firma de JM
**Satisfecho por:** el **operador IA** (orquestador de entregables del entorno Aqyra) · **Consumen:** el producto Aqyra y, a través de él, el usuario (despacho / autónomo)

> Define **qué entra y qué sale del operador IA**: el componente que recibe un **encargo** (petición de un entregable + el modelo abierto + el alcance), **orquesta los motores** (C1 parser/IFC, C4 red, C5 motor-fem) y las **skills de normativa**, y **produce el entregable como propuesta revisable**, con veredicto, trazabilidad y fundamentación. Preparado por la IA; la responsabilidad y la firma son de JM.

> **Numeración:** esquema vigente del ecosistema — C1 (parser/IFC) · C4 (red) · C5 (motor-fem) · C6 (corpus golden) · **C7 (operador IA)** · C8 (intercambio CDE). Ver `C8_intercambio_CDE.md`.

> **La diferencia capital con C5.** El motor-fem (C5) es **determinista**: misma entrada + misma versión ⇒ misma salida dentro de tolerancia. El operador IA **no lo es**. Por eso C7 **no** promete reproducibilidad numérica; la sustituye por cuatro garantías: **(1) propuesta nunca certificación · (2) trazabilidad total · (3) fundamentación obligatoria (cero invención) · (4) conformidad estructural** verificable contra una golden de tipo distinto (completitud + grounding, no número).

---

## 1. Propósito y alcance

Establecer la frontera entre el **encargo** —la petición de un entregable de proyecto sobre un modelo abierto— y el **operador IA**, que lo resuelve orquestando los motores y las skills, de modo que:

- el operador reciba un **encargo bien definido** (tipo de entregable, modelo IFC, uso del edificio, alcance/fase, requisitos y datos confirmados), y
- devuelva un **entregable propuesto** (memoria / justificación / validación) con **veredicto** por exigencia, **trazabilidad** completa y **mapa de fundamentación**, en formato abierto y marcado como `proposal` (modelo de dos llaves).

**Alcance de v0 (lo que ejercita la golden de C7):** el operador de **documentación de cumplimiento**, concretamente la **memoria CTE + justificación urbanística** — el primer entregable firmable del roadmap (cuña autónomo), por ser máxima disposición a pagar y menor coste de construcción (usa las skills de CTE/normativa y C1; no requiere C5). Otras salidas (memoria de cálculo vía C5, predimensionado, presupuesto, validación municipal) son **ganchos para vN**, no parte de v0.

| Entregable | Motores/skills que orquesta | Golden v0 |
|---|---|---|
| **Memoria CTE** (DB-SI/SUA/HS/HR/HE/SE aplicables al uso) | C1 (parser) + skills `cte-documentos-basicos` | **GOL-CTE-01** *(a sembrar)* |
| **Justificación urbanística** | C1 + planeamiento aplicable (E3) | **GOL-URB-01** *(a sembrar)* |
| *(gancho vN)* Memoria de cálculo | C7 invoca **C5** y empaqueta su O1–O4 | — |
| *(gancho vN)* Predim / validación municipal | C5/C4 (predim) · C1+IDS (validación) | — |

## 2. Principios de diseño (no negociables)

1. **Contrato abstracto, no acoplamiento.** El consumidor depende de *esta interfaz*, no del modelo de IA ni de la arquitectura de agentes que haya detrás. Cambiar el modelo o los agentes por dentro **no** es cambio de contrato mientras la frontera y las garantías se respeten.
2. **Propuesta, no verdad.** Toda salida nace marcada `proposal`. La IA **produce y propone; nunca certifica.** La certificación exige la **segunda llave** (firma de JM), gobernada fuera de la API (§6).
3. **No determinista ⇒ trazable y fundamentado.** Sustituye al determinismo de C5. La "reproducibilidad" de C7 es **auditabilidad**: cada salida lleva su traza completa y su mapa de fundamentación, de modo que un humano pueda verificar *cómo* y *de dónde* salió cada afirmación.
4. **Fundamentación obligatoria — cero invención.** Ninguna afirmación sin fuente verificable (artículo de normativa vigente, resultado de C5/C4, propiedad del modelo). Lo que no tiene fuente **se marca `[confirmar]`, no se rellena.** Inventar un dato o citar una norma inexistente es un fallo de contrato.
5. **Humano en el bucle.** El operador **pide confirmación** de las hipótesis críticas (idealización, NDP, zona climática, ocupación, datos faltantes) antes de producir; nunca las asume en silencio.
6. **Formato abierto.** Entregable, veredicto, traza y grounding viajan como **texto diff-able** (Markdown / JSON); nada propietario en la frontera.
7. **SemVer.** `MAJOR.MINOR.PATCH`; **MAJOR** = cambio incompatible de la interfaz (campos del encargo/entregable, semántica del veredicto, esquema del grounding). El consumidor **ancla** la versión en `versions.lock`; subir es deliberado (re-correr golden → adoptar si verde). **Golden vN valida C7 vN.**

## 3. Partes y direcciones

| Dirección | Productor | Consumidor |
|---|---|---|
| **Encargo → operador** | El producto / usuario | El operador IA |
| **Operador → entregable** | El operador IA | El producto / usuario (y, opcional, el CDE vía C8) |

## 4. Objetos que cruzan la frontera

**Entrada (encargo → operador):**

| # | Objeto | Formato / estándar | Semántica |
|---|--------|--------------------|-----------|
| E1 | **Encargo** | JSON | tipo de entregable, uso del edificio, alcance/fase (Básico/Ejecución), banda de PEM |
| E2 | **Modelo abierto** | IFC (vía **C1**) | geometría, espacios, propiedades, clasificación |
| E3 | **Requisitos y contexto** | JSON / IDS / EIR-PIR (vía **C8** O4/O6) | normativa aplicable según uso, planeamiento urbanístico, parámetros, NDP |
| E4 | **Hipótesis y datos confirmados** | JSON | los que fija el humano (zona climática, ocupación, sectores de incendio…) |

**Salida (operador → entregable):**

| # | Objeto | Formato / estándar | Semántica |
|---|--------|--------------------|-----------|
| S1 | **Entregable propuesto** | Markdown / PDF, marcado `proposal` | la memoria / justificación redactada |
| S2 | **Veredicto por exigencia** | JSON / Markdown | CUMPLE / NO CUMPLE / CUMPLE CON OBSERVACIONES, con los huecos `[confirmar]` |
| S3 | **Trazabilidad** | JSON / Markdown | skills y motores usados + sus versiones, hipótesis asumidas, versión de C7 |
| S4 | **Mapa de fundamentación (grounding)** | JSON | cada afirmación ↔ su fuente (artículo, resultado C5/C4, propiedad del modelo) |
| S5 | **Write-back** *(opcional)* | IFC (vía **C1**, Psets) / doc al CDE (**C8** O7) | resultados/propiedades escritos al modelo o publicados |

## 5. Superficie de API (abstracta)

Verbos abstractos; el adaptador los mapea a la implementación concreta (agentes/skills).

| Operación | Dirección | Objeto | Nota |
|---|---|---|---|
| `solicitar_entregable(encargo, modelo, requisitos)` | encargo → operador | E1–E3 → S1–S4 | produce el borrador propuesto con su traza y grounding |
| `listar_huecos(entregable_id)` | operador → | S2 | devuelve los `[confirmar]` que faltan por fijar |
| `confirmar_hipotesis(entregable_id, valores)` | encargo → operador | E4 | el humano fija datos/hipótesis marcados `[confirmar]`; regenera lo afectado |
| `revisar(entregable_id)` | operador → | S3, S4 | entrega traza + mapa de fundamentación para auditoría |
| `proponer_certificacion(entregable_id)` | operador → | — | **propone** pasar a certificado; la 2ª llave la gobierna §6, no la API |

**Transversal:** **mínimo privilegio**, **traza de auditoría** de cada generación (qué versión de qué skill/motor, qué fuentes), e **idempotencia** del write-back.

## 6. Máquina de estados y candado de gobierno

- Estados del entregable: **BORRADOR** (`proposal`) → **REVISADO** (un humano validó hipótesis y grounding) → **CERTIFICADO** (dos llaves) → **PUBLICADO** (al CDE, vía C8).
- **Candado de dos llaves** (mismo principio que C5/C8 §6): la transición a **CERTIFICADO** exige **golden verde + revisión de grounding limpia + firma de JM**. El operador IA solo produce **BORRADOR** y puede `proponer_certificacion`; **nunca certifica**.
- Ningún hueco `[confirmar]` puede quedar abierto en un entregable que se propone a certificación: o se confirma (E4) o se declara explícitamente como no aplicable.

## 7. Oráculo y conformidad (atados a la golden)

El oráculo de C7 **no es numérico** (a diferencia de C5). Es de **conformidad estructural + fundamentación**. Una golden de C7 fija, para un proyecto de referencia, cuatro comprobaciones:

1. **Cobertura** — el entregable cubre **todas** las exigencias aplicables al uso (CTE: DB-SI/SUA/HS/HR/HE/SE + normativa concurrente; urbanística: todos los parámetros del planeamiento). Falta una exigencia aplicable ⇒ rojo.
2. **Citación** — cada justificación cita un **artículo real, vigente y aplicable** al caso. Cita inexistente, derogada o inaplicable ⇒ rojo.
3. **Veredicto** — el CUMPLE / NO CUMPLE / observaciones por exigencia **coincide** con el checklist de referencia.
4. **Grounding** — **0 afirmaciones sin fuente**; los huecos correctamente marcados `[confirmar]`. Una afirmación inventada ⇒ rojo (el fallo más grave).

**Procedencia del oráculo:** checklist de cumplimiento de referencia **revisado y firmado por JM** (mano-JM), apoyado en la skill `cte-documentos-basicos:checklist-cumplimiento`. Un fallo de conformidad **no** se arregla relajando el checklist ni editando el esperado — **solo corrigiendo el operador** (mismo espíritu que C5).

> **Golden de v0 a sembrar:** `GOL-CTE-01` (memoria CTE de un proyecto de referencia — p. ej. Decopak) y `GOL-URB-01` (justificación urbanística). Cada una con su checklist firmado como oráculo. Hasta sembrarlas y ratificarlas, **C7 v0 no es certificable** (Llave 1 incompleta).

## 8. Versionado y compatibilidad

- C7 se versiona con SemVer; el consumidor ancla la versión exacta en `versions.lock`.
- **Verde** en la golden de conformidad → se adopta. **Rojo** → regresión (la corrige el operador) o cambio de contrato (**MAJOR**: se adapta el adaptador y se revalida).
- Al ser DRAFT pre-1.0 (v0.x), se admiten cambios incompatibles entre minors mientras se estabiliza la frontera.

## 9. Puntos abiertos (a cerrar)

1. **Catálogo de entregables de v0** — ¿solo memoria CTE + urbanística, o se incluye ya validación municipal (gancho del Mostrador B)? *Propuesta: solo CTE + urbanística; lo demás a vN.*
2. **Esquema JSON** del encargo (E1), del veredicto (S2) y del mapa de grounding (S4) — `schemas/C7_*.schema.json`, en paralelo a los de C5.
3. **Handoff C7 → C5/C4** cuando el entregable incluye cálculo: cómo invoca el operador al motor y empaqueta su O1–O4 en la memoria (define la composición de contratos).
4. **Fuente de la normativa urbanística** (planeamiento municipal): ¿de dónde se carga el articulado aplicable? (IDS del CDE / carga manual / base de datos del despacho).
5. **Política de citación verificable** — ¿se exige cita literal con referencia fechada de cada artículo? ¿qué versión de cada DB del CTE se ancla (igual que los NDP de C5)?
6. **Sembrar y ratificar `GOL-CTE-01` / `GOL-URB-01`** con su checklist firmado — sin esto, no hay Llave 1.

## 10. Fuera de alcance

- **El cálculo numérico** (vive en C5) y **la resolución de redes** (C4): C7 los **orquesta**, no los reimplementa.
- **La certificación** de los entregables: vive en el gobierno de dos llaves, no en la API.
- **El modelo de IA concreto y la implementación de agentes/skills:** quedan detrás del adaptador.
- **El cobro / la licencia** (capa comercial) y **el tope de uso justo** (guardarraíl operativo): no son parte de esta interfaz.

---

### Firma

| Rol | Nombre | Estado |
|---|---|---|
| Prepara (IA) | equipo IA Estructurando 2.0 / Aqyra | Entregado 2026-06-26 |
| Aprueba/firma | **JM** | ☐ Pendiente |
