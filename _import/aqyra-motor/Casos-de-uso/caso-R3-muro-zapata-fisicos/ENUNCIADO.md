# Caso R3 — Muro + zapata físicos: el puente IFC físico → modelo analítico con superficies VERTICALES + cimientos

> **Tercer peldaño de la Dirección 2** (puente IFC físico → modelo analítico). Antes de
> empezar, lee `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md`,
> `CHANGELOG-plugin.md` y `Hoja-de-ruta_v2_Motor-calculo-estructural.md` (v3.0,
> Dirección 2). Trabaja con el agente `ingeniero-estructurista`.
> Plugin de partida: **motor-calculo-estructural v0.17.0** (`.plugin` acumulativo con
> `puente_analitico/` —casos R1 y R2—, `sismico/` —caso 11— y `pretensado/` —casos 12–13—).
> R3 toma el **siguiente minor = v0.18.0**.

## 1. Contexto y objetivo

El **caso R1** abrió la Dirección 2: `puente_analitico/` deriva el modelo analítico desde
un **IFC físico** (entregable BIM real) para **elementos lineales** (`IfcColumn`/`IfcBeam`).
El **caso R2** lo amplió a **superficies horizontales** (`IfcSlab`, losa): superficie media
del footprint + espesor del `IfcMaterialLayerSet` + conectividad superficie↔vigas, y reprodujo
el caso 2.

Pero una cimentación real lleva **superficies VERTICALES** (`IfcWall`, muros) y **cimientos**
(`IfcFooting`, zapatas). El puente de R2 trataba **todo sólido barrido como losa horizontal**
(footprint en planta + cota media): para un `IfcWall` extruido en +Z eso es **degenerado**
(devuelve una superficie horizontal del grosor de planta a media altura, no el **plano medio
vertical**). Esa es la **brecha de R3**. Este caso amplía el puente a:

- **Clasificación de superficies por orientación** (vertical/horizontal) por la **normal del
  plano medio**, no solo por las z de las esquinas.
- **Plano medio del `IfcWall`**: rectángulo VERTICAL (longitud L_w × altura H = profundidad de
  extrusión), colapsando el lado fino de la huella a su línea central.
- **Footprint y canto del `IfcFooting`** (horizontal), como en R2.
- **Cadena muro→cimiento**: asociar el muro a la zapata que lo soporta (pie del muro sobre la
  huella, por proximidad en planta + cota), como pilar↔zapata del caso 10.

Para **validar contra resultados ya conocidos**, la geometría y los datos son los de los
casos **7 (muro de carga)** y **5 (zapata)**: el puente debe **reproducir ambos**.

## 2. Descripción del modelo (lo que contiene el IFC)

Todo según `validacion-IFC.txt`. SI; Z vertical, gravedad −Z. **IFC físico** (no de análisis):

- **Estructura espacial**: `IfcProject` → `IfcSite` → `IfcBuilding` → `IfcBuildingStorey`.
- **`IfcWall` ×1** (muro de carga C25/30): alzado **H=3,0 m**, espesor **t=0,20 m**, faja de
  cálculo **L=1,0 m** en planta. **Geometría Body** (`IfcExtrudedAreaSolid`, perfil en planta =
  rectángulo 1,0×0,20, **extrusión vertical +Z de 3,0 m**) con su placement. Material/espesor por
  `IfcMaterialLayerSetUsage` → `IfcMaterialLayerSet` (Σ `LayerThickness`=0,20; C25/30). El
  **plano medio es VERTICAL** (1,0 × 3,0). Reproduce el muro de carga del **caso 7**.
- **`IfcFooting` ×1** (zapata C30/37): **2,5 × 2,5 m**, canto **0,60 m**. **Geometría Body**
  (`IfcExtrudedAreaSolid`, huella 2,5×2,5, extrusión +Z de 0,60). Material/canto por
  `IfcMaterialLayerSet`. El **plano medio es HORIZONTAL** (footprint) + canto. Reproduce la
  zapata del **caso 5** (lecho Winkler, EC7 área eficaz + EC2).
- **El muro apoya sobre la zapata**: pie del muro en z=0,60 (cara superior de la huella),
  centrado en planta (offsets idealizados limpios/coplanares).
- **Sin entidades de análisis ni cargas.** Las **hipótesis** (que en BIM real pone el calculista)
  van en Pset:
  - `Pset_Estructurando_CargaHipotesis` en el muro: carga de cabeza **N_G=250 / N_Q=120 kN/m**
    con excentricidad **e=25 mm** (M = N·e), faja 1,0 m (caso 7).
  - `Pset_Estructurando_Suelo` en la zapata: **k_s=40 MN/m³, R_d=250 kPa** (caso 5).
  - `Pset_Estructurando_Zapata`: bajada de carga del soporte equivalente **N_G=700 / N_Q=250 kN +
    M_G=80 kN·m**, lado de pilar y malla (geometría caso-5 que no se deriva limpiamente de la faja
    de muro de 1,0 m).
  - `Pset_Estructurando_ApoyoBase`: cotas base del muro y de la zapata.
  - `Pset_Estructurando_ProyectoAnalisis`: metadatos.

> **Qué sale de GEOMETRÍA vs de PSET.** Del físico se derivan: plano medio del muro (L_w×H) y su
> espesor (`IfcMaterialLayerSet`); huella y canto de la zapata (`IfcFooting`+`IfcMaterialLayerSet`);
> material/fck; cadena muro→cimiento. Del Pset (hipótesis del calculista, no existen en un IFC
> físico): carga de cabeza del muro, terreno (k_s, R_d), bajada de carga a la zapata, cotas de apoyo.

