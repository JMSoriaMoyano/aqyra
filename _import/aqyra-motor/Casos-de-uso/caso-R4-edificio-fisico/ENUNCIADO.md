# Caso R4 — Edificio físico completo (el "caso 10 real")

**Dirección 2 · cuarto peldaño** · puente IFC físico (BIM real) → modelo analítico
**multi-elemento** de un edificio completo, clasificado y enrutado de extremo a extremo.
Plugin de partida: `motor-calculo-estructural` v0.18.0 → **v0.19.0** tras el hilo.

## 1. Objeto

Derivar y calcular el modelo analítico **COMPLETO** de un edificio a partir de un
**ÚNICO IFC FÍSICO** por plantas (entregable BIM real): `IfcColumn`/`IfcBeam`/`IfcSlab`/
`IfcWall`/`IfcFooting` con geometría de barrido (`IfcExtrudedAreaSolid`),
`IfcMaterial(ProfileSet/LayerSet)` y estructura espacial (Project→Site→Building→Storey),
**sin entidades de análisis ni cargas**. El puente deriva **todos los tipos a la vez** en
un solo modelo neutro y un **clasificador/enrutador multi-elemento** asigna **cada**
elemento a su módulo. Cierra la tubería **físico → analítico → cálculo** de extremo a
extremo: es la versión física del **caso 10** (que partía de un IFC ortodoxo de análisis).

## 2. El modelo (geometría = caso 10, para validar contra resultado conocido)

Edificio físico IFC4 por plantas (Cimentación / Planta Baja / Planta Primera) con los 4
subsistemas del caso 10 como **elementos físicos**, separados en planta:

- **Pórtico de acero** — 2 `IfcColumn` HEB 240 + 1 `IfcBeam` IPE 360 (S275), luz 6 m,
  altura 4 m. Carga de línea del dintel G=12 / Q=10 kN/m (Pset).
- **Forjado mixto** — 1 `IfcSlab` (losa C25/30 t=0,12) sobre 1 `IfcBeam` IPE 400 (S275),
  L=8 m, sep 3,0 m. Conectores/chapa y cargas por fase en Pset.
- **Muro de carga** — 1 `IfcWall` C30/37 (H=3,0 t=0,20, faja 1,0 m), plano medio vertical.
  Carga de cabeza N_G=250 / N_Q=120 kN/m, e=25 mm (Pset).
- **Cimentación** — 1 `IfcColumn` de hormigón C30/37 (rectangular 0,40) + 1 `IfcFooting`
  (zapata C30/37 2,5×2,5 canto 0,60) sobre lecho Winkler k_s=40 MN/m³, R_d=250 kPa.
  Bajada de carga N_G=700/N_Q=250 kN + M=80/40 kN·m (Pset). Cadena pilar→cimiento desde
  geometría.

## 3. Trabajo del hilo

1. **Derivar el edificio completo con el puente** (`puente_analitico/puente.py`): un único
   modelo neutro con todas las barras + superficies horizontales/verticales + cimientos,
   con clasificación por orientación, conectividad superficie↔barras y cadenas
   pilar/muro→cimiento. El puente itera TODO (no `by_type[0]`); ningún elemento se pierde.
2. **Clasificar/enrutar cada elemento del modelo neutro** (cierre real de INC-03 en la vía
   física): `clasificar_neutro_edificio` generaliza el patrón de R2/R3 a un edificio
   completo — pilar/dintel de acero I → `barras` EC3; viga de acero I asociada a losa →
   `mixtas` EC4; superficie vertical de hormigón con carga de cabeza → `laminas/solver_muro`
   EC2; superficie horizontal de hormigón con lecho → `cimentaciones/solver_zapata` EC7;
   pilar de hormigón sobre zapata → cadena pilar→cimiento. Asociaciones viga↔losa y
   pilar↔zapata desde geometría (sin Pset).
3. **Orquestar el edificio de extremo a extremo** (`run_all_real_edificio.py`): IFC físico →
   puente → modelo neutro → clasificar/enrutar → construir los dicts `model` por subsistema
   desde neutro + Psets → invocar los solvers existentes SIN CAMBIOS (`barras`,
   `mixtas/solver_mixta`, `laminas/solver_muro`, `cimentaciones/solver_zapata`), con
   aislamiento de módulos homónimos por **subproceso** por subsistema. Consolidar el índice
   del edificio (`resumen_edificio.json`).
4. **Validación — reproduce el caso 10 desde un IFC FÍSICO**: pórtico HEB 240 ≈22,9 % /
   IPE 360 ≈30,5 %; mixta IPE 400 M_Ed≈333 kN·m, η=0,66; muro C30/37 λ=52 esbelto, N-M≈45 %,
   φ10/200; cimentación σ_ef ≤ R_d (sin despegue, e<B/6), zapata ampliada en predim.;
   equilibrios ~0 %. Los 4 subsistemas **CUMPLEN**, aprovechamientos ≤ 1.

## 4. Criterios de aceptación

- El puente deriva **todos** los elementos (5 barras + 3 superficies) de un único IFC
  físico; grafo de nudos multi-planta coherente.
- Clasificador/enrutador asigna correctamente cada elemento a su módulo y resuelve las
  asociaciones sin Pset.
- Los 4 subsistemas CUMPLEN reproduciendo el caso 10 (diferencias pequeñas documentadas);
  equilibrios ~0 %.
- Entregables completos y plugin reempaquetado (acumulativo) al **siguiente minor**.

## 5. Entregables

`generate_casoR4_ifc.py` + `caso-R4.ifc` + `validacion-IFC.txt`, `modelo_neutro.json`,
`clasificacion.json`, `resumen_edificio.json`, `verificacion_*.json` por subsistema,
memoria Word integrada y diagramas. Resultado de **predimensionado**, a revisar y firmar
por técnico competente; NDP marcados `[confirmar AN]`.
