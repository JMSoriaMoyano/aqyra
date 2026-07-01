# Hoja de ruta — Ola 7 (Puentes) y nuevo Motor FEM transversal

**Estado a 23/06/2026 · v1.1.** Documento de planificación de la **Ola 7 (puentes)** del ecosistema
*Estructurando* y, dentro de ella, del **motor de elementos finitos (FEM) propio**, la pieza
transversal más ambiciosa del proyecto. Se construye **por fases**, y cada fase del motor
**habilita** un grupo de tipologías de puente y, de paso, las **estructuras singulares** (cubiertas
laminares, Ola 3) y el horizonte de **tensoestructuras**.

> Todo cálculo y entregable es de **predimensionado/asistencia y debe ser revisado y firmado por
> técnico competente** (Ingeniero de Caminos, Canales y Puertos). Los NDP se marcan `[confirmar AN]`.

> Leyenda de estado: ✅ existe y validado · 🔄 en curso · 🔜 siguiente · ⬜ pendiente.

---

## 0. Decisiones de arranque (confirmadas con el ICCP, 23/06/2026)

1. **El motor FEM es una capacidad TRANSVERSAL en un plugin propio `motor-fem`** (núcleo numpy/scipy),
   al modo del *motor hidráulico de red* de la Ola 4. Lo consumen **puentes** (Ola 7), **estructuras
   singulares** (Ola 3) y, en su horizonte no-lineal, las **tensoestructuras**. No se entierra dentro
   de `motor-calculo-estructural`.
2. **Estrategia *strangler* sobre PyNite.** PyNite (motor actual: barras + lámina plana MITC4) se
   mantiene como **oráculo de validación** mientras se construye el núcleo propio en paralelo; cada
   elemento y cada caso 1–15 se contrastan (cero regresión) y PyNite se **deprecia por fases**.
3. **Secuencia de tipologías por madurez del FEM y uso real:** primero las **lineales y frecuentes**
   (vigas pretensadas → losa postesada → pórtico → celosía → pilas/estribos/cimentaciones); después las
   **avanzadas** (cajón, metálico/mixto, oblicuo, curvo); por último las **no-lineales** (arco,
   atirantado).
4. **Acciones: carretera IAP-11** (modelos de carga, térmica, viento, fatiga, asientos) + **líneas de
   influencia / cargas móviles**. El **ferrocarril (IAPF)** queda como **extensión futura**.

---

## 1. Principio rector: motor transversal + verticales de tipología

Repetimos el patrón que ya ha funcionado dos veces (grafo de red, dominio IFC): **separar la
capacidad transversal de los verticales**.

- **Capacidad transversal — el núcleo FEM (`motor-fem`):** resuelve la mecánica (ensamblaje de la
  matriz de rigidez, librería de elementos, solvers lineal/modal/pandeo/no-lineal, cargas móviles).
  **No conoce normativa ni tipologías.** Crece por una **escalera de capacidades** (FEM-0…FEM-5).
- **Verticales — las tipologías de puente (`puentes`):** cada tipología aporta solo lo suyo
  (idealización, **acciones IAP-11**, **fases constructivas**, comprobación EC2/EC3/EC4, memoria) y
  **consume** el núcleo FEM + la geometría **Alignment** (Ola 5) + el **pretensado** ya existente.

Regla de oro (igual que en todo el ecosistema): *"¿qué de esto es realmente nuevo (idealización,
normativa) y qué ya está en el núcleo (FEM, IFC, acciones, pretensado, memoria)?"* — solo se
construye lo primero.

```
                ┌───────────────────────────────────────────────────────────┐
                │   motor-fem  (TRANSVERSAL)  · núcleo numpy/scipy           │
                │   elementos: barra · lámina plana · lámina curva ·         │
                │   rigidizador · cable · membrana                           │
                │   solvers: lineal · modal · pandeo · no-lineal · móvil     │
                └───────────────┬───────────────────────────┬───────────────┘
                                │ consume                    │ consume
        ┌───────────────────────▼─────────┐     ┌───────────▼───────────────────────┐
        │  puentes (Ola 7)                 │     │  estructuras singulares (Ola 3)    │
        │  vigas/losa/cajón/metálico/...   │     │  cubiertas laminares, voladizos,   │
        │  arco · atirantado               │     │  2.º orden global · tensoestructuras│
        │  + IAP-11 + fases + Alignment    │     │  (horizonte FEM no-lineal)         │
        └──────────────────────────────────┘     └────────────────────────────────────┘
```

---

## 2. Arquitectura del plugin `motor-fem`

