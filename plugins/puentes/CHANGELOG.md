# Changelog

## v0.6.0 — 2026-06-24 · PT 7.5 (Ola 7) · tableros AVANZADOS (mixto, oblicuo, curvo) sobre FEM-2

Tres verticales nuevos sobre el peldaño **FEM-2** del motor (`motor-fem` v0.3.0 **intacto**, no se
toca: es un PT de disciplina, como el 7.3). Regla de oro: solo se construye la **idealización + la
comprobación EC específica**; lámina curva, rigidizador con offset, IAP-11 y write-back se **reutilizan**.

### Añadido — vertical MIXTO acero-hormigón
- **`idealizacion/mixto.py`**: losa de **láminas curvas MITC4** + cada viga de acero como
  **`ElementoRigidizador` con offset rígido** bajo la losa = **interacción completa** (acción
  compuesta). Recuperación del **momento mixto** de sección (`|N_acero|·lever + M_acero`).
- **`comprobacion/ec3ec4_mixto.py`**: **clasificación** de sección (clase 1-4), **abolladura
  EN 1993-1-5** por **ancho/área eficaz** (clase 4), **M_pl,Rd mixto por fibras** (EC4), **cortante**,
  **conexión** (P_Rd, Nc, η — espejo de `motor-calculo` mixtas) y **fatiga básica EN 1993-1-9** (Δσ vs
  Δσ_C/γ_Mf, FLM3). `run_all_mixto.py` + subagente `proyectista-mixto`.
- **Validación** `validacion/mixto_vs_ec4.py`: M_pl vs `motor-calculo` EC4 **0,47 %**; acción
  compuesta (flecha) vs viga compuesta de Euler **0,52 %**.

### Añadido — vertical OBLICUO (esviado)
- **`idealizacion/oblicuo.py`**: malla **romboidal** que sigue la línea de apoyo esviada
  (`x = y·tan φ`), cuadriláteros distorsionados MITC4. **Reparto transversal 2D** y **concentración
  de reacción en la esquina obtusa**.
- **`comprobacion/ec_oblicuo.py`**: EC2 (armado de losa long./transv.) o EC3 (placa). `run_all_oblicuo.py`
  + subagente `proyectista-oblicuo`.
- **Validación** `validacion/oblicuo_vs_recto.py`: recto (φ=0) `Mx` vs viga `w L²/8` **0,7 %**; el esviaje
  dispara la concentración obtusa (~1,5 → ~6,4).

### Añadido — vertical CURVO en planta
- **`idealizacion/curvo.py`**: malla de láminas curvas **siguiendo la directriz** (arco R o
  `IfcAlignment` de Ola 5), sección cajón en la terna `{t, n, z}` por estación. **Torsión acoplada**
  (`dT/ds=M/R`) recuperada del **couple de reacciones** entre almas; `J` de **Bredt**.
- **`comprobacion/ec_curvo.py`**: EC2 con **torsión protagonista** (compresión, armado del fondo,
  **cortante+torsión de Bredt** combinados). `run_all_curvo.py` + subagente `proyectista-curvo`.
- **Validación** `validacion/curvo_vs_viga_curva.py`: flexión vs viga `w S²/8` **6,6 %**; **ley T·R≈cte**
  (`T(R)/T(2R)≈2`, **3,4 %**); torsión **→0** en recto.

### Lector (IFC-driven)
- **`lectura/desde_ifc.py`**: adaptadores `_mixto`/`_oblicuo`/`_curvo` + `_DISPATCH`.
- **`lectura/gen_cases.py`**: builders `mixto` (IfcBeam `IfcIShapeProfileDef` + IfcSlab), `oblicuo`
  (IfcSlab + esviaje) y `curvo` (IfcBeam `IfcArbitraryProfileDefWithVoids` + R). `gen_ifc._ishape`.
  Limpiado el `sys.path` hardcoded de sesión (usa el dir local).
- **`comun/resultado_ifc_puente.py`**: mappers de write-back para las tres tipologías.
- **`iso19650-openbim`**: el parser estructural clasifica `mixto`/`oblicuo`/`curvo` (override
  `Pset_Estructurando_Tipologia` + heurísticas: acero+losa, esviaje, radio).

