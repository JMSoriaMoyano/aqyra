# Repositorio de aprendizaje — Motor de cálculo estructural

Fuente única de conocimiento que se **arrastra entre hilos**. Cada hilo lo lee al empezar
y lo amplía al terminar. Tres secciones: **lecciones** (lo aprendido), **backlog de
incidencias** (lo pendiente de corregir, priorizado) y **decisiones de criterio**.

> Cómo usarlo: al cerrar un caso, añade una entrada en *Lecciones* (qué falló, cómo se
> corrigió, qué generaliza) y mueve/crea las incidencias en el *Backlog*. Las correcciones
> de código se anotan también en `CHANGELOG-plugin.md`.

---

## 1. Lecciones por caso

### Caso 0 — Construcción del catálogo (estado de partida)
- **Convenciones validadas** (no cambiar sin re-validar): ejes X,Y horizontales, Z
  vertical, gravedad −Z; placa MITC4 con `[Mx,My,Mxy]` y momento de campo negativo = sagging
  (tracción inferior); peso propio como A·ρ·g (PyNite usa densidad como peso específico);
  los picos bajo apoyos/cargas puntuales son **singularidades** → usar el valor en la
  sección crítica, no el pico.
- **PyNite — `add_member_dist_load(x1,x2)` usa coordenadas LOCALES al elemento (0..L_elem)**,
  no globales. (Detectado en el muro de contención: el momento salía ~0.)
- **Reacción de muelles**: la fuerza resistente es `k·δ` (signo cuidado al sumar el pasivo
  movilizado en la pantalla).
- **Conexión parcial EC4**: si no caben conectores para conexión total (nervios
  perpendiculares, 1 perno/nervio), `M_Rd = M_a,Rd + η·(M_pl,Rd − M_a,Rd)`, con η ≥ η_min.
- **Contención — fuerza de ancla**: el modelo de muelles subestima el ancla frente al
  método de apoyo libre; **diseñar por la envolvente** de ambos.

### Caso 1 — Pórtico de acero biarticulado (`barras`, EC3) · IFC ortodoxo
- **Parser de sección ortodoxa (INC-01 ✅).** Cuando `RelatingMaterial` de un
  `IfcStructuralCurveMember` es un `IfcMaterialProfileSet`, la sección sale de su
  `IfcMaterialProfile` → `IfcIShapeProfileDef`. Se añadió `perfiles_db.py`: **DB de perfiles**
  (HEB/IPE en SI) con prioridad sobre el cálculo geométrico de placas. Generaliza: el camino
  estándar tiene preferencia y el Pset propio queda como respaldo.
- **DB > geometría (relacionado con INC-06).** Calcular A/I/W del perfil como rectángulos
  ignora los acuerdos (raccords) → subestima A ≈ 4–5 % e I ≈ 5 % (p. ej. IPE 330: A geom.
  59,8 vs catálogo 62,6 cm²). Para resistencia y rigidez **usar valores de catálogo**; la
  geometría es solo respaldo para perfiles no tabulados.
- **Material desde profile set (INC-01 ✅).** `_resolve_material_name` resuelve el material
  tanto de `IfcMaterial` directo como del `IfcMaterialProfileSet`/`IfcMaterialProfile`.
- **Cargas ortodoxas (INC-02 ✅).** `IfcStructuralCurveAction.AppliedLoad`
  (`IfcStructuralLoadLinearForce`, componente Z) da `qz`; el **caso** (G/Q) viene del
  `IfcStructuralLoadGroup` vía `IfcRelAssignsToGroup` y la **barra** de
  `IfcRelConnectsStructuralActivity`. Se mapea action→barra y action→caso por `id()`.
- **Apoyo articulado en la validación cruzada (corrección colateral).** `cross_validate.py`
  solo añadía apoyo si `all(apoyo)` (empotrado) → con **bases biarticuladas** dejaba el
  modelo anaStruct sin apoyos. Ahora discrimina por GDL en el plano: traslaciones DX,DZ
  coaccionadas + giro RY libre → **articulado** (`add_support_hinged`); con RY coaccionado →
  empotrado. Generaliza a cualquier pórtico con bases no empotradas.
- **Coherencia física del pórtico.** M de vano del dintel = 91,6 kN·m < w·L²/8 = 140,4 kN·m
  (cota de biapoyada) porque la acción de pórtico transfiere ≈48,8 kN·m a las esquinas
  (= M en cabeza de pilar). Reacción vertical 93,60 kN/apoyo = (1,35·12+1,50·10)·6/2 exacto.

### Caso 2 — Forjado: losa de hormigón sobre vigas de acero (`laminas` + `barras`) · IFC ortodoxo
- **Parser de láminas ortodoxo (v0.4.0).** La superficie se lee de entidades estándar:
  esquinas de `IfcFaceSurface`→`IfcPolyLoop` (polígono de `IfcCartesianPoint`), espesor de
  `IfcStructuralSurfaceMember.Thickness`, material de `IfcRelAssociatesMaterial`→`IfcMaterial`,
  y cargas de superficie de `IfcStructuralSurfaceAction`+`IfcStructuralLoadPlanarForce` con el
  caso desde `IfcStructuralLoadGroup`. Las **barras** del mismo modelo toman sección/material
  del `IfcMaterialProfileSet`→`IfcIShapeProfileDef` (se reutiliza `perfiles_db.py` de `barras`).
  Generaliza la pauta del caso 1: **camino estándar con prioridad y Pset como respaldo**.
- **Reparto losa→vigas por ancho tributario (INC-03, primer paso).** En losa unidireccional,
  cada viga recibe la carga de su ancho tributario = mitad de la separación entre vigas
  (aquí 2,0 m): `q_línea = q_superficie · b_trib`. La carga total se conserva (los dos anchos
  tributarios cubren el 100 % de la losa) → el equilibrio global cierra exacto. Documentado
  como criterio; alternativa equivalente: reacción de la malla de placa sobre los bordes.
- **Descomposición correcta del caso multi-elemento.** El `solver_3d` existente asume losa
  con **vigas perimetrales en los 4 bordes + pilares** (no aplica a una losa sobre 2 vigas).
  Se resolvió con `run_forjado.py`: losa unidireccional EC2 (banda de 1 m) + reparto + vigas
  con el módulo `barras` (PyNite/EC3). **Lección:** clasificar el sistema estructural antes de
  enrutar; no forzar todo el caso por un único solver acoplado.
- **Validación cruzada de vigas paralelas (cuidado).** `cross_validate.py` proyecta a x–z y
  **colapsa** vigas que solo difieren en `y` (ambas a z=0). Se valida **una viga representativa**
  (las dos son idénticas por simetría) construyendo un submodelo de una sola barra. Pendiente
  general: validación cruzada 3D real de varias barras paralelas (anotado en INC-03).
- **Coherencia física.** Losa: m_Ed = q_ELU·L²/8 = 10,575·4²/8 = 21,15 kN·m/m (banda biapoyada),
  µ=0,134, φ10/125; w_k=0,18 mm < 0,3. Vigas IPE 400: M_Ed=95,2 < M_c,Rd=359 kN·m (26,5 %);
  reacción por extremo (1,35·9,0+1,50·6,0)·6/2 = 63,45 kN. Equilibrio: carga superficie ELU
  10,575·24 = 253,8 kN = Σ reacciones (4·63,45) → error 0,00 %.

### Caso 3 — Losa plana sobre pilares (`laminas` flat, EC2 + punzonamiento) · IFC ortodoxo
- **Sección rectangular ortodoxa (v0.5.0).** Se amplió `perfiles_db.props_from_profile_def`
  a `IfcRectangleProfileDef` (A=b·h, Iy=b·h³/12, Iz=h·b³/12, J de St. Venant, Avz=5/6·A),
  manteniendo la prioridad a catálogo. El parser de `laminas` guarda ya las propiedades del
  pilar (b, h = c1, c2) que necesita el punzonamiento. Generaliza la pauta de los casos 1–2:
  **camino estándar con prioridad, Pset como respaldo**.
- **Inferir el tipo de barra por geometría.** Sin Pset, una barra **vertical** (Δz≠0,
  Δxy≈0) se clasifica como `pilar`. Permite separar pilares de vigas en un IFC ortodoxo sin
  metadatos propios.
- **Apoyos puntuales (INC-03, paso 2).** `solver_flat` ya tenía el solver de placa MITC4 con
  apoyos en pilares, pero leía los pilares de `Pset_Estructurando_Pilar`. Se añadió
  `parse_ortodoxo()`: pilares desde el modelo neutro (cabeza = nodo de mayor z), **posición
  clasificada geométricamente** por la retícula (interior/edge/corner). La malla 0,5 m divide
  el vano de 5,0 m y hace coincidir nodos con las 9 cabezas → reacción por pilar.
- **No duplicar el peso propio.** Cuando la carga G de superficie del IFC **ya incluye** el
  p.p. (caso 3: G=8,5 = 0,28·25 + 1,5), el solver no debe volver a añadir A·ρ·g. Se añadió el
  flag `incluye_pp` (la vía ortodoxa lo activa; la vía Pset lo deja en falso, sin regresión).
  Con ello el equilibrio ELU cierra exacto: 1.597,5 kN aplicados = Σ reacciones (0,000 %).
- **V_Ed de punzonamiento: tributaria vs reacción elástica (lección clave).** En una placa
  elástica sobre **apoyos puntuales idealizados**, la reacción del soporte interior se
  **concentra** muy por encima del área tributaria (aquí 616 kN frente a 399 kN; corners y
  edges quedan por debajo de su tributaria). Es un efecto **singular y sensible al mallado**.
  EC2 admite la **bajada por áreas tributarias** para el punzonamiento de losas planas
  regulares (la redistribución plástica en ELU recupera ese reparto). **Criterio adoptado:**
  V_Ed de cálculo = carga tributaria (interior 25 m² → 399 kN, aprov. 77 %, CUMPLE); se
  reporta además la reacción elástica como **envolvente de seguridad** y se dimensiona la
  solución de punzonamiento para ella (canto / armadura / capitel). Igual que con los picos de
  momento, **no usar el pico singular del apoyo puntual como esfuerzo de diseño directo**.
- **Fisuración consistente con el diámetro dispuesto.** La verificación de `verificacion_flat`
  asumía φ16; con la armadura inferior real (φ10) y la mínima de flexión, w_k>0,3 mm. El
  orquestador del caso ajusta la separación de la armadura inferior (φ10/150→φ10/125) con el
  **diámetro realmente dispuesto** hasta w_k≤0,3 (resultó 0,234 mm). Lección: la fisuración
  debe calcularse con φ y As efectivamente colocados, no con un φ por defecto.
- **Coherencia física.** q_ELU=15,975 kN/m²; tributaria interior 25 m²→399 kN; equilibrio
  1.597,5 kN exacto. Flexión: vano m≈36,3 kN·m/m (α≈0,09·q·L²), soporte m≈91,3 kN·m/m
  (hogging acotado al percentil 97). Flecha total 1,43 mm ≪ L/300=16,7 mm.

### Caso 4 — Cubierta / forjado inclinado (`laminas` incl, EC2 + membrana) · IFC ortodoxo
- **Superficie inclinada ortodoxa (v0.6.0).** `solver_incl.parse()` da prioridad a la vía
  ortodoxa: `_parse_ortodoxo()` deduce de las esquinas inclinadas de `IfcFaceSurface`/
  `IfcPolyLoop` el **ancho L_v** (borde de alero, horizontal), la **longitud de faldón L_u**
  (borde lateral, sobre la pendiente) y el **ángulo θ = asin(Δz/L_u)**; material y cargas G/Q
  vienen del camino estándar (`ifc_to_model_3d`). Generaliza la pauta de los casos 1–3:
  **camino estándar con prioridad, Pset como respaldo**. Verificado: Lu=6,0 / Lv=8,0 / θ=30°.
- **Apoyos de borde desde el IFC (INC-03, continuación).** Los apoyos de alero y cumbrera se
  leen de los `IfcStructuralPointConnection`+`IfcBoundaryNodeCondition` y se **clasifican por
  geometría** (alero z≈0 → `[T,T,T]`; cumbrera z≈z_máx → `[F,T,T]`), aplicando los GDL reales
  en los nodos del borde. **Bordes laterales libres**: el faldón es una losa **1-vía** que
  salva L_u entre alero y cumbrera (no bidireccional). Antes `solve()` apoyaba los 4 bordes y
  **duplicaba el peso propio** (G del IFC ya lo incluye): ambos corregidos (`incluye_pp`).
- **No duplicar el peso propio (recordatorio del caso 3).** La carga G de superficie del IFC
  ortodoxo (6,0 = 5,0 losa + 1,0 cubrición) ya incluye el p.p.; `incluye_pp=True` evita volver
  a sumar A·ρ·g. Con ello el equilibrio ELU cierra exacto.
- **Flexión normal vs membrana tangencial (lección clave del plano inclinado).** Las cargas de
  gravedad *true-length* se reparten como cargas **verticales** nodales por área real del quad;
  el FE descompone solo: la componente **normal** q·cosθ produce la **flexión** (vano en la
  dirección de L_u → momento **My** dominante ≈ q_n·L_u²/8 = 37,4 kN·m/m; FE 38,1, +1,8 %) y la
  componente **tangencial** q·senθ produce los **esfuerzos de membrana** en el plano. La
  dirección gobernante (la del vano, y) se arma en la **capa exterior** (canto útil mayor).
- **Membrana del faldón: empuje tangencial + acoplamiento flexión-membrana (matiz).** El empuje
  tangencial total ELU q·senθ·A = 230 kN se transmite a alero y cumbrera (ambos coartados en el
  plano → **arco atado**: reacciones iguales y opuestas, FY neta = 0). El campo n_y del FE
  (±67 kN/m, simétrico, media≈0) está **dominado por el acoplamiento flexión-membrana del borde
  coartado** (arching), bastante mayor que la cota axial simple q·senθ·L_u/2 ≈ 14 kN/m; es
  **sensible a la hipótesis de apoyo** y secundario frente a la capacidad del hormigón
  (n_Rd=fcd·t=4.000 kN/m → uRd=1,7 %). Igual que con los picos de momento/punzonamiento, no se
  toma el pico como esfuerzo de diseño directo; se reporta el campo y se comprueba la compresión.
- **Fisuración con el φ dispuesto (caso 3).** Con la dirección gobernante en la capa exterior
  (d=170 mm) y φ10/125, w_k=0,231 mm ≤ 0,3 (antes, con la principal en la capa interior d=157,
  salía 0,346 > 0,3). La selección de separación se hace con el diámetro realmente colocado.
- **Coherencia física.** q_ELU=9,6 kN/m²; área real 48 m² → carga total 460,8 kN = Σ reacciones
  (alero 230,7 + cumbrera 230,1), error 0,000 %; My=38,1 kN·m/m (φ10/125, µ=0,067); flecha
  normal 4,84 mm = 24 % de L/300; membrana uRd 1,7 %; invariancia MITC4 OK (0,78 %).

### Caso 5 — Soporte de hormigón + zapata aislada (`cimentaciones` zapata, EC2 + EC7) · IFC ortodoxo
- **Cadena pilar→cimiento ortodoxa (v0.7.0).** `solver_zapata.parse_ortodoxo()` da
  prioridad a la vía estándar y reconstruye todo el problema desde el modelo neutro
  (`ifc_to_model_3d`) + lecturas IFC puntuales: geometría de la zapata de la superficie
  (`IfcStructuralSurfaceMember`/`IfcFaceSurface`), **pilar** identificado por geometría
  (barra vertical, `tipo="pilar"`), lado desde `IfcRectangleProfileDef` y **pie del pilar =
  centro de carga**; **carga de cabeza** (N + M_x) de `IfcStructuralPointAction`+
  `IfcStructuralLoadSingleForce`. `parse_auto()` cae al Pset como respaldo. Generaliza la
  pauta de los casos 1–4: **camino estándar con prioridad, Pset como respaldo**.
- **Lecho elástico Winkler desde el borde IFC (INC-03, continuación).** El módulo de balasto
  se **reconstruye de la rigidez de los `IfcBoundaryNodeCondition`** (`TranslationalStiffnessZ`):
  k_s = k_nodo / área tributaria (esquina → (B/2)·(L/2)). Verificado: de k_esquina=6,25·10⁷ N/m
  se recupera **k_s=40 MN/m³** (= dato geotécnico). El solver reconstruye su **propia malla
  fina** de muelles (k=k_s·trib), no reutiliza los 4 nodos de esquina del IFC.
- **Bajada de carga con peso propio (lección clave).** El axil que llega al terreno = N de
  cabeza + **peso propio de la zapata** (caso G). Hay que **añadir el p.p.** (no estaba en el
  solver): repartido por área tributaria en caso G. Equilibrio Σ reacciones del lecho = axil
  total, error ~0 %. **Matiz importante:** el p.p. **cuenta para el hundimiento (EC7)** —es
  presión sobre el terreno— pero **no flecta la zapata (EC2)**: la presión del p.p. uniforme
  está equilibrada por su propia reacción uniforme y produce momento nulo en la zapata. Por eso
  EC2 (flexión/cortante/punzonamiento) usa la **presión NETA inducida por el pilar** = presión
  de contacto − reacción del p.p. (= N_pilar/A).
- **EC7 hundimiento por área eficaz (lección clave, análoga al pico singular de casos 3-4).**
  Con carga excéntrica el **pico de presión de borde** (σ_max lineal 273 kPa) y el **pico nodal
  del FE Winkler** (271 kPa) **superan R_d=250 kPa**, pero no son el valor de diseño. La
  comprobación EC7 de hundimiento (EN 1997-1 **Anejo D / Meyerhof**) usa la **presión sobre el
  área eficaz**: σ_ef = N_d/(B'·L') con B'=B−2e_x, L'=L−2e_y → **246 kPa ≤ 250 (98 %) CUMPLE**.
  Los picos de borde se reportan como **envolvente de contacto**. Se comprueba además **sin
  despegue**: e=0,075 m < B/6=0,417 m (toda la base comprimida). Igual criterio que con los
  picos de momento/punzonamiento: **no usar el pico singular como valor de diseño**.
- **Flexión: voladizo más cargado + armadura en capa exterior.** El momento de la zapata se
  integra en la **cara del pilar** tomando el **voladizo más comprimido** de cada dirección (con
  excentricidad, un lado flecta más; tomar sólo un lado lo subestimaba). La **dirección
  gobernante** (mayor momento, aquí *y* por el M_x de cabeza) se coloca en la **capa exterior**
  (mayor canto útil), la otra en la interior. Recubrimiento 50 mm (terreno).
- **Fisuración con el φ dispuesto (casos 3-4).** w_k se calcula con el diámetro realmente
  colocado (φ12) en la dirección gobernante (cuasipermanente): w_k=0,272 ≤ 0,30 mm (91 %).
- **Rendimiento (INC-04 ampliado).** La malla fina (0,125 m → 441 nodos) es lenta; se
  **filtran las combinaciones** analizadas/almacenadas a las necesarias (ELU, ELS_car, ELS_cp)
  para que entre en el presupuesto de cálculo. El orquestador `run_all_zapata` encadena los
  pasos; en sandbox conviene ejecutar solver / verificación / mapas por separado.
- **Coherencia física.** N_ELU = 1,35·700 + 1,50·250 + 1,35·92(p.p.) = **1.444 kN** = Σ
  reacciones del lecho (error ~0 %). σ_ef=246 kPa (98 %); flexión M_y=132,7 kN·m/m → φ12/125
  (μ=0,02, As_min gobierna); punzonamiento V_Ed,neto=169 kN (11 %); cortante 56 %; asiento ELS
  4,9 mm; MITC4 OK (Timoshenko 2,5 % / 0,5 %).

### Caso 6 — Forjado colaborante / viga mixta acero-hormigón (`mixtas`, EC4) · IFC ortodoxo
- **Viga mixta ortodoxa (v0.8.0).** `solver_mixta.parse_ortodoxo()` da prioridad a la
  vía estándar y reconstruye todo el problema desde el modelo neutro
  (`laminas/ifc_to_model_3d`): **perfil de acero** de `IfcMaterialProfileSet`→
  `IfcIShapeProfileDef`, **losa** del `IfcStructuralSurfaceMember` (canto, material,
  **ancho tributario = luz transversal** al eje de la viga, no la longitudinal) y
  **cargas por fase** de los `IfcStructuralLoadGroup`+`IfcStructuralSurfaceAction`
  clasificadas por el **nombre del grupo** (`*_construccion`/`*_mixta`) y por G*/Q*.
  `parse_auto()` cae al Pset si no hay datos estándar. Generaliza la pauta de los casos
  1–5: **camino estándar con prioridad, Pset como respaldo**.
- **Datos sin entidad de análisis estándar → Pset (igual que k_s/R_d del caso 5).** Los
  **conectores** (perno) y la **chapa nervada** (hp, hc, b0, nr, apeado) no tienen
  entidad IFC de análisis; se leen de `Pset_Estructurando_Conectores`/`_Losa` en el
  curve member. Es correcto mantenerlos como Pset; el IFC sigue siendo ortodoxo.
- **IPE 360 al catálogo (INC-06 ✅ para este perfil).** La geometría de placas daba
  A≈69,95 cm² (−3,8 % frente a 72,73 de catálogo) por ignorar los acuerdos. Se añadió
  IPE 360 a `perfiles_db` (A, Iy, Wpl,y, Avz de tabla) → resistencia y rigidez con
  valores de catálogo; las **dims (h,b,tw,tf)** se siguen leyendo de la geometría
  (exactas) para el modelo de fibras. **Criterio:** catálogo para propiedades
  integrales (A/I/W/Av), geometría para cotas.
- **Conexión parcial (lección clave EC4 §6.2.1.3).** Con chapa **perpendicular** y
  1 perno/nervio no caben los conectores de conexión total: N_f=29,4 por media luz
  pero solo n_disp=19,3 → **η=0,66 < 1**. Resistencia con conexión parcial
  `M_Rd = M_a,Rd + η·(M_pl,Rd − M_a,Rd)` = 280,2 + 0,66·(510,8−280,2) = **431,6 kN·m**,
  con **η ≥ η_min=0,40** (§6.6.1.2). El P_Rd del perno lleva la reducción **kt** por
  chapa perpendicular (kt=0,85, tope tabla 6.2 para 1 perno a través de chapa).
- **Fases de construcción (sin apear).** Dos análisis sobre la **misma** viga isostática
  (M/V no dependen de la sección): (1) **construcción** — el acero solo resiste
  hormigón fresco (2,5) + ejecución (0,75) → EC3 del perfil (M_c,Rd=Wpl·fy); (2)
  **mixta** — la sección mixta resiste el total + uso. La **flecha** suma la fase de
  construcción (acero, I_a, que en unpropped queda fijada) + las cargas de servicio
  sobre la sección mixta homogeneizada con n₀ (corto) y n_L (largo, fluencia ~Ecm/3).
