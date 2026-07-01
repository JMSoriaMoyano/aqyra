# C8 — Contrato de interfaz: Nuestro entorno ↔ CDE

**Tipo:** contrato de interfaz (SemVer) · **zona protegida** (`contratos-golden/contratos/`)
**Versión:** v0.1.0 (DRAFT, pre-1.0 → interfaz aún inestable) · **Fecha:** 2026-06-23
**Estado:** PROPUESTA — pendiente de (a) alineación con el equipo del CDE y (b) firma de JM
**Co-propiedad:** equipo Estructurando 2.0 / proyecto Entorno · equipo del CDE (producto en paralelo)

> **Nota de numeración (reconciliación 2026-06-23):** este contrato se redactó primero como «C6», pero el esquema de contratos del ecosistema ya reserva **C6 = corpus golden / recuperación por OIR** y **C7 = operador IA** (ver `entorno/integracion/versions.lock`). Para evitar colisión, el intercambio con el CDE pasa a **C8**. Esquema vigente: C1 (parser/IFC), C2 (datos), C3 *(reservado)*, C4 (red), C5 (motor-fem), C6 (corpus), C7 (operador IA), **C8 (intercambio CDE)**. **Reconciliación 2026-06-27 (firmada por JM):** las convenciones de núcleo heredadas pasan a la familia **CN-*** (CN-1 memoria, CN-2 documentación), fuera del espacio C.

> Define **qué cruza la frontera** entre nuestro entorno y el CDE, **en qué formato**, **en qué dirección** y **con qué versión**. Sigue el modelo productor/consumidor de `GOBIERNO_QA_Y_VERSIONES.md` (§A). Preparado por la IA; la responsabilidad y la firma son de JM.

---

## 1. Propósito y alcance

Establecer el intercambio **bidireccional** entre nuestro entorno abierto (basado en IFC) y el CDE que desarrolla el equipo en paralelo, de modo que:

- los entregables de **misión 1** (pre/post de cálculo: IFC con resultados escritos de vuelta) y de **misión 2** (QA del IFC: incidencias) **se publiquen** en el CDE, y
- el CDE **sirva** a nuestro entorno los modelos, los requisitos de información (EIR/PIR) y el contexto de estados/incidencias.

**Principio rector:** la frontera se apoya en **estándares openBIM** (IFC, BCF, IDS) y en el modelo de estados **ISO 19650**; la API es **fina**, y por debajo viajan artefactos estándar. Mismo lema del proyecto: *formato abierto, no binario*, aplicado a la integración.

## 2. Principios de diseño (no negociables)

1. **Contrato abstracto, no acoplamiento.** Su CDE es *una* implementación detrás de un **adaptador**; no *la* dependencia. Si su API cambia, lo absorbe el adaptador (regla §A.3/A.4 del Gobierno).
2. **Estándares por debajo.** Modelo en **IFC**; incidencias en **BCF**; requisitos en **IDS**; estados y metadatos en **ISO 19650**. Solo se inventa lo imprescindible.
3. **SemVer.** `MAJOR.MINOR.PATCH`; **MAJOR** = cambio incompatible de la interfaz. El consumidor **ancla** la versión en `versions.lock`; subir es deliberado (re-correr golden → adoptar si verde).
4. **Golden vN valida C8 vN** (decisión 1 del Gobierno).
5. **Dos llaves para publicar resultados certificados.** Un entregable solo transiciona a estado *Publicado/certificado* con golden verde + informe de QA limpio + **firma de JM**. La IA nunca certifica.

## 3. Partes y direcciones

| Dirección | Productor | Consumidor |
|---|---|---|
| **Entorno → CDE** | Nuestro entorno | El CDE |
| **CDE → Entorno** | El CDE | Nuestro entorno |

## 4. Objetos que cruzan la frontera

| # | Objeto | Dirección | Formato / estándar | Semántica |
|---|--------|-----------|--------------------|-----------|
| O1 | **Modelo de información** | CDE → Entorno | **IFC** (IFC4; IFC4.3 si infra) | El CDE entrega el modelo a procesar (cálculo/QA). |
| O2 | **Modelo con write-back** | Entorno → CDE | **IFC** (Psets de resultado) | Devolvemos el IFC con resultados de cálculo/comprobaciones escritos en Psets. |
| O3 | **Incidencias / QA** | bidireccional | **BCF** (2.1 / 3.0, vía BCF-API) | Misión 2 publica issues de QA como BCF; recibimos su estado/resolución. |
| O4 | **Requisitos validables** | CDE → Entorno | **IDS** | Requisitos de información comprobables sobre el modelo. |
| O5 | **Metadatos de contenedor y estado** | bidireccional | **ISO 19650** (código de estado/suitability, revisión, clasificación) | Estado del contenedor (WIP→Compartido→Publicado→Archivado), revisión, idoneidad. |
| O6 | **Requisitos de información** | CDE → Entorno | Estructurado (EIR/PIR; JSON/doc a definir) | Qué debe entregar el proyecto; alimenta a los copilotos. |
| O7 | **Entregables documentales** | Entorno → CDE | Markdown / PDF | Memoria de cálculo, informe de QA (acompañan al IFC). |

