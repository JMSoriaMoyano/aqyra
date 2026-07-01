# Caso R2 — Forjado físico: el puente IFC físico → modelo analítico con superficies

> **Segundo peldaño de la Dirección 2** (puente IFC físico → modelo analítico). Corre
> **en paralelo** a la segunda tanda. Antes de empezar, lee
> `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md`,
> `CHANGELOG-plugin.md` y `Hoja-de-ruta_v2_Motor-calculo-estructural.md` (v3.0,
> Dirección 2). Trabaja con el agente `ingeniero-estructurista`.
> Plugin de partida: **motor-calculo-estructural v0.14.0** (`.plugin` acumulativo con
> `puente_analitico/` —caso R1— y `sismico/` —caso 11—).

## 1. Contexto y objetivo

El **caso R1** abrió la Dirección 2: el módulo `puente_analitico/` deriva el modelo
analítico desde un **IFC físico** (entregable BIM real) para **elementos lineales**
(`IfcColumn`/`IfcBeam`): eje = directriz del barrido, perfil de
`IfcMaterialProfileSetUsage`, material, nudos por intersección de ejes, apoyos y cargas
de hipótesis (Pset) → enruta a `barras` (EC3). Reprodujo el caso 1 (93,60 kN/apoyo;
HEB 200 32,0 %; IPE 330 44,6 %).

Pero un forjado real lleva **superficies físicas**: `IfcSlab` (losa) con geometría de
barrido y **espesor en `IfcMaterialLayerSet`**, apoyada sobre vigas. El puente todavía
**no sabe leer superficies**. Este caso **amplía el puente a superficies**: extraer la
**superficie media** y el **espesor** de la losa, resolver la **conectividad
superficie↔barras** y reutilizar `laminas` (losa EC2) + `barras` (EC3) con **reparto por
ancho tributario** (`run_forjado`). Para **validar contra un resultado ya conocido**, la
geometría es **idéntica al caso 2**: el puente debe **reproducir el caso 2**.

Doble objetivo:

- **Ampliar** `puente_analitico/` para derivar del `IfcSlab` la superficie media (footprint
  del barrido + placement a mundo) y el espesor (`IfcMaterialLayerSetUsage` →
  `IfcMaterialLayerSet`, Σ `LayerThickness`; geometría de respaldo), asociar la losa a las
  vigas que la soportan, aplicar la hipótesis de carga de superficie y **enrutar a
  `laminas`+`barras`** (reutiliza todo el motor).
- **Validar** que el modelo derivado y las comprobaciones coinciden con el caso 2
  (m_Ed≈21,15 kN·m/m; vigas IPE 400 ≈26,5 %; reacción por extremo 63,45 kN; equilibrio ~0 %).

## 2. Descripción del modelo (lo que contiene el IFC)

Todo según `validacion-IFC.txt`. SI; Z vertical, gravedad −Z. **IFC físico** (no de
análisis):

- **Estructura espacial**: `IfcProject` → `IfcSite` → `IfcBuilding` → `IfcBuildingStorey`.
- **`IfcSlab` ×1** (C30/37, canto 120 mm), planta rectangular **6,0 × 4,0 m**, con
  **geometría Body** (`IfcExtrudedAreaSolid` que barre el contorno en planta —
  `IfcRectangleProfileDef` 6,0×4,0 — un canto de 0,12 m) y **material/espesor** por
  `IfcMaterialLayerSetUsage` → `IfcMaterialLayerSet` → `IfcMaterialLayer`
  (`LayerThickness`=0,12, material C30/37). Superficie media en z≈−0,06.
- **`IfcBeam` ×2** (IPE 400, S275), paralelas a lo largo de X, **luz 6,0 m**, **separadas
  4,0 m** (en y=0 y y=4,0), con **geometría Body** (`IfcExtrudedAreaSolid` del
  `IfcIShapeProfileDef`) y **material/sección** por `IfcMaterialProfileSetUsage`. La losa
  unidireccional salva los 4,0 m entre vigas.
- **Sin entidades de análisis ni cargas.** Las **hipótesis** (que en BIM real pone el
  calculista) van en Pset: carga de superficie del forjado
  `Pset_Estructurando_CargaHipotesis` (**G=4,5 / Q=3,0 kN/m²**, −Z); apoyos de extremo de
  viga `Pset_Estructurando_ApoyoBase` (cota 0, biarticulado, `Ubicacion=extremos_viga`);
  proyecto `Pset_Estructurando_ProyectoAnalisis`.

> Comprobado: el parser de análisis (`laminas/ifc_to_model_3d`) lee **0 elementos** (no hay
> entidades de análisis). El puente de R1 lee las **2 vigas** (IPE 400, S275) pero **ignora
> la losa** — esa es la brecha de R2. La superficie media (6,0×4,0), el espesor (0,12 m de
> `IfcMaterialLayerSet`) y el material (C30/37) son extraíbles (ver `validacion-IFC.txt`).

## 3. Brecha conocida (lo que hay que CREAR/AMPLIAR)

El módulo `puente_analitico/` (v0.14.0) **no lee superficies físicas**. Ampliación
**estructural pero acotada** (sin tocar los casos 1–11 ni romper R1):

