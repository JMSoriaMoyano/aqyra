# C4 — Decisiones de contrato (ancladas)

> Resueltas con JM el **2026-07-02** (OK explícito), antes de tocar código. Complementan los
> ADRs de la ficha (`../../../../Aqyra-Raiz/C4_federacion.md §2.5`), que **no se reabren**:
> QA por IDS estándar · preservar procedencia/GUIDs · EPSG + punto base DECLARADO ·
> clash fuera de C4 v1 · parser sucio = tarea 1.3.

## D1 · Forma del Maestro — AMBOS, manifiesto como fuente de verdad

El artefacto autoritativo del Maestro es el **manifiesto de federación**
(`maestro-manifiesto.schema.json`): refs a los IFC fuente (por hash), transformación
EPSG/punto-base por modelo, procedencia por disciplina y política de GUIDs. Es lo único
esquematizable y lo único honesto con los ADRs (no fundir GUIDs, preservar procedencia).
El **IFC federado** se declara en el contrato como **derivado determinista** del manifiesto —
su "esquema" es IFC4X3, no JSON — y su identidad la cubrirá la golden cuando exista el
service (tarea 1.1). El visor navega el IFC; la verdad vive en el manifiesto.

## D2 · Alcance del esquema v0.1 — 3 esquemas propios + BCF por referencia

`reglas-federacion.schema.json` (entrada) · `maestro-manifiesto.schema.json` (salida) ·
`informe-qa.schema.json` (salida: pass/fail por requisito IDS + estados S0–S7 + incidencias).
El **BCF no se re-esquematiza**: se referencia **BCF 3.0** de buildingSMART y se fija la
versión aquí y en `versions.lock`. Re-esquematizar un estándar es deuda gratuita.

## D3 · Golden C4-FED-01 — sintético con narración→IFC

Dos disciplinas del mismo edificio pequeño (**ARQ**: muros+losa+ascensor · **EST**:
pilares+losa+zapatas), compiladas con `engines/ifc` y **congeladas byte a byte** como
entrada. Determinista, sin dependencias externas. El IFC sucio es la tarea 1.3 — no entra
aquí. El caso incluye **requisitos IDS que fallan adrede** para que el informe esperado
tenga pass Y fail (y el futuro BCF tenga materia).

## D4 · Runner — extender `aqyra_golden` con dispatch por contrato; C4 nace ANCLADO

Hallazgo que lo hace obligatorio: `discover_cases()` hace glob de `C*` — un caso C4 sería
recogido por el runner actual y tratado como C1 (compile) → ROJO. Refactor mínimo:
`--schema-only` descubre y meta-valida **todos** los `packages/contracts/*/*.schema.json`;
los casos se despachan por carpeta (`C1/` → compile+recompute, intacto; `C4/` → **modo
anclado**). El modo anclado, sin service, verifica lo verificable: los ficheros del caso
conforman sus esquemas, los IFC congelados coinciden con sus hashes declarados, y la
coherencia interna (requisitos del informe ⊆ requisitos del IDS; modelos del manifiesto =
modelos de las reglas = ficheros de entrada). El recompute contra el service se conecta en
1.1 **contra el mismo expected** (misma costura que C1 en Fase 0 → Fase I).

## D5 · IDS del golden — pack nuevo `data/packs/ids/`

Fichero `.ids` (**IDS 1.0** estándar, versión fijada) + `pack.json` conforme a
`data/packs/pack.schema.json` (familia `ids` ya prevista) + golden de pack por hash, según
`FUNDACION_C6_golden_y_packs.md`. 5 requisitos comprobables sobre el caso, de los que
1–2 fallan adrede. Anclado en `versions.lock [packs.ids]`.

---

> Bloque del hilo 2.2 (service v0, tarea 1.1). Resueltas con JM el **2026-07-02**
> (OK explícito), antes de tocar código. D1–D5 no se reabren.

## D6 · IFC federado derivado — NO en v0 (v0 = manifiesto + informe)

