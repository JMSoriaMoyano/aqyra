# Caso 2 — Forjado: losa de hormigón sobre vigas de acero (`laminas` + `barras`)

> Segundo peldaño del programa. Antes de empezar, lee
> `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md` y
> `CHANGELOG-plugin.md`. Trabaja con el agente `ingeniero-estructurista`.
> Plugin de partida: **motor-calculo-estructural v0.3.1** (parser de `barras` ya
> lee IFC ortodoxo: sección desde `IfcIShapeProfileDef` y cargas de línea desde
> `IfcStructuralCurveAction`).

## 1. Contexto y objetivo

Se entrega un **modelo IFC ortodoxo** (`caso-02.ifc`) de un forjado con
**superficie + barras en el mismo modelo**: una losa de hormigón apoyada sobre dos
vigas de acero. Doble objetivo:

1. **Calcular** el forjado: la losa con el módulo `laminas` (flexión EC2) y las
   vigas con el módulo `barras` (EC3), con su validación cruzada y memoria.
2. **Cerrar la siguiente brecha del motor**: el parser de `laminas`
   (`ifc_to_model_3d.py`) aún lee la superficie de `Pset_Estructurando_Superficie`
   y `Pset_Estructurando_Carga_Superficie`. Hay que **ampliarlo a IFC ortodoxo**
   (igual que se hizo en `barras` en v0.3.1) y resolver el **reparto de carga
   losa → vigas** (primer caso multi-elemento, INC-03).

## 2. Descripción del modelo (lo que contiene el IFC)

Forjado unidireccional en planta **6,0 × 4,0 m** (plano XY, Z vertical, gravedad −Z):

- **Losa** de hormigón **C30/37**, espesor **0,12 m**, esquinas (0,0,0)·(6,0,0)·
  (6,4,0)·(0,4,0). Apoyada en sus dos bordes largos sobre las vigas (reparto en una
  dirección, luz de losa 4,0 m).
- **Vigas** de acero **S275**, **IPE 400**, luz **6,0 m**, biapoyadas, separadas
  4,0 m: **V1** (borde y=0, N1→N2) y **V2** (borde y=4, N4→N3).
- **Apoyos**: bases biarticuladas en los 4 extremos de viga (N1..N4).
- **Cargas de superficie sobre la losa** (gravedad, −Z):
  **G = 4,5 kN/m²** (p.p. losa 0,12·25 = 3,0 + solado/tabiquería 1,5) y
  **Q = 3,0 kN/m²** (sobrecarga de uso).

**El IFC es ortodoxo** (entidades estándar; **sin** `Pset_Estructurando_*`):
`IfcStructuralSurfaceMember` con `Thickness` y representación `IfcFaceSurface`
(polígono de esquinas), material por `IfcRelAssociatesMaterial` →
`IfcMaterial`(C30/37) + `IfcMaterialProperties`; vigas por `IfcStructuralCurveMember`
+ `IfcMaterialProfileSet` → `IfcIShapeProfileDef` (IPE 400); cargas por
`IfcStructuralLoadGroup` (G, Q) + `IfcStructuralSurfaceAction` +
`IfcStructuralLoadPlanarForce`. Ver `validacion-IFC.txt`.

## 3. Brecha conocida (lo que hay que corregir) — INC-03 (primer paso) + parser de láminas

Con el plugin v0.3.1:

- El parser de `barras` **ya lee** las dos vigas IPE 400 (sección de catálogo y
  material S275). *Verificado:* devuelve `barras={V1,V2}` con sección y material
  correctos y 0 cargas de línea (las cargas son de superficie).
- El parser de `laminas` `ifc_to_model_3d.py` **no leerá** la losa ortodoxa: hoy
  toma esquinas, espesor y cargas de `Pset_Estructurando_Superficie` /
  `Pset_Estructurando_Carga_Superficie`. Debe leerlas de las **entidades estándar**:
  esquinas de la representación `IfcFaceSurface`/`IfcPolyLoop`, espesor de
  `IfcStructuralSurfaceMember.Thickness`, material del `IfcRelAssociatesMaterial`, y
  cargas de `IfcStructuralSurfaceAction` + `IfcStructuralLoadPlanarForce` con el caso
  desde `IfcStructuralLoadGroup`. **Mantener el camino Pset como respaldo.**
