# Registro de decisiones cerradas — Entorno (§9 del brief de V1)

> **Qué es:** bitácora de decisiones **firmadas por JM**, trazables al dossier de evidencia. La IA preparó la evidencia; **JM decidió y firmó**. Una entrada por decisión.
> **Convención:** cada decisión indica fecha, lo firmado, la evidencia de respaldo y las acciones que dispara.

---

## D-001 · §6.1 — Alcance de BCF e IDS en V1

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM
- **Decisión:** **BCF completo (ver + crear) en V1.** **IDS partido:** en V1, cargar un IDS y ejecutar la validación sobre el modelo; **autoría/edición de IDS se difiere a V2.**
- **Evidencia:** `HILO-V1_dossier-decisiones-6-7.md` §6.1 — IDS 1.0 estándar oficial (jun 2024); componentes web nativos `BCFTopics` e `IDSSpecifications` en That Open.
- **Acciones que dispara:** el DoD de V1 incluye ver+crear BCF y validar un requisito IDS de lectura; la UI de autoría IDS entra en el backlog de V2.

## D-002 · §6.2 — Stack de datos

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM
- **Decisión:** **web-ifc + Fragments puro en V1, sin servidor.** Speckle se **reevalúa en V5** (si entonces hace falta capa de datos servidor).
- **Evidencia:** dossier §6.2 — Speckle exige servidor (contradice "web sin instalación + tablet") y tiene un módulo EE no abierto.
- **Cotejo con benchmark — CONFORME (2026-06-24):** `HILO-1_benchmark_entorno.md` (ya en el repo) **respalda** la decisión: recomienda *construir* sobre web-ifc/That Open (MPL-2.0/MIT) + IfcOpenShell, y **advierte** sobre Speckle ("trabaja sobre modelo de objetos, no IFC nativo de fichero; no es BCF-céntrico ni valida IDS nativo"; módulos `workspaces`/`gatekeeper` EE). El benchmark **no** elige Speckle como capa.
- **Riesgo trasladado del benchmark (a vigilar en V1):** la cobertura **IFC4.3** de web-ifc/That Open es **parcial/en evolución [I]**; IfcOpenShell sí cubre 4x3 completo server-side. Si el DoD "abre cualquier IFC 4.3" se resiente, contemplar IfcOpenShell como respaldo de parsing.

## D-003 · §6.3 — Licencia OSS del cebo

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM
- **Decisión:** licenciar `publico/` bajo **Apache-2.0** *(recomendación de la IA por la cláusula de patentes y la vocación spin-off; JM puede revertir a MIT con una línea aquí)*. Se **autoriza el check legal de atribuciones** antes de la primera publicación.
- **Evidencia (licencias verificadas 2026-06-24):** web-ifc = **MPL-2.0** (copyleft por fichero, no contagia al consumirlo como dependencia); `@thatopen/components`, `@thatopen/fragments`, `@thatopen/ui` = **MIT**.
- **Acciones que dispara:** (1) no modificar ficheros de web-ifc dentro del repo (consumir como dependencia anclada; cualquier parche → fork MPL-2.0 separado y publicado); (2) **evidencia incorporada (2026-06-24):** `CHECK_LICENCIAS_publico.md` (mapa paquete→licencia + compatibilidad) y `publico/THIRD-PARTY-NOTICES.template.md` (atribuciones a distribuir con el cebo); (3) **residual — gate de publicación:** validación jurídica + escaneo `license-checker`/`pip-licenses` sobre el **árbol real de dependencias de V1** (incluidas transitivas; bloqueante si aparece GPL/AGPL en `publico/`). **No publicar `publico/` hasta ese cierre.**

## D-004 · §6.4 — Marca

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM
- **Decisión:** **la marca del producto es «Aqyra».** Sustituye al placeholder "Entorno". Nombre acuñado/distintivo (favorable para registro como marca fuerte); sin colisión externa detectada (búsqueda 2026-06-24) ni paquete npm público.
- **Punto a confirmar por JM (no decidido por la IA):** «Aqyra» **ya nombra el CDE** del ecosistema (skill `cde-audit`: "Entorno Común de Datos, incluido Aqyra"). Hay que fijar la relación: ¿marca paraguas única (Aqyra = CDE + visor + entorno) o se distingue el producto del CDE (p. ej. "Aqyra Visor")? De ello depende si se propaga el rename a README/INSTRUCCIONES/HOJA_DE_RUTA.
- **Verificación pendiente (de finalista):** dominio (`.com`/`.io`/`.dev` por WHOIS), marca en EUIPO eSearch plus + USPTO (clases 9 y 42), scope npm/GitHub `@aqyra`.
- **Evidencia:** dossier §6.4 + `HILO-V1_marca-candidatas.md`.
- **✅ Cierre del punto abierto — 2026-06-26 · Firmante: JM:**
  - **Grafía oficial única: «Aqyra»** (`a-q-y-r-a`, sin "u"). Se descartan variantes (Aquira, Aquyra). Verificado: la grafía ya era consistente en 39 documentos del ecosistema; la única deriva estaba en el nombre de la carpeta raíz.
  - **Estructura de marca: paraguas única.** **Aqyra = CDE + visor + entorno + ecosistema.** Los productos/módulos no son marcas separadas; se nombran de forma descriptiva ("el visor de Aqyra"). No se crean submarcas por ahora.
  - **Acción ejecutada:** carpeta raíz del ecosistema renombrada `Aquira Alfa` → `Aqyra-Raiz` (panel de mando).
  - **Documento canónico:** `Aqyra-Raiz/MARCA_Y_NOMENCLATURA.md`.
  - **Sigue pendiente (no bloqueante):** la verificación externa de finalista (dominio/EUIPO/USPTO/scope), que se mantiene abierta.

## D-005 · §7 — Frontera (qué viaja / qué se ancla) + reconciliación C7/C8

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM
- **Decisión:**
  - **Viajan con el Entorno:** benchmark `HILO-1`, instantánea del gobierno, baseline narración→IFC, todo `publico/` y la cáscara de `privado/`.
  - **Se quedan en la zona protegida de 2.0 y se consumen anclados:** **contrato C8 (CDE)**, corpus golden (capa 7), motores de cálculo.
  - **Reconciliación C7/C8:** se confirma que **C8 = CDE** es un contrato adicional que el Entorno **consume anclado pero no incrusta**. Añadido a `integracion/versions.lock`.
