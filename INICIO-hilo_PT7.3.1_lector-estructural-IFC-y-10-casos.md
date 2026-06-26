INICIO de hilo — PT 7.3.1 (Ola 7): **lector estructural IFC→idealización** para la disciplina
**`puentes`** y, sobre él, **10 casos de aplicación IFC-driven** (PUE-07…PUE-16) que ejercitan todo
lo desarrollado en la ola. Proyecto Estructurando. Ejecuta el **PT 7.3.1** (paso de **integración
C1↔puentes**; la escalera FEM se reanuda después en **PT 7.4 — cajón / FEM-2**).

El PT 7.3 ya cerró la **subestructura**: `puentes` **v0.3.0** (pila + aparato de apoyo + cimentación
enrutada; estribo), con el motor **`motor-fem` v0.2.1 intacto** (sigue **FEM-1**). Con ello, la
disciplina cubre de extremo a extremo, **de forma paramétrica**, las 6 tipologías del grupo lineal +
subestructura. **El hueco que cierra este PT** es que los verticales **arrancan de `entrada_caso.json`
(parámetros tecleados), no de un IFC**: falta el **lector estructural** que traduzca un modelo IFC del
puente a la idealización de cada tipología. Construido el lector, se entregan **10 casos IFC-driven**.

> Todo cálculo y entregable es de **predimensionado/asistencia y debe ser revisado y firmado por
> técnico competente** (Ingeniero de Caminos, Canales y Puertos). Los NDP se marcan `[confirmar AN]`.

---

## Objetivo del hilo (dos entregables encadenados)

1. **Lector estructural IFC→idealización** para `puentes`: dado un IFC del puente, **clasificar** sus
   elementos, **extraer** geometría/materiales/secciones, **resolver asociaciones** (viga↔pila,
   pila↔cimentación, tablero↔estribo, aparato de apoyo) y **construir la idealización** de cada
   tipología — produciendo el mismo `entrada_caso`/modelo neutro que hoy se teclea. Es decir, que el
   cálculo **arranque del IFC**.
2. **10 casos de aplicación IFC-driven** (PUE-07…PUE-16): por cada caso, **generar un IFC real**
   (geometría) → **leerlo con el lector** → idealizar → `motor-fem` → IAP-11 → comprobación EC →
   **memoria + write-back al IFC** (round-trip completo). Tabla de casos en §7.

---

## Contexto — estado de la Ola 7 (para situar el hilo)

- **PT 7.0 ✅** `motor-fem` v0.1.0 (FEM-0). **PT 7.1 ✅** `puentes` v0.1.0 + FEM-1 (vigas pretensadas).
  **PT 7.2 ✅** `puentes` v0.2.0 (losa postesada, pórtico, celosía) + `motor-fem` v0.2.1.
  **PT 7.3 ✅** `puentes` v0.3.0 (pila+apoyo+cimentación, estribo) — **motor sin tocar**.
- **`puentes` v0.3.0** consume `motor-fem` (C5) y `Alignment` (C1). Verticales **paramétricos**
  (`scripts/run_all_*.py` + `scripts/idealizacion/*.py` construyen el modelo desde `p`/`tablero`).
- El motor **no se toca** en este PT (no es un peldaño FEM). La escalera FEM (PT 7.4 cajón, FEM-2)
  se reanuda después.

---

## Lo que YA existe y se reutiliza (clave para acotar el alcance)

El hueco es **menor de lo que parece**: buena parte de la subestructura ya tiene parser IFC.

- **Alignment (Ola 5) — `iso19650-openbim` v0.8.0** `scripts/lineal/`:
  `ifc_to_model_lineal.py` (IFC 4.3 `IfcAlignment` → modelo neutro lineal por PK),
  `generate_test_ifc_lineal.py` (genera el eje), `validacion_alineacion.py`. → **el eje del tablero
  se lee del IFC** (recta/clotoide/curva + peralte + PK). Ya integrado en `puentes` (vigas/losa).
