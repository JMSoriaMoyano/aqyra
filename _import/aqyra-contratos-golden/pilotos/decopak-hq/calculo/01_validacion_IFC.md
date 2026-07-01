# Decopak HQ — Validación del modelo IFC (dominio estructural)

- **Documento:** evidencia de entrada para el cálculo · **rol:** build (producción)
- **Estado:** PROPUESTA / evidencia — pendiente de verificación QA independiente y firma de JM
- **Fecha:** 2026-06-24
- **Modelo:** `modelo/DEC-PB-EBAN-HQ-Y-BIM-EST-02-EstructuraNucleoLateral-S1-v0.0.ifc`
- **Versiones consumidas:** ver `versions.lock` (hoy `0.0.0` — núcleo sin primer tag, tarea N1.1). El resultado **no es reproducible** hasta anclar versiones reales. Ver nota en `03_plan_calculo.md`.

> ⚠️ La QA la ejecuta un agente independiente con su propio oráculo. Este informe **prepara la evidencia**; no certifica nada.

---

## 1. Identificación del modelo

| Campo | Valor |
|---|---|
| Esquema | IFC4 (`FILE_SCHEMA(('IFC4'))`) |
| Vista | CoordinationView (ViewDefinition) |
| Origen | IfcOpenShell 0.8.5 |
| Proyecto | «Decopak HQ - Variante B v3 OPTIMIZADO (EC3)» |
| Emplazamiento | Rubí (Barcelona) |
| Edificio | HQ |
| Entidades en DATA | 5.839 |

**Extensión geométrica (bounding box de los puntos cartesianos):** ancho X ≈ 11,5 m · largo Y ≈ 40,5 m · alto Z de −8,50 m (puntas de pilote) a +15,00 m (cubierta). Edificio alargado y estrecho, coherente con un núcleo lateral que resuelve voladizos.

## 2. Estructura espacial (niveles)

| Planta | Nombre IFC | Cota (m) |
|---|---|---|
| Cimentación | Cimentacion | −1,50 |
| Planta baja | PB | 0,00 |
| Altillo | Altillo-Lab | +2,90 |
| Planta 1 | P1 | +5,75 |
| Planta 2 | P2 | +8,833 |
| Planta 3 | P3 | +11,917 |
| Cubierta | PC | +15,00 |

Jerarquía correcta: `IfcProject → IfcSite (Rubí) → IfcBuilding (HQ) → 7× IfcBuildingStorey`, agregadas con `IfcRelAggregates`. Alturas entre plantas tipo ≈ 3,08 m (P1–P2–P3) y 2,85–2,90 m (PB–Altillo–P1). ✔️ Coherente.

## 3. Materiales y propiedades de material

| Material | Tipo | Propiedad declarada | Valor |
|---|---|---|---|
| Acero S355 | steel | YieldStress | 355 MPa |
| Acero S355 | steel | FireResistance_Protected | R 60 |
| HA-30 / B500S | concrete | CompressiveStrength | 30 MPa |
| CLT / cassette | wood | BendingStrength | 24 MPa |

✔️ Coherente con la descripción del piloto (S355 + HA-30/B500S + CLT). Las propiedades cuelgan de `IfcMaterialProperties` (límite elástico, fuego R60, resistencias).

## 4. Inventario de elementos estructurales

| Tipo IFC | Nombre | PredefinedType | Nº |
|---|---|---|---:|
| IfcBeam | Costilla cassette | JOIST | 128 |
| IfcBeam | Conexion dintel O | BEAM | 16 |
| IfcBeam | Conexion dintel E | BEAM | 16 |
| IfcMember | Cajon O diagonal | BRACE | 45 |
| IfcMember | Cercha E diagonal | BRACE | 45 |
| IfcMember | Cajon O montante ext | POST | 16 |
| IfcMember | Cajon O montante int | POST | 16 |
| IfcMember | Cajon O diafragma inf | BRACE | 16 |
| IfcMember | Cajon O diafragma sup | BRACE | 16 |
| IfcMember | Cercha E montante | POST | 16 |
| IfcMember | Alma C montante | POST | 15 |
| IfcMember | Conexion montante | POST | 12 |
| IfcMember | Conexion diagonal | BRACE | 12 |
| IfcMember | Tirante altillo | (sin tipo) | 6 |
| IfcMember | Cajon O cordon ext / int | CHORD | 4 + 4 |
| IfcMember | Cercha E cordon | CHORD | 4 |
| IfcMember | Alma C cordon | CHORD | 4 |
| IfcSlab | Losa CLT cassette | FLOOR | 4 |
| IfcSlab | Altillo Lab (sala formacion) | FLOOR | 1 |
| IfcWall | NC-Lab / NC-Vest (HA e=0,30) | (sin tipo) | 1 + 1 |
| IfcFooting | Encepado NC-Vest (6 D65) | PILE_CAP | 1 |
| IfcFooting | Encepado NC-Lab (4 D45) | PILE_CAP | 1 |
| IfcPile | Pilote D65 NC-Vest (a UG3) | BORED | 6 |
| IfcPile | Pilote D45 NC-Lab (a UG3) | BORED | 4 |