### Casos
- **PUE-18** (mixto), **PUE-19** (oblicuo), **PUE-20** (curvo): IFC4X3 → lector → FEM-2 → EC →
  write-back. Los tres **CUMPLEN** (aprov 0,755 / 0,949 / 0,666).

### Sin cambios
- **`motor-fem` v0.3.0 INTACTO** (no-regresión FEM-0/1/2 por construcción). Cajón (PT 7.4) sin regresión.

## v0.5.0 — 2026-06-23 · PT 7.4 (Ola 7) · vertical CAJÓN POSTESADO (lámina pura, FEM-2)

Nuevo vertical sobre el peldaño **FEM-2** del motor (`motor-fem` v0.3.0). Regla de oro: solo se
construye la **idealización del cajón + la comprobación EC2 específica**; FEM-2, postesado, IAP-11
y write-back se **reutilizan**.

### Añadido
- **`idealizacion/cajon.py`**: idealización por **lámina pura** del cajón unicelular trapezoidal
  (losa superior + losa inferior + dos almas inclinadas) con **láminas curvas MITC4** y
  **diafragmas de apoyo** como rigidizadores (offset rígido); nudos fundidos por coordenada,
  apoyos simples sobre la losa inferior. Propiedades de sección (A, Iy, c_sup, c_inf, **Am/J de
  Bredt**), recuperación de **momento de sección** por integración de Nx, y aplicación de cargas
  (peso propio g1, carga muerta g2, **postesado de balance** P0/Pinf, **LM1** con objetivos
  `esfuerzo_lamina`).
- **`comprobacion/ec2_cajon.py`**: EC2 del cajón por sección crítica — **tensiones por FASE**
  (construcción/transferencia y servicio), **descompresión**, **flexión ELU** (M_Rd del cajón),
  **cortante + torsión** de Bredt combinados (interacción V/T), **shear lag** (b_eff del FEM).
- **`run_all_cajon.py`**: orquestador e2e (acepta `.ifc`). Modal informativo (primer modo físico).
- **`agents/proyectista-cajon.md`** + enrutado en `ingeniero-de-puentes` (tipología `cajon`).
- **Lector**: `lectura/desde_ifc.py` con `_cajon` (Pset_Estructurando_Cajon/Postesado) y
  `lectura/gen_cases.py` con el builder `cajon` (IfcBeam + `IfcArbitraryProfileDefWithVoids`).
- **Validación**: `validacion/cajon_vs_viga.py` — deflexión y momento de sección del modelo de
  láminas vs **teoría de viga-cajón** (Euler), dentro de tolerancia de predimensionado.

### Caso
- **PUE-17** (`caso-PUE-17-cajon-postesado`): cajón postesado de 3 vanos, IFC4X3 → lector
  (tipología `cajon`) → idealización por láminas + postesado evolutivo → FEM-2 (estático + LM1 +
  modal) → EC2 → memoria + write-back. **CUMPLE**.

### Sin cambios / no-regresión
- Los verticales previos (vigas, losa, pórtico, celosía, pila, estribo) y el núcleo espejado
  **intactos**.

## v0.4.0 (2026-06-23) — Lector estructural IFC-driven (PT 7.3.1)

- **Nuevo:** `scripts/lectura/desde_ifc.py` (adaptador modelo neutro estructural -> entrada_caso por tipologia) + `cli_ifc.py`. Los `run_all_*` aceptan un `.ifc` como entrada (ademas del JSON).
- **Nuevo:** generadores IFC4X3 por tipologia (`gen_ifc.py`, `gen_cases.py`) y write-back (`writeback_ifc.py`).
- El parser C1 (`ifc_to_model_estructural.py`) vive en `iso19650-openbim` (clave aditiva del modelo neutro).
- Geometria extruida REAL (perfiles + cajon con huecos); A/Iy/Iz exactos, J de pared delgada.
- Validacion: round-trip parametrico<->IFC en las 6 tipologias (max 1,1e-6). 10 casos IFC-driven PUE-07..16.
- Idealizacion / IAP-11 / EC / write-back y motor-fem (C5) SIN cambios. Nucleo espejado intacto.

# Changelog — puentes

