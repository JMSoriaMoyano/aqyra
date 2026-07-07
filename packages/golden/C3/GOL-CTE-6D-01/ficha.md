# Golden GOL-CTE-6D-01 — el cumplimiento vuelve al modelo (write-back 6D)

> El segundo caso del contrato **C3**: hace **6D** el modelo que `GOL-CTE-01` verificó. El veredicto
> de cumplimiento (por elemento) vuelve al IFC en un **Property Set de marca** `Pset_Aqyra_Cumplimiento`,
> para que el visor lo LEA y pinte (D-6D-1). Auditable hasta el elemento. `GOL-CTE-01` queda intacto.

## Flujo (runner `run_case_c3`, rama 6D)

1. **Federar + derivar** las fixtures con el Maestro (`reglas.json`, patrón C4-FED-06) → derivado (la
   vista que abre el visor). El engine ABRE el derivado, no federa (D7).
2. **Verificar** (engine C3, reutiliza 3.3) → veredicto por exigencia (reproduce `GOL-CTE-01`).
3. **`escribir_cumplimiento(veredicto, maestro, salida)`** → IFC 6D con, por elemento:
   `Pset_Aqyra_Cumplimiento` = `Resultado` (peor caso, D-6D-2) + `Exigencia` dominante +
   `DocumentoBasico` + `Apartado` + `Pack` (+ `MotivoNoVerificable` si `no-verificable`).

## Qué ancla (opción b — sin md5 hardcodeado, EOL-frágil)

- **DETERMINISMO:** escribir el 6D **dos veces** produce **bytes idénticos** (cabecera SPF con firma
  fija sin versión + `time_stamp` constante + GUIDs `uuid5`, patrón `derivar`/`escribir_coste`).
- **SEMÁNTICA:** el `Pset` **casa con el veredicto proyectado a elementos por peor caso** — proyección
  **INDEPENDIENTE** del runner (`_proyectar_peor_caso_6d`, reimplementa la regla D-6D-2 sin importar el
  engine) que debe coincidir con el `Resultado`/`Exigencia` escritos; cobertura total (todo elemento
  del Maestro recibe un `Resultado`); conteos `por_resultado` (IFC) == expected == proyección; el
  veredicto agregado es `no-conforme`.

## Peor caso (D-6D-2) sobre el veredicto de GOL-CTE-01

`E-SI-RF-DECL` es **no-cumple** con `por_modelo` para ARQ y EST; domina la severidad
(`no-cumple`≻`no-verificable`≻`cumple`; `no-aplica` neutro) en **todos** los elementos de ambos
submodelos federados → **todos `no-cumple`**, `Exigencia` = `E-SI-RF-DECL`.

## Regla de oro

Un fallo NO se arregla aflojando el check: se investiga el ENGINE (`escritura.py`). Las fixtures y el
derivado son los del 2.6/3.2 — **`GOL-CTE-01` y la zona anclada quedan intactos** (más checks, nunca menos).
