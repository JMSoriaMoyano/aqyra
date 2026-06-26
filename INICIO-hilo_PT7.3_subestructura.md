INICIO de hilo — PT 7.3 (Ola 7): **subestructura de puente** — **pilas**, **aparatos de apoyo**,
**estribos** y **cimentaciones** —, reusando el motor ya maduro (**`motor-fem` v0.2.1 / FEM-1**)
**sin subir de peldaño** y ampliando la disciplina **`puentes`** con sus nuevos verticales de
subestructura. Proyecto Estructurando. Ejecuta el **PT 7.3 de la Ola 7 (puentes)**.

El PT 7.2 ya **cerró el grupo lineal del tablero**: `puentes` **v0.2.0** (3 verticales nuevos —
**losa postesada** por lámina DKMQ, **pórtico** por barras+resortes Winkler, **celosía** por barras
articuladas; casos `caso-PUE-02/03/04` **CUMPLEN**) y el motor subió a **`motor-fem` v0.2.1** (única
extensión: objetivo **`esfuerzo_lamina`** en `fem1.movil`, **aditivo**, **sin** subir de peldaño —
sigue en **FEM-1**). Ahora se baja del tablero a lo que lo **sostiene**: la **subestructura**.
Este PT añade **verticales nuevos a `puentes`**, **no** un peldaño nuevo del núcleo.

> Todo cálculo y entregable es de **predimensionado/asistencia y debe ser revisado y firmado por
> técnico competente** (Ingeniero de Caminos, Canales y Puertos). Los NDP se marcan `[confirmar AN]`.

**Alcance confirmado en la planificación (Ola 7, mapa de tipologías §4 de la hoja de ruta):**
- **Pilas, apoyos y cimentaciones** — idealización **columna + 2.º orden + rigidez del aparato de
  apoyo**; fase **FEM-0** (→ FEM-3 para esbeltez fina). Reutiliza el **dimensionado de pilares y
  cimentaciones ya existente** (`motor-calculo-estructural/scripts/`: `cimentaciones` —zapata—,
  `pilotes`, `bielas-tirantes` —encepados—) + **aparatos de apoyo** (nuevo) + **IAP-11**.
  Comprobación **EC2/EC3** (fuste), **EC7** (cimentación) y **EC8-2** (sísmica de puente, si procede).
- **Estribos** — idealización **muro + empuje de tierras + cargas de tablero**; fase **FEM-0**.
  Reutiliza **`muros-contencion`** (EC7: vuelco/deslizamiento/hundimiento; EC2: alzado/zapata) +
  las **reacciones del tablero** (de los verticales del PT 7.1/7.2) como cargas de cabeza.
  Comprobación **EC7/EC2**.
- **Aparatos de apoyo** (la pieza realmente nueva, *slot* C4-puentes): traducen las **reacciones del
  tablero** a la subestructura como **resortes** (elastoméricos: `k = G·A/t` por dirección + rigidez
  a giro; POT/esféricos: coacción/liberación por GdL). Cierran el círculo **tablero → apoyo →
  pila/estribo → cimentación**.
- **El motor `motor-fem` NO sube de peldaño** en este PT: se queda en **FEM-1** y **FEM-0 basta**
  (columnas, resortes y muros ya están). El **2.º orden** de pilas se trata por **amplificación
  aproximada** (como en el pórtico del PT 7.2); el P-Δ riguroso / pandeo queda para **FEM-3**
  (decisión abierta nº3). No se admite extensión del núcleo salvo que aparezca una necesidad
  genuina e ineludible (y entonces sería **C5 §3 aditivo sin romper** + su parche de validación).
- **PyNite sigue siendo solo oráculo de test** del núcleo; los verticales nuevos **consumen** el
  motor propio (C5) y **no recalculan** la mecánica.

**Dónde encaja en la Ola 7 (mapa, para situar el hilo):**
- **PT 7.0 ✅ — Cimiento del motor (FEM-0):** `motor-fem` v0.1.0. **Entregado.**
- **PT 7.1 ✅ — Disciplina `puentes` + IAP-11 + cargas móviles (FEM-1):** `motor-fem` v0.2.0 +
  `puentes` v0.1.0 (vigas pretensadas e2e). **Entregado.**
- **PT 7.2 ✅ — Completar el grupo lineal:** `puentes` v0.2.0 (losa postesada, pórtico, celosía) +
  `motor-fem` v0.2.1 (`esfuerzo_lamina`). **Entregado.**
- **PT 7.3 (este hilo) — Subestructura:** **pilas, apoyos, estribos y cimentaciones** de puente
  (sobre FEM-0/FEM-1).
- **PT 7.4 —** cajón (FEM-2: lámina curva + rigidizadores + pared delgada) · habilita Ola 3.
- **PT 7.5…7.7 —** metálico/mixto/oblicuo/curvo (FEM-2); arco (FEM-3); atirantado (FEM-4).
  Ver `Hoja-de-ruta_Ola7-puentes-y-motor-FEM.md`.