La golden anclada no ancla ningún IFC derivado; emitir una salida sin oráculo rompe el
espíritu contract-first. El esquema deja `ifc_derivado` opcional adrede (D1: la verdad
vive en el manifiesto). El IFC derivado llega en v0.x como tarea propia, con su anclaje
decidido entonces (md5 en expected: decisión explícita con JM).

## D7 · Motor de validación IDS — implementación PROPIA mínima sobre ifcopenshell

Solo se necesitan 4 facets (entity, classification, property, attribute+pattern) y el
terreno ya está mapeado por el oráculo manual (material en
`Pset_Estructurando_Spec.Material`, no como asociación IfcMaterial; `IsExternal` en
`Pset_WallCommon`). `ifctester` sería superficie ajena que anclar y cuya semántica podría
discrepar del oráculo en los bordes — un desajuste obligaría a investigar SU comportamiento,
no el nuestro. R4-GEORREF (`origen='modulo'`) va aparte en ambos casos: presencia de
`IfcMapConversion` + `IfcProjectedCRS`. Puerta abierta a adoptar ifctester en v1 si el
pack crece más allá de estos facets.

## D8 · BCF en v0 — `bcf.emitido=false` (la emisión de topics es 1.2)

El informe declara las incidencias (con GUIDs) y el bloque `bcf` queda como en el expected
congelado: `version 3.0, emitido: false`. La emisión de topics BCF 3.0 reales es la tarea
1.2 (QA/IDS→BCF). Cambiarlo ahora obligaría a tocar el expected (prohibido).

## D9 · Empaquetado — paquete uv del workspace `aqyra-federacion`

`services/federacion/` con `src/aqyra_federacion/` + `tests/` + CLI mínimo, consumido por
el runner por import de path (mismo patrón que `engines/ifc`). Sus pytest entran al gate
añadiendo `services/federacion` al Paso 1 de `ci.yml` — una única edición quirúrgica en la
línea que ya lista los paths explícitos. Nada más de `ci.yml` se toca.

## D10 · Recompute en el runner — anclado + recompute en el MISMO `run_case_c4`

Los checks anclados actuales se conservan íntegros y se ANTEPONE el recompute:
`federar(entradas, reglas)` + `validar(maestro, ids_pack)` → comparación de manifiesto e
informe recomputados contra el MISMO `expected.json` con `tolerancias.json` (conteos y
estados exactos; traslación ±1e-6 m, rotación ±1e-9°). Más checks, nunca menos — la
costura idéntica a la que cerró C1 en Fase I·h1.

---

> Bloque del hilo 2.3 (emisión BCF 3.0, tarea 1.2). Resueltas con JM el **2026-07-02**
> (OK explícito), antes de tocar código. D1–D10 no se reabren.

## D11 · Superficie de la API — `emitir_bcf(informe, carpeta)` como TERCERA función

`validar()` queda intacta y C4-FED-01 intocado POR CONSTRUCCIÓN, no por disciplina: la
salida por defecto del service sigue declarando `emitido=false` (D8). La emisión refleja
`emitido=true` + `carpeta` + `bcf_topic_guid` por incidencia SOLO en el informe que
devuelve, y solo cuando se invoca (no muta la entrada). CLI: subcomando `emitir-bcf`
(con `--bcfzip` opcional para el derivado).

## D12 · Contenedor — el ÁRBOL descomprimido es lo anclado (md5 por fichero)

La golden ancla el contenedor BCF 3.0 descomprimido con md5 por fichero (`bcf_md5` del
expected), coherente con cómo ya se anclan las entradas. Un zip determinista es frágil
(zlib/orden/timestamps) y sería el único hash "de segundo orden" del repo. El `.bcfzip`
de intercambio es un DERIVADO sin anclar (lo genera el CLI).

## D13 · GUIDs de topic — uuid5 deterministas; autor/fecha inyectables

