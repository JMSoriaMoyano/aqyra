# Caso 9 — Cimentación profunda: pilote + encepado + pantalla anclada (EC7 + EC2)

> Noveno peldaño del programa. Antes de empezar, lee
> `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md` y
> `CHANGELOG-plugin.md`. Trabaja con el agente `ingeniero-estructurista`.
> Plugin de partida: **motor-calculo-estructural v0.10.0** (en el caso 8 quedó
> resuelta la lectura ortodoxa de la **losa de cimentación (raft) multipilar** —losa
> de la `IfcStructuralSurfaceMember`, pilares como barras verticales, cargas de cabeza
> de `IfcStructuralPointAction`, lecho `ks` de los `IfcBoundaryNodeCondition`—, la
> placa Winkler multipilar con **asiento diferencial** y el punzonamiento con alivio
> del terreno EC2 §6.4.4(2)).

## 1. Contexto y objetivo

Se entrega un **modelo IFC ortodoxo** (`caso-09.ifc`) con la **cimentación profunda**
de un edificio con sótano: **dos pilotes** que bajan la carga de un pilar a través de
un **encepado de 2 pilotes** (región D), y una **pantalla anclada** que sostiene la
excavación. Es el peldaño que ejercita la **geotecnia EC7 completa** encadenando
**tres módulos** del motor —`pilotes` + `bielas-tirantes` + `muros-contencion`— y, por
primera vez de forma marcada, exige **clasificar y enrutar cada elemento** del IFC
(antesala del caso 10 integrado).

Doble objetivo, como en cada peldaño:

- **Calcular** las tres subestructuras con el motor y validar contra los criterios.
- **Cerrar la siguiente brecha**: dar a `pilotes/solver_pilote.py`,
  `bielas-tirantes/run_all_encepado.py` y `muros-contencion/solver_pantalla.py` una
  **vía ortodoxa** (`parse_ortodoxo()` + `parse_auto()`, igual que los casos 5 y 8) que
  lea la geometría y las cargas de las **entidades estándar**, manteniendo en Pset
  **solo** los datos sin entidad de análisis estándar (geotecnia, ancla, geometría de
  región D); y **clasificar/enrutar** cada elemento del modelo.

## 2. Descripción del modelo (lo que contiene el IFC)

Todo C30/37. Unidades SI; Z vertical, gravedad −Z; pilotes y pantalla descienden en −Z.

- **A) Dos pilotes** Ø600 mm, L = 12 m, separados a = 1,80 m. `IfcStructuralCurveMember`
  vertical (z = 0 → −12) + `IfcMaterialProfileSet` → `IfcCircleProfileDef` (R = 0,30).
  Geotecnia (balasto horizontal `kh` = 15 MN/m³, fuste `qs` = 60 kPa, punta
  `qb` = 2.500 kPa) en `Pset_Estructurando_Pilote`. **Carga de cabeza** por pilote
  (`IfcStructuralPointAction`): N_G = 650 / N_Q = 225 kN y una horizontal H_Q = 60 kN.
- **B) Encepado de 2 pilotes** bajo pilar 0,45 × 0,45, canto 0,90 m, ancho 0,90 m.
  `IfcStructuralSurfaceMember` horizontal (`Thickness` = 0,90) + `IfcFaceSurface`; los
  **dos pilotes son `IfcStructuralPointConnection`** (apoyos = cabezas de los pilotes).
  Carga del pilar (`IfcStructuralPointAction`): N_G = 1.300 / N_Q = 450 kN. Geometría de
  región D (a, canto, ancho, lado del pilar, Ø pilote) en `Pset_Estructurando_Encepado`.
- **C) Pantalla anclada** e = 0,60 m, excavación H = 7,0 m, empotramiento d = 4,5 m
  (L = 11,5 m), una fila de anclas a z = 1,5 m (incl. 25°, sep. 2,0 m, bulbo Ø0,20,
  τ = 200 kPa). `IfcStructuralCurveMember` vertical + `IfcMaterialProfileSet` →
  `IfcRectangleProfileDef` (XDim = espesor, YDim = 1 m). Terreno (γ = 19, φ = 30°,
  q = 10 kPa, R_d = 350 kPa), ancla y balasto en `Pset_Estructurando_Pantalla`/`_Ancla`/
  `_Terreno`/`_Carga_q`.

**El IFC es ortodoxo**: cada elemento es una entidad estándar de análisis (barra
vertical con sección de perfil, superficie con espesor, apoyos y cargas de cabeza); los
únicos datos no estándar (geotecnia, ancla, geometría de región D) van en Pset, que se
mantiene además como **respaldo** del solver actual. Ver `validacion-IFC.txt`.

## 3. Brecha conocida (lo que hay que corregir)

Con el plugin v0.10.0:

- El parser genérico `laminas/ifc_to_model_3d.py` **ya lee** las 3 barras verticales
  (2 pilotes + pantalla, `tipo = pilar` por geometría) con su sección del profile y la
  superficie del encepado, además de las cargas de `IfcStructuralPointAction` y los
  apoyos de cabeza (`IfcBoundaryNodeCondition`).