- **Coherencia física.** Fase mixta q_ELU=30,46 kN/m → M=q·L²/8=243,6 kN·m, V=q·L/2=121,8
  kN (FE = analítico, error 0,000 %); construcción q=14,26 → M=114,0 / V=57,0. b_eff=2,10 m
  (=b0+L/4 ≤ sep). M_Ed/M_Rd=56 %, cortante 22 %, construcción 41 %, flecha total 61 %
  (19,5/32 mm, L/250) y activa 18 % (4,2/22,9 mm, L/350). PNA en ala superior.

### Caso 7 — Muro de carga (esbeltez EC2) + muro de contención ménsula (EC7 DA-2*) · IFC ortodoxo
- **Muros ortodoxos (v0.9.0).** Vía **ortodoxa** en los dos módulos de muro
  (`laminas/solver_muro.py` y `muros-contencion/solver_muro.py`), con prioridad y
  Pset de respaldo: **alzado (H), espesor (= `Thickness`) y material** de la
  `IfcStructuralSurfaceMember` vertical (vía `ifc_to_model_3d`). **Clasificación**
  muro de carga vs muro de contención por la **presencia de
  `Pset_Estructurando_Terreno`** (contención) / su ausencia + carga de cabeza
  (carga). Generaliza la pauta de los casos 1–6: **camino estándar con prioridad,
  Pset como respaldo**.
- **Carga de cabeza ortodoxa (igual que el pilar del caso 5).** El axil excéntrico
  del muro de carga se lee de `IfcStructuralPointAction`+`IfcStructuralLoadSingleForce`
  (**ForceZ** + **MomentY** = N·e), con caso del `IfcStructuralLoadGroup`. **Signo:
  la carga vertical de cabeza es de compresión** (FZ negativa) — al portarla
  ortodoxamente hubo que negar el valor (el Pset legacy ya lo guardaba negativo);
  con el signo correcto el equilibrio ELU cerró a 0,000 %.
- **Datos sin entidad de análisis estándar → Pset (igual que k_s/R_d del caso 5 y
  conectores del caso 6).** La **geometría en T** de la zapata (puntera, talón, B,
  canto, Df) y los **parámetros del terreno** (γ, φ, c, δ, pasivo, base, R_d) no
  tienen entidad IFC de análisis: se mantienen en `Pset_Estructurando_Muro` /
  `_Terreno` / `_Carga_Muro_q`. El IFC sigue siendo ortodoxo.
- **Esbeltez EC2 por columna modelo / curvatura nominal (lección clave, §5.8.8).**
  El método simplificado de muros §12.6.5.2 (factor Φ) es conservador; el caso pide
  el **método de la columna modelo**: λ vs λ_lim (§5.8.3.1) y, si esbelto,
  `M_Ed = M0Ed + M2` con `M2 = N·e2`, `e2 = Kr·Kφ·(1/r0)·lo²/π²`. La sección se
  comprueba por **interacción N-M** con armadura vertical simétrica (bloque
  rectangular). En el caso 7: λ=52 > λ_lim=27 → esbelto; M_Ed = 17,0 + 14,3 = 31,3
  kN·m/m, M_Rd=67,3 (φ10/200 c/cara), aprov. 47 %. El método §12.6.5.2 da 21 % (más
  conservador en N, pero no expone M2 ni el N-M).
- **Estabilidad EC7 DA-2* (vuelco/deslizamiento/hundimiento).** Vuelco (EQU,
  γ_dst=1,10 / γ_stb=0,90), deslizamiento (GEO, rozamiento de base + **pasivo
  parcial** f=0,5, γ_Rh=1,10) y hundimiento (GEO, **σ por área eficaz B′ de
  Meyerhof** ≤ R_d), todos con CS ≥ 1. **Sin despegue**: e=0,398 < B/6=0,567 (toda
  la base comprimida). El deslizamiento es el que más se acerca al límite
  (u=0,97); el pasivo movilizado parcial es decisivo.
- **Fisuración con el φ dispuesto + capa exterior (lección casos 3–6, aplicada a la
  contención).** La armadura de flexión por sí sola (mínima EC2) deja w_k > 0,3 mm
  con barras grandes; se **selecciona (φ, s)** para w_k ≤ 0,3 mm con el φ realmente
  dispuesto bajo combinación cuasipermanente, y la **principal va en la capa
  exterior** (trasdós del alzado, cara inferior de la puntera, superior del talón).
  Resultó alzado φ16/100 (w_k=0,263), puntera φ16/225 (0,277), talón φ20/200 (0,296).
- **Robustez multi-superficie + aislamiento de módulos homónimos.** El parser de
  `muros-contencion` usaba `by_type[0]` (rompía con 2 superficies); ahora
  **selecciona la superficie por su Pset**. Además, importar el `ifc_to_model_3d`
  de `laminas` insertaba su carpeta en `sys.path` y **ensombrecía los módulos
  homónimos** de `muros-contencion` (`verificacion_muro`, `plots_muro`…): se carga
  por **ruta explícita con salvaguarda de `sys.path`**.
- **Coherencia física.** Muro de carga: N_Ed=537,4=1,35·(250+14,7 p.p.)+1,50·120;
  equilibrio 0,000 %. Muro de contención: Ka=0,333 (Rankine φ=30°); Eh=114,4 ≈
  0,5·0,333·19·5,5²+0,333·10·5,5; M_base alzado 240,6 ≈ analítico 240,3; validación
  empuje 0,21 %.

### Caso 8 — Losa de cimentación (raft) multipilar sobre lecho elástico (`cimentaciones` raft, EC2 + EC7) · IFC ortodoxo
- **Raft ortodoxo multipilar (v0.10.0).** `solver_raft.parse_ortodoxo()` + `parse_auto()`
  dan prioridad a la vía estándar (Pset como respaldo, sin regresión). Generaliza la cadena
  pilar→cimiento del caso 5 de **una zapata con un pilar** a una **losa con varios pilares**:
  la losa (BX, LY, canto=`Thickness`, material) de la `IfcStructuralSurfaceMember` horizontal
  (vía `ifc_to_model_3d`); los **pilares** identificados por geometría (barras verticales,
  `tipo="pilar"`), con su **lado** (`IfcRectangleProfileDef`) y su **pie** (centro de carga);
  y la **carga de cabeza por pilar** mapeada `IfcStructuralPointAction`→**nodo de cabeza**
  (`IfcRelConnectsStructuralActivity`, `RelatingElement.Name` = `Pxx_cabeza`) y action→caso
  por el `IfcStructuralLoadGroup`. El Pset legacy (`_Losa`/`_Pilar_*`) queda de respaldo.
- **Lecho elástico Winkler multipilar (igual que caso 5).** k_s se **reconstruye de la
  rigidez de los `IfcBoundaryNodeCondition`** de los 4 nodos de esquina (z=0):
  k_s = k_esquina / ((BX/2)·(LY/2)); verificado k_esquina=2,4·10⁸ N/m → **k_s=40 MN/m³** (=
  dato geotécnico). El solver reconstruye su **propia malla fina** de muelles (k=k_s·trib),
  no reutiliza los 4 nodos del IFC. R_d se toma de `Pset_Estructurando_Suelo`.
- **Signo de la carga de cabeza (lección del caso 7, confirmada).** La vía ortodoxa lee
  `ForceZ` (negativa = gravedad −Z) y la aplica tal cual; el solver Pset esperaba valores
  **negativos** (el self-test del módulo ya los guardaba negativos). El backup Pset del IFC
  del caso 8 los guardaba **positivos** → la vía Pset daría signo erróneo, pero la **ortodoxa
  tiene prioridad** y cierra el equilibrio a 0,00 %. (Se añadió además el **peso propio de la
  losa** al solver del raft, caso G por área tributaria; equilibrio = cabezas + p.p.)
- **EC7 capacidad: presión media característica ≤ R_d; pico como envolvente (criterio casos
  3–5).** La presión media de contacto (combinación **característica** G+Q, p.p. incluido)
  se compara con R_d; el **pico** bajo pilares/esquinas del campo de Winkler es una
  **singularidad** → envolvente, no valor de diseño. Aquí p_med=231 ≤ 300 kPa (u=0,77); pico
  caract. 247 / ELU 342 kPa (informativo). Sin despegue (p_min>0).
- **Asiento diferencial centro–borde (objeto del caso).** El mayor axil de los pilares
  centrales hace que el centro asiente más que las esquinas: s_max=6,18 / s_min=5,78 →
  Δs=0,40 mm; distorsión 1/5045 ≪ 1/500. La losa de 0,60 m es rígida y reparte bien.
- **Punzonamiento de cimentación con alivio del terreno (EN 1992-1-1 §6.4.4(2)).** En un raft,
  la reacción **ascendente** del terreno dentro del perímetro de control reduce el esfuerzo de
  punzonamiento: V_Ed,red = N_Ed − p_med,ELU·A_u1. Con canto 0,60 m (d≈0,53) y p≈322 kPa el
  alivio (~1.730 kN) supera el axil del pilar más cargado (1.598 kN) → V_red≈0 (no crítico). Se
  reporta también la utilización **sin alivio** (conservadora, 237 %) para transparencia. Es la
  razón física por la que el punzonamiento rara vez gobierna un raft grueso (≠ losa plana del
  caso 3, donde no hay presión ascendente).
- **Cortante (1 dirección) y fisuración con el φ dispuesto + capa exterior (lecciones 3–7).**
  Se añadieron a `verificacion_raft`: cortante de placa fuera de la huella (V_Rd,c sin armadura,
  x 73 % / y 36 %) y **fisuración** con la armadura **realmente dispuesta** (helper `disponer()`
  que elige Ø/separación para cumplir ELU **y** w_k≤0,3 mm a la vez). La armadura **principal**
  (dirección X, lados largos) va en la **capa exterior** (mayor d). Resultó inferior X φ16/150
  (w_k=0,293 mm ≤ 0,30).
- **Coherencia física.** Σ aplicada ELU = 1,35·(3.900+353 p.p.) + 1,50·1.320 = **7.722 kN** =
  Σ reacciones del lecho (error 0,00 %); M_x sagging de vano 231 kN·m/m (φ16/150, capa
  exterior); end-to-end (solver+verif.+mapas) 15,7 s en sandbox.

### Caso 9 — Cimentación profunda: pilote + encepado + pantalla anclada (`pilotes` + `bielas-tirantes` + `muros-contencion`, EC7 + EC2) · IFC ortodoxo
- **Tres sistemas en un mismo IFC: clasificar ANTES de enrutar (lección clave del caso).**
  El IFC del caso 9 contiene 3 subestructuras. Las **dos barras verticales** (pilote y
  pantalla) son indistinguibles por geometría (ambas `tipo=pilar`), y la superficie podría
  confundirse con una losa/raft. La clasificación se resuelve por el **Pset presente**
  (`Pset_Estructurando_Pilote` / `_Pantalla` / `_Encepado`), igual que el caso 7 separó muro
  de carga vs contención por `Pset_Estructurando_Terreno`. Cada parser ortodoxo **selecciona
  su elemento por Pset**, no por `by_type[0]` (que con 3 curve members habría cogido el
  elemento equivocado — la pantalla `parse()` legacy usaba `[0]` y habría leído un pilote).
- **Sección circular ortodoxa (v0.11.0).** Se amplió `perfiles_db.props_from_profile_def` a
  `IfcCircleProfileDef` (A=π·D²/4, Iy=Iz=π·D⁴/64, Wpl=D³/6, J=2·I, Avz=0,9·A; antes devolvía
  `None`). El parser genérico ya reconoce la sección del pilote ("Pilote D600"). Generaliza
  la pauta de casos 1–8: catálogo con prioridad, geometría de respaldo.
- **Pilote ortodoxo (v0.11.0).** `solver_pilote.parse_ortodoxo()` lee **D** del
  `IfcCircleProfileDef` (Radius·2), la **carga de cabeza** (N_G, N_Q, H) de los
  `IfcStructuralPointAction`+`IfcStructuralLoadSingleForce` mapeados al **nodo de cabeza**
  (z máx) por `IfcRelConnectsStructuralActivity` y caso del `IfcStructuralLoadGroup`
  (ForceZ −Z → axil de compresión como magnitud; ForceX → H lateral), y la **geotecnia**
  kh/qs/qb del Pset. Dos pilotes idénticos → se analiza el representativo (misma D/L/carga
  por pilote = bajada del pilar /2). **EC7 capacidad axil** R_c,d = R_s/γ_s + R_b/γ_b (fuste
  qs·π·D·L + punta qb·A_b, γ_s=γ_b=1,10); **lateral** como viga sobre muelles kh (PyNite),
  esfuerzos M/V y flecha de cabeza, EC2 sección circular con armadura mínima EN 1536 (0,5 %·Ac).
- **Encepado ortodoxo = región D (v0.11.0).** `run_all_encepado.parse_ortodoxo()` toma el
  **canto = `Thickness`** de la superficie y la **separación entre pilotes** de la **distancia
  entre los dos `IfcStructuralPointConnection` de cabeza** (los que llevan BC
  `TranslationalStiffnessZ`, z≈0); la **carga del pilar** del `IfcStructuralPointAction` sobre
  el nodo de pilar (z≈0, **sin BC**, distinto de las cabezas) — el discriminante "tiene/no
  tiene BC vertical" separa el nudo de pilar de los nudos de apoyo. Ancho/lado pilar/Ø pilote
  (geometría de región D, sin entidad estándar) se mantienen en Pset. **EC2 §6.5 bielas y
  tirantes**: celosía (2 bielas + 1 tirante) resuelta con el solver de barras y contrastada
  con la estática cerrada (T=R/tanθ, C=R/senθ), comprobación de biela y nudos CCC/CCT y
  armadura del tirante.
- **Pantalla anclada ortodoxa (v0.11.0).** `solver_pantalla.parse_ortodoxo()` lee el
  **espesor** del `IfcRectangleProfileDef` (XDim) y el material de la asociación; terreno
  (γ/φ/q/R_d), ancla (z, inclinación, separación, bulbo τ) y la geometría de excavación /
  empotramiento (sin entidad de análisis estándar) se mantienen en Pset. **EC7** empuje
  activo (Rankine) + sobrecarga, terreno delante como **muelles** (pasivo movilizado), ancla
  como **apoyo horizontal** (su reacción = fuerza de ancla); ley M/V del fuste, empotramiento
  (FoS pasivo), bulbo y armado EC2.
- **Fuerza de ancla por la envolvente (lección caso 0 confirmada).** El modelo de muelles
  subestima el ancla frente al método de **apoyo libre**; se diseña por la **envolvente** de
  ambos (T_h muelles 138 kN/m × sep ≈ 276 vs apoyo libre → **F_ancla=403 kN** gobierna).
- **Coherencia física.** Pilote: N_Ed=1,35·650+1,50·225=**1.215 kN** ≤ Rc,d=1.876 (65 %),
  equilibrio lateral 0,000 %. Encepado: N_Ed=1,35·1.300+1,50·450=**2.430 kN**, celosía vs
  cerrado 0,00 %, θ=39,7°. Pantalla: Ka=0,333 (Rankine φ=30°), equilibrio horizontal ELU
  0,00 %, M_máx=251 kN·m/m. Tres veredictos **CUMPLE**, aprovechamientos ≤ 1.

### Caso 10 — Edificio integrado: pórtico + forjado mixto + muro + cimentación (TODOS los módulos) · IFC ortodoxo multi-elemento
- **Clasificar/enrutar ANTES de resolver, iterando TODO el IFC (cierre de INC-03,
  lección clave del caso y de la tanda).** Un único `IfcStructuralAnalysisModel`
  con 4 sistemas (5 barras + 3 superficies) se resuelve construyendo el modelo
  neutro genérico (`laminas/ifc_to_model_3d`) y un **clasificador
  multi-elemento** (`scripts/clasificador.py`) que itera cada barra y cada
  superficie y la enruta por **geometría + sección + material + lecho/carga de
  cabeza**: barra vertical de acero I → pilar EC3; barra horizontal de acero I
  aislada → viga/dintel EC3; barra horizontal de acero I **asociada a losa** →
  viga mixta EC4; superficie vertical de hormigón con carga de cabeza → muro EC2;
  superficie horizontal de hormigón **con lecho** → zapata EC7; barra vertical de
  hormigón rectangular **sobre zapata** → cadena pilar→cimiento. Generaliza la
  clasificación por geometría+Pset de los casos 7 (carga/contención) y 9
  (pilote/pantalla/encepado) a un grafo completo.
- **Asociaciones sin Pset (objetivo del caso).** viga↔losa (mixta) por
  proximidad en planta (centro de la viga dentro del bbox de una losa horizontal
  **sin lecho**) y pilar↔zapata por **pie común** (base de la barra dentro del
  bbox de una superficie horizontal **con lecho**). El Pset marcador
  (`Portico/Mixta/MuroCarga/Suelo`) queda solo como confirmación.
- **Sub-IFC node-minimal por subsistema = la forma robusta de dar a cada módulo
  "su porción".** En vez de tocar los `by_type[0]` internos de cada parser (que
  en multi-elemento cogen el elemento equivocado — p. ej. `solver_zapata` lee
  `IfcStructuralSurfaceMember[0]`, que aquí es la **losa mixta**, no la zapata; o
  el muro/zapata **iteran todas** las `IfcStructuralPointAction` y mezclarían las
  cabezas), el clasificador **extrae un sub-IFC** con solo los miembros, **los
  nodos referenciados** (endpoints de barra + esquinas de superficie —incluidos
  los 4 nodos de lecho de la zapata— + nodos de las acciones) y las acciones del
  subsistema. Cada `run_all*` se ejecuta sobre su sub-IFC reproduciendo EXACTO las
  condiciones de sistema único de los casos 1/5/6/7. **Sin nodos huérfanos**: si
  se dejan todos los nodos, PyNite marca inestables los del pórtico (lección al
  resolver el caso).
- **Orquestador con subprocesos = aislamiento de módulos homónimos.**
  `run_all_edificio.py` lanza cada `run_all*` en **subproceso** → cada paquete
  importa sus propios `solver_*`/`combinaciones`/`plots_*`/`verificacion_*` sin
  que el `sys.path` de uno ensombrezca al otro (mitiga INC-04bis homónimos sin
  cargar por ruta explícita en un único proceso). En sandbox, ejecutar **por
  subsistema** (`--solo`) por el límite de 45 s; la malla fina de la zapata es el
  cuello de botella (~26 s).
- **Convenios de Pset/topología distintos entre casos → parsers backward-compatible.**
  El generador del caso 10 usó (a) **vértices distintos** para la arista de la
  barra y para el `IfcStructuralPointConnection` → el id no casa: respaldo por
  **coordenadas** en `barras/ifc_to_model` (caso 1 con vértices compartidos sigue
  por id); (b) **otros nombres** de Pset de conectores/chapa (`Diametro_m/
  Altura_m/nr_por_nervio` vs `d_m/hsc_m/sep_long_m`) → `solver_mixta` lee **ambos
  convenios** (sin paso de nervio explícito, lo deriva 0,207 m hp58/hc62
  `[confirmar]`); (c) el **momento de cabeza en MomentY** (caso 5 en MomentX) →
  `solver_zapata` toma `max(|Mx|,|My|)`. Las tres correcciones son acotadas y
  verificadas sin regresión (casos 1/6 re-ejecutados; 5 idéntico a nivel de parser).
- **Predimensionado real: la zapata de modelo no cumple por 2 %.** Con N+M de
  cabeza mayor que el caso 5 (momento también en Q), la zapata **2,5×2,5** da
  hundimiento por área eficaz **σ_ef=255 ≤ R_d=250 kPa → 102 %**. El motor
  **amplía a 2,6×2,6** (centrada en el pilar) con pre-chequeo analítico + un único
  solve FE de confirmación → **94 %**. Es el comportamiento esperado de un
  predimensionado: dimensionar hasta cumplir, no forzar la geometría dada.
- **Coherencia física (los 4 subsistemas, picos como envolvente).** Pórtico EC3:
  HEB 240 N-M 22,9 %, IPE 360 30,5 %, equilibrio exacto, PyNite vs anaStruct OK.
  Mixta EC4: b_eff=2,10 m, M_Ed=333/M_Rd=450 (74 %), η=0,66, cortante 25 %, fase
  construcción 32 %, flecha 64 %. Muro EC2: λ=52>λ_lim=30 esbelto, columna modelo
  M_Ed=M0Ed 16,4+M2 13,9=30,2 kN·m/m, M_Rd=68,1 (φ10/200), N-M 44 %. Cimentación
  EC2+EC7: zapata 2,6×2,6 σ_ef 94 %, e=0,116<B/6 (sin despegue), punzonamiento
  17 %, cortante 51 %, fisuración w_k=0,28 mm (93 %), asiento 4,9 mm, equilibrio
  del lecho 0,00 %. **Edificio: los 4 CUMPLEN; aprovechamientos ≤ 1.** Cierre de
  la **primera tanda**.

### Caso 11 — Pantalla de cortante + sísmico EC8 (`sismico` + biblioteca EC8) · APERTURA de la SEGUNDA TANDA (Dirección 1)
- **Un TIPO DE ANÁLISIS nuevo, no sólo una verificación (lección clave del caso y de la
  tanda).** Hasta el caso 10 el motor resolvía estática lineal y añadía cláusulas EC. El
  caso 11 abre el **análisis dinámico/espectral**: se crea el módulo `sismico/` y la
  **biblioteca EC8** (`ec8.py`), reutilizables por los casos sísmicos siguientes (núcleos,
  Mononobe-Okabe). Corrección **estructural pero acotada**: grupo nuevo, sin tocar los
  casos 1–10. Versión **coordinada con la Dirección 2** (R1): caso 11 → **0.13.0**, R1 →
  0.14.0; el `.plugin` instalado es **acumulativo** (contiene `sismico/` **y**
  `puente_analitico/`).
- **Voladizo equivalente (stick) con masas concentradas: la idealización correcta de una
  pantalla.** La pantalla (superficie vertical) se reduce a un **stick de 6 nodos** con la
  sección de pared (E, I=tw·Lw³/12=1,60 m⁴) y las **5 masas de planta** (W_i de los
  `IfcStructuralPointAction`, ForceZ −Z → W_i; m_i=W_i/g) concentradas en sus nodos.
  **El cortante NO es despreciable en muro corto**: con H/Lw=15/4 la flexibilidad de
  cortante (Timoshenko, φ=12EI/(GA_vL²)=5,12) domina sobre la de flexión → hay que
  incluirla o el periodo sale muy corto y la rigidez sobrestimada.
