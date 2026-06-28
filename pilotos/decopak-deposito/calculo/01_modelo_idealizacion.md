# 01 · Lectura del IFC, validación e idealización estructural

**Depósito enterrado de Decopak (Rubí, Barcelona)** · Modelo `DepositoDecopakEnterrado.ifc`
**Estado:** PROPUESTA pendiente de verificación QA + firma de JM · 2026-06-24

> Herramientas usadas en la lectura: `ifcopenshell 0.8.5` (parser IFC2X3) + extracción de
> geometría en coordenadas de mundo. Plugin de referencia: `iso19650-openbim` (versión
> en `versions.lock` = `0.0.0` → **versión NO anclada**; ver evidencia QA).

---

## 1. Inventario del modelo (físico, tal cual exportado)

El IFC es un modelo **físico** (geometría + materiales) en coordenadas compartidas de Revit,
**sin dominio de análisis** (sin cargas, apoyos ni eje analítico). Se idealiza desde el físico.

| Elemento (IFC) | Nº | Material (capa) | Espesor | Cota Z (msnm) | Geometría |
|---|---|---|---|---|---|
| `IfcSlab` Losa depósito (BASESLAB) | 1 | E315 Formigó Fonamentació HA | **0,60 m** | 146,40 → 147,00 | losa de fondo, **A ≈ 302,8 m²** |
| `IfcWall` Muro contención 50 cm | 5 | Hormigón in situ | **0,50 m** | 147,00 → 151,35 | h ≈ **4,35 m** (4 perímetro + 1 interior) |
| `IfcWall` Mur contenció 20 | 2 | Hormigón in situ | **0,20 m** | 151,35 → 152,05 | **murete/recrecido superior** (h = 0,70 m y 0,10 m) |
| `IfcSlab` Losa 60 cm (FLOOR) | 1 | Hormigón | **0,60 m** | 151,35 → 151,95 | losa superior, A ≈ 193,8 m² (luz ≈ 11,37 m) |
| `IfcSlab` Losa 70 cm (FLOOR) | 1 | Hormigón | **0,70 m** | 151,25 → 151,95 | losa superior **transitable**, A ≈ 39,7 m² (banda de 4,65 m) |
| `IfcCovering` Sika Waterbar A-320 | 5 | PVC (junta) | — | — | **no estructural** (junta de estanqueidad) |

## 2. Hallazgos de validación (⚠️ a confirmar por JM)

1. **La compartimentación la hace un muro de 50 cm, no de 20 cm.** De los 5 muros de 50 cm,
   cuatro son perimetrales (2 largos ≈ 21,5 m y 2 testeros ≈ 10,5 m) y **uno es interior**
   (eje 164779, L ≈ 10,4 m) que separa un **compartimento pequeño** (≈ 3,3 m × 10 m) en un
   testero del **compartimento grande** (≈ 18 m × 10 m). El «depósito interior mayor lleno de
   agua» del encargo = **compartimento grande**.
2. **Los muros de 20 cm («Mur contenció 20») NO son tabiques interiores de compartimentación
   a altura completa**, sino **muretes/recrecidos superiores** de 0,70 m y 0,10 m de altura
   sobre la losa de cubierta (cota 151,35→152,05), a lo largo del borde largo. Se tratan como
   elementos secundarios (peto/recrecido), no como muro de contención principal. *Difiere del
   supuesto del encargo; confirmar función real (peto perimetral / canal / formación de
   pendiente).*
3. **Las cotas Z son de emplazamiento (msnm), no altura de pieza.** La cota de implantación
   resultante del modelo es: **base de la losa de fondo = +146,40**, rasante superior
   (cubierta transitable) ≈ **+151,95 a +152,05**.
4. **No hay pilares ni vigas** en el modelo: la losa de cubierta salva la luz transversal
   apoyada solo en los muros largos → **losa unidireccional de luz c/c ≈ 11,37 m** (clara ≈ 10,9 m).
   Es una luz grande para un canto de 0,60–0,70 m; se comprueba expresamente (ver 04).
5. El IFC **no exporta cantidades base** (Qto) ni `IfcMaterial` por capa en 4 de los 5 muros
   de 50 cm (export de vista de coordinación). Geometría y espesores se obtienen de los sólidos
   de barrido y del `IfcMaterialLayerSet` disponible.

## 3. Idealización adoptada (geometría de cálculo)

**Cajón estanco rectangular enterrado**, ejes locales: *L* = dirección larga (≈ 21,5 m),
*T* = dirección transversal (≈ 11,37 m c/c entre muros largos).

| Magnitud | Valor adoptado | Origen |
|---|---|---|
| Altura libre interior / altura de muro | **H = 4,35 m** (147,00 → 151,35) | geometría |
| Calado máximo de agua | **h_w = 4,35 m** (lleno hasta intradós cubierta) | servicio (conservador) |
| Luz transversal cubierta (c/c muros largos) | **L_T = 11,37 m** (clara ≈ 10,87 m) | geometría |
| Longitud tanque (entre testeros) | ≈ 21,5 m | geometría |
| Compartimento grande (lleno) | ≈ 18,0 × 10,0 m | geometría |
| Espesores | muros 0,50 m · fondo 0,60 m · cubierta 0,60 / 0,70 m | material/capa |
| Recubrimiento del terreno sobre cubierta | ≈ 0 (cubierta a rasante, transitable) | servicio |
| Altura de tierras retenida (cara exterior muro) | **H_t ≈ 4,95 m** (147,00 → 151,95 rasante) | servicio |

**Esquema estructural por elemento:**
- *Muros perimetrales 50 cm:* losa/franja vertical de 1 m, **empotrada en la losa de fondo y
  apoyada (apuntalada) en la losa de cubierta** → ménsula apuntalada vertical. Armado en ambas
  caras (acción reversible agua↔tierras).
- *Muro interior 50 cm:* franja vertical apuntalada, **empuje diferencial de agua** (grande lleno / pequeño vacío).
- *Losa de fondo (raft):* losa sobre lecho elástico (Winkler); reacción del terreno + columna de
  agua; comprobación de subpresión/flotación.
- *Losa de cubierta 60/70 cm:* losa unidireccional sobre los muros largos, **tráfico pesado
  (IAP-11 LM1)** → flexión + **punzonamiento**.

## 4. Materiales (propuesta — confirmar)

| Material | Propuesta | Notas |
|---|---|---|
| Hormigón estructural | **HA-30/B/20/IIa+Qb** (f_ck = 30 MPa) | grado a confirmar; HA-30 mínimo recomendable en depósito |
| Acero pasivo | **B500S** (f_yk = 500 MPa) | — |
| Recubrimiento nominal | **c_nom = 45 mm** (cara agua/tierra) | clase exposición XC4/XD; depósito de líquidos |
| Clase de estanqueidad (EN 1992-3) | **Clase 1** → w_k,máx = **0,20 mm** (caras en contacto con agua) | tightness class de proyecto, a confirmar |

*Procedencia: brief de JM (HA-30/B500S salvo dato) + criterio de depósito de líquidos (EN 1992-3).*
