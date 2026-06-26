# Caso 3 — Losa plana sobre pilares (`laminas` flat, EC2 + punzonamiento)

> Tercer peldaño del programa. Antes de empezar, lee
> `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md` y
> `CHANGELOG-plugin.md`. Trabaja con el agente `ingeniero-estructurista`.
> Plugin de partida: **motor-calculo-estructural v0.4.0** (el parser de `laminas`
> ya lee superficies ortodoxas —esquinas de `IfcFaceSurface`/`IfcPolyLoop`,
> espesor de `.Thickness`, material de `IfcRelAssociatesMaterial` y cargas de
> `IfcStructuralSurfaceAction`— y el reparto losa→vigas por ancho tributario).

## 1. Contexto y objetivo

Se entrega un **modelo IFC ortodoxo** (`caso-03.ifc`) de un **forjado de losa
maciza (losa plana) apoyada directamente sobre pilares**, sin vigas. Doble objetivo:

1. **Calcular** la losa plana con el módulo `laminas` (flexión EC2 por bandas y,
   sobre todo, **punzonamiento** EC2 6.4 en los pilares, con dimensionamiento),
   más flecha y fisuración, con su validación y memoria.
2. **Cerrar la siguiente brecha del motor**: leer **apoyos puntuales / pilares**
   desde el IFC ortodoxo (sección de pilar desde `IfcRectangleProfileDef`, no solo
   `IfcIShapeProfileDef`) y resolver la losa **apoyada en una retícula de pilares**
   (no en bordes lineales como el caso 2). Es el siguiente paso de INC-03.

## 2. Descripción del modelo (lo que contiene el IFC)

Forjado de losa maciza en planta **10,0 × 10,0 m** (dos vanos × dos vanos de 5,0 m;
plano XY, Z vertical, gravedad −Z):

- **Losa** de hormigón **C30/37**, espesor **0,28 m**, esquinas (0,0,0)·(10,0,0)·
  (10,10,0)·(0,10,0).
- **9 pilares** de hormigón **C30/37**, sección **0,40 × 0,40 m**, altura 3,0 m,
  en retícula 3×3 a x,y = {0, 5, 10} m. **Empotrados** en su base (z = −3,0).
  El **pilar interior P5 (5,5)** es el **crítico a punzonamiento**.
- **Cargas de superficie** sobre la losa (gravedad, −Z):
  **G = 8,5 kN/m²** (p.p. losa 0,28·25 = 7,0 + solado/tabiquería 1,5) y
  **Q = 3,0 kN/m²** (sobrecarga de uso, Cat. B).

**El IFC es ortodoxo** (entidades estándar; **sin** `Pset_Estructurando_*`):
`IfcStructuralSurfaceMember` con `Thickness` y representación `IfcFaceSurface`;
pilares `IfcStructuralCurveMember` + `IfcMaterialProfileSet` → `IfcRectangleProfileDef`
(0,40×0,40) con material C30/37; cabezas y bases por `IfcStructuralPointConnection`
(bases con `IfcBoundaryNodeCondition` empotrado); cargas por `IfcStructuralLoadGroup`
(G, Q) + `IfcStructuralSurfaceAction` + `IfcStructuralLoadPlanarForce`.
Ver `validacion-IFC.txt`.

## 3. Brecha conocida (lo que hay que corregir) — INC-03 (apoyos puntuales) + punzonamiento

Con el plugin v0.4.0:

- El parser de `laminas` **ya lee** la losa ortodoxa (esquinas, espesor, material y
  cargas de superficie G/Q). *Verificado:* devuelve la superficie con t=0,28 m,
  C30/37 y cargas G=8,5 / Q=3,0 kN/m².
- El parser **lee el nombre** del perfil de pilar (`C 400x400`) pero **no sus
  propiedades de sección** porque `perfiles_db.props_from_profile_def` solo resuelve
  `IfcIShapeProfileDef`. Hay que **ampliarlo a `IfcRectangleProfileDef`** (A = b·h,
  I = b·h³/12, etc.) para tener la dimensión del pilar (c1, c2) que necesita el
  punzonamiento. **Mantener catálogo y geometría como respaldo.**
