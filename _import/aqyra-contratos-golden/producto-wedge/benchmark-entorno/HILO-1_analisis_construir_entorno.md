# Hilo 1 (anexo) — Análisis del escenario "construir el entorno desde cero"

> **Premisa fijada por JM:** crear valor poniendo **la IA como operador nativo sobre formato abierto** (IFC texto), construyendo nuestro propio entorno (visor + CDE + incidencias) en vez de comprar uno.
> **Estado:** evidencia y posición preparadas por la IA (PM / Ing. BIM-IFC) para que **JM decida y firme**. La IA propone; no concluye la decisión.
> **Insumos:** `TESIS_PRODUCTO.md`, `SPRINT_0_REENCUADRE_PROPUESTA.md`, `HILO-1_benchmark_entorno.md`. **Fecha:** 2026-06-24.
> **Alcance pedido:** estratégico + técnico · con esfuerzo orientativo (supuestos explícitos) · contrastando **build vs integrate vs adopt** pieza a pieza.

---

## 0. Tesis del anexo en una frase

> **No se trata de construir "un entorno" —eso sería reconstruir commodity saturado— sino de construir la única capa que el mercado no tiene: el operador IA nativo sobre IFC, ensamblando por debajo piezas abiertas que ya existen (y que en buena parte ya tenemos).** "Desde cero" bien entendido es *delgado por arriba, profundo en un solo sitio*.

---

## 1. La distinción que decide todo: entorno ≠ diferencial

El benchmark (Hilo 1) dejó dos hechos:

1. **Visor, CDE e incidencias son commodity.** Hay diez productos maduros que los cubren; nadie gana ahí por features.
2. **El hueco real es por ausencia:** nadie ha puesto a la IA como **operador nativo** sobre formato abierto. Las APIs del mercado existen para sincronizar dashboards, no para que un agente genere el modelo, lo audite y mueva incidencias.

La `TESIS_PRODUCTO.md` ya nombra esto con precisión: **señuelo vs foso**. El señuelo (table stakes, copiable) es la interfaz y las funciones de entorno; el foso (defendible) es el **corpus golden verificado y recuperable por requisito de información (OIR→AIR/PIR→EIR)** acuñado por la QA de dos llaves. Y el reencuadre del Sprint 0 advierte literalmente de **"la trampa": sobreinvertir en lo vistoso y copiable (motor de lenguaje natural, UI) e infrainvertir en lo aburrido y defendible**.

Aplicado a "construir el entorno", la conclusión es directa:

> **Construir el entorno completo desde cero es, en su mayor parte, construir señuelo.** El visor y el CDE no son el foso; son el envase. Lo que crea valor es la **capa operador IA + el corpus golden**. Por tanto la pregunta correcta no es "¿construimos un entorno?" sino "**¿qué capa del entorno construimos, y qué reutilizamos para no malgastar el esfuerzo en commodity?**".

---

## 2. No partimos de cero: inventario de activos ya existentes

Un dato que cambia la valoración. El ecosistema **Estructurando** (productor) ya tiene, como plugins artesanales, casi todas las piezas del entorno abierto. "Construir desde cero" es en realidad **industrializar lo artesanal + construir la pieza que falta**.

| Capa del entorno | Activo que ya existe (skill/plugin) | Madurez |
|---|---|---|
| Visor IFC web | `visor-ifc` (web-ifc + Three.js, HTML autocontenido, navegación 3D, panel de Psets, árbol espacial) | Funcional, crece por versiones |
| Generación IFC desde lenguaje natural | `narracion-a-ifc` (compilador narración→IFC con geometría real) + `ifc-create` | Funcional (la semilla de Decopak HQ nació así) |
| Validación / QA de modelo | `ifc-validate` (nomenclatura, Psets, reglas) | Funcional |
| Clasificación / enriquecimiento | `bsdd-clasificacion` (bsDD + Uniclass + GuBIMClass) | Funcional |
| Auditoría de CDE / estados ISO 19650 | `cde-audit` (flujo S0–S7, WIP→Compartido→Publicado→Archivado, hitos) | Funcional |
| Requisitos de información | `bep-eir` (BEP/EIR/AIR/PIR/OIR), `loin-matrix` (LOIN, entregables) | Funcional |
| Cálculo y verificación normativa | motores estructuras/instalaciones/obra lineal/puentes + Eurocódigos + CTE | Extensos |

