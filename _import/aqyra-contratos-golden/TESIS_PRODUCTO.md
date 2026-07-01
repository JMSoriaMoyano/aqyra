# Tesis de producto — Estructurando 2.0

**Documento fundacional** · reencuadra el enfoque de producto del proyecto
**Estado:** PROPUESTA — pendiente de firma de JM · **Fecha** 2026-06-23 · **Versión** 1.0
**Reemplaza:** el enfoque previo «wedge = visor + auditoría ISO 19650 + checklist CTE», que se archiva por insuficiente (escondía el 95 % del valor en el rincón más saturado y de menor valor del mercado).

> Preparado por la IA (PM) a partir de la sesión de estrategia con JM. Fija el «qué» y el «por qué» del producto. La responsabilidad y la aprobación son de JM.

---

## 0. En una frase

> **Interfaz copiable arriba, corpus golden verificado e indexado por requisito de información (OIR→AIR/PIR→EIR) abajo; el gobierno de QA es la máquina que acuña el foso.**

El producto no es un modelador ni un visor. Es un **organismo vivo**: del lenguaje natural y el conocimiento acumulado nace un modelo IFC con criterio de ingeniero, y de esa semilla cuelgan —casi gratis— el cálculo, la firma, la obra y el mantenimiento. Lo que se vende y lo que defiende no es la herramienta, es **la experiencia verificada del ecosistema, recuperable cuando un nuevo proyecto la necesita.**

## 1. El tablero: el campo de batalla es el formato y la curva, no las funciones

Las herramientas que dominan el sector (Revit, Cype) tienen el mercado cautivo por dos cosas, no por ser mejores:

- **El binario propietario.** El `.rvt` opaco es su foso. Y en la era de la IA es su talón de Aquiles: *un agente no puede operar de forma nativa sobre un binario cerrado.*
- **La curva de aprendizaje.** Años de inversión y coste hundido atan al usuario. Esa curva es lo que impide que se vayan.

Atacar features es competir en su tablero. La jugada es otra: **cambiar el tablero.**

- El **IFC** lleva 20 años siendo el estándar abierto «aburrido» de intercambio. Resulta que es **texto** —legible, editable, versionable, audtable, *diff*-able— y por tanto **el único sustrato sobre el que la IA opera nativamente.** El foso del incumbente (el binario) se convierte en su herida.
- La **IA** lleva la curva de aprendizaje a cero. El usuario ya no aprende *el idioma de la herramienta*; habla **el suyo**. Disolver la curva no es una mejora de UX: es disolver lo que protege a Revit.

## 2. La disrupción se apoya en dos pilares

1. **IFC abierto** (existe hace +20 años): código no binario, editable como texto, democrático.
2. **IA que acumula conocimiento** (existe hoy): asiste en todas las fases —ubicación, diseño, redacción, ejecución, mantenimiento— y, sobre todo, *compone interés* proyecto a proyecto.

Competir en todas las fases es posible **no por hacer mucho, sino porque la ventaja —el conocimiento acumulado— es transversal a todas.** Pero una plataforma entra al mercado por **una sola herida**.

## 3. La herida de entrada: crear el modelo

El cuello de botella del sector es **crear el modelo**: caro en horas, hecho por personal con poca experiencia de obra, y por eso desconectado de la realidad construible. Las dolencias del cliente lo señalan:

1. Coste de aprendizaje de las herramientas (modelar en Revit no es fácil).
2. Los modeladores tienen poca experiencia de obra → modelo divorciado de la buildabilidad.
3. El coste de licencia no es barato.
4. Bajo ese paradigma cerrado, acumular experiencia agéntica para despachos y constructoras depende de la voluntad del incumbente.

**Entrada elegida (año 1): la creación del modelo desde lenguaje natural.** El cálculo, la firma, la obra y el mantenimiento son *bonus tracks* que se capitalizan por inercia **siempre que cuelguen de la misma semilla IFC viva.** Un modelo bien hecho produce obra bien hecha: evita retrabajo y acelera la ejecución.

## 4. Señuelo vs. foso

| | Señuelo (table stakes) | Foso (defendible) |
|---|---|---|
| Qué es | El modelado por lenguaje natural (la interfaz) | El corpus de casos golden **verificados**, indexados por requisito de información (OIR→AIR/PIR→EIR), en todas las fases |
| Por qué | Hay que construirlo, pero **es copiable**; la ventaja se erosiona | No es un dataset scrapeable: es **confianza acuñada** caso a caso |
| Horizonte | ~18 meses hasta que un incumbente saque su «describe tu edificio» | Compone interés indefinidamente; nadie puede arrancarlo desde silos binarios |

**El valor no es la herramienta. Es la experiencia acumulada y verificada del ecosistema.** Lo escaso que se vende en ingeniería no es la solución, es **la confianza verificada** — y la confianza no se entrena con datos ajenos encerrados en binarios; se acuña con un proceso institucional (QA independiente + firma) que el incumbente no tiene.

## 5. La unidad de valor: el átomo no es «el proyecto»

El activo no es «el proyecto Decopak HQ». El átomo reusable es:

> **Una respuesta verificada a un requisito de información, en una fase.**

Ejemplo real (Decopak HQ): *voladizo grande + planta diáfana → forjado ligero CLT/cassette + acero S355 + optimización EC3* — **verificado, firmado, recuperable.** El proyecto es solo el envase; el átomo es la respuesta verificada al requisito.

