# Contrato C1 — interoperabilidad (IFC ↔ modelo neutro)

> **Ficha autoritativa** (6 campos). Fuente: `Aqyra-Raiz/FUNDACION_C1_y_modelo-neutro.md §1`
> (las fichas de `Aqyra-Raiz` son la fuente; esta copia es la que rige en el monorepo).
> El **esquema ejecutable** de este contrato son los dos `*.schema.json` de esta carpeta.

## Ficha (6 campos)

**Propósito.** Traducir entre el **IFC** (soporte de intercambio abierto) y el **modelo neutro**
(lengua franca del cálculo), en las **dos direcciones**, y escribir los **resultados de vuelta**
al IFC. El resto del motor **nunca conoce IFC**.

**Frontera.** Productor: `engines/ifc` (hoy plugin `iso19650-openbim` + `narracion-ifc`).
Consumidores: **todos** los engines (C3/C5/C9/C10/C11+), los services (C4 federación, C7
operador) y la app (visor).

**Entra.**
- *Parsear:* un IFC (IFC4X3) + la **vía** (analítica o física).
- *Compilar:* un **alto-spec** (`<m>.alto.json`) — ver `alto-spec.schema.json`.
- *Write-back:* resultados por elemento (a Psets), localizados por **GUID**.

**Sale.**
- *Parsear* → **modelo neutro** (JSON) — ver `modelo-neutro.schema.json`.
- *Compilar* → **IFC4X3 autoritativo**, con **doble clasificación** (bsDD + Uniclass).
- *Write-back* → IFC **enriquecido** (Psets de resultado); no cambia geometría.

**Garantía + oráculo.** **Determinista** (misma entrada + misma versión → misma salida).
Golden por **conteo de entidades** y **round-trip** (compilar→parsear reproduce el modelo).
Oráculo: golden `C1-*` (p. ej. `C1-APERTURA-01`, en `packages/golden/C1/`).

**Versión.** SemVer; el consumidor ancla `iso19650-openbim x.y.z` en `versions.lock`.
**Estado: firmado (0.10.0)** aguas arriba; esquema formalizado en el monorepo (schema 0.1.0).

## API abstracta

```
parsear(ifc, vía)               → modelo
compilar(alto_spec)             → ifc
escribir_resultados(ifc, res)   → ifc
```

## Nota multi-código

C1 es **agnóstico al código de comprobación** — solo mueve geometría, datos y clasificación.
Las acciones y la comprobación por código (EC/ACI/AISC/NFPA…) viven en los engines de cálculo
(C9/C10/C11+), **nunca** en C1.

## Regla de evolución del modelo neutro (sagrada)

*Añadir claves nuevas, nunca cambiar la semántica de las existentes.* Una vista nueva no rompe
a un consumidor viejo (retrocompatible; por eso los esquemas son *forward-open*).

---
*La ficha es el diseño; el esquema + la golden son el contrato ejecutable.*
