# Caso 8 — Losa de cimentación (raft) multipilar sobre lecho elástico (EC2 + EC7)

> Octavo peldaño del programa. Antes de empezar, lee
> `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md` y
> `CHANGELOG-plugin.md`. Trabaja con el agente `ingeniero-estructurista`.
> Plugin de partida: **motor-calculo-estructural v0.9.0** (en el caso 7 quedó
> resuelta la lectura ortodoxa de los muros —alzado/espesor/material de la
> `IfcStructuralSurfaceMember` y carga de cabeza de `IfcStructuralPointAction`—,
> la esbeltez EC2 por columna modelo y la estabilidad EC7 DA-2\*).

## 1. Contexto y objetivo

Se entrega un **modelo IFC ortodoxo** (`caso-08.ifc`) con **una losa de
cimentación (raft)** sobre la que descargan **varios pilares**, apoyada en un
**lecho elástico de Winkler**. Es el siguiente peldaño de la cadena
pilar→cimiento del caso 5: de **una zapata con un pilar** a una **losa con varios
pilares** (placa Winkler multipilar, con **asiento diferencial**).

Doble objetivo, como en cada peldaño:

- **Calcular** la losa de cimentación con el motor (`cimentaciones`, módulo
  `raft`) y validar contra los criterios.
- **Cerrar la siguiente brecha**: dar a `cimentaciones/solver_raft.py` una **vía
  ortodoxa** que lea la losa de la `IfcStructuralSurfaceMember`, identifique los
  **pilares** (barras verticales) y baje sus **cargas de cabeza**
  (`IfcStructuralPointAction`), reconstruyendo el **lecho elástico** de la rigidez
  de los nodos de borde (como el `ks` del caso 5), generalizado a la malla
  multipilar; **manteniendo el Pset como respaldo**.

## 2. Descripción del modelo (lo que contiene el IFC)

- **Losa de cimentación C30/37**, **BX × LY = 6,0 × 4,0 m**, canto **0,60 m**.
  `IfcStructuralSurfaceMember` horizontal (z = 0; `IfcFaceSurface`/`IfcPolyLoop`,
  4 esquinas; `Thickness = 0,60`) + material por `IfcRelAssociatesMaterial`.
- **Retícula de 6 pilares** C30/37, sección **0,40 × 0,40 m**, en una malla 3 × 2
  (x = {1, 3, 5}, y = {1, 3}). Cada pilar es una `IfcStructuralCurveMember`
  vertical (z = 0 → 3,0) + `IfcMaterialProfileSet` → `IfcRectangleProfileDef`.
- **Lecho elástico (Winkler)**: módulo de balasto **ks = 40 MN/m³**, expresado
  como **rigidez de muelle** en los 4 nodos de esquina de la losa
  (`IfcStructuralPointConnection` + `IfcBoundaryNodeCondition`,
  `TranslationalStiffnessZ = ks·(BX/2)·(LY/2)`). Resistencia de cálculo del
  terreno **R_d = 300 kPa** como dato geotécnico.
- **Cargas en cabeza de cada pilar** (gravedad −Z), por `IfcStructuralPointAction`
  + `IfcStructuralLoadSingleForce` (misma pauta ortodoxa que el pilar del caso 5):
  - Pilares de **esquina** (P11, P31, P12, P32): `N_G` = 550 kN, `N_Q` = 180 kN.
  - Pilares **centrales** (P21, P22): `N_G` = 850 kN, `N_Q` = 300 kN.
  - El mayor axil central induce **asiento diferencial** centro–borde.
- **Datos sin entidad IFC estándar** (se mantienen como Pset, igual que el
  R_d/ks del caso 5 y los conectores/chapa del caso 6): `Pset_Estructurando_Suelo`
  (R_d, ks) y, como **respaldo** del solver actual, `Pset_Estructurando_Losa` y
  `Pset_Estructurando_Pilar_1..6`.

**El IFC es ortodoxo**: entidades estándar para la losa (superficie), los pilares
(barras con sección rectangular), los apoyos (lecho elástico) y las cargas de
cabeza; los únicos datos no estándar son R_d/ks (geotécnicos). Ver
`validacion-IFC.txt`.

## 3. Brecha conocida (lo que hay que corregir) — raft ortodoxo

Con el plugin v0.9.0:

