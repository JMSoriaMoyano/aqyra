# C2 — Contrato de datos: dato crudo del cliente ↔ conocimiento aprendido de Aqyra

**Tipo:** contrato de interfaz / gobierno de datos (SemVer) · **zona protegida** (`contratos-golden/contratos/`)
**Versión:** v0.1.0 (DRAFT, pre-1.0 → interfaz aún inestable) · **Fecha:** 2026-06-26
**Estado:** PROPUESTA — borrador IA, pendiente de firma de JM
**Satisfecho por:** el entorno Aqyra (custodio del dato y del aprendizaje) · **Consumen:** el cliente (dueño del dato crudo) y el operador IA (**C7**, que extrae y consume conocimiento)

> Define **la frontera entre el dato crudo del cliente y el conocimiento que Aqyra puede aprender y retener de él**: qué es de quién, qué puede cruzar de "crudo" a "aprendido", con qué de-identificación, bajo qué consentimiento y con qué derecho de borrado. Es el contrato que sostiene el **foso-conocimiento** sin romper la promesa de apertura. Preparado por la IA; la responsabilidad y la firma son de JM.

> **Numeración:** ocupa **C2** (hueco libre, foundational: C1 mete el dato → C2 gobierna qué se aprende de él). **C3 queda reservado.** Esquema vigente: C1 (parser/IFC) · **C2 (datos)** · C3 *(reservado)* · C4 (red) · C5 (motor-fem) · C6 (corpus golden) · C7 (operador IA) · C8 (intercambio CDE). **Reconciliación 2026-06-27 (firmada por JM):** las convenciones de núcleo heredadas (memoria, documentación) salen del espacio C a la familia **CN-*** (CN-1 memoria, CN-2 documentación), de modo que C3 sigue libre y no hay colisión de C2.

> **La distinción quirúrgica (corazón del contrato).** El **dato crudo** es del **cliente** y es **abierto** —diff-able, exportable, nunca cautivo—. Los **patrones/criterios aprendidos**, una vez **de-identificados**, son de **Aqyra**: ese es el moat. El foso es el **modelo aprendido, no el dato en bruto.** Y la de-identificación no es un adorno: es **lo que hace el foso legalmente sostenible**, porque un patrón que no conserva ninguna traza identificable **sobrevive a un borrado** del dato crudo sin tener que "des-aprenderse".

---

## 1. Propósito y alcance

Establecer la frontera, dentro del entorno Aqyra, entre:

- el **dato crudo** que el cliente aporta o genera (su proyecto: IFC, geometría, propiedades, cantidades, documentos, resultados firmados), del que el cliente es **dueño soberano**, y
- el **conocimiento aprendido** (patrones, criterios, heurísticas, distribuciones) que Aqyra extrae al procesarlo y **retiene de-identificado** para mejorar la asistencia en proyectos futuros (el círculo virtuoso, transversal y capitalizado).

de modo que el aprendizaje **nunca** se haga a costa de la soberanía ni de la apertura del dato del cliente, y que lo retenido **no pueda reconducirse** a un cliente, un proyecto, ni a la cadena de responsabilidad civil de una firma.

**Alcance de v0:** la frontera de aprendizaje sobre los entregables del operador IA (**C7**) y de los motores (C5/C4): qué se puede extraer, qué se debe de-identificar y qué está prohibido retener. La **monetización** del consentimiento (descuento por opt-in, etc.) y la implementación del almacén quedan fuera (capa comercial / ingeniería).

## 2. Principios de diseño (no negociables)