Lo que **NO existe todavía** —ni en Estructurando, según la propia tesis— es la pieza F1.2: la **capa de indexado · recuperación · reaplicación keyed al requisito de información (OIR→AIR/PIR→EIR)**, la que convierte un archivo de casos en un flywheel. *Ese* es el verdadero "construir desde cero", y es exactamente donde está el foso.

**Implicación:** el coste marginal de tener un entorno abierto operable por IA es **mucho más bajo de lo que sugiere "construir desde cero"**, porque el grueso del entorno ya está hecho de forma artesanal. El esfuerzo nuevo se concentra en (a) industrializar esas piezas a calidad de producto y (b) construir la capa de recuperación por OIR.

---

## 3. Arquitectura de referencia del entorno propio

Siete capas, de sustrato a diferencial. La columna **decisión** anticipa la sección 5.

| # | Capa | Qué hace | Pieza abierta de apoyo | Decisión |
|---|---|---|---|---|
| 1 | **Sustrato** | IFC como texto: legible, versionable, *diff*-able, auditable | IFC4 / IFC4.3 (estándar bSI), IfcOpenShell | **Adoptar** (es el estándar; es la premisa) |
| 2 | **Almacén + versionado** | Guardar y versionar modelos y casos; histórico, ramas, *diff* | **Git** (texto) + **Speckle** (objetos versionados, Apache-2.0, self-host) | **Integrar** |
| 3 | **Visor** | Navegar IFC en web/tablet, selección, Psets, árbol | **That Open / web-ifc** (MPL-2.0) — ya tenemos `visor-ifc` | **Construir (delgado) sobre open source** |
| 4 | **CDE / estados 19650** | WIP→Compartido→Publicado→Archivado, metadatos, naming, trazabilidad | Git como motor de estados + metadatos; `cde-audit` ya audita el flujo | **Construir (delgado)** |
| 5 | **Incidencias** | Crear/leer/mover issues; coordinación (diseño) y snagging (obra) | **BCF estándar** (buildingSMART); BCF-API; BIMcollab/Dalux para campo | **Integrar (por BCF)** |
| 6 | **★ Operador IA nativo** | Genera el IFC desde lenguaje natural, lo audita, acuña incidencias, calcula, redacta; opera *sin GUI* sobre el texto | LLM + skills propias (`narracion-a-ifc`, `ifc-validate`, motores) | **Construir — es el diferencial** |
| 7 | **★ Foso: corpus golden + recuperación por OIR** | Indexa cada respuesta verificada por EIR/PIR (llave) y OIR (objetivo); la recupera y reaplica en el caso N+1; gobierno QA de dos llaves la acuña | No existe en el mercado ni en Estructurando | **Construir — es el foso (F1.1/F1.2)** |

Las capas 1–5 son **el entorno** (commodity, ensamblable). Las capas 6–7 son **el producto** (foso). La premisa de JM —IA operador nativo sobre formato abierto— se materializa en que **la capa 6 opera directamente sobre la capa 1 (texto)**, sin pasar por binarios, y la capa 7 es lo que hace que ese operador *componga interés* proyecto a proyecto.

---

## 4. Dónde se crea valor y dónde se destruye

**Se crea valor (construir tiene sentido):**