| Pieza | Contenido |
|---|---|
| **Modelo de análisis (C5)** | Modelo neutro de **malla FEM**: nodos, elementos (barra/lámina/cable/membrana), materiales, secciones/laminados, apoyos (resortes incl.), casos de carga y combinaciones. Derivado del **modelo neutro estructural** (C1) por un **mallador**. |
| **Librería de elementos** | Barra 3D (Timoshenko) · lámina plana (membrana con *drilling* + flexión Mindlin) · **lámina curva** (isoparamétrica) · **rigidizador** (barra excéntrica acoplada) · **cable** · **membrana**. |
| **Ensamblador + solvers** | Matriz de rigidez dispersa (`scipy.sparse`); solvers: **estático lineal**, **modal**, **pandeo lineal**, **no-lineal geométrico** (corotacional/arc-length), **cargas móviles / líneas de influencia**. |
| **Arnés de validación** | Parches analíticos (viga, placa Timoshenko, membrana, catenaria) + **oráculo PyNite** + *benchmarks* tipo **NAFEMS**. Puerta de no-regresión. |
| **API estable** | `resolver(modelo, tipo_analisis, ...)` → esfuerzos/desplazamientos/modos/cargas críticas; agnóstica a disciplina. |

**Frontera con el resto del ecosistema:**
- `iso19650-openbim` (C1): lectura/escritura IFC y modelo neutro **físico/estructural**. **No cambia.**
- `motor-fem` (C5, **nuevo**): el **núcleo de cálculo** que toma el modelo neutro estructural, lo
  **malla** y lo resuelve. Es donde migra, por *strangler*, la mecánica hoy en PyNite.
- `motor-calculo-estructural`: pasa a ser un **consumidor** del núcleo FEM (sus verticales —barras,
  láminas, mixtas, cimentaciones— llaman al núcleo en vez de a PyNite, sin cambiar su normativa).
- `puentes` (**nuevo**, vertical): agente `ingeniero-de-puentes` + subagentes por tipología.

**Estrategia *strangler* (cero regresión):**
1. El núcleo propio nace reproduciendo **barra + lámina plana** y se valida contra **PyNite** y contra
   soluciones analíticas en los **casos 1–15** (tolerancia numérica documentada).
2. Mientras dura la convivencia, PyNite es el **oráculo**: cualquier divergencia > tolerancia es un
   error del núcleo, no del caso.
3. Cuando el núcleo cubre todo lo que hoy hace PyNite **sin regresión**, se **deprecia PyNite**
   (queda solo como test de referencia). Las capacidades nuevas (curva, no-lineal, cables) **solo**
   existen en el núcleo propio.

**Núcleo común existente:** `motor-fem` **espeja** `scripts/nucleo/` (`ifc_utils`/`grafo_red`) como el
resto de plugins (decisión nº4), aunque el grafo de red no sea su parte principal; la puerta
`verificar_espejo_nucleo.py` se aplica.

---

## 3. Escalera de capacidades del motor FEM (FEM-0 … FEM-5)

Cada peldaño es **entregable y validado** por sí mismo, y desbloquea tipologías concretas.

| Fase | Capacidad nueva | Validación | Desbloquea |
|---|---|---|---|
| **FEM-0** | Núcleo lineal propio: **barra 3D** + **lámina plana** (membrana+flexión), ensamblaje disperso, **estático lineal**, apoyos/resortes. | Parche analítico (viga, placa Timoshenko) + **oráculo PyNite** en casos 1–15 (sin regresión). | Emparrillado de vigas, losa, pórtico, celosía, pilas (lineal). |
| **FEM-1** | **Líneas de influencia / cargas móviles** (envolventes de tráfico) + **análisis modal** (frecuencias, masa participante). | Líneas de influencia analíticas (viga isostática/continua); modal vs solución cerrada. | Envolventes IAP-11 en todas las tipologías lineales; comprobación dinámica básica. |
| **FEM-2** | **Lámina curva** (isoparamétrica) + **rigidizadores** (barra excéntrica acoplada) + **secciones de pared delgada** (torsión de Saint-Venant, **alabeo/distorsión**, *shear lag*). | NAFEMS (lámina curva), placa rigidizada, cajón vs teoría de viga-cajón. | Cajón, metálico/mixto (paneles rigidizados), oblicuo, curvo. **+ Ola 3 cubiertas laminares.** |
| **FEM-3** | **No-lineal geométrico** (corotacional) + **2.º orden P-Δ** + **pandeo lineal** (autovalores). | Columna de Euler, pórtico P-Δ, arco vs solución de estabilidad. | Arco, pilas esbeltas (2.º orden), abolladura de paneles. |
| **FEM-4** | **Cable** (solo-tracción/catenaria) + **membrana** + **form-finding** (densidad de fuerza / relajación dinámica) + no-lineal con grandes desplazamientos. | Catenaria analítica; *patch tests* de membrana; *benchmark* de tensoestructura. | **Atirantado** (tesado evolutivo, estado de cargas permanentes) + **tensoestructuras** (horizonte). |
| **FEM-5** *(horizonte)* | **Dinámica avanzada en el tiempo**: *time-history* (sismo, viento *buffeting*, cargas móviles dinámicas), amortiguamiento. | *Benchmarks* dinámicos. | Comprobaciones dinámicas finas (no comprometido en esta ola). |

