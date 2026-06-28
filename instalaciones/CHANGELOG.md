# CHANGELOG — instalaciones

Versionado SemVer. Todo resultado es de predimensionado/asistencia y debe ser
revisado y firmado por tecnico competente.

## v0.3.0 (2026-06-22) — vertical ELECTRICO (REBT): bases de demanda + solver + write-back (Ola 4, PT 4.5)

- **Segundo vertical de la disciplina: instalaciones ELECTRICAS de baja tension (REBT).**
  Otro solver **sobre el mismo grafo de red** (el primero es el hidraulico); BT radial → se
  reutiliza la **propagacion por arbol** del solver hidraulico (`red/solver_red._arbol_desde_fuente`),
  sin Hardy-Cross y sin duplicar el grafo. Frontera C1/CN-3 intacta.
- **Bases de demanda electrica (CN-3).** `scripts/electrico/bases_demanda_electrica.py` (NUEVO):
  modo **vivienda** (ITC-BT-25: circuitos C1–C12, Fu/Fs, grado de electrificacion basica/elevada,
  ITC-BT-10) y modo **receptores** (terciario/industrial: catalogo luminaria/toma/motor/clima,
  ITC-BT-44/-47). Dispatcher `aplicar_demanda_electrica`. El dato del IFC prevalece. `[confirmar AN]`.
- **Solver de red electrica.** `scripts/electrico/solver_electrico.py` (NUEVO): reparto de potencias
  por arbol; **intensidad** I=P/(U·cosφ) mono / P/(√3·U·cosφ) tri; **propuesta de seccion** por
  momentos + **intensidad admisible** (ITC-BT-19, PVC/XLPE, Cu/Al); **caida de tension** acumulada
  por el **metodo de las intensidades** (I·R con cosφ) y **redimensionado** automatico si supera el
  limite (3 % alumbrado / 5 % fuerza). Catalogo de secciones normalizadas. `[confirmar AN]`.
- **Arnes** `scripts/electrico/verificacion_electrico.py` (NUEVO): **balance de potencias** (~0 %),
  caida de tension acumulada ≤ limite e intensidad ≤ admisible. **Micro-test**
  `scripts/electrico/test_solver_electrico.py` (NUEVO): caida de tension mono/tri contra calculo
  analitico, balance de potencias y redimensionado (14/14 OK).
- **Write-back electrico.** `scripts/electrico/resultado_ifc_electrico.py` (NUEVO, stdlib): mapping
  de `Pset_Estructurando_ResultadoRed` (seccion, intensidad, caida de tension, potencia, fases). La
  **mecanica** IFC la aporta `iso19650-openbim` (v0.4.2, validador **sistema-aware**: exige
  `Pset_CableSegmentTypeCommon` en ELECTRICAL). **Orquestador** `scripts/electrico/run_all_electrico.py`.
- **Subagente `proyectista-electrico`** (NUEVO) + agente `ingeniero-de-instalaciones` ampliado
  (enruta ELECTRICAL → REBT; catalogo de sistemas).
- **Casos e2e** `caso-REBT-01-vivienda` (8 circuitos, ΔU máx 1,098 %) y `caso-REBT-02-terciario`
  (mono/tri, ΔU máx 3,318 %): IFC ELECTRICAL → demanda → solver → verificacion **CUMPLE** (balance
  0,0 %) → Psets de resultado al IFC, validado **APTO**. Memoria md+docx.
- **Nucleo transversal espejado intacto** (identico al canonico del motor v0.23.0).

## v0.2.0 (2026-06-22) — rociadores + solver de mallas + write-back (Ola 4, PT 4.4)

- **Solver de MALLAS (Hardy-Cross).** `scripts/red/solver_red.py` resuelve ahora el reparto
  **hiperestatico** en redes con bucles: base de **ciclos fundamentales** (cuerdas del arbol
  generador), correccion por lazo (n=2, friccion reevaluada por iteracion) imponiendo
  **continuidad en nudos + perdida de carga nula por lazo**. El **arbol** es el caso de 0 lazos
  (**sin regresion**: caso PCI-01 byte a byte). Caudal con **signo** por tramo (`sentido`,
  `caudal_signed_l_s`) y bloque `topologia`/`hardy_cross` en la salida.
- **Arnes ampliado.** `scripts/red/verificacion_red.py`: **balance nodal con signo** (vale en
  arbol y malla) + **cierre de perdida por lazo** (~0 kPa). Micro-test `test_solver_red.py`:
  malla de 1 lazo (reparto analitico 50/50) y de **2 lazos** (balance nodal + cierre).
- **Rociadores automaticos (UNE-EN 12845).** `scripts/pci/bases_demanda.py`: rama de rociadores
  por **densidad x area de operacion** (LH/OH1-4/HHP), nº del area mas desfavorable
  `n = ⌈A_op/A_cob⌉`, **K** (Q=K·√p), caudal de diseno y presion en boquilla; dispatcher
  `aplicar_demanda` (BIE vs rociadores). `[confirmar AN]`.
- **Write-back de Psets de resultado.** `scripts/red/resultado_ifc.py` (NUEVO, stdlib) construye
  el mapping `Pset_Estructurando_ResultadoRed` (DN, caudal, velocidad, presion, margen) del
  resultado; la **mecanica** IFC la aporta `iso19650-openbim:ifc-create` (v0.4.1).
- **Subagente `proyectista-pci`** ampliado (rociadores + malla + write-back); agente
  `ingeniero-de-instalaciones` con la etapa de write-back y mallas.
- **Caso e2e** `caso-PCI-02-rociadores-malla` (IFC mallado 3 lazos → demanda OH1 → Hardy-Cross →
  verificacion **CUMPLE**, balance 0,0 %, cierre lazo 5·10⁻⁶ kPa → Psets de resultado al IFC,
  validado APTO). Memoria md+docx.
- **Nucleo transversal espejado intacto** (identico al canonico del motor v0.23.0).

## v0.1.0 (2026-06-22) — nace la disciplina (Ola 4, PT 4.3)

- **Nuevo plugin `instalaciones`** + agente `ingeniero-de-instalaciones` y subagente
  `proyectista-pci` (vertical PCI; electricas/clima esbozadas).
- **Motor hidraulico de red** (capacidad transversal del ecosistema, nace aqui):
  `scripts/red/solver_red.py` — reparto de caudales en arbol, perdida de carga
  **Darcy-Weisbach** (Swamee-Jain), propagacion de presiones con cota, comprobacion
  de terminales; `scripts/red/verificacion_red.py` — balance de caudales (~0 %) y
  presiones; micro-test `scripts/red/test_solver_red.py`.
- **Bases de demanda (hueco H3, contrato CN-3):** `scripts/pci/bases_demanda.py` —
  rellena `demanda` para PCI (BIE) segun RIPCI/UNE-EN 671/UNE 23500/DB-SI [confirmar AN].
- **Orquestador** `scripts/pci/run_all_pci.py` (modelo neutro -> demanda -> solver ->
  verificacion).
- **Nucleo transversal espejado** en `scripts/nucleo/` (identico al canonico del motor;
  control de identidad entre espejos en la puerta de empaquetado).
- **Skill** `criterios-memoria` (C2/C3).
- **Caso e2e** `caso-PCI-01-bie-presion` (red PCI leida por el parser MEP del PT 4.2 ->
  demanda -> solver -> verificacion **CUMPLE**, balance 0,0 %).
- Frontera confirmada: lectura IFC MEP en `iso19650-openbim`; demanda + calculo aqui.