## v0.3.0 (2026-06-23) — PT 7.3: subestructura (pilas, apoyos, estribos, cimentaciones)
Dos verticales nuevos sobre el motor maduro (regla de oro: solo se construye la
**idealizacion + comprobacion**; FEM, EC7 de muro y cimentaciones se **reutilizan**).
El motor **`motor-fem` NO sube de peldano** (sigue FEM-1, sin cambios): columna,
resortes y modal/movil ya bastan.

### Pila + aparato de apoyo + cimentacion (`proyectista-pilas-apoyos`)
- **Idealizacion** `idealizacion/pila.py`: columna (barra 3D) plano XZ, base sobre
  **resorte Winkler** y **aparato de apoyo** (resorte 6 GdL) en cabeza.
- **Aparatos de apoyo** `comun/aparatos_apoyo.py`: elastomerico (`k=G·A/Te` + giro),
  POT/esferico (coaccion/liberacion por GdL), reparto horizontal por rigidez efectiva,
  reacciones del tablero en **dos modos** (dato del caso / acoplado al tablero 7.1-7.2).
- **Acciones** `acciones/iap11.py`: cargas de cabeza (permanente, LM1, **frenado/
  arranque**, viento, termica), peso propio y viento del fuste, combinaciones (γQ=1.35).
- **Comprobacion** `comprobacion/ec2ec7_pila.py`: fuste **flexo-compresion M-N**
  (armadura simetrica) + **2.o orden aproximado** δ=1/(1−N/N_cr) + cortante por bielas;
  cimentacion **EC7 enrutada** `comun/cimentacion_router.py` (zapata Meyerhof /
  pilotes Rc,d / encepado biela-tirante; formulas de motor-calculo reutilizadas).
- **Sismica EC8-2 = gancho diferido** (PT sismico de puente dedicado).

### Estribo (`proyectista-estribos`)
- **Idealizacion** `idealizacion/estribo.py`: estribo = **muro con cargas de tablero**
  en coronacion; fuste (alzado) resuelto por **motor-fem** (mensula). Empuje **activo
  Ka** (abierto/con junta) o **reposo K0** (cerrado/integral), selector del caso.
- **Comprobacion** `comprobacion/ec7ec2_estribo.py`: **reusa `verificacion_muro`**
  (EC7 vuelco/deslizamiento/hundimiento + EC2 alzado/puntera/talon); unica extension =
  el **frenado del tablero** inyectado en la estabilidad global.
- `empujes`/`pesos`/`ka_*` copiados byte-fiel de `solver_muro` (su import arrastra PyNite).

### Casos e2e
- **caso-PUE-05-pila-cimentacion**: pila H=8 m + apoyo elastomerico + zapata 6×6
  (CUMPLE). **caso-PUE-06-estribo**: estribo Hm=4.5 m, empuje activo Ka (CUMPLE).

### Validacion
- Pila: M_base FEM vs cerrada (H·H) err 8e-12; modal con reintento (modelo pequeno).
- Estribo: empuje integrado vs forma cerrada err 2e-3; validacion cruzada de muro.
- Motor-fem **sin tocar** (FEM-0/FEM-1 sin regresion por construccion).

## v0.2.0 — 2026-06-23 · PT 7.2 (Ola 7) · completa el grupo lineal

Amplia la disciplina con **tres verticales nuevos** sobre el motor maduro (FEM-0/1;
el motor solo sube a v0.2.1 por la extension aditiva `esfuerzo_lamina` que exige la
losa). Reutiliza por PYTHONPATH el postesado (`balance_2d`,
`verificacion_losa_postesada`), los muros/EC7 (`verificacion_muro`) y el EC3 de acero.
**Predimensionado; revisar y firmar por ICCP.**

### Anadido
- **Subagente `proyectista-losa-postesada`** + `idealizacion/losa_lamina.py` (malla
  **lamina DKMQ** + vigas de borde; membrana bloqueada, precompresion analitica),
  postesado biaxial por **balance de cargas 2D** (`iap11.postesado_losa`), LM1 con
  **dos lineas de rueda** por carril y **objetivo `esfuerzo_lamina`**, y
  `comprobacion/ec2_losa.py` (tensiones vacio/servicio, descompresion, flexion ELU
  por franja, punzonamiento si hay apoyos puntuales). `run_all_losa_postesada.py`.
  Caso `caso-PUE-02-losa-postesada` CUMPLE (aprov 0.967, f1=6.43 Hz).
