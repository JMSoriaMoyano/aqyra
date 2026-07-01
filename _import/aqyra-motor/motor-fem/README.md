# motor-fem — Motor de elementos finitos transversal (FEM-0)

**v0.1.0 · Ola 7 (puentes) · PT 7.0.** Nace el **motor FEM propio** del ecosistema
*Estructurando* como **capacidad transversal** (núcleo `numpy`/`scipy`), el cimiento de
cálculo que consumirán los **puentes** (Ola 7), las **estructuras singulares** (Ola 3) y, en
su horizonte no-lineal, las **tensoestructuras**. No conoce normativa ni tipologías: resuelve
la mecánica y devuelve esfuerzos/desplazamientos/reacciones.

> Todo cálculo es de **predimensionado/asistencia** y debe ser **revisado y firmado por
> técnico competente** (Ingeniero de Caminos, Canales y Puertos). NDP marcados `[confirmar AN]`.

## Escalera de capacidades

Este plugin es el **peldaño FEM-0**: núcleo lineal propio (barra 3D + lámina plana),
ensamblaje disperso, **estático lineal**, apoyos y **resortes**. Los peldaños FEM-1…FEM-5
(cargas móviles/modal, lámina curva/rigidizadores, no-lineal/pandeo, cables/membranas,
dinámica) son de PTs posteriores y están previstos como **ganchos** del contrato C5.

## Estrategia *strangler* sobre PyNite

El núcleo propio nace **reproduciendo a PyNite** (el motor actual: barras + lámina) y se
valida contra él como **oráculo** y contra soluciones analíticas, con **cero regresión** en
los casos de referencia. PyNite es **solo oráculo de test** (vive en otro plugin); el cálculo
del núcleo nuevo es autónomo. Hallazgos clave del arranque:

- La barra de PyNite (`Member3D.k()`) es **Euler-Bernoulli** (sin cortante). Por eso la barra
  de FEM-0 es **EB por defecto** (conmutador Timoshenko desactivado) para casar exactamente.
- El quad de PyNite (`Quad3D`) es **DKMQ** (Katili) con *drilling* a 1/1000 (Bathe), no MITC4
  clásico. `lamina.py` reproduce esa formulación → no-regresión de placa exacta.

## Estructura

```
scripts/
  elementos/barra.py     barra 3D 12 GdL (EB + conmutador Timoshenko, FER, liberaciones)
  elementos/lamina.py    quad DKMQ (membrana+drilling + flexión Mindlin), esfuerzos por unidad de ancho
  fem_core.py            ensamblaje disperso (COO/scipy.sparse) + spsolve + reacciones + equilibrio
  mallador.py            modelo neutro C1 -> malla FEM C5 (+ adaptador espejo desde_pynite)
  resolver.py            API estable C5: resolver(modelo, analisis="estatico_lineal")
  validacion/            analitico.py · oraculo_pynite.py · nafems.py · no_regresion.py
  test_fem_core.py       micro-test
  nucleo/                ESPEJO byte a byte del núcleo transversal (ifc_utils + grafo_red)
```

## API (contrato C5)

```python
from resolver import resolver
res = resolver(modelo, analisis="estatico_lineal", combos=None)
# modelo: dict del modelo de análisis (extiende el modelo neutro C1) o un ModeloFEM.
# -> {"combos": {nombre: {desplazamientos, reacciones, esfuerzos_barra, esfuerzos_lamina, equilibrio}}}
```

`analisis ∈ {"estatico_lineal"}` (FEM-0). `"modal"`, `"pandeo_lineal"`, `"no_lineal"`,
`"movil"` son **ganchos reservados** (lanzan `NotImplementedError`; se implementan en FEM-1+).

## Validación (resumen del *strangler*, PYTHONPATH=/tmp/pylibs)

| Comprobación | Resultado |
|---|---|
| Barra `k` vs PyNite `Member3D._k_unc` | dif ≈ 2e-10 (≈ máquina) |
| Lámina `K` vs PyNite `Quad3D.K` | dif rel ≈ 1e-16 |
| Viga/voladizo/axil/torsión vs analítico (EB) | exacto (≤ 1e-13) |
| Placa cuadrada SS vs Timoshenko | ≈ 1–2.5 % (malla; < 5 %) |
| Patch test de membrana (tensión constante) | 5.6e-16 |
| Oráculo PyNite (pórtico) | despl 2e-17 · reac 3e-11 · esf 4e-11 |
| Oráculo PyNite (placa) | despl y M **exactos (0.0)** · reac 4e-11 |
| **No-regresión caso-01** (barra) vs `resultados.json` | 4e-11 |
| **No-regresión caso-03** (placa real, 2646 GdL) vs `resultados.json` | Rz pilar **0.0** · M rel 1.3e-11 |

Ejecutar: `python3 scripts/test_fem_core.py` · `python3 scripts/validacion/analitico.py` ·
`python3 scripts/validacion/nafems.py` · `python3 scripts/validacion/oraculo_pynite.py` ·
`python3 scripts/validacion/no_regresion.py <Casos-de-uso>`.

## Alcance FEM-0 sobre los casos 1–15

FEM-0 = **FEM lineal genérico** (barra + lámina). Cubre los casos con malla lineal directa
(01 barra; 02/03/04/10 lámina/mixto). Los casos 05–09 y 11–15 son **verticales
especializados** (Winkler, EC4, EC7, EC8, pretensado): su sustrato barra/placa es el ya
validado; su migración al núcleo es de PTs posteriores.

---
*Núcleo transversal del ecosistema Estructurando. Contrato C5 en
`Nucleo-transversal/C5_Contrato-motor-FEM.md`.*