- **Cimentaciones y muro — `motor-calculo-estructural` v0.23.0** ya parsean IFC:
  `scripts/muros-contencion/solver_muro.py::parse_auto` (muro/estribo),
  `scripts/pilotes/solver_pilote.py::parse`, `scripts/bielas-tirantes/run_all_encepado.py::parse`,
  `scripts/cimentaciones/solver_zapata.py` (zapata). → la **cimentación y el muro** ya saben leerse de
  un IFC (aunque arrastran PyNite al importar; ver Notas de método).
- **narración→IFC — `iso19650-openbim`** `skills/narracion-a-ifc/scripts/` (`spec_to_ifc.py`,
  `catalogo_ifc.py`, `compilar_spec.py`): genera geometría IFC real (elementos + Psets) desde prosa.
  → **generación del IFC por caso**.
- **Parser MEP de red — `iso19650-openbim`** `scripts/mep/ifc_to_model_mep.py`: **patrón** de
  parser IFC→modelo neutro (clasificación + extracción + grafo) a imitar para el estructural.
- **Clasificación multi-elemento — `motor-calculo`** `clasificador.py` + `run_all_edificio.py`
  (v0.12.0, caso 10): clasifica y enruta CADA elemento de un `IfcStructuralAnalysisModel`
  (barra/superficie + sección + material + asociaciones por proximidad). **Patrón directo** para el
  lector de puente.
- **Write-back** — el mapping `Pset_Estructurando_ResultadoPuente` que ya produce `puentes`
  (`comun/resultado_ifc_puente.py`) + el escritor genérico de `iso19650`.

> **Hueco real a construir:** el lector del **tablero** (emparrillado de vigas, losa, pórtico/marco,
> celosía) y de la **pila + aparato de apoyo**. La cimentación (zapata/pilotes/encepado) y el estribo
> (muro) **reutilizan los parsers de `motor-calculo`**; el eje, el de `iso19650`.

---

## Arquitectura del lector (decisión de diseño recomendada)

Respetar la frontera del ecosistema: **el parser vive en C1, la idealización en la disciplina**.

- **Capa C1 (`iso19650-openbim`, nuevo `scripts/estructural/ifc_to_model_estructural.py`):** IFC →
  **modelo neutro estructural de puente** (lista de elementos clasificados con tipo, geometría,
  material, sección y relaciones). Análogo a `ifc_to_model_lineal`/`ifc_to_model_mep`. **Solo añade
  clave nueva** al contrato C1 (modelo hermano, retrocompatible).
- **Capa disciplina (`puentes`, nuevo `scripts/lectura/desde_ifc.py`):** modelo neutro estructural →
  **idealización por tipología** (el `entrada_caso`/modelo C5 que hoy se teclea). Un **adaptador por
  tipología** (thin), que reutiliza los parsers de cimentación/muro de `motor-calculo` y el de
  Alignment de `iso19650` por PYTHONPATH.

Así el lector no duplica mecánica: clasifica, extrae y **mapea** a lo ya existente.

### Qué hace el lector, paso a paso (por tipología)
1. **Clasificar** cada `IfcElement`: tablero/viga, pila, estribo, zapata/encepado/pilote, aparato de
   apoyo — por tipo IFC + Pset + geometría/orientación (no `by_type[0]`: iterar todo el modelo).
2. **Geometría**: luces y nº de vanos, canto/ancho, altura de pila, separación de vigas, dimensiones
   de zapata/puntera/talón, cotas y posición de apoyos. Eje del tablero por **Alignment**.
3. **Materiales/secciones**: `IfcMaterial`/`IfcMaterialProfileSet`; armado/postesado por Pset (dato
   de predimensionado del proyecto).
4. **Asociaciones**: viga↔pila, pila↔cimentación, tablero↔estribo, aparato de apoyo (proximidad/
   contacto; Pset como confirmación).
5. **Idealización**: construir el modelo de cada vertical (emparrillado / lámina DKMQ / barras+
   resortes / barras articuladas / columna+resorte / muro).

---

## Frontera (contratos del núcleo) — respétala

- **C1 (`iso19650-openbim`):** lectura/escritura IFC + modelo neutro físico/estructural + Alignment.
  Aquí **crece** con el parser estructural de puente (clave nueva aditiva). Es su sitio natural.
