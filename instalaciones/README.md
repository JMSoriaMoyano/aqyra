# instalaciones — disciplina de Instalaciones (PCI / electricas / clima)

Plugin de la **disciplina Instalaciones** del ecosistema *Estructurando* (Ola 4).
Monta **solvers de red** sobre el **modelo neutro de red** del dominio IFC MEP, **sin
reimplementar el nucleo**. Dos verticales OK: **PCI** (BIE y **rociadores** UNE-EN 12845;
motor hidraulico de red Darcy-Weisbach, **arbol o malla** Hardy-Cross) y **electricas
(REBT)** (redes de BT **radiales**: intensidad, seccion y caida de tension, **otro solver
sobre el mismo grafo**). Clima (RITE) queda esbozado.

## Arquitectura (frontera de contratos)

- **C1 — lectura/escritura IFC (en `iso19650-openbim`, no aqui):** `scripts/mep/
  ifc_to_model_mep.py` traduce IFC MEP -> modelo neutro de red; el write-back de Psets de
  resultado lo escribe `ifc-create:escribir_psets_resultado.py`. Este plugin **consume** y
  aporta la **semantica**.
- **CN-3 — bases de demanda (aqui):** PCI `scripts/pci/bases_demanda.py` (BIE:
  simultaneidad/caudal/presion; rociadores: densidad x area) — hueco **H3**; REBT
  `scripts/electrico/bases_demanda_electrica.py` (potencias, cosphi, fases, tension —
  ITC-BT-10/25/44/47).
- **Calculo (aqui):** PCI `scripts/red/solver_red.py` (Darcy-Weisbach; **Hardy-Cross** en
  malla) + `scripts/red/verificacion_red.py`; REBT `scripts/electrico/solver_electrico.py`
  (intensidad, seccion, caida de tension) + `scripts/electrico/verificacion_electrico.py`.
- **Write-back (aqui, semantica):** `scripts/red/resultado_ifc.py` (PCI) y
  `scripts/electrico/resultado_ifc_electrico.py` (REBT) arman el mapping de
  `Pset_Estructurando_ResultadoRed`.
- **Nucleo transversal (espejo):** `scripts/nucleo/` (`ifc_utils` + `grafo_red`, PT 4.1).
  **Identico** al canonico del motor; no editar (control de identidad en el empaquetado).

## Uso

```
# 1) IFC MEP -> modelo neutro (plugin iso19650-openbim)
python3 ifc_to_model_mep.py red.ifc modelo_neutro_mep.json
# 2a) PCI: demanda -> solver hidraulico -> verificacion
python3 scripts/pci/run_all_pci.py modelo_neutro_mep.json [outdir]
# 2b) REBT: demanda electrica -> solver electrico -> verificacion -> mapping write-back
python3 scripts/electrico/run_all_electrico.py modelo_neutro_mep.json [outdir]
# 3) write-back de resultados al IFC (la mecanica la aporta iso19650-openbim:ifc-create)
python3 scripts/red/resultado_ifc.py modelo_neutro_mep.json <base>_resultado.json mapping.json
```

Salidas: `<base>_demanda.json`, `<base>_resultado.json`, `<base>_verificacion.json`.

## Agentes

- `ingeniero-de-instalaciones` — clasifica el sistema (PCI/REBT/clima), enruta, orquesta y write-back.
- `proyectista-pci` — subagente del vertical PCI (BIE y rociadores).
- `proyectista-electrico` — subagente del vertical electrico (REBT, BT radial).

## Solver de red

Reparto de caudales por continuidad (**arbol**) y **reparto hiperestatico Hardy-Cross**
(**malla**: continuidad en nudos + perdida nula por lazo); perdida de carga **Darcy-Weisbach**
(Swamee-Jain), propagacion de presiones desde la(s) fuente(s) con cota, comprobacion de caudal
y presion en terminales. Hipotesis y NDP **[confirmar AN]** (agua 20 C, rugosidad en mm,
accesorios +20 %, v_max 6 m/s). Micro-test: `scripts/red/test_solver_red.py` (arbol + mallas).

## Solver electrico (REBT)

**Otro solver sobre el mismo grafo de red.** BT de interior **radial** -> reutiliza la
propagacion por arbol del solver hidraulico (`red/solver_red._arbol_desde_fuente`), sin
Hardy-Cross. Intensidad I=P/(U.cosphi) mono / P/(sqrt3.U.cosphi) tri; **seccion** por
momentos + **intensidad admisible** (ITC-BT-19, Cu/Al, PVC/XLPE); **caida de tension** por
el metodo de las intensidades, acumulada con **redimensionado** si supera 3 % (alumbrado) /
5 % (fuerza). NDP **[confirmar AN]** (gamma Cu 56 / Al 35). Micro-test:
`scripts/electrico/test_solver_electrico.py`.

Todo es **predimensionado/asistencia**; a revisar y firmar por tecnico competente.
