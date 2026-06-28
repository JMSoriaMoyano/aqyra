# Verificación de cierre de la Ola 1 (PT 1.6)

**Auditoría del núcleo transversal y de la edificación cerrada · 22/06/2026.** Comprueba que el
núcleo (contratos C1 + CN-1/CN-2/CN-3) está listo para que **enchufe una disciplina nueva sin tocarlo** y que la
edificación queda cubierta de extremo a extremo. No es desarrollo nuevo. Realizada con el agente
`ingeniero-estructurista` y contrastada con una **verificación independiente** (subagente). Todo
resultado es de **predimensionado/asistencia y debe ser revisado y firmado por técnico competente**;
NDP marcados `[confirmar AN]`.

> **Veredicto global: Ola 1 CERRABLE ✅, una vez aplicada la corrección de empaquetado.** Los
> contratos son coherentes con la implementación y la edificación cumple de extremo a extremo. La
> auditoría detectó **un defecto de empaquetado** en el `.plugin` v0.22.0 (8 módulos truncados al
> reempaquetar), **ya corregido en v0.22.1**. El resto de hallazgos son precisiones de
> documentación de contrato y puntos de extensión **previstos** para disciplinas no estructurales
> (backlog de la Ola 4), no defectos de la edificación.

---

## 1. Tabla contrato por contrato

| Contrato | Veredicto | Evidencia |
|---|---|---|
| **C1 — IFC / modelo neutro** | ⚠️ Coherente con matices | El esquema documentado coincide con los parsers intactos: `barras/ifc_to_model.py` emite `unidades, materiales, secciones, nodos, barras, cargas` (caso 1 lo confirma, con `cargas` a nivel raíz `{caso,barra,direccion,qz}`); `laminas/ifc_to_model_3d.py` emite `unidades, materiales, secciones, nodos, barras, superficies` (caso 10 lo confirma). El caso 15 **añade claves nuevas** (`pantallas[]`, `diafragma`, `dinteles`, `ec8`, `nucleo`, `masas`) sin alterar la semántica de las existentes. **Matices** (ver §6): (a) la colocación de cargas difiere entre 1D (raíz) y 2D (`superficies[].cargas`) y el contrato no lo explicita; (b) el modelo sísmico es un **modelo hermano** que usa `material` (singular) en vez de `materiales` (dict) y omite la topología gravitatoria; (c) referencias de ola **desfasadas** en §4 ("habilita la Ola 3 (PCI)"); (d) el parser `puente.py` y `barras/ifc_to_model.py`, citados por el contrato, estaban **truncados en el paquete v0.22.0** (corregido en v0.22.1). |
| **C2 — Memoria del despacho** | ✅ Coherente | `criterios-despacho.md` tiene las **5 secciones** fijas (Normativa, Materiales, Coeficientes y criterios, Lecciones aprendidas, **Formato de memoria**), idénticas a `plantilla-criterios-disciplina.md`. La skill `estructuras-eurocodigos:criterios-memoria` lee/mantiene `criterios-despacho.md` (raíz) + `memoria-estructural.md` (subcarpeta) al iniciar, con entradas fechadas y promoción de criterios. El patrón "una skill `criterios-memoria` por plugin" ya existe **duplicado** (estructuras + `cte-documentos-basicos:criterios-memoria-cte`). Matiz cosmético: el título "Materiales habituales" vs "Materiales / componentes habituales" de la plantilla. |
| **C3 — Entregables / memoria** | ✅ Coherente (con 1 alineación menor) | `plantilla-memoria.md` reproduce **exactamente** los 7 apartados de C3 §1 (Datos del proyecto · Normativa · Materiales · Acciones/bases · Comprobaciones por elemento · **Registro fechado** · Conclusiones). El generador del motor `sismico/generate_memoria_nucleo.py` ya emite memoria Word con esa estructura (caso 15). **Alineación pendiente:** la skill `estructuras-eurocodigos:memoria-calculo` documenta una estructura de 7 secciones **distinta** (sin apartado "Registro de comprobaciones fechado", "Objeto y alcance" en vez de "Datos del proyecto", "Modelo estructural" separado). Conviene alinearla con el esqueleto C3 y que toda disciplina parta de `plantilla-memoria.md`. |
| **CN-3 — Acciones / bases de cálculo** | ✅ Coherente (en su alcance actual) | Existe la skill `estructuras-eurocodigos:bases-acciones`; su `SKILL.md` cubre **EN 1990 (EC0) + EN 1991 (EC1)** con Anejo Nacional español: coeficientes parciales y de simultaneidad, ELU/ELS, permanentes/variables, viento, nieve, sobrecargas de uso, térmicas, combinaciones §6.4/§6.5; marca `[NDP - confirmar en AN]`. Alimenta al resto de skills y sigue el protocolo de memoria (lee `criterios-despacho.md`). Las acciones de tráfico (IAP) e hidrología son extensión **futura** (olas 5–6), correctamente fuera del alcance de la Ola 1. Para disciplinas no estructurales el "slot" CN-3 son las **bases de demanda** (caudales/potencias/ocupación), **ya creadas para PCI** en `instalaciones` v0.1.0 (`bases_demanda.py`, hueco H3 ✅). |

