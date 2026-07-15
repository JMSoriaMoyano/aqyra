# Tareas · La proyección (E2.2)

> Gobernado por `docs/PROCESO_SDD.md`. Comportamiento NUEVO sobre el engine C5 + salida EXTENDIDA
> (forward-open). La golden de coste **no se mueve**. El contrato C5, `data/packs`, `packages/golden` y
> `engines/` están en la frontera CODEOWNERS → el merge es firma de JM (Llave 2). Gobierna **N-06** (D-028)
> y continúa E2.1 (`c5-cortes-agrupaciones-nativas`, en `main`).

## Paso 0 · Ratificación (BLOQUEA el código) — HECHO
- [x] JM ratifica **D24** (firma de `proyectar` = `(presupuesto, modelo, eje, corte)`; recibe el modelo).
- [x] JM ratifica **D25** (lectura del eje: `coste`→`importe`; no-coste→`valores[eje].total`; unidad del eje).
- [x] JM ratifica **D26** (atribución partida→objeto = **por magnitud EXACTA**; el engine emite `traza_cantidades`).
- [x] JM ratifica **D27** (residuales deterministas: `(sin geometría)` / `(sin clasificar)` → Σ EXACTO).
- [x] JM ratifica **D28** (anclaje `GOL-PRE-03` = DETERMINISMO + SEMÁNTICA + INVARIANTE, sin md5 de salida).
- [x] JM ratifica **D29** (fixtures aumentadas de `GOL-PRE-01`; `GOL-PRE-03` caso NUEVO con `criterio/AQ/v2`).
- [x] Anclar D24–D29 en `packages/contracts/C5-presupuesto/DECISIONES.md` (continúan D1–D23).

## Paso 1 · Rama (primero, tras ratificar) — PENDIENTE (host)
- [ ] Crear y cambiar a `feat/c5-proyeccion-vista` desde `origin/main` (git por `.bat` en el host).

## Paso 2 · Contrato (esquema, forward-open) — HECHO
- [x] `salida-presupuesto.schema.json`: `partida_medida` gana `traza_cantidades` (opcional) + `$defs.traza_cantidad`
      (`{guid:string, cantidad:number}`). **JSON válido a verificar** en el paso de test.
- [ ] `contrato.md`: documentar `traza_cantidades` (desglose por objeto para la proyección; sólo `origen=modelo`).

## Paso 3 · Engine — emisión del desglose (aditivo, D26) — HECHO
- [x] `presupuesto.py`: acumular `cantidad_O` por `(codigo, guid)` en el bucle de mapeo; emitir
      `traza_cantidades:[{guid,cantidad}]` por partida `origen=modelo`. Coste byte-idéntico (recompute
      compara claves nombradas → `GOL-PRE-01` verde).
- [x] `pyproject.toml`: bump `aqyra-presupuesto` 0.3.0 → **0.4.0** (aditivo).

## Paso 4 · Engine — `proyectar` (NUEVO módulo, group-by puro) — HECHO
- [x] `proyeccion.py`: `proyectar(presupuesto, modelo, eje, corte)` (D24–D27). Lee el valor por partida
      (D25), reparte por magnitud EXACTA (D26, `traza_cantidades`), de objeto a grupo por `fraccion` de
      `cortes[corte]` (E2.1), residuales (D27). Determinista (orden por aparición).
- [x] `__init__.py`: exportar `proyectar`.

## Paso 5 · Test puro (sandbox, sin ifcopenshell) — la Llave 1 del path puro
- [x] `tests/test_proyeccion.py`: invariante `Σ == total` por eje/corte; reparto por magnitud EXACTA
      (pesos ≠ ⇒ shares ≠); residuales (S&S sin trazabilidad → `(sin geometría)`; objeto sin corte →
      `(sin clasificar)`); determinismo (2× igual); eje coste (importe) y eje no-coste (`valores[eje]`).
- [ ] Correr `test_proyeccion.py` en el **sandbox** (path puro, no exige ifcopenshell).

## Paso 6 · Golden de vista `GOL-PRE-03` (caso NUEVO, patrón `GOL-PRE-02`)
- [ ] `gen_fixtures.py`: genera `entrada/ARQ.ifc`+`EST.ifc` aumentadas (árbol 4.3 + `IfcSystem` + `IfcZone`
      +espacios+`IfcRelSpaceBoundary`) de forma determinista desde las de `GOL-PRE-01`. **Conda `mcp-bim`.**
- [ ] `entrada.json` (fuente_maestro → fixtures aumentadas + md5 propios; `criterio_ref=AQ/v2`;
      `banco_ref=AQ-DEMO/v1`; `parametros` = los de `GOL-PRE-01`).
- [ ] `expected.json` (`modo:"proyeccion"`): `entradas_md5` + las CINCO vistas (grupos, `valor_total`,
      `fuente`) computadas del caso + `cost.PEM/PEC` de referencia. `tolerancias.json` (`importe_abs`).
- [ ] `ficha.md`: qué ancla y por qué (patrón `GOL-PRE-02`).

## Paso 7 · Runner — rama `proyeccion` (solo AÑADE) — HECHO (código); PENDIENTE (verde en CI)
- [x] `run_golden.py`: `run_case_c5` dispatch `modo=="proyeccion"` → `_run_c5_proyeccion`
      (identidad + DETERMINISMO + INVARIANTE + SEMÁNTICA de las 5 vistas; ancla `criterio/AQ/v2` por su
      `content_sha256`). C1/C3/C4 y las otras ramas C5 **sin tocar**.
- [ ] `GOL-PRE-01/02`/`GOL-DOC-01` siguen verdes; `GOL-PRE-03` verde (conda `mcp-bim` → CI).

## Paso 8 · No-regresión + versión
- [ ] `versions.lock [contracts.C5]`: `engine_version` 0.3.0 → **0.4.0** (salida gana `traza_cantidades`;
      proyección añadida). `schema_version` sin subir (aditivo de una clave opcional; se documenta).
- [ ] Verificar en el conda `mcp-bim` (patrón E2.1): `pytest` de `engines/presupuesto` + goldens C5.

## Pasos obligatorios (Llave 1)
- [ ] `adversarial-review c5-proyeccion-vista`: engine importa/compila; `proyectar` determinista; golden
      C5 verde; ningún `expected` de `GOL-PRE-01/02/DOC-01` alterado; ninguna clave existente con semántica
      cambiada; `criterio/AQ/v1` intacto.
- [ ] `opsx:archive` → **PR** `feat/c5-proyeccion-vista` → `main`; gate verde (Llave 1).
- [ ] **Llave 2 = JM** (merge/firma). **SIN release**.

## Fuera de estas tareas
- Ingesta/emisión BC3 (E0.1/E0.2, siguientes changes del hilo) · `banco-carbono`/`GOL-CAR-01` (Ola 2) ·
  dashboard (E6) · tocar el motor económico, el parser de cortes de E2.1 o el runner base.