> **Dependencia práctica:** el núcleo usa `numpy` + `scipy.sparse`; en el sandbox se cargan en
> `/tmp/pylibs` (como `ifcopenshell`). El cálculo del núcleo es **Python científico**, no *stdlib*
> pura (a diferencia de los solvers hidráulicos).

---

## 4. Tipologías de puente → capacidad FEM + transversales

| Tipología | Idealización | Fase FEM | Transversales clave | Normativa |
|---|---|---|---|---|
| **Vigas pretensadas** (doble-T / T / artesa) | Emparrillado (*grillage*) barra+losa, o barra+lámina | FEM-0/1 | Pretensado ✅ + IAP-11 + líneas de influencia | EC2 §5.10, IAP-11 |
| **Losa postesada** | Lámina plana + postesado | FEM-0/1 | Postesado ✅ + IAP-11 | EC2 |
| **Pórtico** | Barras + suelo (resorte) | FEM-0/1 | IAP-11 + 2.º orden ligero + empuje de tierras | EC2/EC7 |
| **Celosía** | Barras / articulado | FEM-0/1 | IAP-11 + **fatiga** de uniones | EC3 |
| **Pilas, apoyos y cimentaciones** | Columna + 2.º orden + rigidez de aparato de apoyo | FEM-0 (→FEM-3 esbeltez) | Reutiliza pilares/cimentaciones ✅ + aparatos de apoyo + IAP-11 | EC2/EC3/EC7/EC8-2 |
| **Estribos** | Muro + empuje de tierras + cargas de tablero | FEM-0 | Reutiliza muros-contención ✅ (EC7) + tablero | EC7/EC2 |
| **Cajón postesado** | Barra+lámina; torsión/distorsión/*shear lag* | FEM-2 | Postesado **evolutivo** + **fases** + IAP-11 | EC2 |
| **Metálicos y mixtos** | Lámina rigidizada + conectores ✅ | FEM-2 | Abolladura, **fatiga**, conexión EC4 ✅ | EC3/EC4 |
| **Oblicuos** | Mallado oblicuo (lámina/grillage) | FEM-2 | Reparto, líneas de influencia 2D | EC2/EC3 |
| **Curvos** | Mallado sobre **Alignment** curvo; torsión | FEM-2 | Geometría Ola 5 + torsión | EC2/EC3 |
| **Arco** | No-lineal geométrico + pandeo + proceso constructivo | FEM-3 | Estabilidad, imperfecciones, cimbra/avance | EC2/EC3 |
| **Atirantado** | Cables no-lineales + tesado evolutivo + *form-finding* | FEM-4 | Estado de cargas permanentes, **fases** | EC2/EC3 (cables) |

---

## 5. Capacidades transversales de puente (más allá del FEM)

Son el "CN-3 de puentes" y la fontanería que comparten todas las tipologías:

- **Acciones IAP-11** (módulo nuevo, *slot* CN-3): permanentes y reológicas; **tráfico** (LM1: tándem +
  carga uniforme; LM2; sobrecarga de uso en aceras); **viento**; **térmica** (componente uniforme +
  **gradiente vertical**); **nieve**; **asientos** de apoyo; **fatiga** (LM3); **sísmica** (EC8-2);
  **combinaciones** específicas de puente (ELU/ELS, frecuente/cuasipermanente).
- **Líneas de influencia y cargas móviles** (FEM-1): generación de **envolventes** de esfuerzos por
  paso del tren de cargas a lo largo del eje; posiciones pésimas automáticas.
- **Fases constructivas + efectos diferidos**: montaje (vano a vano, **voladizos sucesivos**, empuje),
  **tesado evolutivo**, **pérdidas diferidas** de pretensado (**fluencia/retracción/relajación**) y
  **redistribución por fluencia**. Aprovecha y extiende `scripts/pretensado/` (continua hiperestática ✅).
- **Geometría del tablero (Alignment, Ola 5)**: el eje (recta/clotoide/curva), el **peralte** y la
  **oblicuidad** vienen del **modelo neutro lineal** (`iso19650-openbim` v0.5.0); el **mallador** del
  FEM los usa para generar la malla curva/oblicua. Cierra el círculo Ola 5 ↔ Ola 7.
- **Fatiga** (transversal a metálico/mixto y celosía): categorías de detalle EC3-1-9, daño acumulado.

---

## 6. Plan de la Ola 7 por paquetes de trabajo (PT)

Interleva **fases del motor** (entregan capacidad) con **verticales de puente** (entregan tipología).

| PT | Foco | Motor | Entregable de tipología | Estado |
|---|---|---|---|---|
| **7.0** | **Cimiento del motor FEM** | **FEM-0** | ✅ (nace `motor-fem` v0.1.0; *strangler* vs PyNite; barra EB + lámina DKMQ; sin regresión) | ✅ |
| **7.1** | Disciplina `puentes` + **IAP-11** + cargas móviles | **FEM-1** | ✅ (`puentes` v0.1.0; vigas pretensadas e2e `caso-PUE-01` CUMPLE; FEM-1 modal+móvil sin regresión) | ✅ |
| **7.2** | Completar el grupo lineal | FEM-0/1 (+v0.2.1) | ✅ (`puentes` v0.2.0: **losa postesada** lámina DKMQ, **pórtico** barras+resortes+K0, **celosía** EC3; casos PUE-02/03/04 CUMPLEN) | ✅ |
| **7.3** | Subestructura | FEM-0 (FEM-1 reuso) | ✅ (`puentes` v0.2.0→**v0.3.0**: **pila**+apoyo+cimentación enrutada y **estribo**; casos PUE-05/06 CUMPLEN; **motor sin tocar**) | ✅ |
| **7.4** | **Lámina curva + rigidizadores + pared delgada** | **FEM-2** | ✅ (`motor-fem` v0.2.1→**v0.3.0**: lámina curva MITC4 + rigidizador offset + pared delgada Bredt/shear lag, NAFEMS ±5%; `puentes` v0.4.0→**v0.5.0**: **cajón postesado** por lámina pura, `caso-PUE-17` CUMPLE; `iso19650` v0.9.1 tipología `cajon`) | ✅ |
| **7.5** | Tableros avanzados | FEM-2 | ✅ (`puentes` v0.5.0→**v0.6.0**: **mixto** acero-hormigón lámina rigidizada [EC3 clase 1-4 + abolladura EN 1993-1-5, EC4 conexión, fatiga EN 1993-1-9], **oblicuo** malla romboidal [reparto 2D + esquina obtusa], **curvo** sobre Alignment [torsión Bredt acoplada]; casos PUE-18/19/20 CUMPLEN; `iso19650` v0.9.2; **motor sin tocar**) | ✅ |
| **7.6** | **No-lineal geométrico / pandeo** | **FEM-3** | **Arco** (estabilidad, proceso constructivo) | 🔜 |
| **7.7** | **Cables / membranas + form-finding** | **FEM-4** | **Atirantado** (tesado evolutivo) — **cierra puentes** | ⬜ |
| **7.8** *(horizonte)* | **Tensoestructuras** + dinámica avanzada | FEM-4/FEM-5 | Cubiertas tensadas, mallas de cables (spin-off, fuera del alcance comprometido) | ⬜ |

**Definición de "hecho" por PT:** cada PT entrega (a) la capacidad del motor **validada** (parche
analítico + oráculo/benchmark), (b) un **caso e2e** por tipología (IFC/Alignment → modelo → FEM →
acciones → comprobación EC → memoria + write-back), y (c) las **puertas** en verde
(`verificar_empaquetado.py` APTO + `verificar_espejo_nucleo.py` ESPEJOS IDÉNTICOS).

---

## 7. Conexión con la Ola 3 (singular) y el horizonte tensoestructuras

- **Ola 3 — estructuras singulares (cubiertas laminares):** la hoja de ruta maestra la situaba como
  "empuje del motor de cálculo". Con esta decisión, **Ola 3 deja de necesitar un motor propio**: pasa
  a ser **consumidora de `motor-fem`**. En cuanto exista **FEM-2** (lámina curva + rigidizadores), las
  **cubiertas laminares** son un vertical directo; con **FEM-3** se cubren grandes voladizos y 2.º
  orden global. Recomendación: **reactivar Ola 3 como spin-off de FEM-2/FEM-3**, en paralelo a PT 7.4/7.6.
- **Tensoestructuras (horizonte):** el peldaño **FEM-4** (cables/membranas + *form-finding*) que exige
  el **atirantado** es **exactamente** el que habilita **cubiertas tensadas y mallas de cables**.
  Construirlo bien para puentes deja "gratis" la tensoestructura (PT 7.8). Por eso conviene diseñar
  FEM-4 con la membrana en mente desde el principio (no solo el cable de tirante).

---

## 8. Contrato C5 — Motor FEM (modelo de análisis + API del solver)

Nuevo contrato del núcleo (junto a C1, CN-1, CN-2 y CN-3), que estabiliza cómo cualquier disciplina pide cálculo:

- **Modelo de análisis (malla FEM)** — extiende el modelo neutro estructural (C1 §2) con:
  `mallas`/`elementos` (tipo: `barra|lamina|lamina_curva|rigidizador|cable|membrana`), `laminados`
  (capas para mixto/lámina), `apoyos` (incl. **resortes** y aparatos de apoyo), `casos`/`combinaciones`,
  `cargas` (incl. **móviles** y de **pretensado** como cargas equivalentes). **Solo añade claves**,
  sin redefinir las existentes (modelo hermano, retrocompatible).
- **API del solver** (estable, agnóstica): `resolver(modelo, analisis)` con
  `analisis ∈ {estatico_lineal, modal, pandeo_lineal, no_lineal, movil}` → esfuerzos,
  desplazamientos, modos, factores críticos, envolventes.
- **Arnés de validación** (puerta de calidad del núcleo): parches analíticos + **oráculo PyNite** +
  **benchmarks NAFEMS** (lámina curva, placa rigidizada) + catenaria/membrana. Falla si una capacidad
  diverge de su referencia más allá de la tolerancia documentada.

> El mallador (estructural → malla FEM) puede vivir en `motor-fem` o en `motor-calculo-estructural`
> como adaptador; **decisión abierta** (ver §10).

---

## 9. Riesgos y mitigaciones

- **Corrección del FEM propio** (lo más crítico). → *Strangler* con PyNite como oráculo, parches
  analíticos por elemento y **benchmarks NAFEMS** estándar como puerta; nada se da por bueno sin
  contraste.
- **Convergencia del no-lineal** (FEM-3/4: arco, cables, membranas). → Métodos robustos
  (**arc-length**/longitud de arco, relajación dinámica para *form-finding*), arranque desde estado
  tensado, control de pasos.