- El parser genérico `laminas/ifc_to_model_3d.py` **ya lee** la losa como
  superficie (canto, material, esquinas), los 6 pilares como barras verticales
  (`tipo = pilar`, sección `IfcRectangleProfileDef`) y las cargas de cabeza están
  disponibles como `IfcStructuralPointAction` (igual que el caso 5).
- `cimentaciones/solver_raft.py` **todavía lee** la geometría de la losa, los
  pilares y sus cargas de `Pset_Estructurando_Losa` / `_Pilar_*`. Hay que **añadir
  una vía ortodoxa** (`parse_ortodoxo()` + `parse_auto()`, igual que el caso 5 en
  `solver_zapata.py`) que:
  1. lea la **losa** (BX, LY, canto = `Thickness`, material) de la
     `IfcStructuralSurfaceMember` horizontal;
  2. identifique los **pilares** (barras verticales, `tipo = pilar`), su **lado**
     de la sección rectangular y su **pie** (centro de carga) en la huella;
  3. baje la **carga de cabeza** (N_G, N_Q) de cada pilar de los
     `IfcStructuralPointAction`;
  4. reconstruya el **lecho elástico** `ks` de la rigidez de los
     `IfcBoundaryNodeCondition` (`TranslationalStiffnessZ` / área tributaria de
     esquina), y tome **R_d** del `Pset_Estructurando_Suelo`;
  **manteniendo el Pset como respaldo** (igual que casos 1–7).

Corregir de forma **acotada**, sin romper los IFC con Psets ni los casos 2–7.
Anotar en `CHANGELOG-plugin.md` y subir el plugin a **0.9.1** (patch) o **0.10.0**
(minor) según el alcance.

## 4. Criterios de aceptación

1. **Modelo neutro** con material C30/37, la superficie horizontal (BX = 6,0,
   LY = 4,0, t = 0,60) y los 6 pilares con su sección y carga de cabeza (G y Q).
2. **Equilibrio**: Σ reacciones del lecho (ELU) = carga total aplicada (cabezas
   de pilar + peso propio de la losa), error ~0 %.
3. **Terreno (EC7)**: presión de contacto (Winkler) con **presión media ≤ R_d**;
   se reporta el **asiento diferencial** centro–borde y el pico de presión como
   envolvente (no como valor de diseño, igual criterio que los picos singulares de
   los casos 3–5).
4. **EC2 de la losa**: flexión por bandas (momentos en las dos direcciones, vano y
   sobre pilares con el pico de hogging acotado), **punzonamiento** de cada pilar
   (6.4, con el axil del pilar), cortante, **fisuración con el φ realmente
   dispuesto** y armadura principal en la **capa exterior** (lección casos 3–7);
   aprovechamientos ≤ 1.
5. **Memoria** Word y diagramas (planta de la losa con pilares, mapas de momentos
   Mx/My, mapa de presiones de contacto y mapa de asientos).

## 5. Entregables del hilo

- Parser/solver de `cimentaciones` (raft) ampliado a la lectura ortodoxa + plugin
  reempaquetado **v0.9.1/0.10.0** y `CHANGELOG-plugin.md` actualizado.
- En `caso-08-losa-cimentacion/`: `modelo_neutro.json`, `verificacion.json`,
  memoria y diagramas.
- `REPOSITORIO-aprendizaje.md`: lección del caso 8 (raft ortodoxo multipilar;
  asiento diferencial; placa Winkler) y fila de métricas.
- **Caso 9 preparado**: `caso-09-cimentacion-profunda/ENUNCIADO.md` + su IFC
  ortodoxo (pilote + encepado + pantalla anclada; `pilotes` +
  `bielas-tirantes` + `muros-contencion`) con su generador y validación.

## 6. Cómo ejecutar (orientación)

```bash
# 1) (ya hecho) generar el IFC del caso:  python3 generate_caso08_ifc.py
# 2) tras ampliar el parser/solver a la lectura ortodoxa:
cd <plugin>/scripts/cimentaciones
python3 run_all_raft.py proyecto-caso08 <ruta>/caso-08.ifc
```

> Recuerda: la malla fina de la placa Winkler es lenta en el sandbox (ejecuta
> solver / verificación / mapas por separado si el orquestador supera 45 s). No
> uses el pico singular de presión/momento como esfuerzo de diseño. Resultado de
> **predimensionado**, a revisar y firmar por técnico competente; marca
> `[confirmar AN]` los NDP.