1. **Soberanía del dato crudo.** El dato crudo es del cliente: **exportable** en formato abierto en todo momento, **portable** (no cautivo de Aqyra), y **borrable** a petición. Aqyra es **custodio**, no dueño.
2. **El moat es el aprendido, no el crudo.** Aqyra capitaliza **patrones de-identificados**, nunca el dato bruto. Vender apertura y capitalizar el bruto a la vez sería la contradicción que este contrato existe para impedir.
3. **De-identificación robusta y verificable.** Un patrón solo cruza a "aprendido/retenible" si **no permite reconstruir** ni el cliente, ni el proyecto, ni su geometría/cantidades identificables, ni la cadena de firma/responsabilidad. La robustez se **prueba** (golden anti-re-identificación, §7), no se asume.
4. **Prohibido reutilizar la firma y su responsabilidad civil.** Un cálculo lleva la firma de un colegiado y responsabilidad civil. **Nada** de lo retenido puede atar un patrón a un entregable firmado concreto ni a su autor. La firma es del que la pone, nunca insumo de entrenamiento.
5. **Consentimiento explícito (opt-in, soberanía primero).** Por defecto **no se capitaliza** nada del proyecto de un cliente sin su **consentimiento explícito**. El cliente conserva siempre el dato, su exportación y su borrado, consienta o no. *(El modelo de incentivo —descuento por consentir, opt-in vs opt-out— es decisión comercial, §9.)*
6. **Derecho al olvido sin des-aprender.** El borrado del dato crudo es inmediato y total. Como el patrón retenido **no conserva traza identificable** (principio 3), el borrado **no obliga** a des-aprender — y si un patrón fuese reconducible a lo borrado, **no debió retenerse**.
7. **Trazabilidad y dos llaves.** Toda retención registra su procedencia y su prueba de de-identificación. La IA **propone** retener; la certificación de "este patrón es capitalizable" exige la **segunda llave** (firma de JM). La IA nunca certifica que algo es seguro de retener.
8. **Formato abierto.** El dato y los registros de consentimiento/procedencia viajan como **texto diff-able**; nada propietario en la frontera del dato del cliente.

## 3. Partes y direcciones

| Dirección | Productor | Consumidor |
|---|---|---|
| **Dato crudo → entorno** | El cliente | Aqyra (custodio) — lo procesa, no lo posee |
| **Conocimiento de-identificado → almacén** | Aqyra (vía operador IA, C7) | Aqyra (lo capitaliza para proyectos futuros) |
| **Export / borrado** | Aqyra (custodio) | El cliente (ejerce su soberanía) |

## 4. Objetos que cruzan la frontera

| # | Objeto | Lado | Régimen |
|---|--------|------|---------|
| D1 | **Dato crudo del proyecto** | del cliente | IFC, geometría, propiedades, cantidades, documentos, resultados firmados. **Soberano, abierto, borrable.** Nunca insumo de entrenamiento sin D4. |
| D2 | **Candidato a patrón** | en la frontera | abstracción extraída al procesar (criterio, heurística, distribución). **Aún no retenible**: pasa por la puerta de de-identificación (§6). |
| D3 | **Conocimiento aprendido de-identificado** | de Aqyra | el patrón ya despojado de toda traza identificable. **Capitalizable**, el moat. |
| D4 | **Registro de consentimiento** | del cliente | opt-in explícito (alcance, fecha, revocable). Sin él, D2 **no** cruza a D3. |
| D5 | **Prueba de de-identificación** | de Aqyra | evidencia de que D3 supera el test anti-re-identificación (§7), atada a la golden. |

**Lista de lo PROHIBIDO retener** (si aparece en D2, no cruza): identidad del cliente o del autor/colegiado; identificadores del proyecto, emplazamiento o catastro; geometría o cantidades que reconstruyan el proyecto; cualquier vínculo a una firma o a su responsabilidad civil; datos personales (RGPD).

## 5. Superficie de API (abstracta)

| Operación | Dirección | Objeto | Nota |
|---|---|---|---|
| `otorgar_consentimiento(cliente, alcance)` / `revocar_consentimiento(id)` | cliente → | D4 | opt-in explícito y revocable; revocar corta futuras retenciones |
| `exportar_datos(proyecto)` | → cliente | D1 | dato crudo en formato abierto, en cualquier momento |
| `borrar_datos(proyecto)` | cliente → | D1 | borrado inmediato y total del crudo |
| `proponer_retencion(candidato)` | operador IA → | D2 → D5 | **propone** retener un patrón; adjunta su prueba de de-identificación |
| `auditar_aprendido(filtro)` | → JM / cliente | D3, D5 | inspecciona qué se ha retenido y su procedencia/prueba |

**Transversal:** mínimo privilegio, **traza de auditoría** de cada retención y cada consentimiento, e **idempotencia** del borrado.

## 6. Máquina de estados y candado de gobierno

