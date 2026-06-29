INICIO de hilo — PT 7.2 (Ola 7): **completar el grupo lineal de puentes** sobre el motor ya
maduro — **losa postesada**, **pórtico** y **celosía** —, reusando **`motor-fem` v0.2.0 (FEM-1)**
sin subir de peldaño y ampliando la disciplina **`puentes`** con sus nuevos verticales.

Proyecto Estructurando. Ejecuta el **PT 7.2 de la Ola 7 (puentes)**. El PT 7.1 ya entregó el
peldaño **FEM-1** del motor (`motor-fem` v0.2.0: **modal** + **cargas móviles / líneas de
influencia**, módulo aditivo `fem1.py`, estático FEM-0 **sin regresión**) y **nació la disciplina
`puentes` v0.1.0** (agente `ingeniero-de-puentes` + subagente `proyectista-vigas-pretensadas`;
idealización por **emparrillado** barra+barra, **acciones IAP-11**, inyección del **pretensado**,
comprobación **EC2**, memoria y **write-back**; caso `caso-PUE-01-vigas-pretensadas` **CUMPLE**).
Ahora se **completa el grupo de tipologías lineales y frecuentes** del mapa de la Ola 7,
**consumiendo el motor tal cual** (FEM-0/FEM-1 ya bastan): este PT añade **verticales nuevos a
`puentes`**, no un peldaño nuevo del núcleo.

> Todo cálculo y entregable es de **predimensionado/asistencia y debe ser revisado y firmado por
> técnico competente** (Ingeniero de Caminos, Canales y Puertos). Los NDP se marcan `[confirmar AN]`.

**Alcance confirmado en la planificación (Ola 7, mapa de tipologías §4 de la hoja de ruta):**
- **Losa postesada** — idealización por **lámina plana** (DKMQ) + **postesado biaxial**; reutiliza el
  **postesado ya existente** (`motor-calculo-estructural/scripts/pretensado/`: `balance_2d.py`,
  `solver_losa_postesada.py`, `verificacion_losa_postesada.py`, caso 13) como **cargas equivalentes**
  en dos direcciones; acciones **IAP-11** (LM1 + térmica + viento) y comprobación **EC2**.
- **Pórtico** (marco) — idealización por **barras + suelo (resortes Winkler)**; acciones IAP-11 +
  **2.º orden ligero** + **empuje de tierras** (reusa `muros-contencion`/EC7); comprobación **EC2/EC7**.
- **Celosía** — idealización por **barras articuladas** (releases de extremo, ya soportados); acciones
  IAP-11 + **fatiga** de uniones (EC3-1-9, daño acumulado, categorías de detalle); comprobación **EC3**
  (reusa `acero-ec3`).
- **El motor `motor-fem` NO sube de peldaño** en este PT: se queda en **FEM-1**. Solo se admite una
  **extensión aditiva menor** si la losa postesada exige objetivos de **esfuerzo de lámina** en el
  barrido móvil/líneas de influencia (hoy `fem1.movil` resuelve objetivos de barra y reacción; ver
  decisión abierta nº1). Si se añade, es **C5 §3 aditivo sin romper** y con su parche de validación.
- **PyNite sigue siendo solo oráculo de test** del núcleo; los verticales nuevos **consumen** el
  motor propio (C5) y **no recalculan** la mecánica.

**Dónde encaja en la Ola 7 (mapa, para situar el hilo):**
- **PT 7.0 ✅ — Cimiento del motor (FEM-0):** `motor-fem` v0.1.0. **Entregado.**
- **PT 7.1 ✅ — Disciplina `puentes` + IAP-11 + cargas móviles (FEM-1):** `motor-fem` v0.2.0 +
  `puentes` v0.1.0 (vigas pretensadas e2e). **Entregado.**
- **PT 7.2 (este hilo) — Completar el grupo lineal:** **losa postesada**, **pórtico**, **celosía**
  (sobre FEM-0/FEM-1).
- **PT 7.3 —** subestructura: pilas, apoyos, estribos y cimentaciones de puente.
- **PT 7.4 —** cajón (FEM-2: lámina curva + rigidizadores + pared delgada) · habilita Ola 3.
- **PT 7.5…7.7 —** metálico/mixto/oblicuo/curvo (FEM-2); arco (FEM-3); atirantado (FEM-4).
  Ver `Hoja-de-ruta_Ola7-puentes-y-motor-FEM.md`.