1. **Ampliar `puente_analitico/` a superficies** (físico → modelo neutro):
   - **Extracción de superficie**: por cada `IfcSlab` (y, en R3, `IfcWall`/`IfcFooting`),
     la **superficie media** = footprint del `IfcExtrudedAreaSolid` (esquinas del
     `IfcRectangleProfileDef`/`IfcArbitraryClosedProfileDef`) llevado a coordenadas de
     mundo con el placement (`ifcopenshell.util.placement.get_local_placement`) y la cota
     media del barrido; el **espesor** de `IfcMaterialLayerSetUsage` → `IfcMaterialLayerSet`
     (Σ `LayerThickness`; geometría como respaldo); el **material** de
     `IfcRelAssociatesMaterial`→`IfcMaterial`. Reutilizar la extracción de eje/perfil/material
     de barras de R1 para las vigas.
   - **Conectividad superficie↔barras**: asociar la losa a las **vigas que la soportan**
     (vigas dentro/bajo el contorno de la superficie, por proximidad en planta — como las
     asociaciones del clasificador del caso 10), generar los **nudos** y, si procede, los
     apoyos de borde.
   - **Apoyos**: extremos de viga (Pset/cota base, biarticulado). **Cargas**: el IFC físico
     no las trae → **carga de superficie** de `Pset_Estructurando_CargaHipotesis`
     (G/Q kN/m², −Z).
   - **Salida**: el **mismo modelo neutro estándar** (superficie + barras) que ya consume el
     motor → **reutilizar el clasificador/enrutador, `laminas` (EC2) y `barras` (EC3)** con
     el **reparto losa→vigas por ancho tributario** del caso 2 (`run_forjado`).
2. **Orquestador**: ampliar `puente_analitico/run_all_real.py` (IFC físico con superficies →
   puente → modelo neutro → clasificar/enrutar → resolver → memoria), o un
   `run_all_real_forjado.py` análogo que encadene el puente con `laminas/run_forjado`.

Anotar en `CHANGELOG-plugin.md` y subir el plugin al **siguiente minor** (ampliación de
`puente_analitico/` a superficies). *Coordinar la versión con la Dirección 1: si el caso 12
(pretensado) ya tomó 0.15.0, este será 0.16.0. El `.plugin` es **acumulativo**: partir del
v0.14.0 actual (que ya contiene `sismico/` + el `puente_analitico/` de R1) y AÑADIR encima.*

## 4. Criterios de aceptación

1. **Puente (superficie + barras)**: del IFC físico se derivan **1 superficie** (losa
   C30/37, t=120 mm, 6,0×4,0 m, material y espesor del `IfcMaterialLayerSet`) y **2 barras**
   (vigas IPE 400 horizontales de acero I, L=6,0 m), con la losa asociada a las dos vigas
   (conectividad) y los apoyos de extremo de viga.
2. **Enrutado**: el modelo neutro derivado se clasifica y enruta a **`laminas` (losa EC2) +
   `barras` (EC3)** con reparto por ancho tributario, exactamente como el caso 2.
3. **Reproduce el caso 2 (validación clave)**: losa C30/37 t=120 mm, m_Ed≈**21,15 kN·m/m**
   (φ10/125, w_k≈0,18 mm, flecha ~39 %); reparto G=9,0 / Q=6,0 kN/m; **vigas IPE 400 aprov.
   ≈26,5 %**; reacción por extremo ≈**63,45 kN**; **equilibrio global ~0 %**
   (carga de superficie ELU 10,575·24 = 253,8 kN = Σ reacciones); validación cruzada OK.
   Aprovechamientos ≤ 1.
4. **Salidas**: `modelo_neutro.json` (derivado del físico, con superficie + barras),
   `verificacion.json`, diagramas (losa: momento/sección; vigas: esfuerzos; planta del
   forjado) y memoria. Documentar las **hipótesis** de carga/apoyo y la **extracción de
   superficie media + espesor de `IfcMaterialLayerSet`**.

## 5. Entregables del hilo

- Ampliación de `puente_analitico/` (lectura de superficies + conectividad superficie↔barras)
  (+ orquestador), plugin reempaquetado y `CHANGELOG-plugin.md` actualizado.
- En `caso-R2-forjado-fisico/`: `modelo_neutro.json`, `verificacion.json`, memoria Word y
  diagramas.
- `REPOSITORIO-aprendizaje.md`: lección del caso R2 (puente físico→analítico de superficies:
  superficie media + espesor de `IfcMaterialLayerSet` + conectividad superficie↔barras) y fila
  de métricas.

## 6. Cómo ejecutar (orientación)

```bash
# 1) (ya hecho) generar el IFC fisico del caso:  python3 generate_casoR2_ifc.py
# 2) tras ampliar el puente a superficies:
cd <plugin>/scripts && python3 puente_analitico/run_all_real.py <proj> <ruta>/caso-R2.ifc
```

> Recuerda: el puente trabaja sobre **geometría real**; usa
> `ifcopenshell.util.placement.get_local_placement` para el placement a mundo, el footprint
> del `IfcExtrudedAreaSolid` para la superficie media y `IfcMaterialLayerSetUsage` →
> `IfcMaterialLayerSet` para el espesor (geometría de respaldo). El reto es la **superficie
> media + la conectividad superficie↔barras**, no el solver. R2 es **limpio** (losa y vigas
> idealizadas coplanares); los **offsets/excentricidades** eje de viga ↔ plano medio de la
> losa se dejan para R5 (INC-07). La **descripción de `plugin.json` debe ser ≤ 500
> caracteres** (validación de instalación). Escribe el código por heredoc y valida con
> `ast.parse` (INC-04). Empaqueta el `.plugin` excluyendo `node_modules`/`__pycache__`
> (INC-05) y **parte del v0.14.0 actual para no revertir `sismico/` ni R1**. Las herramientas
> de fichero (Read/Write/Edit) son la fuente de verdad de la carpeta del proyecto (el shell
> puede ver copias truncadas de ficheros markdown preexistentes — no los edites por shell).
> Resultado de **predimensionado**, a revisar y firmar por técnico competente; NDP marcados
> `[confirmar AN]`.