- **Capa 6 — operador IA nativo.** Es el hueco verificado del mercado. Construirlo nos da algo que ACC, Aconex o Dalux no pueden ofrecer sin renunciar a su lock-in binario. El sustrato de texto es lo que lo hace posible; por eso la premisa "formato abierto" no es ideología, es el habilitador técnico del diferencial.
- **Capa 7 — corpus golden + recuperación por OIR.** Es el foso. No es scrapeable: es confianza acuñada caso a caso por el gobierno de QA. Aquí "construir desde cero" es literal y obligatorio, porque no existe en ningún sitio.
- **Capas 3–4 *delgadas y propias*.** Tener visor y estados de CDE *propios* (no comprados) vale porque (a) eliminan dependencia y coste de licencia, (b) son embebibles donde la IA los necesita, y (c) ya los tenemos casi hechos. El valor no está en que sean "mejores", sino en que son **nuestros y operables por la IA**.

**Se destruye valor (construir sería la trampa):**

- **Reimplementar un visor de nivel comercial** (clash por reglas tipo Solibri, render de millones de objetos, AR). Años de trabajo para empatar commodity. Si un piloto lo exige, se *adopta* Solibri/Zoom.
- **Construir un CDE documental enterprise** (permisos finos, workflows de aprobación, escala de Aconex/Asite). Saturado, pesado, sin diferencial. Se integra/adopta.
- **Construir una app de campo nativa** (offline real, sync, snagging en tablet) desde cero. PlanRadar/Dalux Field lo tienen resuelto; competir ahí es quemar el presupuesto en el rincón más commodity. Se integra por API/BCF.
- **Un servidor BCF-API completo y certificado.** Salvo necesidad, es más barato hablar el BCF-API de BIMcollab que mantener uno propio conforme.

> Regla de oro derivada de la tesis: **construir solo lo que es a la vez (a) diferencial y (b) imposible de comprar sin lock-in. Todo lo demás se integra por estándar abierto o se adopta.** Construir de más nos mete a competir en el mercado saturado que la tesis dice evitar.

---

## 5. Build vs Integrate vs Adopt — pieza a pieza

| Componente | Build | Integrate | Adopt | Recomendación (insumo) |
|---|---|---|---|---|
| Sustrato IFC texto | — | — | ✓ | **Adoptar** estándar bSI. Premisa no negociable. |
| Almacén/versionado | parcial | **✓ Speckle + Git** | — | **Integrar.** Speckle self-host (Apache-2.0); Git para *diff* de texto. |
| Visor web/tablet | **✓ delgado** | (web-ifc/That Open) | — | **Construir delgado** sobre `visor-ifc` ya existente. No reinventar Solibri. |
| Estados CDE 19650 | **✓ delgado** | — | (o Trimble/usBIM free) | **Construir delgado** apoyado en `cde-audit`; Git como motor de estados. |
| Incidencias coordinación | — | **✓ BCF / BIMcollab** | Solibri/Zoom acuña | **Integrar por BCF.** Única con BCF-API estándar = BIMcollab. |
| Incidencias campo/obra | — | **✓ Dalux/PlanRadar API** | — | **Integrar.** No construir app de campo; los mejores ya existen. |
| Clash / QA reglado | — | (IDS) | **✓ Solibri/Zoom** | **Adoptar** como productor de issues; nuestra IA los gestiona. |
| **Operador IA nativo** | **✓✓** | — | — | **Construir.** El diferencial. Apóyate en `narracion-a-ifc`, `ifc-validate`, motores. |
| **Corpus golden + recuperación OIR** | **✓✓** | — | — | **Construir (F1.1/F1.2).** El foso. No existe en ningún sitio. |
| Cálculo/normativa | **✓ (ya hecho)** | — | oráculos (PyNite) | **Reutilizar** motores del ecosistema; anclar oráculo de referencia. |

Patrón: **construir solo la columna ★ (capas 6–7) y el barniz delgado de 3–4; integrar 2 y 5; adoptar 1 y el QA reglado.**

---

## 6. Esfuerzo orientativo (con supuestos explícitos)

