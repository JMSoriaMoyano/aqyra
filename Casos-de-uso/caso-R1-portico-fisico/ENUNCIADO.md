# Caso R1 — Pórtico físico: el puente IFC físico → modelo analítico

> **Primer peldaño de la Dirección 2** (puente IFC físico → modelo analítico). Corre
> **en paralelo** a la segunda tanda (caso 11+). Antes de empezar, lee
> `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md`,
> `CHANGELOG-plugin.md` y `Hoja-de-ruta_v2_Motor-calculo-estructural.md` (v3.0,
> Dirección 2). Trabaja con el agente `ingeniero-estructurista`.
> Plugin de partida: **motor-calculo-estructural v0.12.0**.

## 1. Contexto y objetivo

Las 11 casos anteriores partieron de **IFC ortodoxo** (dominio de análisis, hecho a
mano: `IfcStructuralCurveMember`/`IfcStructuralSurfaceMember`, acciones y apoyos
explícitos). Pero los entregables BIM **reales** son **IFC físicos**: elementos
constructivos (`IfcColumn`/`IfcBeam`/`IfcWall`/`IfcSlab`/`IfcFooting`…) con
**geometría** (sólidos de barrido), material y sección, estructura espacial
(`IfcBuilding`/`Storey`), pero **sin entidades de análisis y sin cargas**. (El
incidente del visor lo evidenció: el IFC de análisis no tiene geometría que
renderizar; el IFC físico sí, pero no tiene modelo de análisis.)

Se entrega un **pórtico físico** (IFC4): 2 `IfcColumn` (HEB 200) + 1 `IfcBeam`
(IPE 330), S275, con geometría `Body` (`IfcExtrudedAreaSolid`) y estructura espacial.
El objetivo es **construir el puente físico → modelo analítico** y, para poder
**validarlo contra un resultado ya conocido**, la geometría es **idéntica al caso 1**
(luz 6 m, altura 4 m, G=12 / Q=10 kN/m): el puente debe **reproducir el caso 1**.

Doble objetivo:

- **Crear** el módulo `puente_analitico/` que deriva el modelo neutro desde la
  geometría física (ejes, secciones, materiales, **nudos por conectividad**), aplica
  las hipótesis de carga/apoyo y **enruta a `barras`** (reutiliza todo el motor).
- **Validar** que el modelo analítico derivado y la comprobación EC3 coinciden con el
  caso 1 (93,60 kN/apoyo; pilares 32,0 %; dintel 44,6 %).

## 2. Descripción del modelo (lo que contiene el IFC)

Todo según `validacion-IFC.txt`. SI; Z vertical, gravedad −Z. **IFC físico** (no de
análisis):

- **Estructura espacial**: `IfcProject` → `IfcSite` → `IfcBuilding` → `IfcBuildingStorey`.
- **`IfcColumn` ×2** (HEB 200, S275), verticales 4,0 m, en (0,0,0)→(0,0,4) y
  (6,0,0)→(6,0,4); **`IfcBeam` ×1** (IPE 330, S275), horizontal (0,0,4)→(6,0,4).
  Cada uno con **geometría Body** (`IfcExtrudedAreaSolid` barriendo un
  `IfcIShapeProfileDef` a lo largo del eje) y **material/sección** por
  `IfcMaterialProfileSetUsage` → `IfcMaterialProfileSet` → `IfcMaterialProfile`.
- **Sin entidades de análisis ni cargas.** Las **hipótesis** (que en BIM real las pone
  el calculista) van en Pset: carga del dintel `Pset_Estructurando_CargaHipotesis`
  (G=12, Q=10 kN/m, −Z); apoyo de base `Pset_Estructurando_ApoyoBase`
  (cota 0, biarticulado); proyecto `Pset_Estructurando_ProyectoAnalisis`.

> Comprobado: el parser de análisis (`laminas/ifc_to_model_3d`) lee **0 elementos**
> (no hay entidades de análisis). La extracción geométrica recupera los 3 ejes, los
> perfiles HEB 200/IPE 330 y el material S275 (ver `validacion-IFC.txt`).

## 3. Brecha conocida (lo que hay que CREAR)

El plugin v0.12.0 **no sabe leer un IFC físico**. Corrección **estructural** (módulo
nuevo, sin tocar los casos 1–11):

