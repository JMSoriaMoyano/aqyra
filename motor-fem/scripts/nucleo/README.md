# Núcleo transversal — utilidades IFC + grafo de red (PT 4.1, Ola 4)

Capacidad **compartida y agnóstica al solver** que extrae lo común a todas las
disciplinas (estructuras, instalaciones, obras lineales) al leer un IFC y al
construir la topología de una red de elementos lineales. Resuelve el hueco **H1**
de la verificación de la Ola 1 y la **decisión abierta nº4** de la hoja de ruta
(incubado aquí, en `scripts/nucleo/`, para promoverse/espejarse a módulo
compartido cuando nazca el plugin `instalaciones`).

> Devuelve **datos** (nodos + tramos + topología), **no calcula**. El solver
> (FEM estructural, hidráulico Darcy/Manning, eléctrico, térmico) y la
> verificación normativa viven en **cada disciplina**.

## `ifc_utils.py` — lectura IFC (antes duplicada por parser)

| Función | Qué hace |
|---|---|
| `psets(element)` | Property Sets → `{Pset: {Prop: valor}}` |
| `length_scale(ifc)` | Factor de unidad de longitud del `IfcUnitAssignment` → metros (mm→m, pulgada/pie) |
| `pset_value(ifc, pset, prop, def_)` | Valor puntual de una propiedad (p. ej. `Snap_tol_m`); el Pset es parámetro |
| `matmul / apply / to_list4 / ident4` | Álgebra homogénea 4×4 |

## `grafo_red.py` — grafo nodos+tramos

Primitivas (consumidas por `puente_analitico/puente.py` con **retrocompatibilidad
byte a byte** de la serie R):

- `RegistroNodos(tol)` — fusión de nudos por tolerancia (snap), representante "primero añadido".
- `proyeccion(p,a,b)`, `punto_en_segmento(p,a,b,tol)`, `bbox_xy(esquinas)`.
- `cortes_por_interseccion(segmentos, tol)` — puntos de troceo T/X por segmento.
- `ordenar_segmento(p0,p1,extra)` — puntos ordenados por parámetro t.
- `filtrar_componentes_desconectadas(nodos, tramos, es_ancla)` — union-find genérico
  (en estructuras `es_ancla`=nudo apoyado; en MEP=nudo fuente).

API de alto nivel (**gancho H2 / MEP**): un futuro `ifc_to_model_mep.py` la alimenta
con segmentos de `IfcDistributionPort`/`IfcRelConnectsPorts` **sin tocar el núcleo**:

```python
grafo = grafo_red.construir_grafo(segmentos, tol)
#   segmentos = [{"p0":[x,y,z], "p1":[x,y,z], "payload":{...}}, ...]
#   -> {"nodos":{...}, "tramos":{...}, "metricas":{...}}
```

## Micro-test

`python3 test_grafo_red.py` — valida intersección / snap / troceo T/X / union-find
y la API de alto nivel (exit ≠ 0 si falla).

---
*Predimensionado/asistencia; a revisar y firmar por técnico competente. NDP marcados `[confirmar AN]`.*