> **Frontera (contratos del núcleo) — respétala:**
> - **C1 (`iso19650-openbim`):** lectura/escritura IFC + modelo neutro físico/estructural y
>   **Alignment** (Ola 5). **No se toca** salvo clave nueva aditiva.
> - **C5 (`motor-fem`):** mallado + ensamblaje + solver (estático/**modal**/**móvil**). En **FEM-1**.
>   **No conoce IAP-11, ni aparatos de apoyo, ni tipologías.** No se amplía en este PT salvo necesidad
>   genuina (decisión nº5).
> - **`puentes` (vertical):** idealización (pila=columna+resorte de apoyo; estribo=muro+empuje+cargas
>   de tablero), **acciones IAP-11** + **sísmica EC8-2** (si procede), **aparatos de apoyo**,
>   comprobación **EC2/EC3/EC7/EC8-2**, memoria y **write-back**. **Consume** C5 y C1.
> - **`motor-calculo-estructural`:** no se migra; se **reutilizan** sus módulos (pilares,
>   `cimentaciones`/`pilotes`/`bielas-tirantes`, `muros-contencion`/EC7) por **PYTHONPATH** (frontera
>   de reuso entre plugins, como en PT 7.1–7.2 con `ec2_pretensado`, `balance_2d` y `verificacion_muro`).

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ola7-puentes-y-motor-FEM.md` — **§4** (filas *Pilas, apoyos y cimentaciones* y
   *Estribos*: idealización, fase FEM y transversales clave), **§5** (IAP-11, aparatos de apoyo,
   fases), **§6** (PT 7.3), **§10** (decisiones), y el **registro v1.3** (cierre del PT 7.2).
2. `Nucleo-transversal/C5_Contrato-motor-FEM.md` — **§2/§3** (modelo de análisis; `resolver` con
   estático/modal; **resortes** de nudo `[kx,ky,kz,krx,kry,krz]` ya soportados — son el aparato de
   apoyo y el suelo Winkler), **§4** (barra 3D para la pila), **§8** (cómo extender sin romper, **si**
   hiciera falta).
3. **El plugin `puentes` v0.2.0 a ampliar** (`puentes/scripts/`): `idealizacion/portico.py` (patrón
   de **barras + resortes Winkler** en base — base directa para pila y estribo), `acciones/iap11.py`
   (permanentes/LM1/empuje **K0**/combinaciones — reutilizable; **frenado/arranque** y **sísmica**
   son lo nuevo a añadir), `comprobacion/ec2ec7_portico.py` (EC2 fuste + **EC7** hundimiento/
   deslizamiento con la reacción real de base — patrón a replicar), `comun/resultado_ifc_puente.py`
   (despacho de write-back por tipología — añadir `pila`/`estribo`), `run_all_*` por tipología.
   **Recordatorios críticos de PT 7.2:** construir con **`estabilizar_plano=True`** (marco/columna
   plano XZ); el **deslizamiento/EC7 por la reacción REAL de base** (no el empuje total); 2.º orden
   por **amplificación aproximada**; **hazard de mount** (ficheros editados con Edit se leen
   truncados → autorar en `/tmp` + `TMPDIR=/tmp`).
4. **El motor `motor-fem` v0.2.1** (`scripts/fem_core.py` + `elementos/barra.py` + `mallador.py` +
   `fem1.py`): la **barra 3D**, los **resortes de nudo** (`add_resorte`) y el **modal/móvil** ya
   existen; el aparato de apoyo es un **resorte** (no toca el núcleo).
5. **Los módulos a reutilizar** (`motor-calculo-estructural` v0.23.0, por PYTHONPATH):
   `scripts/cimentaciones/` (zapata aislada, EC7+EC2 — casos 5/8), `scripts/pilotes/` (pilote/grupo),
   `scripts/bielas-tirantes/` (encepado, regiones D — caso 4), `scripts/muros-contencion/` (estribo:
   empuje + EC7 + armado, `verificacion_muro`/`solver_muro`). La skill **`geotecnia-sismico-ec7-ec8`**
   (EC7 capacidad portante/asientos/empujes; **EC8** espectro/ductilidad) para la sísmica de puente.
6. Casos y puertas: `Casos-de-uso/caso-PUE-03-portico` y `caso-PUE-01..04` (patrón a replicar);
   crear `caso-PUE-05-pila-cimentacion` y `caso-PUE-06-estribo`;
   `Nucleo-transversal/verificar_empaquetado.py` y `verificar_espejo_nucleo.py`;
   `criterios-despacho.md` (lecciones PT 7.2: resortes de base, EC7 por reacción real, 2.º orden
   aproximado, gotcha `estabilizar_plano`, hazards de entorno).

**Objetivo y alcance (qué hay que hacer):**
1. **Ampliar `puentes` a v0.3.0** con los verticales de subestructura (subagentes + scripts):
   - **Pila + aparato de apoyo + cimentación** (`proyectista-pilas-apoyos`): idealización **columna**
     (barra 3D) con **aparato de apoyo en cabeza** (resorte: elastomérico `k=G·A/t` + giro; POT
     liberando giros) que recibe las **reacciones del tablero** (permanentes + envolvente LM1 + viento
     + **frenado/arranque** + térmica + **sísmica EC8-2** si procede); **base** sobre la **cimentación**
     (zapata / pilotes / encepado — **enruta** al módulo de `motor-calculo` según el tipo); **2.º
     orden aproximado** del fuste. Comprobación **EC2** (fuste: flexión compuesta N-M + cortante),
     **EC7** (cimentación) y, si se activa, **EC8-2**.
   - **Estribo** (`proyectista-estribos`): idealización **muro/estribo** con **empuje de tierras**
     (activo Ka / reposo K0 según movilidad) + **cargas de tablero** en cabeza (reacción vertical +
     frenado horizontal) + **sobrecarga de tierras** del relleno; reutiliza **`muros-contencion`**
     (EC7 vuelco/deslizamiento/hundimiento; EC2 alzado/puntera/talón). Comprobación **EC7/EC2**.
   - **Aparatos de apoyo** (módulo común): biblioteca de **rigideces de apoyo** (elastomérico,
     POT, esférico) → vector de **resorte** `[kx,ky,kz,krx,kry,krz]` por aparato, y el **reparto**
     de las reacciones del tablero a las pilas/estribos.
2. **(Solo si aparece una necesidad genuina) extensión aditiva de `motor-fem`** — en principio **no
   se toca** (columna + resortes + modal/móvil ya bastan). Si surgiera (p. ej. autovalores de pandeo
   para esbeltez fina), sería **FEM-3** y **se sale de este PT**: documentarlo y dejar el gancho.
3. **Casos e2e**: `caso-PUE-05-pila-cimentacion` (pila intermedia con aparato de apoyo + zapata o
   encepado) y `caso-PUE-06-estribo` (estribo con empuje + cargas de tablero) — IFC/Alignment o modelo
   neutro → idealización → IAP-11 (+EC8-2) → motor-fem → comprobación EC → memoria + write-back.
4. **Actualizar**: hoja de ruta Ola 7 (PT 7.3 ✅ → PT 7.4 🔜), hoja maestra (estado `puentes` v0.3.0),
   `C5` (solo si hubo extensión aditiva), `criterios-despacho.md` (lección + INC si aplica) y la
   memoria del proyecto.

**Decisiones a resolver y documentar (antes de mover una línea):**
- **Subagentes**: **dos subagentes** (`proyectista-pilas-apoyos` y `proyectista-estribos`) —
  recomendado, coherente con el patrón del ecosistema — **vs** uno genérico de subestructura.
- **Aparato de apoyo**: modelar como **resorte de 6 GdL** (elastomérico `k=G·A/t` + giro; POT
  liberando giros) — recomendado — **vs** coacciones rígidas idealizadas. Y cómo **repartir** las
  reacciones del tablero a las pilas/estribos (de los resultados del tablero del PT 7.1/7.2 vs como
  cargas de entrada del caso). `[confirmar AN]`
- **Cimentación de la pila**: **enrutado por tipo** (zapata `cimentaciones` / pilotes `pilotes` /
  encepado `bielas-tirantes`) reutilizando `motor-calculo` — recomendado — y criterio de selección
  (por dato del IFC / parámetro del caso). `[confirmar AN]`
- **2.º orden de pilas**: **amplificación aproximada ahora** (coherente con el pórtico del PT 7.2)
  **vs** diferir a **FEM-3** (pandeo/P-Δ riguroso) para pilas esbeltas. `[confirmar AN]`
- **Sísmica EC8-2**: ¿se implementa ya (espectro + ductilidad + combinación sísmica para la pila,
  reusando `geotecnia-sismico-ec7-ec8`) **o** se deja **gancho diferido** a un PT sísmico de puente?
  `[confirmar AN]`
- **Estribo**: **empuje activo Ka vs reposo K0** (según movilidad: estribo cerrado/abierto, integral
  vs con junta) y tratamiento de la **sobrecarga de tráfico tras el estribo**. `[confirmar AN]`
- **Convención de ejes/esfuerzos**: respetar la del núcleo (X,Y horizontales, Z vertical, −Z
  gravedad; barra `Iy`=mayor) y `estabilizar_plano=True` para pila/estribo planos.

**Entregable:**
- **`puentes` v0.3.0 (.plugin)**: 2 subagentes nuevos + `scripts/` (idealización pila+apoyo /
  estribo + módulo de **aparatos de apoyo** + comprobaciones EC2/EC7(/EC8-2) + enrutado a
  cimentaciones de `motor-calculo` + run_all por tipología + write-back), `scripts/nucleo/` espejado,
  `README.md` + `CHANGELOG.md` + `plugin.json` (`description` ≤500).
- **(Opcional) `motor-fem`**: en principio **sin cambios** (justificarlo); solo si hubo extensión
  aditiva ineludible, nueva versión + validación **sin regresión**.
- **`caso-PUE-05` y `caso-PUE-06`** documentados (idealización → … → memoria + write-back).
- **Actualizar** hoja de ruta Ola 7, hoja maestra, `C5` (si aplica), `criterios` y memoria del proyecto.
- **Puertas de calidad obligatorias** (pega su salida en el cierre):
  `TMPDIR=/tmp HOME=/tmp PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py <plugin>.plugin --ref <previo>.plugin`
  (**APTO**, exit 0; `description` ≤500) para `puentes` v0.3.0 (y `motor-fem` si se toca) **y**
  `verificar_espejo_nucleo.py --canonico <motor>.plugin <puentes>.plugin` (**ESPEJOS IDÉNTICOS**) **y**
  el **arnés de validación** (FEM-0/FEM-1 sin regresión; casos PUE-05/06 e2e).

**Notas de método (críticas, confirmadas en PT 4.x–7.2):**
- **Entorno**: `/tmp/pylibs` puede no existir al arrancar (el sandbox se reinicia) → reinstalar
  `pip install --no-cache-dir --target=/tmp/pylibs numpy scipy` con **`TMPDIR=/tmp HOME=/tmp
  PIP_NO_CACHE_DIR=1`**. Re-extraer las fuentes de los `.plugin` del workspace (sobreviven al
  reinicio). Ejecutar con `PYTHONPATH=/tmp/pylibs`.
- **Hazard de mount (re-confirmado en PT 7.2)**: los ficheros **editados con la herramienta Edit** se
  leen **truncados** desde el shell; los creados con **Write** se leen íntegros. **Desarrolla y testea
  en `/tmp`**; **reconstruye el `.plugin` y los verificadores en `/tmp`** desde el contenido íntegro
  (autorando con heredoc los ficheros editados). **`cp` de /tmp→workspace SÍ escribe bytes correctos**
  (verifícalo por tamaño exacto). Ejecuta los verificadores con **`TMPDIR=/tmp HOME=/tmp`** (si no,
  `extractall` falla con *No space* al caer el temp en `/sessions` lleno).
- **Disco `/sessions`** puede estar al 100 %: libera borrando `/sessions/<sesión>/tmp/{esp_nuc_*,
  verif_*}` (extracciones de los verificadores); no borres datos del usuario. Excluye `__pycache__`/
  `*.pyc` al empaquetar.
- **Gotchas reutilizables (PT 7.2)**: pila/estribo planos → **`estabilizar_plano=True`**; **base sobre
  resortes** (no apoyos rígidos); **EC7 deslizamiento/hundimiento por la reacción REAL de base**;
  **cortante por bielas (V_Rd,max) + cercos**; 2.º orden por **amplificación aproximada**. El
  **aparato de apoyo es un resorte** (`add_resorte`) — no necesita tocar el núcleo.
- **Reutiliza, no reescribas**: cimentaciones (`cimentaciones`/`pilotes`/`bielas-tirantes`), muros/EC7
  (`muros-contencion`), EC7/EC8 (`geotecnia-sismico-ec7-ec8`), modal/móvil (motor-fem) y write-back
  (iso19650) ya están. La regla de oro: *"¿qué es realmente nuevo (idealización de pila/estribo, el
  aparato de apoyo, su comprobación) y qué ya está en el núcleo?"* — solo se construye lo primero.
- Todo es **predimensionado, a revisar y firmar por técnico competente** (ICCP); NDP marcados
  `[confirmar AN]`.

**Empieza** leyendo los documentos (hoja de ruta §4/§5/§6/§10 + registro v1.3, **C5 §2/§3/§4/§8**, el
**plugin `puentes` v0.2.0** a ampliar, el **motor v0.2.1** y los **módulos a reutilizar**), y
**proponiendo, antes de mover una sola línea: (a)** la **idealización** de cada vertical (pila=columna+
resorte de apoyo+cimentación enrutada; estribo=muro+empuje+cargas de tablero) y el modelo del
**aparato de apoyo**; **(b)** la **estructura de los nuevos verticales** de `puentes` (subagentes +
scripts + reuso por PYTHONPATH de cimentaciones/muros/EC8); y **(c)** el **plan de validación**
(no-regresión del motor + casos PUE-05/06 e2e), con las tolerancias propuestas.