- **Acciones que dispara (previas a escribir código):**
  1. **`versions.lock` actualizado** ✅ — anclado `iso19650-openbim "0.8.2"` (tag real del baseline); añadido `C8` (CDE); rango de contratos C1..C8.
  2. **Traer el benchmark `HILO-1` al repo** ✅ — `HILO-1_benchmark_entorno.md` incorporado (subido por JM 2026-06-24) y cotejado contra D-002.
  3. **Rellenar `versions.lock` con los tags reales** ✅ — anclados según el plan de release **N1.1** (primer corte, política `0.x`): `motor-fem 0.1.0`, `motor-calculo 0.1.0`, `visor-ifc 0.1.0`, `estructuras-eurocodigos 0.1.0`, `iso19650-openbim 0.8.2`. `operador`/`corpus` (capas 6/7, `privado/`) siguen en `0.0.0` (aún no liberadas). **Cierre formal pendiente de JM:** suite golden en verde + tag GPG firmado (segunda llave del release N1.1, firma "☐ Pendiente").

---

## D-006 · Decisiones técnicas de V1 (plan técnico §8)

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM
- **Decisión:** monorepo con **pnpm workspaces**; bundler **Vite**; publicación SemVer en **registro privado hasta V5**; embebible como **Web Component estándar** `<aqyra-viewer>`; scope npm **`@aqyra/*`**; modelo de referencia de rendimiento **Decopak HQ**.
- **Evidencia:** `HILO-V1_plan-tecnico.md` §8.
- **Nota:** el scope `@aqyra/*` queda sujeto a la verificación autoritativa de marca/dominio (residual D-004); "registro privado hasta V5" se alinea con los gates de D-003 (legal) y D-004 (marca).

---

## D-007 · Dirección de producto de la interfaz (lienzo limpio + NL contextual)

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM
- **Decisión:** la superficie de Aqyra es **canvas-first**: el modelo 3D ocupa todo y la UI **aparece bajo demanda** (menú contextual al clic, barra de comandos en lenguaje natural, paneles sumonables/fijables), **no** paneles permanentes. La interfaz se **adapta al rol/tarea** (Calculista, BIM Manager, Modelador…) priorizando las acciones relevantes. Los paneles "commodity" (lista de clases, Psets fijos) se conservan como demo de verificación, no como producto.
- **Por qué:** alinea con el principio fundacional "la curva de entrada es el enemigo" y con el diferencial (NL sobre formato abierto). Compite por *disolver la curva*, no por features.
- **Frontera cebo/anzuelo:** la **superficie** NL es pública (`publico/ui-nl/`, hoy stub de reglas en la skin Calculista); el **criterio** que la hará inteligente (recuperado del corpus) es privado y se enciende en **V4**.
- **Estado:** prototipo validado en la skin `demo/calculista.html` (barra de comandos, menús contextuales, deshacer, clases interactivas, árbol). El copiloto real es V4.
- **Evidencia:** sesión de producto 2026-06-24; `ESTADO_V1.md`.

---

## D-008 · Arquitectura de organización por ejes/lentes + carril "Higiene BIM" (V1)

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM
- **Decisión de arquitectura:** Aqyra modela la organización del modelo como un **conjunto de ejes/lentes**, no un árbol único: **un eje espacial obligatorio** (1-a-1: cada elemento en un contenedor) + **N ejes funcionales** opcionales y solapables (muchos-a-muchos): zonas (`IfcZone`), sistemas (`IfcSystem`/`IfcDistributionSystem`), estructural-por-comportamiento (`IfcGroup`/dominio analítico), clasificación (Uniclass/GuBIMClass) y mantenimiento/explotación. El lector espacial cubre **IFC4** (`IfcBuilding`/`IfcBuildingStorey`) e **IFC4.3** (`IfcFacility`/`IfcFacilityPart`, `IfcBridge`/`IfcRoad`).
- **Carril de V1 "Higiene BIM / saneamiento" — secuencia firmada:**
  1. **Opción 1 — Sanear el eje espacial** (reasignar por geometría: cota/centroide → planta; reconstruir el árbol) + **Opción 4 — consulta NL simple** sobre el eje saneado ("¿cuántas ventanas en P1?") → **primer corte**.
  2. **Opción 2 — navegación multi-lente** (leer ejes que el IFC trae + derivar los simples) → incremento.
  3. **Opción 3 — autoría asistida de estructuras funcionales** (proponer/escribir `IfcZone`/`IfcSystem`/`IfcGroup` por criterio) → incremento (anzuelo fuerte; enlaza con V4).
- **Gobierno:** toda estructura que la IA **derive o cree** es `proposal`; el write-back va con **preview/diff + aprobación**; se preserva el original (Pset) para deshacer. **Cebo** = mecánica (leer/escribir IFC, recorrer, contar); **anzuelo** = criterio (cómo agrupar/nombrar/clasificar, del corpus). La IA propone; **JM firma**.
- **Métrica espacial enchufable (implementado 2026-06-24):** el motor de saneamiento es genérico sobre una **métrica** (`SpatialMetric` en `publico/visor/src/spatial-metric.ts`). `elevationMetric` (**cota → IfcBuildingStorey**, edificación) está operativo y probado; `stationMetric` (**PK sobre IfcAlignment → IfcFacilityPart**, infraestructura) es un **hook preparado** que se implementará en el incremento de obra lineal (apoyado en el dominio del núcleo). `proposeSpatialFix(kind)` selecciona la métrica; el write-back (reasignar contención + reescribir) es común a ambas.
- **Evidencia:** sesión de producto 2026-06-24; backlog en `ESTADO_V1.md`.

---