> **Frontera (contratos del núcleo) — respétala:**
> - **C1 (`iso19650-openbim`):** lectura/escritura IFC + modelo neutro físico/estructural y
>   **Alignment** (Ola 5). **No se toca** salvo clave nueva aditiva.
> - **C5 (`motor-fem`):** mallado + ensamblaje + solver (estático/**modal**/**móvil**). En FEM-1.
>   **No conoce IAP-11 ni tipologías.** Solo se amplía de forma **aditiva** si hace falta el objetivo
>   de esfuerzo de lámina en `fem1.movil` (decisión nº1).
> - **`puentes` (vertical):** idealización (losa=lámina, pórtico=barras+resortes, celosía=barras
>   articuladas), **acciones IAP-11**, **postesado/empuje/fatiga**, comprobación **EC2/EC3/EC7**,
>   memoria y **write-back**. **Consume** C5 y C1.
> - **`motor-calculo-estructural`:** no se migra; se **reutilizan** sus módulos (postesado, muros/EC7,
>   acero/EC3) por **PYTHONPATH** (frontera de reuso entre plugins, como en PT 7.1 con `ec2_pretensado`).

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ola7-puentes-y-motor-FEM.md` — **§4** (filas *losa postesada*, *pórtico*, *celosía*:
   idealización y transversales clave), **§5** (IAP-11, líneas de influencia, fases+diferidos), **§6**
   (PT 7.2), **§10** (decisiones).
2. `Nucleo-transversal/C5_Contrato-motor-FEM.md` — **§2/§3** (modelo de análisis; `analisis="modal"|
   "movil"` ya implementados; objetivos de `cargas_moviles`), **§4** (librería: **lámina DKMQ** para
   la losa), **§8** (cómo extender sin romper si hace falta el objetivo de esfuerzo de lámina).
3. **El plugin `puentes` v0.1.0 a ampliar** (`puentes/scripts/`): `idealizacion/emparrillado.py`
   (de barra+barra a **barra+lámina**/lámina para la losa; barras+resortes para el pórtico; barras
   articuladas para la celosía), `acciones/iap11.py` (ya tiene permanentes/LM1/térmica/viento/
   combinaciones — reutilizable), `comprobacion/` (añadir EC2-losa, EC2/EC7-pórtico, EC3+fatiga-celosía),
   `run_all_*` por tipología, `comun/resultado_ifc_puente.py` (mapping de write-back). **Recordatorio
   crítico del PT 7.1:** construir el `ModeloFEM` con **`estabilizar_plano=False`** (tablero horizontal
   flecta fuera de plano) y, si hay láminas, pasarles `rho` para el modal; la térmica va en **formato
   nativo** (no por `desde_modelo_neutro`).
4. **El motor `motor-fem` v0.2.0** (`scripts/fem1.py` + `fem_core.py` + `elementos/lamina.py`): el
   **modal** y el **móvil** ya existen; la lámina **DKMQ** ya está; si se necesita el objetivo
   `esfuerzo_lamina` en `fem1.movil`, ahí se añade (aditivo) con su validación.
5. **Los módulos a reutilizar** (`motor-calculo-estructural` v0.23.0, por PYTHONPATH):
   `scripts/pretensado/` (`balance_2d.py`/`solver_losa_postesada.py`/`verificacion_losa_postesada.py`
   — **postesado biaxial** ✅, caso 13), `scripts/muros-contencion/` (empuje de tierras + EC7 para el
   pórtico), `scripts/barras/` y la skill `acero-ec3` (EC3 para la celosía).
6. Casos y puertas: `Casos-de-uso/caso-PUE-01-vigas-pretensadas` (patrón a replicar);
   crear `caso-PUE-02-losa-postesada`, `caso-PUE-03-portico`, `caso-PUE-04-celosia`;
   `Nucleo-transversal/verificar_empaquetado.py` y `verificar_espejo_nucleo.py`;
   `criterios-despacho.md` (lecciones PT 7.1: módulo aditivo, gotcha `estabilizar_plano`, cortante por
   bielas, hazards de entorno).

**Objetivo y alcance (qué hay que hacer):**
1. **Ampliar `puentes` a v0.2.0** con tres verticales nuevos (subagentes + scripts):
   - **Losa postesada** (`proyectista-losa-postesada`): idealización **lámina DKMQ** (+ vigas de borde
     como barras si procede); **postesado biaxial** como cargas equivalentes (reusa `balance_2d.py`);
     acciones IAP-11 (LM1 sobre la losa + térmica + viento); comprobación **EC2** (flexión biaxial,
     punzonamiento si hay apoyos puntuales, fisuración, tensiones). Decisión: **láminas vs emparrillado
     denso** para el reparto y para las **líneas de influencia** (objetivo de lámina vs banda de barras).
   - **Pórtico** (`proyectista-portico`): idealización **barras + resortes** (suelo Winkler en
     cimentación); acciones IAP-11 + **empuje de tierras** (reposo/activo) + **2.º orden ligero**;
     comprobación **EC2** (dinteles/pilas) y **EC7** (cimentación). Reusa `muros-contencion`.
   - **Celosía** (`proyectista-celosia`): idealización **barras articuladas** (releases); acciones
     IAP-11; comprobación **EC3** (tracción/compresión/pandeo de barras y **uniones**) + **fatiga**
     (EC3-1-9, daño acumulado por LM3/categorías de detalle). Reusa `acero-ec3`.
2. **(Solo si la losa lo exige) extensión aditiva de `motor-fem`** a v0.2.1: objetivo
   `esfuerzo_lamina` en `fem1.movil` (líneas de influencia de momento de placa) + parche de validación
   analítico (placa simplemente apoyada bajo carga móvil / banda equivalente). **Sin regresión** del
   estático y del móvil de barras. Si no se necesita, **el motor no se toca** y se documenta por qué.
3. **Casos e2e**: `caso-PUE-02-losa-postesada`, `caso-PUE-03-portico`, `caso-PUE-04-celosia`
   (IFC/Alignment o modelo neutro → idealización → IAP-11 → motor-fem → comprobación EC → memoria +
   write-back). Veredicto y aprovechamientos por tipología.
4. **Actualizar**: hoja de ruta Ola 7 (PT 7.2 ✅ → PT 7.3 🔜), hoja maestra (estado `puentes` v0.2.0),
   `C5` (si hubo extensión aditiva), `criterios-despacho.md` (lección + INC si aplica) y la memoria
   del proyecto.

**Decisiones a resolver y documentar (antes de mover una línea):**
- **Idealización de la losa postesada**: **lámina DKMQ** (placa) — recomendado, casa con el postesado
  biaxial y el punzonamiento — **vs emparrillado denso** de barras. Y, ligado a ello, cómo obtener las
  **líneas de influencia / envolventes LM1** en la losa: **objetivo de esfuerzo de lámina** en
  `fem1.movil` (extensión aditiva nº2) **vs** banda de barras equivalente. `[confirmar AN]`
- **Subagentes**: **tres subagentes** (`proyectista-losa-postesada`, `proyectista-portico`,
  `proyectista-celosia`) — recomendado, coherente con el patrón del ecosistema — **vs** uno genérico
  parametrizado. 
- **Pórtico**: modelo del **suelo** (resorte Winkler distribuido vs apoyos elásticos puntuales) y del
  **empuje de tierras** (reposo K0 vs activo Ka); ¿2.º orden ligero ya o diferido a FEM-3? `[confirmar AN]`
- **Celosía**: **fatiga** ¿se implementa ya (LM3 + categorías de detalle EC3-1-9, daño Palmgren-Miner)
  o se deja gancho para un PT de fatiga? Releases por barra (articulación pura) vs nudos rígidos.
  `[confirmar AN]`
- **Postesado de la losa**: pérdidas **simplificadas** (coherente con la decisión nº5 del PT 7.1) y
  **trazado biaxial** (bandas en pilares + distribuidos) con `balance_2d.py`. `[confirmar AN]`
- **Convención de ejes/esfuerzos**: respetar la del núcleo (X,Y horizontales, Z vertical, −Z gravedad;
  barra `Iy`=mayor; placa `[Mx,My,Mxy]`) y `estabilizar_plano=False` para el tablero horizontal.

**Entregable:**
- **`puentes` v0.2.0 (.plugin)**: 3 subagentes nuevos + `scripts/` (idealización lámina/barras+resortes/
  barras articuladas + comprobaciones EC2/EC7/EC3+fatiga + run_all por tipología + write-back),
  `scripts/nucleo/` espejado, `README.md` + `CHANGELOG.md` + `plugin.json` (`description` ≤500).
- **(Opcional) `motor-fem` v0.2.1**: objetivo `esfuerzo_lamina` en `fem1.movil` + validación, **sin
  regresión**; o justificación de que no se toca.
- **`caso-PUE-02/03/04`** documentados (idealización → … → memoria + write-back).
- **Actualizar** hoja de ruta Ola 7, hoja maestra, `C5` (si aplica), `criterios` y memoria del proyecto.
- **Puertas de calidad obligatorias** (pega su salida en el cierre):
  `PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py <plugin>.plugin`
  (**APTO**, exit 0; `description` ≤500) para `puentes` v0.2.0 (y `motor-fem` v0.2.1 si se toca) **y**
  `verificar_espejo_nucleo.py --canonico <motor>.plugin <puentes>.plugin` (**ESPEJOS IDÉNTICOS**) **y**
  el **arnés de validación** (FEM-1 sin regresión; parche de la extensión de lámina si se añade;
  casos PUE-02/03/04 e2e).

**Notas de método (críticas, confirmadas en PT 4.x–7.1):**
- **Entorno**: `/tmp/pylibs` puede no existir al arrancar (el sandbox se reinicia) → reinstalar
  `pip install --no-cache-dir --target=/tmp/pylibs numpy scipy` con **`TMPDIR=/tmp HOME=/tmp
  PIP_NO_CACHE_DIR=1`** (si `/sessions` está lleno, pip falla con "No space"). Re-extraer las fuentes
  de los `.plugin` del workspace (sobreviven al reinicio). Ejecutar con `PYTHONPATH=/tmp/pylibs`.
- **Hazard de mount**: el shell **lee truncados** los ficheros de texto editados del workspace
  (Read/Write/Edit son la fuente de verdad). **Desarrolla y testea en `/tmp`**; **reconstruye el
  `.plugin` y los verificadores en `/tmp`** desde el contenido íntegro; copia el `.plugin` con nombre
  versionado (`cp`). **`cp` de /tmp→workspace SÍ escribe bytes correctos** (verifícalo por tamaño exacto).
- **Disco `/sessions`** puede estar al 100 %: libera borrando `/sessions/<sesión>/tmp/{esp_nuc_*,
  verif_*}` (extracciones de los verificadores); no borres datos del usuario. Excluye `__pycache__`/
  `*.pyc` al empaquetar y al copiar la fuente.
- **Gotcha del grillage/losa (PT 7.1)**: `mallador.desde_modelo_neutro` con `estabilizar_plano=True`
  mata la flexión de un tablero horizontal → **`estabilizar_plano=False`**; láminas necesitan `rho`
  (atributo `el.rho`) para el modal; la **térmica** va en formato nativo. **Cortante** de puente por
  **bielas (V_Rd,max) + cercos**, no V_Rd,c sin armadura.
- **Reutiliza, no reescribas**: postesado biaxial (`balance_2d.py`), empuje/EC7 (`muros-contencion`),
  EC3/fatiga (`acero-ec3`), líneas de influencia/modal (motor-fem v0.2.0) y write-back (iso19650) ya
  están. La regla de oro: *"¿qué es realmente nuevo (idealización de cada tipología, su comprobación)
  y qué ya está en el núcleo?"* — solo se construye lo primero.
- Todo es **predimensionado, a revisar y firmar por técnico competente** (ICCP); NDP marcados
  `[confirmar AN]`.

**Empieza** leyendo los documentos (hoja de ruta §4/§5/§6, **C5 §2/§3/§4/§8**, el **plugin `puentes`
v0.1.0** a ampliar, el **motor v0.2.0** y los **módulos a reutilizar**), y **proponiendo, antes de
mover una sola línea: (a)** la **idealización** de cada tipología (losa=lámina DKMQ; pórtico=barras+
resortes+empuje; celosía=barras articuladas+fatiga) y si hace falta la **extensión aditiva** del
objetivo de esfuerzo de lámina en `fem1.movil`; **(b)** la **estructura de los nuevos verticales** de
`puentes` (subagentes + scripts + reuso por PYTHONPATH del postesado/EC7/EC3); y **(c)** el **plan de
validación** (parche analítico de la losa/celosía + no-regresión del motor + casos PUE-02/03/04 e2e),
con las tolerancias propuestas.