- **Espectro EC8 Sd(T) de cuatro ramas como biblioteca (EN 1998-1 §3.2.2.5).** Sd(T) se
  construye de los parámetros del `Pset_Estructurando_Sismo` (ag, S, TB, TC, TD, q, λ) con
  el límite inferior β·ag (β=0,2 `[confirmar AN]`). Verificado en la **meseta**
  (TB≤T≤TC): Sd=ag·S·2,5/q=0,20·1,15·2,5/3,0=**0,1917 g**. Igual que ks/Rd/conectores/
  terreno de casos 5/6/7/9, los datos sísmicos **sin entidad de análisis estándar** van en
  Pset; el IFC sigue siendo ortodoxo.
- **Modal espectral (scipy.eigh) vs fuerzas laterales: contraste y envolvente.** El modal
  (K y M del stick condensados a los GDL laterales, `scipy.linalg.eigh`) da **T1=0,408 s**
  (en meseta), **M_eff,1=68,9 %** (≥60–70 %, criterio de modo fundamental dominante) y
  Fb,SRSS=785 kN; el **método de fuerzas laterales** (§4.3.3.2) da Fb=Sd·M·λ=**928,6 kN**.
  La diferencia (15,5 %) la explican λ=0,85 y que M_eff,1=68,9 %<100 %. **Gobierna la
  envolvente** (fuerzas laterales, mano 929 kN). Equilibrio **Fb=ΣF_i 0,000 %**; momento
  de vuelco en base **9.877 kN·m** (altura eficaz 10,64 m); N base=ΣW=5.700 kN.
- **Verificación de pantalla de cortante (EC2 §6.2.3 + EC8 §5.4): el elemento de borde
  gobierna.** Cortante del alma con **amplificación DCM ε=1,5** `[confirmar AN]` (aprov.
  0,31, lejos de V_Rd,max); **N-M en la base** por fibras con armadura de borde+alma
  (0,86); **deriva** muy holgada (0,23; d_r·ν=5,1 mm ≤ 0,75 %·h=22,5 mm). El que manda es
  el **elemento de borde confinado** (EC8 §5.4.3.4.2): la compresión de borde obliga a
  **agrandar l_c de 0,60 a 1,20 m** (=0,30·Lw) en predimensionado para que F_compr≤N_Rd,c
  (aprov. 0,97). Misma filosofía que los casos previos (dimensionar hasta cumplir; picos
  como envolvente). **Veredicto CUMPLE, aprov. máx 0,97.**
- **Coherencia física.** Sd(meseta)=0,1917 g; T1=0,408 s (meseta); M_eff,1=68,9 %;
  Fb,lateral=928,6 kN ≈ mano 929; M_vuelco=9.877 kN·m; equilibrio 0,000 %. Predimensionado
  a revisar y firmar por técnico competente; NDP marcados `[confirmar AN]` (ag, S,
  TB/TC/TD, β, q, λ, ε, ν, límite de deriva — NCSE-02 / EC8 España).

### Caso R1 — Pórtico físico: puente IFC FÍSICO (BIM real) → modelo analítico (`puente_analitico` → `barras`) · APERTURA de la Dirección 2
- **Físico ≠ análisis: el IFC físico no tiene modelo de análisis, hay que DERIVARLO
  (lección clave de la tanda real).** Los casos 1–10 partieron de un **IFC ortodoxo**
  (entidades del dominio de análisis: `IfcStructuralCurveMember`, acciones, apoyos). Un
  entregable BIM real es un **IFC físico**: `IfcColumn`/`IfcBeam` con **geometría** de
  barrido, material y sección, estructura espacial, pero **sin entidades de análisis ni
  cargas**. Verificado: el parser de análisis (`laminas/ifc_to_model_3d`) lee **0
  elementos** del IFC físico — esa es exactamente la brecha que cubre el nuevo módulo
  `puente_analitico/`. El puente produce el **mismo modelo neutro estándar**, de modo que
  el clasificador/enrutador y `barras` se reutilizan **sin cambios** (v0.14.0).
- **Eje = directriz del barrido (extracción geométrica).** El eje de cada elemento lineal
  se obtiene del **`ObjectPlacement` compuesto** resuelto a coordenadas de mundo con
  `ifcopenshell.util.placement.get_local_placement` (origen = columna de traslación;
  dirección = **eje local Z** del placement) y la **longitud = `Depth`** del
  `IfcExtrudedAreaSolid` (respaldo: `ExtrudedDirection`·`Depth` proyectada al mundo si la
  extrusión no es +Z local). Verificado: Pilar_1 (0,0,0)→(0,0,4) L=4,00; Pilar_2
  (6,0,0)→(6,0,4); Dintel (0,0,4)→(6,0,4) L=6,00. **Sección/material** de
  `IfcMaterialProfileSetUsage`→`IfcMaterialProfileSet`→`IfcMaterialProfile`→
  `IfcIShapeProfileDef` (reutiliza `perfiles_db`, prioridad a catálogo; geometría del
  `SweptArea` de respaldo) → HEB 200 / IPE 330 / S275.
- **Grafo de nudos por intersección de ejes con tolerancia (el punto de valor de la D2).**
  Se fusionan extremos coincidentes (tol 1 mm) y se trocea una barra cuando el extremo de
  otra cae en su **interior** (proyección paramétrica t∈(0,1) + distancia ≤ tol). En R1 los
  ejes son limpios y se cortan en los extremos → **4 nudos, 3 barras** (= caso 1). Los
  **offsets/excentricidades** físico↔analítico (eje físico no centrado) se endurecen en
  **R5** (IFC "real-sucio").
- **Apoyos y cargas son HIPÓTESIS del calculista (no están en el IFC físico).** En BIM real
  las condiciones de contorno y las cargas no viajan en el IFC. En el modelo de prueba se
  aportan como Pset y el puente las traslada: apoyo `Pset_Estructurando_ApoyoBase`
  (biarticulado → `[T,T,T,F,F,T]`, nudos a cota base) y carga
  `Pset_Estructurando_CargaHipotesis` (G=12/Q=10 kN/m, −Z → N/m con signo) sobre la barra
  del dintel. Se **documentan explícitamente** en la memoria como hipótesis a confirmar.
- **Validación = reproducir un resultado conocido.** Geometría idéntica al caso 1 a
  propósito: el modelo derivado del **físico** da equilibrio **93,60 kN/apoyo** (Σ=187,2 kN,
  ~0 %; horizontales ±12,19 kN), **HEB 200 32,0 %**, **IPE 330 44,6 %**, validación cruzada
  PyNite vs anaStruct conforme — **idéntico al caso 1**, lo que certifica que el puente no
  introduce sesgo. Patrón replicable para R2–R4 (forjado, muro+zapata, edificio físico).

### Caso 12 — Viga postesada isostática (`pretensado` + biblioteca EC2 §5.10) · APERTURA de la tipología de PRETENSADO
- **El pretensado entra de DOS formas equivalentes y hay que validarlo cruzando ambas
  (lección clave del caso).** (a) **Cargas equivalentes / load balancing**: el tendón
  parabólico de flecha f=e ejerce una carga repartida hacia arriba `w_p = 8·P·e/L²` más el
  axil de compresión P (y momentos de anclaje P·e_anc, nulos si ancla en el c.d.g.). (b)
  **Fuerza + excentricidad**: tensión directa por fibra `σ = −P/A ± M·c/I` con
  `M = M_ext − P·e` (el momento del pretensado M_p=−P·e es *hogging*, contraflecha). Los dos
  métodos deben dar el **MISMO estado tensional**; en el caso 12 coinciden a Δ=0,0 MPa bajo
  cuasipermanente (sup −4,55 / inf −1,99 MPa). Es la verificación cruzada propia de esta
  tipología (análoga a PyNite vs anaStruct en barras).
- **Load balancing: dimensionar P para equilibrar la PERMANENTE (residual ~0).** P_m,∞ se
  fija con `P = w_perm·L²/(8·e)`: aquí 21,25·400/(8·0,50)=**2125 kN**, que da w_p=21,25 kN/m =
  permanente exacta → residual 0,0 %. La sobrecarga q queda sin equilibrar y produce el
  momento neto de servicio. σp,∞=P/Ap=1090 MPa=**0,586·fpk**; en transferencia P0=2535 kN
  (σp0=0,699·fpk), pérdidas diferidas (P0→P_m,∞) ≈16 %.
- **Tensiones por fibra en TRES estados (transferencia, cuasiperm, rara) con límites EC2
  distintos.** Transferencia (P0+g0): compresión ≤ **0,6·fck(t)** (§5.10.2.2; con fck(t)=32
  MPa → 19,2 MPa), todo comprimido (sup −0,67 / inf −7,13). Cuasipermanente (P_∞+M_qp):
  compresión ≤ **0,45·fck** (linealidad de fluencia §7.2(3); 18,0 MPa) y control de
  descompresión del fondo (inf −1,99 ≤ 0 → sin descompresión). Rara (P_∞+M_rara): compresión
  ≤ 0,6·fck (24,0 MPa) y tracción de fondo (**inf +0,99 MPa < fctm=3,5**) → fisuración
  controlada. El estado crítico de tracción se da en la combinación rara, no en la
  cuasipermanente.
- **ELU de flexión por FIBRAS con armadura ACTIVA (+ pasiva), como en EC4.** No-linealidad de
  sección por bloque de compresión (η·fcd, profundidad λ·x; para C40/50 ≤50 MPa: η=1,0,
  λ=0,8). Equilibrio de axil C=T → x; tracción del acero activo a fpd=fp01k/γs (1426 MPa) y
  pasivo a fyd. M_Rd=2908 ≥ M_Ed=2334 kN·m, x/d=0,23 (dúctil). Generaliza el modelo de fibras
  del caso 6 al acero activo.
- **g0 con γc=25 kN/m³ (convención EC2/EHE), no A·ρ·g con g=9,81.** Para coincidir con la
  práctica española (y el chequeo de mano: M_g0=812,5 kN·m), el peso propio se toma
  g0 = A·γc = 0,65·25 = 16,25 kN/m. Documentado en el solver (equivale a A·ρ·g con γc=25 000
  N/m³). Matiz frente a la convención general A·ρ·g del catálogo: aquí se prioriza el peso
  específico normativo del hormigón armado.
- **Datos del pretensado sin entidad de análisis estándar → Pset (igual que k_s/R_d del caso
  5, conectores del 6, terreno del 7, sismo del 11).** P0/σp0, Ap, fpk, trazado/e, μ/k,
  penetración de cuña y relajación van en `Pset_Estructurando_Pretensado` del curve member; el
  IFC sigue siendo ortodoxo (sección/material/apoyos/cargas g2,q por la vía estándar). El
  parser carga `laminas/ifc_to_model_3d` por **ruta explícita con salvaguarda de `sys.path`**
  (lección caso 7/11) con respaldo robusto a lectura directa del IFC.
- **Pérdidas: instantáneas (rozamiento μ·(θ+k·x), penetración de cuña con longitud de
  influencia x_set, acortamiento elástico) y diferidas (ec. 5.46 combinada
  retracción+fluencia+relajación, relajación ec. 3.29 clase 2).** El modelo de pérdidas
  diferidas independiente (con eps_cs y φ adoptados, **[confirmar AN]**) cierra contra el
  P_m,∞ del Pset con ~9 % de holgura — coherente para predimensionado; los valores titulares
  (P_m,∞, σp,∞) provienen del Pset/load balancing, no del recálculo de pérdidas.

### Caso R2 — Forjado físico: puente IFC FÍSICO → analítico con SUPERFICIES (`puente_analitico` → `laminas`+`barras`) · segundo peldaño de la Dirección 2
- **Superficie media + espesor de `IfcMaterialLayerSet`: el puente ya lee losas físicas
  (lección clave del caso).** R1 derivaba solo ejes de barras; un forjado real lleva una
  **superficie física** (`IfcSlab`). El puente se amplía: la **superficie media** = footprint
  del `IfcExtrudedAreaSolid` (esquinas del `IfcRectangleProfileDef`/
  `IfcArbitraryClosedProfileDef`) llevado a MUNDO con el placement compuesto
  (`get_local_placement` ∘ `get_axis2placement` de la `Position` del sólido) y la **cota
  media** del barrido (base + `ExtrudedDirection`·`Depth`/2). El **espesor** sale de
  `IfcMaterialLayerSetUsage`→`IfcMaterialLayerSet` (Σ `LayerThickness`); la geometría (`Depth`)
  es respaldo. Verificado: footprint X[0,6]×Y[0,4], **t=0,120 m del LayerSet**, z_med=−0,06,
  material C30/37. Generaliza la pauta del catálogo (camino estándar con prioridad, geometría
  de respaldo) al lado **físico** de la D2.
- **Propiedades de hormigón desde el IFC físico: fck de `CompressiveStrength`, fctm DERIVADO.**
  El `IfcMaterialProperties` del hormigón trae E/G/ν/ρ/fck pero **no fctm**; el puente lo
  calcula con EC2 (3.1): fctm=0,30·fck^(2/3) (fck≤50). Así el modelo neutro derivado lleva las
  claves que `run_forjado` necesita (`fck`, `fctm`, `E`) sin tocar el motor.
- **Conectividad superficie↔barras por proximidad en planta (como el caso 10).** La losa se
  asocia a las **vigas que la soportan**: eje de viga dentro/bajo el contorno en planta de la
  superficie (bbox X/Y con tolerancia) → `vigas_asociadas=[B1,B2]`. Es la misma idea que la
  asociación viga↔losa del clasificador del caso 10, ahora sobre geometría física.
- **Salida = el MISMO modelo neutro estándar → motor reutilizado SIN CAMBIOS.** El puente
  escribe `superficies[]` con las claves de `laminas/ifc_to_model_3d` (`esquinas_coords`,
  `espesor`, `material`, `cargas`) y las cargas de hipótesis de SUPERFICIE
  (`Pset_Estructurando_CargaHipotesis`, G/Q kN/m², −Z). El orquestador
  `run_all_real_forjado.py` clasifica (1 superficie horizontal de hormigón + barras
  horizontales de acero I → `forjado_losa_sobre_vigas`) y enruta a `laminas/run_forjado`
  (losa EC2 unidireccional + reparto por ancho tributario + vigas EC3), sin modificar
  `run_forjado` ni `barras`. El plotter del caso 2 fija nombres `V1/V2`; para no tocarlo se
  añadió `plots_real_forjado.py` con nombres de barra **genéricos** del puente.
- **Validación = reproducir el caso 2 (el puente no introduce sesgo).** Geometría idéntica al
  caso 2: del **físico** se obtiene losa φ10/125 **m_Ed=21,15 kN·m/m** (w_k=0,18 mm, flecha
  39 %), reparto trib 2,0 m → G=9,0/Q=6,0 kN/m, **vigas IPE 400 26,5 %**, **reacción
  63,45 kN/extremo**, **equilibrio 0,000 %** (253,8=253,8 kN), validación cruzada viga 0,042 %
  y strip de losa 0,000 % (MITC4 OK) — **idéntico al caso 2**. Patrón replicable a R3 (muro+
  zapata físicos) y R4 (edificio físico). Offsets eje de viga↔plano medio de losa → R5 (INC-07).
- **Coordinación de versiones (hilos en paralelo, carrera resuelta).** R2 = **v0.16.0** (el
  caso 12, pretensado, tomó 0.15.0). Durante el hilo el caso 12 reescribió el `.plugin`
  instalado a 0.15.0 con `pretensado/` **válido**; el reempaquetado final de R2 se hizo
  **acumulativo partiendo de ese 0.15.0** y añadiendo encima los ficheros de R2. El **v0.16.0
  instalado contiene TODO**: casos 1–11 + `sismico/` (EC8) + `pretensado/` (EC2 §5.10) +
  `puente_analitico/` con R1 (barras) **y** R2 (superficies) — 133 entradas, verificado
  end-to-end desde el paquete instalado. Lección: en carrera de escritura sobre la carpeta
  compartida, **partir del `.plugin` instalado MÁS RECIENTE** (no del que se leyó al empezar) y
  re-verificar la versión instalada justo antes y después de copiar.

### Caso 13 — Losa plana postesada 2D (`pretensado` + `laminas/flat`, EC2 §5.10 + §6.4.4) · lleva el PRETENSADO a 2D
- **El pretensado a 2D = dos balances 1D acoplados por dirección (lección clave).** Tendones
  **banded en X** (sobre líneas de pilares) + **distribuidos en Y**, cada familia parabólica de
  drape a equilibra su presión `w_p = 8·P/m·a/L²`. El reparto se hace **½ permanente por
  dirección**: w_p,x = w_p,y = 8·212·0,17/8² = **4,505 kN/m²** → w_p = 9,01 ≈ permanente 9,0
  (**residual 0,11 %**). P/m=212 kN/m por dirección → **σcp = P/m / t = 212/0,25 = 0,848 MPa**.
  La precompresión es **biaxial** (σcp,x y σcp,y; media para el término de punzonamiento).
- **Punzonamiento con efecto favorable del pretensado §6.4.4 (LO NUEVO).** Dos efectos, ambos
  RELAJAN el aprovechamiento: (a) **v_Rd,c += k₁·σcp** (k₁=0,10 `[confirmar AN]`) y (b) **V_Ed,red =
  V_Ed − V_p**, donde **V_p = (w_px+w_py)·A_control** es la componente vertical de los tendones
  que cruzan u1 (por equilibrio del trozo de losa interior al perímetro de control). Pilar
  interior V_Ed,ELU = (1,35·9,0+1,5·5,0)·64 = **1.258 kN**; con d=0,204 m, u1=4,36 m, β=1,15:
  v_Ed/v_Rd,c **sin** pretensado ≈ 2,62; **con** pretensado ≈ 2,28 (V_p≈14 kN, +k₁σcp en v_Rd,c).
  El pretensado **relaja** pero **no elimina** la necesidad de armadura de punzonamiento en una
  losa de 0,25 m a 8,0 m de vano sin ábaco/capitel → se dispara el dimensionado (canto/Asw/
  capitel) como en el caso 3. **Lección de predimensionado: las losas planas postesadas finas a
  L=8 m suelen requerir refuerzo de punzonamiento o ábacos; el pretensado ayuda al canto, no lo
  sustituye.**
- **Ampliación retrocompatible del punzonamiento del caso 3.** `laminas/ec2_punz_fis.punzonamiento`
  recibe `sigma_cp=0, V_p=0, k1=0.1` por defecto → con los defaults reproduce EXACTAMENTE el caso 3
  (k₁·0 = 0, V_Ed,red = V_Ed). Patrón "parámetro opcional con default neutro" para no romper casos
  anteriores (igual que el alivio del terreno §6.4.4(2) del raft, caso 8).
- **Tensiones por fibra y franja con los momentos NETOS tomados del FEM (no de fórmulas de vano
  aislado).** Primer intento con `M_franja = w_net·L²/8` (vano simplemente apoyado) sobre-estimaba
  el momento de campo ~2× (en una losa CONTINUA el coeficiente es ~L²/14–16) y disparaba falsos
  excesos de tracción en rara. **Corrección**: los momentos de servicio (transferencia/cuasiperm/
  rara) se leen de los **combos del solver MITC4** (ELS_cp/ELS_car/P0_transfer, que ya incluyen el
  caso P), con **envolvente por percentil** (P95 campo, P97 hogging) para evitar el pico singular.
  Es la razón de ser del motor: la continuidad la da el FEM, no el chequeo de mano. Con ello, bajo
  cuasiperm la sección queda comprimida o con tracción reducida y bajo la rara la **tracción de
  fondo < fctm=3,5 MPa** (fisuración controlada), como en el chequeo de mano.
- **Caso P del pretensado en la placa MITC4 = presión equivalente hacia ARRIBA.** El pretensado se
  aplica como `add_quad_surface_pressure(+w_p)` (qz>0, contra la gravedad) en un **caso de carga P**
  con coeficiente 1,0 (valor medio P_m,∞ en servicio/ELU; combo de transferencia con P0). El
  **equilibrio ELU se cierra sobre la carga NETA** (1,35(g0+g2)+1,5q − 1,0·w_p), no sobre la bruta.
- **Contraste cargas-equivalentes vs fuerza+excentricidad por franja (como en el caso 12, ahora
  2D).** Identidad exacta: M_net = (w_qp−w_p)·L²/8 y M_tot = M_ext + M_p con M_p = −P·e; como
  w_p·L²/8 = (8·P·e/L²)·L²/8 = P·e, ambos métodos coinciden a **Δ≈0** por franja. Verificación
  cruzada propia de la tipología.
- **g0 NO viene del IFC (incluye_pp=False).** A diferencia del caso 3 (donde la G de superficie ya
  incluía el peso propio), aquí la G del IFC es solo g2=2,75 kN/m² y g0=t·25=6,25 lo añade el solver
  en un caso **G0** aparte (igual que el caso 12). Cuidado con `parse_ortodoxo` de `solver_flat`, que
  fuerza `incluye_pp=True`: el solver de losa postesada lo **sobrescribe a False** y añade G0 él
  mismo (evita duplicar / omitir el peso propio).
- **Datos del pretensado en el `Pset_Estructurando_Pretensado` de la SUPERFICIE** (no del curve
  member como en el caso 12): layout banded/distribuido, drape, P/m por dirección, σp0/σp,∞,
  pérdidas. El IFC sigue siendo ortodoxo (losa+pilares+cargas g2/q por la vía estándar). Pérdidas
  diferidas (σp0→σp,∞) = (1339−1116)/1339 = **16,7 %** (rango 16–18 %).

### Caso R3 — Muro + zapata físicos: puente IFC FÍSICO → analítico con superficies VERTICALES + cimientos (`puente_analitico` → `laminas`+`cimentaciones`) · tercer peldaño de la Dirección 2
- **Clasificar la superficie por la NORMAL del plano medio, no por las z de las esquinas
  (lección clave del caso).** R2 trataba TODO sólido barrido como losa horizontal (footprint
  en planta + cota media): para un `IfcWall` extruido en +Z eso es **degenerado** (devuelve una
  «superficie horizontal» del grosor de planta a media altura, no el plano medio vertical). En R3
  `_superficie(element, clase, espesor_layer)` decide la orientación por la **dirección de
  extrusión en mundo** y el **aspecto del footprint**: si el elemento es `IfcWall`, la extrusión
  es vertical (|edw_z|≈1) y la huella es «alargada y fina» (lado_menor ≤ 2,5·espesor del
  `IfcMaterialLayerSet` y lado_mayor > 1,5·lado_menor) → **VERTICAL**; resto → **HORIZONTAL**. El
  modelo neutro lleva ahora `orientacion`, `normal`, `altura`, `largo` en cada superficie. R1/R2
  intactos: `IfcSlab` sigue saliendo horizontal y, sin walls/footings, el comportamiento es idéntico.