- **Subagente `proyectista-portico`** + `idealizacion/portico.py` (marco XZ: dintel
  + pilas + **resortes Winkler** en base), empuje de tierras **K0 reposo**
  (`iap11.empuje_tierras`), y `comprobacion/ec2ec7_portico.py` (dintel flexion +
  cortante por bielas; pilas con **2.o orden aproximado**; **EC7** hundimiento +
  deslizamiento por la reaccion real de base). `run_all_portico.py`. Caso
  `caso-PUE-03-portico` CUMPLE (aprov 0.644, gobierna EC7).
- **Subagente `proyectista-celosia`** + `idealizacion/celosia.py` (Pratt de **barras
  articuladas**, 2D pura con RY coaccionada), y `comprobacion/ec3_celosia.py`
  (traccion, **compresion-pandeo curva b**, uniones; **fatiga EN 1993-1-9 = gancho
  diferido**). `run_all_celosia.py`. Caso `caso-PUE-04-celosia` CUMPLE (aprov 0.985).
- **Acciones IAP-11** ampliadas (`acciones/iap11.py`): losa, portico y celosia.
- **Write-back** (`comun/resultado_ifc_puente.py`) despacha por tipologia.

### Sin cambios
- El nucleo `scripts/nucleo/` se mantiene **espejado** byte a byte con `motor-fem`.

# Changelog — puentes

SemVer. Predimensionado/asistencia; revisar y firmar por tecnico competente (ICCP).

## v0.1.0 — 2026-06-23 · PT 7.1 (Ola 7)

Nace la **disciplina `puentes`** (plugin propio, decision nº2), primer consumidor
pleno del nucleo `motor-fem` (C5, **FEM-1**) y de la geometria **Alignment** (C1).

### Añadido
- **Agente** `ingeniero-de-puentes` (orquestador: clasifica tipologia, idealiza,
  acciona IAP-11, llama a motor-fem, comprueba EC2, memoria + write-back) +
  **subagente** `proyectista-vigas-pretensadas` (primer vertical).
- **Idealizacion por emparrillado** (`scripts/idealizacion/emparrillado.py`):
  malla C5 barra+barra (vigas + riostras) desde el eje (Alignment/recto), apoyos
  isostaticos. Decision: barra+barra (grillage clasico).
- **Acciones IAP-11** (`scripts/acciones/iap11.py`): permanentes (g1+g2), **LM1**
  (tandem + UDL por carril -> `cargas_moviles`), termica (uniforme + gradiente),
  viento, combinaciones de puente (ELU 6.10; ELS car/frec/cuasiperm.).
- **Inyeccion del pretensado** (`scripts/pretensado/inyeccion_pretensado.py`):
  perdidas (instantaneas + diferidas simplificadas EC2 5.46, decision nº5) +
  caso `P` de cargas equivalentes. **Reutiliza** `ec2_pretensado` (motor-calculo).
- **Comprobacion EC2** (`scripts/comprobacion/ec2_tablero.py`): tensiones en vacio
  y servicio, flexion ELU (M_Rd), cortante por bielas (V_Rd,max + cercos),
  fisuracion/descompresion.
- **Write-back** (`scripts/comun/resultado_ifc_puente.py`): mapping
  `Pset_Estructurando_ResultadoPuente`.
- **Orquestador e2e** (`scripts/run_all_viga_pretensada.py`).
- **Nucleo transversal espejado** (`scripts/nucleo/`) byte a byte del canonico.

### Caso de referencia
- `caso-PUE-01-vigas-pretensadas`: tablero L=25 m, 4 vigas doble-T (HP-45),
  2 carriles LM1 -> **CUMPLE** (aprov. max 0.81, gobierna cortante; flexion 0.72;
  perdidas 21.2 %; f1=2.24 Hz).

### Decisiones (confirmadas con el ICCP, 23/06/2026)
- `puentes` **plugin propio** (nº2). IAP-11 **en la disciplina** (no en el nucleo).
- Emparrillado **barra+barra**. Pérdidas diferidas **simplificadas** (nº5).
