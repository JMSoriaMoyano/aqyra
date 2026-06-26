# Texto de inicio — PT 4.6 (Ola 4): verificación de la Ola 4 (motor de red multi-vertical: PCI + REBT) antes del cierre

> Copia y pega el bloque siguiente al iniciar el hilo nuevo en el proyecto **Estructurando**.
> Da todo el contexto necesario sin información adicional.
>
> *(Ruta recomendada: consolidar y verificar lo construido en la Ola 4 —el motor de red y sus dos
> verticales, PCI y eléctricas— antes de abrir el tercer vertical (clima/RITE), igual que el PT 1.6
> verificó la Ola 1 antes de avanzar. El tercer vertical (RITE) queda como PT posterior; este PT decide
> si la Ola 4 se cierra con RITE o si RITE pasa a una sub-ola, y deja una base certificada.)*

---

Proyecto Estructurando. Ejecuta el **PT 4.6 de la Ola 4**: **verificación y consolidación de la Ola 4**
(el **motor de red** del ecosistema y sus dos verticales ya construidos: **PCI** —BIE + rociadores— y
**eléctricas REBT**), análogo a lo que el **PT 1.6** hizo con la Ola 1. **No** construyas un vertical
nuevo: el objetivo es **certificar** que la cadena IFC→neutro→demanda→solver→verificación→write-back→
validación es coherente, **sin regresiones**, con los contratos C1–C4 respetados, las puertas de calidad
en verde y el núcleo espejado idéntico; y dejar un **checklist "listo para el tercer vertical (clima/RITE)"**
y para la Ola 5. Respeta la frontera **C1 lectura/escritura (iso19650) ↔ C4 demanda ↔ cálculo (instalaciones)**.

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ecosistema-ingenieria.md` — §3 (mapa de plugins: `motor-calculo-estructural` v0.23.0,
   `iso19650-openbim` v0.4.2, `instalaciones` v0.3.0; `description` ≤ 500), §4 (núcleo y contratos C1–C4;
   "motor hidráulico de red" y el **solver eléctrico** como **dos solvers sobre el mismo grafo**), §5
   (Instalaciones: PCI ✅ / REBT ✅ / RITE esbozado), §6 (Ola 4; PT 4.1–4.5 ✅) y §8 (decisiones nº1, nº4).
2. `Nucleo-transversal/Verificacion-Ola1.md` — **es la plantilla de este PT**: estructura del informe de
   verificación, checklist "listo para nueva disciplina", detección del defecto de empaquetado y el backlog.
   Replica ese formato para la Ola 4.
3. `Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` (§4 modelo neutro de red MEP **agnóstico al
   sistema**; §5/§5bis write-back de Psets de resultado y **validación sistema-aware** Pipe/Cable/Duct) y
   `Nucleo-transversal/C2_…`/`C3_…` (memoria/entregables) + el "slot **C4**" de demanda (no estructural).
4. **Plugins empaquetados a auditar:** `motor-calculo-estructural-v0.23.0.plugin` (canónico del núcleo),
   `iso19650-openbim-v0.4.2.plugin` (parser MEP + write-back + validador sistema-aware),
   `instalaciones-v0.3.0.plugin` (verticales PCI y REBT; `scripts/red`+`scripts/pci`+`scripts/electrico`+
   `scripts/nucleo` espejado). Y las puertas `Nucleo-transversal/verificar_empaquetado.py` y
   `Nucleo-transversal/verificar_espejo_nucleo.py`.
5. **Casos e2e a re-ejecutar (regresión):** `caso-MEP-01-red-pci`, `caso-PCI-01-bie-presion`,
   `caso-PCI-02-rociadores-malla` (PCI) y `caso-REBT-01-vivienda`, `caso-REBT-02-terciario` (REBT). Más
   los **micro-test**: `instalaciones/scripts/nucleo/test_grafo_red.py`, `…/red/test_solver_red.py`
   (árbol + mallas) y `…/electrico/test_solver_electrico.py`.
6. `criterios-instalaciones.md` (raíz), `Casos-de-uso/REPOSITORIO-aprendizaje.md` (lecciones PT 4.1–4.5 y
   backlog de incidencias INC-01…INC-11; el *hazard* de mount), `instalaciones/CHANGELOG.md` e
   `iso19650-openbim/CHANGELOG.md`.

**Objetivo y alcance (qué hay que hacer — verificar, no construir):**

1. **Coherencia de contratos C1–C4 con la implementación multi-vertical.** Comprueba que el **modelo
   neutro de red** es realmente agnóstico al sistema (PCI hidráulico y REBT eléctrico lo consumen igual);
   que la frontera **C1 (lectura/escritura iso19650) ↔ C4 (demanda) ↔ cálculo (instalaciones)** se
   mantiene en los dos verticales; y que el **write-back** (mecánica en iso19650, semántica en
   instalaciones, mismo `Pset_Estructurando_ResultadoRed`) y la **validación sistema-aware**
   (Pipe/Cable/Duct) son consistentes. Documenta cualquier divergencia.
2. **Regresión integral (sin tocar código salvo para corregir defectos).** Re-ejecuta **todos** los
   micro-test y los **5 casos e2e** desde `/tmp` (reconstruidos), y confirma: PCI **sin regresión** tras
   las adiciones de REBT (PCI-01/02 con los mismos veredictos y cifras), REBT CUMPLE/APTO, balances ≈0,
   ΔU/presiones dentro de límite. Recoge una **tabla resumen** (caso · sistema · veredicto · cifra clave).
3. **Puertas de calidad sobre los 3 plugins.** `verificar_empaquetado.py` (con `--ref` a la versión
   previa íntegra de cada uno) **APTO** y `verificar_espejo_nucleo.py` (canónico motor v0.23.0)
   **ESPEJOS IDÉNTICOS** en `iso19650-openbim` e `instalaciones`. Audita la **identidad md5** del núcleo
   (`scripts/nucleo/`) en los tres plugins. `description` ≤ 500 en todos.
4. **Auditoría de defectos de empaquetado** (como el truncado que cazó el PT 1.6/PT 4.4): confirma que
   los `.plugin` entregados no truncan ningún `.py`, no llevan artefactos (`__pycache__`/`node_modules`/
   `*.pyc`) y que **workspace vs `.plugin` no divergen** en ficheros clave (atención a `.md` que el
   empaquetado reconstruyó en `/tmp` y pudo no sincronizarse al workspace — lección del PT 4.5).
5. **Checklist "listo para el tercer vertical (clima/RITE)" y para la Ola 5.** Igual que el PT 1.6 dejó
   el checklist de "nueva disciplina": ¿qué reutiliza RITE del núcleo (grafo de red, unidades, IFC,
   write-back, validador sistema-aware con `AIRCONDITIONING→Duct` ya previsto) y qué es realmente nuevo
   (solver de conductos / cargas térmicas, demanda RITE/DB-HE)? Deja el hueco preparado.
6. **Cerrar/registrar incidencias.** Revisa el backlog INC y marca lo resuelto en la Ola 4; abre INC si
   la verificación destapa algo (p. ej. la divergencia workspace↔`.plugin` de `.md`, o la aproximación
   "feeder mono+tri = trifásico equilibrado" del solver eléctrico).

**Decisión a resolver y documentar:**
- **¿Se cierra la Ola 4 con RITE antes de la Ola 5, o RITE pasa a un PT posterior** (sub-ola 4.x) dejando
  la Ola 4 "cerrada en lo verificado" (núcleo de red + PCI + REBT)? Propón y justifica.
- **Estado de las capacidades transversales:** "motor hidráulico de red" y "solver eléctrico" como **dos
  solvers sobre el mismo grafo** — confirma que esta es la abstracción a anunciar al núcleo (la Ola 6 de
  obras hidráulicas reutilizará el grafo + un solver Manning, lámina libre).

**Entregable:**
- `Nucleo-transversal/Verificacion-Ola4.md` (nuevo), con el formato del `Verificacion-Ola1.md`: coherencia
  de contratos, tabla de regresión (micro-test + 5 casos), resultado de las puertas en los 3 plugins,
  auditoría del núcleo espejado, checklist "listo para clima/RITE" y para la Ola 5, y el backlog/INC
  actualizado.
- Actualizar: `Hoja-de-ruta_Ecosistema-ingenieria.md` (estado de la Ola 4 tras la verificación; decisión
  sobre RITE) y `Casos-de-uso/REPOSITORIO-aprendizaje.md` (entrada PT 4.6 + INC si aplica). **No** se
  reempaqueta ningún plugin salvo que la verificación destape un defecto que haya que corregir (en ese
  caso, reempaquetado acumulativo + puertas).

**Puerta de calidad obligatoria** (ejecútalas y pega su salida en el informe):
`PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py <plugin> --ref <previo>`
(APTO, exit 0, para `iso19650-openbim-v0.4.2` vs v0.4.1 y `instalaciones-v0.3.0` vs v0.2.0) **y**
`python3 Nucleo-transversal/verificar_espejo_nucleo.py --canonico motor-calculo-estructural-v0.23.0.plugin iso19650-openbim-v0.4.2.plugin instalaciones-v0.3.0.plugin`
(ESPEJOS IDÉNTICOS). Si corriges algún defecto, vuelve a pasarlas. `description` ≤ 500; `--allow-shrink`
solo para encogimientos auditados.

**Notas de método (críticas, confirmadas en PT 4.4/4.5):** las herramientas de fichero (Read/Write/Edit)
son la **fuente de verdad**; el shell del sandbox sirve copias **truncadas/stale** de ficheros
**pre-existentes** (incluidos `.py`/`.json`/`.md` no editados en el hilo, p. ej. `solver_red.py`,
`plugin.json`, las propias puertas), pero **los ficheros NUEVOS se leen íntegros** y **los `.plugin`
(ZIP) extraen íntegros**. Por tanto: para ejecutar/verificar, **reconstruye el árbol en `/tmp`
extrayendo cada `.plugin` con `unzip`** (fuente íntegra) y, para un fichero suelto pre-existente que
necesites (p. ej. una puerta truncada), **léelo con la herramienta Read (íntegro) y reconstrúyelo en
`/tmp` por heredoc** (con `ast.parse`). Usa un **directorio `/tmp` nuevo** (los previos pueden tener
ficheros read-only de sesiones anteriores). Toolchain Python en `/tmp/pylibs` (ifcopenshell 0.8.5) →
ejecuta con `PYTHONPATH=/tmp/pylibs`; el solver y la demanda de `instalaciones` son **stdlib pura** (solo
el parser/escritor/validador de `iso19650-openbim` usan ifcopenshell). Para `docx`/`pdf`: pandoc
disponible, o `npm install docx` local en `/tmp` + `NODE_PATH=/tmp/node_modules`. Clave de entidad IFC =
`entity.id()` (STEP), **NUNCA** `id()` de Python. Empaquetado **acumulativo** desde la última versión
íntegra (solo si hay que corregir). Todo es **predimensionado, a revisar y firmar por técnico competente**
(Ingeniero de Caminos); NDP marcados `[confirmar AN]`.

**Empieza** leyendo los documentos y los tres plugins, **reconstruyendo el banco de pruebas en `/tmp`**
(extrae los `.plugin`, copia los casos), y **proponiendo el plan de verificación** (qué micro-test y casos
re-ejecutas, en qué orden corres las puertas, y cómo contrastas workspace↔`.plugin`) **antes** de emitir
el `Verificacion-Ola4.md`.