- **C5 (`motor-fem`):** **no se toca** (este PT no es un peldaño FEM).
- **`puentes`:** crece con la **capa de lectura** (adaptador IFC neutro→idealización) por tipología;
  la idealización, IAP-11, EC2/EC3/EC7 y write-back **ya existen** (PT 7.1–7.3) y no se reescriben.
- **`motor-calculo-estructural`:** no se migra; se **reutilizan** sus parsers de cimentación/muro por
  PYTHONPATH (frontera de reuso entre plugins).

---

## Decisiones a resolver y documentar (antes de mover una línea)

- **Ubicación del parser estructural:** en **C1 (`iso19650`)** —recomendado, coherente con el lineal/
  MEP— vs dentro de `puentes`. `[confirmar AN]`
- **Estrategia de clasificación:** geometría+orientación primero, Pset como respaldo (patrón
  `clasificador.py` de edificación) vs Pset obligatorio. Recomendado: **geometría primero**.
- **Profundidad geométrica:** ¿leer geometría extruida real (perfiles/mallas) o **apoyarse en Psets**
  de dimensiones que escribe narración→IFC? Recomendado: **híbrido** (Psets de dimensiones + ejes;
  geometría fina solo donde haga falta), por robustez. `[confirmar AN]`
- **Cobertura por tipología y orden:** ¿las 6 a la vez o por olas? Recomendado: **(1) cimentación +
  muro/estribo** (reuso casi directo de `motor-calculo`), **(2) pila + aparato de apoyo**, **(3)
  tablero** (vigas sobre Alignment → losa → pórtico → celosía). `[confirmar AN]`
- **Validación del lector:** round-trip **paramétrico↔IFC** — generar IFC desde un `entrada_caso`,
  leerlo y comprobar que el `entrada_caso` reconstruido **reproduce el resultado** del caso
  paramétrico equivalente (PUE-01..06) dentro de tolerancia. Tolerancias propuestas: geometría exacta
  (1e-6 relativo), aprovechamientos 1e-3.
- **Aparato de apoyo en el IFC:** ¿`IfcBearing` (IFC 4.3) o `IfcDiscreteElement`+Pset? Recomendado:
  `IfcBearing` si el generador lo soporta, con Pset de rigideces. `[confirmar AN]`

---

## Los 10 casos de aplicación (PUE-07…PUE-16), IFC-driven

Cada caso: **generar IFC** (geometría + Psets; eje por Alignment) → **lector** → idealización →
`motor-fem` → IAP-11 → comprobación → **memoria + write-back al IFC**. Entregable por caso: carpeta
`Casos-de-uso/caso-PUE-NN-…` con el `.ifc` de entrada, `entrada_caso.json` (reconstruido por el
lector), `resultado_*.json`, el `.ifc` con resultados (write-back), `memoria-*.md` y `README.md`.
Más un índice `Casos-de-uso/INDICE-PUE.md` con veredictos y aprovechamientos.

| # | Caso | Vertical(es) | Escenario | Demuestra |
|---|------|--------------|-----------|-----------|
| 07 | Paso superior vigas artesa, 3 vanos | vigas pretensadas | L≈30 m, 2 carriles LM1, HP-45, **Alignment recto** | lector tablero + eje Alignment |
| 08 | Losa postesada ancha de un vano | losa postesada | losa biaxial, calzada inset, apoyo puntual | lector lámina + objetivo `esfuerzo_lamina` |
| 09 | Marco de paso inferior bajo terraplén | pórtico | empuje **K0**, 2 carriles | lector marco + resortes |
| 10 | Pasarela peatonal en celosía | celosía | sobrecarga peatonal, **confort dinámico (modal)** | lector celosía + modal |
| 11 | Pila alta esbelta sobre **pilotes** | pila + pilotes | H≈14 m, 2.º orden relevante | lector pila + reuso parser **pilotes** |
| 12 | Pila sobre **encepado de 2 pilotes** | pila + encepado | cimentación profunda en grupo | lector pila + reuso parser **encepado** |
| 13 | Estribo **cerrado integral** (K0) | estribo | empuje **reposo K0** | reuso parser **muro** + selector K0 |
| 14 | Estribo **abierto** alto, gran sobrecarga | estribo | empuje **activo Ka** + sobrecarga | reuso parser muro + Ka |
| 15 | **Puente completo integrado** (insignia) | todos | tablero (2 vanos) + 2 estribos + 1 pila; **modo acoplado** (reacciones reales del tablero) | cadena tablero→apoyo→pila/estribo→cimentación en un IFC |
| 16 | **Rediseño** (NO CUMPLE → ajuste) | pila o estribo | geometría insuficiente → ajuste a CUMPLE | el tool detecta el fallo; valor iterativo |

