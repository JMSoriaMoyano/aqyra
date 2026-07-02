"""
FEM-2: LAMINA CURVA + RIGIDIZADOR + PARED DELGADA (motor-fem).

Capa ADITIVA sobre FEM-0/1: NO modifica `fem_core.py`, `elementos/barra.py`,
`elementos/lamina.py` (DKMQ) ni `fem1.py`. Aporta:
 - `ElementoLaminaCurva`: subclase de `ElementoLamina` que sustituye la DKMQ por
   la lamina curva MITC4 (`elementos/lamina_curva.LaminaCurvaMITC4`), con la MISMA
   interfaz -> el ensamblaje, el modal (masa de lamina) y el movil (objetivo
   `esfuerzo_lamina`) la usan sin cambios. `isinstance(el, ElementoLamina)` True.
 - `ElementoRigidizador`: barra excentrica acoplada por offset rigido (en
   `elementos/rigidizador.py`). `isinstance(el, ElementoBarra)` True.
 - PARED DELGADA: utilidades de post-proceso para la idealizacion de cajon ->
   J de Bredt (torsion de celda cerrada), ancho eficaz por SHEAR LAG y modo de
   distorsion (indicador). El motor sigue siendo AGNOSTICO a la normativa.

Por construccion, las rutas de FEM-0/1 para las instancias base
(`ElementoBarra`/`ElementoLamina` DKMQ) quedan intactas -> no-regresion exacta;
las clases nuevas solo aparecen cuando una idealizacion FEM-2 las crea.

SI (N, m). Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
from __future__ import annotations
import os, sys
import numpy as np
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
sys.path.insert(0, os.path.join(_here, "elementos"))
from fem_core import ElementoLamina, ElementoBarra        # noqa: E402
from lamina_curva import LaminaCurvaMITC4                  # noqa: E402
from rigidizador import ElementoRigidizador               # noqa: E402  (re-export)


class ElementoLaminaCurva(ElementoLamina):
    """Lamina curva MITC4 con la interfaz de `ElementoLamina` (FEM-2)."""

    def __init__(self, eid, nodos, coords, t, E, nu, rho=0.0):
        self.eid = eid
        self.nodos = nodos
        self.quad = LaminaCurvaMITC4(coords[0], coords[1], coords[2], coords[3], t, E, nu)
        self.Kglobal = self.quad.K()
        self.cargas = []
        self.rho = rho


# --------------------------------------------------------------------------- #
#  PARED DELGADA: torsion de Bredt, shear lag (ancho eficaz), distorsion       #
# --------------------------------------------------------------------------- #
def bredt_J(area_celda, tramos):
    """Constante de torsion de Saint-Venant de una CELDA CERRADA (1.a formula de
    Bredt): J = 4 Am^2 / sum(s_i / t_i).

    area_celda: Am, area encerrada por la linea media (m2).
    tramos: lista de (longitud_s, espesor_t) de cada pared de la celda.
    """
    Am = float(area_celda)
    denom = sum(float(s) / float(t) for (s, t) in tramos if t)
    return 4.0 * Am * Am / denom if denom > 0 else 0.0


def shear_lag_beff(b, L, tipo="vano", n_almas=2):
    """Ancho EFICAZ de ala por shear lag (criterio tipo EC2 §5.3.2.1, simplificado).

    b: semiancho fisico del ala desde el alma (m); L: luz (o distancia entre
    puntos de momento nulo, m). Devuelve b_eff/b y b_eff. Para predimensionado:
    l0 = L para vano isostatico; ~0.7 L / 0.15 L en continuos (se pasa L=l0).
        beff_i = min(0.2*bi + 0.1*l0, 0.2*l0, bi)  -> aqui en fraccion.
    """
    l0 = float(L)
    beff = min(0.2 * b + 0.1 * l0, 0.2 * l0, b)
    frac = beff / b if b > 0 else 1.0
    return {"b_eff_m": beff, "b_eff_frac": frac, "l0_m": l0}


def shear_lag_desde_fem(N_ala_borde, N_ala_centro):
    """Ancho eficaz EMPIRICO desde el FEM: razon entre la fuerza de membrana
    longitudinal media y la del borde junto al alma (donde es maxima). beta=
    Nx_medio/Nx_borde aproxima b_eff/b real captado por la malla. Predim."""
    if N_ala_borde == 0:
        return 1.0
    return float(N_ala_centro / N_ala_borde)


def indicador_distorsion(despl_almas):
    """Indicador (0..1) de DISTORSION del cajon: razon entre el cambio relativo de
    forma de la celda (movimiento diferencial de almas) y el desplazamiento medio.
    Solo informativo para predimensionado (avisa de necesidad de diafragmas)."""
    if not despl_almas:
        return 0.0
    medio = np.mean(np.abs(despl_almas))
    if medio == 0:
        return 0.0
    return float((np.max(despl_almas) - np.min(despl_almas)) / (2 * medio))