- **Rendimiento / tamaño de malla.** → `scipy.sparse` + solver disperso; mallas de predimensionado
  (no detalle); permitir submodelos.
- **Ámbito desbordado** (es la pieza más ambiciosa). → **Escalera de capacidades**: cada PT entrega y
  valida una capacidad; no se empieza un puente cuya fase FEM no esté cerrada.
- **Dependencia numpy/scipy en el sandbox.** → Pre-aprovisionar en `/tmp/pylibs`; el empaquetado del
  plugin no incluye binarios (solo código).
- **Doble fuente de verdad durante la convivencia.** → PyNite es **solo oráculo de test**; el cálculo
  de producción pasa al núcleo propio en cuanto cubre la capacidad sin regresión.

---

## 10. Decisiones

**Tomadas (23/06/2026):** (nº8) **motor FEM transversal en plugin `motor-fem`**; *strangler* sobre
PyNite; secuencia por madurez/uso; acciones **IAP-11** (ferrocarril futuro). Ola 3 (singular) pasa a
**consumir `motor-fem`**.

**Abiertas (a confirmar por el ICCP):**
1. **Ubicación del mallador** (estructural → malla FEM): ¿en `motor-fem` o como adaptador en
   `motor-calculo-estructural`? (recomendado: en `motor-fem`, junto al núcleo).