`guid_topic = uuid5(NAMESPACE_AQYRA, "{caso}/{INC-xx}")` y
`guid_viewpoint = uuid5(NAMESPACE_AQYRA, "{caso}/{INC-xx}/viewpoint")`, con
`NAMESPACE_AQYRA = uuid5(NAMESPACE_DNS, "aqyra.bcf")`: estables entre ejecuciones y
ANCLADOS en el expected de C4-FED-02 (un UUID aleatorio obligaría a sacar el guid del
diff, debilitando el oráculo). `autor`/`fecha` (CreationAuthor/CreationDate) son
metadatos de generación INYECTABLES — misma filosofía que la `procedencia` del
manifiesto; la golden los fija en `bcf_generacion` y el runner los inyecta.

## D14 · Golden — caso NUEVO C4-FED-02; el paso de emisión lo activa el expected

Mismas entradas CONGELADAS que el 01 (mismos md5, byte a byte), expected propio con
`emitido=true` + árbol BCF anclado. C4-FED-01 queda como record intocado del
contract-first. El runner descubre el caso por glob y la emisión se activa por presencia
en el expected (`informe_qa.bcf.emitido == true`): el 01 ni se entera. D10 se respeta —
más checks, nunca menos.

## D15 · Release — Llave 2 del service en este hilo

