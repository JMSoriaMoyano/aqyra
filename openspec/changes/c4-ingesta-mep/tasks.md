# Tareas · c4-ingesta-mep (contract-first, baby steps; git por .bat, dos llaves)

## Paso 0 · Fixture (precondición del golden, D-MEP-5)
- [x] `tools/gen_fixture_mep.py` (ifcopenshell): extrae 1–2 `IfcDistributionSystem` del modelo real
      + sus elementos + relaciones, escribe `packages/golden/CMEP/fixtures/mep_min.ifc` DETERMINISTA.
- [x] Fixture generado+validado con conda `mcp-bim`; anclado `mep_min.ifc` por md5 (8d56937d…) en `versions.lock` (sección `[golden.cmep]`).

## Paso 1 · Contrato + esquema (ANTES del engine)
- [x] Esquema `modelo-neutro.schema.json`: clave `instalaciones` (vista_mep: elemento_mep + sistema_mep), forward-open; diff = solo añadidos.
- [x] Golden `GOL-MEP-01` (contrato CMEP) + `run_case_cmep`/`CASE_RUNNERS["CMEP"]` en run_golden.py: conteo por CLASE EXACTA (7/10), elemento→sistema (5/3/2 sin sistema), sistemas+PredefinedType, cota de planta. Modo anclado verificado (rojo sin engine).

## Paso 2 · Engine (apply)
- [x] `engines/ifc/ifc_to_model_mep.py`: IFC→vista MEP (7 clases exactas, sistemas por IfcRelAssignsToGroup+IfcRelServicesBuildings, elevationMetric por planta) reutilizando `aqyra_core.ifc_utils` SIN tocar el núcleo anclado.
- [~] `services/federacion` estructura_funcional: DIFERIDO (rompería los 6 golden C4-FED anclados; baby-step siguiente con su golden C4). Decidido con JM 2026-07-17.
- [x] Recompute `GOL-MEP-01` VERDE verificado byte-exacto (fixture canónico md5 8d56937d…, ifcopenshell); Llave 1 = gate CI.

## Paso 3 · Visor (consumo, apps/ Llave 1)
- [~] Visor (enumerar MEP + «Estructura funcional»): DIFERIDO al skin de Instalaciones F5.1 (consumo aguas abajo que este change desbloquea). Decidido con JM 2026-07-17.

## Pasos obligatorios
- [ ] adversarial-review · gate verde (Llave 1) · **Llave 2 JM** · archivar el change.
- [ ] No tocar zona anclada (fixtures edificación, E2E, cámara D29, golden C4/C3, versions.lock salvo la
      fila nueva del fixture MEP).