2. **Disciplina `puentes`: ¿plugin propio** (análogo a `instalaciones`/`obras-lineales`) **o** tipología
   dentro de `motor-calculo-estructural`? (recomendado: **plugin propio** `puentes`, por ritmo y
   normativa IAP/fases específicas).
3. **Alcance de FEM-5** (dinámica en el tiempo): ¿comprometer en esta ola o dejar como horizonte?
   (recomendado: **horizonte**; cerrar la ola con FEM-4 + atirantado).
4. **Tensoestructuras (PT 7.8):** ¿se compromete como entregable de la ola o como spin-off posterior?
   (recomendado: **spin-off**, pero diseñar FEM-4 con la membrana en mente).
5. **Pérdidas diferidas / fluencia-retracción:** ¿modelo simplificado por coeficientes (EC2) o
   integración paso a paso en el tiempo? (recomendado: empezar **simplificado**, dejar el gancho para
   paso a paso).

---

## 11. Definición de "hecho" de la Ola 7

La Ola 7 se considerará **cerrada** cuando:
1. Exista el **núcleo FEM propio** (`motor-fem`) que **sustituye a PyNite sin regresión** en los casos
   1–15 y cubre barra · lámina plana · **lámina curva** · rigidizador · **no-lineal geométrico** ·
   **cable**.
2. La disciplina **`puentes`** cubra de extremo a extremo (IFC/Alignment → FEM → IAP-11 → comprobación
   EC → memoria + write-back) las tipologías comprometidas: **vigas pretensadas, losa postesada,
   pórtico, celosía, pilas/estribos/cimentaciones, cajón, metálico/mixto, oblicuo, curvo, arco y
   atirantado**.
3. Las **acciones IAP-11**, las **cargas móviles/líneas de influencia** y las **fases constructivas +
   diferidos** estén integradas y validadas.
4. Todas las **puertas** en verde (empaquetado APTO + espejos idénticos) y un **caso e2e por
   tipología** documentado.

Con ello, el ecosistema queda **completo en sus tres disciplinas** (estructuras —incl. singular y
puentes—, instalaciones, obras lineales) sobre un **núcleo maduro** (IFC + grafo de red + **FEM**), y
abierto al horizonte de **tensoestructuras**.

---

## Registro de versiones del documento