- **Reparto losa → vigas (INC-03):** establecer cómo la carga de superficie llega a
  las vigas. Para la losa unidireccional de este caso, el reparto por **ancho
  tributario** es 2,0 m por viga ⇒ línea sobre cada viga **G = 9,0 kN/m**,
  **Q = 6,0 kN/m** (vía contorno de apoyo de la losa o reacción de la malla de
  placa sobre los bordes apoyados en las vigas). Documentar el criterio elegido.

Corregir de forma **acotada** (extender el parser de láminas y el reparto, sin
romper la lectura de los IFC con Psets). Anotar en `CHANGELOG-plugin.md` y subir el
plugin a **0.4.0** (minor: nueva capacidad de parser de láminas ortodoxas + reparto).

## 4. Criterios de aceptación

1. **Modelo neutro** del IFC ortodoxo con: materiales (S275 y C30/37), 1 superficie
   (losa C30/37, t=0,12 m, 4 esquinas, 2 cargas de superficie G/Q), 2 barras
   (V1, V2 = IPE 400 con material+sección) y 4 nodos con apoyo biarticulado.
2. **Losa (EC2, `laminas`)**: flexión de la losa unidireccional (luz 4,0 m) con
   momento de campo coherente con `m ≈ q·L²/8` por metro de ancho en ELU
   (q_ELU = 1,35·4,5 + 1,50·3,0 = 10,58 kN/m² ⇒ m ≈ 21,2 kN·m/m, cota de banda
   biapoyada); armado y fisuración dentro de rangos; aprovechamientos ≤ 1.
3. **Reparto y vigas (EC3, `barras`)**: cada viga recibe **G = 9,0 / Q = 6,0 kN/m**
   (tributario 2,0 m). Equilibrio: reacción por extremo de viga en ELU
   = (1,35·9,0 + 1,50·6,0)·6,0/2 = **≈ 63,5 kN** (error < 1 %). La IPE 400 verifica
   EC3 (referencia: M ≤ q·L²/8 = 21,15·6²/8 = 95,2 kN·m < Mc,Rd ≈ 359 kN·m).
4. **Validación cruzada** (anaStruct para las vigas; comprobación de placa para la
   losa) con error reducido, y **equilibrio global** (carga total
   = (G+Q)·6·4 vs reacciones).
5. **Memoria** Word y diagramas (losa y vigas).

## 5. Entregables del hilo

- Parser de `laminas` ampliado (IFC ortodoxo) + criterio de reparto losa→vigas +
  plugin reempaquetado **v0.4.0** y `CHANGELOG-plugin.md` actualizado.
- En `caso-02-forjado-losa-vigas/`: `modelo_neutro.json`, `verificacion.json`,
  memoria y diagramas.
- `REPOSITORIO-aprendizaje.md`: lección del caso 2, INC-03 (primer paso) y fila de
  métricas.
- **Caso 3 preparado**: `caso-03-losa-plana-pilares/ENUNCIADO.md` + su IFC ortodoxo
  (losa plana sobre pilares, punzonamiento) con su generador y validación.

## 6. Cómo ejecutar (orientación)

```bash
# 1) (ya hecho) generar el IFC del caso:  python3 generate_caso02_ifc.py
# 2) tras ampliar el parser de laminas a IFC ortodoxo:
cd <plugin>/scripts/laminas
python3 ifc_to_model_3d.py <ruta>/caso-02.ifc proyecto-caso02/modelo_neutro.json
python3 run_all.py proyecto-caso02        # losa EC2 + reparto + vigas EC3 + diagramas
# 3) las vigas se comprueban con el modulo barras (ya ortodoxo en v0.3.1)
```

> Recuerda: resultado de **predimensionado**, a revisar y firmar por técnico
> competente; marcar `[confirmar AN]` los NDP.