> **Fuera de la frontera:** los candidatos a golden y la evidencia interna de QA viven en `contratos-golden/` y `qa/`, **no** se publican al CDE salvo decisión expresa.

## 5. Superficie de API (abstracta)

Verbos abstractos; el adaptador los mapea a la API concreta del CDE.

| Operación | Dirección | Objeto | Nota |
|---|---|---|---|
| `obtener_modelo(id, rev)` | CDE → Entorno | O1 | Descarga el IFC de un contenedor/revisión. |
| `publicar_modelo(id, ifc, meta)` | Entorno → CDE | O2, O5 | Sube IFC con write-back + metadatos; **no** publica como certificado por sí solo (ver §6). |
| `listar_incidencias(filtro)` | CDE → Entorno | O3 | Lee issues (BCF). |
| `publicar_incidencia(bcf)` / `actualizar_incidencia(id)` | Entorno → CDE | O3 | Empuja/actualiza issues de QA. |
| `leer_requisitos(proyecto)` | CDE → Entorno | O4, O6 | Obtiene IDS y EIR/PIR. |
| `leer_estado(id)` / `proponer_transicion(id, estado)` | bidireccional | O5 | Lee o **propone** cambio de estado (la transición a Publicado la gobierna §6). |
| `adjuntar_documento(id, doc)` | Entorno → CDE | O7 | Sube memoria/informe. |

**Transversal:** autenticación (mecanismo a confirmar con el equipo del CDE), **mínimo privilegio**, **idempotencia** en las escrituras y **traza de auditoría** (exigida por ISO 19650).

## 6. Máquina de estados y candado de gobierno

- Las transiciones siguen ISO 19650: **WIP → Compartido → Publicado → Archivado**.
- **Candado:** la transición a **Publicado/certificado** de un resultado de cálculo **requiere las dos llaves** (golden verde + informe de QA limpio + **firma de JM**). Nuestro entorno solo puede `proponer_transicion`; la publicación certificada la ratifica el proceso de gobierno, no la API.
- No se publica sobre un contenedor ya Publicado sin nueva revisión (sin sobrescritura silenciosa).

## 7. Versionado y compatibilidad

- C8 se versiona con SemVer; el consumidor ancla la versión exacta en `versions.lock` (entrada `cde-interfaz` + la versión del producto CDE cuando se ratifique).
- **Verde** en la suite golden de interfaz → se adopta. **Rojo** → regresión (la corrige el productor) o cambio de contrato (**MAJOR**: se adapta el adaptador y se revalida).
- Al ser DRAFT pre-1.0 (v0.x), se admiten cambios incompatibles entre minors mientras se estabiliza con el equipo del CDE.

## 8. Puntos abiertos (a cerrar con el equipo del CDE)

1. **Versión de IFC** soportada por el CDE (IFC4 vs IFC4.3) y perfil/MVD.
2. **Versión de BCF** (2.1 vs 3.0) y si exponen **BCF-API** (REST) o solo BCFzip.
3. **Soporte de IDS** para requisitos validables.
4. **Mecanismo de autenticación** y modelo de permisos (quién puede transicionar estados).
5. **Esquema de O6** (EIR/PIR): formato estructurado concreto (JSON Schema a acordar).
6. **Códigos de estado/idoneidad** exactos que usa su CDE (mapeo a ISO 19650 S0–S7).
7. **Hosting/despliegue** (cloud / on-prem) e implicaciones de la auditoría.

## 9. Fuera de alcance

- Construir un CDE (lo hace el equipo en paralelo).
- La lógica interna del CDE (permisos, almacenamiento) más allá de lo que cruza la frontera.
- La certificación de resultados (vive en el gobierno de dos llaves, no en la API).

---

### Firma

| Rol | Nombre | Estado |
|---|---|---|
| Prepara (IA) | equipo IA Estructurando 2.0 | Entregado 2026-06-23 |
| Alinea (CDE) | equipo del CDE | ☐ Pendiente |
| Aprueba/firma | **JM** | ☐ Pendiente |