1. **Nuevo módulo `puente_analitico/`** (físico → modelo neutro):
   - **Extracción geométrica**: por cada `IfcColumn`/`IfcBeam` (y, en R2–R4,
     `IfcMember`/`IfcWall`/`IfcSlab`/`IfcFooting`/`IfcPile`), el **eje** = directriz
     del barrido (`ObjectPlacement` compuesto + `ExtrudedDirection`·`Depth`); el
     **perfil** de `IfcMaterialProfileSetUsage`→`IfcIShapeProfileDef` (reutiliza
     `perfiles_db`; geometría del `SweptArea` como respaldo); el **material** del
     profile set. Superficie media y espesor de muros/losas en R2–R3.
   - **Conectividad / nudos**: grafo de uniones por **intersección de ejes con
     tolerancia**, troceo de barras en cruces, **fusión de nudos coincidentes**.
     (R1: ejes limpios que se cortan en (0,0,4) y (6,0,4) → 4 nudos. Los
     **offsets/excentricidades** físico↔analítico se endurecen en R5.)
   - **Apoyos**: inferidos de la cota base / `Pset_Estructurando_ApoyoBase`
     (biarticulado). **Cargas**: el IFC físico no las trae → de
     `Pset_Estructurando_CargaHipotesis` (hipótesis de proyecto).
   - **Salida**: el **mismo modelo neutro estándar** que ya consume el motor →
     **reutiliza el clasificador/enrutador y `barras` (EC3)** sin cambios.
2. **Orquestador** `run_all_real.py` (o reutilizar `run_all_edificio` tras el puente):
   IFC físico → puente → modelo neutro → clasificar/enrutar → resolver → memoria.

Anotar en `CHANGELOG-plugin.md` y subir el plugin al **siguiente minor** (módulo
`puente_analitico/`). *Coordinar la versión con la Dirección 1: si el caso 11 ya tomó
0.13.0, este será 0.14.0.*

## 4. Criterios de aceptación

1. **Puente**: del IFC físico se derivan **3 barras** (2 pilares verticales de acero I
   + 1 dintel horizontal de acero I) y **4 nudos** (por intersección de ejes), con
   perfil (HEB 200/IPE 330), material (S275) y longitudes (4,0 / 6,0 m) correctos.
2. **Enrutado**: el modelo neutro derivado se clasifica y enruta a **`barras` (EC3)**
   exactamente como el caso 1.
3. **Reproduce el caso 1 (validación clave)**: equilibrio **93,60 kN/apoyo** (Σ=187,2
   kN, error ~0 %); pilares **HEB 200 aprov. 32,0 %**; dintel **IPE 330 aprov. 44,6 %**;
   validación cruzada PyNite vs anaStruct OK. Aprovechamientos ≤ 1.
4. **Salidas**: `modelo_neutro.json` (derivado del físico), `verificacion.json`,
   diagramas (momentos/cortantes/axiles/deformada) y memoria. Documentar las
   **hipótesis** de carga/apoyo (no venían en el IFC).

## 5. Entregables del hilo

- Módulo `puente_analitico/` (+ orquestador), plugin reempaquetado y
  `CHANGELOG-plugin.md` actualizado.
- En `caso-R1-portico-fisico/`: `modelo_neutro.json`, `verificacion.json`, memoria
  Word y diagramas.
- `REPOSITORIO-aprendizaje.md`: lección del caso R1 (puente físico→analítico:
  extracción de eje/sección/material y generación de nudos) y fila de métricas.
  **Apertura de la Dirección 2.**

## 6. Cómo ejecutar (orientación)

```bash
# 1) (ya hecho) generar el IFC fisico del caso:  python3 generate_casoR1_ifc.py
# 2) tras crear el puente:
cd <plugin>/scripts && python3 puente_analitico/run_all_real.py <proj> <ruta>/caso-R1.ifc
```

> Recuerda: el puente trabaja sobre **geometría real** (placements compuestos,
> barridos); usa `ifcopenshell.util.placement.get_local_placement` para el eje en
> coordenadas de mundo y `IfcMaterialProfileSetUsage` para perfil/material. El reto es
> la **construcción del grafo de nudos** (tolerancias), no el solver. R1 es **limpio**
> (ejes que se cortan); los offsets se dejan para R5. Escribe el código por heredoc y
> valida con `ast.parse` (INC-04). Empaqueta el `.plugin` excluyendo
> `node_modules`/`__pycache__` (INC-05). Las herramientas de fichero (Read/Write/Edit)
> son la fuente de verdad de la carpeta del proyecto (el shell puede ver copias
> truncadas de ficheros markdown preexistentes — no los edites por shell). Resultado de
> **predimensionado**, a revisar y firmar por técnico competente.