`federacion` 0.2.0 con la emisión = primera superficie completa de adopción → primer tag
FIRMADO del service tras el merge: `federacion-v0.2.0` (estilo de los tags de componente
del repo), patrón del release v0.10.0 del engine (tag GPG anotado sobre main;
release.yml verifica golden VERDE + tipo+firma con el re-fetch del objeto de tag, PR
#10). release.yml amplía su disparo en UNA línea: `tags: ["v*", "federacion-v*"]`.

---

> Bloque del hilo 2.4 (IFC sucio — tarea 1.3). Resueltas con JM el **2026-07-02**
> (OK explícito), antes de tocar código. D1–D15 no se reabren. Este bloque CIERRA el
> ADR de la ficha "parser sucio = tarea 1.3".

## D16 · Dónde vive el endurecimiento — SOLO `services/federacion`

El engine C1 es zona firmada y produce IFC limpio por construcción; toda la suciedad
real entra por el CONSUMIDOR (`federar()`/`validar()`), que es donde se endurece
(módulo `lectura.py` + retoques en `federar.py`/`qa.py`/`ids_min.py`). Si algún hilo
futuro exigiera tocar `engines/ifc`, será PR separado con su propia justificación.

## D17 · Política de fallo — taxonomía de DOS NIVELES

**TOLERABLE** → se lee, se degrada y se DECLARA (nunca en silencio): `Name=None` en la
estructura espacial → nodo `"(sin nombre)"` + aviso · nombre duplicado intra-modelo y
mismo nivel → aviso · nivel ausente (sin Site/Building/Storey) → aviso · más de un
`IfcProject` → aviso · esquema ≠ IFC4X3 (IFC2X3/IFC4) → aviso y R4-GEORREF falla con
detalle en vez de reventar · unidades no métricas o ausentes → aviso · entidad corrupta
saltable → aviso con su `#id` · fichero grande (>256 MB) → aviso (política de tamaño,
sin optimización). **BLOQUEANTE** → `LecturaIfcError` (subclase de `ValueError`) con
diagnóstico accionable (fichero, entidad, campo, motivo — nunca stack trace pelado):
fichero ausente · no parsea · md5 ≠ declarado. **Matiz anclado:** Psets vía TIPO
(`IsTypedBy`/`IfcRelDefinesByType`) y clasificaciones con `ReferencedSource` ENCADENADO
no son suciedad — son IFC conforme (patrón Revit) que el motor v0 leía mal; su arreglo
es CORRECCIÓN de lectura (la herencia ocurrencia>tipo la manda IDS), sin aviso, y el
recompute de C4-FED-01/02 demuestra que no mueve nada.

## D18 · IFC sucio del golden — SINTÉTICO ensuciado adrede por script

`entrada/ensuciar.py` (versionado en el caso, procedencia) parte del `ARQ.ifc` CONGELADO
de C4-FED-01 (anclado por md5) e inyecta cada suciedad por separado con ifcopenshell,
normalizando la cabecera SPF (timestamp fijo) para que la generación sea determinista.
El resultado `SUCIO.ifc` se congela byte a byte (md5 en el expected), como toda entrada
golden. Sin derechos de terceros. Un export real de Revit puede entrar después como
pytest local no versionado si se quiere fidelidad extra (decisión nueva).

## D19 · Forma del golden — caso NUEVO C4-FED-03 + pytest para bloqueantes

C4-FED-03 ancla el CAMINO FELIZ-DEGRADADO: IFC sucio → manifiesto (con nodos
`"(sin nombre)"` visibles) + informe con las degradaciones declaradas en el expected.
Activación por contenido (patrón D14): 01 y 02 ni se enteran; el runner lo descubre por
glob y NO se toca (`ci.yml` tampoco). La suciedad BLOQUEANTE (diagnósticos de
`LecturaIfcError`) se cubre con pytest (`tests/test_lectura.py`) — los errores no se
anclan en golden.

## D20 · Contrato de la degradación — clave forward-open `avisos_lectura` en el INFORME QA

`validar()` añade al informe `avisos_lectura`: lista de `{modelo, codigo, detalle}` por
modelo, SOLO cuando hay avisos (modelos limpios → la clave NO aparece: C4-FED-01/02
intactos por construcción, y `_diffs` del runner no ve claves nuevas). `detalle` es texto
libre (normalizado en el recompute, como `titulo`); la semántica anclada son `modelo` +
`codigo`. El esquema ya es forward-open; se documenta la clave en
`informe-qa.schema.json` (aditivo). El MANIFIESTO no gana claves (procedencia intacta);
lo estructural degradado ya queda visible en sus `agregados`. La API crece →
`services/federacion` 0.3.0.

---

> Bloque del hilo 2.5 (golden de federación adicional — tarea 1.4). Resueltas con JM el
> **2026-07-02** (OK explícito), antes de tocar código. D1–D20 no se reabren.

## D21 · Alcance de 1.4 — DOS casos: C4-FED-04 (integración) + C4-FED-05 (mantener-separada)

**C4-FED-04** es el caso de INTEGRACIÓN: federación MIXTA (el `SUCIO.ifc` CONGELADO del 03
+ el `EST.ifc` CONGELADO del 01, reutilizados **byte a byte** — patrón D14, cero ficheros
de entrada nuevos; la suciedad ya está diseñada) **con emisión** (`emitido=true`). Ancla lo
que ningún caso ancla: la interacción 1.2×1.3 (informe con `avisos_lectura` + emisión de
topics BCF) y la **procedencia de los avisos POR MODELO** (solo SUC aporta avisos; EST
limpio no aparece). Usa `unificar-por-nombre` para seguir comparable con 01/03.
**C4-FED-05** es el caso pequeño dedicado a la política `mantener-separada` (D22), con las
entradas limpias del 01 (`ARQ.ifc` + `EST.ifc`, byte a byte) y sin emisión.

## D22 · `mantener-separada` — SE IMPLEMENTA y se ancla en C4-FED-05

**Hallazgo de 1.4:** el service 0.3.0 ACEPTABA la política y la ECOABA en el manifiesto
(`"mantenida-separada"`) sin aplicarla — los nodos se unificaban por `(nivel, nombre)`
incondicionalmente. Un manifiesto que declara una política que no aplicó es un bug, y
anclarlo en golden anclaría comportamiento incorrecto. Se implementa: con
`mantener-separada` la clave del nodo incluye el MODELO → nodos por modelo sin fundir
(`aportado_por` unitario); el nivel Project sigue único por definición (política
documentada en `federar.py`, sin cambio). Comportamiento nuevo → service **0.4.0** (D25).

## D23 · Estados y transformación del 04 — heterogéneos y no triviales

Estados DISTINTOS por modelo: `SUC=S1, EST=S3` → `maestro=S1` — primera vez que la regla
"maestro = min(S)" (política de v0, qa.py) se ancla con estados que difieren. Puntos base
DISTINTOS por modelo y `rotacion_deg ≠ 0`: ancla la copia declarada de la transformación
y da a las tolerancias del recompute (±1e-6 m, ±1e-9°) valores reales que tolerar. La
rotación es METADATO declarado (ADR punto base declarado): el service NO rota geometría
en v0 y el caso no lo finge.

## D24 · `prioridad` — RESERVADA en v0 (sin semántica)

El service no la usa y no se inventa semántica sin caso de uso real. Se documenta en
`reglas-federacion.schema.json` (`$comment`: reservada en v0). Si algún día gana
significado (p. ej. orden de resolución en conflictos de unificación), será decisión
nueva con su propio anclaje golden.

## D25 · Versionado y release — service 0.4.0, SIN release

**0.4.0** por D22 (comportamiento nuevo en una entrada documentada), no 0.3.1: semver
honesto. SIN tag/release en este hilo: la Llave 2 del service sigue en `federacion-v0.2.0`
y el siguiente tag llegará con superficie nueva de adopción (IFC federado derivado, v0.x
— D6), no con cobertura. Confirmado con JM al cierre.

---

> Bloque del hilo 2.6 (IFC federado derivado + cámara BCF — v0.x, D6). Resueltas con JM
> el **2026-07-03** (OK explícito), antes de tocar código. D1–D25 no se reabren. Este
> bloque CIERRA la decisión que D6 aplazó ("con su anclaje decidido entonces").

## D26 · Anclaje del derivado — md5 byte a byte, con cabecera determinista PROPIA

El `.ifc` derivado se ancla por **md5 byte a byte** en el expected
(`maestro_manifiesto.ifc_derivado.md5`), el patrón del repo (entradas por md5, árbol BCF
por md5 — D12). Lo hace viable el spike del hilo (2026-07-03): dos ejecuciones de la misma
combinación sobre las entradas congeladas reales del 01 (IFC4X3_ADD2, ifcopenshell 0.8.5)
→ md5 idéntico; el ÚNICO no-determinismo observado es el timestamp de FILE_NAME. En vez
de normalizar a posteriori (regex del 03), `derivar()` escribe la cabecera SPF
DETERMINISTA él mismo: `time_stamp` INYECTADO (patrón `bcf_generacion`/D13 — la golden lo
fija en `derivado_generacion` y el runner lo inyecta) y
`preprocessor_version`/`originating_system` fijados a `aqyra-federacion` SIN número de
versión ADREDE (un bump del service sin cambio de comportamiento no puede mover el md5
del contrato; la versión ya vive en `procedencia.generado_por` del manifiesto) — un
string de build del wheel (`IfcOpenShell 0.8.5-1c5b825`) tampoco puede decidir el md5. La versión del writer queda anclada por uv.lock (0.8.5); el md5 se verifica en
Linux x86_64 (mismo wheel en CI y recompute) — si otra plataforma diera md5 distinto, es
hallazgo de portabilidad y decisión nueva, no aflojamiento de la golden.

## D27 · Materialización de la transformación — PLACEMENT RAÍZ por modelo + georref IFC

La geometría interna de los modelos NO se toca (se mantiene el principio de v0: el
service no rota geometría; la transformación es METADATO declarado — D23). El derivado
materializa la transformación donde IFC manda: cada modelo cuelga de un **placement raíz
propio** (`IfcLocalPlacement` con `IfcAxis2Placement3D`: Location = traslación declarada
[dE, dN, dCota], RefDirection = rotación declarada alrededor de Z), y el conjunto declara
el CRS destino con `IfcMapConversion` + `IfcProjectedCRS` (EPSG de las reglas) sobre el
contexto geométrico — con lo que el derivado CUMPLE R4-GEORREF de serie, cerrando el
círculo del QA. Un IfcProject ÚNICO (nombre = proyecto de las reglas), estructura
espacial de origen re-colgada bajo él SIN fundir nodos (la unificación declarada vive en
el manifiesto — D1: la verdad no cambia de sitio). Esquemas heterogéneos entre modelos →
`LecturaIfcError` (el writer no puede mezclar esquemas SPF; diagnóstico accionable, D17).

## D28 · GUIDs duplicados entre modelos — CONSERVAR ambos + aviso `guid-duplicado`

Política D1 intacta: GUIDs preservados, dedup=nunca. Si dos modelos aportan el MISMO
`GlobalId`, el derivado CONSERVA ambos y la degradación se DECLARA (coherente con D17:
se declara, no se calla): aviso `{modelo, codigo: "guid-duplicado", detalle}` en
`avisos_lectura`, emitido por `validar()` (que ya abre todos los modelos — la detección
es transversal, no de un fichero). La taxonomía del esquema se amplía de forma ADITIVA
(`informe-qa.schema.json`, enum de `codigo`). Los casos 01–05 no tienen GUIDs cruzados
(entradas de linajes distintos) → sus expected quedan intactos POR CONSTRUCCIÓN; el
camino se cubre con pytest (duplicado sintético), no con golden nueva.

## D29 · Cámara del viewpoint — UN caso C4-FED-06 con derivado+cámara JUNTOS

La cámara sin derivado no existe (bcf.py lo documenta desde 1.2): son la misma feature
vista de dos lados → **un solo caso golden C4-FED-06**. Cámara PERSPECTIVA determinista
por bounding box de los elementos de los GUIDs del topic en el DERIVADO: el bbox se
calcula sobre los ORÍGENES de los placements absolutos (cadena de `ObjectPlacement`
resuelta — determinista y sin motor de geometría; la cámara por malla exacta sería
decisión nueva), posición = centro + k·(1, −1, 1)·d con **k = 1.0** y d = max(diagonal
del bbox, 1 m) — constantes DOCUMENTADAS aquí y en el código, sin números mágicos —,
mirando al centro (`CameraDirection` = normalizado centro−posición, `CameraUpVector`
ortogonalizado con Z arriba, `FieldOfView` = 60°, `AspectRatio` = 16/9, floats con 6
decimales fijos). SOLO se emite cuando `emitir_bcf()` recibe el derivado (opt-in;
activación por contenido del expected — patrón D14): los `bcf_md5` de 02/04 quedan
intactos POR CONSTRUCCIÓN, no por disciplina.

## D30 · Superficie API + versionado + release — `derivar()` SEPARADA · 0.5.0 · release SÍ

Cuarta función del contrato: **`derivar(manifiesto, base_dir, salida) → manifiesto
actualizado`** con `ifc_derivado = {fichero, md5, determinista: true}` — la clave que el
esquema dejó opcional adrede (D6) gana su forma final SIN cambio de esquema. `federar()`
queda INTACTA (patrón D11: cada superficie nueva es un paso explícito) → 01–05 intocados
por construcción. CLI: subcomando `derivar`. El runner gana el paso de derivación
activado por contenido del expected (presencia de `maestro_manifiesto.ifc_derivado`) —
edición mínima de run_golden.py justificada AQUÍ; ci.yml y release.yml NO se tocan.
Versionado: **0.5.0** (superficie nueva). Release: **SÍ** — el derivado es la superficie
nueva de adopción que D25 esperaba → tag firmado `federacion-v0.5.0` + Release run tras
el merge (Llave 2 = JM, patrón D15/PR #10); confirmación explícita al cierre.

---
*Regla de oro heredada: un fallo no se arregla aflojando la golden. El CI nunca certifica
(Llave 2 = JM).*
