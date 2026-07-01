# Caso 5 — Soporte de hormigón + zapata aislada (`cimentaciones` zapata, EC2 + EC7)

> Quinto peldaño del programa. Antes de empezar, lee
> `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md` y
> `CHANGELOG-plugin.md`. Trabaja con el agente `ingeniero-estructurista`.
> Plugin de partida: **motor-calculo-estructural v0.6.0** (el parser de
> `laminas` ya lee superficies ortodoxas planas e **inclinadas** con apoyos de
> borde; la sección rectangular de pilar `IfcRectangleProfileDef` se resuelve
> vía `perfiles_db`; el módulo `cimentaciones` resuelve la zapata aislada sobre
> lecho elástico Winkler con esfuerzos de placa + EC7 + EC2).

## 1. Contexto y objetivo

Se entrega un **modelo IFC ortodoxo** (`caso-05.ifc`) de un **soporte de
hormigón con su zapata aislada**, encadenados (pilar → cimiento) y apoyados en
un **lecho elástico (Winkler, EC7)**. Doble objetivo:

1. **Calcular** la cimentación con el módulo `cimentaciones` (zapata): **bajada
   de carga** del pilar a la zapata, **presiones de contacto** del terreno por
   Winkler (presión = k_s·asiento), comprobaciones **geotécnicas EC7**
   (hundimiento; sin tracción con e < B/6) y **armado EC2** de la zapata
   (flexión + punzonamiento del pilar), con flecha/asiento, validación y memoria.
2. **Cerrar la siguiente brecha del motor**: leer la **cadena pilar→cimiento
   ortodoxa** (pilar `IfcStructuralCurveMember` con `IfcRectangleProfileDef`;
   zapata `IfcStructuralSurfaceMember`/`IfcFaceSurface`; carga en **cabeza de
   pilar** por `IfcStructuralPointAction`+`IfcStructuralLoadSingleForce`; **lecho
   elástico** por `IfcBoundaryNodeCondition` con rigidez de muelle), en lugar del
   `Pset_Estructurando_Zapata`/`Pset_Estructurando_Carga_Pilar` que usa hoy
   `solver_zapata.py`.

## 2. Descripción del modelo (lo que contiene el IFC)

- **Pilar** de hormigón **C30/37**, sección **0,40 × 0,40 m**, altura **3,0 m**,
  arrancando del centro de la zapata `(1,25; 1,25; 0)` hasta la cabeza
  `(1,25; 1,25; 3,0)`. `IfcStructuralCurveMember` + `IfcEdge` (nodos base/cabeza)
  + `IfcMaterialProfileSet` → `IfcMaterialProfile` → `IfcRectangleProfileDef`.
- **Zapata aislada** **C30/37**, **B × B = 2,5 × 2,5 m**, canto **0,60 m**.
  `IfcStructuralSurfaceMember` (`Thickness=0,60`) con representación
  `IfcFaceSurface`/`IfcPolyLoop` (4 esquinas en z = 0) + material por
  `IfcRelAssociatesMaterial`.
- **Lecho elástico (Winkler)**: el apoyo del terreno se expresa como **resortes
  verticales** en los nodos de la zapata, mediante `IfcStructuralPointConnection`
  + `IfcBoundaryNodeCondition` con rigidez `TranslationalStiffnessZ`
  (`IfcLinearStiffnessMeasure`, N/m) = k_s·área tributaria. **Módulo de balasto
  k_s = 40 MN/m³**. La **resistencia de cálculo del terreno R_d = 250 kPa** se
  aporta como **dato geotécnico** (`Pset_Estructurando_Suelo`): no existe entidad
  IFC estándar de análisis para la capacidad portante del suelo.
- **Cargas en cabeza de pilar** (gravedad −Z): `IfcStructuralLoadGroup` (G, Q) +
  `IfcStructuralPointAction` + `IfcStructuralLoadSingleForce`:
  **G: N = −700 kN, M_x = 80 kN·m** (excentricidad); **Q: N = −250 kN**
  `[confirmar AN/zona]`.

**El IFC es ortodoxo** (entidades estándar; el único dato no estándar es el
geotécnico R_d/k_s, inherente al problema). Ver `validacion-IFC.txt`.

## 3. Brecha conocida (lo que hay que corregir) — cadena pilar→cimiento ortodoxa

Con el plugin v0.6.0:

- El parser genérico `laminas/ifc_to_model_3d.py` **ya lee** el pilar como barra
  vertical (`tipo="pilar"`, sección `0,40×0,40` desde `IfcRectangleProfileDef`),
  la zapata como superficie (esquinas z = 0, espesor, material) y los nodos.
  *Verificado.*