- **Plano medio VERTICAL del `IfcWall` (lección clave).** El plano medio es un **rectángulo
  vertical** (longitud L_w del muro × altura H = profundidad de extrusión): se **colapsa la
  dirección fina** del footprint a su línea central y se generan **4 esquinas de la base a la
  cabeza** del barrido (z_base → z_base+edw_z·depth), NO a media altura. Así `_vertical(coords)`
  de `solver_muro` y la clasificación dan vertical, y el largo del muro alimenta la faja de
  cálculo. Verificado: muro 1,0×0,20 en planta, extrusión +Z 3,0 m → plano medio 1,0×3,0 vertical,
  espesor 0,20 m del `IfcMaterialLayerSet`.
- **Footprint y canto del `IfcFooting` (igual que la losa de R2).** La zapata es HORIZONTAL:
  footprint del `IfcExtrudedAreaSolid` a la cota media del barrido + canto = Σ `LayerThickness`
  del `IfcMaterialLayerSet`. Verificado: huella 2,5×2,5, canto 0,60 m del LayerSet, C30/37.
- **Cadena muro→cimiento por proximidad en planta + cota (como pilar↔zapata del caso 10).** El
  muro vertical se asocia a la zapata que lo soporta: **centro del muro dentro de la huella**
  (bbox X/Y con tolerancia) **y** pie del muro ≈ cara superior de la zapata (z_med + canto/2) →
  `zapata_asociada`/`muros_asociados`. Generaliza la asociación geométrica del caso 10 a
  superficies físicas verticales↔horizontales.
- **Solvers reutilizados SIN CAMBIOS construyendo los dicts `model` desde neutro + Psets (patrón
  R2).** Los `parse_ortodoxo`/`run_muro_carga`/`run_all_zapata` releen entidades de ANÁLISIS
  (`IfcStructuralSurfaceMember`, `IfcStructuralPointAction`, `IfcBoundaryNodeCondition`) que el IFC
  FÍSICO no tiene. El orquestador `run_all_real_muro_zapata.py` **construye** los dos dicts `model`
  (muro: H/L/espesor/malla/beta/material + `cargas` top_vertical NEGATIVO + `cabeza` N+M=N·e;
  zapata: B/L/espesor/malla/material + c_pilar/ks/Rd/xp/yp + `cargas` N negativo + Mx) desde el
  modelo neutro del puente + los Psets, y llama directamente `solver_muro.solve`+`verificacion_muro`
  y `solver_zapata.solve`+`verificacion_zapata.verificar`. Mismo espíritu que R2 (forjado).
- **Aislamiento de módulos homónimos por ruta explícita (lección caso 7/11, confirmada).**
  `solver_muro`/`verificacion_muro`/`plots_muro` viven en `laminas`; `solver_zapata`/
  `verificacion_zapata`/`plots_zapata` en `cimentaciones`. El orquestador los carga con un helper
  `_load(modname, ruta, extra_paths)` que inserta las carpetas del paquete **solo durante el
  import** y restaura `sys.path` después, evitando que un paquete ensombrezca los homónimos del
  otro. Los plotters (`plots_muro.generar`/`diagrama_NM`, `plots_zapata.generar`) toman dicts y se
  reutilizan tal cual (no leen ficheros fijos), sin añadir un plotter genérico.
- **Qué sale de GEOMETRÍA vs de PSET (idea del puente físico).** Del físico: plano medio del muro
  (L_w×H) y su espesor; huella y canto de la zapata; material/fck (fctm derivado EC2); cadena
  muro→cimiento. Del Pset (hipótesis del calculista, no existen en un IFC físico): carga de cabeza
  del muro (N_G/N_Q + e), terreno (k_s, R_d), bajada de carga del soporte equivalente a la zapata
  (la geometría caso-5 no se deriva limpiamente de la faja de muro de 1,0 m) y cotas de apoyo.
- **Validación = reproducir los casos 7 y 5 (el puente no introduce sesgo).** **Muro** (caso 7):
  N_Ed=537,4 kN/m, λ=52>λ_lim ⇒ esbelto, M_Ed=M0Ed+M2≈31,3 kN·m/m, φ10/200 c/cara, N-M≈47 %,
  equilibrio vertical ELU ~0,000 %. **Zapata** (caso 5): N_ELU=1.444 kN, EC7 σ_ef≤R_d=250 kPa
  (e≈0,075<B/6 sin despegue), EC2 flexión My φ12/125 capa exterior, punz ~11 %, fisuración φ12
  w_k≈0,272 mm, equilibrio del lecho ~0 %. Patrón replicable a R4 (edificio físico). Offsets
  eje↔plano medio → R5 (INC-07).
- **Reparación del truncado de `puente.py` (INC-04, confirmada).** Al ejecutar en sandbox, el
  `ast.parse` detectó que `puente.py` quedó **truncado** a media función `parse()` (línea 548,
  `dz = abs(z_pie - z_` sin cerrar) por la edición de líneas largas. Se restauró cortando en la
  última línea íntegra y reescribiendo por **heredoc** el tramo final (cierre de la cadena
  muro↔cimiento, lectura de la carga de cabeza del muro, volcado de superficies al modelo neutro
  con `orientacion`/`normal`/`largo`/`cabeza`, apoyos e hipótesis), validado con `ast.parse`.
  Mantener la práctica de escribir por heredoc y validar SIEMPRE con `ast.parse` tras editar.
- **Ejecución completa en el hilo principal (con `mcp__workspace__bash`).** Generado `caso-R3.ifc`,
  corrido el orquestador `run_all_real_muro_zapata.py` (puente → clasificar → muro `solver_muro` +
  zapata `solver_zapata` → equilibrios → 7 diagramas) y la memoria Word, **reproduciendo los casos
  7 y 5 EXACTAMENTE** (muro N-M 47 %, λ=52, M_Ed 31,3; zapata σ_ef 246/250, e=0,075, punz 11 %,
  w_k 0,272; equilibrios 0,000 %). **`.plugin` v0.18.0 reempaquetado acumulativo** partiendo del
  v0.17.0 instalado (preservando `sismico/`+`pretensado/`+`puente_analitico/` R1+R2 y añadiendo la
  ampliación de R3), con re-verificación de la versión instalada antes y después de copiar.

### Caso R4 — Edificio físico completo: puente IFC FÍSICO multi-elemento → analítico de TODO el edificio (`puente_analitico` → barras + mixtas + láminas + cimentaciones) · cuarto peldaño de la Dirección 2
- **Derivar TODO el edificio de un único IFC físico y enrutar CADA elemento (lección clave
  del caso y cierre de INC-03 en la vía física).** R1/R2/R3 derivaban del físico cada
  **tipo** por separado (barras, superficies horizontales, superficies verticales +
  cimientos). R4 lo hace **a la vez**: `puente.parse` sobre un IFC físico por plantas
  (3 `IfcColumn` + 2 `IfcBeam` + 1 `IfcSlab` + 1 `IfcWall` + 1 `IfcFooting`, sin entidades
  de análisis) devuelve **un único modelo neutro** con 8 nudos + 5 barras + 3 superficies,
  con la clasificación por orientación (R3), la conectividad superficie↔barras (R2,
  `vigas_asociadas={B2→Mixta_Losa}`) y la cadena pilar↔zapata (R3/caso 10) ya resueltas.
  **El `puente.py` no se tocó**: ya sabía hacer todo esto; R4 solo añade el clasificador/
  enrutador multi-elemento y el orquestador. Verificado: ningún elemento se pierde (itera
  TODO, no `by_type[0]`).
- **Clasificador/enrutador multi-elemento SOBRE EL MODELO NEUTRO del puente (no releyendo el
  IFC).** `clasificar_neutro_edificio(model, ifc)` generaliza el patrón `clasificar_neutro`
  de R2/R3 a un edificio completo: itera barras y superficies y asigna (rol, módulo) por
  **geometría + sección + material + lecho/carga de cabeza + asociaciones** — barra de acero
  I (no asociada a losa) → `barras` EC3; viga de acero I **asociada a losa sin lecho** →
  `mixtas` EC4; superficie vertical de hormigón → `laminas/solver_muro` EC2; superficie
  horizontal de hormigón con lecho (`Pset_Suelo`/`IfcFooting`) → `cimentaciones/solver_zapata`
  EC7; pilar vertical de hormigón **sobre la huella de una zapata** (pie común) → cadena
  pilar→cimiento. Es el análogo «físico» de `scripts/clasificador.py` (caso 10), pero
  consume el **modelo neutro del puente** en vez de releer el IFC ortodoxo con
  `laminas/ifc_to_model_3d` (que lee 0 elementos de un IFC físico). El Pset marcador queda
  solo como confirmación.
- **Solvers reutilizados SIN CAMBIOS construyendo los dicts `model` desde neutro + Psets
  (patrón R2/R3, ahora ×4).** `build_model_portico` filtra el sub-modelo de barras del
  pórtico y fija apoyos biarticulados en los nudos de base; `build_model_mixta` arma el dict
  de la viga mixta (perfil de catálogo `perfiles_db` + dims del `IfcIShapeProfileDef`;
  conectores/chapa de `Pset_Estructurando_Conectores`/`_Losa`; **cargas por fase de
  `Pset_Estructurando_CargasMixta`** —en el físico no hay acciones de superficie—);
  `build_model_muro` (= R3) y `build_model_zapata` (= R3 + `M_Q` + **predimensionado** con
  ampliación). Se llaman directamente `solver`/`solver_mixta`/`solver_muro`/`solver_zapata`
  + sus verificaciones. No se usan `parse_ortodoxo`/`run_all*` (releen entidades de análisis
  que el físico no tiene).
- **Aislamiento de módulos homónimos por SUBPROCESO por subsistema (lección caso 10
  confirmada).** `barras`, `mixtas`, `laminas`, `cimentaciones` tienen módulos homónimos
  (`solver_*`, `combinaciones`, `verificacion_*`, `plots_*`). El orquestador
  `run_all_real_edificio.py` ejecuta cada subsistema **re-invocándose con `--solo`** en un
  subproceso → cada proceso carga solo los módulos de un paquete (sin que el `sys.path` de
  uno ensombrezca al otro). Dentro de un `--solo` se cargan por **ruta explícita con
  salvaguarda de `sys.path`** (helper `_load`). La malla fina de la zapata (~24 s) es el
  cuello de botella; el edificio completo (4 subprocesos) corre en ~35 s.
- **Las cargas de la viga mixta van en Pset (no hay acciones de superficie en el físico).**
  En el caso 10 (ortodoxo) las cargas por fase venían de `IfcStructuralSurfaceAction` +
  `IfcStructuralLoadGroup` (`*_construccion`/`*_mixta`). En el físico no existen → se aportan
  en `Pset_Estructurando_CargasMixta` de la losa (G_losa/Qc/G2/Q kN/m²) y el constructor las
  lee. Misma idea que conectores/chapa (caso 6) y terreno (caso 5): datos sin entidad de
  análisis estándar → Pset.
- **Validación = reproducir el caso 10 desde un IFC FÍSICO (el puente no introduce sesgo).**
  Pórtico EC3: HEB 240 **22,9 %**, IPE 360 **30,5 %**, reacción **93,60 kN/apoyo**,
  validación cruzada PyNite vs anaStruct CONFORME. Mixta EC4: **M_Ed=333 kN·m**, **η=0,66**
  (idénticos al caso 10); M_Rd=522 (u 64 %), flecha 53 % — la rutina EC4 vigente sitúa el
  **PNA en el ala superior** (verificado a mano: para Fcf=1844,5 y N_a=2322,65 idénticos al
  caso 10, la compresión de acero sobre el PNA es (N_a−Fcf)/2=239 kN → 4,8 mm en el ala),
  de donde M_Rd=607,6 (full) → 522 (parcial); la diferencia frente al 450 histórico del caso
  10 es un **refinamiento de la rutina de flexión del motor, no del puente**. Muro EC2:
  C30/37 λ=52 esbelto, **N-M 45 %**, φ10/200, equilibrio 0,000 %. Cimentación EC7+EC2:
  zapata **ampliada 2,50→2,55** (predim.), **σ_ef 245/250 kPa (98 %)**, e=0,116<B/6 sin
  despegue, punz 14 %, fisuración φ12 w_k=0,278 mm (93 %), equilibrio del lecho 0,000 %.
  **Los 4 subsistemas CUMPLEN; aprovechamientos ≤ 1.** Cierre de la tubería
  físico→analítico→cálculo de extremo a extremo. Offsets eje físico↔analítico → R5 (INC-07).

### Caso 14 — Viga postesada CONTINUA (hiperestática, 2 vanos): momentos secundarios, línea de presiones y concordancia (`pretensado` + FEM de viga continua, EC2 §5.10/§5.5/§5.10.8) · lleva el PRETENSADO a estructuras HIPERESTÁTICAS
- **El momento secundario es lo que cambia al pasar de isostático a hiperestático (lección
  clave del caso).** En una viga isostática (caso 12) el pretensado solo produce el
  **primario** M₁ = −P·e. En una **continua** el pretensado induce una **reacción en el apoyo
  redundante** (el central) → aparece el **secundario/hiperestático** M_sec. Se obtiene como
  diferencia: aplicar las **cargas equivalentes** del tendón (w_p hacia arriba en los vanos)
  a la **viga continua** (FEM) da **M_p,tot**; el primario es **M₁ = −P·e(x)** (estructura
  liberada); **M_sec = M_p,tot − M₁**. Verificado: **M_sec es LINEAL entre apoyos y NULA en
  los apoyos extremos** (R² = 1,000000; extremos 0,00/0,00 kN·m), máxima sobre el apoyo
  central (**+351,5 kN·m**, *sagging* → alivia el hogging de cálculo allí). Es un teorema: el
  secundario procede de una única reacción redundante, luego es lineal.
- **Trazado parabólico por vano = carga equivalente uniforme (cómo se modela).** Cada vano se
  describe con una parábola de **drape a** sobre la cuerda de excentricidades de apoyo:
  e(x) = cuerda(x) + 4·a·(s/L)(1−s/L). La curvatura es constante **e'' = −8a/L²** → la carga
  equivalente es **uniforme** w_p = −P·e'' = 8·P·a/L² (hacia arriba). El kink del tendón sobre
  el apoyo central (reverse curvature) produce una **fuerza de desvío** que se **reacciona en
  el apoyo** (no flecta la viga); las anclas en e = 0 en los extremos no dan momento de
  anclaje. Por eso el FEM solo necesita el **w_p uniforme por vano**.
- **FEM vs método de las fuerzas (validación cruzada propia del caso).** Para la continua
  simétrica de 2 vanos, M_p,tot en el apoyo central = w_p·L²/8 (resultado clásico); el método
  de las fuerzas (1 incógnita = reacción del apoyo central) da el mismo M_sec que el FEM
  (**Δ = 0,000 %**). Además se comprueba la **identidad M_p,tot = M₁ + M_sec** (error
  5,8·10⁻¹¹). Es el análogo, en hiperestático, del contraste cargas-equivalentes vs
  fuerza+excentricidad de los casos 12/13.
- **Línea de presiones y concordancia.** e_p(x) = M_p,tot/P = e(x) + M_sec/P. Si M_sec = 0 el
  tendón es **concordante** (la línea de presiones coincide con el tendón). Aquí M_sec ≠ 0 →
  tendón **NO concordante**: la línea de presiones se separa del tendón **+0,15 m** (= M_sec/P)
  en el apoyo central. La línea de presiones es la posición "efectiva" del pretensado en la
  estructura real (incluye el secundario).
- **ELU con el momento secundario como ACCIÓN (γ_P = 1,0, §5.10.8) — no contar dos veces el
  primario.** El secundario es un **efecto hiperestático de reacción**, así que entra en el
  lado de las **acciones**: M_Ed = γ_G·M_g + γ_Q·M_q + **1,0·M_sec**. El **primario NO** se
  suma como acción: va implícito en la **resistencia por fibras** (el acero activo a f_pd ya
  representa la fuerza de pretensado). En el apoyo central el secundario (+sagging) **ALIVIA**
  el hogging: M_Ed = −2.334 + 1,0·(+352) = **−1.983 kN·m** (M_Rd = 2.509, u = 0,79); en el
  vano se **suma** al sagging. Lección: el secundario se trata como acción; doblar el primario
  sería un error de seguridad.
- **M_Rd por fibras genérico sagging/hogging.** La rutina del caso 12 (tendón a d_p = cdg+e,
  *sagging*) se generaliza al **hogging** del apoyo: con compresión abajo, d_p = h − (cdg+e),
  y el tendón sobre el apoyo (e = −0,30, a 0,35 m del borde superior) queda del **lado
  traccionado** → contribuye a M_Rd. x/d ≈ 0,29 (dúctil) en ambas secciones.
- **Refinamiento de las excentricidades para que el balance equilibre la permanente.** El
  enunciado sugería e ≈ ±0,50 m; con esos valores el drape sería 0,75 m y w_p = 8·P·a/L² =
  35 kN/m **sobre-equilibraría** la permanente (21,25). Se **refinó a e_vano = +0,30 /
  e_apoyo = −0,30** (drape 0,45) → w_p = 21,09 kN/m equilibra la permanente (residual
  −0,74 %), con **14×Y1860S7** y σp,∞ = 0,60·fpk como pedía el enunciado. Lección: el balance
  fija el drape (a = w·L²/(8P)); las excentricidades se ajustan a ese drape, no al revés.
- **Redistribución §5.5 disponible pero no necesaria.** Con x/d = 0,296 (fck ≤ 50) el
  coeficiente mínimo admisible es δ = 0,44 + 1,25·x/d = 0,81 (hasta 19 % de reducción del
  hogging del apoyo). Como u = 0,79 < 1 ya cumple, no se aplica; se reporta la capacidad.
- **Sandbox disponible: ejecución completa en el hilo principal (INC-08).** El hilo dispuso de
  `mcp__workspace__bash`: generado `caso-14.ifc` (2 `IfcStructuralCurveMember` + 3
  `IfcStructuralPointConnection`+BC + `Pset_Estructurando_Pretensado` por vano, validado),
  corrido `run_all_pretensado_continua.py` (FEM continua + secundarios + verificación), 8
  diagramas + memoria Word, y **reempaquetado `.plugin` v0.20.0 acumulativo** (preservando
  `sismico/` + `pretensado/` 12+13 + `puente_analitico/` R1–R4), con re-verificación de la
  versión instalada antes (0.19.0) y después (0.20.0) de copiar.
- **Coherencia física.** Esfuerzos externos del FEM = chequeo de mano EXACTO (apoyo ELU
  −2.334, vano ELU +1.313, cuasiperm −1.242, rara −1.662). Balance residual −0,74 %; M_sec
  apoyo +351,5 (lineal R²=1, nula en extremos), FEM vs fuerzas Δ=0,000 %; tensiones por fibra
  con M_sec dentro de límites (apoyo rara top +0,71 < fctm=3,5; resto comprimido); ELU apoyo
  0,79 / vano 0,64; flecha 1,02 mm ≪ L/250. **Aprov. máx 0,79 (≤ 1).**

### Caso R5 — IFC físico "real-sucio" de un exportador: endurecimiento del puente físico→analítico (`puente_analitico`) · CIERRE de INC-07 y de la Dirección 2
- **Limpiar antes de calcular: el puente convierte un export "sucio" en el modelo
  analítico limpio (lección clave del caso y de la serie R).** R1–R4 partieron de IFC
  físicos LIMPIOS (ejes baricéntricos centrados que se cortan en los extremos, fusión por
  tolerancia trivial de 1 mm, sin elementos sobrantes, metros). Un entregable BIM REAL es
  "sucio". Verificado: el parser crudo del puente sobre `caso-R5.ifc` leería **8 nudos / 4
  barras** (coordenadas en mm sin escalar, ejes con offset sin recuperar, la viga suelta
  incluida); tras la limpieza entrega **4 nudos / 3 barras** = el modelo de R1. El reto es
  de LECTURA/IDEALIZACIÓN, no de solver: `run_all_real.py` y `barras` se reutilizan SIN
  CAMBIOS; toda la robustez vive en `puente.py` (+ alias en `perfiles_db`).
- **Recuperación del eje analítico por CardinalPoint (offset eje físico↔analítico).** El
  sólido se barre desde un `CardinalPoint` ≠ 5 del `IfcMaterialProfileSetUsage` (esquina o
  cara del perfil). `_axis_recovery()` lee el cardinal point y, con (b,h) del perfil,
  desplaza el eje de referencia al **centroide** sobre los ejes locales del placement
  (`get_local_placement`), guardando la **excentricidad** por barra. Verificado: C1/C2
  **0,141 m** (CP 1 y 3, esquina inferior), B1 **0,165 m** (CP 8, cara superior del ala).
  `CardinalPoint=5`/ausente → offset nulo → R1–R4 idénticos.
- **Grafo de nudos con tolerancia parametrizable, bridging y troceo T/X con offset.** La
  tolerancia de snap pasa de fija (1 mm) a **parametrizable** (`Pset_Estructurando_Puente.
  Snap_tol_m`; aquí 60 mm; por defecto = TOL = R1–R4). Fusiona extremos próximos
  registrando los **huecos/solapes puenteados** (2 saltos de 0,05 m en R5), y **trocea un
  pasante** cuando el extremo de otra barra cae cerca (no exactamente) de su interior,
  **proyectando** el punto de corte sobre la directriz del pasante (margen paramétrico
  relativo a L, no absoluto — antes `t<=tol` mezclaba distancia y fracción). El pórtico no
  tiene cruces T/X; la capacidad se validó en micro-test (pasante 0–6 m + montante con
  50 mm de offset → 2 segmentos + montante enganchado en el nudo proyectado).
- **Snap con representante "primero añadido" + columnas antes que vigas = reproduce la luz
  exacta.** Como `_Nodos.add` conserva el primer punto del clúster y las columnas se
  procesan antes que las vigas, los extremos del dintel se fusionan a las cabezas de pilar
  → **luz del dintel exactamente 6,0 m** ⇒ reacción **93,60 kN/apoyo EXACTA** e IPE 330
  44,8 %. Los pilares quedan en 4,04 m (solape de 40 mm recuperado) → HEB 200 31,8 %
  (vs 32,0 %): pequeña diferencia atribuible a la idealización del offset, **aceptada y
  documentada** como en R1–R4.
