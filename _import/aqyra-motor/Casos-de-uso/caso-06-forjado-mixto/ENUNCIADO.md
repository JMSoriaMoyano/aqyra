# Caso 6 — Forjado colaborante / viga mixta acero-hormigón (`mixtas`, EC4)

> Sexto peldaño del programa. Antes de empezar, lee
> `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md` y
> `CHANGELOG-plugin.md`. Trabaja con el agente `ingeniero-estructurista`.
> Plugin de partida: **motor-calculo-estructural v0.7.0** (la cadena
> pilar→cimiento ortodoxa y el lecho elástico de borde quedaron resueltos en el
> caso 5; el parser de `barras`/`laminas` ya lee perfiles de
> `IfcMaterialProfileSet`→`IfcIShapeProfileDef` y superficies de
> `IfcStructuralSurfaceMember`/`IfcFaceSurface`).

## 1. Contexto y objetivo

Se entrega un **modelo IFC ortodoxo** (`caso-06.ifc`) de una **viga mixta
acero-hormigón** secundaria, biapoyada, con **forjado colaborante** (chapa
nervada perpendicular a la viga) y **construcción sin apear** (unpropped). Doble
objetivo:

1. **Calcular** la viga mixta con el módulo `mixtas` (EC4): **ancho eficaz** de
   la losa, **M_pl,Rd** por fibras y **M_Rd con grado de conexión**, **conexión a
   cortante** (nº de conectores, grado η), **cortante** del alma, **fase de
   construcción** (el perfil de acero solo bajo el hormigón fresco) y **flecha**
   por fases (n₀ / n_L), con validación y memoria.
2. **Cerrar la siguiente brecha del motor**: leer la viga mixta **ortodoxa** — el
   **perfil de acero** de `IfcMaterialProfileSet`→`IfcIShapeProfileDef`, la
   **losa** de `IfcStructuralSurfaceMember`/`IfcFaceSurface` (canto, material,
   ancho), y las **cargas por fase** de los `IfcStructuralLoadGroup` +
   `IfcStructuralSurfaceAction` — en lugar del `Pset_Estructurando_VigaMixta` /
   `_Cargas_Mixta` que usa hoy `solver_mixta.py`.

## 2. Descripción del modelo (lo que contiene el IFC)

- **Viga de acero IPE 360, S275**, luz **L = 8,0 m**. `IfcStructuralCurveMember`
  horizontal (eje X) + `IfcEdge` (apoyos en x = 0 y x = L) +
  `IfcMaterialProfileSet` → `IfcMaterialProfile` → `IfcIShapeProfileDef` (geometría
  completa: `OverallDepth` 0,360, `OverallWidth` 0,170, `WebThickness` 0,008,
  `FlangeThickness` 0,0127, `FilletRadius` 0,018). Apoyos biapoyados por
  `IfcStructuralPointConnection` + `IfcBoundaryNodeCondition`.
- **Losa colaborante C25/30**, **canto total ht = 0,12 m**, ancho =
  **separación entre vigas SEP = 3,0 m** (ancho tributario).
  `IfcStructuralSurfaceMember` (`Thickness = 0,12`) con representación
  `IfcFaceSurface`/`IfcPolyLoop` (4 esquinas sobre la viga) + material por
  `IfcRelAssociatesMaterial`.
- **Cargas por fase** (gravedad −Z), por `IfcStructuralLoadGroup` +
  `IfcStructuralSurfaceAction` + `IfcStructuralLoadPlanarForce` sobre la losa, con
  la **fase codificada en el nombre del grupo**:
  - Fase **construcción** (el acero solo resiste): `G_construccion` = peso del
    hormigón fresco **2,5 kN/m²**; `Qc_construccion` = sobrecarga de ejecución
    **0,75 kN/m²**.
  - Fase **mixta** (sección mixta): `G2_mixta` = carga muerta adicional
    **1,5 kN/m²**; `Q_mixta` = sobrecarga de uso **3,0 kN/m²** `[confirmar AN]`.
- **Datos sin entidad IFC estándar** (se mantienen como Pset, igual que el
  R_d/k_s del caso 5, porque no existe entidad de análisis estándar para ellos):
  - `Pset_Estructurando_Conectores`: perno **d = 19 mm, h = 100 mm, fu = 450 MPa,
    separación longitudinal 207 mm** (≈ 1 conector por nervio).
  - `Pset_Estructurando_Losa`: chapa nervada **hp = 58, hc = 62, b0 = 100 mm,
    nervios perpendiculares, nr = 1**, `apeado = 0`.

**El IFC es ortodoxo** (entidades estándar; los únicos datos no estándar son los
conectores y la chapa, inherentes al problema). Ver `validacion-IFC.txt`.

