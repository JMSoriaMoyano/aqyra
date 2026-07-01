# Caso 7 — Muro de carga (esbeltez EC2) + muro de contención en ménsula (EC7 DA-2*)

> Séptimo peldaño del programa. Antes de empezar, lee
> `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md` y
> `CHANGELOG-plugin.md`. Trabaja con el agente `ingeniero-estructurista`.
> Plugin de partida: **motor-calculo-estructural v0.8.0** (en el caso 6 quedó
> resuelta la lectura ortodoxa de la viga mixta y se añadió IPE 360 al catálogo;
> el parser de `laminas` ya lee superficies de `IfcStructuralSurfaceMember`/
> `IfcFaceSurface` y cargas de cabeza de `IfcStructuralPointAction`).

## 1. Contexto y objetivo

Se entrega un **modelo IFC ortodoxo** (`caso-07.ifc`) con **dos elementos** que el
agente debe **clasificar y enrutar** a módulos distintos (misma pauta
multi-elemento de los casos 2–5):

1. **Muro de carga** → módulo `laminas` (muro de carga): **esbeltez EC2** bajo
   carga vertical excéntrica de cabeza (efectos de segundo orden, columna
   modelo / rigidez nominal).
2. **Muro de contención en ménsula** (T-invertida) → módulo `muros-contencion`:
   **estabilidad geotécnica EC7 DA-2\*** (vuelco EQU, deslizamiento GEO,
   hundimiento GEO por área eficaz B′ de Meyerhof) + **armado EC2** del alzado,
   puntera y talón.

Doble objetivo, como en cada peldaño:

- **Calcular** ambos muros con el motor y validar contra los criterios.
- **Cerrar la siguiente brecha**: dar a `laminas` (muro de carga) y a
  `muros-contencion` una **vía ortodoxa** que lea el alzado/espesor/material de
  la `IfcStructuralSurfaceMember` y la carga de cabeza de los
  `IfcStructuralPointAction`, en lugar de los Psets propios que usan hoy.

## 2. Descripción del modelo (lo que contiene el IFC)

### A) Muro de carga — `laminas` (EC2 esbeltez)

- **Muro de hormigón C25/30**, altura **H = 3,0 m**, espesor **t = 0,20 m**,
  faja de 1,0 m, **arriostrado**. `IfcStructuralSurfaceMember` vertical (plano
  Y = 0; `IfcFaceSurface`/`IfcPolyLoop`, 4 esquinas; `Thickness = 0,20`) +
  material por `IfcRelAssociatesMaterial`.
- **Carga vertical excéntrica de cabeza** (forjado superior), por
  `IfcStructuralPointAction` + `IfcStructuralLoadSingleForce` en el nodo de
  coronación (misma pauta ortodoxa que la carga de cabeza del pilar del caso 5):
  - `Ncab_G` = **250 kN/m** (permanente), `Ncab_Q` = **120 kN/m** (variable),
    con **excentricidad e = 25 mm** → `MomentY = N·e` (6,25 y 3,0 kN·m).
- Apoyos: base empotrada en el plano `[T,T,T]`, coronación arriostrada
  lateralmente `[T,T,F]` (`IfcStructuralPointConnection` +
  `IfcBoundaryNodeCondition`).
- Dato auxiliar `Pset_Estructurando_MuroCarga` (tipo, H, t, ancho, arriostrado,
  excentricidad de cabeza) como respaldo.

### B) Muro de contención en ménsula — `muros-contencion` (EC7 DA-2\*)

- **Hormigón C30/37**; alzado **Hm = 5,0 m**, espesor **0,40 m**; zapata canto
  **0,50 m**, **puntera 1,0 m**, **talón 2,0 m**, **B = 3,40 m**; tierras
  delante **Df = 0,80 m**. El **alzado** es una `IfcStructuralSurfaceMember`
  vertical (plano X = 11,0; `IfcFaceSurface`/`IfcPolyLoop`; `Thickness = 0,40`)
  + material; arranque empotrado en la zapata (`IfcStructuralPointConnection`).
- **Terreno**: relleno granular γ = 19 kN/m³, φ = 30°, c = 0, β = 0 (relleno
  horizontal), δ = 20° (rozamiento muro-terreno), pasivo φ = 30° con fracción
  movilizable 0,5, base φ = 30° sin adherencia, **R_d = 300 kPa**, sin nivel
  freático. **Sobrecarga sobre el relleno q = 10 kPa**.
- **Datos sin entidad IFC estándar** (se mantienen como Pset, igual que el
  R_d/k_s del caso 5 y los conectores/chapa del caso 6, porque **no hay entidad
  de análisis estructural estándar** para la geometría en T de la cimentación ni
  para los parámetros del terreno):
  - `Pset_Estructurando_Muro` (geometría T-invertida).
  - `Pset_Estructurando_Terreno` (γ, φ, c, β, δ, pasivo, base, R_d, freático).
  - `Pset_Estructurando_Carga_Muro_q` (sobrecarga).