- **v1.7 (24/06/2026):** **PT 7.5 ✅ CERRADO** — tres **verticales avanzados** sobre **FEM-2**, con
  el motor `motor-fem` **v0.3.0 INTACTO** (PT de disciplina, como el 7.3: no-regresión FEM-0/1/2 por
  construcción; FEM-0/1 sin regresión, NAFEMS FEM-2 ≤3,4 %). `puentes` sube a **v0.6.0**:
  (1) **MIXTO acero-hormigón** (`idealizacion/mixto.py`): losa de **láminas curvas MITC4** + cada viga
  de acero como **`ElementoRigidizador` con offset rígido** = **interacción completa**; comprobación
  (`comprobacion/ec3ec4_mixto.py`) **EC3** (clasificación clase 1-4, **abolladura EN 1993-1-5** por
  ancho/área eficaz si clase 4) + **EC4** (M_pl,Rd mixto por fibras, **conexión** P_Rd/Nc/η — espejo de
  `motor-calculo` mixtas) + **fatiga básica EN 1993-1-9** (Δσ FLM3 vs Δσ_C/γ_Mf).
  (2) **OBLICUO** (`idealizacion/oblicuo.py`): malla **romboidal** que sigue la línea de apoyo esviada
  (`x=y·tan φ`); **reparto transversal 2D** + **concentración en la esquina obtusa**; EC2 armado de losa
  o EC3 placa (`comprobacion/ec_oblicuo.py`).
  (3) **CURVO** (`idealizacion/curvo.py`): malla de láminas curvas **sobre la directriz** (arco R /
  `IfcAlignment` de Ola 5); **torsión acoplada** a la flexión (`dT/ds=M/R`) por **Bredt**; EC2 con
  torsión protagonista (`comprobacion/ec_curvo.py`). Subagentes `proyectista-mixto/oblicuo/curvo`;
  lector extendido (`desde_ifc`, `gen_cases`, `gen_ifc._ishape`, write-back). `iso19650-openbim`
  **v0.9.2**: el parser clasifica `mixto`/`oblicuo`/`curvo` (override `Pset_Estructurando_Tipologia` +
  heurísticas: acero+losa, esviaje, radio). **Decisiones (confirmadas):** interacción completa por
  offset · abolladura por ancho eficaz (no autovalores → FEM-3) · fatiga check básico Δσ · malla
  romboidal · Alignment reutilizado · motor intacto. **Validación:** mixto M_pl vs motor-calculo EC4
  **0,47 %** y acción compuesta vs Euler **0,52 %**; oblicuo recto vs viga **0,7 %** + esquina obtusa
  (×1,5→×6,4); curvo flexión vs viga **6,6 %** + **ley T·R≈cte** (T(R)/T(2R)≈2, **3,4 %**) + torsión→0
  en recto. **Casos PUE-18** (mixto, CUMPLE 0,755), **PUE-19** (oblicuo, CUMPLE 0,949), **PUE-20**
  (curvo, CUMPLE 0,666), todos IFC4X3→lector→FEM-2→EC→write-back. Puertas: empaquetado **APTO** ×2
  (desc ≤500) + espejos **IDÉNTICOS** ×2 + no-regresión FEM-0/1/2. **Siguiente: PT 7.6 🔜** (arco,
  no-lineal/pandeo, FEM-3).

- **v1.6 (24/06/2026):** **PT 7.4 ✅ CERRADO** — **FEM-2** (lámina curva + rigidizadores + pared
  delgada) y el primer **vertical avanzado: CAJÓN POSTESADO**. `motor-fem` sube a **v0.3.0**:
  módulos **aditivos** `elementos/lamina_curva.py` (**MITC4**: cuadrilátero curvo membrana+flexión
  con cortante asumido, libre de bloqueo), `elementos/rigidizador.py` (**barra excéntrica con offset
  rígido**, subclase de `ElementoBarra`) y `fem2.py` (`ElementoLaminaCurva` + **pared delgada**:
  `bredt_J`, `shear_lag_beff`, distorsión) — `fem_core`/`barra`/`lamina`/`fem1` **intactos** →
  no-regresión FEM-0/1 **EXACTA por construcción**. Validación **NAFEMS** (`validacion/nafems2.py`):
  Scordelis-Lo **1,6 %**, pinched cylinder **2,8 %**, hemispherical shell **0,4 %**, placa rigidizada
  vs Euler compuesta **1,3 %**, cajón vs Bredt **3,4 %** (tolerancia **±5 %**). `puentes` sube a
  **v0.5.0**: `idealizacion/cajon.py` (**lámina pura**: cajón mallado con láminas curvas +
  diafragmas-rigidizadores; A/Iy/Bredt; recuperación de momento de sección), `comprobacion/ec2_cajon.py`
  (tensiones por **fase** construcción/servicio, descompresión, flexión ELU, **cortante+torsión de
  Bredt**, **shear lag**), `run_all_cajon.py`, subagente `proyectista-cajon` y extensión de `desde_ifc`
  a la tipología `cajon`. `iso19650-openbim` **v0.9.1**: el parser clasifica `cajon` (sección con celda
  cerrada, clave aditiva). **Decisiones (confirmadas):** lámina pura · MITC4 · fases simplificadas +
  coef. EC2 · NAFEMS ±5 %. **Validación de idealización:** cajón de láminas vs viga-cajón de Euler —
  deflexión **0,77 %**, momento de sección **5,3 %** (el resto es *shear lag* real). **Caso PUE-17**
  (cajón 3×40 m, IFC4X3 → lector `cajon` → FEM-2 → EC2 → write-back) **CUMPLE** (aprov. 0,754, gobierna
  la compresión inferior en transferencia; f₁ 3,14 Hz). Puertas: empaquetado **APTO** ×3 (desc ≤500) +
  espejos **IDÉNTICOS** ×3. Semilla de la **Ola 3** (cubiertas laminares) habilitada por la lámina
  curva. **Siguiente: PT 7.5 🔜** (tableros avanzados: metálicos/mixtos, oblicuos, curvos).