> **Supuestos** (si cambian, cambian las cifras): equipo pequeño (1 full-stack JS/BIM + 1 Python/IA + JM en núcleo FEM + agente QA separado); se reutilizan los plugins artesanales existentes como base; objetivo = **MVP interno operable** para los pilotos Decopak HQ / Terres Cavades, **no** producto comercial endurecido; FTE-mes = una persona a tiempo completo un mes. Rangos amplios a propósito: es insumo, no compromiso.

| Componente | Esfuerzo orientativo | Naturaleza | Nota |
|---|---|---|---|
| Visor propio a calidad usable | **1–2 FTE-mes** | Industrializar | Partimos de `visor-ifc`; barniz, no obra nueva. |
| Almacén/versionado (Speckle self-host + Git) | **0,5–1 FTE-mes** | Integrar | Stand-up + conectores; mantenimiento de infra aparte. |
| Estados CDE 19650 (capa delgada) | **2–4 FTE-mes** | Construir delgado | Metadatos + S0–S7 + trazabilidad sobre Git; apóyate en `cde-audit`. |
| Incidencias por BCF (integración) | **1–3 FTE-mes** | Integrar | Cliente BCF + conector a BIMcollab/Dalux; no servidor propio. |
| **Operador IA nativo (capa 6)** | **6–12+ FTE-mes** | Construir ★ | El grueso del valor; iterativo y continuo, no "termina". |
| **Corpus golden + recuperación OIR (capa 7, F1.1/F1.2)** | **6–12+ FTE-mes** + continuo | Construir ★★ | El foso. Diseño primero (Sprint 0), implementación después; compone con cada caso. |
| Integración de campo (Dalux/PlanRadar) | **1–2 FTE-mes** | Integrar | Diferible hasta fase Construcción de un piloto. |

**Lectura del esfuerzo, no la suma.** Sumar da un rango de ~**18–36 FTE-mes** hasta un MVP interno con foso incipiente, pero **la cifra importante no es el total: es el reparto.** Las capas commodity (visor, almacén, CDE, incidencias) son **~5–10 FTE-mes** y la mayor parte es integración o barniz sobre lo ya hecho. El diferencial (capas 6–7) es **~12–24+ FTE-mes y nunca "acaba"**. Si el reparto se invierte —mucho esfuerzo en visor/CDE, poco en foso— estamos ejecutando la trampa que la tesis ordena evitar.

**Coste de licencia evitado (a favor del build):** construir/integrar abierto elimina suscripciones recurrentes por usuario (referencias del Hilo 1: ACC ~0,5–1,3 k$/u·año; Solibri ~1,4–2,8 k€/año; Dalux/Aconex bajo consulta). Para un despacho que escala usuarios, el ahorro recurrente es real; pero **no es la razón para construir** —la razón es el diferencial—, es un beneficio colateral.

---

## 7. Riesgos del escenario "construir"

