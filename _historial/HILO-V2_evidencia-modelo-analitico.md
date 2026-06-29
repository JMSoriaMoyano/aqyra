# HILO-V2 · Evidencia del modelo analítico y recomendación para §6 (decisiones abiertas)

> **Qué es:** primer paso del hilo de V2 (§7 del brief). Inspección de IFC reales **antes de escribir código**, para que **JM cierre §6.1–§6.4**. La IA prepara la evidencia; **JM decide y firma**.
> **Fecha:** 2026-06-24. **Formato:** Markdown en el repo (§8). **Verificado** = medido sobre fichero; **[I]** = inferido.

---

## 1. Qué se ha inspeccionado

| Fichero | Origen | Esquema · MVD | Tamaño |
|---|---|---|---|
| `DEC-PB-EBAN-HQ-Y-BIM-EST-02-EstructuraNucleoLateral-S1-v0.0.ifc` | **Decopak HQ** (caso guía), `pilotos/decopak-hq/modelo/` | IFC4 · CoordinationView | 5 848 líneas |
| `raft.ifc` | Ecosistema (motor-cálculo, IfcOpenShell 0.8.5) | IFC4 · CoordinationView | 101 líneas |
| `pantalla.ifc` | Ecosistema (motor-cálculo, IfcOpenShell 0.8.5) | IFC4 · CoordinationView | 72 líneas |

---

## 2. Hallazgo decisivo (verificado)

**El modelo del caso guía (Decopak HQ) NO trae dominio de análisis estructural.** Es un modelo **físico** de vista de coordinación.

| Magnitud (conteo de entidades) | Decopak HQ | raft (núcleo) | pantalla (núcleo) |
|---|---|---|---|
| `IfcStructuralAnalysisModel` | **0** | 1 | 1 |
| Miembro analítico (`…SurfaceMember`/`…CurveMember`) | **0** | 1 (superficie) | 1 (curva) |
| Conexiones / **apoyos** (`…Connection`) | **0** | 0 | 0 |
| **Cargas/casos** (`LoadGroup`/`LoadCase`/`StructuralAction`) | **0** | 0 | 0 |
| Elementos **físicos** estructurales | **408** | 0 | 0 |

**Desglose físico de Decopak HQ:** 231 `IfcMember` (algunos `PredefinedType=.CHORD.`), 160 `IfcBeam`, 10 `IfcPile`, 5 `IfcSlab`, 2 `IfcWall`, 2 `IfcFooting`. Estructura espacial completa (1 Project · 1 Site · 1 Building · **7 BuildingStorey**).

**Secciones presentes** (clave para idealizar): 7 `IfcIShapeProfileDef`, 10 `IfcCircleProfileDef`, 9 `IfcRectangleHollowProfileDef`, 7 `IfcArbitraryClosedProfileDef`. Materiales: 3 `IfcMaterial` + 3 `IfcRelAssociatesMaterial`.

**Geometría:** 410 `IfcExtrudedAreaSolid` (+410 `IfcShapeRepresentation`); **0 representaciones `'Axis'`**. → El eje de barra **no viene dado**; hay que **derivarlo** del sólido extruido (colocación + dirección·profundidad de extrusión).

### Lectura
1. **Decopak HQ = solo físico.** La opción §6.1(a) —leer `IfcStructuralAnalysisModel`— **no es viable para el caso guía**, porque CoordinationView no incluye el dominio de análisis (es su propia MVD, *Structural Analysis View*).
2. **El núcleo emite un analítico esquelético.** raft/pantalla traen el *contenedor* del modelo de análisis + el *miembro* idealizado, pero **ni apoyos ni cargas**. La opción (c) da geometría idealizada del núcleo, no las acciones.
3. **Apoyos y cargas nunca vienen en el IFC de entrada** (ni físico ni analítico del núcleo). → **Siempre se autoran en Aqyra** como *entradas* (`proposal`). Coherente con el principio nº 3 (dos llaves).

---

## 3. Recomendación de la IA para §6 (JM cierra)

### §6.1 · Fuente del modelo analítico → **(b) derivar del físico, como vía primaria**
- **Primaria (b):** derivar el idealizado del modelo físico — ejes de barra desde la trayectoria de extrusión de `IfcBeam`/`IfcColumn`/`IfcMember`, sección desde el `…ProfileDef`, clasificación por `PredefinedType`. **Es la única vía que funciona sobre el caso guía.**
- **Oportunista (a):** si un IFC de entrada **sí** trae `IfcStructuralAnalysisModel` (Structural Analysis View), leerlo directo.
- **Puente (c):** consumir el analítico del núcleo (estilo raft/pantalla) cuando Aqyra trabaje **aguas abajo** de una idealización del núcleo.
- **Apoyos/cargas:** **siempre autorados** en Aqyra (no están en la entrada) → ver §6.3.
- *Matiz técnico:* derivar el eje exige reconstruirlo del `IfcExtrudedAreaSolid` (no hay `'Axis'`). Factible; el primer corte debe demostrarlo sobre vigas/pilares.

