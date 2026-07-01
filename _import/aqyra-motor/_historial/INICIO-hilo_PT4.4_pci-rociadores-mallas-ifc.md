# Texto de inicio — PT 4.4 (Ola 4): completar el motor hidráulico de red — rociadores (UNE-EN 12845) + solver de mallas + write-back de resultados al IFC

> Copia y pega el bloque siguiente al iniciar el hilo nuevo en el proyecto **Estructurando**.
> Da todo el contexto necesario sin información adicional.
>
> *(Ruta recomendada: profundizar el vertical PCI y endurecer el motor de red. Si prefieres
> abrir antes otro vertical —eléctricas REBT o clima RITE—, la estructura del PT y de la
> frontera C1/CN-3 es la misma; cambia solo el solver y las bases de demanda.)*

---

Proyecto Estructurando. Ejecuta el **PT 4.4 de la Ola 4**: **completa el motor hidráulico de red y el
vertical PCI** del plugin **`instalaciones`** (v0.1.0, nacido en el PT 4.3). Tres frentes que se apoyan
entre sí: (1) **solver de mallas** (redes con bucles, hoy el solver solo resuelve árboles), (2) **rociadores
automáticos** según **UNE-EN 12845** (segundo vertical PCI, con redes típicamente **malladas** que motivan
el solver anterior), y (3) **write-back de los Psets de resultado al IFC** (cierra el ciclo
IFC→cálculo→IFC, **diferido** en el PT 4.3). Reutiliza el **núcleo transversal** (`ifc_utils` + `grafo_red`,
espejado), el **dominio IFC MEP** (`iso19650-openbim` v0.4.0) y el **motor hidráulico** del PT 4.3 **sin
romperlos**. Mantén la frontera **C1 lectura (iso19650) ↔ CN-3 demanda ↔ cálculo (instalaciones)**.

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ecosistema-ingenieria.md` — §3 (mapa de plugins; `instalaciones` ✅ v0.1.0, subagente
   PCI ✅, rociadores pendiente; `description` ≤ 500), §4 ("**motor hidráulico de red**" y los contratos
   C1, CN-1, CN-2 y CN-3), §5 (disciplina **Instalaciones**: PCI/REBT/RITE), §6 (Ola 4; H1/H2/H3 ✅) y §8 (decisiones:
   nº1 ✅ un plugin con subagentes, nº4 ✅ patrón de espejo + puerta de integridad).
2. `instalaciones/` (el plugin a ampliar): `scripts/red/solver_red.py` (solver **a presión Darcy-Weisbach**,
   reparto por **árbol** BFS — **avisa pero no resuelve mallas**: ese es el frente 1),
   `scripts/red/verificacion_red.py` (arnés balance de caudales ≈0 % + presiones), `scripts/red/
   test_solver_red.py`, `scripts/pci/bases_demanda.py` (H3, slot CN-3: BIE; **rociadores no implementado**),
   `scripts/pci/run_all_pci.py`, `scripts/nucleo/` (espejo del núcleo), `agents/` y `CHANGELOG.md`.
3. `Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` — §4 (modelo neutro de red MEP; el solver lo
   consume) y **§5 Salida IFC (escritura)**: enriquecer el IFC con **Psets de resultado** (DN dimensionado,
   caudal, velocidad, presión) vía `iso19650-openbim:ifc-create` — es la entrada del frente 3.
4. **Entregables del PT 4.3 (tu punto de partida):** `Casos-de-uso/caso-PCI-01-bie-presion/` (modelo
   neutro → demanda → solver → verificación **CUMPLE**, balance 0,0 %; memoria md+docx); plugin
   `instalaciones-v0.1.0.plugin`; la puerta de espejo `Nucleo-transversal/verificar_espejo_nucleo.py`.
5. `criterios-instalaciones.md` (raíz), `Casos-de-uso/REPOSITORIO-aprendizaje.md` (lección **PT 4.3** —
   patrón de agente de disciplina, frontera C1/CN-3, motor hidráulico, decisión nº4 cerrada como espejo;
   trampas de mount y `entity.id()`), `instalaciones/CHANGELOG.md` y `Casos-de-uso/CHANGELOG-plugin.md`.
6. **Normativa PCI** (ya en el ecosistema): `cte-documentos-basicos:normativa-concurrente` (RIPCI —
   RD 513/2017; rociadores **UNE-EN 12845**; abastecimiento UNE 23500) y `cte-documentos-basicos:db-si-sua`
   (DB-SI, dotación de instalaciones de protección). Marca los NDP como `[confirmar AN]`.

**Objetivo y alcance (qué hay que hacer):**

1. **Solver de mallas (redes con bucles).** Hoy `solver_red.resolver` reparte caudales por **árbol** (raíz =
   fuente) y solo **avisa** si hay mallas. Implementa el **reparto hiperestático** en redes no arborescentes
   manteniendo Darcy-Weisbach y la API: balance de caudales en nudos + pérdida de carga nula en cada bucle
   (**Hardy-Cross** o **Newton-Raphson nodal** `[confirmar criterio]`). El **núcleo da la topología** (detecta
   los bucles: nº tramos − nº nodos + componentes); el **solver resuelve** los caudales de malla. El arnés
   de verificación debe cerrar **balance de caudales ≈ 0 %** también en malla. Micro-test con una malla de
   2 bucles contrastada (suma de pérdidas en cada lazo ≈ 0).
2. **Rociadores automáticos (UNE-EN 12845).** Segundo vertical PCI (subagente `proyectista-pci` ampliado o
   uno nuevo). **Bases de demanda** por **densidad de descarga × área de operación** según clase de riesgo
   (LH / OH1–4 / HHP–HHS) `[confirmar AN]`, nº de rociadores del **área más desfavorable**, **factor K** del
   rociador (Q = K·√p). Comprobación: caudal y presión en el rociador más desfavorable y **curva
   demanda vs abastecimiento** (punto de funcionamiento). Rellena la clave `demanda` (H3) para rociadores,
   igual que BIE. Caso típico **mallado** → ejercita el frente 1.
3. **Write-back de resultados al IFC (cierra IFC→cálculo→IFC; diferido del PT 4.3).** Escribe los **Psets de
   resultado de red** (DN dimensionado, caudal, velocidad, presión por tramo; presión disponible/margen por
   terminal) de vuelta al IFC vía `iso19650-openbim:ifc-create`. Valida con `iso19650-openbim:ifc-validate`.
   Visualiza con `visor-ifc` si procede.
4. **Memoria y registros.** Actualiza `memoria-instalaciones.md` del caso, `criterios-instalaciones.md`
   (lección de mallas/rociadores), `Casos-de-uso/` (nuevo caso e2e), el CHANGELOG del/los plugin(s) y la
   hoja de ruta (rociadores ✅; motor de red con mallas). Reutiliza `docx`/`pdf`.
5. **Caso PCI de rociadores de extremo a extremo.** Genera (o toma) un IFC MEP de una **red mallada de
   rociadores**, pásalo por demanda (densidad/área) → solver de mallas → verificación CUMPLE → memoria, con
   DN/presiones/caudales dimensionados y, si procede, los Psets de resultado escritos al IFC.

**Decisión a resolver y documentar (antes de mover una línea):**
- **Método del solver de mallas:** **Hardy-Cross** (clásico, transparente, converge bien en redes pequeñas)
  vs **Newton-Raphson nodal** (más robusto y general). Propón cuál y por qué; mantén el arnés de balance.
- **Dónde vive la escritura de Psets de resultado:** la **semántica** de qué escribir es de la disciplina
  (`instalaciones`), pero la **mecánica IFC** es de la capa transversal. Decide si (a) se amplía
  `iso19650-openbim:ifc-create` con una utilidad de "Psets de resultado de red" (reempaqueta **iso19650 →
  v0.4.1**, con `--ref` v0.4.0) o (b) `instalaciones` invoca la skill `ifc-create` existente sin tocar
  iso19650 (no reempaqueta iso19650). Propón la frontera y qué plugin(es) se reempaquetan.
- **Frontera C1↔disciplina (recordatorio):** la lectura/escritura IFC es de `iso19650-openbim`; demanda +
  solver (árbol y malla) son de `instalaciones`, sobre el modelo neutro de red.

**Entregable:**
- `instalaciones` ampliado (**solver de mallas** + **rociadores UNE-EN 12845** + **write-back de Psets de
  resultado**), con **micro-test** de malla (balance de caudales y cierre de pérdida por lazo) y un **caso de
  rociadores de extremo a extremo** que pase (IFC mallado → demanda densidad/área → solver de mallas →
  verificación CUMPLE → memoria, y resultados escritos al IFC si se incluye el frente 3).
- Actualizar: hoja de ruta (Ola 4: rociadores ✅; motor de red con mallas), C1 §5 (escritura de Psets de
  resultado de red), `REPOSITORIO-aprendizaje.md` (lección + INC si aplica), CHANGELOG del/los plugin(s) que
  toques (`instalaciones` → v0.2.0; `iso19650-openbim` → v0.4.1 solo si se elige la opción (a)).
- **Puerta de calidad obligatoria** antes de dar por bueno cada paquete:
  `PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py <nuevo>.plugin --ref <previo>.plugin`
  (APTO, exit 0; usa `--ref` la versión previa íntegra de ese plugin) **y**
  `python3 Nucleo-transversal/verificar_espejo_nucleo.py --canonico motor-...-v0.23.0.plugin <plugin(s) con núcleo>`
  (ESPEJOS IDÉNTICOS). `description` ≤ 500 caracteres; `--allow-shrink` solo para encogimientos auditados.

**Notas de método:** las herramientas de fichero (Read/Write/Edit) son la **fuente de verdad** (el shell del
sandbox sirve copias **truncadas/stale** de markdown y de `.py`/`.json` —incluso de ficheros estables, como
le pasó a `verificar_empaquetado.py` en el PT 4.3—, de forma persistente; **no los edites ni los ejecutes
fiándote del shell**: reconstruye en `/tmp` por heredoc lo que vayas a ejecutar/empaquetar, con `ast.parse`
+ salto de línea final por fichero). Toolchain Python en `/tmp/pylibs` (ifcopenshell 0.8.5) → ejecuta con
`PYTHONPATH=/tmp/pylibs`; el **solver y la demanda de `instalaciones` son stdlib pura** (solo el parser de
`iso19650-openbim` usa ifcopenshell). Para `docx`: `npm install -g` falla por permisos → instala local en
`/tmp` (`npm install docx`) + `NODE_PATH=/tmp/node_modules`. Clave de entidad IFC = `entity.id()` (STEP),
**NUNCA** `id()` de Python. Si reempaquetas un plugin instalado read-only, reconstruye su fuente + `chmod -R
u+w` y entrega el `.plugin` versionado a reinstalar (no se activa en vivo); construye el ZIP en `/tmp`,
cópialo con `cat > destino`, nombre versionado, excluyendo `__pycache__`/`node_modules`/`*.pyc`;
**mantén el núcleo espejado idéntico** (la puerta `verificar_espejo_nucleo.py` lo verifica). Empaquetado
**acumulativo** desde la última versión íntegra. Todo es **predimensionado, a revisar y firmar por técnico
competente** (Ingeniero de Caminos); NDP marcados `[confirmar AN]`.

**Empieza** leyendo los documentos, el plugin `instalaciones` (`scripts/red/` + `scripts/pci/`) y el caso
`caso-PCI-01-bie-presion`, y **proponiendo** (antes de mover una sola línea): el método del solver de mallas,
las bases de demanda de rociadores (densidad/área/K), dónde vive la escritura de Psets de resultado y qué
plugin(s) se reempaquetan.