**Totales:** 160 IfcBeam · 231 IfcMember · 10 IfcPile · 2 IfcFooting · 5 IfcSlab · 2 IfcWall. No hay IfcColumn (los soportes verticales son los montantes/cordones del cajón y los muros de hormigón). No hay armadura modelada (`IfcReinforcingBar` = 0), esperado en fase de cálculo.

### Lectura del sistema estructural
- **Cajón O** y **Cercha E** y **Alma C**: tres celosías de acero S355 (cordones CHORD + diagonales BRACE + montantes POST + diafragmas) que forman el **núcleo lateral** y resuelven los **grandes voladizos**.
- **Forjado CLT cassette**: 4 losas tipo cassette + 128 costillas (JOIST) → voladizo ligero (el criterio que da sentido al caso).
- **Conexiones dintel/montante/diagonal**: elementos de enlace entre subsistemas.
- **Muros HA-30 e=0,30** (NC-Lab, NC-Vest) → núcleos de hormigón.
- **Cimentación**: 2 encepados (6×D650 y 4×D450) sobre 10 pilotes perforados empotrados en UG3.

## 5. Perfiles presentes

- **IPE:** 160, 180, 200, 220, 240, 270, 300 (1 def. cada uno).
- **SHS (tubo cuadrado):** 80×8, 120×6, 150×8, 160×8, 180×8, 200×10, 250×12, 250×16, 300×16.
- **Circulares (pilotes):** D650 (Ø0,65 m, 6 ud) y D450 (Ø0,45 m, 4 ud).
- **Perfiles arbitrarios / sin nombre:** 7 `IfcArbitraryClosedProfileDef`, 2 `IfcArbitraryProfileDef`, 9 secciones con nombre `$` → corresponden a losas/muros/cassette (secciones genéricas). 

## 6. Hallazgos de validación (control de calidad de entrada)

| # | Hallazgo | Severidad | Acción |
|---|---|---|---|
| V1 | El modelo **no contiene cargas** (sin `IfcStructuralLoad*` ni Psets de carga). | Esperado (semilla) | Definir hipótesis de acciones → `02_bases_acciones_HIPOTESIS.md`. |
| V2 | **Sin Property Sets de elemento** (`IfcPropertySet` = 0); solo `IfcMaterialProperties`. No hay `Pset_*Common`, ni Psets de resultado/clasificación por elemento. | Media | Tras el cálculo, escribir Psets de resultado al IFC (write-back) y, si procede, clasificación bsDD/Uniclass. |
| V3 | **Asignación de unidades incompleta**: solo se declara `LENGTHUNIT = METRE`. Faltan unidades de área, volumen, masa, fuerza y ángulo. | Baja | No bloquea el cálculo (longitudes en m). Documentar; completar en write-back. |
| V4 | Elementos con **PredefinedType sin asignar** (`$`): «Tirante altillo» (6), muros NC-Lab/NC-Vest (2). | Baja | Clasificar (tirante = TENSIONMEMBER/`IfcMember`; muros = `SHEAR`/estándar) al enriquecer. |
| V5 | Perfiles de losa/muro como secciones **genéricas/arbitrarias sin nombre** (`$`). | Baja | Verificar espesores (muro e=0,30 declarado en el nombre; losas CLT/cassette) al modelar el cálculo. |
| V6 | Nomenclatura de elementos **descriptiva pero no codificada** (nombres en lenguaje natural, no un esquema tipo `EST-VIG-001`). | Informativo | Coherente con el origen «nacido del lenguaje natural». No bloquea; valorar codificación para trazabilidad QA. |

**Veredicto de validación (propuesta):** el IFC es **apto como entrada de cálculo** — geometría, niveles, materiales y tipología estructural son coherentes y completos para idealizar. Las carencias detectadas (V1–V6) son las propias de un modelo semilla y se resuelven definiendo acciones y, tras calcular, escribiendo resultados al modelo. **Pendiente de verificación por QA y firma de JM.**

## 7. Trazabilidad (para el informe de QA)

```
input:    DEC-PB-EBAN-HQ-Y-BIM-EST-02-EstructuraNucleoLateral-S1-v0.0.ifc (IFC4)
parser:   iso19650-openbim · ifc-validate  (versión a anclar — hoy 0.0.0)
método:   inventario por tipo/nombre/perfil/material/nivel + bounding box
salida:   este informe (inventario + hallazgos V1–V6 + veredicto de aptitud)
oráculo:  recuento independiente del fichero IFC (texto STEP)
veredicto: APTO como entrada (propuesta) → pendiente QA + firma JM
```