- Pero `solver_pilote.py`, `run_all_encepado.py` y `solver_pantalla.py` **leen todavía**
  geometría y cargas de los `Pset_Estructurando_*`. Hay que:
  1. **Clasificar/enrutar cada elemento.** La barra vertical es genéricamente `pilar`;
     distinguir **pilote** (`Pset_Estructurando_Pilote`) de **pantalla**
     (`Pset_Estructurando_Pantalla`), y la superficie como **encepado**
     (`Pset_Estructurando_Encepado`). Es el paso previo al caso 10 (multi-elemento).
  2. Añadir **vía ortodoxa** (`parse_ortodoxo()` + `parse_auto()`) en cada módulo, que
     lea la geometría de las entidades estándar (barra vertical + `IfcCircleProfileDef` /
     `IfcRectangleProfileDef`; superficie del encepado + pilotes en
     `IfcStructuralPointConnection`) y las **cargas de cabeza** de los
     `IfcStructuralPointAction`; manteniendo en Pset **solo** geotecnia / ancla /
     geometría de región D, igual que casos 5/6/8.
  3. Ampliar `perfiles_db.props_from_profile_def` a **`IfcCircleProfileDef`**
     (A = π·D²/4, I = π·D⁴/64) para la sección ortodoxa del pilote (hoy devuelve `None`).

Corregir de forma **acotada**, sin romper los IFC con Pset ni los casos 2–8. Anotar en
`CHANGELOG-plugin.md` y subir el plugin a **0.10.1** (patch) o **0.11.0** (minor: lectura
ortodoxa de pilote/encepado/pantalla) según el alcance.

## 4. Criterios de aceptación

1. **Clasificación/enrutado**: el agente identifica y enruta los 3 elementos a
   `pilotes`, `bielas-tirantes` (encepado) y `muros-contencion` (pantalla),
   respectivamente, leyendo la geometría de las entidades estándar.
2. **Pilotes (EC7 + EC2)**: capacidad axil de cálculo R_c,d = R_s/γ_s + R_b/γ_b ≥ N_Ed
   (fuste + punta); comportamiento lateral (viga sobre muelles `kh`) con esfuerzos
   (M, V, desplazamiento de cabeza) y armado EC2; aprovechamientos ≤ 1.
3. **Encepado (EC2 §6.5, bielas y tirantes)**: modelo de celosía en equilibrio
   (compresión de biela, tracción de tirante), comprobación de bielas y nudos (CCC/CCT),
   armadura del tirante; aprovechamientos ≤ 1.
4. **Pantalla anclada (EC7)**: empuje activo/pasivo (Rankine/Coulomb), fuerza del ancla
   y comprobación del bulbo, empotramiento, esfuerzos (M, V) y armado EC2; estabilidad y
   aprovechamientos ≤ 1. Picos como envolvente; no usar el pico singular como diseño.
5. **Memoria(s)** Word y diagramas por elemento (pilote: capacidad + ley lateral;
   encepado: esquema de bielas y tirantes; pantalla: empujes, ley de M/V y ancla).

## 5. Entregables del hilo

- Parser/solver de `pilotes`, `bielas-tirantes` y `muros-contencion` ampliados a la
  lectura ortodoxa + clasificación/enrutado + plugin reempaquetado **v0.10.1/0.11.0** y
  `CHANGELOG-plugin.md` actualizado.
- En `caso-09-cimentacion-profunda/`: `modelo_neutro.json`, `verificacion*.json`,
  memoria(s) y diagramas.
- `REPOSITORIO-aprendizaje.md`: lección del caso 9 (cimentación profunda; geotecnia EC7
  encadenada; clasificación/enrutado multi-elemento) y fila de métricas.
- **Caso 10 preparado**: `caso-10-edificio-integrado/ENUNCIADO.md` + su IFC ortodoxo
  multi-elemento (pórtico + forjado mixto + núcleo/muro + cimentación) con su generador
  y validación.

## 6. Cómo ejecutar (orientación)

```bash
# 1) (ya hecho) generar el IFC del caso:  python3 generate_caso09_ifc.py
# 2) tras añadir la vía ortodoxa y el enrutado, por elemento:
cd <plugin>/scripts/pilotes          && python3 run_all_pilote.py   <proj> <ruta>/caso-09.ifc
cd <plugin>/scripts/bielas-tirantes  && python3 run_all_encepado.py <proj> <ruta>/caso-09.ifc
cd <plugin>/scripts/muros-contencion && python3 run_all_pantalla.py <proj> <ruta>/caso-09.ifc
```

> Recuerda: clasifica el sistema estructural ANTES de enrutar (aquí hay 3 sistemas
> distintos en un mismo IFC). No uses el pico singular como esfuerzo de diseño. La malla
> fina / el solver de barras pueden ser lentos en el sandbox (ejecuta por separado si
> superas 45 s). Resultado de **predimensionado**, a revisar y firmar por técnico
> competente; marca `[confirmar AN]` los NDP.
