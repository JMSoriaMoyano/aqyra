# Tareas · export-firmable-proyeccion

- [x] Paso 0 · Ratificar D-EX-1..D-EX-5 y anclar en `documentos/export/DECISIONES.md`.
- [x] Paso 2 · Contract-first: `descriptor-export.schema.json` + `manifiesto-export.schema.json`
      (forward-open) + golden `GOL-EXP-01` (oraculo por contenido) ANTES del modulo.
- [x] Paso 1 (D-EX-1 A) · `documentos/comun` (`aqyra-documento-comun`): formato del despacho extraido.
- [x] Paso 3 · Nucleo `documentos/export`: `componer_export` = manifiesto (procedencia + hash + sello
      determinista) + sellado (PDF pure-python) + firma (integridad gate / GPG release). Sin LLM.
- [x] Paso 4 · Consumidor PRIMARIO CONTRACTUAL (presupuesto-obra, redireccion JM 2026-07-12): ENVUELVE
      componer_documento (Word) + emitir_bc3 (BC3) + PDF sellado (con justificacion de medicion criterio+GUIDs)
      + XLSX. Proyeccion = consumidor de gestion (secundario). Pliego = slice siguiente.
- [x] Paso 5 · Goldens `GOL-EXP-01` (presupuesto contractual, PRIMARIO) + `GOL-EXP-02` (proyeccion, gestion),
      rama `modo=export` -> despacho por consumidor en `run_case_c5`. VERDES en sandbox (13 + 13 checks).
- [x] Paso 6 · No-regresion (GOL-PRE-03/DOC-01/PLI-01 + documentos + dashboard) INTACTOS; `versions.lock
      [documentos.comun]`/`[documentos.export]` NUEVOS; workspace + ci.yml + release.yml quirurgicos.
- [ ] Cierre · adversarial-review -> archive -> PR `feat/export-firmable-proyeccion` -> main (Llave 1).
- [ ] Llave 2 · firma GPG de JM + release `documento-export-v0.1.0`.