## 3. Brecha conocida (lo que hay que corregir) — viga mixta ortodoxa

Con el plugin v0.7.0:

- El parser genérico `laminas/ifc_to_model_3d.py` **ya lee** la viga como barra
  horizontal (sección IPE 360 desde `IfcIShapeProfileDef`, material S275) y la
  losa como superficie (canto, material, esquinas), y las **cargas por fase** de
  los grupos. *Verificado* en `validacion-IFC.txt` (IPE 360 por geometría:
  A ≈ 69,95 cm² frente a 72,73 de catálogo, ≈ 3,8 % menor — INC-06).
- `mixtas/solver_mixta.py` **todavía lee** L, separación, perfil, geometría,
  losa, conectores y cargas de `Pset_Estructurando_VigaMixta` / `_Losa` /
  `_Conectores` / `_Cargas_Mixta`. Hay que **añadir una vía ortodoxa** que:
  1. tome el **perfil de acero** de `IfcMaterialProfileSet`→`IfcIShapeProfileDef`
     (reutilizar `perfiles_db`; **añadir IPE 360 al catálogo** para no perder el
     ~4 % de los acuerdos, INC-06);
  2. tome la **losa** (canto, material, ancho = luz lateral de la superficie) del
     `IfcStructuralSurfaceMember`;
  3. lea las **cargas por fase** de los `IfcStructuralLoadGroup` +
     `IfcStructuralSurfaceAction`, **clasificando construcción vs mixta** por el
     nombre del grupo (`*_construccion` / `*_mixta`);
  4. mantenga los **conectores y la chapa** del Pset (sin entidad estándar);
  **manteniendo el Pset como respaldo** (igual que casos 1–5).

Corregir de forma **acotada** (viga mixta ortodoxa + IPE 360 en catálogo), sin
romper la lectura de los IFC con Psets ni de los casos 2–5. Anotar en
`CHANGELOG-plugin.md` y subir el plugin a **0.7.1** (patch) o **0.8.0** (minor)
según el alcance.

## 4. Criterios de aceptación

1. **Modelo neutro** del IFC ortodoxo con: materiales S275 y C25/30, 1 viga
   (IPE 360, horizontal), 1 losa (C25/30, ht = 0,12 m, ancho 3,0 m) y las cargas
   de las dos fases (construcción y mixta).
2. **Ancho eficaz** b_eff de la losa según EC4 (≤ L/4 y ≤ separación) y **sección
   mixta** (M_pl,Rd por fibras; eje neutro plástico).
3. **Conexión a cortante**: nº de conectores disponibles, **grado de conexión η**
   y **M_Rd** con conexión parcial si η < 1 (`M_Rd = M_a,Rd + η·(M_pl,Rd − M_a,Rd)`,
   η ≥ η_min). Cortante del alma EC3.
4. **Fase de construcción** (sin apear): el perfil de acero solo resiste el peso
   del hormigón fresco + sobrecarga de ejecución (comprobación EC3 del acero).
5. **Flecha** por fases (acero en construcción + mixta con n₀/n_L) frente a los
   límites (L/250 total, L/350 activa — viga mixta).
6. **Aprovechamientos ≤ 1**; **memoria** Word y diagramas (M/V por fase, sección
   mixta, conexión).

## 5. Entregables del hilo

- Parser/solver de `mixtas` ampliado (viga mixta ortodoxa + IPE 360 en catálogo)
  + plugin reempaquetado **v0.7.1/0.8.0** y `CHANGELOG-plugin.md` actualizado.
- En `caso-06-forjado-mixto/`: `modelo_neutro.json`, `verificacion.json`, memoria
  y diagramas.
- `REPOSITORIO-aprendizaje.md`: lección del caso 6 (viga mixta ortodoxa; fases de
  construcción; conexión parcial) y fila de métricas.
- **Caso 7 preparado**: `caso-07-muros/ENUNCIADO.md` + su IFC ortodoxo (muro de
  carga `laminas` + muro de contención ménsula `muros-contencion`, EC7
  estabilidad) con su generador y validación.

## 6. Cómo ejecutar (orientación)

```bash
# 1) (ya hecho) generar el IFC del caso:  python3 generate_caso06_ifc.py
# 2) tras ampliar el parser/solver mixta a la lectura ortodoxa:
cd <plugin>/scripts/mixtas
python3 run_all_mixta.py proyecto-caso06 <ruta>/caso-06.ifc
#    viga mixta: ancho eficaz + M_pl,Rd + grado de conexion + fase construccion + flecha
```

> Recuerda: resultado de **predimensionado**, a revisar y firmar por técnico
> competente; marcar `[confirmar AN]` los NDP.