- **Filtrado de no-estructurales y de componentes no conectadas, solo en real-sucio.** Se
  admiten solo las clases estructurales (`IfcColumn/IfcBeam/IfcMember/IfcSlab/IfcWall/
  IfcFooting`); `IfcRailing`/`IfcBuildingElementProxy` se avisan y descartan.
  `_filtrar_desconectadas()` (union-find) elimina las componentes sin nudo apoyado (la viga
  suelta). **Clave de la no-regresión:** el filtrado por conectividad y por clase **solo se
  activa si `snap_tol > TOL`** (IFC real-sucio); un IFC limpio (R4, con subsistemas
  legítimamente separados) NO se filtra → R4 sigue dando 8 nudos / 5 barras idénticos.
- **Alias de perfiles del exportador y unidades.** `perfiles_db._norm_name` mapea la
  Euronorm `HE 200 B`/`HE200B` → `HEB 200`; `props_from_profile_def` devuelve el **nombre
  normalizado** de catálogo, para que el clasificador reconozca el perfil en I (si no, lo
  marcaba "heterogéneo"). `_length_scale` respeta el `IfcUnitAssignment`: MILLIMETRE →
  escala 1e-3 en coordenadas, longitudes y dimensiones de sección; METRE → 1.0 → R1–R4
  intactos.
- **Validación = reproducir el caso limpio a pesar de la suciedad.** Del IFC real-sucio
  (mm, cardinal point, huecos/solapes, no-estructurales, alias) el modelo derivado da
  reacción **93,60 kN/apoyo**, horizontales ±12,01 kN balanceadas, **HEB 200 31,8 %**,
  **IPE 330 44,8 %**, validación cruzada PyNite vs anaStruct **CONFORME**, equilibrio ~0 %.
  Regresión: R1 (32,0/44,6 %) y R4 (modelo neutro idéntico) sin cambio, verificados desde
  el `.plugin` empaquetado. **Cierra INC-07 y la serie R / Dirección 2.**
- **Coordinación de versiones (carrera resuelta).** Al empezar, el `.plugin` instalado era
  v0.19.0; durante el hilo el caso 14 (pretensado continua) lo reescribió a **v0.20.0**
  (detectado al re-verificar). El reempaquetado de R5 se hizo **acumulativo partiendo de
  ese v0.20.0** (preservando `sismico/` + `pretensado/` 12+13+14 + `clasificador.py`/
  `run_all_edificio.py` + `puente_analitico/` R1–R4 y añadiendo encima la robustez de R5) →
  R5 = **v0.21.0**, con re-verificación de la versión instalada antes (0.20.0) y después
  (0.21.0) de copiar. El `puente.py`/`perfiles_db.py` del v0.20.0 eran idénticos al
  v0.19.0 (el caso 14 no los tocó), de modo que el overlay no revirtió nada.

### Caso 15 — Núcleo de pantallas acopladas + sísmico integrado en el edificio (`sismico/nucleo` + `edificio_sismo`, EC8) · PT 1.5 (Ola 1), cierre de la estabilización lateral de edificación

- **Del stick 1 GdL al diafragma rígido 3 GdL/planta (lección clave del caso).** La pantalla
  aislada del caso 11 (un voladizo, 1 GdL/planta) se generaliza al **núcleo** ensamblando la
  rigidez de cada pantalla en un modelo de **diafragma rígido con 3 GdL por planta (ux, uy, θz)**.
  Cada pantalla aporta su rigidez de voladizo (reutiliza `ec8.stick_lateral_stiffness`, flexión
  Euler-Bernoulli + cortante Timoshenko) en su **dirección** (X/Y por la normal del plano) y su
  **posición en planta** vía la matriz de compatibilidad `T` (lever `r = -(yc-CMy)·ex + (xc-CMx)·ey`).
  De ahí salen el **centro de rigidez CR** y, frente al **centro de masa CM**, la **excentricidad
  estática e0**. `nucleo.py` (NUEVO) + `solver_nucleo.py` (parser que lee varias
  `IfcStructuralSurfaceMember` verticales y deriva Lw/tw/posición/dirección + masas de diafragma +
  Psets EC8/núcleo, extendiendo el modelo neutro con claves nuevas `pantallas[]`/`dinteles`/
  `diafragma`, contrato C1, sin romper las existentes).
- **El acoplamiento ENTRA en la rigidez global (no son voladizos independientes).** Modelar los
  machones de alma como dos voladizos sueltos sobrestima T1 y vuelve el primer modo torsional.
  Se condensan en **UN elemento Y** con la rigidez del par acoplado: plano-pórtico 2D (Y-Z) de los
  dos machones con **brazos rígidos** (mitad del machón) + **dintel con flexibilidad de cortante**
  (viga profunda, `Ib_eff = Ib/(1+12·E·Ib/(G·Avb·ln²))`, aquí ≈0,58·Ib) y **condensación estática**
  a las traslaciones Y de planta (diafragma: `c1_j.Y = c2_j.Y`). Con ello T1 baja a la meseta y la
  respuesta es traslación-dominante.
- **Torsión: sección abierta en U ⇒ CR≠CM; reparto directo + torsional + accidental.** El cortante
  de planta se reparte resolviendo el sistema 3 GdL: la **torsión natural** (CR≠CM) sale sola, y la
  **torsión accidental** se añade como par `±F·e_acc` con `e_acc = 0,05·L` (EC8 §4.3.2), tomando la
  **envolvente** de signos. Bajo sismo Y los machones llevan el cortante directo y las **alas** toman
  el **par torsional** (±, suma nula); bajo sismo X las alas llevan el directo y los machones ~0.
  Suma de cortantes por dirección = cortante basal (**error 0,000 %**).
- **El núcleo en U es comparativamente flexible a torsión (lección física).** El brazo torsional lo
  dan solo las alas (los machones, en x=CR, no aportan a J_R), así que el **radio torsional ≈ semiancho
  del núcleo** limita la regularidad: para que `r > l_s` (radio de giro de la masa) hay que mantener
  el **edificio compacto** (núcleo casi-pleno, torre estabilizada por el núcleo). Criterio adoptado:
  plano 8×8 m, e0x≈0,6 m (modesto y realista). Se documenta que un caso real exigiría verificar la
  regularidad torsional (EC8 §5.2.2.1) o añadir elementos perimetrales/cajón cerrado.
- **Vigas de acoplamiento DCM (§5.5.3.5).** Del mismo plano-pórtico se obtiene el **cortante del
  dintel por planta** (extremo transversal) → **axil de acoplamiento** `N(z)=Σ V_dintel` y **grado de
  acoplamiento** `DoC = N_base·ℓ/M_vuelco` (aquí **0,72**, acoplamiento fuerte: el par axil resiste el
  72 % del vuelco, la flexión de los machones solo el 28 %). Dintel `ln/h = 1,4/0,7 = 2,0 < 3` ⇒
  **armadura DIAGONAL** (`V_Ed = 2·As_d·fyd·senα`); diseño por capacidad con `γ_Rd` [confirmar AN].
- **Tracción neta en el machón a barlovento (efecto del acoplamiento).** El axil de acoplamiento
  resta del gravitatorio en un machón (aquí 667−1441 = **−775 kN, tracción neta**): la **armadura
  vertical de borde** se dimensiona para esa tracción (el chequeo `elemento_borde` lo captura con el
  N real), mientras el **N-M de la sección** se comprueba con el axil gravitatorio (lado seguro,
  evitando extrapolar la frontera N-M a tracción).
- **Integración en el orquestador de edificio (objetivo 2).** `edificio_sismo.py` (NUEVO) **deriva las
  masas de planta** del modelo (explícitas del IFC o `G + ψ2·Q` por planta), monta el modelo lateral
  (núcleo), **distribuye el cortante sísmico** y **verifica derivas globales**, con **combinación
  sísmica EC0 §6.4.3.4** (`Ed = E + ΣGk + Σψ2·Qk`, γ=1,0). `run_all_edificio.py` añade una **etapa
  sísmica** `[E]` (auto si hay `Pset_Estructurando_Sismo`, o `--sismo`) que la ejecuta en subproceso
  aislado y la **consolida** (`_caso_sismico_EC8`) sin tocar el flujo gravitatorio.
- **Reutilización limpia.** `ec8.py` y `verificacion_sismo.py` (cortante alma, elemento de borde,
  N-M, deriva) del caso 11 se reutilizan **sin tocarlos**; `verificacion_nucleo.py` añade solo la
  **viga de acoplamiento** y el bucle por pantalla. Regresión del caso 11 verificada idéntica
  (T1=0,408 s, Fb=929 kN, borde 0,97). `.plugin` v0.22.0 acumulativo sobre v0.21.0.
- **Coherencia física.** Sd(meseta)=ag·S·2,5/q=0,1597 g (q=3,6); **T1x=0,305 / T1y=0,390 s** (meseta);
  ΣM_eff=100 % en X e Y; **e0x=0,60 m**; Fb_X=Fb_Y=543 kN (laterales, equilibrio 0,000 %); modal SRSS
  454/368 kN (contraste); **DoC=0,72**; V_dintel,máx=346 kN; deriva máx 0,225 %·h. Aprovechamientos:
  alas 0,62, machón comprimido 0,72, machón traccionado 0,33, dintel 0,22, deriva 0,15 → **aprov. máx
  0,72, CUMPLE**. Picos como envolvente. Predimensionado.

### PT 1.6 — Verificación de cierre de la Ola 1 (auditoría del núcleo + edificación)
- **El empaquetado acumulativo puede truncar módulos que ni se tocan (lección clave del PT).** El
  `.plugin` **v0.22.0** quedó con **8 módulos preexistentes truncados** a media instrucción
  (`puente.py` perdió 27 de 42 KB; `cimentaciones/{solver_raft,solver_zapata,verificacion_raft,
  run_all_raft,plots_raft}`; `barras/{ifc_to_model,perfiles_db}`), pese a que el caso 15 solo añadía
  `sismico/*`. Manifestación del *hazard* INC-04 en el **paso de empaquetado**, no de edición.
  Resultado: v0.22.0 **no instala limpio** (5 SyntaxError al importar). Corregido restaurando los 8
  desde v0.21.0 (cada uno **prefijo exacto** del completo → truncado puro) → **v0.22.1** (126 `.py`,
  0 errores). Los resultados de casos no se vieron afectados (corren desde copias completas).
- **`ast.parse` no detecta todo el truncado.** 3 de los 8 archivos **parseaban** (acababan en una
  expresión válida por azar, p. ej. `qz`). El control fiable combina: `ast.parse` + **falta de salto
  de línea final** + **contraste de tamaño contra la versión previa** + recuento de módulos.
  Institucionalizar como **checklist de empaquetado** post-zip (hueco H6).
- **Para markdown, la fuente de verdad son las herramientas de fichero, no el shell.** La
  verificación independiente reportó un falso "C2 incompleto" porque el **shell del sandbox leyó una
  copia truncada** de `criterios-despacho.md` (2.153 B, 4 secciones) cuando el archivo real tiene las
  5. Confirma la regla de método del proyecto (no editar/leer markdown crítico por shell).
- **Coherencia contrato↔implementación (resultado).** C1 ⚠️ (esquema coincide con los parsers
  intactos y el caso 15 añade claves nuevas; matices: colocación de `cargas` 1D-raíz vs
  2D-`superficies[]`, `material` singular del modelo sísmico, refs de ola desfasadas, parsers
  truncados en el paquete), C2 ✅, C3 ✅ (alinear `memoria-calculo` al esqueleto de 7 apartados), C4 ✅
  (EC0/EC1). Edificación E2E: caso 10 CUMPLE 4/4 (máx 94,4 %), caso 15 CUMPLE (equilibrio 0,0 % X/Y,
  máx 0,72).
- **Dry-run de "enchufe" (instalaciones).** C2 y C3 enchufan ya sin tocar el núcleo; C1 y C4 exigen
  trabajo de núcleo previo = **arranque de la Ola 4**: extraer **grafo de red + utilidades IFC**
  (`_psets`, factor de unidades, construcción de grafo) hoy embebidas en `puente.py`/estructuras
  (H1); ampliar `iso19650-openbim` a **MEP** (H2); definir **bases de demanda** para disciplinas no
  estructurales (H3). Entregable: `Nucleo-transversal/Verificacion-Ola1.md`. **Ola 1 cerrada.**

### PT 4.1 — Extracción del grafo de red + utilidades IFC al núcleo (Ola 4, hueco H1; decisión nº4) · v0.23.0
- **Refactor "extraer sin cambiar comportamiento": la regresión byte a byte es la red de
  seguridad (lección clave del PT).** El grafo de nudos endurecido en R5 y las utilidades IFC
  (`_psets`, factor de unidades, álgebra 4×4) vivían embebidos en `puente.py` y duplicados en los
  parsers. Se extrajeron a un **núcleo transversal** (`scripts/nucleo/ifc_utils.py` + `grafo_red.py`)
  y `puente.py` quedó como **adaptador fino** que los delega (921→833 ln), sin tocar el solver ni la
  verificación. **Patrón:** fijar primero la **golden** (salida de v0.22.1 de R1–R5), mover las piezas
  como **delegaciones** que preservan el cómputo exacto (mismo orden de alta de nudos `N%d`, mismo
  troceo), y exigir `diff` byte a byte. Resultado: **R1–R5 idénticos** y casos 1/5/7/10 **CUMPLEN**.
- **La referencia de regresión es la SALIDA de la versión previa, no el JSON comprometido.** Los
  `modelo_neutro.json` versionados de R1–R4 son **anteriores** al endurecimiento de R5 (les faltan
  `limpieza`/`factor_escala_ifc`/`orientacion`…); solo R5 coincide con v0.22.1. Por eso la golden se
  **regeneró** corriendo el `puente.py` de v0.22.1 sobre cada `caso-RX.ifc`; comparar contra los JSON
  históricos habría dado falsos positivos de "diferencia".
- **Frontera núcleo/disciplina: el núcleo da topología, la disciplina calcula.** Entra al núcleo lo
  común (lectura IFC genérica + grafo nodos+tramos: snap, troceo T/X, union-find); **se queda** en la
  disciplina el solver (FEM/hidráulico/eléctrico/térmico), la recuperación de eje/sección/material y la
  semántica estructural (pilar/viga, cargas de hipótesis, cadenas muro↔zapata). El `union-find` se hizo
  **genérico** vía predicado `es_ancla` (estructuras = nudo apoyado; MEP = nudo fuente).
- **Gancho H2 dejado listo sin construir MEP.** `grafo_red.construir_grafo(segmentos, tol)` acepta
  segmentos genéricos `(p0, p1, payload)`: un futuro `ifc_to_model_mep.py` lo alimentará desde
  `IfcDistributionPort`/`IfcRelConnectsPorts` **sin tocar el núcleo**. Este PT **no** implementa el
  dominio MEP (H2) ni el solver hidráulico.
- **Decisión abierta nº4 resuelta (dónde vive el motor hidráulico de red).** El grafo+utilidades se
  **incuban** en `scripts/nucleo/` del plugin de estructuras (única ubicación empaquetable y
  verificable por la puerta de calidad en este hilo), con **API estable y agnóstica al solver**, para
  **promoverse/espejarse** a módulo compartido cuando nazca el plugin `instalaciones` (Ola 4). El
  motor **hidráulico** (Darcy/Manning) será el **solver** que esa disciplina añada sobre este grafo.
- **Verificación doble (una independiente a ciegas) + puerta de empaquetado.** Micro-test del núcleo
  (snap/troceo/union-find/`construir_grafo`), regresión byte a byte y `ast.parse` (129 `.py`, 0
  errores) confirmados por el hilo y por una auditoría independiente que **re-derivó la referencia**
  desde v0.22.1. Empaquetado acumulativo y `verificar_empaquetado.py` (INC-09) como puerta obligatoria.
- **La puerta de empaquetado necesita distinguir refactor de truncado (mejora de proceso).** Su
  heurística anti-truncado marca como sospechoso cualquier `.py` que **encoja** vs la referencia; un
  refactor que extrae código a un módulo legítimamente encoge (puente −3411 B, parsers −299/−295 B).
  Se añadió la opción **`--allow-shrink`** (allowlist NOMINAL de ficheros con encogimiento auditado):
  solo esos, nombrados uno a uno, se aceptan; el resto sigue a **tolerancia cero** (no se usa el
  `--shrink-tol` global, que enmascararía truncados en los demás módulos). Comando de la puerta:
  `verificar_empaquetado.py motor-...-v0.23.0.plugin --ref motor-...-v0.22.1.plugin --allow-shrink
  scripts/puente_analitico/puente.py,scripts/barras/ifc_to_model.py,scripts/laminas/ifc_to_model_3d.py`
  → **APTO (129 .py, 0 errores), exit 0.**
- **Hazard de mount confirmado también para `.py` editados con herramientas de fichero.** Tras editar
  `verificar_empaquetado.py` con Edit, el **shell del sandbox sirvió una copia truncada** (207 ln vs
  246 reales en disco). La herramienta de fichero (Read) mostraba el archivo íntegro: la fuente de
  verdad es el fichero, no el shell. Solución: ejecutar la lógica desde una copia escrita en `/tmp`.

### PT 4.2 — Apertura del dominio IFC MEP: parser red + generador + validación (Ola 4, hueco H2) · `iso19650-openbim` v0.4.0
- **El núcleo H1 cumplió su promesa: una disciplina nueva enchufó SIN tocarlo (lección clave del PT).**
  El parser MEP `ifc_to_model_mep.py` consume `ifc_utils` (psets/length_scale/pset_value) y
  `grafo_red.construir_grafo`/`filtrar_componentes_desconectadas` exactamente como `puente.py`, vía
  `sys.path` a `../nucleo`. Los `IfcFlowSegment` aportan los **segmentos** `{p0,p1,payload}`; los
  `IfcDistributionPort`/`IfcRelConnectsPorts`, los **nudos** (puertos conectados → coord compartida →
  el snap del núcleo los fusiona). El `union-find` genérico se reusó con `es_ancla`=nudo **fuente**.
  El modelo neutro de red es **hermano** del estructural: claves nuevas (`sistema`/`tramos`/
  `terminales`/`fuentes`) sin redefinir las existentes; bloque `unidades` SI declarado.
- **Frontera respetada: el parser da topología+datos, NO calcula.** Ni Darcy/Manning ni eléctrico ni
  térmico (eso es el solver de `instalaciones`). La validación de red es topológica (continuidad
  conexa desde fuente, terminales conectados, sin huérfanas, SI), análoga al arnés de equilibrio.
- **Empaquetado: el plugin natural (`iso19650-openbim`, capa IFC transversal) estaba instalado en
  SOLO-LECTURA y sin fuente en la carpeta → se reconstruyó como fuente editable** (copia de
  `.remote-plugins/...` a la carpeta del proyecto) y se reempaquetó a **v0.4.0**. El cambio no se
  activa en vivo (la skill cacheada es read-only): se entrega el `.plugin` versionado a reinstalar,
  igual que con el motor. **No se tocó `motor-calculo-estructural`.**
- **Núcleo ESPEJADO al plugin (avance de la decisión nº4).** Como `iso19650-openbim` no puede importar
  el núcleo del motor en runtime, se copió `ifc_utils.py`+`grafo_red.py` (verbatim, micro-test incluido)
  a `iso19650-openbim/scripts/nucleo/`. El **canónico sigue en el motor**; este es el primer espejo del
  módulo compartido previsto cuando nazca `instalaciones`. Pendiente: unificar a un módulo único.
- **Unidades del banco de pruebas (lección de generador, análoga a length_scale del puente).**
  `ifcopenshell` `unit.assign_unit` por defecto declara **MILÍMETROS** → coords escritas como metros se
  leían a 1/1000 (T1 de 10 m salía 0,01 m). El parser era correcto (respeta `length_scale`); el fallo
  estaba en el generador. Fijar la unidad SI explícita: `unit.add_si_unit(LENGTHUNIT)` sin prefijo +
  `assign_unit(units=[...])`. El parser es **agnóstico al esquema**: IFC4 PCI=`FIREPROTECTION`,
  IFC4X3=`FIRESUPPRESSION`; emite el string tal cual (en IFC4 `FIRESUPPRESSION` no es enum válido).
- **Gancho H3 dejado listo sin construir demanda.** Clave `demanda` prevista por terminal y por
  sistema en el modelo neutro; el parser no calcula caudales/potencias/ocupación (eso es H3).
- **Hazard de mount AGRAVADO en ficheros recién editados (refuerza INC-04/INC-10).** Tras editar un
  `.py` con la herramienta de fichero, el shell del sandbox sirvió **copias truncadas/corruptas de
  forma persistente** (no se arregló esperando ~40 s); `cp`/`shutil.copyfile` arrastraban la corrupción.
  Solución aplicada: **reconstruir el fichero en `/tmp` por heredoc** (contenido autoritativo) y
  **empaquetar desde `/tmp`** (no desde el mount), con `ast.parse`+salto de línea por fichero antes de
  zipear y la puerta de calidad como red final. La copia read-only del plugin además exigió
  **`chmod -R u+w`** (los Edit fallaban con EPERM al renombrar el `.tmp`).
- **Clave estable de entidad IFC: `entity.id()` (STEP), NUNCA `id(entity)` de Python (bug de
  no-determinismo cazado y corregido).** El union-find de puertos conectados (`IfcRelConnectsPorts`)
  agrupaba por `id(puerto)` de Python. ifcopenshell devuelve un **wrapper nuevo en cada acceso**, así
  que el `id()` obtenido vía `RelConnectsPorts` no coincidía con el obtenido vía `IsNestedBy` y, peor,
  **colisionaba aleatoriamente por reuso de direcciones de memoria** → el grafo salía con 3, 4 o 5
  tramos según la ejecución (terminales mapeados al nudo equivocado). El núcleo (`construir_grafo`) era
  **determinista** (probado 8/8 idéntico); el fallo era del parser. Corregido usando `puerto.id()`
  (id de línea STEP, estable entre accesos). Tras el fix: 8/8 ejecuciones → (5 nodos, 4 tramos, 3
  terminales, 1 fuente). Lección general: cualquier clave/dedup de entidades IFC debe usar `.id()`.
- **Verificación: micro-test de red (`test_red_mep.py`) + caso e2e (`caso-MEP-01-red-pci`).** Genera→
  parsea→valida: 5 nodos / 4 tramos / 3 BIE / 1 fuente, cobertura 100 %, sin huérfanas → **CUMPLE**.
  `ast.parse` de los 11 `.py` del plugin (0 errores); puerta `verificar_empaquetado.py` v0.4.0 --ref
  v0.3.0.

