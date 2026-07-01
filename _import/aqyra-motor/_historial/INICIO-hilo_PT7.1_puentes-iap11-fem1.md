INICIO de hilo — PT 7.1 (Ola 7): nace la disciplina **`puentes`** + **acciones IAP-11** +
**cargas móviles / líneas de influencia**, y el peldaño **FEM-1** del motor (cargas móviles +
modal), con el **primer vertical e2e: vigas pretensadas (emparrillado)**.

Proyecto Estructurando. Ejecuta el **PT 7.1 de la Ola 7 (puentes)**. El PT 7.0 ya entregó el
**motor FEM propio** (`motor-fem` v0.1.0, peldaño **FEM-0**: barra 3D Euler-Bernoulli + lámina
DKMQ, ensamblaje disperso + estático lineal + resortes, contrato **C5**, *strangler* vs PyNite
**sin regresión**). Ahora se construye **sobre ese motor** el **primer vertical de puente** y se
sube el motor al peldaño **FEM-1**. Es el equivalente, para puentes, de lo que el PT 4.3 fue
para instalaciones: nace la **disciplina** que **consume el núcleo**.

> Todo cálculo y entregable es de **predimensionado/asistencia y debe ser revisado y firmado por
> técnico competente** (Ingeniero de Caminos, Canales y Puertos). Los NDP se marcan `[confirmar AN]`.

**Alcance confirmado en la planificación (Ola 7, decisiones del 23/06/2026):**
- **`puentes` = plugin propio** (análogo a `instalaciones`/`obras-lineales`), con agente
  `ingeniero-de-puentes` + subagente(s) por tipología. (Decisión abierta nº2 → se cierra aquí
  como **plugin propio**, por ritmo y normativa IAP/fases específicas.)
- **Motor a FEM-1**: el núcleo `motor-fem` añade **cargas móviles / líneas de influencia**
  (envolventes de tráfico) y **análisis modal** (frecuencias + masa participante). Sigue la
  **escalera FEM-0…FEM-5**; este PT es **FEM-1**.
- **Acciones IAP-11** (carretera): es el módulo transversal de puente (*slot* C4-puentes).
  Aquí se implementa **lo que exige el primer vertical** (vigas pretensadas): permanentes y
  reológicas, **tráfico LM1** (tándem + carga uniforme), **térmica** (uniforme + gradiente),
  **viento** (básico), combinaciones de puente (ELU/ELS, frecuente/cuasipermanente). El resto
  de modelos de carga (LM2/LM3 fatiga, sísmica EC8-2, asientos) entran con sus tipologías.
- **Primer vertical e2e: vigas pretensadas** (doble-T / artesa) por **emparrillado (grillage)**
  barra + losa, reutilizando el **pretensado ya existente** (`motor-calculo-estructural/
  scripts/pretensado/`, EC2 §5.10, casos 12/13/14) como cargas equivalentes.
- **PyNite sigue siendo solo oráculo de test**: las capacidades nuevas (cargas móviles, modal)
  **solo** existen en el núcleo propio; el contraste de FEM-1 es contra **analítico** (líneas de
  influencia de viga isostática/continua; frecuencias cerradas) y, donde aplique, NAFEMS.

**Dónde encaja en la Ola 7 (mapa, para situar el hilo):**
- **PT 7.0 ✅ — Cimiento del motor (FEM-0):** `motor-fem` v0.1.0; barra EB + lámina DKMQ;
  estático lineal; strangler sin regresión; contrato C5. **Entregado.**
- **PT 7.1 (este hilo) — Disciplina `puentes` + IAP-11 + cargas móviles (FEM-1):** nace
  `puentes`; primer vertical **vigas pretensadas** e2e.
- **PT 7.2 —** completar el grupo lineal (losa postesada, pórtico, celosía).
- **PT 7.3…7.7 —** subestructura; cajón (FEM-2); metálico/mixto/oblicuo/curvo; arco (FEM-3);
  atirantado (FEM-4). Ver `Hoja-de-ruta_Ola7-puentes-y-motor-FEM.md`.