**Precisión de terminología (ISO 19650).** «Requisito de información» no es un nivel único, sino una cascada — **OIR → AIR/PIR → EIR**:

- **OIR** (organización): el objetivo estratégico, el *por qué* el caso merece guardarse y reusarse. Da **prioridad y sentido**, no es llave de búsqueda.
- **AIR / PIR** (activo / proyecto): el requisito de la fase (explotación / entrega).
- **EIR** (intercambio): el requisito **concreto y accionable** («losa en voladizo de 4 m, R60, planta diáfana»). Es la **llave técnica de recuperación**.

Es decir, el átomo se **indexa a dos niveles**: el **EIR/PIR** como llave de búsqueda (lo que se recupera) y el **OIR** como objetivo que lo justifica y prioriza.

## 6. Archivo vs. flywheel: lo que de verdad compone

Un montón de casos verificados es un **archivo**, no un flywheel. Decopak HQ puede ser un golden perfecto y **no** abaratar el siguiente edificio de voladizos si el caso N+1 no puede *recuperar* y *apoyarse* en el N.

El valor no está en *acumular* experiencia, sino en **recordarla y reaplicarla** en el instante en que un nuevo requisito de información —un **EIR/PIR** concreto— la necesita. La pieza que convierte archivo en flywheel —y que **aún no existe ni en Estructurando**— es la **capa de indexado · recuperación · reaplicación, keyed al requisito de información (OIR→AIR/PIR→EIR).** Sin ella: un cementerio de soluciones geniales, cada una huérfana.

Dos pruebas de que el flywheel gira:

- El **segundo** edificio de voladizos nace **más barato** que el primero porque Decopak HQ dejó conocimiento estructurado detrás → *flywheel girando.*
- Lo produce **alguien que no es JM**, sin la conversación brillante → *producto.*

## 7. El gobierno de QA es la fábrica del foso

El gobierno de `GOBIERNO_QA_Y_VERSIONES.md` no era solo control de calidad. Un caso es «golden» porque **pasó la QA independiente de dos llaves y lo firmó un ingeniero**. Por tanto:

> **Cada certificación de dos llaves mina un activo defendible.**

La separación de funciones, las tres capas y la firma de JM son el **proceso institucional que acuña confianza**. Eso recolorea todo el proyecto: la QA no es un coste de calidad, es la **línea de producción del foso.**

## 8. El wedge, reencuadrado

- **Qué es:** crear el modelo IFC con criterio de ingeniero **desde lenguaje natural**, apoyándose en el corpus golden verificado del ecosistema.
- **Qué NO es:** un visor con checklist; un «mejor Revit»; una guerra de features sobre una interfaz copiable. (Detalle en `producto-wedge/PRD/`.)
- **Por qué gana:** «fácil por arriba» exige «durísimo por debajo». La simplicidad es posible **porque** el conocimiento acumulado y el gobierno de QA absorben la complejidad. Nadie más puede ofrecer «fácil» sin tener antes el «difícil».

## 9. Decopak HQ: la prueba extremo a extremo

El IFC `DEC-PB-EBAN-HQ-...-S1-v0.0.ifc` (IFC4, texto; Rubí; 7 plantas −1,5→+15; S355 + HA-30 + CLT; Psets de límite elástico y fuego R60; optimización EC3) **nació de una conversación en lenguaje natural sobre un informe de voladizos, sin Revit ni licencia.** No es proyecto ni memoria de cálculo ni sirve para ejecutar todavía — es **la semilla**, y la prueba de que el organismo arranca. Es nuestro piloto para industrializar el camino semilla → modelo calculable → firmado → construible.

## 10. Implicaciones (qué cambia a partir de aquí)

- **PRD del wedge:** se archiva «visor + checklist»; se reescribe como «modelo desde lenguaje natural sobre corpus golden» (B1.1/B1.2 reencuadrados).
- **Proyecto Entorno (`entorno/`):** la primera realización concreta del wedge — visor OpenBIM asistido por IA (pre/post de cálculo), con estrategia **cebo-anzuelo** hacia una spin-off. El *señuelo/foso* de esta tesis se materializa físicamente como `publico/` (cebo) vs `privado/` (anzuelo). La interfaz con el CDE es el contrato **C8**.
- **Sprint 0:** se reordena alrededor del foso — definir la **unidad de caso golden** y la **capa de recuperación por requisito de información (OIR→AIR/PIR→EIR)**, con Decopak HQ como prueba E2E (propuesta aparte, pendiente de firma de JM).
- **Métricas (A2.1):** el ROI sigue valiendo, pero la métrica estrella pasa a ser **el coste marginal decreciente** del caso N+1 frente al N (prueba del flywheel).
- **Activo a construir, por prioridad:** (1) la capa de recuperación/reaplicación por requisito de información (OIR→AIR/PIR→EIR) [foso], (2) el motor de lenguaje natural → IFC [table stakes, ya existe `narracion-a-ifc`], (3) la maquinaria de acuñación golden [ya diseñada en el gobierno].

> **Trampa a vigilar:** sobreinvertir en el motor de lenguaje natural (lo vistoso y demoable, pero copiable) e infrainvertir en la capa golden/recuperación (lo aburrido y defendible). Casi todos construyen la demo y nunca el foso.

---

### Firma

| Rol | Nombre | Estado |
|---|---|---|
| Prepara (IA · PM) | equipo IA Estructurando 2.0 | Entregado 2026-06-23 |
| Aprueba/firma | **JM** | ☐ Pendiente |