## 3. Brecha conocida (lo que hay que CREAR/AMPLIAR)

Ampliación **estructural pero acotada** de `puente_analitico/` (sin tocar los casos 1–13 ni
romper R1/R2):

1. **Clasificar superficies por orientación** (vertical/horizontal) por la normal del plano medio
   y el aspecto del footprint (un lado ≈ espesor → muro fino).
2. **Plano medio vertical del `IfcWall`**: 4 esquinas verticales de base a cabeza (NO a media
   altura), centradas en el lado fino. `IfcSlab`/`IfcFooting` siguen saliendo horizontales
   (R1/R2 intactos).
3. **Extraer espesor/canto** del `IfcMaterialLayerSet`, material/fck, y el lecho Winkler (k_s de
   Pset).
4. **Cadena muro↔zapata** (`zapata_asociada`/`muros_asociados`).
5. **Orquestador** `run_all_real_muro_zapata.py`: IFC físico → puente → clasificar/enrutar →
   construir los dicts `model` de muro y zapata desde neutro+Psets → `solver_muro.solve()` +
   `verificacion_muro` (láminas) y `solver_zapata.solve()` + `verificacion_zapata.verificar()`
   (cimentaciones), **sin** `parse_ortodoxo`/`run_muro_carga`/`run_all_zapata` (releen entidades
   de análisis que el IFC físico no tiene) → equilibrios → diagramas → memoria.

Anotar en `CHANGELOG-plugin.md`, subir el plugin a **v0.18.0** y registrar la lección + métricas
en `REPOSITORIO-aprendizaje.md`. El `.plugin` es **acumulativo**.

## 4. Criterios de aceptación

1. **Puente (superficies verticales + cimientos)**: del IFC físico se derivan **1 muro VERTICAL**
   (C25/30, plano medio 1,0×3,0, t=0,20 del `IfcMaterialLayerSet`) y **1 zapata HORIZONTAL**
   (C30/37, huella 2,5×2,5, canto 0,60), clasificadas por orientación, con la **cadena
   muro→cimiento** resuelta.
2. **Enrutado**: el modelo neutro derivado se enruta a **láminas (muro EC2)** + **cimentaciones
   (zapata EC7/EC2)**, reutilizando los solvers sin cambios.
3. **Reproduce el caso 7 (muro)**: λ=52 > λ_lim → **ESBELTO**; M_Ed = M0Ed+M2 ≈ **31,3 kN·m/m**;
   **φ10/200 c/cara**; **N-M ≈ 47 %**; equilibrio vertical ELU ~0,000 %.
4. **Reproduce el caso 5 (zapata)**: EC7 **σ_ef ≤ R_d** (sin despegue, e<B/6); EC2
   flexión/punzonamiento/fisuración; equilibrio del lecho ~0 %; cadena muro→cimiento coherente.
   Aprovechamientos ≤ 1.
5. **Salidas**: `caso-R3.ifc`, `validacion-IFC.txt`, `modelo_neutro.json`, `clasificacion.json`,
   `verificacion.json`, diagramas (.png) y memoria Word. Documentar las **hipótesis** y la
   **extracción del plano medio del muro + canto de la zapata + espesor del `IfcMaterialLayerSet`**.

## 5. Entregables del hilo

- Ampliación de `puente_analitico/` (clasificación por orientación + plano medio del `IfcWall` +
  cadena muro→cimiento) + orquestador `run_all_real_muro_zapata.py` + memoria, plugin reempaquetado
  (**v0.18.0**) y `CHANGELOG-plugin.md` actualizado.
- En `caso-R3-muro-zapata-fisicos/`: `generate_casoR3_ifc.py`, `caso-R3.ifc`, `validacion-IFC.txt`,
  `modelo_neutro.json`, `clasificacion.json`, `verificacion.json`, memoria Word y diagramas.
- `REPOSITORIO-aprendizaje.md`: lección del caso R3 (puente físico→analítico de superficies
  verticales y cimientos: plano medio del `IfcWall`, huella/canto del `IfcFooting`, clasificación
  por orientación, cadena muro→cimiento) y fila de métricas.

## 6. Cómo ejecutar (orientación)

```bash
# 1) generar el IFC fisico del caso:
python3 generate_casoR3_ifc.py
# 2) puente + muro + zapata de extremo a extremo:
cd <plugin>/scripts && python3 puente_analitico/run_all_real_muro_zapata.py <proj> <ruta>/caso-R3.ifc
# 3) memoria:
python3 puente_analitico/generate_memoria_real_muro_zapata.py <proj>
```

> Recuerda: el puente trabaja sobre **geometría real**; usa
> `ifcopenshell.util.placement.get_local_placement` para el placement a mundo y `get_axis2placement`
> para la Position del sólido. El reto es la **clasificación de superficies por orientación**, el
> **plano medio del muro** y la **cadena muro→cimiento**, no el solver. R3 es **limpio** (muro y
> zapata idealizados coplanares); los offsets eje↔plano medio se dejan para R5 (INC-07). La
> descripción de `plugin.json` debe ser **≤ 500 caracteres**. Escribe el código por heredoc y valida
> con `ast.parse` (INC-04). Empaqueta el `.plugin` excluyendo `node_modules`/`__pycache__` (INC-05)
> y **parte del v0.17.0 actual para no revertir `sismico/`/`pretensado/`/R1/R2**. Resultado de
> **predimensionado**, a revisar y firmar por técnico competente; NDP marcados `[confirmar AN]`.