### PT 4.3 — Nace `instalaciones`: solver hidráulico de red + bases de demanda (Ola 4, hueco H3) · `instalaciones` v0.1.0
- **El patrón de agente de disciplina se replicó limpio (lección clave del PT).** Nuevo plugin
  `instalaciones` con agente `ingeniero-de-instalaciones` (clasificar sistema desde el IFC MEP → enrutar
  al subagente/solver → orquestar IFC→neutro[PT 4.2]→demanda→solver→verificación→memoria → registrar) y
  subagente `proyectista-pci`, igual que `ingeniero-estructurista`. La disciplina aporta SOLO lo suyo
  (normativa PCI + solver hidráulico + demanda); el núcleo y la lectura IFC MEP se reutilizan sin tocar.
- **Frontera C1↔C4↔cálculo confirmada y operativa.** La lectura IFC MEP (parser/validación) se queda en
  `iso19650-openbim` (capa transversal); la **demanda** (`pci/bases_demanda.py`, slot C4) y el **cálculo**
  (`red/solver_red.py` + `red/verificacion_red.py`) viven en `instalaciones`, consumiendo el **modelo
  neutro de red** (JSON). El solver NO lee IFC. El núcleo da topología, el solver calcula.
- **Nace el motor hidráulico de red (capacidad transversal).** `solver_red.py`: reparto de caudales por
  continuidad en **árbol** (raíz=fuente, demanda acumulada del subárbol), pérdida de carga
  **Darcy-Weisbach** (fricción **Swamee-Jain**, aprox. explícita de Colebrook-White; laminar 64/Re),
  propagación de presiones desde la fuente **con cota**, presión requerida vs disponible y comprobación
  de caudal/presión en terminales. Reutiliza `grafo_red` (núcleo) para orientar el árbol. Mismo grafo
  conceptual que el estructural, distinto solver (lo previsto en la hoja de ruta §4).
- **Bases de demanda = el slot C4 no estructural (H3 cerrado).** `bases_demanda.py` rellena la clave
  `demanda` (terminal+sistema) con simultaneidad (2 BIE más desfavorables), caudal y presión dinámica de
  BIE según **RIPCI/UNE-EN 671/UNE 23500/DB-SI** `[confirmar AN]`. **El dato del proyecto (IFC) prevalece**
  sobre el valor por defecto (`fuente_dato`). Es a instalaciones lo que EC0/EC1 a estructuras.
- **Arnés de verificación análogo al equilibrio estructural.** `verificacion_red.py`: balance de caudales
  (cabecera = demanda; residuo en nudos de unión) **≈0 %**, presiones admisibles, terminal gobernante.
  Caso e2e `caso-PCI-01-bie-presion`: IFC→parser MEP(PT 4.2)→demanda→solver→verificación **CUMPLE**,
  balance **0,0000 %**, fuente 600 vs **352,9 kPa requerida** (BIE-2 gobierna), v_pico 0,995 m/s. Micro-test
  `test_solver_red.py` (tramo recto vs analítico, balance en la te, fricción) → 0 fallos.
- **Decisión nº4 cerrada: patrón de ESPEJO + puerta de integridad (no módulo único).** El aislamiento de
  runtime entre plugins impide un módulo importable compartido; se adopta el **espejo byte a byte** del
  núcleo (canónico en el motor → `iso19650-openbim` → `instalaciones`) y se añade la puerta
  `Nucleo-transversal/verificar_espejo_nucleo.py` (md5; FALLA si un espejo diverge/falta/sobra). Probada
  **ESPEJOS IDÉNTICOS** en los 3 (mismo md5). Solo se empaqueta `instalaciones` (motor e iso19650 intactos).
- **Hazard de mount confirmado de nuevo (refuerza INC-04/INC-10).** El shell sirvió una copia **truncada**
  (200 ln/9201 B) de `verificar_empaquetado.py` —fichero estable, no editado este hilo— mientras la
  herramienta de fichero lo mostraba íntegro (252 ln). Solución: **reconstruir la puerta en `/tmp` por
  heredoc** y ejecutarla allí. Empaquetado desde `/tmp`, copia con `cat >`, nombre versionado.
- **Puerta de calidad: APTO (exit 0).** `verificar_empaquetado.py instalaciones-v0.1.0.plugin` (8 `.py`,
  0 sintaxis, 0 truncados, plugin.json válido, `description` 478/500, sin artefactos); sin `--ref` (plugin
  nuevo). + puerta de espejo del núcleo APTA. Memoria md + **docx** (docx-js local, validado).

### PT 4.4 — Motor de red con MALLAS + rociadores UNE-EN 12845 + write-back al IFC (Ola 4) · `instalaciones` v0.2.0 / `iso19650-openbim` v0.4.1
- **Solver de mallas por Hardy-Cross (decisión adoptada vs Newton-Raphson nodal).** Para redes PCI
  pequeñas se eligió **Hardy-Cross** (clásico, transparente, **stdlib pura**, comprobable a mano para la
  memoria que firma el ICCP, y encaja con el arnés). La **semilla** es la solución de árbol existente
  (continuidad por construcción) y la base de lazos son los **ciclos fundamentales** = cuerdas del árbol
  generador (`m − n + componentes`). Corrección por lazo `ΔQ = −Σh_L/Σ(2|h_L|/|Q|)` (n=2, fricción
  reevaluada). **Clave de no-regresión:** con 0 lazos no hay correcciones → resultado **byte a byte** igual
  al del árbol (PCI-01 intacto: fuente 600/352,9 kPa). Verificado: malla simétrica de 1 lazo reparte
  **50/50 exacto**; malla de 2 lazos cierra ambos lazos (~1e-5 kPa) con balance nodal 0,0 %.
- **Balance nodal RIGUROSO requiere el caudal CON SIGNO.** El arnés v0.1.0 estimaba el balance por una
  heurística de árbol ("el mayor = suma de los demás"), inválida en malla. Se añadió al solver el **caudal
  con signo** por tramo (`caudal_signed_l_s`, `sentido`) y el arnés calcula `net_in(nudo)` exacto: 0 en
  unión, demanda en terminal, −total en fuente. Lección: para verificar mallas hay que **exportar la
  orientación del flujo**, no solo la magnitud.
- **Rociadores = densidad × área de operación (UNE-EN 12845), distinto de la simultaneidad fija de BIE.**
  `bases_demanda` gana una rama de rociadores (tabla LH/OH1-4/HHP) y un **dispatcher** `aplicar_demanda`
  que enruta BIE vs rociadores por tipo de terminal o `sistema.clase_riesgo`. n=⌈A_op/A_cob⌉ del área más
  desfavorable; p_min de boquilla por **Q=K·√p**; Q_dis=densidad·A_op. La red de rociadores es típicamente
  **mallada** → ejercita el solver de mallas en el mismo caso.
- **Write-back: mecánica (transversal) vs semántica (disciplina) — opción (a).** La **escritura IFC** vive
  en `iso19650-openbim` (`ifc-create:escribir_psets_resultado.py`, escritor genérico por mapping
  Name/GlobalId); la **semántica** (`Pset_Estructurando_ResultadoRed`) en `instalaciones`
  (`red/resultado_ifc.py`, stdlib). El **aislamiento de runtime** impide que `instalaciones` importe el
  escritor → la **orquestación la hace el agente** (corre el solver, construye el mapping, invoca la skill
  `ifc-create`, valida con `ifc-validate`). `ifc-validate` (`checks-mep`) reconoce el Pset de resultado.
- **Frontera C1↔disciplina respetada al reempaquetar.** Solo se tocan los dos plugins que cambian:
  `instalaciones` (semántica + solver + demanda) → **v0.2.0** e `iso19650-openbim` (mecánica + generador
  mallado de prueba) → **v0.4.1**. El núcleo espejado queda **intacto** en ambos (md5 idéntico al canónico
  motor v0.23.0; puerta de espejo APTA).
- **Hazard de mount confirmado de nuevo y SISTEMATIZADO (refuerza INC-04/INC-10).** El shell sirve copias
  **truncadas/stale** de ficheros **pre-existentes recién editados** (`solver_red.py`, `plugin.json`,
  `CHANGELOG.md`, agentes, `bases_demanda.py`, `verificar_empaquetado.py`), pero **los ficheros NUEVOS se
  leen íntegros**. Patrón aplicado: editar/crear vía herramienta de fichero (verdad de la fuente), y para
  **ejecutar/empaquetar reconstruir cada fichero cambiado en `/tmp` por heredoc** (ast.parse + salto final)
  y **construir el ZIP desde `/tmp`** (los nuevos se copian del mount). Las puertas se ejecutan desde `/tmp`.
- **Puertas de calidad: APTO + ESPEJOS IDÉNTICOS.** `verificar_empaquetado.py` APTO para
  `instalaciones-v0.2.0` (9 `.py`, 0 truncados, `description` 491/500, vs v0.1.0: 1 nuevo `resultado_ifc.py`)
  y para `iso19650-openbim-v0.4.1` (13 `.py`, desc 369/500, 2 nuevos). `verificar_espejo_nucleo.py`
  ESPEJOS IDÉNTICOS en ambos. Caso e2e PCI-02 CUMPLE; memoria md+docx.

### PT 4.5 — Segundo vertical: instalaciones ELÉCTRICAS de BT (REBT) (Ola 4) · `instalaciones` v0.3.0 / `iso19650-openbim` v0.4.2
- **Otro solver sobre el mismo grafo (confirma la tesis del núcleo).** El grafo nodos+tramos es
  **agnóstico al solver**: el vertical eléctrico reutiliza la **propagación por árbol** del solver
  hidráulico (`red/solver_red._arbol_desde_fuente`, importado) — BT de interior es **radial**, no hay
  Hardy-Cross y **no se duplica el grafo**. El solver eléctrico (`electrico/solver_electrico.py`, stdlib)
  solo aporta su física. Mismo patrón demanda→solver→verificación→write-back que PCI.
- **Decisión de método: HÍBRIDO (momentos + intensidades).** Sección **propuesta** por momentos sobre
  catálogo normalizado + **intensidad admisible** (ITC-BT-19); **comprobación vinculante** por el método
  de las **intensidades** (I·R con cosφ, mono/tri), ΔU acumulada por la rama, con **redimensionado**
  automático del tramo gobernante si supera 3 %/5 %. Micro-test contra cálculo analítico cerrado
  (mono y tri) + balance de potencias + redimensionado: **14/14 OK**.
- **Dónde nace la sección del conductor (decisión de frontera C1↔disciplina).** La sección es una
  **variable de diseño** (el entregable, análogo al "DN dimensionado"), no geometría BIM → nace en la
  **capa de demanda/criterios de `instalaciones`**; el **parser de `iso19650` NO se toca**. Se escribe
  como resultado (mismo `Pset_Estructurando_ResultadoRed` con propiedades eléctricas).