### §6.2 · Dónde regenera / write-back → **client-side con web-ifc**
- Persistir cargas/apoyos **en el navegador con web-ifc** (ya escribe IFC, probado en V1). Honra D-002 ("sin servidor"). El write-back de Psets es **texto diff-able**.
- **Reservar** un backend Python/IfcOpenShell **solo** si la regeneración paramétrica completa (Capa 2·C íntegra) lo exige más adelante.

### §6.3 · Modelo de datos de cargas/combinaciones → **Pset/anejo propio diff-able**
- Representar apoyos, cargas, casos y combinaciones como un **Pset Aqyra** (p. ej. `Pset_AqyraStructural_*`) adjunto al miembro/grupo analítico, **sin depender** de que la entrada traiga entidades nativas `IfcStructuralLoad*`.
- Motivos: (1) la entrada no las trae; (2) es el camino diff-able más simple client-side con web-ifc; (3) mantiene limpio `DataState=proposal`.
- *Opcional, diferido (≈V3):* poder **emitir también** `IfcStructuralLoadGroup`/`IfcStructuralAction` nativos para interoperar cuando madure el round-trip con el motor.

### §6.4 · Extensión del contrato `AqyraViewer` → sub-API `pre` (SemVer **MINOR**)
Nueva sub-API de solo lectura, espejando `bcf`/`ids`, para no ensuciar la superficie núcleo. Todo dato devuelto en estado `proposal`:

```ts
readonly pre: {
  getStructuralModel(): Promise<StructuralModel>;        // miembros/nudos idealizados (derivados o leídos)
  listSupports(): Support[];  setSupport(nodeId, restraints): void;
  listLoads(): Load[];        addLoad(target, load): string;  removeLoad(id): void;
  listLoadCases(): LoadCase[];  listCombinations(): Combination[];
}
```

---

## 4. Primer corte propuesto (mínimo demoable del DoD)

1. **Leer+derivar:** del físico de Decopak HQ, derivar ejes de vigas/pilares/miembros y **pintarlos como wireframe** sobre el modelo; leer sección desde el `ProfileDef`.
2. **Apoyos:** render + autorar **un** apoyo (p. ej. base de pilotes/zapatas como empotrado).
3. **Una carga:** autorar **una** carga (distribuida en una viga o puntual en un nudo) por menú contextual / barra de comandos; render como glifo de flecha con valor, `DataState=proposal`.
4. **Un write-back:** persistir esa carga/apoyo como **Pset Aqyra** en el IFC, **client-side con web-ifc**; reabrir → sigue ahí (diff-able).
5. **Superficie:** conectar los comandos **ya reservados** en la skin Calculista (`calculista.ts:302`, regex `carga|sobrecarga|apoyo|empotr|barra|nudo|analitic|hipotesis`) para que **despachen** en vez de avisar "V2 no disponible".

---

## 5. Borrador de entradas para `DECISIONES.md` (pendientes de firma de JM)

> No firmadas. La IA propone; **JM cierra** y traslada a `DECISIONES.md` con fecha y firma.

**D-008 · §6.1 — Fuente del modelo analítico.** *Propuesta:* derivar del físico (b) como vía primaria; leer dominio de análisis (a) si la entrada lo trae; consumir analítico del núcleo (c) como puente. *Evidencia:* §2 (Decopak HQ sin dominio de análisis; núcleo esquelético).

**D-009 · §6.2 — Write-back.** *Propuesta:* client-side con web-ifc (texto diff-able); backend Python solo si lo exige la regeneración paramétrica completa. *Evidencia:* D-002 + write-back de web-ifc probado en V1.

**D-010 · §6.3 — Modelo de datos de acciones.** *Propuesta:* Pset Aqyra diff-able (`proposal`); emisión nativa `IfcStructuralLoad*` diferida. *Evidencia:* entradas sin cargas/apoyos (§2).

**D-011 · §6.4 — Contrato.** *Propuesta:* sub-API `pre` de solo lectura, SemVer MINOR, datos en `proposal`. *Evidencia:* patrón `bcf`/`ids` ya en `contract.ts`.

---

## 6. Fuentes

- buildingSMART — *IfcStructuralAnalysisModel* (IFC4.3.2.0, dominio Structural Analysis; atributo opcional `LoadedBy` → `IfcStructuralLoadGroup`). Consultado 2026-06-24: <https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcStructuralAnalysisModel.htm>
- buildingSMART — *IfcStructuralAnalysisDomain* (visión del dominio). Consultado 2026-06-24: <https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/ifcstructuralanalysisdomain/content.html>
- Conteos de entidades: medidos sobre los tres `.ifc` listados en §1 (2026-06-24).

---

*Evidencia preparada por la IA (PM / Ing. BIM-IFC) · proyecto Aqyra · 2026-06-24 · para la firma de §6 por JM. Tras la firma, arranca el primer corte (§4) en `publico/`.*