## D-009 · §6.1 — Fuente del modelo analítico (V2)

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM · **FIRMA: ✅**
- **Decisión:** **derivar el idealizado del modelo físico (b)** como vía primaria (ejes desde la trayectoria de extrusión de `IfcBeam`/`IfcColumn`/`IfcMember`, sección desde `…ProfileDef`, clasificación por `PredefinedType`); **leer `IfcStructuralAnalysisModel` (a)** si el IFC de entrada lo trae; **consumir el analítico del núcleo (c)** como puente aguas abajo. Apoyos y cargas **siempre autorados** en Aqyra (no vienen en la entrada).
- **Evidencia:** `HILO-V2_evidencia-modelo-analitico.md` §2 (Decopak HQ sin dominio de análisis); `HILO-V2_evidencia-cruzada_calculo.md` §3 (vía (b) ejercitada con éxito: la QA reconstruyó nudos y conectividad reales para el FEM nodal).
- **Acciones que dispara:** el primer corte deriva el eje del `IfcExtrudedAreaSolid` (no hay `'Axis'`); la derivación se diseña enchufable (estilo `SpatialMetric`) por tipología; la idealización sale como `proposal` revisable por un humano (preview/diff).
- **Salvedad registrada:** la verificación estructural que respalda esta vía se hizo en predimensionado verificado **sin el oráculo PyNite** (re-ejecución pendiente en *Estructurando 2.0*); no condiciona esta decisión de producto/arquitectura.

## D-010 · §6.2 — Dónde regenera / write-back (V2)

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM · **FIRMA: ✅**
- **Decisión:** persistir cargas/apoyos **client-side con web-ifc** (texto diff-able), honrando D-002 ("sin servidor"); reservar un backend Python/IfcOpenShell solo si la regeneración paramétrica completa lo exige más adelante.
- **Evidencia:** D-002 + write-back de web-ifc probado en V1; `HILO-V2_evidencia-cruzada_calculo.md` §3 (IFC tratado como texto STEP diff-able en el cálculo).
- **Acciones que dispara:** el write-back del primer corte es client-side; queda como residual la opción backend para la Capa 2·C íntegra.

## D-011 · §6.3 — Modelo de datos de cargas/combinaciones (V2)

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM · **FIRMA: ✅**
- **Decisión:** representar apoyos, cargas, casos y combinaciones como **Pset Aqyra `Pset_AqyraStructural_*`** *diff-able* en estado `proposal`, sin depender de entidades `IfcStructuralLoad*` nativas; diferir a ≈V3 la emisión nativa para interoperar con el motor.
- **Evidencia:** entradas sin cargas/apoyos (`HILO-V2_evidencia-modelo-analitico.md` §2); `HILO-V2_evidencia-cruzada_calculo.md` §3 (campos mínimos del cálculo: acciones —incl. sismo ac—, γ/ψ, apoyos, casos, combinaciones ELU/ELS+sísmica).
- **Acciones que dispara:** diseñar el esquema del Pset con esa lista de campos mínima.

## D-012 · §6.4 — Extensión del contrato `AqyraViewer` (V2)

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM · **FIRMA: ✅**
- **Decisión:** añadir una sub-API **`pre`** de solo lectura (espejando `bcf`/`ids`), datos en `proposal`, versionada **SemVer MINOR**: `getStructuralModel()`, `listSupports()/setSupport()`, `listLoads()/addLoad()/removeLoad()`, `listLoadCases()/listCombinations()`.
- **Evidencia:** patrón `bcf`/`ids` y `DataState` ya en `publico/embed/src/contract.ts`; `HILO-V2_evidencia-cruzada_calculo.md` §3 (qué expone `getStructuralModel`: miembros con eje y sección, nudos, apoyos, materiales).
- **Acciones que dispara:** extender `contract.ts` (MINOR), implementar la sub-API en el primer corte, conectar la skin Calculista (`publico/demo/src/calculista.ts:324`).

---

## D-013 · Write-back del anejo por *append* STEP (no `SaveModel`) (V2)

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM · **FIRMA: ✅**
- **Decisión:** el write-back de cargas/apoyos (D-010) se persiste **añadiendo** el anejo Aqyra como líneas STEP al final del bloque `DATA` del IFC **original**, dejándolo intacto (diff **mínimo y reversible**). **No** se usa `SaveModel` de web-ifc para esto: re-serializa todo el fichero y produce un diff enorme, contrario al principio "texto diff-able". El anejo se delimita con marcadores y la reescritura es **idempotente** (`stripStructuralPset(append(x)) === x`).
- **Evidencia:** `publico/visor/src/ifc-loader.ts` (`appendStructuralPset`/`stripStructuralPset`); test `publico/visor/test/pre-structural.test.ts` (restaura el original byte a byte; no duplica el anejo). Concuerda con D-002 (client-side, sin servidor) y D-010.
- **Acciones que dispara:** mantener el patrón `SaveModel` (reescritura completa) solo para el saneamiento espacial de V1 (`reassignSpatial`), donde sí se edita el grafo del modelo; el pre-proceso usa append.
- **Residual:** ~~confirmar en Windows que web-ifc reparsea el anejo con comentarios STEP `/* */`~~ **CONFIRMADO ✅** (2026-06-24): el test de round-trip reabre el IFC con anejo y lee el Pset sin problema.

## D-014 · Tolerancia de coincidencia de nudos (V2)

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM · **FIRMA: ✅**
- **Decisión:** fundir extremos de barra en un mismo nudo con **tolerancia por defecto 150 mm** (revisada al alza desde 20 mm a la vista de Decopak HQ: los extremos derivados de la geometría concurren separados por el canto de los elementos), **configurable** por llamada (`deriveStructural({ tolerance })`). El filtro de "eje nulo" se **desacopla** de la tolerancia (umbral fijo 1 mm) para que subirla no borre barras cortas.
- **Evidencia:** `publico/visor/src/idealize.ts` (`deriveModel`, clustering por rejilla de tolerancia); test `idealize.test.ts` (dos barras colineales → 3 nudos). Verificado visualmente sobre Decopak HQ (2026-06-24).
- **Partido en intersecciones (implementado 2026-06-24):** dos mecanismos en `idealize.ts`, ambos como `proposal` revisable: (1) `splitAtIntersections` parte una barra donde el **extremo de otra** cae sobre su vano (T: vigueta apoyada en viga, pilar pasante por planta); (2) `connectCrossings` inserta nudo en el **cruce INTERIOR** de dos barras cuando **ambas son paralelas a un eje global y ortogonales** entre sí (tirante vertical × viga de forjado, rejilla de forjado) y parte ambas. Conservador: las barras **inclinadas** quedan fuera, así que NO conecta las **aspas** de arriostramientos/cerchas (que cruzan sin nudo real). Tests: `idealize.test.ts` (T → 3 miembros; tirante×forjado → 4; aspa inclinada → no conecta; flags para desactivar).
- **Residual (refinamiento, no bloquea):** (a) el partido depende de la tolerancia — si la viga de perímetro es más ancha que `tol`, la vigueta no la corta; ajustable. (b) **Miembros no rectos** (vigas en L/quebradas): el PCA da un único eje recto (cuerda) que "corta" el quiebro → se verá "doblado"; requeriría derivar una **polilínea** por miembro. (c) **Analítico de superficies** (muros/losas como lámina o diafragma) y **tipificación de uniones** (rígida/articulada) — incremento siguiente.