- **INC-11 (nueva): el validador MEP no era sistema-aware.** `checks-mep.py` exigía
  `Pset_PipeSegmentTypeCommon` en **todo** segmento (su propio comentario lo marcaba como TODO "o
  Duct/Cable según sistema") → una red `ELECTRICAL` daba **NO APTO**. **Resuelto** haciéndolo
  sistema-aware (Pipe/Cable/Duct según `sistema.tipo`) → `iso19650-openbim` **v0.4.2** (validador, **no**
  el parser). Sin regresión en PCI (sigue exigiendo Pipe).
- **Fixtures: el parser casa la clase EXACTA `el.is_a()`.** `IfcCableSegment`/`IfcLightFixture` (subtipos
  de FlowSegment/FlowTerminal) **no** los lee el parser intacto (compara con `("IfcFlowSegment",)`); hay
  que crear los fixtures como `IfcFlowSegment`/`IfcFlowTerminal`. Además, **tramos colineales solapados**
  (TOMA y MOTOR sobre el mismo eje) los **trocea** el grafo por intersección T/X → lazo espurio; se
  dispusieron las derivaciones en direcciones distintas (el solver lo trataba como radial igualmente).
- **Línea general mono+tri = trifásica equilibrada (aproximación de predimensionado).** Un feeder que
  alimenta cargas mono y tri se resuelve como **trifásico** (U=400); la ΔU acumulada mezcla tramos a 400 V
  y ramas a 230 V, expresada en % sobre la tensión del terminal → documentado como NDP `[confirmar AN]`.
- **Puertas de calidad.** `instalaciones-v0.3.0` (APTO, `--ref` v0.2.0) e `iso19650-openbim-v0.4.2`
  (APTO, `--ref` v0.4.1); `verificar_espejo_nucleo.py` ESPEJOS IDÉNTICOS (canónico motor v0.23.0). Casos
  e2e `caso-REBT-01-vivienda` (ΔU máx 1,098 %) y `caso-REBT-02-terciario` (ΔU máx 3,318 %) **CUMPLE** y
  validados **APTO**; memorias md+docx.

### PT 4.6 — Verificación y consolidación de la Ola 4 (núcleo de red + PCI + REBT) · `Verificacion-Ola4.md`
- **El modelo neutro de red ES agnóstico al sistema (probado, no asumido).** El mismo parser
  `ifc_to_model_mep.py` emite top-keys idénticas (`unidades/sistema/nodos/tramos/terminales/fuentes/metricas`)
  y el mismo bloque `unidades` para `FIREPROTECTION` y `ELECTRICAL`; **solo cambia `sistema.tipo`**. La
  sección del conductor nace en demanda (no en el parser) → el parser quedó intacto v0.4.0→v0.4.2 (puerta:
  0 encogidos/0 nuevos). Dos solvers (Darcy-Weisbach + eléctrico) sobre el mismo `grafo_red`. Patrón a
  anunciar al núcleo: **"grafo de red + N solvers"** (Manning en Ola 6, conductos en clima 4.x).
- **Regresión: re-ejecutar desde `/tmp` y contrastar contra el JSON de referencia, hoja a hoja.** Micro-test
  3/3; 5 casos e2e. MEP-01/REBT-01/REBT-02 **byte-idénticos**; PCI-01 numéricamente idéntico (info[] del
  arnés reformulado + esquema almacenado anterior al caudal con signo → "claves nuevas", **no** regresión).
  **PCI sin regresión tras REBT**: PT 4.5 no tocó el solver hidráulico ni la demanda PCI.
- **Lección clave (INC-12): un caso e2e puede depender de un paso de ORQUESTACIÓN del agente, no
  reproducible con las llamadas CLI aisladas.** PCI-02 (rociadores) divergía al re-ejecutar `run_all_pci.py`
  porque el dispatcher `aplicar_demanda` cae a **BIE** si falta `sistema.clase_riesgo`, y la clase de riesgo
  (OH1) **la inyecta el agente** (el IFC no la lleva; el README lo dice). Con la inyección reproduce
  **exacto** (req 58,9 / margen 241,1; 0 mismatches/282 claves). Generaliza: documentar (o codificar como
  flag/Pset) todo dato que el agente inyecta entre parser y solver, para que la regresión sea reproducible.
  **→ Resuelto en este mismo PT (`iso19650-openbim` v0.4.3, opción a+c):** el parser lee `clase_riesgo` de
  `Pset_Estructurando_SistemaPCI` del `IfcDistributionSystem` (el dato del IFC prevalece, como con
  caudal/presión de terminal) y el generador lo escribe; PCI-02 reproduce **sin inyección** y el `clase_riesgo`
  **round-trips** por el write-back IFC (re-parseado CUMPLE, OH1). Sin regresión (BIE/REBT → None); núcleo e
  `instalaciones` intactos; puertas APTO + ESPEJOS IDÉNTICOS.
- **El hazard de mount también corrompe el contraste workspace↔`.plugin`.** Al hashear por shell los `.py`
  del workspace salían "divergencias" que eran **lecturas truncadas** (p. ej. `solver_red.py` 15 209 B con
  SyntaxError vs 22 810 B en el `.plugin`; 4/5 fallan `ast.parse` = firma de corrupción, no de stale). Se
  desmiente con la herramienta `Read` (fuente de verdad: el workspace tiene 522 ln y termina igual que el
  `.plugin`). **Regla:** para contrastar workspace↔`.plugin`, el `.plugin` por `unzip` (íntegro) y el
  workspace por `Read`, **nunca** `md5` de la copia por shell. La lección PT 4.5 (`.md` no sincronizado)
  **no recurrió** (CHANGELOGs al día; `checks-mep.py` del workspace = del `.plugin`).
- **La propia puerta `verificar_empaquetado.py` llegó mount-corrupta** (9201 B / 200 ln / SyntaxError 201):
  reconstruida desde `Read` (251 ln, parsea) y ejecutada desde `/tmp`. La puerta de espejo se sirvió íntegra.
- **`--allow-shrink` es para refactores auditados, no para tapar truncados.** El motor v0.23.0 da "NO APTO"
  contra v0.22.1 por 3 encogidos = el refactor H1 (código movido a `scripts/nucleo/`: puente.py −3411 B,
  barras −299, laminas −295); con `--allow-shrink` de esos 3 → APTO. Distinto de un truncado (esos parsean).
- **Decisión: cerrar la Ola 4 "en lo verificado" (PCI+REBT) y RITE → sub-ola 4.x (PT 4.7).** El hueco de
  clima está pre-aprovisionado (parser agnóstico, validador `AIRCONDITIONING→Duct`, patrón demanda/subagente);
  RITE es vertical nuevo (conductos, cargas térmicas, demanda RITE/DB-HE), no verificación.

### PT 5.1 — Apertura del dominio georreferenciado de obra lineal: parser de alineación + validación + GIS (Ola 5) · `iso19650-openbim` v0.5.0

- **Patrón "abrir un dominio IFC nuevo reutilizando el núcleo sin tocarlo" reaplicado (como PT 4.2 con MEP).**
  Nace `scripts/lineal/` en `iso19650-openbim` espejando la estructura de `scripts/mep/`
  (parser + generador + validación + micro-test), consumiendo `ifc_utils` (`length_scale`) **sin
  modificar el núcleo** → `verificar_espejo_nucleo.py` sigue **md5-idéntico** en los 3 plugins.
- **El soporte lineal es un MODELO NEUTRO HERMANO NUEVO, no una red.** La alineación es
  **referenciación lineal por PK** (curva paramétrica 1D); **no** se reutiliza `grafo_red` (eso es
  drenaje/obras hidráulicas, Ola 6). El parser emite `alineacion{planta[]/alzado[]/peralte[]}` +
  `georref` con las mismas convenciones `unidades` SI y claves nuevas, sin redefinir las existentes.
- **Ruta de lectura del `IfcAlignment` (IFC4X3):** `IsNestedBy` → `IfcAlignmentHorizontal/Vertical/Cant`
  → `IsNestedBy` → `IfcAlignmentSegment` → `.DesignParameters` (`IfcAlignment{Horizontal,Vertical,Cant}Segment`).
  Caso a la **clase exacta** `el.is_a()` (lección PT 4.2). Convenio IFC del radio: **0 = recta = radio
  infinito** (→ `None` en el neutro); A de clotoide derivado = √(R·L).
- **Validación geométrica por integración:** generador y validador comparten el **mismo integrador de
  curvatura lineal en s** (n=400), de modo que la continuidad/tangencia de planta se comprueba
  re-integrando cada segmento y contrastando su extremo con el inicio del siguiente (máx 0,0001 m /
  0,0 rad en el banco). El micro-test añade **3 casos negativos** (salto, PK no contiguo, sin georref)
  para confirmar que el arnés muerde.
- **Georreferencia leída en el parser lineal** (`IfcMapConversion`+`IfcProjectedCRS`), **no en el
  núcleo** (decisión PT 5.1): mínima disrupción, espejo intacto; se promoverá a `ifc_utils` solo cuando
  una **segunda** disciplina georreferenciada lo necesite (obligaría a re-espejar).
- **Decisión nº3 (GIS) resuelta: GeoJSON + IFC 4.3 (dos soportes complementarios).** `export_gis.py`
  vuelca la planta a `LineString` en el CRS proyectado (puente a cartografía/cuencas para la Ola 6);
  Shapefile queda documentado como opción futura (evita dependencia binaria/`pyshp`).
- **Decisión nº2 (empaquetado) confirmada:** un plugin único `obras-lineales` con subagentes, que
  **nace en PT 5.2**; el parser/validación de alineación viven en `iso19650-openbim` (capa IFC
  transversal), igual que el MEP.
- **Hazard de mount reconfirmado (refuerza INC-04/INC-10).** El shell sirvió copias **truncadas/stale**
  de ficheros pre-existentes (REPOSITORIO a 59 ln, SKILL.md, un `.py` recién escrito por Write a 209 ln
  con string cortado) y de un `.py` recién creado tras `cp` desde el mount. Mitigado: **`Read` como
  fuente de verdad**, autoría de los `.py` por **heredoc en `/tmp`** (extraído del `.plugin`, íntegro),
  test y empaquetado **desde `/tmp`**; persistencia a la carpeta por `cp /tmp → mount` verificado con
  `Read`. Los `.plugin` (ZIP) extraen íntegros.

### PT 5.2 — Nace la disciplina `obras-lineales`: trazado 3.1-IC + firmes 6.1-IC (Ola 5) · `obras-lineales` v0.1.0
- **Nace una disciplina vertical sobre el modelo neutro lineal** (análogo a `instalaciones` en PT 4.3,
  pero lineal): la lectura/coherencia del IFC 4.3 sigue en `iso19650-openbim` (PT 5.1); el **cálculo de
  trazado (3.1-IC) y la selección de firme (6.1-IC)** son del nuevo plugin, que **consume el JSON neutro
  lineal** (no el IFC). Agente `ingeniero-de-obra-lineal` (clasifica trazado/firmes/ambos) + subagentes
  `proyectista-de-trazado` y `proyectista-de-firmes`. **Trazado y firmes son geometría + normativa: NO
  hay FEM ni solver de red.** [casos LIN-02/LIN-03]
- **Frontera validación (iso19650) vs cumplimiento (obras-lineales).** `validacion_alineacion.py` (PT 5.1)
  comprueba **coherencia geométrica** (PK/continuidad/tangencia/georref) y deja el 3.1-IC como **aviso
  informativo** (A∈[R/3,R]); el **veredicto normativo frente a la Vp** (radio mínimo, Kv, pendiente, Dp)
  es de `obras-lineales`. No se duplica: cada capa hace lo suyo. [caso LIN-02]
- **Vp es el parámetro de proyecto gobernante del trazado.** El mismo eje (caso-LIN-01) **CUMPLE a Vp=60**
  y **NO CUMPLE a Vp=100** (R 300<450, clotoides cortas por confort, Kv 2000<7125). La herramienta **no
  rediseña**: reporta CUMPLE/NO CUMPLE por elemento + propuesta de predimensionado. Los umbrales (radio,
  Kv convexo `Dp²/(2(√h1+√h2)²)`, Dp, pendiente) se computan de forma transparente y NDP `[confirmar AN]`
  en `parametros_3_1_IC.py` (preferible a tabular números que podrían quedar desactualizados). [caso LIN-02]
- **Relleno de ganchos del modelo neutro (C1 §4bis).** Firmes rellena `firme` (sección del **catálogo
  6.1-IC**) y una `secciones_tipo` básica; **solo añade claves**, nunca redefine las existentes (modelo
  hermano retrocompatible). `terreno` queda en `None` (drenaje/movimiento de tierras, Ola 6). El IFC
  enriquecido (`Pset_Estructurando_ResultadoLineal`) **re-parsea y revalida CUMPLE** (no rompe el modelo). [caso LIN-03]
- **Firmes por catálogo, no por fatiga** (decisión PT 5.2): la 6.1-IC manda secciones de catálogo;
  combinaciones T00/T0/T1 × E1 rechazadas (mejorar explanada). El **dato del IFC prevalece** para Vp e
  IMDp/explanada (patrón INC-12). [caso LIN-03]
- **Decisión: sin espejo de núcleo.** El plugin no lee IFC ni usa `grafo_red` (la alineación es
  referenciación 1D por PK, no una red), así que **no espeja `scripts/nucleo/`** y la puerta
  `verificar_espejo_nucleo.py` **no aplica** (declarado). Cálculo en **stdlib pura**. Puerta de
  empaquetado **APTO** (description 478/500; sin `--ref` por ser v0.1.0).
- **Hazard de mount reconfirmado (refuerza INC-04/INC-10).** El shell sirvió una copia **stale** de
  `plugin.json` recién **editado** (JSON con "Extra data" en una línea fantasma) — desmentido con `Read`
  (fuente de verdad). Mitigado: `plugin.json` canónico reconstruido por **heredoc en `/tmp`** para
  empaquetar; los `.py`/`.md` **nuevos** se leyeron íntegros y el `.plugin` (ZIP) extrae íntegro. La
  puerta de empaquetado se ejecutó desde `/tmp`.

*(A partir de aquí, una entrada por cada caso del programa.)*

---

## 2. Backlog de incidencias (priorizado)

Estado: 🔴 abierta · 🟡 en curso · ✅ resuelta. Prioridad: P1 (bloqueante) … P3 (mejora).

| ID | Prioridad | Estado | Descripción | Detectada en | Resuelta en |
|---|---|---|---|---|---|
| INC-01 | P1 | ✅ | **Parser de sección ortodoxa.** Resuelto: sección desde `IfcMaterialProfileSet`→`IfcIShapeProfileDef` con `perfiles_db.py` (DB HEB/IPE + geometría de respaldo) y material desde el profile set. Pset propio se mantiene como respaldo. | Caso 1 | **Caso 1 (v0.3.1)** |
| INC-02 | P1 | ✅ | **Parser de cargas ortodoxas.** Resuelto: `IfcStructuralCurveAction`+`IfcStructuralLoadLinearForce` con caso desde `IfcStructuralLoadGroup` (`IfcRelAssignsToGroup`) y barra desde `IfcRelConnectsStructuralActivity`. Respaldo Pset si no hay cargas ortodoxas. | Caso 1 | **Caso 1 (v0.3.1)** |
| INC-03 | P2 | ✅ | **Multi-elemento.** Los parsers usan `by_type(...)[0]` (un solo elemento). Para IFC con varios elementos hay que iterar todos y que el agente clasifique/enrute cada uno. **Caso 1**: itera todas las barras. **Caso 2 (v0.4.0)**: el parser de láminas lee superficie + barras juntas y `run_forjado.py` resuelve el **reparto por ancho tributario** (losa unidireccional sobre 2 vigas). **Caso 3 (v0.5.0)**: **apoyos puntuales** — `solver_flat.parse_ortodoxo()` lee los 9 pilares del modelo neutro (sección rectangular `IfcRectangleProfileDef`, posición clasificada por la retícula) y apoya la malla MITC4 en sus cabezas; `run_losa_plana.py` enruta la losa a flexión por bandas + punzonamiento EC2. **Caso 4 (v0.6.0)**: **superficie inclinada + apoyos lineales de borde** — `solver_incl._parse_ortodoxo()` deduce L_u/L_v/θ de las esquinas inclinadas y aplica los apoyos de alero/cumbrera desde `IfcStructuralPointConnection`+`IfcBoundaryNodeCondition` (clasificados por geometría; laterales libres, faldón 1-vía). **Caso 5 (v0.7.0)**: **cadena pilar→cimiento + lecho elástico de borde** — `solver_zapata.parse_ortodoxo()` lee la zapata (superficie), identifica el pilar (barra vertical) y baja su carga de cabeza (`IfcStructuralPointAction`), y reconstruye k_s de la rigidez de los `IfcBoundaryNodeCondition`. **Caso 6 (v0.8.0)**: **viga mixta ortodoxa** — `solver_mixta.parse_ortodoxo()` lee el perfil (`IfcMaterialProfileSet`→`IfcIShapeProfileDef`), la losa (`IfcStructuralSurfaceMember`, ancho = luz transversal) y las **cargas por fase** (`IfcStructuralLoadGroup`+`IfcStructuralSurfaceAction` clasificadas por nombre `*_construccion`/`*_mixta`); conectores y chapa siguen en Pset. **Caso 7 (v0.9.0)**: **muros ortodoxos** — `solver_muro.parse_ortodoxo()` (en `laminas` y `muros-contencion`) lee el alzado (H, espesor=`Thickness`, material) de la `IfcStructuralSurfaceMember` vertical, **clasifica muro de carga vs contención** por la presencia de `Pset_Estructurando_Terreno`, lee la **carga de cabeza** (`IfcStructuralPointAction`, N+M) del muro de carga y mantiene geometría T + terreno en Pset; `parse()` del muro de contención hecho **robusto a multi-superficie** (selección por Pset, no `by_type[0]`). **Caso 8 (v0.10.0)**: **raft multipilar ortodoxo** — `solver_raft.parse_ortodoxo()` lee la losa (superficie), identifica los 6 pilares (barras verticales) con lado/pie, mapea la carga de cabeza de cada pilar (`IfcStructuralPointAction`→nodo de cabeza) y reconstruye k_s del lecho (`IfcBoundaryNodeCondition`), generalizando la cadena del caso 5 a la malla multipilar. **Caso 9 (v0.11.0)**: **cimentación profunda multi-sistema** — `parse_ortodoxo()` en los **tres** módulos (`pilotes`, `bielas-tirantes`, `muros-contencion`) con **clasificación/enrutado por Pset** de tres elementos en un mismo IFC (2 barras verticales pilote/pantalla + superficie encepado, indistinguibles por geometría); pilote D del `IfcCircleProfileDef` (perfiles_db ampliado) + carga de cabeza de `IfcStructuralPointAction`; encepado canto=`Thickness` + separación de los `IfcStructuralPointConnection` de cabeza + carga de pilar; pantalla espesor del `IfcRectangleProfileDef`. Cada parser selecciona su elemento por Pset (no `by_type[0]`). **Caso 10 (v0.12.0)**: **CERRADO** — `scripts/clasificador.py` itera TODO el IFC, clasifica/enruta cada elemento por geometría+sección+material+lecho/carga de cabeza, resuelve las asociaciones viga↔losa y pilar↔zapata sin Pset, y **extrae un sub-IFC node-minimal por subsistema** para que cada `run_all*` se ejecute sobre su porción (evita los `by_type[0]` internos sin tocarlos); `scripts/run_all_edificio.py` orquesta por subprocesos (aísla módulos homónimos) y consolida el índice del edificio. 4 sistemas (pórtico/mixta/muro/cimentación) resueltos en un mismo IFC, todos CUMPLEN. | Programa | ✅ **casos 1–10** (cerrado en el 10) |
| INC-04 | P3 | 🟡 | **Robustez de edición.** El editor/linter trunca líneas largas al guardar (f-strings con comillas anidadas). En el caso 1 se evitó escribiendo por heredoc en sandbox y `%`-formato; verificado con `ast.parse`. Mantener la práctica. | Catálogo | Mitigado caso 1 |
| INC-05 | P3 | 🟡 | **Limpieza de artefactos.** `node_modules` (docx) y `__pycache__` quedan en carpetas. En el caso 1 se **excluyeron del `.plugin`** (`-x */node_modules/* */__pycache__/*`) y se instaló docx en local. Documentado el patrón de empaquetado. | Catálogo | Mitigado caso 1 |
| INC-07 | P2 | ✅ | **Puente físico→analítico: offsets/excentricidades y geometría "real-sucia".** El módulo `puente_analitico` (caso R1) derivaba ejes/nudos de un IFC físico **limpio**. **R2 (v0.16.0)**: superficie media + espesor de `IfcSlab` (`IfcMaterialLayerSet`) + conectividad superficie↔barras. **R3 (v0.18.0)**: superficies VERTICALES (`IfcWall`) + cimientos (`IfcFooting`) con clasificación por orientación y cadena muro→cimiento. **R4 (v0.19.0)**: edificio multi-elemento completo desde un único IFC físico (`run_all_real_edificio.py`). **R5 (v0.21.0) — CERRADO**: `puente.py` endurecido ante geometría real-sucia, retrocompatible: (a) recuperación del eje analítico por **`CardinalPoint`** del `IfcMaterialProfileSetUsage` (excentricidad guardada por barra); (b) **grafo de nudos** con tolerancia de snap **parametrizable** (`Pset_Estructurando_Puente.Snap_tol_m`) + bridging de huecos/solapes + **troceo en T/X con offset** (proyección sobre la directriz, margen paramétrico relativo a L); (c) **filtrado** de no-estructurales (clases admitidas) y de componentes **no conectadas** (union-find), solo activo en real-sucio (`snap_tol>TOL`); (d) **alias de perfiles** (Euronorm `HE 200 B`→`HEB 200`) + nombre normalizado de catálogo; (e) **factor de unidades** del `IfcUnitAssignment` (mm→m). **R1–R4 idénticos** en IFC limpio (regresión byte a byte del modelo neutro). Reproduce el caso 1/R1 desde un IFC real-sucio (93,60 kN/apoyo; HEB 200 31,8 %; IPE 330 44,8 %; cruzada CONFORME). Pendiente menor (fuera de INC-07): `IfcPile` físico. | Caso R1 (Dirección 2) | **R5 (v0.21.0) — CERRADO** (R2 0.16.0 + R3 0.18.0 + R4 0.19.0 + R5 0.21.0) |
| INC-08 | P2 | 🟡 | **Sandbox sin ejecución (casos 12 y 13).** En estos hilos el entorno solo expuso herramientas de fichero (Read/Write/Edit) sobre las carpetas conectadas; **no hubo `bash`/`python3`** (los tools `mcp__workspace__bash`/`Bash` respondieron "No such tool available"). **Caso 12**: se entregó TODO el código de `pretensado/` (en `caso-12-viga-postesada/_codigo/`) y los entregables numéricos closed-form (`modelo_neutro.json`, `verificacion_pretensado.json`). **Caso 13**: se entregó TODO el código nuevo en `plugin_work/scripts/pretensado/` (`run_all_losa_postesada.py`, `solver_losa_postesada.py`, `balance_2d.py`, `verificacion_losa_postesada.py`, `plots_losa_postesada.py`, `generate_memoria_losa_postesada.py`) + la ampliación retrocompatible de `laminas/ec2_punz_fis.py`, copiado a `caso-13-losa-postesada/_codigo/`, más el `modelo_neutro.json` (parse determinista) y la validación closed-form (balance/P/m/σcp/pérdidas/punzonamiento §6.4.4/cross-check). **Caso 13 RESUELTO en este hilo** (el hilo principal sí dispone de `mcp__workspace__bash`): ejecutado `run_all_losa_postesada.py` (FEM MITC4 malla 1,0 m, ~12 s) → `resultados.json` + `verificacion_losa_postesada.json` + 8 `.png` + memoria `.docx`; corregidos en sandbox el **truncado de `ec2_punz_fis.py`** (INC-04, se restauró del `.plugin` y se re-amplió), el **V_Ed de punzonamiento por área tributaria** (criterio del caso 3; pico elástico como envolvente) y el **dimensionado de la armadura pasiva superior** sobre pilares; **`.plugin` v0.17.0 reempaquetado acumulativo** (preservando `sismico/`+`pretensado/`+`puente_analitico/` R1+R2). Equilibrio FEM 0,000 %, aprov. estructural 0,99. Queda pendiente solo el FEM del caso 12 (1D, closed-form ya válido). **Caso R3 (Dirección 2)**: el subagente entregó el código pero reportó no tener ejecución; el **hilo principal SÍ dispone de `mcp__workspace__bash`** y **RESOLVIÓ el caso**: reparado el truncado de `puente.py` (INC-04), validado `ast.parse`, generado `caso-R3.ifc`, corrido el orquestador (puente+muro+zapata → `modelo_neutro.json`/`clasificacion.json`/`verificacion.json`/7 diagramas/memoria) **reproduciendo los casos 7 y 5**, y **reempaquetado `.plugin` v0.18.0 acumulativo** (preservando `sismico/`+`pretensado/`+`puente_analitico/` R1+R2). Patrón: cuando el subagente no tiene sandbox, el hilo orquestador ejecuta. **Caso R4 ✅**: el hilo orquestador dispuso de `mcp__workspace__bash` y ejecutó todo (generó `caso-R4.ifc`, corrió `run_all_real_edificio.py` —puente + clasificador multi-elemento + 4 subsistemas en subprocesos—, produjo JSON/diagramas/memoria y reempaquetó el `.plugin` v0.19.0 acumulativo). Queda pendiente solo el FEM del caso 12 (1D, closed-form ya válido). | Caso 12 | **Caso 13 ✅ (v0.17.0)**, **Caso R3 ✅ (v0.18.0)**, **Caso R4 ✅ (v0.19.0)**; caso 12 FEM 1D pendiente |
| INC-09 | P1 | ✅ | **Verificación de empaquetado (el empaquetado trunca módulos).** En v0.22.0 el reempaquetado acumulativo truncó 8 módulos preexistentes (raft/zapata/puente/barras) sin que nada lo detectara → el `.plugin` no instalaba limpio. Corregido en **v0.22.1** (restaurados desde v0.21.0). **Automatizado**: `Nucleo-transversal/verificar_empaquetado.py` audita el `.plugin` y devuelve exit≠0 si algo falla (`ast.parse` de todos los `.py` + salto de línea final + sin artefactos + plugin.json válido + contraste de tamaños vs `--ref` previo). Puerta obligatoria antes de publicar: `PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py <nuevo>.plugin --ref <previo>.plugin`. Probado: APTO en v0.22.1, NO APTO en copia truncada (caza los 3 síntomas; `ast.parse` solo no basta — 3/8 parseaban). Generaliza INC-04 al paso de empaquetado. | PT 1.6 (Ola 1) | **v0.22.1 + script de puerta (PT 1.6)** |
| INC-06 | P3 | 🟡 | **Modelo de fibras EC4 / propiedades del perfil.** Resuelto para los perfiles del catálogo: la vía ortodoxa de `mixtas` toma A/Iy/Wpl,y/Avz de `perfiles_db` (catálogo, con acuerdos) y solo las cotas h,b,tw,tf de la geometría; **IPE 360 añadido al catálogo** (caso 6, v0.8.0). Pendiente solo para perfiles **no tabulados** (siguen por geometría, ~4 % conservador) → ampliar catálogo según haga falta. | Caso 6 (EC4) | **Caso 6 (v0.8.0)** (perfiles de catálogo) |
| INC-10 | P2 | ✅ | **Reempaquetar un plugin de skills externo (read-only) + espejar el núcleo.** El plugin natural para MEP (`iso19650-openbim`) estaba instalado en solo-lectura y sin fuente en la carpeta. Patrón aplicado (PT 4.2): copiar la fuente a la carpeta, **`chmod -R u+w`** (Edit fallaba con EPERM al renombrar), **espejar** el núcleo a `scripts/nucleo/` del plugin (runtime aislado entre plugins), reempaquetar con baseline previa como `--ref`, y entregar el `.plugin` a reinstalar (no se activa en vivo). Mount **corrompió** lecturas de `.py` recién editados de forma persistente → reconstruir por heredoc en `/tmp` y empaquetar desde `/tmp`. **RESUELTO (PT 4.3):** decidido el **patrón de espejo** (no un módulo único importable, imposible por el aislamiento de runtime); núcleo **canónico en el motor**, espejado byte a byte a `iso19650-openbim` e `instalaciones`, con puerta de integridad `Nucleo-transversal/verificar_espejo_nucleo.py` (md5; FALLA si diverge). Probado ESPEJOS IDÉNTICOS (mismo md5 en los 3). | PT 4.2 (Ola 4) | ✅ **Resuelto (PT 4.3)**: espejo + puerta de integridad; decisión nº4 cerrada |
| INC-11 | P2 | ✅ | **Validador MEP no sistema-aware.** `iso19650-openbim:checks-mep.py` exigía `Pset_PipeSegmentTypeCommon` en TODO `IfcFlowSegment` (TODO heredado "o Duct/Cable según sistema") → una red `ELECTRICAL` (conductores con `Pset_CableSegmentTypeCommon`) daba **NO APTO** pese a continuidad 100 % y write-back correcto. **RESUELTO (PT 4.5):** Pset de segmento requerido **según `sistema.tipo`** (ELECTRICAL→Cable, AIRCONDITIONING→Duct, resto→Pipe) → `iso19650-openbim` **v0.4.2** (solo el validador; el **parser no se toca**). Sin regresión en PCI. Re-verificado PT 4.6. | PT 4.5 (Ola 4) | ✅ **Resuelto (PT 4.5)**: validador sistema-aware (v0.4.2) |
| INC-12 | P3 | ✅ | **Reproducibilidad de la red de rociadores PCI.** El caso e2e PCI-02 (rociadores OH1) no se reproducía solo con las 2 llamadas CLI: `run_all_pci.py` caía a demanda **BIE** si faltaba `sistema.clase_riesgo` (dato de proyecto que el agente inyectaba entre parser y demanda; el IFC no lo llevaba). **RESUELTO (PT 4.6, `iso19650-openbim` v0.4.3, opción a+c):** el **parser** `ifc_to_model_mep.py` lee `sistema.clase_riesgo` de `Pset_Estructurando_SistemaPCI.ClaseRiesgo` (o `Pset_Estructurando_Red`) cuando existe; si no, queda `None` y la inyecta el agente (respaldo). El generador `generate_test_ifc_rociadores.py` escribe ese Pset (`ClaseRiesgo=OH1`). Verificado: el IFC se autodescribe y **PCI-02 reproduce SIN inyección** (req 58,9 / margen 241,1; resultado 0/282 claves; write-back IFC re-parseado CUMPLE con `clase_riesgo=OH1`). **Sin regresión** (BIE/REBT → `clase_riesgo=None`, idéntico). El núcleo e `instalaciones` **no se tocan** (el dispatcher ya enrutaba por `clase_riesgo`). Puertas APTO + ESPEJOS IDÉNTICOS. | PT 4.6 (Ola 4) | ✅ **Resuelto (PT 4.6)**: parser sistema-aware de clase de riesgo (v0.4.3) |
| INC-13 | P3 | 🟡 | **Aproximación feeder mono+tri = trifásico equilibrado (REBT).** Un feeder que alimenta cargas mono y tri se resuelve como trifásico (U=400) y la ΔU acumulada mezcla tramos a 400 V y ramas a 230 V, expresada en % sobre la tensión del terminal. Aproximación de predimensionado, ya marcada `[confirmar AN]`; mantener como NDP a revisar por técnico (gancho para reactancia/desequilibrio en el futuro). | PT 4.5 / registrada PT 4.6 | 🟡 registrada (NDP `[confirmar AN]`) |

---

## 3. Decisiones de criterio (despacho)

Se consolidan también en `criterios-despacho.md` (raíz). Por defecto, salvo que el caso diga
otra coso:

- **Anejo Nacional**: España. NDP no verificados marcados `[confirmar AN]`.
- **Materiales por defecto**: hormigón C30/37, acero estructural S275, acero de armar B500S.
- **Coeficientes parciales**: γ_G=1,35 / γ_Q=1,50 (ELU, EC0 6.10); EC7 muros DA-2*; γc=1,5, γs=1,15, γM0=1,0, γv=1,25 (conectores).
- **Límites de flecha**: L/300 total y L/500 activa (forjados de hormigón); L/250 y L/350 (viga mixta) — ajustar por proyecto.
- **Recubrimientos**: 50 mm en contacto con terreno; 25–30 mm interiores (según exposición).

---

## 4. Métricas de salud del motor (se rellenan por caso)

| Caso | Equilibrio (error %) | Validación cruzada | Veredicto | Plugin tras el hilo |
|---|---|---|---|---|
| 1 | 0,0 % (93,60 kN/apoyo; Σ=187,2 kN) | OK (PyNite vs anaStruct, máx 0,06 %) | CUMPLE — C1/C2 HEB 200 aprov. 32,0 % (N+M); B1 IPE 330 aprov. 44,6 % (flecha L/300) | v0.3.1 |
| 2 | 0,00 % (4·63,45 = 253,8 kN vs 253,8 kN) | OK (viga vs anaStruct 0,04 %; placa strip vs q·L²/8 0,00 %; MITC4 OK) | CUMPLE — Losa C30/37 t=120 mm φ10/125 (µ=0,134; w_k=0,18 mm; flecha 39 %); V1/V2 IPE 400 aprov. 26,5 % | v0.4.0 |
| 3 | 0,000 % (1.597,5 kN aplicados = Σ 9 reacciones) | OK (MITC4 autodiagnóstico; tributaria interior 399 kN = q_ELU·25 m²) | CUMPLE — Losa plana C30/37 t=280 mm: vano φ10/150–φ10/125, soporte φ12/100; flecha 9 %; w_k=0,234 mm; punzonamiento P5 V_Ed,trib=399 kN aprov. 77 %. Reacción elástica 616 kN dimensionada (canto≥320 mm / Asw·s_r 22,2 cm²/m / capitel 576 mm) como envolvente | v0.5.0 |
| 4 | 0,000 % (460,8 kN aplicados = alero 230,7 + cumbrera 230,1) | OK (invariancia MITC4 0,78 %; My=38,1 ≈ q_n·L_u²/8=37,4 kN·m/m) | CUMPLE — Faldón inclinado C30/37 t=200 mm θ=30°: flexión vano My φ10/125 (µ=0,067), flecha 24 %, w_k=0,231 mm; membrana comp/trac ±67 kN/m, n_xy=7,1 kN/m → uRd 1,7 % (empuje tangencial q·senθ a alero/cumbrera, arco atado) | v0.6.0 |
| 5 | ~0 % (1.444 kN = cabeza 1.320 + p.p. 124 = Σ reacciones del lecho) | OK (MITC4 Timoshenko 2,5 %/0,5 %; k_s reconstruido 40 MN/m³ = dato) | CUMPLE — Zapata C30/37 2,5×2,5 t=600 mm sobre lecho k_s=40 MN/m³, pilar 0,40: EC7 hundimiento área eficaz σ_ef=246 ≤ R_d=250 kPa (98 %), e=0,075<B/6=0,417 (sin despegue; picos borde 273 / FE 271 envolvente); EC2 flexión My φ12/125 capa exterior, punz 11 %, cortante 56 %, fisuración φ12 w_k=0,272 mm (91 %), asiento 4,9 mm | v0.7.0 |
| 6 | 0,000 % (fase mixta M=q·L²/8=243,6 kN·m, V=q·L/2=121,8 kN; FE = analítico) | OK (sección de catálogo A=72,73 cm²; conexión parcial η=0,66 → M_Rd=280,2+0,66·(510,8−280,2)=431,6) | CUMPLE — Viga mixta IPE 360 S275 + losa colaborante C25/30 t=120 mm (hp58/hc62, chapa ⊥, sin apear), L=8,0 m sep=3,0 m: b_eff=2,10 m; M_pl,Rd=510,8 / M_a,Rd=280,2; **conexión parcial η=0,66 ≥ η_min=0,40** (kt=0,85) → M_Ed/M_Rd 56 %; cortante 22 %; fase construcción 41 %; flecha total 19,5/32 mm L/250 (61 %), activa 4,2/22,9 mm L/350 (18 %) | v0.8.0 |
| 7 | Carga: 0,000 % (537,4 kN/m = 1,35·(250+14,7)+1,50·120). Contención: empuje 0,21 % (Eh=114,4 ≈ 0,5·Ka·γ·H²+Ka·q·H; M_base 240,6 ≈ analítico 240,3) | OK (Ka=0,333 Rankine φ=30°; λ=52/λ_lim=27 §5.8.3.1; N-M con armadura simétrica; B′ Meyerhof) | CUMPLE — **Muro de carga** C25/30 H=3,0 t=0,20 (faja 1,0, arriostrado): λ=52>λ_lim=27 esbelto → M_Ed=M0Ed 17,0+M2 14,3=31,3 kN·m/m, φ10/200 c/cara M_Rd=67,3 (N-M 47 %), compresión §12.6.5.2 21 %. **Muro de contención** C30/37 Hm=5,0 t=0,40 B=3,40: vuelco u=0,50 (FS=2,62), deslizamiento u=0,97 (FS=1,67, pasivo parcial), hundimiento u=0,55 (q_Ed=165≤R_d=300, e=0,398<B/6=0,567 sin despegue); alzado φ16/100 trasdós (M=241, w_k=0,263), puntera φ16/225 (0,277), talón φ20/200 (0,296) | v0.9.0 |
| 8 | 0,00 % (7.722 kN = 1,35·(3.900 cabezas G + 353 p.p.) + 1,50·1.320 = Σ reacciones del lecho) | OK (k_s reconstruido 40 MN/m³ = dato; vía ortodoxa; placa MITC4 Winkler) | CUMPLE — **Losa de cimentación (raft)** C30/37 6,0×4,0 t=0,60 m sobre k_s=40 MN/m³, 6 pilares 0,40 (malla 3×2): EC7 presión media caract. 231 ≤ R_d=300 kPa (77 %, pico env. 247/ELU 342), **asiento dif. centro–borde 0,40 mm** (1/5045), sin despegue; EC2 flexión inferior X φ16/150 capa exterior (M=231 kN·m/m), cortante x 73 %/y 36 %, **punzonamiento con alivio del terreno §6.4.4(2)** no crítico (sin alivio 237 %), fisuración φ16/150 w_k=0,293 mm (98 %) | v0.10.0 |
| 9 | Pilote lateral 0,000 % (H=90 kN ELU = Σ muelles); encepado celosía vs cerrado 0,00 % (T=1.464, C=1.902 kN); pantalla horiz. ELU 0,00 % (Ea,car=457 kN/m) | OK (D del `IfcCircleProfileDef`; celosía PyNite vs estática θ=39,7°; Ka=0,333 Rankine φ=30°; clasificación 3 elementos por Pset) | CUMPLE — **Pilote** Ø0,60 L=12: EC7 N_Ed=1.215 ≤ Rc,d=1.876 kN (65 %, fuste 1.357+punta 707), lateral M=88 kN·m flecha 4,3 mm (43 %), EC2 As,min 14,1 cm². **Encepado** 2 pilotes a=1,80 canto 0,90: N_Ed=2.430 kN, tirante As 33,7 cm², biela 42 %, CCC 68 %, CCT 29 %. **Pantalla** e=0,60 H=7,0 d=4,5: M_máx=251 kN·m/m, **F_ancla=403 kN** (envolvente), bulbo 6,41 m, FoS_pasivo 1,78, As fuste 11,2 cm²/m | v0.11.0 |
| 10 | Pórtico exacto (PyNite vs anaStruct OK); muro vert. 0,000 %; zapata lecho 0,00 % | OK (clasificación/enrutado de **6 elementos** iterando TODO el IFC; asociaciones viga↔losa y pilar↔zapata sin Pset; sub-IFC por subsistema) | **CUMPLE (4 subsistemas)** — **Pórtico** HEB 240 N-M 22,9 % / IPE 360 30,5 %; **Mixta** IPE 400+losa C25/30 b_eff 2,10, M 333/450 (74 %), η=0,66, flecha 64 %; **Muro** C30/37 λ=52 esbelto, columna modelo M_Ed 30,2/M_Rd 68,1 (N-M 44 %), φ10/200; **Cimentación** zapata **ampliada 2,5→2,6** (predim.), σ_ef 236/250 (94 %), punz 17 %, cort 51 %, fis 0,28 mm (93 %), asiento 4,9 mm. Aprov. ≤ 1. **Cierre INC-03 y de la 1ª tanda** | v0.12.0 |
| 11 | 0,000 % (Fb=ΣF_i; Fb,lateral=928,6 kN, mano 929; M vuelco base 9.877 kN·m) | OK (modal `scipy.eigh` T1=0,408 s en meseta, M_eff,1=68,9 %; Sd(meseta)=0,1917 g=ag·S·2,5/q; modal SRSS 785 kN vs fuerzas laterales 928,6 kN, dif. 15,5 %) | **CUMPLE — APERTURA 2ª TANDA / familia sísmica** (módulo `sismico/` + biblioteca EC8 EN 1998-1) — **Pantalla de cortante** C30/37 Lw=4,0 tw=0,30 H=15,0 (5 plantas), ΣW=5.700 kN (m=581 t), q=3,0 DCM, λ=0,85: voladizo equivalente (stick, flexión + cortante Timoshenko); cortante alma 0,31 (ε=1,5, Asw/s=11,1 cm²/m), **elemento de borde l_c 0,60→1,20 m (gobierna, 0,97)**, N-M base 0,86 (M_Rd=11.515 kN·m), deriva 0,23 (≤0,75 %·h). Aprov. máx 0,97 | v0.13.0 |
| R1 | 0,0 % (93,60 kN/apoyo; Σ=187,2 kN; horiz. ±12,19 kN balanceadas) | OK (PyNite vs anaStruct; el puente físico→analítico reproduce el caso 1) | **CUMPLE — APERTURA Dirección 2** (IFC FÍSICO BIM real → analítico): de un IFC físico (2 `IfcColumn` HEB 200 + 1 `IfcBeam` IPE 330, sin entidades de análisis ni cargas) se derivan **3 barras + 4 nudos** (eje = directriz del barrido vía `get_local_placement`+`Depth`; sección/material de `IfcMaterialProfileSetUsage`; nudos por intersección de ejes con tol 1 mm), apoyos biarticulados y cargas G/Q de hipótesis (Pset) → enrutado a `barras` EC3: pilares HEB 200 **32,0 %**, dintel IPE 330 **44,6 %** | v0.14.0 |
| 12 | **Load balancing residual 0,0 %** (w_p=21,25 kN/m = permanente 21,25); cross-check cargas equiv. vs fuerza+excentricidad Δ=0,0 MPa (cuasiperm sup −4,55 / inf −1,99) | OK (dos métodos de pretensado coincidentes; M_ELU=2.334 ≈ mano 2.334; tensiones por fibra = chequeo de mano) | **CUMPLE — APERTURA tipología PRETENSADO** (módulo `pretensado/` + biblioteca EC2 §5.10) — **Viga postesada** C40/50 b=0,50×h=1,30 L=20 m, 1 tendón 13×Y1860S7 Ap=1.950 mm² trazado parabólico e=0,50 m: **P_m,∞=2.125 kN (σp,∞=0,586·fpk)**, P0=2.535 kN (σp0=0,699·fpk, pérdidas dif. ~16 %); tensiones transferencia sup −0,67/inf −7,13 (0,6·fck(t)), cuasiperm sup −4,55/inf −1,99 (sin descompresión, 0,45·fck), rara sup −7,53/**inf +0,99 < fctm=3,5**; **ELU fibras M_Rd=2.908 ≥ M_Ed=2.334 kN·m** (x/d=0,23); cortante V_Rd,c con σcp aprov. 0,91 (gobierna). Aprov. máx 0,91 | v0.15.0 |
| R2 | 0,000 % (carga superficie ELU 253,8 kN = Σ reacciones 4·63,45; reacción 63,45 kN/extremo) | OK (viga anaStruct vs teórico 0,042 %; strip de losa vs q·L²/8 0,000 %; MITC4 OK; el puente físico→analítico de superficies reproduce el caso 2) | **CUMPLE — Dirección 2, puente a SUPERFICIES** (IFC FÍSICO BIM real con `IfcSlab`): del IFC físico (1 `IfcSlab` C30/37 t=120 mm 6,0×4,0 + 2 `IfcBeam` IPE 400 S275, sin entidades de análisis ni cargas) el puente deriva **1 superficie media** (footprint del `IfcExtrudedAreaSolid` + placement a mundo, z_med=−0,06; **espesor 0,120 m de `IfcMaterialLayerSet`**; fctm derivado EC2) + **2 barras** (vigas), con **conectividad losa↔vigas [B1,B2]** y apoyos biarticulados de extremo → enrutado a `laminas`+`barras` (`run_forjado`, reparto por ancho tributario): losa φ10/125 **m_Ed=21,15 kN·m/m** (w_k=0,18 mm, flecha 39 %), **vigas IPE 400 26,5 %**. Reproduce el caso 2 | v0.16.0 |
| 13 | **Balance 2D residual 0,11 %** (w_px+w_py = 4,505+4,505 = 9,01 ≈ permanente 9,0 kN/m²); cross-check cargas equiv. vs fuerza+excentricidad por franja **Δ=0,000 MPa** (identidad M_net = M_ext − P·e); equilibrio ELU sobre carga NETA **0,000 %** (FEM MITC4 malla 1,0 m, 9 cabezas) | OK FEM+closed-form (P/m=212 kN/m, σcp=0,848 MPa, σp,∞=0,600·fpk, σp0=0,720·fpk, pérdidas dif. 16,7 %, V_Ed,punz interior 1.258 kN tributaria — pico elástico 1.937 kN como envolvente; el efecto favorable §6.4.4 relaja punz. 2,61→2,27 (−13 %); ampliación de punz. con defaults reproduce el caso 3) | **CUMPLE con solución de punzonamiento (predim.) — lleva el PRETENSADO a 2D** (módulos `pretensado/balance_2d` + `solver/verificacion/run_all_losa_postesada` + ampliación §6.4.4 de `laminas/ec2_punz_fis`) — **Losa plana postesada** C40/50 t=0,25 m, 3×3 pilares 0,45², vanos 8,0 m (L/h≈32), postesado **no adherente monotorón** Y1860S7 0,6" banded_X+distribuido_Y, drape 0,17: balance equilibra la permanente (residual 0,11 %), σcp=0,85 MPa; tensiones por fibra del FEM (transferencia inf +2,26<fctm; cuasiperm comprimido; rara inf +1,64<fctm=3,5); **ELU flexión** campo 0,68 / apoyo hogging 0,99 con As sup. **dimensionada 9,50 cm²/m (≈φ16/200)**; **punzonamiento §6.4.4** sin pret. 2,61 / con pret. 2,27 → losa fina a 8 m **requiere ábaco h≈0,47 m / capitel ≈2,18 m / Asw·sr≈110 cm²/m** (el pretensado ayuda, no sustituye); **flecha 5,2 mm ≪ L/250=32 (0,16)**, contraflecha de balance; fisuración 0,47. **Aprov. estructural máx 0,99 (≤1)** | v0.17.0 |
| R3 | Muro vert. ELU 0,000 % (N_Ed=537,4 kN/m = 1,35·(250+14,7 p.p.)+1,50·120 = Σ reacciones de base); zapata lecho ELU ~0 % (N_ELU=1.444 kN = 1,35·700 + 1,50·250 + 1,35·92 p.p. = Σ muelles) | OK (el puente físico→analítico de superficies VERTICALES + cimientos reproduce los casos 7 y 5; clasificación por orientación: 1 muro vertical + 1 zapata horizontal; cadena muro→cimiento ligada; MITC4 muro/placa OK) | **CUMPLE — Dirección 2, puente a superficies VERTICALES + cimientos** (IFC FÍSICO BIM real con `IfcWall` + `IfcFooting`): del IFC físico (1 `IfcWall` C25/30 H=3,0 t=0,20 faja 1,0 + 1 `IfcFooting` C30/37 2,5×2,5 canto 0,60, sin entidades de análisis ni cargas) el puente deriva **1 superficie VERTICAL** (plano medio del `IfcWall` 1,0×3,0, esquinas de base a cabeza centradas en el lado fino; **espesor 0,20 m de `IfcMaterialLayerSet`**) + **1 superficie HORIZONTAL** (footprint/canto del `IfcFooting`), clasificadas por **orientación** (normal del plano medio), con **cadena muro→cimiento** (pie del muro sobre la huella) → enrutado a `laminas/solver_muro` (EC2 §5.8.8) y `cimentaciones/solver_zapata` (EC7+EC2). **Muro** (caso 7): λ=52>λ_lim ⇒ esbelto, M_Ed=M0Ed+M2≈31,3 kN·m/m, **φ10/200 c/cara**, N-M≈47 %. **Zapata** (caso 5): EC7 σ_ef≤R_d=250 kPa (e=0,075<B/6 sin despegue), EC2 flexión My φ12/125 capa exterior, punz ~11 %, fisuración φ12 w_k≈0,272 mm. Reproduce los casos 7 y 5. Aprov. ≤ 1 | v0.18.0 |
| R4 | Pórtico exacto (reacción 93,60 kN/apoyo, horiz. balanceadas; PyNite vs anaStruct CONFORME); muro vert. ELU 0,000 %; zapata lecho ELU 0,000 % | OK (de UN IFC físico por plantas el puente deriva 8 nudos + 5 barras + 3 superficies y el clasificador multi-elemento enruta los 6 elementos resolubles; asociaciones losa↔viga {B2} y pilar↔zapata {C3} sin Pset; reproduce el caso 10 desde el físico) | **CUMPLE (4 subsistemas) — Dirección 2, EDIFICIO físico completo multi-elemento** (IFC FÍSICO BIM real con `IfcColumn`+`IfcBeam`+`IfcSlab`+`IfcWall`+`IfcFooting` por plantas, sin entidades de análisis): del **único IFC físico** el puente deriva todas las barras + superficies horizontales/verticales + cimientos con clasificación por orientación, conectividad superficie↔barras y cadenas pilar/muro→cimiento; el clasificador/enrutador multi-elemento (`run_all_real_edificio`) asigna cada elemento a su módulo y se calcula con los solvers existentes SIN CAMBIOS (subproceso por subsistema). **Pórtico** HEB 240 N-M 22,9 % / IPE 360 30,5 %; **Mixta** IPE 400+losa C25/30 b_eff 2,10, M_Ed 333 kN·m, η=0,66, M_Rd 522 (u 64 %), flecha 53 % (PNA en ala superior, verificado a mano; difiere del 450 histórico por refinamiento de la rutina EC4, no del puente); **Muro** C30/37 λ=52 esbelto, N-M 45 %, φ10/200; **Cimentación** zapata ampliada 2,50→2,55 (predim.), σ_ef 245/250 (98 %), e=0,116<B/6 sin despegue, punz 14 %, fis φ12 w_k 0,278 mm (93 %). Cierra la tubería físico→analítico→cálculo de extremo a extremo. Aprov. ≤ 1 | v0.19.0 |
| 14 | **Balance residual −0,74 %** (w_p=8·P·a/L²=21,09 kN/m ≈ permanente g0+g2=21,25); **M_sec lineal R²=1,000000, nula en extremos** (0,00/0,00 kN·m); **FEM vs método de las fuerzas Δ=0,000 %** (M_sec apoyo central 351,5 vs 351,5); identidad M_p,tot=M₁+M_sec (5,8·10⁻¹¹); esfuerzos externos FEM = chequeo de mano exacto (apoyo ELU −2.334, vano +1.313) | OK (FEM viga continua Euler-Bernoulli; secundario por diferencia M_p,tot−M₁ y por método de las fuerzas coincidentes; σp0/fpk=0,720, σp,∞/fpk=0,600, pérdidas dif. 16,7 %; tensiones por fibra con M_sec) | **CUMPLE — lleva el PRETENSADO a estructuras HIPERESTÁTICAS** (módulos `pretensado/ec2_continua` + `verificacion_continua` + `solver/run_all_pretensado_continua`) — **Viga postesada continua** C40/50 b=0,50×h=1,30, 2 vanos L=20 m (L/h=15,4), 3 apoyos, 14×Y1860S7 Ap=2.100 mm², trazado parabólico por vano e_vano=+0,30/e_apoyo=−0,30 (drape 0,45): **momentos secundarios** M_sec apoyo central **+351,5 kN·m** (sagging, alivia el hogging); **línea de presiones** e_p=e+M_sec/P, tendón **NO concordante** (desv. 0,15 m); tensiones por fibra con M_sec (apoyo rara top +0,71<fctm=3,5; resto comprimido); **ELU con secundario γ_P=1,0**: apoyo M_Ed=−2.334+1,0·352=**−1.983**/M_Rd=2.509 (u=0,79, x/d=0,296), vano M_Ed=1.614/M_Rd=2.537 (u=0,64); redistribución §5.5 δ_min=0,81 disponible (no aplicada); flecha 1,02 mm ≪ L/250=80. **Aprov. máx 0,79 (≤1)** | v0.20.0 |
| R5 | **Reacción 93,60 kN/apoyo EXACTA** (horiz. ±12,01 kN balanceadas); equilibrio M/V/flecha ~0 %; PyNite vs anaStruct CONFORME | OK (del IFC real-sucio el parser crudo leería 8 nudos/4 barras en mm; tras la limpieza → 4 nudos/3 barras = R1; regresión R1 32,0/44,6 % y R4 modelo neutro idénticos desde el `.plugin` empaquetado) | **CUMPLE — CIERRE de INC-07 y de la serie R / Dirección 2** (puente físico→analítico ENDURECIDO ante IFC "real-sucio" de exportador) — de `caso-R5.ifc` (IFC4 en **mm**: 2 `IfcColumn` "HE 200 B" + 1 `IfcBeam` "IPE330" con `CardinalPoint` 1/3/8, **solape 40 mm** en pilares, **hueco 30 mm** en dintel, + `IfcRailing` + `IfcBuildingElementProxy` + `IfcBeam` suelto) el puente: (a) **recupera el eje analítico** por cardinal point (ecc C1/C2 **0,141 m**, B1 **0,165 m**); (b) **grafo robusto** snap_tol 60 mm → **2 huecos/solapes puenteados** (0,05 m), troceo T/X validado en micro-test; (c) **filtra 3 elementos** (railing + proxy + viga suelta); (d) **alias** HE 200 B→HEB 200; (e) **unidades** mm→m (escala 1e-3). Enruta a `barras` (EC3): **HEB 200 31,8 %**, **IPE 330 44,8 %** (diferencias vs 32,0/44,6 % por la idealización del solape de 40 mm → pilares 4,04 m, documentada; reacción exacta). **R1–R4 intactos** en IFC limpio (tolerancia por defecto + sin offset). Reproduce el caso limpio a pesar de la suciedad | v0.21.0 |
| 15 | **0,000 %** (reparto X e Y: Σ V por pantalla = Fb; equilibrio fuerzas laterales 0,000 %; M_p,tot del par = M_vuelco) | OK (modal `scipy.eigh` 3 GdL/planta T1x=0,305/T1y=0,390 s en meseta, ΣM_eff=100 % X/Y; Sd(meseta)=0,1597 g=ag·S·2,5/q; modal SRSS 454/368 kN vs fuerzas laterales 543/543 kN; condensación del par acoplado y DoC=0,72 coherentes) | **CUMPLE — PT 1.5: NÚCLEO de pantallas acopladas + sísmico en el ORQUESTADOR de edificio** (módulos `sismico/nucleo` + `solver_nucleo` + `verificacion_nucleo` + `run_all_nucleo` + `plots_nucleo` + `generate_memoria_nucleo` + `edificio_sismo`; etapa sísmica en `run_all_edificio`) — **Núcleo en U abierto** C30/37, 2 machones de alma Lw=2,0 (acoplados por dintel) + 2 alas Lw=4,0, tw=0,30, 6 plantas×3,0=18 m, ΣW=4.000 kN, **q=3,6 DCM muros acoplados**, λ=0,85: diafragma rígido 3 GdL/planta, **CR(3,40;4,00) vs CM(4,00;4,00) → e0x=0,60 m**; reparto directo+torsión+**torsión accidental ±0,05·L (§4.3.2)** (sismo Y: machones directo, alas par ±; sismo X: alas directo); **vigas de acoplamiento DCM diagonal §5.5.3.5** (ln/h=2,0, V_dintel,máx=346 kN, **DoC=0,72**, N_acopl=1.441 kN → **machón a barlovento en tracción neta −775 kN**, armadura de borde dimensionada); aprov. alas 0,62 / machón compr. 0,72 / machón tracc. 0,33 / dintel 0,22 / deriva 0,15 (0,225 %·h ≤ 0,75 %·h). **Integrado en `run_all_edificio` (deriva masas, monta modelo lateral, reparte cortante, verifica derivas globales, EC0 §6.4.3.4)**. Caso 11 sin regresión. Aprov. máx **0,72**. **Cierra la estabilización lateral de edificación (Ola 1)** | v0.22.0 |
