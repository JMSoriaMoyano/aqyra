# Tareas · Los cortes nacen del IFC (E2.1)

> Gobernado por `docs/PROCESO_SDD.md`. **EXTIENDE** el contrato C5 + el parser (forward-open). La golden
> de coste **no se mueve**. El contrato C5 y `data/packs` están en la frontera CODEOWNERS → el merge es
> firma de JM (Llave 2). Gobierna **N-06** (D-028).

## Paso 0 · Ratificación (BLOQUEA el código) — HECHO
- [x] JM ratifica **D20** (forma de `cortes{}` = lista de pertenencias `[{grupo, fraccion, fuente}]`).
- [x] JM ratifica **D21** (reparto de frontera 50/50 fijo, materializado en el parser; regla `1/N` por
      espacio agregada por zona; (c) por superficie = gancho forward). *No reabre N-06.*
- [x] JM ratifica **D22** (*fallback* funcional = `criterio/AQ/v2` nuevo = v1 + `reglas_sistema`, sin
      re-anclar v1; taxonomía `Ss` de Uniclass).
- [x] JM ratifica **D23** (fixtures aumentadas de `GOL-PRE-01`; golden de vista `GOL-PRE-03` es caso
      NUEVO en E2.2, no edita `GOL-PRE-01`).
- [x] Anclar D20–D23 en `packages/contracts/C5-presupuesto/DECISIONES.md` (continúan D1–D19).

## Paso 1 · Rama (primero, tras ratificar) — PENDIENTE (host)
- [ ] Crear y cambiar a `feat/c5-cortes-agrupaciones-nativas` desde `origin/main` (git por `.bat` en el host).

## Paso 2 · Contrato (esquema, forward-open) — HECHO
- [x] `entrada-presupuesto.schema.json`: `objeto_medicion` gana `cortes` (opcional) + `$defs.cortes` +
      `$defs.corte_eje` (lista) + `$defs.pertenencia` (`{grupo, fraccion(0..1, default 1.0),
      fuente∈{ifc,criterio}}`). **JSON válido verificado.**
- [ ] `contrato.md`: documentar `cortes`, la convención de `fuente` y el invariante `Σ fraccion == 1`.

## Paso 3 · Pack criterio v2 (fallback) — HECHO
- [x] `data/packs/criterio/AQ/v2/`: v1 (mapeo IDÉNTICO) + `reglas_sistema` **por jerarquía de tipos IFC** (24 reglas → **10 familias** de dominio + default; `Ss` Uniclass). Cubre el centenar de clases sin enumerarlas.
- [x] Golden de pack `content_sha256` de v2 (`079c28e9…`) + `md5_criterio` (`4e0f56e4…`). **Verificado** (content_hash==golden, md5==manifiesto, mapeo v1==v2, v1 intacto, fallback por supertipo probado).
- [x] `criterio/AQ/v1` y su hash **intactos** (no se re-ancla `[packs.criterio]`: sigue en v1 → GOL-PRE-01).

## Paso 4 · Parser (apply — solo lo afectado) — HECHO
- [x] `modelo.py`: `espacial_de` (árbol 4.3), `sistemas_de` (`IfcSystem`), `zonas_de`
      (`IfcZone`→`IfcSpace`→`IfcRelSpaceBoundary`, reparto `1/N`), `cortes_clasificacion`, `is_external_de`,
      `cortes_de` (funcional por prioridad IfcSystem > IfcZone > fallback criterio) + puras `_agregar`/`reparto_zonas`/`sistema_fallback`.
- [x] `medicion.py`: `_objeto_neutro` adjunta `cortes`; `medir(fuentes, criterio=None)` pasa el criterio para el *fallback*.
- [x] Motor económico, cuadros, `resumen`, `presupuestar`, `escritura.py` y el runner **sin tocar**.

## Paso 5 · Test (la Llave 1 de E2.1)
- [x] `tests/test_cortes.py` bloque **puro** (reparto 50/50, fallback): **verificado en el sandbox** (sin ifcopenshell).
- [ ] `tests/test_cortes.py` bloque **integración** (IFC4 mínimo self-built: árbol + `IfcSystem` +
      `IfcZone`+espacios+`IfcRelSpaceBoundary`): **verificar en el conda `mcp-bim`** (el sandbox de
      desarrollo no trae ifcopenshell). El 50/50 en un tabique compartido y el *fallback* `fuente=criterio` se comprueban aquí.
- [x] `packages/packs/tests/test_packs.py`: tests de `criterio/AQ/v2` (manifiesto + identidad + superset de v1).

## Paso 6 · No-regresión — PENDIENTE (CI / conda)
- [x] Analizado: `_diff_medicion_c5` sólo compara cantidades por GUID e ignora claves extra → `cortes` no altera la medición.
- [ ] `run_case_c5` deja `GOL-PRE-01` **verde y byte-idéntica**; `GOL-PRE-02` y `GOL-DOC-01` verdes (CI).

## Pasos obligatorios (Llave 1)
- [ ] `adversarial-review c5-cortes-agrupaciones-nativas`: engine importa/compila; golden C5 verde;
      ningún `expected` alterado; ninguna clave existente con semántica cambiada; `criterio/AQ/v1` intacto.
- [ ] `opsx:archive` → **PR** `feat/c5-cortes-agrupaciones-nativas` → `main`; gate verde (Llave 1).
- [ ] **Llave 2 = JM** (merge/firma). **SIN release**.

## Fuera de estas tareas
- `proyectar()` + golden de vista `GOL-PRE-03` (E2.2, segundo change del hilo) · `banco-carbono`/`GOL-CAR-01`
  (Ola 2) · ingesta/emisión BC3 (E0).