**El IFC es ortodoxo**: entidades estándar para los muros (superficies),
materiales, apoyos y la carga axil de cabeza; los únicos datos no estándar son el
terreno y la geometría de la zapata en T. Ver `validacion-IFC.txt`.

## 3. Brecha conocida (lo que hay que corregir) — muros ortodoxos

Con el plugin v0.8.0:

- El parser genérico `laminas/ifc_to_model_3d.py` **ya lee** los dos muros como
  superficies (canto, material, esquinas) y la carga de cabeza está disponible
  como `IfcStructuralPointAction` (igual que el pilar del caso 5).
- `muros-contencion/solver_muro.py` y el muro de carga de `laminas` **todavía
  leen** alzado, espesor, material y cargas de `Pset_Estructurando_Muro` /
  `_MuroCarga` / `_Carga_Muro_q`. Hay que **añadir una vía ortodoxa** que:
  1. tome el **alzado** (altura, espesor = `Thickness`, material) de la
     `IfcStructuralSurfaceMember` vertical;
  2. **clasifique** muro de carga vs muro de contención ménsula (por geometría
     y/o por la presencia de `Pset_Estructurando_Terreno`);
  3. para el **muro de carga**, lea la **carga de cabeza** (N + M = N·e) de los
     `IfcStructuralPointAction` y resuelva la **esbeltez EC2**;
  4. para el **muro de contención**, mantenga la **geometría T y el terreno** en
     Pset (sin entidad estándar) y resuelva la **estabilidad EC7 DA-2\*** + EC2;
  **manteniendo el Pset como respaldo** (igual que casos 1–6).

Corregir de forma **acotada**, sin romper los IFC con Psets ni los casos 2–6.
Anotar en `CHANGELOG-plugin.md` y subir el plugin a **0.8.1** (patch) o **0.9.0**
(minor) según el alcance.

## 4. Criterios de aceptación

1. **Modelo neutro** con materiales C25/30 y C30/37, las 2 superficies verticales
   (muro de carga t = 0,20; muro de contención t = 0,40) y la carga de cabeza
   (G y Q) del muro de carga.
2. **Muro de carga (EC2)**: esbeltez λ vs λ_lim; si λ > λ_lim, efectos de segundo
   orden (momento total M_Ed = M0 + M2); comprobación de la sección (N-M) y
   armado vertical; aprovechamiento ≤ 1.
3. **Muro de contención (EC7 DA-2\*)**: coeficientes de seguridad de **vuelco**,
   **deslizamiento** (con pasivo parcial) y **hundimiento** (σ por área eficaz
   B′ ≤ R_d), todos ≥ 1,0; **sin despegue** excesivo (resultante en el núcleo
   central / e ≤ B/6 o criterio EC7).
4. **Armado EC2** del muro de contención: alzado (ménsula, M en la base), puntera
   y talón, con fisuración con el φ realmente dispuesto y armadura principal en
   la **capa exterior** (lección casos 3–6).
5. **Aprovechamientos ≤ 1**; **memoria(s)** Word y diagramas (empujes, esfuerzos
   del alzado, presiones de contacto; N-M del muro de carga).

## 5. Entregables del hilo

- Parser/solver de `laminas` (muro de carga) y `muros-contencion` ampliados a la
  lectura ortodoxa + plugin reempaquetado **v0.8.1/0.9.0** y `CHANGELOG-plugin.md`
  actualizado.
- En `caso-07-muros/`: `modelo_neutro.json`, `verificacion*.json`, memoria(s) y
  diagramas.
- `REPOSITORIO-aprendizaje.md`: lección del caso 7 (muros ortodoxos; esbeltez
  EC2; estabilidad EC7 DA-2\*) y fila de métricas.
- **Caso 8 preparado**: `caso-08-losa-cimentacion/ENUNCIADO.md` + su IFC ortodoxo
  (losa de cimentación / raft multipilar, `cimentaciones`) con su generador y
  validación.

## 6. Cómo ejecutar (orientación)

```bash
# 1) (ya hecho) generar el IFC del caso:  python3 generate_caso07_ifc.py
# 2) tras ampliar el parser/solver a la lectura ortodoxa:
cd <plugin>/scripts/muros-contencion
python3 run_all_muro.py proyecto-caso07 <ruta>/caso-07.ifc
cd <plugin>/scripts/laminas
python3 run_muro_carga.py proyecto-caso07 <ruta>/caso-07.ifc   # esbeltez EC2
```

> Recuerda: resultado de **predimensionado**, a revisar y firmar por técnico
> competente; marcar `[confirmar AN]` los NDP.