- **Apoyo de la losa en pilares (INC-03, siguiente paso):** hoy `solver_flat`/`solver_3d`
  generan vigas perimetrales + pilares de esquina de forma automática. Para esta losa
  plana hay que **apoyar la malla de placa en las 9 cabezas de pilar** (apoyos puntuales
  donde el mallado coincide con la retícula; malla que divida 5,0 m, p. ej. 0,5 m) y
  obtener la **reacción de cada pilar** para el punzonamiento.
- **Punzonamiento (EC2 6.4) con dimensionamiento:** comprobar el pilar interior P5
  (`posicion="interior"`) con V_Ed = reacción del pilar; si no cumple, dimensionar
  (canto mínimo / armadura de punzonamiento / ábaco) con `ec2_punz_fis.dimensionar_punzonamiento`.

Corregir de forma **acotada** (perfil rectangular + apoyos puntuales + punzonamiento
desde IFC ortodoxo, sin romper la lectura de los IFC con Psets ni del caso 2). Anotar
en `CHANGELOG-plugin.md` y subir el plugin a **0.5.0** (minor: sección rectangular +
apoyos puntuales + punzonamiento ortodoxo) — o **0.4.1** si el alcance es menor.

## 4. Criterios de aceptación

1. **Modelo neutro** del IFC ortodoxo con: material C30/37, 1 superficie (losa
   C30/37, t=0,28 m, 4 esquinas, 2 cargas G/Q), 9 pilares (sección 0,40×0,40 m con
   propiedades) y 18 nodos (9 cabezas + 9 bases empotradas).
2. **Losa (EC2, flexión por bandas)**: momentos de vano y de soporte coherentes con
   una losa plana de 5,0 m de vano (orden de magnitud m ≈ α·q·L²); armadura y
   fisuración dentro de rangos; flecha ≤ límite; aprovechamientos ≤ 1.
3. **Punzonamiento (EC2 6.4)**: pilar interior P5 con V_Ed ≈ (1,35·8,5 + 1,50·3,0)·5,0²
   ≈ **399 kN** (tributario 25 m²). Comprobar v_Ed ≤ v_Rd,c en el perímetro u1 y
   v_Ed ≤ v_Rd,max en u0; si no cumple, **dimensionar** (canto/armadura/ábaco).
4. **Equilibrio global**: carga total ELU = (1,35·8,5 + 1,50·3,0)·10·10 ≈ **1.597 kN**
   ≈ Σ reacciones de los 9 pilares (error < 1 %). Validación de placa (autodiagnóstico
   MITC4) OK.
5. **Memoria** Word y diagramas (mapa de momentos de la losa y esquema de punzonamiento).

## 5. Entregables del hilo

- Parser de `laminas` ampliado (perfil rectangular + apoyos puntuales) + punzonamiento
  desde IFC ortodoxo + plugin reempaquetado **v0.5.0** (o v0.4.1) y `CHANGELOG-plugin.md`
  actualizado.
- En `caso-03-losa-plana-pilares/`: `modelo_neutro.json`, `verificacion.json`, memoria
  y diagramas.
- `REPOSITORIO-aprendizaje.md`: lección del caso 3, avance de INC-03 (apoyos puntuales)
  y fila de métricas.
- **Caso 4 preparado**: `caso-04-cubierta-inclinada/ENUNCIADO.md` + su IFC ortodoxo
  (cubierta/forjado inclinado, flexión + membrana) con su generador y validación.

## 6. Cómo ejecutar (orientación)

```bash
# 1) (ya hecho) generar el IFC del caso:  python3 generate_caso03_ifc.py
# 2) tras ampliar el parser (perfil rectangular + apoyos puntuales):
cd <plugin>/scripts/laminas
python3 ifc_to_model_3d.py <ruta>/caso-03.ifc proyecto-caso03/modelo_neutro.json
#    losa plana: flexion EC2 por bandas + PUNZONAMIENTO en pilares + diagramas
#    (apoyar la malla en las 9 cabezas de pilar; malla 0,5 m que divide el vano de 5,0 m)
```

> Recuerda: resultado de **predimensionado**, a revisar y firmar por técnico
> competente; marcar `[confirmar AN]` los NDP.