- **v1.5 (23/06/2026):** **PT 7.3.1 ✅ CERRADO** — **lector estructural IFC→idealización** +
  **10 casos IFC-driven (PUE-07…16)**. El parser estructural vive en C1
  (`iso19650-openbim` **v0.9.0**, `scripts/estructural/ifc_to_model_estructural.py`: IFC4X3 físico →
  modelo neutro estructural, clave aditiva); el adaptador por tipología en `puentes` **v0.4.0**
  (`scripts/lectura/desde_ifc.py`; los `run_all_*` aceptan un `.ifc`). **Decisión: geometría extruida
  REAL** (A/Iy/Iz exactos de perfiles y de `IfcArbitraryProfileDefWithVoids`; J de pared delgada;
  Psets solo para lo no geométrico). **Hallazgos IFC4X3:** todo el dominio de puentes va en **IFC4X3**
  (`IfcBearing`/`IfcAlignment` no existen en IFC4) y **`IfcStructuralProfileProperties` se eliminó tras
  IFC2X3**. Validación: **round-trip paramétrico↔IFC en las 6 tipologías (máx 1,1×10⁻⁶)** + 10 casos
  e2e (PUE-15 puente completo acoplado CUMPLE; PUE-16 rediseño NO CUMPLE→CUMPLE). **Motor-fem sin
  cambios; núcleo espejado IDÉNTICO.** Puertas: empaquetado **APTO** (puentes v0.4.0 e iso v0.9.0,
  description ≤500) + espejos **IDÉNTICOS**. **Siguiente: PT 7.4 🔜** (cajón postesado, FEM-2).
- **v1.4 (23/06/2026):** **PT 7.3 ✅ CERRADO** — `puentes` sube a **v0.3.0**
  (subestructura) y el motor **`motor-fem` v0.2.1 NO se toca** (sigue **FEM-1**:
  columna + resortes + modal/móvil ya bastan). Dos verticales nuevos (2 subagentes):
  **pila + aparato de apoyo + cimentación** (`proyectista-pilas-apoyos`: columna
  barra 3D + **aparato de apoyo** resorte de 6 GdL en cabeza —elastomérico `k=G·A/Te`
  + giro / POT— + base sobre **resorte Winkler**; reacciones del tablero en **dos
  modos** —dato del caso / acoplado al tablero 7.1-7.2—; EC2 fuste **flexo-compresión
  M-N** + **2.º orden aproximado** + cortante por bielas; **EC7 cimentación enrutada**
  zapata/pilotes/encepado reutilizando `motor-calculo`; **EC8-2 = gancho diferido**) y
  **estribo** (`proyectista-estribos`: muro con **cargas de tablero** en coronación;
  empuje **activo Ka** / **reposo K0** según movilidad; fuste por **motor-fem**;
  **reusa `verificacion_muro`** EC7 vuelco/deslizamiento/hundimiento + EC2
  alzado/puntera/talón; única extensión = el **frenado** del tablero en la estabilidad
  global). Casos **PUE-05** (pila H=8 m + apoyo elastomérico + zapata 6×6, **CUMPLE**
  aprov 0.785 gobierna EC7; f₁=4.51 Hz; δ=1.016) y **PUE-06** (estribo Hm=4.5 m,
  empuje activo Ka=0.307, **CUMPLE** aprov 0.971 gobierna cortante de puntera).
  Puertas: empaquetado **APTO** (description 484/500, 8 ficheros nuevos, 0 encogidos)
  + espejo **IDÉNTICO** (motor sin cambios); **sin regresión** de PUE-01..04 (PUE-03
  0.644, PUE-04 0.985 idénticos). Reuso por PYTHONPATH/copia-byte-fiel:
  `verificacion_muro`, `empujes`/`pesos`/`ka_*` (el import de `solver_muro` arrastra
  PyNite, no disponible), capacidad axil de pilote y biela-tirante de encepado.
  Decisiones cerradas: 2 subagentes, aparato=resorte 6 GdL, cimentación enrutada por
  tipo, 2.º orden aproximado, sísmica diferida, empuje Ka/K0 selector. **Siguiente:
  PT 7.4 🔜** (cajón postesado, FEM-2: lámina curva + rigidizadores + pared delgada).