## D-015 · Convenio de unidades y signos de carga (provisional V2) (V2)

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM · **FIRMA: ✅ (provisional) — ⚠️ SUPERADA por D-018 (2026-06-25)**
- **Decisión (provisional para el primer corte):** magnitud en **kN** (puntual) / **kN·m⁻¹** (distribuida), **positiva**; el **sentido** lo fija `direction` (eje global `x`/`y`/`z`); la carga **gravitatoria** por defecto es `direction="y"` hacia **−Y**. Todo en estado `proposal`.
- **Evidencia:** `publico/openbim/src/index.ts` (`PreAdapter`), `publico/embed/src/element.ts` (`addDistributedLoad`), skin `calculista.ts`.
- **Cierre:** ~~confirmar el convenio de signos al conectar el motor (C5)~~ **RESUELTO por D-018 (2026-06-25):** global **Z-up**, gravedad **−Z** (deja sin efecto el *default* −Y de aquí); ejes locales por rol; N>0 tracción; V/M/T canónico PyNite. La acción 1 de D-018 corrige el `direction` por defecto en el código.

## D-016 · Idealización de superficies: diafragma/lámina seleccionable (V2)

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM · **FIRMA: ✅**
- **Decisión:** derivar losas/muros como superficie idealizada (plano por PCA, contorno, normal), con `kind` **editable** por el ingeniero: **losa→diafragma** (rigidez en plano + nudo maestro), **muro→lámina** por defecto. La **precisión FE** de la lámina la calcula el motor (V3); en V2 es malla-propuesta revisable. Mecánica = cebo; qué muro es pantalla = criterio (V4).
- **Evidencia:** `publico/visor/src/idealize.ts` (`deriveSurfaces`), `openbim` (`StructuralSurface`, `listSurfaces`/`setSurfaceKind`), tests. Bump `@aqyra/embed` → 0.3.0.

## D-017 · Correcciones de idealización de superficie (revisión desde el cálculo)

- **Fecha de firma:** 2026-06-24 · **Firmante:** JM · **FIRMA: ✅ (parcial; ver diferidos)**
- **Indicación A (área de carga):** el área de reparto de carga es la **planta REAL** (envolvente convexa), no el rectángulo del diafragma; si no, F=q·A_rect > q·A_real → sobrecarga. *Implementado:* `area` (real) y `extentArea` (rectángulo) en la superficie; el contorno dibujado pasa a ser el real. *Diferido:* aplicar q sobre el área → cargas en vigas de borde; separar formalmente diafragma-rigidez de superficie-de-carga al introducir cargas de área.
- **Indicación B (núcleo):** un núcleo es una **caja de 4 muros**, no un plano; colapsarlo pierde 3 muros, la torsión de sección cerrada y la flexión biaxial. *Implementado:* (1) **detección de no-planaridad** (`planar=false`) → no se falsea como una lámina; rojo + cartel persistente. (2) **Columna-cajón equivalente** (`deriveCores`): el núcleo no-plano se idealiza como UNA barra vertical con propiedades de la **sección HUECA** (A, Ix, Iy = exterior − interior, contorno interior por offset del espesor supuesto) + **J de Bredt** (sección cerrada) — coherentes entre sí; se muestra también la sección bruta para comparar. Visible en magenta, con sus valores en un **panel persistente** de la skin (comando "columna-cajón"). Es la alternativa de comparación pedida por JM (ruta b). *Diferido:* descomponer en **4 láminas** (requiere normales/triángulos de la malla); **armado** → V3 (dos llaves).
- **Indicación B-bis (núcleo autorado por caras):** un núcleo dibujado como **muros planos sueltos** (p. ej. EST-01: NC1/NC2/NC3, caras Sur/Este/Norte/Oeste) NO dispara el flag no-plano (cada cara es plana) → pasaría como láminas sueltas. *Implementado:* **detección de grupo-núcleo** (`groupCores`) por adyacencia de esquinas (union-find) que reconoce las caras como **un** núcleo y lo clasifica **caja cerrada** (todas las caras con ≥2 vecinas) o **U/L abierta**; se resalta en el visor (teal/ámbar) y se informa. Resuelve la diferencia entre los dos modelos de Decopak (EST-02 = núcleo en un `IfcWall` hueco → no-plano/rojo; EST-01 = núcleo por caras → grupo reconocido). **4 láminas cosidas (implementado 2026-06-24):** `buildCoreShell` malla cada cara del grupo y **funde los nudos coincidentes** (tol) → las caras **comparten los nudos de las aristas de esquina** = malla shell ÚNICA del núcleo (las 4 láminas trabajan conectadas). Comando "4 láminas"/"cose el núcleo" en la skin (teal cerrado / ámbar abierto). Verificado: caja → 16 nudos de esquina compartidos. *Diferido:* (a) la **resolución FE** del shell cosido la calcula el motor (V3); (b) el caso **EST-02** (núcleo en UN `IfcWall` hueco) necesita además **partir ese elemento en caras** por clustering de triángulos/normales (refactor para llevar la topología a la derivación) — pendiente.
- **Indicación C (cajón de hormigón grueso, p. ej. depósito enterrado):** muros/losas **gruesos** (depósito: muro e=0,50 h=4,35 → t/luz≈0,12; losas 0,60–0,70) donde la **lámina delgada (Kirchhoff) no aplica**. *Implementado:* detección **GRUESO** (`thick` = espesor>0,25 m y t/luz>0,1) → se resalta en **rosa** y se avisa ("→ sólido/placa gruesa"). Los `IfcWall` del depósito **sin perfil extruido** (geometría facetada) producen planos PCA **ladeados** ("muros torcidos"): son **artefactos de derivación** y, como todo lo derivado, salen como `proposal` revisable (D-008), nunca como malla cerrada dada por buena. **Detector + corrección de "plano torcido" (implementado 2026-06-24):** un `IfcWall` es VERTICAL en realidad; si el plano PCA sale **ligeramente ladeado** (artefacto de geometría facetada, |normal·Z|<0,7) se **VERTICALIZA** (se fuerza la normal a horizontal y la lámina sale recta) — así el analítico no "gira" un muro que físicamente es vertical. Si el muro queda **muy tumbado** (|normal·Z|>0,4 tras intentar verticalizar, o >0,7 de origen) se marca `skewed` → artefacto/posible muro real, contorno **rojo** y aviso, revisable como `proposal`. *Diferido:* cerrar el cajón conectando planos en aristas/offsets rígidos = parte del cosido FE (motor, V3).
- **Gobierno:** todas son decisiones de idealización (fuente de error, D-008) → salen como `proposal` revisable; el resultado definitivo (esfuerzos/armado) lo sella la QA con el FEM real en V3.
- **Evidencia:** `HILO-V2` revisión desde el cálculo (2026-06-24); `publico/visor/src/idealize.ts` (`deriveSurfaces`: hull/área/planaridad); tests `idealize.test.ts` (Indicación A y B).

