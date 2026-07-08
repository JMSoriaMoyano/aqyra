# Contrato C5 — presupuesto trazable desde la medición del modelo

> **Ficha autoritativa** (6 campos). Fuente: `Aqyra-Raiz/C5_presupuesto.md` (ficha C5) y
> `Aqyra-Raiz/PLAN_reestructuracion_industrializacion.md §2` (fila C5). El **esquema ejecutable** de
> este contrato son los dos `*.schema.json` de esta carpeta. Decisiones de contrato ancladas en
> `DECISIONES.md` (D1–D5, OK JM 2026-07-03).

## Ficha (6 campos)

**Propósito.** Producir el **presupuesto (PEM/PEC)** a partir de la **medición del modelo**, con
**justificación de mediciones** (trazable hasta el objeto) y **justificación de precios** (cuadros
nº1 y nº2). **La medición no se teclea, nace del modelo:** los `Qto_*` + la doble clasificación de
cada objeto. **Determinista dado criterio + banco.**

**Frontera.** Productor: `engines/presupuesto` (**aún no existe** — contract-first). Consumidores:
**C7** (compone el Documento de Presupuesto con el formato del despacho) y el producto; **write-back**
del coste al IFC vía **C1** (5D). C5 **no redacta** el documento (D1) ni federa (C4) ni certifica.

**Entra.** Ver `entrada-presupuesto.schema.json`:
- **modelo** = **modelo neutro de medición** (por objeto: `{guid, clase, clasificacion(uniclass/bsDD),
  cantidades{tipo: m2|m3|ml|ud, valor, fuente_qto}, ubicacion, cortes}`), la vista de medición del
  Maestro (C1 en modo cantidades). La medición LEE `Qto` (precondición de conformidad: el QA/IDS de C4
  garantiza su presencia aguas arriba — D_modelo).
  - **cortes{}** (E2.1 / D20–D22, N-06, OPCIONAL, aditivo) — atribución del objeto a grupos por los
    cuatro ejes de agrupación: `espacial` (árbol `IfcSpatialStructure`, IFC 4.3 incl.
    `IfcFacility`/`IfcFacilityPart`), `funcional` (`IfcSystem` y/o `IfcZone`), `uniclass`, `gubim`. Cada
    eje es una **lista de pertenencias** `{grupo, fraccion, fuente ∈ {ifc, criterio}}`; la suma de
    `fraccion` de un objeto atribuido a un eje es **1.0** (invariante que `proyectar` usa para
    `Σ == total`). El reparto de frontera **50/50** (tabique entre dos zonas) se resuelve **aquí**, al
    construir el modelo neutro (no en la proyección: el corte es CONSULTA). El eje `funcional` sigue la
    prioridad `IfcSystem` > `IfcZone` > *fallback* del criterio (`reglas_sistema`, `fuente=criterio`).
    Un eje sin agrupación conocida → **ausente**, nunca error. El coste (`estado_mediciones`) **no**
    depende de `cortes`.
- **criterio_ref** — pack `criterio/<id>/<version>` (reglas de medición + mapeo clase→partida).
- **banco_ref** — pack `banco/<id>/<version>` (precios descompuestos).
- **parametros** — `{moneda, iva_pct, gg_pct, bi_pct}`.

**Sale.** Ver `salida-presupuesto.schema.json` (artefacto AUTORITATIVO, D1):
- **estado_mediciones[]** — por partida `{codigo, descripcion, unidad, cantidad, precio_unitario,
  importe, criterio_aplicado, origen ∈ {modelo, regla, manual}, trazabilidad:[guids]}`. Cada cantidad
  se justifica hasta los GUIDs que la producen.
  - **valores{}** (E1.1 / D16–D18, OPCIONAL, aditivo) — eje de valor **multi-eje**: mapa
    `id-de-eje → {unitario, total, unidad, banco?, etapas?}`. El eje **coste** canónico **no** vive
    aquí (D16): sigue en `precio_unitario`/`importe`; `valores` abre la partida a otros ejes
    (`carbono`, `agua`, …) sin duplicar ni cambiar el coste. Un eje sin banco para la partida → su
    clave **ausente**, nunca error. `etapas` = desglose EN 15978 (`A1A3`, `A4A5`, …) con Σ = `total`.
- **cuadro_precios_1[]** — precio unitario en cifra y en letra.
- **cuadro_precios_2[]** — descompuesto (MO + materiales + maquinaria + costes indirectos), justificación.
- **resumen** — parciales por capítulo → **PEM** → (+GG +BI) → base → (+IVA) → **PEC**.

**Garantía + oráculo.** **Determinista dado criterio + banco** (mismo modelo + mismo criterio + mismo
banco → mismo presupuesto). El **presupuesto esperado** de la golden es el oráculo, **medición manual
de referencia** congelada, cubierta por el tag GPG del cierre (Llave 2). Oráculo: golden `GOL-PRE-01`
(en `packages/golden/C5/`) — **modo ANCLADO** (presupuesto calculado a mano y verificado ×2 sobre la
medición del C4-FED-06) hasta que el engine exista. El valor del golden es **consistencia y
no-regresión**, no verdad física — el PEM es una **convención** (criterio + banco), no una ley.

**Versión.** SemVer; el consumidor ancla `presupuesto x.y.z` **+** `criterio vN` **+** `banco vN` en
`versions.lock` (`[contracts.C5]` + `[packs.criterio]` + `[packs.banco]`). Sin los tres, el mismo
modelo daría otro número. **Estado: contract-first** (2 esquemas 0.1.0 + packs `criterio/AQ/v1` y
`banco/AQ-DEMO/v1` mínimos + `GOL-PRE-01` anclada; el engine `engines/presupuesto` llega en un hilo
posterior).

## API abstracta

```
presupuestar(modelo_medicion, criterio, banco, parametros) → presupuesto
    (estado de mediciones + cuadros nº1/nº2 + resumen PEM→PEC)
```

## Qué NO es (fronteras honestas)

- **No redacta el Documento de Presupuesto** (PDF/Word con formato de despacho): eso lo compone **C7**.
  C5 produce el JSON autoritativo (D1).
- **No mide geometría a ciegas:** lee `Qto`. Si el modelo no los declara, la medición cojea — es un
  problema de **calidad del IFC** que el QA/IDS de C4 debe atajar aguas arriba, no un `if` del engine.
- **No inventa el criterio ni el banco:** son **packs** versionados de `data/`, anclados por hash.
  Cambiar de criterio/banco/año = cambiar de pack, no de engine.
- **No hace el write-back** (eso es C1, 5D) ni certifica (la firma es de la persona, Llave 2).

## Regla de evolución (heredada de C1/C3/C4, sagrada)

*Añadir claves nuevas, nunca cambiar la semántica de las existentes.* Los dos esquemas son
*forward-open*. La taxonomía de `origen` es un enum **cerrado** de 3 valores (`modelo`/`regla`/`manual`,
D5): un origen futuro se reclasifica dentro del mismo enum, no lo amplía. En cambio, el **id de eje**
de `valores{}` es un `string` **abierto** por convención (D17): añadir un eje nuevo (carbono, agua…)
**no** re-ancla el contrato — la disciplina de nombres es de pack/criterio, no del esquema.

---
*La ficha es el diseño; los esquemas + la golden + los packs son el contrato ejecutable.*