Cobertura: 4 verticales de tablero (07-10), 3 cimentaciones de pila —zapata (en PUE-05), pilotes (11),
encepado (12)—, ambos empujes de estribo (K0 13 / Ka 14), modo **acoplado** (15), **modal** (10) y
**rediseño** (16).

---

## Lee primero, en este orden

1. `Hoja-de-ruta_Ola7-puentes-y-motor-FEM.md` — **§4/§5** (tipologías, transversales) y el **registro
   v1.4** (cierre PT 7.3 + decisiones cerradas de subestructura).
2. `Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` — el modelo neutro físico/estructural y
   cómo **añadir una clave nueva** (el modelo estructural de puente) sin romper.
3. **El plugin `puentes` v0.3.0** (`puentes/scripts/`): los `idealizacion/*.py` definen el **esquema
   de parámetros objetivo** que el lector debe producir (`emparrillado.py`, `losa_lamina.py`,
   `portico.py`, `celosia.py`, `pila.py`, `estribo.py`, `comun/aparatos_apoyo.py`); los `run_all_*.py`
   muestran el flujo a alimentar; `comun/resultado_ifc_puente.py` el write-back.
4. **`iso19650-openbim` v0.8.0**: `scripts/lineal/ifc_to_model_lineal.py` (+ `generate_test_ifc_lineal`,
   `validacion_alineacion`) y `scripts/mep/ifc_to_model_mep.py` (**patrón** de parser IFC→neutro);
   `skills/narracion-a-ifc/scripts/spec_to_ifc.py` + `catalogo_ifc.py` (generación de IFC).
5. **`motor-calculo-estructural` v0.23.0**: `clasificador.py` + `run_all_edificio.py` (clasificación
   multi-elemento), `scripts/muros-contencion/solver_muro.py::parse_auto`,
   `scripts/pilotes/solver_pilote.py::parse`, `scripts/bielas-tirantes/run_all_encepado.py::parse`,
   `scripts/cimentaciones/solver_zapata.py` (parsers IFC de cimentación/muro a reutilizar).
6. `criterios-despacho.md` — lecciones PT 7.1–7.3 (gotchas de idealización, reuso, entorno) y la
   lección nueva de subestructura (PyNite ausente, copia byte-fiel, modal ARPACK).

---

## Entregable

- **`iso19650-openbim` vX.Y (.plugin)**: nuevo parser estructural de puente
  (`scripts/estructural/ifc_to_model_estructural.py`) + validación; clave aditiva del modelo neutro
  (C1). Núcleo espejado intacto.
- **`puentes` v0.4.0 (.plugin)**: capa de lectura `scripts/lectura/desde_ifc.py` (adaptador IFC
  neutro→idealización por tipología) + enganche en los `run_all_*` (acepta `--ifc`). Idealización/
  comprobación/write-back **sin reescribir**. `scripts/nucleo/` espejado. README/CHANGELOG/plugin.json
  (`description` ≤500). **`motor-fem` sin cambios.**
- **`caso-PUE-07…PUE-16`** documentados (IFC de entrada + lectura + … + memoria + write-back al IFC)
  + `Casos-de-uso/INDICE-PUE.md`.
- **Actualizar**: hoja de ruta Ola 7 (PT 7.3.1 ✅ → PT 7.4 🔜), hoja maestra, C1 (clave nueva),
  `criterios-despacho.md` (lección del lector) y la memoria del proyecto.