---

## D-018 · Convenio definitivo de ejes y signos (sustituye D-015) (V3)

- **Fecha de firma:** 2026-06-25 · **Firmante:** JM · **FIRMA: ✅**
- **Decisión:** **Global Z-up dextrógiro**, gravedad **−Z**; el modelo analítico y el contrato C5 hablan **Z-up** (el Y-up del visor en Three.js es solo presentación, no parte del contrato). **Ejes locales de barra por ROL** (`axis` longitudinal i→j / `strong` eje fuerte mayor I / `weak` eje débil menor I), con **mapeo explícito** a PyNite (x / z-strong / y-weak) y a Eurocódigo EN 1993 (x / y-y mayor / z-z menor) — **nunca se pasa la letra cruda entre capas**, para no cruzar fuerte↔débil. **N>0 = tracción** (compresión negativa). **V/M/T en la convención positiva canónica de PyNite** (productor + segunda llave), alineada por el adaptador C5. **Deformada y reacciones** en componentes globales (reacciones → `IfcStructuralReaction` del IFC StructuralAnalysisDomain). ***Releases*** de extremo: 6 GdL/extremo `{ux,uy,uz,rx,ry,rz}×{i,j}`, **true = GdL LIBERADO**; el adaptador C5 **invierte la polaridad** frente a `Restraints` (true = restringido) y al llamar a `def_releases` de PyNite (rótula = liberar giros de flexión `strong`/`weak`).
- **Bifurcación firmada por JM:** vertical global **+Z** (opción recomendada; IFC-nativa, mínimo cambio). Descartada la alternativa +Y (frame del visor).
- **Evidencia:** PyNite docs — ejes locales x/z-strong/y-weak, `def_releases` true=liberado, cargas global MAYÚSCULA / local minúscula (verificado 2026-06-25); EN 1993-1-1 — y-y mayor / z-z menor, `My,Ed` de eje fuerte (verificado 2026-06-25); IFC StructuralAnalysisDomain — `IfcStructuralReaction`/`IfcStructuralResultGroup` (IFC4.3, verificado 2026-06-25); código V2 — `idealize.ts` deriva en Z-up (`normal[2]`), `openbim` `Restraints` true=restringido. Detalle y tablas de mapeo en `HILO-V3_para-firma_D-018-signos.md`.
- **Sustituye:** **D-015** (convenio provisional kN / −Y) → marcada superada.
- **A confirmar en implementación (distinguido de lo verificado):** el signo exacto de las flechas de V/M/T se ancla contra el diagrama `sign_convention.png` de PyNite al cablear el adaptador C5; aquí se fija la **regla** (PyNite canónico + N>0 tracción), no el diagrama.
- **Acciones que dispara:** (1) corregir el *default* de carga gravitatoria de `direction="y"`/−Y a **−Z global** en `PreAdapter`/`element.ts`/`calculista.ts`; (2) el contrato C5 (D-019) expone ejes por rol + esquema de resultados con su signo y estado de dato; (3) el adaptador C5 (`privado/`) implementa la traducción de letras (rol→PyNite→EC), la inversión de polaridad de *releases* y la alineación de signo de PyNite; (4) añadir un **test de signos** (ménsula patrón: carga −Z → tracción arriba, flecha −Z, reacción +Z y M de empotramiento de signo conocido) como red de la segunda llave.

---

## D-019 · Contrato C5 — forma de entrada y de salida (V3)