- **R1 · La trampa de la tesis (el más grave).** Sobreinvertir en lo copiable (visor bonito, motor narración→IFC demoable) e infrainvertir en F1.1/F1.2. *Mitigación:* fijar por gobierno el orden de prioridad del reencuadre (foso primero) y medir la **métrica estrella**: coste marginal del caso N+1 vs N.
- **R2 · Mantenimiento del commodity propio.** Un visor/CDE propio es deuda perpetua (formatos IFC nuevos, navegadores, escala). *Mitigación:* mantenerlo **delgado** y apoyado en open source mantenido por terceros (That Open, Speckle); no perseguir paridad con Solibri.
- **R3 · Dependencia de open source de terceros.** web-ifc (MPL-2.0) y Speckle (Apache-2.0) son sanos hoy, pero su gobierno/financiación es externa. *Mitigación:* licencias permiten *fork*; verificar licencia **paquete a paquete** del ecosistema That Open antes de cerrar arquitectura (conviven MPL-2.0 y posibles MIT — pendiente del Hilo 1).
- **R4 · Fidelidad del *roundtrip* IFC.** Generar y editar IFC por IA con geometría y Psets correctos y *re-exportables* sin pérdida es difícil; es el corazón técnico de la capa 6. *Mitigación:* el gobierno QA de dos llaves existe precisamente para no firmar lo no verificado; Decopak HQ es la prueba E2E.
- **R5 · BCF-API inmaduro como producto.** Solo BIMcollab ofrece BCF-API estándar; el resto es dialecto propio. *Mitigación:* tratar BCF como protocolo de salida/entrada e integrarse con quien lo hable; no casarse con un solo proveedor de campo.
- **R6 · Talento concentrado.** Requiere a la vez JS/Three.js + Python/IA + dominio BIM/ingeniería. Equipo pequeño = *bus factor* alto. *Mitigación:* la propia IA del ecosistema reduce la dependencia; documentar y versionar (gobierno ya cerrado).
- **R7 · El foso no está probado.** La capa 7 (recuperación por OIR que abarata el N+1) es la hipótesis central y **aún no existe**. Es el mayor riesgo *y* la mayor recompensa. *Mitigación:* el M2 del reencuadre la pone a prueba con un segundo caso medido.

---

## 8. Posición (insumo para JM, no decisión)

**El escenario "construir desde cero" es acertado en su premisa y peligroso en su literalidad.**

- **Acertado:** poner la IA como operador nativo sobre IFC texto ataca el único hueco real del mercado y solo es posible construyéndolo —ningún incumbente puede ofrecerlo sin renunciar a su lock-in binario—. La premisa de JM apunta al sitio correcto.
- **Peligroso si se toma al pie de la letra:** "construir *el entorno* (visor + CDE + incidencias) desde cero" sería reconstruir commodity saturado y caer en la trampa que la propia tesis ordena evitar. Además sería ignorar que **ese entorno ya está casi hecho** de forma artesanal en Estructurando.

**Reformulación recomendada del escenario:** no "construir un entorno", sino **"ensamblar un entorno abierto a partir de piezas que ya tenemos/existen, y construir desde cero solo el operador IA nativo (capa 6) y el foso de recuperación por OIR (capa 7)"**. Es *delgado por arriba, profundo en un solo sitio*. Eso:

1. Materializa la premisa (IA operador nativo sobre formato abierto).
2. Respeta la tesis (esfuerzo al foso, no al señuelo).
3. Aprovecha los activos existentes (coste marginal bajo del entorno).
4. Mantiene óptica abierta: integrar por BCF/IFC, adoptar lo commodity, construir lo defendible.

**Lo que esta posición *no* hace:** no decide compras ni cierra arquitectura. Tres puntos quedan abiertos para JM: (i) confirmar el reparto de esfuerzo foso-vs-entorno; (ii) elegir Speckle como capa de datos o quedarse en Git+web-ifc puro; (iii) decidir si la integración de campo (Dalux/PlanRadar) entra en el MVP o se difiere. La decisión y la firma son de JM.

---

## 9. Siguiente paso sugerido

Encaja con el Sprint 0 reencuadrado: priorizar **F1.1 (esquema de la unidad de caso golden)** y **F1.2 (capa de recuperación por OIR)** —la capa 7—, usar **Decopak HQ** como prueba E2E de las capas 6–7 sobre el entorno ya existente, y dejar el visor/CDE/incidencias como *delgado e integrado*. Si se quiere, el Hilo 2 puede ser el **diseño técnico de la capa 6+7** (arquitectura, esquema del átomo golden, índice por OIR→EIR), que es donde se juega el valor.

---

*Procedencia: anexo al Hilo 1, preparado por la IA (PM / Ing. BIM-IFC) de Estructurando 2.0 · 2026-06-24 · evidencia y posición para decisión y firma de JM. Datos de herramientas verificados en `HILO-1_benchmark_entorno.md`.*