- `cimentaciones/solver_zapata.py` **todavía lee** B, L, canto, malla, k_s, R_d,
  posición del pilar y cargas (N, M_x) de `Pset_Estructurando_Zapata` /
  `Pset_Estructurando_Carga_Pilar`. Hay que **añadir una vía ortodoxa** que:
  1. tome la **geometría de la zapata** del modelo neutro estándar (superficie:
     B, L, canto, material);
  2. resuelva la **cadena pilar→cimiento**: identificar el pilar (barra vertical),
     su lado (sección rectangular) y su posición en planta (pie del pilar = centro
     de carga), y **bajar la carga de cabeza** (N + M_x del
     `IfcStructuralPointAction`) al plano de la zapata;
  3. reconstruya el **lecho elástico Winkler** a partir de la rigidez de
     `IfcBoundaryNodeCondition` (k_s = k_nodo / área tributaria) o del dato k_s;
  4. lea **R_d** del dato geotécnico;
  **manteniendo el Pset como respaldo** (igual que casos 1–4).

Corregir de forma **acotada** (cadena pilar→cimiento ortodoxa + lecho elástico
de borde), sin romper la lectura de los IFC con Psets ni de los casos 2–4.
Anotar en `CHANGELOG-plugin.md` y subir el plugin a **0.6.1** (patch) o **0.7.0**
(minor) según el alcance.

## 4. Criterios de aceptación

1. **Modelo neutro** del IFC ortodoxo con: material C30/37, 1 zapata (C30/37,
   t = 0,60 m, 2,5 × 2,5 m, 4 esquinas z = 0), 1 pilar (sección 0,40 × 0,40 m,
   vertical), cargas de cabeza G/Q (N, M_x) y el lecho elástico (k_s).
2. **Bajada de carga (cadena pilar→cimiento)**: el axil que llega a la zapata =
   N de cabeza + peso propio de la zapata; reparto de presiones por Winkler
   coherente con la excentricidad e = M/N.
3. **EC7 (terreno)**: presión máxima de contacto σ_max ≤ R_d = 250 kPa
   (hundimiento); **sin tracción** (e < B/6 = 0,417 m → toda la base comprimida);
   asiento dentro de rango. Aprovechamientos ≤ 1.
4. **EC2 (zapata)**: armadura de flexión de la zapata (momento en la cara del
   pilar) y **punzonamiento** del pilar (EC2 6.4) dentro de rangos; fisuración con
   el diámetro dispuesto.
5. **Equilibrio**: Σ reacciones del lecho (k_s·δ) = N total aplicado (cabeza +
   peso propio), error < 1 %. Validación de placa (autodiagnóstico MITC4) OK.
6. **Memoria** Word y diagramas (mapa de presiones de contacto, momentos de la
   zapata, asiento/deformada).

## 5. Entregables del hilo

- Parser/solver de `cimentaciones` (zapata) ampliado (cadena pilar→cimiento
  ortodoxa + lecho elástico de borde) + plugin reempaquetado **v0.6.1/0.7.0** y
  `CHANGELOG-plugin.md` actualizado.
- En `caso-05-soporte-zapata/`: `modelo_neutro.json`, `verificacion.json`,
  memoria y diagramas.
- `REPOSITORIO-aprendizaje.md`: lección del caso 5 (cadena pilar→cimiento; lecho
  elástico) y fila de métricas.
- **Caso 6 preparado**: `caso-06-forjado-mixto/ENUNCIADO.md` + su IFC ortodoxo
  (viga mixta acero-hormigón con forjado colaborante, EC4; sección mixta +
  conexión + fases de construcción) con su generador y validación.

## 6. Cómo ejecutar (orientación)

```bash
# 1) (ya hecho) generar el IFC del caso:  python3 generate_caso05_ifc.py
# 2) tras ampliar el parser/solver zapata a la cadena pilar->cimiento ortodoxa:
cd <plugin>/scripts/cimentaciones
python3 run_all_zapata.py proyecto-caso05 <ruta>/caso-05.ifc
#    zapata sobre lecho elastico: bajada de carga + presiones EC7 + flexion/punzonamiento EC2
#    (carga de cabeza de pilar; Winkler desde la rigidez de los nodos de la zapata)
```

> Recuerda: resultado de **predimensionado**, a revisar y firmar por técnico
> competente; marcar `[confirmar AN]` los NDP.