Leyenda: ✅ coherente · ⚠️ desajuste menor / a precisar · ❌ falta.

---

## 2. Hallazgo principal: integridad del paquete v0.22.0 (corregido → v0.22.1)

Al re-empaquetar **acumulativamente** v0.22.0 (caso 15, PT 1.5), **8 módulos preexistentes que solo
debían arrastrarse sin cambios quedaron truncados** (cortados a media instrucción). Es la
manifestación del *hazard* de truncado de empaquetado ya conocido (INC-04). Los módulos del caso 15
(`sismico/*`, `run_all_edificio.py`, `clasificador.py`, `laminas/ifc_to_model_3d.py`) están intactos.

| Módulo truncado en v0.22.0 | v0.22.0 | v0.21.0 (íntegro) | Efecto |
|---|---|---|---|
| `puente_analitico/puente.py` | 14 476 B (344 ln) | 41 728 B (921 ln) | ❌ IndentationError — **físico→analítico (serie R) inservible** |
| `cimentaciones/solver_raft.py` | 8 129 B | 17 557 B | ❌ IndentationError tras `def parse` |
| `cimentaciones/solver_zapata.py` | 15 320 B | 15 756 B | ❌ unterminated string literal |
| `cimentaciones/verificacion_raft.py` | 7 764 B | 14 208 B | ❌ unterminated string literal |
| `cimentaciones/run_all_raft.py` | 1 997 B | 2 002 B | ❌ `'(' was never closed` |
| `cimentaciones/plots_raft.py` | 2 779 B | 4 927 B | ⚠️ trunca, parsea por azar |
| `barras/ifc_to_model.py` | 6 098 B | 11 189 B | ⚠️ trunca (sin `parse()`), parsea por azar |
| `barras/perfiles_db.py` | 6 288 B | 6 546 B | ⚠️ trunca, parsea por azar |

**Evidencia y método.** Barrido `ast.parse` de los 126 `.py` del paquete: **5 errores de sintaxis**
en v0.22.0; **0** en v0.21.0; **0** en v0.22.1. Firma de truncado adicional (no termina en salto de
línea final): exactamente esos **8 archivos** en v0.22.0; ninguno en v0.21.0/v0.22.1. Cada archivo
truncado de v0.22.0 es un **prefijo exacto** del completo de v0.21.0 → truncado puro, sin pérdida de
ediciones intencionadas. Lección de método: **`ast.parse` por sí solo no basta** (3 de los 8 truncados
parsean); hace falta contrastar tamaño/última línea contra la versión anterior.

**Corrección aplicada — v0.22.1.** Se restauraron los 8 módulos desde v0.21.0 (íntegros y validados),
se mantuvo todo lo del caso 15, se subió la versión a **0.22.1** y se reempaquetó excluyendo
`node_modules`/`__pycache__`. Verificación del `.plugin` resultante: **126 módulos, 0 errores de
parseo, `puente.py` restaurado a 921 líneas, `barras/ifc_to_model.py` con `parse()`**, ZIP válido.
Archivo: `motor-calculo-estructural-v0.22.1.plugin` en la raíz del proyecto.

> El defecto **no afecta a los resultados de los casos** (se ejecutaron desde copias de trabajo
> completas), pero **sí rompía la instalación limpia** del plugin — justo lo que la Ola 1 debe
> garantizar ("el `.plugin` abre y los módulos están"). Distribuir **v0.22.1**, no v0.22.0.

