# Caso 1 — Pórtico de acero biarticulado (módulo `barras`, EC3)

> Primer peldaño del programa de aprendizaje. Antes de empezar, lee
> `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md` y
> `CHANGELOG-plugin.md`. Trabaja con el agente `ingeniero-estructurista`.

## 1. Contexto y objetivo

Se entrega un **modelo IFC ortodoxo** (`caso-01.ifc`) de un pórtico de acero. El objetivo
doble del caso es:

1. **Calcular** el pórtico con el módulo `barras` (esfuerzos, EC3, validación cruzada,
   memoria).
2. **Cerrar la primera brecha del motor**: el parser actual **no lee** la sección ni las
   cargas de un IFC ortodoxo. Hay que **ampliar el parser** para consumir entidades IFC
   estándar (objetivo transversal de todo el programa).

## 2. Descripción del modelo (lo que contiene el IFC)

Pórtico biarticulado de acero **S275**, en plano XZ (Z vertical):

- Geometría: luz **6,0 m**, altura de pilares **4,0 m**. Nodos N1(0,0,0), N2(0,0,4),
  N3(6,0,4), N4(6,0,0).
- Barras: pilares **C1, C2 = HEB 200**; dintel **B1 = IPE 330**.
- Apoyos: **bases biarticuladas** en N1 y N4 (traslaciones coaccionadas, giros libres).
- Cargas sobre el dintel B1: permanente **G = 12 kN/m** y variable **Q = 10 kN/m**
  (gravedad, −Z).

**El IFC es ortodoxo** (entidades IFC estándar; **sin** `Pset_Estructurando_*`):
`IfcStructuralPointConnection` + `IfcBoundaryNodeCondition` (apoyos),
`IfcStructuralCurveMember` + `IfcEdge` (barras/topología), sección por
`IfcMaterialProfileSet` → `IfcMaterialProfile` → `IfcIShapeProfileDef` (dimensiones reales
del perfil), material por `IfcRelAssociatesMaterial` + `IfcMaterialProperties`
(Pset_MaterialMechanical), y cargas por `IfcStructuralLoadGroup` (G y Q) +
`IfcStructuralCurveAction` + `IfcStructuralLoadLinearForce`. Ver `validacion-IFC.txt`.

## 3. Brecha conocida (lo que hay que corregir) — INC-01, INC-02

Ejecutando el parser actual `scripts/barras/ifc_to_model.py` sobre este IFC se obtiene:
materiales OK (S275), nodos + apoyos + topología OK, pero **`secciones: {}`**, **barras con
`material: null` y `seccion: null`** y **0 cargas**. Es decir, el parser:

- lee la sección de `Pset_Estructurando_Analisis` (no existe aquí) → debe leerla del
  **perfil `IfcIShapeProfileDef`** del `IfcMaterialProfileSet` asociado, calculando A, I_y,
  I_z, J, W_pl, W_el, A_vz (de la geometría del perfil o de una pequeña **base de datos de
  perfiles** HEB/IPE);
- toma el material del miembro como `IfcMaterial` directo → debe resolverlo también cuando
  `RelatingMaterial` es un `IfcMaterialProfileSet`;
- lee las cargas de `Pset_Estructurando_Carga` + `IfcStructuralLinearAction` → debe leer
  `IfcStructuralCurveAction` con `IfcStructuralLoadLinearForce` y asignar el **caso** (G/Q)
  desde el `IfcStructuralLoadGroup` que agrupa la acción, y la barra desde
  `IfcRelConnectsStructuralActivity`.

Corregir de forma **acotada** (extender el parser, sin romper la lectura de los IFC con
Psets propios: mantener ambos caminos, dando prioridad a las entidades estándar). Anotar la
corrección en `CHANGELOG-plugin.md` y subir el plugin a **0.3.1**.

## 4. Criterios de aceptación

1. **Modelo neutro** generado del IFC ortodoxo con: materiales (S275 con E, G, ν, ρ, f_y),
   secciones HEB 200 e IPE 330 (con A, I_y, W_ply…), 3 barras con material+sección+nodos, y
   **2 cargas** (G y Q en B1).
2. **Equilibrio**: reacciones verticales en ELU (1,35·G + 1,50·Q = 31,2 kN/m sobre 6 m =
   **187,2 kN**) → **≈ 93,6 kN por apoyo** (error < 1 %).
3. **Validación cruzada anaStruct** (la del módulo `barras`) con error ~0 %.
4. **EC3**: el dintel IPE 330 y los pilares HEB 200 verifican (aprovechamientos ≤ 1) a
   flexión, cortante y pandeo; reportar u_M, u_V, u_N y el aprovechamiento gobernante.
   (Referencia: M de dintel < w·L²/8 = 140 kN·m en ELU, cota superior de viga biapoyada.)
5. **Memoria** Word generada y diagramas (N, V, M, deformada).

## 5. Entregables del hilo

- Parser de `barras` ampliado (IFC ortodoxo) + plugin reempaquetado **v0.3.1** y
  `CHANGELOG-plugin.md` actualizado.
- En `caso-01-portico-acero/`: `modelo_neutro.json`, `verificacion.json`, memoria y
  diagramas.
- `REPOSITORIO-aprendizaje.md`: lección del caso 1, INC-01/INC-02 → ✅, y fila de métricas.
- **Caso 2 preparado**: `caso-02-.../ENUNCIADO.md` + su IFC ortodoxo (forjado: losa de
  hormigón sobre vigas de acero — superficie + barras en el mismo modelo) con su generador y
  validación.

## 6. Cómo ejecutar (orientación)

```bash
# 1) (ya hecho) generar el IFC del caso:  python3 generate_caso01_ifc.py
# 2) calcular con el modulo barras (tras ampliar el parser):
cd <plugin>/scripts/barras
python3 ifc_to_model.py <ruta>/caso-01.ifc proyecto-caso01/modelo_neutro.json
python3 run_all.py proyecto-caso01        # solver + EC3 + validacion cruzada + diagramas
NODE_PATH=$(npm root -g) node generate_memoria.js proyecto-caso01
```

> Recuerda: resultado de **predimensionado**, a revisar y firmar por técnico competente;
> marcar `[confirmar AN]` los NDP.