- **Fecha de firma:** 2026-06-25 · **Firmante:** JM · **FIRMA: ✅**
- **Decisión:** congelar el contrato **C5** (puente al `motor-fem 0.1.0` anclado, adaptador en `privado/puente-calculo/`; SemVer, MAJOR = rotura). **Entrada** = `StructuralModel` (frame Z-up, D-018) extendido con `member.releases` (D-020), **propiedades numéricas de sección/material** (A, I_strong, I_weak, J, E, G, fy/fck — ejes por rol), **combinaciones estructuradas** `{caso: factor}` (≅ `IfcRelAssignsToGroupByFactor`; la cadena `expression` se conserva solo para mostrar) y `surface.areaLoad` (≅ Indicación A, D-017). **Salida** = esquema de resultados con **`state: DataState`** (D-021, nace `computed`): `MemberResult` (N/V/M/T por x i→j, deformada local, aprovechamiento, signos D-018, N>0 tracción), `NodeResult` (desplazamientos globales + reacciones ≅ `IfcStructuralReaction`), `SurfaceResult` (membrana n_x/n_y/n_xy + placa m_x/m_y/m_xy), **envolventes** con combinación gobernante; mapeo a `IfcStructuralResultGroup`. **Frontera:** tipos públicos (entrada + resultados); adaptador y motor **privados**.
- **Bifurcaciones firmadas por JM:** **C.1.a** — las propiedades de sección/material se resuelven **en el lado Aqyra** (el motor recibe números listos, no necesita catálogo → motor reutilizable). **C.2.a** — combinación como **mapa `{caso: factor}`** (espeja `IfcRelAssignsToGroupByFactor`; el motor no parsea texto). **C.3.a** — la **carga por área** entra ya en el esquema C5 (`surface.areaLoad`) y el adaptador la **reparte por área tributaria real** a vigas de borde/nudos, separando diafragma-rigidez de superficie-de-carga (cierra la Indicación A). **C.4 — servicio de cálculo: SÍ** — el post-proceso introduce un **servicio de cálculo privado** (el motor es Python/PyNite, no corre en el navegador); el **visor (cebo) sigue sin-servidor para ver**, solo el cálculo llama al servicio. Coherente con D-002 (que aplica al visor) y D-010 (backend reservado); es el anzuelo, no el cebo.
- **Evidencia:** IFC StructuralAnalysisDomain — `IfcStructuralLoadGroup`/`IfcLoadGroupTypeEnum`, `IfcRelAssignsToGroupByFactor` (casos→combinación con factor), `IfcStructuralResultGroup`/`IfcStructuralReaction` (verificado 2026-06-25); PyNite — esfuerzos por dirección local, envolventes por `combo_tags` (verificado 2026-06-25); D-018/D-020/D-021; código V2 — `StructuralModel`, `SectionRef` solo strings, `Combination.expression` string. Detalle en `HILO-V3_para-firma_D-019-contrato-C5.md`.
- **Acciones que dispara:** (1) extender los tipos públicos de entrada (sección/material numéricos, `releases`, `terms`, `areaLoad`) y definir los tipos públicos de **resultado** + bump SemVer del contrato; (2) implementar el **adaptador C5** en `privado/puente-calculo/` (serialización modelo→motor, traducción ejes/signos/releases D-018/D-020, *solve*, mapeo de resultados con estado, reparto de `areaLoad`); (3) levantar el **servicio de cálculo** privado (C.4); (4) `write-back` de resultados al IFC como `IfcStructuralResultGroup`; (5) caso patrón end-to-end (Decopak HQ: una combinación ELU → deformada + aprovechamientos `computed`) como prueba del contrato.

---

## D-020 · Tipificación de uniones (rígido/articulado / *releases*) (V3)

- **Fecha de firma:** 2026-06-25 · **Firmante:** JM · **FIRMA: ✅**
- **Decisión:** uniones **rígidas por defecto** (sin *release* = transmite N/V/M/T); extremos **liberables a articulado** por el ingeniero. *Release* por extremo i/j en **ejes locales por rol** (D-018), 6 GdL, **true = liberado**; **rótula = liberar `mStrong`+`mWeak`** (los dos flectores), **biarticulada = rótula en ambos extremos**. Se prohíbe liberar axil o torsión en los dos extremos a la vez (inestabilidad, PyNite). Modelo de datos: `StructuralMember.releases?` + `PreApi.setRelease/listReleases` (contrato **MINOR**); persistencia como línea `release:{id}` en `Pset_AqyraStructural` (*append* D-013), espejando `IfcRelConnectsStructuralMember.AppliedCondition`. UI/NL en la skin Calculista con glifo de rótula, todo `proposal`. **Semirrígido y clasificación de nudos EC3 → diferidos** (campo `stiffness?` reservado; criterio = anzuelo, V4).
- **Bifurcación firmada por JM — default de `brace`: opción C.b (ARTICULADO).** Las barras clasificadas como aspa/arriostramiento (`brace`) **nacen biarticuladas** (rótula en ambos extremos = solo axil), por comodidad práctica (casi siempre lo son). **Excepción pragmática acotada:** es el ÚNICO auto-default por tipología que entra en la mecánica del cebo; NO abre la puerta a más auto-criterio (el resto de la idealización de uniones sigue siendo autorado explícito; la sugerencia de uniones por norma/corpus sigue siendo anzuelo, V4). El ingeniero puede revertir cualquier aspa a rígida (es `proposal` editable).
- **Evidencia:** IFC StructuralAnalysisDomain — `IfcRelConnectsStructuralMember.AppliedCondition` en `ConditionCoordinateSystem` de ejes locales; articulado=libre giro, rígido=transmite momento (IFC4/4.3, verificado 2026-06-25); PyNite `def_releases` 6 GdL/extremo true=liberado, advertencia de inestabilidad por liberar axil/torsión en ambos extremos (verificado 2026-06-25); D-018 (mecánica de *releases* y ejes por rol); código V2 (`StructuralMember` sin releases hoy; `kind` ya incluye `brace`). Detalle en `HILO-V3_para-firma_D-020-uniones.md`.
- **Acciones que dispara:** (1) extender `StructuralMember`/`PreApi` (`publico/openbim`) con `releases`/`setRelease`/`listReleases` + bump MINOR de `@aqyra/embed`; (2) **default articulado para `kind="brace"`** al derivar el modelo (marcado `proposal`, revertible); (3) codificar `release:{id}` en el anejo y su round-trip; (4) UI/NL de rótula en la skin Calculista (glifo + comandos), con la regla de estabilidad; (5) test: barra biarticulada → solo axil (M nulo en extremos) y aspa derivada → articulada por defecto, en el caso patrón.

---

## D-021 · Estado de dato en el visor (dos llaves visibles) (V3)