---

## 3. Edificación cerrada de extremo a extremo

Re-revisados los últimos *runs* contra los artefactos reales (no solo el relato):

**Caso 10 — edificio integrado (4 subsistemas, IFC ortodoxo multi-elemento).** Veredicto global
**CUMPLE (4/4)**. Pórtico EC3 aprov. máx **30,5 %** (dintel IPE 360) / 22,9 % (pilares HEB 240);
mixta EC4 u_flexión **73,9 %** (η=0,66), flecha 64,2 %; muro EC2 esbelto (λ=52) N-M **44,4 %**
(φ10/200); cimentación zapata **ampliada 2,5→2,6 m** (predimensionado real: 2,5 daba u=1,021),
σ_ef **94,4 %**, fisuración 93,1 %. Equilibrio del muro y del lecho de la zapata **≈0 %**
(2,4·10⁻¹³ % / 6,4·10⁻¹⁰ %). *Aprovechamiento máximo del edificio: 94,4 %.*

**Caso 15 — núcleo de pantallas acopladas + sísmico EC8 (`verificacion_nucleo.json`).** Veredicto
**CUMPLE**. **Equilibrio X = 0,0 % e Y = 0,0 %** (`equilibrio_X/Y_error_pct`); reparto por pantalla
≈10⁻¹² %. Modal 3 GdL/planta: T1x=0,305 s / T1y=0,390 s (en meseta), ΣM_eff=100 % en X e Y;
CR(3,40;4,00) vs CM(4,00;4,00) → e0x=0,60 m. Acoplamiento DoC=0,719; deriva máx 0,225 %·h
(≤0,75 %·h). Aprovechamientos: alas 0,62, machón comprimido **0,72** (gobierna), machón traccionado
0,33, dintel 0,22, deriva 0,15. *Aprovechamiento máximo: 0,72.* Caso 11 sin regresión.

**Validación cruzada y rangos físicos:** conformes en ambos (PyNite vs anaStruct; modal `scipy.eigh`
vs SRSS; picos singulares tratados como envolvente, no como valor de diseño). El esquema neutro del
caso 15 **extiende** el del núcleo con claves nuevas, sin romper las existentes.

---

## 4. Checklist consolidado "listo para nueva disciplina"

Reúne los checklists de C1 §6, C2 §5 y C3 §4 y evalúa si el **núcleo habilita** cada punto para una
disciplina nueva (no si una disciplina concreta lo ha rellenado).

**C1 — IFC / modelo neutro**

- [x] Una disciplina puede **elegir su vía de entrada** IFC (análisis / físico / —MEP, planificada—).
- [x] Los parsers producen **modelo neutro** con `unidades` SI declaradas.
- [~] Reutiliza utilidades del núcleo (`_psets`, factor de unidades, **grafo**, `perfiles_db`/DN):
  disponibles, pero **embebidas en `puente.py`/parsers de estructuras**, no expuestas como módulo
  transversal independiente (hueco H1).
- [x] **Extiende** el esquema con claves nuevas sin alterar las existentes (caso 15 lo demuestra).
- [x] Dispone de **generador de IFC de prueba** y **validación** de equilibrio/continuidad (estructural).
- [x] Escribe resultados vía `iso19650-openbim:ifc-create` y valida con `ifc-validate` (**dominio
  estructural** ✅ y **MEP** ✅ desde PT 4.2 / `iso19650-openbim` v0.4.0; **Alignment** pendiente, Ola 5).

**C2 — Memoria del despacho**

- [x] Patrón `criterios-<disciplina>.md` en la raíz con las 5 secciones (plantilla lista).
- [x] `Casos-de-uso/` con PROGRAMA + REPOSITORIO + CHANGELOG (existe para estructuras).
- [x] `memoria-<disciplina>.md` por proyecto en subcarpeta (plantilla lista).
- [x] Skill `criterios-memoria` por plugin que lee/escribe al iniciar (ya replicado en 2 plugins).

**C3 — Entregables / memoria**

- [x] Esqueleto de **7 apartados** disponible y agnóstico de disciplina (`plantilla-memoria.md`).
- [x] Citas de artículo y marcado `[confirmar AN]` de NDP (convención fijada).
- [x] Registro fechado + advertencia de revisión/firma (en plantilla y criterios).
- [x] Una memoria por obra, hereda criterios del despacho (C2).
- [x] Motor de documentos común reutilizable (`docx`/`pdf`/`pptx`/`xlsx`).
- [~] **Alinear** `memoria-calculo` al esqueleto C3 y partir siempre de `plantilla-memoria.md` (hueco H4).