- Estados de un candidato a patrón: **CANDIDATO** (D2) → **DE-IDENTIFICADO** (supera el test §7) → **CONSENTIDO** (existe D4 vigente) → **CAPITALIZADO** (retenido en el almacén, D3).
- **Candado de dos llaves:** un candidato solo llega a **CAPITALIZADO** con **prueba de de-identificación verde (golden) + consentimiento vigente + firma de JM**. El operador IA solo `propone_retencion`; **nunca certifica** que un patrón es seguro de capitalizar.
- **Revocación / borrado:** revocar el consentimiento corta futuras retenciones; borrar el crudo es inmediato. Ningún patrón CAPITALIZADO puede quedar atado a un crudo borrado (si lo estuviera, no superó §7 y se purga).

## 7. De-identificación y oráculo (atados a la golden)

El oráculo de C2 **no es numérico ni de conformidad documental** — es de **no-reconducción**. Una golden de C2 somete al conocimiento retenido (D3) a un **intento adversario de re-identificación** y exige que **fracase** en recuperar:

1. **la identidad del cliente** (o del autor/colegiado);
2. **la identidad del proyecto** (nombre, emplazamiento, catastro);
3. **la geometría / cantidades** que reconstruyan el proyecto;
4. **la cadena de firma / responsabilidad civil**.

Si el ataque recupera **cualquiera** de las cuatro ⇒ **rojo**: el patrón **no es retenible**. El fallo más grave es el 4 (reconducir a una firma).

**Procedencia del oráculo:** conjunto de re-identificación **definido y firmado por JM** (mano-JM) sobre proyectos de referencia. Un fallo **no** se arregla relajando el ataque ni el criterio — **solo endureciendo la de-identificación** (mismo espíritu que C5/C7).

> **Golden de v0 a sembrar:** `GOL-DAT-01` — sobre un proyecto de referencia, extraer candidatos a patrón, de-identificarlos y verificar que el ataque de re-identificación fracasa en las cuatro dimensiones. Hasta sembrarla y ratificarla, **C2 v0 no es certificable** (Llave 1 incompleta) y **no se capitaliza nada**.

## 8. Versionado y compatibilidad

- C2 se versiona con SemVer; el consumidor ancla la versión exacta en `versions.lock`.
- **Verde** en la golden anti-re-identificación → se adopta el régimen de retención. **Rojo** → se endurece la de-identificación (regresión) o se cambia el contrato (**MAJOR**).
- Al ser DRAFT pre-1.0 (v0.x), se admiten cambios incompatibles entre minors mientras se estabiliza.

## 9. Puntos abiertos (a cerrar)

1. **Modelo de consentimiento e incentivo** — opt-in (recomendado, soberanía primero) vs opt-out; ¿descuento o contraprestación por consentir? *(decisión comercial — afecta a la tarjeta de precios del roadmap).*
2. **Qué es un "patrón" capitalizable** — taxonomía concreta de D3 (criterios de predimensionado, distribuciones de soluciones, heurísticas de cumplimiento…) y su granularidad.
3. **Técnica de de-identificación** — agregación / k-anonimato / privacidad diferencial / abstracción simbólica; qué se exige para v0.
4. **Encaje legal** — RGPD (datos personales), propiedad intelectual del proyecto, y el deslinde explícito frente a la firma colegiada y su responsabilidad civil. Revisión jurídica antes del primer cliente serio.
5. **Composición con C7** — el operador IA es quien extrae los candidatos; fijar el handoff C7 → C2 (`proponer_retencion`) y que C7 nunca retenga por su cuenta.
6. **Sembrar y ratificar `GOL-DAT-01`** con su conjunto de re-identificación firmado — sin esto, no hay Llave 1.

## 10. Fuera de alcance

- **La implementación del almacén** de conocimiento (base de datos, vectores) — detrás del adaptador.
- **La monetización del consentimiento** (capa comercial).
- **El intercambio con el CDE** (vive en C8) y **la generación de entregables** (vive en C7); C2 solo gobierna qué se aprende y retiene.
- **El modelo de IA concreto** y cómo entrena — detrás del adaptador.

---

### Firma

| Rol | Nombre | Estado |
|---|---|---|
| Prepara (IA) | equipo IA Estructurando 2.0 / Aqyra | Entregado 2026-06-26 |
| Revisa (jurídico) | *(pendiente — RGPD / PI / responsabilidad civil)* | ☐ Pendiente |
| Aprueba/firma | **JM** | ☐ Pendiente |