- **Fecha de firma:** 2026-06-25 · **Firmante:** JM · **FIRMA: ✅ (C.1.a + C.2)**
- **Decisión:** el visor representa el estado de cada dato con un **modelo que refleja las dos llaves** —`proposal` (input) / `computed` (motor, 0 llaves) / `qa-passed` (1.ª llave: QA PyNite) / `verified-signed` (2.ª llave: firma JM)— mapeado a ISO 19650 (S0 / S0 / S3 / A) para alinear con el CDE Aqyra. **Regla visual binaria:** solo `verified-signed` recibe el tratamiento «certificado» (verde/limpio); todo lo demás se ve provisional (chip de estado + marca de agua «NO VERIFICADO»). **Enforcement:** el verde está condicionado a `state==="verified-signed"`, estado que **solo acuña el flujo de firma de `privado/`** — el render público nunca lo produce. Cambio de contrato **MINOR** (añade `computed`/`qa-passed` a `DataState`; `PreDataState` espeja).
- **Bifurcación firmada por JM — C.1 granularidad: opción C.1.a (4 ESTADOS).** `proposal`/`computed`/`qa-passed`/`verified-signed`, que hacen legibles las dos llaves (qué falta: QA o firma) y casan con ISO 19650 (S0/S0/S3/A). La frontera visual sigue siendo binaria (solo `verified-signed` = certificado).
- **Bifurcación firmada por JM — C.2 guarda de exportación: SÍ.** Toda exportación de un resultado no firmado (imagen/PDF/BCF) **estampa la marca de estado** («NO VERIFICADO») para cerrar la fuga fuera de pantalla; solo lo `verified-signed` puede exportarse sin marca.
- **Evidencia:** ISO 19650 — códigos S (WIP/Compartido, no contractual) vs A/B (Publicado, contractual tras sign-off); S3 = revisión, antesala del sign-off (verificado 2026-06-25); contrato V2 — `DataState` ya reserva `proposal`/`verified-signed` (`embed/src/contract.ts`); skin Calculista — `warnBanner` persistente sin ✕ (`demo/src/calculista.ts`). Detalle en `HILO-V3_para-firma_D-021-estado-dato.md`.
- **Acciones que dispara:** (1) extender `DataState`/`PreDataState` con `computed`/`qa-passed` + bump MINOR de `@aqyra/embed`; (2) chip de estado + marca de agua + leyenda en el visor/skin, con el verde *gated* a `verified-signed`; (3) guarda de exportación que estampa estado en toda salida no firmada (C.2); (4) mapeo estado↔ISO 19650 compartido con `cde-audit`; (5) test: un layer `computed` NUNCA renderiza con estilo certificado; solo el *write-back* firmado vira a verde.

---

## D-022 · Alcance del armado en V3 (V3)

- **Fecha de firma:** 2026-06-25 · **Firmante:** JM · **FIRMA: ✅**
- **Decisión:** el **suelo de V3** (cumple el DoD del roadmap) entrega, para todo el modelo y por combinación, **esfuerzos N/V/M + deformada + reacciones** con su `DataState`, y para **acero** el **aprovechamiento EC3** (interacción N-M-V, pandeo) + **«qué no cumple»**. El **armado EC2** (elementos de hormigón + **núcleo** por **modelo sándwich** —EN 1992-2 Anejo LL / EN 1992-1-1:2023— o columna-cajón equivalente, según la idealización elegida en V2: D-016/D-017) es la **capa pesada**, **escalonada dentro de V3** (C.2.a). Distinción clave: en hormigón sin armadura en el IFC, **verificar exige dimensionar** (el «qué no cumple» del hormigón vive en el armado). Todo armado es resultado **bajo dos llaves** (D-023), en entorno certificado (`privado/`); la mecánica es cálculo, el criterio normativo sigue siendo anzuelo (V4).
- **Bifurcaciones firmadas por JM:** **C.1 — suelo de V3 = verificación + «qué no cumple»: SÍ** (esfuerzos + deformada + aprovechamiento EC3 acero + «qué no cumple»; cierra el DoD del roadmap). **C.2.a — armado EC2 escalonado dentro de V3:** primero el lazo end-to-end con verificación y las dos llaves probadas; **después** el armado (elementos EC2 + núcleo sándwich/columna-cajón) como incremento de V3; el hormigón obtiene su «qué no cumple» en ese incremento.
- **Evidencia:** roadmap V3 DoD (deformada + aprovechamiento EC3 + elementos al límite = verificación); EN 1992-2 Anejo LL / EN 1992-1-1:2023 — **modelo sándwich** de 3 capas para armar láminas/núcleo desde esfuerzos de membrana/placa (verificado 2026-06-25); EC3 — interacción y pandeo para verificación de acero; D-016/D-017 (idealización del núcleo), D-019/D-021/D-023. Detalle en `HILO-V3_para-firma_D-022-armado.md`.
- **Acciones que dispara:** (1) implementar el **suelo de V3** (esfuerzos/deformada/reacciones + aprovechamiento EC3 + «qué no cumple») sobre el contrato C5 (D-019); (2) planificar el **armado EC2** (elementos + núcleo sándwich/columna-cajón) como **incremento** posterior dentro de V3 (C.2.a); (3) pintar aprovechamiento/armado con `DataState` (D-021) y bajo QA (D-023); (4) caso patrón: Decopak HQ → aprovechamiento EC3 de las barras de acero al límite (DoD), y un elemento/núcleo de hormigón armado de ejemplo en el incremento de armado.

---

## D-023 · Carril de QA con PyNite (segunda llave) (V3)