**CN-3 — Acciones / bases de cálculo**

- [x] `bases-acciones` cubre EC0/EC1 + AN para disciplinas estructurales.
- [x] Para disciplinas **no estructurales** el "slot" de **bases de demanda** existe (hueco H3 ✅; `instalaciones:bases_demanda.py`, PCI).

**Definición de "hecho" de la Ola 1 (roadmap §7)**

- [x] (a) Leer/escribir IFC (C1) — ✅ estructural; ⚠️ MEP/Alignment planificados.
- [x] (b) Aprender entre hilos (CN-1) — ✅.
- [x] (c) Emitir memoria homogénea (CN-2) — ✅ (alineación menor de `memoria-calculo`).
- [x] (d) Tomar acciones (CN-3) — ✅ estructural; ✅ bases de demanda para no estructurales (PCI, H3, `instalaciones` v0.1.0).
- [x] Edificación cubierta de extremo a extremo — ✅ (casos 1–10, 11, 15).
- [x] El `.plugin` abre y los módulos están — ✅ **en v0.22.1** (❌ en v0.22.0).

Leyenda: [x] habilitado · [~] habilitado con hueco anotado para la Ola 4.

---

## 5. Prueba de "enchufe" (dry-run): cómo consumiría `instalaciones` cada contrato

Recorrido paso a paso del futuro plugin `instalaciones` (Ola 4: PCI + eléctricas + clima), sin
construir nada, para localizar dónde **tocaría el núcleo** (lo que no debería pasar).

1. **C1 (IFC / modelo neutro → dominio MEP).** `instalaciones` elige la vía **MEP** (no la de
   análisis estructural). Escribiría `ifc_to_model_mep.py` que lee `IfcDistributionSystem` /
   `IfcFlowSegment/Fitting/Terminal` + `IfcDistributionPort` y emite el **modelo neutro de red**
   (`nodos`+`tramos`+`terminales`+`fuentes`, con `unidades` SI declaradas) descrito en C1 §4 —
   mismo patrón que el estructural. **Reutilizaría** `_psets`, el **factor de unidades** y la
   **construcción de grafo por intersección/puertos**. → **Aquí choca:** esas utilidades están
   **dentro de `puente.py` y de los parsers de estructuras**, no en un módulo del núcleo. Tal como
   está, `instalaciones` tendría que **depender de las tripas de `motor-calculo-estructural`** o
   reimplementarlas → **toca el núcleo** (hueco **H1**). Además, `iso19650-openbim:ifc-create/
   ifc-validate` aún **no conocen entidades MEP** → no podría escribir/validar resultados de red
   (hueco **H2**). El esquema neutro estructural **no se contradice** con el MEP (son modelos
   hermanos que comparten convenciones), eso sí funciona.

2. **C2 (memoria del despacho).** Copia `plantilla-criterios-disciplina.md` → `criterios-
   instalaciones.md` en la raíz (la sección "Materiales / componentes habituales" ya contempla
   "tubería/cable/conducto"); crea su `Casos-de-uso/` (PROGRAMA/REPOSITORIO/CHANGELOG) y
   `memoria-instalaciones.md` por obra; añade su skill `criterios-memoria`. **Enchufa sin tocar el
   núcleo. ✅** (Único arreglo: corregir la referencia de ola — ver H5.)

3. **C3 (entregables / memoria).** Genera `memoria-instalaciones.md` con el **esqueleto de 7
   apartados** (el apartado 4 admite "caudales/potencias/ocupación" y las unidades l/s, kPa, kW, A
   ya están previstas en C3 §2) y reutiliza `docx`/`pdf`. **Enchufa. ✅** Debe partir de
   `plantilla-memoria.md` (canónica), no de la estructura de `memoria-calculo` (hueco H4).

