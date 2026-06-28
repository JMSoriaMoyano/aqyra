# Texto de inicio — PT 4.5 (Ola 4): segundo vertical de Instalaciones — eléctricas (REBT): bases de demanda + solver de red eléctrica (caída de tensión)

> Copia y pega el bloque siguiente al iniciar el hilo nuevo en el proyecto **Estructurando**.
> Da todo el contexto necesario sin información adicional.
>
> *(Ruta recomendada: abrir el vertical eléctrico, que reutiliza el patrón de disciplina y el grafo
> de red ya maduros. Si prefieres abrir antes **clima/RITE**, la estructura del PT y de la frontera
> C1/CN-3 es idéntica: cambian solo el solver —conductos de aire / cargas térmicas— y las bases de
> demanda. Tras eléctricas + clima, la Ola 4 se cierra con un PT de verificación, como hizo el PT 1.6
> con la Ola 1.)*

---

Proyecto Estructurando. Ejecuta el **PT 4.5 de la Ola 4**: abre el **segundo vertical de la disciplina
`instalaciones`** — **instalaciones eléctricas de baja tensión (REBT)**. Replica el **patrón de agente de
disciplina** ya probado en PCI: nuevo subagente `proyectista-electrico`, **bases de demanda eléctrica**
(slot CN-3) y un **solver de red eléctrica** (caída de tensión / intensidades / sección de conductor) sobre
el **mismo modelo neutro de red**. Reutiliza el **núcleo transversal** (`ifc_utils` + `grafo_red`,
espejado), el **dominio IFC MEP** (`iso19650-openbim` v0.4.1, sistema `ELECTRICAL`) y, donde aplique, el
**write-back de Psets de resultado** del PT 4.4, **sin romperlos**. Mantén la frontera **C1 lectura/escritura
(iso19650) ↔ CN-3 demanda ↔ cálculo (instalaciones)**.

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ecosistema-ingenieria.md` — §3 (mapa de plugins; `instalaciones` ✅ v0.2.0 con PCI
   completo, eléctricas/clima esbozadas; `description` ≤ 500), §4 (núcleo y contratos C1, CN-1, CN-2 y CN-3; "motor
   hidráulico de red" como capacidad transversal — el solver eléctrico es **otro solver sobre el mismo
   grafo**), §5 (disciplina Instalaciones: PCI ✅ / **REBT** / RITE), §6 (Ola 4; PT 4.1–4.4 ✅) y §8
   (decisiones: nº1 ✅ un plugin con subagentes, nº4 ✅ espejo + puerta de integridad).
2. `instalaciones/` (el plugin a ampliar, **v0.2.0**): `scripts/red/solver_red.py` (solver hidráulico
   Darcy-Weisbach, árbol y **malla por Hardy-Cross** — el patrón de propagación por árbol y el grafo te
   sirven de plantilla para la **propagación de tensiones**), `scripts/red/verificacion_red.py` (arnés:
   balance de caudales con signo + cierre por lazo), `scripts/pci/bases_demanda.py` (slot CN-3: BIE +
   rociadores; **plantilla** para la demanda eléctrica), `scripts/red/resultado_ifc.py` (semántica del
   write-back), `scripts/pci/run_all_pci.py` (orquestador), `scripts/nucleo/` (espejo del núcleo),
   `agents/ingeniero-de-instalaciones.md` (clasifica `sistema.tipo`: ELECTRICAL → REBT) y
   `agents/proyectista-pci.md` (patrón de subagente a replicar), `CHANGELOG.md`.
3. `Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` — §4 (modelo neutro de red MEP; el parser
   `ifc_to_model_mep.py` es **agnóstico al tipo de sistema** y ya emite `sistema`/`nodos`/`tramos`/
   `terminales`/`fuentes`/`demanda`) y **§5/§5bis** (escritura de Psets de resultado de red — reutilizable
   para resultados eléctricos: sección, caída de tensión, intensidad).
4. **Entregables del PT 4.4 (tu punto de partida):** `Casos-de-uso/caso-PCI-02-rociadores-malla/` (IFC
   mallado → demanda → solver de mallas → verificación **CUMPLE** → write-back; memoria md+docx);
   plugins `instalaciones-v0.2.0.plugin` e `iso19650-openbim-v0.4.1.plugin`; la puerta de espejo
   `Nucleo-transversal/verificar_espejo_nucleo.py`.
5. `criterios-instalaciones.md` (raíz; ya cita REBT/RITE como esbozados), `Casos-de-uso/
   REPOSITORIO-aprendizaje.md` (lección **PT 4.4** — Hardy-Cross, rociadores, write-back, hazard de mount
   en ficheros pre-existentes editados vs nuevos íntegros; frontera C1/CN-3), `instalaciones/CHANGELOG.md`
   e `iso19650-openbim/CHANGELOG.md`.
6. **Normativa eléctrica** (en el ecosistema): `cte-documentos-basicos:normativa-concurrente` (**REBT**,
   RD 842/2002) y `cte-documentos-basicos:db-he` (HE3 iluminación, HE5 autoconsumo) si procede. Marca los
   NDP como `[confirmar AN]`.

**Objetivo y alcance (qué hay que hacer):**

1. **Bases de demanda eléctrica (slot CN-3).** Nuevo `scripts/electrico/bases_demanda_electrica.py` (o
   amplía `bases_demanda.py` con dispatcher por `sistema.tipo`): **previsión de potencias** por circuito,
   **coeficientes de simultaneidad y utilización** y grado de electrificación según **REBT ITC-BT-10**
   (previsión de cargas), **ITC-BT-25** (viviendas: circuitos C1–C12, electrificación básica/elevada),
   **ITC-BT-44/-47** (receptores) `[confirmar AN]`. Rellena la clave `demanda` por terminal (potencia,
   cosφ, monofásico/trifásico) y por sistema (tensión nominal, simultaneidad), igual que en PCI.
2. **Solver de red eléctrica.** Nuevo `scripts/electrico/solver_electrico.py` sobre el **modelo neutro de
   red** (reutiliza `grafo_red` del núcleo para la topología): redes BT típicamente **radiales** (árbol;
   no necesitan Hardy-Cross — reutiliza la propagación por árbol del solver hidráulico como plantilla).
   Calcula por tramo: **intensidad** (I = P/(U·cosφ) mono / P/(√3·U·cosφ) tri), **caída de tensión
   acumulada** (ΔU = 2·L·I·cosφ/(γ·S) mono / √3·L·I·cosφ/(γ·S) tri, γ conductividad Cu/Al `[confirmar
   AN]`) y propuesta/comprobación de **sección**. Arnés `verificacion_electrico.py`: balance de potencias,
   **caída de tensión acumulada ≤ límite** (ITC-BT-19: 3 % alumbrado / 5 % fuerza en interiores; DI/LGA
   según concentración de contadores) `[confirmar AN]`, e **intensidad ≤ admisible** del conductor
   (ITC-BT-19, según aislamiento PVC/XLPE e instalación).
3. **Write-back de resultados al IFC (reutiliza el frente 3 del PT 4.4).** Escribe los Psets de resultado
   eléctricos (sección dimensionada, intensidad, caída de tensión acumulada por tramo; potencia/cosφ por
   terminal) vía `iso19650-openbim:ifc-create:escribir_psets_resultado.py` (la **mecánica** ya existe; solo
   aportas la **semántica** desde `instalaciones`). Valida con `iso19650-openbim:ifc-validate`.
4. **Subagente y orquestación.** Nuevo subagente `proyectista-electrico` (análogo a `proyectista-pci`);
   amplía el agente `ingeniero-de-instalaciones` para enrutar `ELECTRICAL → REBT` y orquestar
   IFC→neutro→demanda eléctrica→solver eléctrico→verificación→write-back→memoria.
5. **Memoria y registros.** `memoria-instalaciones.md` del caso, `criterios-instalaciones.md` (lección
   eléctrica), `Casos-de-uso/` (nuevo caso e2e), CHANGELOG del/los plugin(s) y la hoja de ruta (REBT ✅).
   Reutiliza `docx`/`pdf`.
6. **Caso eléctrico de extremo a extremo.** Genera (o toma) un IFC MEP de una red eléctrica radial
   (`ELECTRICAL`: cuadro/fuente → líneas → terminales: luminarias/tomas) → demanda → solver eléctrico →
   verificación CUMPLE → memoria, con secciones/intensidades/caídas dimensionadas y los Psets de resultado
   escritos al IFC.

**Decisión a resolver y documentar (antes de mover una línea):**
- **Método del solver:** caída de tensión por **intensidades** (I·R, con cosφ y mono/trifásico) vs por
  **momentos eléctricos** (Σ P·L). Propón cuál y por qué; mantén el arnés (balance de potencias + ΔU
  acumulada + I admisible).
- **Dónde viven los datos del conductor** (sección, material Cu/Al, aislamiento): ¿se amplía el **parser
  MEP de `iso19650-openbim`** para leer cables (`IfcCableSegment`/`Pset_CableSegmentTypeCommon`,
  conductor/sección) — reempaqueta **iso19650 → v0.4.2/v0.5.0** con `--ref`— o los aporta la capa de
  **demanda/criterios de `instalaciones`** sobre el modelo neutro (no reempaqueta iso19650)? Propón la
  frontera C1↔disciplina y qué plugin(es) se reempaquetan. (Recordatorio: el modelo neutro ya distingue
  `tramos`/`terminales`/`fuentes`; falta decidir dónde nace la **sección/material del conductor**.)
- **Topología radial vs malla:** confirma que BT es radial (árbol) y que **no** necesita Hardy-Cross
  `[confirmar criterio]`; reutiliza la propagación por árbol (no dupliques el grafo).

**Entregable:**
- `instalaciones` ampliado (**bases de demanda eléctrica** + **solver eléctrico** + write-back +
  subagente `proyectista-electrico`), con **micro-test** del solver eléctrico (caída de tensión contra
  cálculo analítico de un tramo; balance de potencias) y un **caso eléctrico de extremo a extremo** que
  pase (IFC ELECTRICAL → demanda → solver → verificación CUMPLE → memoria, y resultados escritos al IFC).
- Actualizar: hoja de ruta (Ola 4: **REBT ✅**), C1 (lectura de cables si se extiende el parser),
  `REPOSITORIO-aprendizaje.md` (lección + INC si aplica), CHANGELOG del/los plugin(s) que toques
  (`instalaciones` → v0.3.0; `iso19650-openbim` → v0.4.2/v0.5.0 solo si se extiende el parser a cables).
- **Puerta de calidad obligatoria** antes de dar por bueno cada paquete:
  `PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py <nuevo>.plugin --ref <previo>.plugin`
  (APTO, exit 0; usa `--ref` la versión previa íntegra de ese plugin) **y**
  `python3 Nucleo-transversal/verificar_espejo_nucleo.py --canonico motor-...-v0.23.0.plugin <plugin(s) con núcleo>`
  (ESPEJOS IDÉNTICOS). `description` ≤ 500 caracteres; `--allow-shrink` solo para encogimientos auditados.

**Notas de método (críticas, confirmadas en el PT 4.4):** las herramientas de fichero (Read/Write/Edit)
son la **fuente de verdad**; el shell del sandbox sirve copias **truncadas/stale** de los ficheros
**pre-existentes recién editados** (`.py`/`.json`/`.md`), pero **los ficheros NUEVOS se leen íntegros**.
Por tanto: edita/crea vía herramienta de fichero y, para **ejecutar/empaquetar, reconstruye en `/tmp` por
heredoc cada fichero cambiado** (con `ast.parse` + salto de línea final) y **construye el ZIP desde `/tmp`**
(los nuevos se copian del mount); ejecuta también las puertas desde `/tmp` reconstruidas. Toolchain Python
en `/tmp/pylibs` (ifcopenshell 0.8.5) → ejecuta con `PYTHONPATH=/tmp/pylibs`; el **solver y la demanda de
`instalaciones` son stdlib pura** (solo el parser/escritor de `iso19650-openbim` usa ifcopenshell). Para
`docx`: `npm install -g` falla por permisos → instala local en `/tmp` (`npm install docx`) +
`NODE_PATH=/tmp/node_modules`. Clave de entidad IFC = `entity.id()` (STEP), **NUNCA** `id()` de Python. Si
reempaquetas un plugin instalado read-only, reconstruye su fuente + `chmod -R u+w` y entrega el `.plugin`
versionado a reinstalar (no se activa en vivo); construye el ZIP en `/tmp`, cópialo con `cat > destino`,
nombre versionado, excluyendo `__pycache__`/`node_modules`/`*.pyc`; **mantén el núcleo espejado idéntico**
(la puerta `verificar_espejo_nucleo.py` lo verifica). Empaquetado **acumulativo** desde la última versión
íntegra. Todo es **predimensionado, a revisar y firmar por técnico competente** (Ingeniero de Caminos); NDP
marcados `[confirmar AN]`.

**Empieza** leyendo los documentos, el plugin `instalaciones` (`scripts/red/` + `scripts/pci/` como
plantilla) y el caso `caso-PCI-02-rociadores-malla`, y **proponiendo** (antes de mover una sola línea): el
método del solver eléctrico (intensidades vs momentos), las bases de demanda REBT (previsión de cargas,
simultaneidad), dónde nacen los datos del conductor (parser iso19650 vs demanda de instalaciones) y qué
plugin(s) se reempaquetan.