- **Fecha de firma:** 2026-06-25 · **Firmante:** JM · **FIRMA: ✅**
- **Decisión:** la 1.ª llave (`qa-passed`) la produce una **QA independiente** del productor: `motor-fem` (productor → `computed`) y **PyNite** (oráculo QA, **código independiente** → `qa-passed`); la 2.ª llave es la **firma de JM** (→ `verified-signed`). La QA reconcilia sobre el mismo modelo: **equilibrio global** (gate de pura estática), reacciones, desplazamientos clave, esfuerzos/envolventes y aprovechamientos. **`qa-fail` bloquea** la firma y **expone** la discrepancia (no degrada en silencio); el visor mantiene el resultado `computed` con marca de QA fallida. Corre en **entorno certificado** (`privado/`, carril *Estructurando 2.0*), por vía de código distinta del productor; la auditoría guarda **ambas ejecuciones + la reconciliación**. `qa-passed` es necesario, no suficiente: solo la firma sella `verified-signed`. Anclado en el **chequeo independiente Cat 3** (BS 5975).
- **Bifurcaciones firmadas por JM:** **C.1 — independencia: SÍ** (PyNite debe ser código distinto del solver de `motor-fem`; si lo compartieran, la QA usa otro motor/método → verificación pendiente). **C.2 — tolerancias: propuesta aceptada** (equilibrio ~0,1 %; reacciones y desplazamientos ±2–5 %; esfuerzos y aprovechamientos ±5 %; a afinar contra Decopak HQ). **C.3 — equilibrio como gate previo: SÍ** (chequeo de pura estática Σreacciones=Σacciones antes del re-cálculo completo). **C.4.a — ante `qa-fail`: bloqueo con anulación documentada** (bloquea por defecto; JM puede anular solo con justificación escrita que queda en la auditoría).
- **Evidencia:** chequeo independiente Cat 3 (BS 5975) — revisor organizativamente independiente, cálculos propios, no peer review (verificado 2026-06-25); PyNite — re-cálculo independiente, envolventes por `combo_tags` (verificado 2026-06-25); repo — `motor-fem` productor vs PyNite oráculo QA (`HILO-V2_cierre-y-arranque-V3.md` §3, `DECISIONES.md` D-009 salvedad, `privado/README.md` dos llaves); D-018/D-019/D-021. Detalle en `HILO-V3_para-firma_D-023-qa-pynite.md`.
- **Acciones que dispara:** (1) verificar que `motor-fem` y PyNite no comparten núcleo de solver (C.1); (2) implementar la QA en `privado/` (re-cálculo PyNite + chequeo de equilibrio + reconciliación con tolerancias C.2/C.3); (3) gate `qa-passed`/`qa-fail` cableado al estado de dato (D-021) y a la guarda de firma; (4) registro de auditoría (ambas ejecuciones + reconciliación); (5) caso patrón: Decopak HQ, una combinación ELU → `motor-fem` `computed` → PyNite reconcilia → `qa-passed`, y un caso forzado de discrepancia → `qa-fail` que bloquea.

---

## D-024 · P1 Hito 2 (modo edición) — capa de overrides (datos) + puente gesto→datos

- **Fecha de firma:** 2026-06-29 · **Firmante:** JM · **FIRMA: ☐ Pendiente**
- **Decisión:** abrir el modo edición por la **capa de datos (overrides)** antes que el viewport. La manipulación directa entra como **entrada** —`BuildingInput.overrides: Record<code,{dx,dy,rotDeg}>`— que `buildModel` aplica tras generar (gira sobre el centroide, luego traslada; el punto es invariante al giro). Es render-agnóstica, determinista y golden-able; el puente emite las coordenadas ya movidas → **frontera-cero con C1** (sin bump). El hueco de forjado que perfora la rampa queda **acoplado** (`derivedFrom`) y se mueve con ella. El **puente gesto→datos** `deriveOverride` (inverso de `applyOverride`) cierra el contrato que cualquier renderer debe cumplir: el gizmo deriva el dato del antes/después, no lo inventa.
- **Slice cerrado por JM:** overrides primero · viewport **Three híbrido** (Pieza 2) · familias con **identidad propia** · gesto **trasladar + girar**.
- **Hallazgo de frontera:** el **giro de esta familia es frontera-cero** (rampa/carpintería = `línea`, forjados/huecos = `polígono`: la orientación vive en las coordenadas que el cebo ya autora). La cota **z se difiere** (derivada del nivel, no del placement 2D). Único caso que pediría dato nuevo en `alto.json`: giro de pilar (puntual con sección) → fuera de la familia editable.
- **Reservado a JM (residual):** el **núcleo** es composite/driver → editar solo elementos de código único ahora vs. implementar override de driver ya (a decidir al cablear la Pieza 2).
- **Evidencia (Llave 1):** suite golden **verde** — `pnpm test` en `publico/demo` (run de JM 2026-06-29) = **11 archivos / 115 tests passed**, `overrides.golden.test.ts` (11) verde y los 10 previos **sin regresión** (`derivedFrom` invisible al snapshot). NUEVO: `test/derive-override.golden.test.ts` (ida-y-vuelta de `deriveOverride`) — núcleo verificado verbatim, **pendiente de re-run de la suite por JM**. Código: `publico/demo/src/model.ts` + `test/overrides.golden.test.ts` + `test/derive-override.golden.test.ts`. Detalle en `P1_para-firma_modo-edicion-overrides.md`.
- **Estado del viewport (Pieza 2):** módulo Three **preparado** en `publico/demo/proposals/edit-viewport.ts` (`EditViewport`: picking + `TransformControls` → escribe `overrides`), **fuera de `src/`** para no romper el build (importa `three`, aún no dep del demo). **NO verificado en pantalla** (sandbox sin GL).
- **Acciones que dispara:** (1) cablear la Pieza 2 — `pnpm add three @types/three` en `publico/demo`, mover el módulo a `src/`, enganchar en `diseno.ts`, **probar en pantalla**; (2) coordinar el gesto con el hilo de usabilidad de skins (un gesto = lo mismo en todas las skins); (3) resolver el residual del núcleo-como-driver.

---

## Pendientes que bloquean el arranque de código

| # | Pendiente | Bloqueado por | Dueño |
|---|---|---|---|
| 1 | ~~Copiar `HILO-1` al repo~~ ✅ hecho 2026-06-24 | — | — |
| 2 | ~~Tags reales en `versions.lock`~~ ✅ anclados (N1.1, 0.x). Falta el **cierre formal**: golden verde + tag GPG firmado | suite golden + firma de release | JM (Núcleo) |
| 3 | ~~Elección de marca~~ ✅ Aqyra (D-004); queda fijar relación con Aqyra-CDE y verificación autoritativa de marca/dominio | EUIPO/USPTO/WHOIS | JM |
| 4 | Check legal de `publico/` — evidencia ✅ (`CHECK_LICENCIAS_publico.md` + `THIRD-PARTY-NOTICES`); falta validación jurídica + escaneo del árbol real de V1 | jurista + dep-tree de V1 | JM / jurista |

---

*Procedencia: registro de decisiones · proyecto Entorno/Aqyra · firmado por JM 2026-06-24 (D-001..D-017) y 2026-06-25 (D-018..D-023, V3) · evidencia preparada por la IA. La IA opera; JM firma.*