4. **CN-3 (acciones / bases).** `instalaciones` es dimensionado de redes + cumplimiento, **menos FEM**.
   Sus "acciones" no son cargas EC0/EC1 sino **demandas** (ocupación→caudal, factores de
   simultaneidad, potencias, intensidades) según RITE/REBT/CTE-HS. `bases-acciones` **no cubre**
   esto. → El "slot" CN-3 lo rellenaría una **base de demanda propia** de la disciplina (hueco **H3**);
   el contrato CN-3 debería aclarar que para disciplinas no estructurales este contrato se cumple con
   módulos de demanda específicos. No se toca el núcleo, pero el contrato debe explicitarlo.

**Conclusión del dry-run:** CN-1 y CN-2 enchufan limpiamente hoy. C1 y CN-3 enchufan **a nivel de patrón**,
pero exigen **trabajo de núcleo previo** (extraer grafo+utilidades IFC; ampliar IFC a MEP; definir
bases de demanda). Eso es precisamente el contenido planificado de la **Ola 4** — no son defectos de
la Ola 1, sino sus puntos de extensión, ahora explicitados.

---

## 6. Huecos detectados — backlog para la Ola 4

| ID | Prioridad | Contrato | Hueco | Acción propuesta |
|---|---|---|---|---|
| **H1** | P1 (Ola 4) | C1 | El **grafo de red** y las utilidades IFC compartidas (`_psets`, factor de unidades, construcción de grafo por puertos/intersección) están **embebidas en `puente.py`/parsers de estructuras**, no expuestas como capacidad transversal. | ✅ **Aplicado (PT 4.1, v0.23.0).** Extraído a `scripts/nucleo/` (`ifc_utils` + `grafo_red`), agnóstico al solver, con API estable y micro-test; `puente.py` lo consume como adaptador fino (R1–R5 byte a byte, casos 1/5/7/10 cumplen). Resuelve la decisión abierta nº4. H2 (IFC MEP) queda pendiente. |
| **H2** | P1 (Ola 4) | C1 | `iso19650-openbim` (ifc-create/ifc-validate) **no soportaba MEP** (IfcDistributionElement/FlowSegment/Port, Pset_*). | ✅ **Aplicado (PT 4.2, `iso19650-openbim` v0.4.0).** Abierto el dominio IFC MEP: `scripts/mep/ifc_to_model_mep.py` (físico→modelo neutro de red, reutiliza el núcleo **sin tocarlo**), `generate_test_ifc_mep.py` (red PCI de prueba) y `validacion_red.py` (continuidad/terminales/huérfanas/SI), con micro-test `test_red_mep.py` y caso e2e `caso-MEP-01-red-pci` (CUMPLE, cobertura 100 %). `ifc-create`/`ifc-validate` ampliadas a MEP (`checks-mep.py`). Núcleo **espejado** al plugin (avance de la decisión nº4). Sin solver hidráulico (nace con `instalaciones`). Gancho **H3** (clave `demanda`) dejado listo, no implementado. |
| **H3** | P2 (Ola 4) | CN-3 | CN-3 = `bases-acciones` solo cubre acciones estructurales EC0/EC1; no hay **bases de demanda** (caudales/potencias/ocupación, simultaneidad). | ✅ **Aplicado (PT 4.3, plugin `instalaciones` v0.1.0).** Creada la base de demanda no estructural `scripts/pci/bases_demanda.py` (PCI: simultaneidad, caudal y presión dinámica de cálculo de BIE según RIPCI/UNE-EN 671/UNE 23500/DB-SI, `[confirmar AN]`), que rellena la clave `demanda` del modelo neutro de red. Aclarado que para disciplinas no estructurales el "slot" CN-3 son las **bases de demanda** (análogo a las acciones EC0/EC1). Nace además el **solver hidráulico de red** (Darcy-Weisbach) y el caso e2e `caso-PCI-01-bie-presion` (CUMPLE, balance 0,0 %). |
| **H4** | P3 | C3 | La skill `estructuras-eurocodigos:memoria-calculo` **no sigue exactamente** el esqueleto de 7 apartados de C3 (sin "Registro fechado", "Objeto y alcance" vs "Datos del proyecto"). | 🟡 **Parcial:** fijada en C3 §3 la fuente canónica (`plantilla-memoria.md`) y registrada la alineación pendiente. El cambio en la skill se hace en el plugin `estructuras-eurocodigos` (Settings > Capabilities), no editable desde este hilo. |
| **H5** | P3 | C1, C2 | **Referencias de ola desfasadas** tras la re-secuenciación v2.1: C1 §4 decía MEP "habilita la Ola 3 (PCI) y la Ola 4"; C2 §1 decía "criterios-instalaciones.md (a crear en Ola 3)". Con v2.1, **instalaciones es Ola 4** (Ola 3 = edificación singular). | ✅ **Aplicado:** corregido en C1 §4 (texto y "Tareas… para la Ola 4") y C2 §1 ("a crear en Ola 4"). |
| **H6** | P1 (proceso) | — | El **empaquetado** truncó 8 módulos en v0.22.0 sin que ningún control lo detectara antes de publicar. | ✅ **Aplicado:** automatizado en `Nucleo-transversal/verificar_empaquetado.py` (exit≠0 si falla; `ast.parse` + salto de línea final + sin artefactos + plugin.json válido + contraste de tamaños vs `--ref`). Probado APTO en v0.22.1 y NO APTO en copia truncada. Pendiente menor: integrarlo como paso fijo del flujo de empaquetado (INC-09). |
| **H7** | P3 | C1 | **Precisiones del esquema neutro:** colocación de `cargas` distinta en 1D (raíz) y 2D (`superficies[].cargas`) no explicitada; el modelo sísmico usa `material` (singular) vs `materiales` (dict). | ✅ **Aplicado:** C1 §2 documenta las dos colocaciones de carga; C1 §3 declara los "modelos hermanos por tipo de análisis" y deja anotada la reconciliación `material`/`materiales`. |

