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