- **v1.3 (23/06/2026):** **PT 7.2 ✅ CERRADO** — `puentes` sube a **v0.2.0**
  (completa el grupo lineal) y el motor a **`motor-fem` v0.2.1** (extensión
  **aditiva** `esfuerzo_lamina` en `fem1.movil`, sin subir de peldaño: sigue en
  FEM-1). Tres verticales nuevos (3 subagentes): **losa postesada** (lámina **DKMQ**
  + postesado biaxial por **balance de cargas 2D** + envolventes LM1 por objetivo de
  lámina; EC2 tensiones/flexión-franja/punzonamiento; membrana bloqueada, calzada
  inset), **pórtico** (barras + **resortes Winkler** + empuje **K0** reposo + 2.º
  orden aproximado; EC2 dintel/pilas + **EC7** cimentación; deslizamiento por la
  reacción real de base) y **celosía** (barras articuladas Pratt, 2D pura con RY
  coaccionada; EC3 tracción/pandeo curva b/uniones; **fatiga = gancho diferido**).
  Casos **PUE-02** (losa, CUMPLE aprov 0.967, f₁=6.43 Hz), **PUE-03** (pórtico,
  CUMPLE aprov 0.644 gobierna EC7) y **PUE-04** (celosía, CUMPLE aprov 0.985).
  Puertas: empaquetado **APTO** (ambos plugins, description ≤500) + espejo
  **IDÉNTICO**; arnés FEM-0/FEM-1 **sin regresión** + parche de lámina
  (consistencia IL 8.6e-15). Reuso por PYTHONPATH: `balance_2d`,
  `verificacion_losa_postesada`, `verificacion_muro`, EC3. **Siguiente: PT 7.3 🔜**
  (subestructura: pilas, apoyos, estribos, cimentaciones).
- **v1.2 (23/06/2026):** **PT 7.1 ✅ CERRADO** — sube el motor a **`motor-fem` v0.2.0**
  (peldaño **FEM-1**, módulo aditivo `fem1.py`): **análisis modal** (masa concentrada,
  `eigsh` shift-invert, masa participante) y **cargas móviles / líneas de influencia**
  (barrido de carga unidad reutilizando `splu(Kff)` + envolventes por tren tándem+UDL).
  **Sin regresión** del estático FEM-0. Nace la disciplina **`puentes` v0.1.0** (plugin
  propio, decisión nº2): agente `ingeniero-de-puentes` + subagente
  `proyectista-vigas-pretensadas`; idealización por **emparrillado** (barra+barra),
  **acciones IAP-11** (permanentes, LM1 tándem+UDL, térmica, viento, combinaciones),
  **inyección del pretensado** (reusa `ec2_pretensado`), **comprobación EC2** y
  **write-back**; `scripts/nucleo/` espejado. Caso **`caso-PUE-01-vigas-pretensadas`**
  (L=25 m, 4 vigas doble-T HP-45, 2 carriles LM1) **CUMPLE** (aprov. 0.81, gobierna
  cortante; pérdidas 21.2 %; f₁=2.24 Hz). Puertas: empaquetado **APTO** (ambos plugins,
  description ≤500) + espejo **IDÉNTICO**; arnés FEM-1 analítico OK. Decisiones cerradas:
  emparrillado barra+barra, masa concentrada, LM1 completo, pérdidas diferidas
  simplificadas. **Siguiente: PT 7.2 🔜** (losa postesada, pórtico, celosía).
- **v1.1 (23/06/2026):** **PT 7.0 ✅ CERRADO** — nace el plugin **`motor-fem` v0.1.0**
  (peldaño **FEM-0**): barra 3D **Euler-Bernoulli** (conmutador Timoshenko) + lámina
  cuadrilátera **DKMQ** (membrana+drilling), ensamblaje disperso `scipy.sparse` + estático
  lineal con apoyos/resortes, mallador (modelo neutro C1 → malla C5) con adaptador espejo
  `desde_pynite`, API `resolver()` (contrato **C5**) y arnés de validación. **Strangler vs
  PyNite SIN REGRESIÓN**: barra `k` 2e-10 y lámina `K` 1e-16 vs PyNite; analítico EB exacto;
  placa vs Timoshenko 1–2.5 %; patch test membrana 5.6e-16; oráculo pórtico (despl 2e-17) y
  placa (despl/M exactos); caso-01 4e-11 y caso-03 (2646 GdL) Rz pilar 0.0 / M rel 1.3e-11
  vs `resultados.json`. Puertas: empaquetado **APTO** + espejo **IDÉNTICO**. Hallazgo: el
  oráculo PyNite es **EB** (barra) y **DKMQ** (placa), no Timoshenko/MITC4 — por eso FEM-0 los
  reproduce. Decisiones confirmadas: barra EB+conmutador, mallador en `motor-fem`, C5 estático
  + ganchos. **Siguiente: PT 7.1 🔜** (disciplina `puentes` + IAP-11 + FEM-1).
- **v1.0 (23/06/2026):** primera versión. Arranque de la Ola 7 (puentes) con el **motor FEM
  transversal `motor-fem`** (decisión nº8), escalera de capacidades FEM-0…FEM-5, mapa de tipologías,
  capacidades transversales (IAP-11, cargas móviles, fases+diferidos, Alignment), plan PT 7.0–7.8,
  contrato C5, conexión con Ola 3 (cubiertas laminares) y horizonte tensoestructuras, riesgos y
  decisiones. Confirmadas las 4 decisiones de arquitectura con el ICCP.