> Nota: el soporte **GIS** (decisión abierta nº3) y la acción de **tráfico/hidrología** (CN-3) son de
> las olas 5–6, no de la Ola 4; no bloquean el enchufe de `instalaciones`.

---

## 7. Verificación independiente (subagente)

Se lanzó una auditoría **ciega** en paralelo (sin las conclusiones previas) sobre los tres `.plugin`
y los contratos. **Confirmó** de forma independiente: los **8 módulos truncados** en v0.22.0
(coincidencia exacta de lista y tamaños), su ausencia en v0.21.0 y su corrección en v0.22.1
(0 errores); la advertencia de que **`ast.parse` infravalora** el truncado; la coherencia de **C3**
(7 apartados) y **CN-3** (EC0/EC1); y los números de **caso 10** (CUMPLE 4/4, máx 94,4 %) y **caso 15**
(CUMPLE, equilibrio 0,0 % X/Y, máx 0,72).

Aportó además dos precisiones de C1 (colocación de `cargas` y el modelo hermano del caso 15),
incorporadas como **H7**. Reportó un supuesto desajuste de **C2** ("falta la sección Formato de
memoria"), que se comprobó **falso positivo**: la lectura por *shell* del sandbox devolvió una copia
**truncada** del markdown (2 153 B, 4 secciones), mientras la herramienta de fichero (fuente de
verdad) muestra el archivo completo con las **5 secciones**. El episodio **valida la regla de método**
de este proyecto: para markdown, mandan las herramientas de fichero (Read/Write/Edit), no el shell.

---

## 8. Conclusión

La **Ola 1 puede cerrarse (✅)**: el núcleo es coherente con su implementación (C1 + CN-1/CN-2/CN-3), la edificación
cumple de extremo a extremo (casos 1–10, 11, 15, equilibrios ≈0 %, aprovechamientos ≤1) y una
disciplina nueva puede aprender entre hilos (CN-1) y emitir memoria homogénea (CN-2) sin tocar el núcleo;
las acciones estructurales (CN-3) están cubiertas. La condición material para el cierre era reparar el
**empaquetado v0.22.0 → v0.22.1**, ya hecho: el plugin instala limpio y todos los módulos están.

Los huecos H1–H3 (extraer grafo+utilidades, IFC MEP, bases de demanda) **no son deudas de la Ola 1**
sino el **arranque natural de la Ola 4**: el dry-run confirma que `instalaciones` enchufa por CN-1/CN-2 y
necesita ese trabajo de núcleo en C1/CN-3 —exactamente lo previsto—. H4–H7 son correcciones acotadas de
documentación y de proceso. **Recomendación:** marcar PT 1.6 ✅, distribuir **v0.22.1**, e iniciar la
Ola 4 abordando H1/H2/H3 antes de redactar el agente `ingeniero-de-instalaciones`.

*Predimensionado/asistencia; a revisar y firmar por técnico competente (Ingeniero de Caminos).*