- **Puertas de calidad obligatorias** (pega su salida en el cierre):
  `TMPDIR=/tmp HOME=/tmp PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py <plugin>.plugin --ref <previo>.plugin`
  (**APTO**, `description` ≤500) para `puentes` v0.4.0 e `iso19650` vX.Y, **y**
  `verificar_espejo_nucleo.py --canonico <motor>.plugin <plugin>.plugin` (**ESPEJOS IDÉNTICOS**), **y**
  el **arnés de validación del lector** (round-trip paramétrico↔IFC reproduce PUE-01..06 dentro de
  tolerancia) + los 10 casos e2e.

---

## Notas de método (críticas, confirmadas en PT 4.x–7.3)

- **Entorno / ifcopenshell:** `/tmp/pylibs` puede quedar **read-only** de una sesión previa (propietario
  `nobody`) → **instala `ifcopenshell` en un target limpio** `pip install --no-cache-dir --target=/tmp/ifclib ifcopenshell`
  (verificado: trae numpy/shapely/lark; v0.8.5) y ejecuta con `PYTHONPATH=/tmp/ifclib:/tmp/pylibs`.
  numpy/scipy en `/tmp/pylibs`. Re-extraer fuentes de los `.plugin` (sobreviven al reinicio del sandbox).
  Exportar siempre **`TMPDIR=/tmp HOME=/tmp PIP_NO_CACHE_DIR=1`**.
- **Hazard de mount:** los ficheros **editados con Edit** se leen **truncados** desde el shell; los
  creados con **Write** se leen íntegros. **Desarrolla y testea en `/tmp`**; **reconstruye el `.plugin`
  y los verificadores en `/tmp`** desde el contenido íntegro; `cp /tmp→workspace` escribe bytes
  correctos (verifícalo por tamaño exacto). Ejecuta los verificadores con `TMPDIR=/tmp HOME=/tmp`.
- **Disco `/sessions`** puede estar al **100 %**: las extracciones de los verificadores deben caer en
  `/tmp` (de ahí `TMPDIR=/tmp`); libera `/sessions/<sesión>/tmp/{esp_nuc_*,verif_*}`. Excluye
  `__pycache__`/`*.pyc` al empaquetar.
- **PyNite no está en el sandbox** (ni vendorizado). `solver_muro`/`solver_pilote`/`ec2_strut_tie`
  importan PyNite a nivel de módulo → para reutilizar sus **parsers** habrá que aislarlos (importar
  solo la función de parseo sin disparar el import de PyNite, o copiar byte-fiel la parte de parseo),
  como se hizo en PT 7.3 con `empujes`/`pesos`/`ka_*` y la capacidad axil/biela-tirante.
- **Reutiliza, no reescribas:** Alignment (`ifc_to_model_lineal`), parsers de cimentación/muro
  (`motor-calculo`), clasificación (`clasificador.py`), generación (`narración→IFC`), idealización/
  comprobación/write-back (`puentes` v0.3.0). La regla de oro: *"¿qué es realmente nuevo (clasificar +
  extraer geometría del tablero/pila + mapear a la idealización) y qué ya está?"* — solo se construye
  lo primero.
- Todo es **predimensionado, a revisar y firmar por técnico competente** (ICCP); NDP `[confirmar AN]`.

**Empieza** leyendo los documentos (hoja de ruta §4/§5 + registro v1.4, **C1**, el plugin `puentes`
v0.3.0 —esquemas de idealización objetivo—, los parsers de `iso19650` —Alignment/MEP— y de
`motor-calculo` —muro/zapata/pilote/encepado—), y **proponiendo, antes de mover una línea: (a)** la
**arquitectura del lector** (parser estructural en C1 + adaptador por tipología en `puentes`) y el
esquema del modelo neutro estructural de puente; **(b)** la **estrategia de clasificación y extracción**
por tipología (qué se lee de geometría, qué de Psets, cómo se resuelven las asociaciones); **(c)** el
**plan de validación** (round-trip paramétrico↔IFC que reproduzca PUE-01..06) y el **orden de los 10
casos** PUE-07..16, con tolerancias.
