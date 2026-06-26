# Texto de inicio — PT 4.3 (Ola 4): nace `instalaciones` — solver hidráulico de red + bases de demanda (H3)

> Copia y pega el bloque siguiente al iniciar el hilo nuevo en el proyecto **Estructurando**.
> Da todo el contexto necesario sin información adicional.

---

Proyecto Estructurando. Ejecuta el **PT 4.3 de la Ola 4**: **nace la disciplina `instalaciones`** —
crea el **plugin `instalaciones`** (+ agente `ingeniero-de-instalaciones`) y, sobre el **modelo neutro
de red** que ya emite el parser MEP del PT 4.2, añade el **solver hidráulico de red** (pérdida de carga
a presión) y las **bases de demanda (hueco H3)**, **arrancando por PCI** (BIE). Reutiliza el **núcleo
transversal** (`ifc_utils` + `grafo_red`, PT 4.1) y el **dominio IFC MEP** (PT 4.2, `iso19650-openbim`
v0.4.0) **sin romperlos**. Es el cierre de los huecos **H3** (bases de demanda) y del **motor
hidráulico de red** (decisión abierta nº4, parte de cálculo). Trabaja con el patrón de agente de
disciplina (el mismo de `ingeniero-estructurista`). El parser MEP (lectura IFC→neutro) **se queda en
`iso19650-openbim`**; el **solver y la demanda son de `instalaciones`** (frontera C1 lectura ↔ C4
demanda ↔ disciplina cálculo).

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ecosistema-ingenieria.md` — §3 (mapa de plugins; `instalaciones` "a crear", 1 plugin
   con subagentes PCI/eléctricas/clima; `description` ≤ 500), §4 ("**capacidad transversal emergente:
   motor hidráulico de red**" y los contratos C1–C4), §5 (disciplina **Instalaciones**: PCI/REBT/RITE),
   §6 (olas; este hilo es Ola 4) y §8 (decisiones: nº1 instalaciones = **un plugin con subagentes**, ya
   resuelta; nº4 núcleo compartido, **parcialmente abierta** — unificar los espejos, ver INC-10).
2. `Nucleo-transversal/Verificacion-Ola1.md` — hueco **H3** (bases de demanda = el "slot" C4 para
   disciplinas no estructurales) y el **dry-run §5** (cómo enchufa `instalaciones` por C1/C2/C3/C4).
3. `Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` — §4 (dominio MEP: el **modelo neutro de red**
   `unidades`/`sistema`/`nodos`/`tramos`/`terminales`/`fuentes`, ya **implementado** en PT 4.2, con la
   clave `demanda` prevista por terminal/sistema = el gancho H3; y la nota "**cálculo MEP ≠ FEM**:
   hidráulico Darcy-Weisbach/Hazen-Williams"). Es la **entrada** del solver.
4. **Entregables del PT 4.2 (tu punto de partida de E/S):** `iso19650-openbim/scripts/mep/`
   (`ifc_to_model_mep.py` parser, `generate_test_ifc_mep.py`, `validacion_red.py`, `test_red_mep.py`,
   `README.md`), `iso19650-openbim/scripts/nucleo/` (núcleo **espejado**), y el caso de extremo a
   extremo `Casos-de-uso/caso-MEP-01-red-pci/` (red PCI fuente → 4 tramos → 3 BIE; modelo neutro +
   verificación CUMPLE). El plugin reempaquetado es `iso19650-openbim-v0.4.0.plugin`.
5. `criterios-despacho.md`, `Casos-de-uso/REPOSITORIO-aprendizaje.md` (lección **PT 4.2** —reúso del
   núcleo, frontera núcleo/disciplina, **clave de entidad IFC = `entity.id()` no `id()` de Python**,
   hazard de mount; **INC-10** reempaquetar plugin read-only + unificar el núcleo espejado) y
   `Casos-de-uso/CHANGELOG-plugin.md` + `iso19650-openbim/CHANGELOG.md` (entrada v0.4.0).
6. **Normativa PCI** (la conoce ya el ecosistema): `cte-documentos-basicos:normativa-concurrente`
   (RIPCI — RD 513/2017; abastecimiento UNE 23500; BIE UNE-EN 671; rociadores UNE-EN 12845) y
   `cte-documentos-basicos:db-si-sua` (DB-SI, dotación de instalaciones de protección). Marca los NDP
   como `[confirmar AN]`.

**Objetivo y alcance (qué hay que hacer):**

1. **Plugin `instalaciones` + agente `ingeniero-de-instalaciones`.** Patrón de agente de disciplina:
   `clasificar (sistema PCI/eléctrico/clima desde el IFC MEP) → enrutar al subagente/solver → orquestar
   (IFC → modelo neutro de red [PT 4.2] → demanda → solver de red → verificación normativa → memoria) →
   visualizar → registrar criterios`. Subagentes previstos: **PCI**, **eléctricas (REBT)**, **clima
   (RITE)**; este PT implementa **PCI** como primer vertical (los otros dos quedan esbozados).
2. **Solver hidráulico de red (a presión).** Sobre los `nodos`+`tramos` del modelo neutro MEP: pérdida
   de carga por tramo (**Darcy-Weisbach** o **Hazen-Williams** `[confirmar AN/criterio]`), balance de
   caudales en nudos, propagación de presiones desde la(s) `fuentes` y **comprobación en terminales**
   (BIE: caudal y presión dinámica mínimos `[confirmar AN]`). El **núcleo da la topología, el solver
   calcula** (frontera del PT 4.1/4.2). Arnés de verificación propio (balance de caudales ≈ 0 %,
   presiones admisibles), análogo al de equilibrio estructural.
3. **Bases de demanda (hueco H3).** Skill/módulo de **bases de demanda** que rellena la clave `demanda`
   del modelo neutro (caudales/ocupación/simultaneidad). Para PCI: nº de BIE/rociadores simultáneos y
   caudal de cálculo según RIPCI/UNE `[confirmar AN]`. Es el "slot" **C4** para disciplinas no
   estructurales (aclarar C4 en consecuencia).
4. **Memoria y criterios (C2/C3).** `criterios-instalaciones.md` (raíz, desde
   `Nucleo-transversal/plantilla-criterios-disciplina.md`), `memoria-instalaciones.md` por obra (desde
   `plantilla-memoria.md`, 7 apartados), skill `criterios-memoria` del plugin, y `Casos-de-uso/` propio
   (PROGRAMA/REPOSITORIO/CHANGELOG) si procede. Reutiliza `docx`/`pdf`.
5. **Caso PCI de extremo a extremo.** Toma `caso-MEP-01-red-pci` (o uno nuevo más completo) y pásalo por
   demanda → solver → verificación → memoria, con resultado dimensionado (DN, presiones, caudales) y, si
   da tiempo, **escribe los Psets de resultado de red** de vuelta al IFC vía `iso19650-openbim:ifc-create`.

**Decisión a resolver y documentar (antes de mover una línea):**
- **El núcleo (`ifc_utils`+`grafo_red`) hoy está DUPLICADO**: canónico incubado en
  `motor-calculo-estructural/scripts/nucleo/` y **espejo** en `iso19650-openbim/scripts/nucleo/` (PT 4.2).
  `instalaciones` también lo necesita. **¿Se promueve YA a un módulo compartido único** (resolver del
  todo la decisión nº4 e **INC-10**) **o se mantiene el patrón de espejo** (otro espejo en
  `instalaciones`)? Propón la frontera y **qué plugin(es) se reempaquetan** y con qué `--ref`.
- **Frontera C1↔disciplina:** confirma que la **lectura IFC MEP** (parser/validación) se queda en
  `iso19650-openbim` y que **solver + demanda** viven en `instalaciones` (consumiendo el modelo neutro).

**Entregable:**
- Plugin `instalaciones` (agente + subagente PCI + solver de red + bases de demanda + skills de memoria),
  con **micro-test** del solver (balance de caudales/presiones) y un **caso PCI de extremo a extremo** que
  pase (red leída por el parser MEP del PT 4.2 → demanda → solver → verificación CUMPLE → memoria).
- Actualizar contratos: **C4** (aclarar bases de demanda para disciplinas no estructurales),
  `Verificacion-Ola1.md` (**H3 → ✅**), la hoja de ruta (Ola 4: H1/H2/H3 ✅; motor hidráulico nacido) y,
  si se unifica el núcleo, C1 §3bis / decisión nº4 / INC-10.
- Registrar: lección en `REPOSITORIO-aprendizaje.md` (+ fila/INC si aplica), entrada SemVer en el
  CHANGELOG del/los plugin(s) que toques, y **subir versión + reempaquetar** ese/esos `.plugin`.
- **Puerta de calidad obligatoria** antes de dar por bueno cada paquete:
  `PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py <nuevo>.plugin
  --ref <previo>.plugin` (APTO, exit 0). `description` ≤ 500 caracteres; `--allow-shrink` solo para
  encogimientos intencionados y auditados.

**Notas de método:** las herramientas de fichero (Read/Write/Edit) son la **fuente de verdad** (el shell
del sandbox sirve copias **truncadas/stale** de markdown y de `.py`/`.json` recién editados, de forma
persistente — **no los edites por shell**; si necesitas ejecutar/empaquetar algo editado, **reconstrúyelo
en `/tmp` por heredoc y empaqueta desde `/tmp`**, con `ast.parse` + salto de línea final por fichero).
Toolchain Python en `/tmp/pylibs` (ifcopenshell 0.8.5) → ejecuta con `PYTHONPATH=/tmp/pylibs`. **Clave de
entidad IFC = `entity.id()` (STEP), NUNCA `id()` de Python** (causa no-determinismo). Si reempaquetas un
plugin instalado read-only, **reconstruye su fuente en la carpeta + `chmod -R u+w`** y entrega el
`.plugin` versionado a reinstalar (no se activa en vivo). Construye el ZIP en `/tmp` y cópialo con
`cat > destino`, **nombre versionado** (no sobrescribas), excluyendo `__pycache__`/`node_modules`/`*.pyc`.
Empaquetado **acumulativo** desde la última versión íntegra. Todo es **predimensionado, a revisar y
firmar por técnico competente**; NDP marcados `[confirmar AN]`.

**Empieza** leyendo los documentos, el núcleo (`scripts/nucleo/`) y los entregables MEP del PT 4.2
(`iso19650-openbim/scripts/mep/` + `caso-MEP-01-red-pci`), y **proponiendo la frontera** (qué calcula el
solver de red, cómo se rellena la demanda, dónde vive cada pieza, si se unifica el núcleo y qué plugin(s)
se reempaquetan) **antes de mover una sola línea**.