> **Frontera (contratos del núcleo) — respétala:**
> - **C1 (`iso19650-openbim`):** lectura/escritura IFC + **modelo neutro físico/estructural** y
>   **Alignment** (Ola 5, geometría del tablero: eje/peralte/oblicuidad por PK). **No se toca**
>   salvo que el tablero exija una clave nueva aditiva (entonces, extender C1 §3 sin romper).
> - **C5 (`motor-fem`):** **mallado + ensamblaje + solver**. FEM-1 amplía el contrato C5 con
>   `analisis ∈ {modal, movil}` y la clave `cargas_moviles` (hoy gancho reservado). El núcleo
>   **no conoce IAP-11 ni tipologías**.
> - **`puentes` (nuevo, vertical):** idealización (emparrillado desde Alignment + secciones),
>   **acciones IAP-11**, **fases/pretensado** (reusa `pretensado/`), comprobación **EC2**,
>   memoria y **write-back** al IFC. **Consume** C5 y C1; **no recalcula** la mecánica.
> - **`motor-calculo-estructural`:** no se migra todavía (sigue con PyNite en su producción).

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ola7-puentes-y-motor-FEM.md` — **§3** (escalera FEM; este hilo = **FEM-1**),
   **§4** (fila *vigas pretensadas*: idealización emparrillado, transversales clave), **§5**
   (capacidades transversales: **IAP-11**, **líneas de influencia/cargas móviles**, **fases +
   diferidos**, **geometría Alignment**), **§10** (decisión nº2 `puentes` plugin propio; nº5
   pérdidas diferidas simplificado vs paso a paso).
2. `Nucleo-transversal/C5_Contrato-motor-FEM.md` — **todo**, en especial **§3** (API `resolver`,
   ganchos `modal`/`movil`), **§2** (claves del modelo de análisis; dónde encaja
   `cargas_moviles`) y **§8** (extensión FEM-1 sin romper). El nuevo trabajo de C5 es **activar
   esos ganchos**.
3. **El motor FEM-0 a extender** (`motor-fem` v0.1.0, dentro del `.plugin` y en
   `motor-fem/scripts/`): `fem_core.py` (ensamblaje disperso + estático; aquí se añade el
   **modal** vía `scipy.sparse.linalg.eigsh` y el **barrido de cargas móviles**),
   `elementos/barra.py` y `elementos/lamina.py` (el grillage usa barra + lámina), `mallador.py`
   (`desde_modelo_neutro` y el espejo `desde_pynite`), `resolver.py` (añadir `analisis="modal"`
   y `"movil"`), `validacion/` (añadir parches de **línea de influencia** y **modal**).
4. **El pretensado existente a reutilizar** (`motor-calculo-estructural` v0.23.0):
   `scripts/pretensado/` (`solver_pretensado*.py`, `ec2_pretensado.py`, `ec2_continua.py`,
   `balance_2d.py`) — **cargas equivalentes de tendón** y continua hiperestática ya resueltas
   (casos 12/13/14). El vertical de vigas pretensadas las **inyecta como caso de carga** en el
   modelo de análisis C5; **no se reescribe** el pretensado.
5. `Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` — **§2/§3** (modelo neutro estructural;
   cómo extenderlo) y **§4bis** (Alignment/obra lineal: el **eje del tablero** —recta/clotoide/
   curva, peralte, oblicuidad por PK— sale del **modelo neutro lineal** de `iso19650-openbim`
   v0.5.0; el **mallador del emparrillado** lo usa). Cierra el círculo Ola 5 ↔ Ola 7.
6. Casos de referencia y puertas: `Casos-de-uso/` (crear `caso-PUE-01-vigas-pretensadas`);
   `Nucleo-transversal/verificar_empaquetado.py` y `verificar_espejo_nucleo.py`;
   `criterios-despacho.md` (raíz) + la skill `criterios-memoria` de estructuras.

**Objetivo y alcance (qué hay que hacer):**
1. **Sube `motor-fem` a v0.2.0 (FEM-1)** — capacidades nuevas en el núcleo, agnósticas a
   disciplina:
   - **Análisis modal**: `resolver(modelo, analisis="modal")` → frecuencias propias, modos y
     **masa participante** por dirección. Matriz de masas (consistente o concentrada
     `[confirmar AN]`); `scipy.sparse.linalg.eigsh` (modo *shift-invert*). Masas desde `rho`·
     volumen de barras/láminas + masas nodales.
   - **Cargas móviles / líneas de influencia**: `resolver(modelo, analisis="movil")` con la
     clave **`cargas_moviles`** (tren de cargas IAP-11 LM1: tándem + uniforme, carriles), que
     **barre** posiciones a lo largo de un **camino** (sobre el eje/PK) y devuelve **envolventes**
     de esfuerzos/reacciones y **posiciones pésimas**. Reaprovecha la factorización estática
     (resolver una vez, mover la carga = N términos por superposición de cargas nodales).
   - **Líneas de influencia** propiamente: para un esfuerzo objetivo, la curva de respuesta a
     una carga unidad móvil (método directo por barrido; opcional Müller-Breslau como check).
   - **Validación FEM-1**: líneas de influencia **analíticas** (viga isostática biapoyada y viga
     continua de 2 vanos); **modal** vs frecuencias cerradas de viga (βnL); **sin regresión**
     del estático (FEM-0) intacto. Actualiza `validacion/` y el contrato **C5 §8**.
2. **Nace el plugin `puentes` v0.1.0**:
   - `.claude-plugin/plugin.json` (`description` ≤500), `README.md`, `CHANGELOG.md`.
   - **Agente** `agents/ingeniero-de-puentes.md` (clasifica tipología, orquesta IFC/Alignment →
     idealización → C5 (FEM-1) → IAP-11 → EC2 → memoria + write-back) + **subagente**
     `agents/proyectista-vigas-pretensadas.md`.
   - `scripts/` de la disciplina: **idealización/emparrillado** (de Alignment + secciones a
     malla C5: vigas longitudinales + riostras/losa transversal), **acciones IAP-11**
     (`scripts/acciones/iap11.py`: permanentes, **LM1**, térmica, viento, combinaciones),
     **inyección del pretensado** (puente al `pretensado/` existente como cargas equivalentes),
     **comprobación EC2** del tablero, **memoria** y **write-back** de resultados al IFC
     (reusa el escritor genérico de `iso19650-openbim`).
   - `scripts/nucleo/` **espejado byte a byte** del canónico (puerta
     `verificar_espejo_nucleo.py` → **ESPEJOS IDÉNTICOS**), como el resto de disciplinas.
3. **Caso e2e `caso-PUE-01-vigas-pretensadas`**: IFC/Alignment (o modelo neutro) de un tablero
   de vigas pretensadas → emparrillado → **envolvente IAP-11 (LM1)** por líneas de influencia →
   pretensado (cargas equivalentes) → comprobación EC2 (flexión, cortante, fisuración, tensiones
   en vacío y en servicio) → **memoria** + write-back. Veredicto y aprovechamientos.

**Decisiones a resolver y documentar (antes de mover una línea):**
- **`puentes` plugin propio** (recomendado; cierra nº2) **vs** tipología dentro de
  `motor-calculo-estructural`.
- **Ubicación de IAP-11**: módulo en `puentes` (recomendado, es normativa de la disciplina) vs
  núcleo. **No** va en `motor-fem` (el núcleo no conoce normativa).
- **Idealización del tablero**: **emparrillado (grillage)** barra+barra/losa (recomendado para
  vigas pretensadas, casa con la práctica) vs barra+lámina (placa para la losa). Definir el
  reparto transversal y las riostras. `[confirmar AN]`
- **Masas para el modal**: matriz **consistente** vs **concentrada**; qué masas (peso propio +
  cuasipermanente). `[confirmar AN]`
- **Cargas móviles**: barrido directo (recomendado) y definición del **camino/carriles** sobre
  el PK del Alignment; nº de posiciones; tratamiento del tándem (2 ejes) y de la carga uniforme
  por carril. `[confirmar AN]`
- **Pérdidas diferidas** (nº5): empezar **simplificado por coeficientes** (EC2), dejar gancho
  para paso a paso. `[confirmar AN]`
- **Convención de ejes/esfuerzos**: respetar la del núcleo (X,Y horizontales, Z vertical,
  −Z gravedad; barra `Iy`=mayor; placa `[Mx,My,Mxy]`) para que el grillage y la no-regresión
  sean directos.

**Entregable:**
- **`motor-fem` v0.2.0 (FEM-1)**: modal + cargas móviles/líneas de influencia en `fem_core`/
  `resolver`, `validacion/` ampliada, `scripts/nucleo/` espejado; `CHANGELOG.md` + `plugin.json`
  (`description` ≤500). **Sin regresión** del estático (FEM-0).
- **`puentes` v0.1.0 (.plugin)**: agente + subagente vigas pretensadas, `scripts/` (emparrillado
  + IAP-11 + EC2 + memoria + write-back), `scripts/nucleo/` espejado, `README.md` + `CHANGELOG.md`
  + `plugin.json`.
- **`caso-PUE-01-vigas-pretensadas`** documentado (IFC/Alignment → … → memoria + write-back).
- **Actualizar**: `C5_Contrato-motor-FEM.md` (§3/§8: `modal`/`movil` ya implementados),
  hoja de ruta Ola 7 (PT 7.1 ✅ → PT 7.2 🔜; FEM-1 cerrado), hoja de ruta maestra (fila `puentes`
  + registro de versiones), `criterios` (lección + INC si aplica) y la memoria del proyecto.
- **Puertas de calidad obligatorias** (pega su salida en el cierre):
  `PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py <plugin>.plugin`
  (**APTO**, exit 0; `description` ≤500) para **ambos** plugins (`motor-fem` v0.2.0 y `puentes`
  v0.1.0) **y** `verificar_espejo_nucleo.py --canonico <motor>.plugin <plugin>.plugin`
  (**ESPEJOS IDÉNTICOS**) **y** el **arnés de validación** (FEM-1: líneas de influencia +
  modal analíticos; estático FEM-0 **sin regresión**; caso-PUE-01 e2e).

**Notas de método (críticas, confirmadas en PT 4.x–7.0):**
- **Toolchain en `/tmp/pylibs`**: numpy 2.2.6, scipy 1.15.3, PyNite 2.0.2, ifcopenshell 0.8.5 →
  ejecuta con `PYTHONPATH=/tmp/pylibs`. El núcleo FEM usa numpy/scipy (no stdlib).
- **Hazard de mount (reconfirmado en PT 7.0)**: el shell del sandbox **lee truncados** los
  ficheros de texto **editados** del workspace (p. ej. `fem_core.py` se truncó al `cp`/import,
  y `verificar_empaquetado.py` a 200/252 líneas). **Desarrolla y testea en `/tmp`** (fs local
  fiable); las herramientas **Read/Write/Edit son la fuente de verdad**. Para empaquetar:
  **reconstruye el `.plugin` en `/tmp`** (ficheros nuevos validados + espejo del núcleo copiado
  del ZIP del motor + verificadores reconstruidos desde Read) y cópialo con **nombre versionado**
  (`cat > destino`/`cp`), excluyendo `__pycache__`/`*.pyc`.
- **PyNite full-solve es lento** (Python puro; ~400 quads agotan el presupuesto de 45 s del
  sandbox). Para el strangler, **captura el `FEModel3D`** que construye el solver de producción
  (monkeypatch de `analyze_linear` para abortar tras construir) y **resuelve con el núcleo
  propio**; o compara contra los `resultados.json`/analítico de referencia. El **adaptador
  espejo** `mallador.desde_pynite` ya existe para esto.
- **Reutiliza, no reescribas**: el **pretensado** (EC2 §5.10) y el **write-back** al IFC ya
  están; el **eje del tablero** viene del **Alignment** (Ola 5). La regla de oro: *"¿qué es
  realmente nuevo (idealización de puente, IAP-11) y qué ya está en el núcleo (FEM, IFC,
  pretensado, memoria)?"* — solo se construye lo primero.
- Todo es **predimensionado, a revisar y firmar por técnico competente** (ICCP); NDP marcados
  `[confirmar AN]`.

**Empieza** leyendo los documentos (hoja de ruta §3/§4/§5, **C5 §2/§3/§8**, el **motor FEM-0** a
extender, el **pretensado** a reutilizar y **C1 §2/§4bis** del Alignment), y **proponiendo,
antes de mover una sola línea: (a)** la ampliación del contrato **C5** para FEM-1 (claves
`cargas_moviles`/masas, API `resolver(modelo, analisis="modal"|"movil")`) y la **estructura del
plugin `puentes`** (agente + subagente + scripts); **(b)** la **formulación de FEM-1**
(matriz de masas + `eigsh` para modal; barrido de cargas móviles + líneas de influencia por
superposición) y la **idealización por emparrillado** del tablero de vigas pretensadas; y
**(c)** el **plan de validación** (líneas de influencia y modal analíticos + no-regresión del
estático FEM-0 + caso-PUE-01 e2e), con las tolerancias propuestas.
