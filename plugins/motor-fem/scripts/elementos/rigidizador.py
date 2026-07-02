"""
Elemento RIGIDIZADOR = barra EXCENTRICA acoplada a la lamina (FEM-2).

Una barra cuyo eje neutro esta DESPLAZADO (offset) respecto al plano medio de la
lamina a la que rigidiza (diafragmas, almas rigidizadas, conexion losa-alma del
cajon). Se acopla por OFFSET RIGIDO: NO se anaden nudos; la rigidez de la barra,
calculada en su eje, se transforma a los GdL de los nudos de lamina mediante el
*rigid link* u_punto = u_nudo + theta x r (r = vector de offset, perpendicular al
plano medio). Por nudo:  [u_beam; th_beam] = [[I, -skew(r)],[0, I]] [u_nudo; th_nudo].

Capa ADITIVA de FEM-2: subclase de `ElementoBarra` (FEM-0) -> conserva su terna
local, condensacion de liberaciones, FER y masa concentrada (modal) intactas; solo
re-mapea la rigidez y la recuperacion de esfuerzos por la matriz de offset G.
`isinstance(el, ElementoBarra)` sigue siendo True -> el ensamblaje/modal/movil del
nucleo lo tratan como barra sin cambios.

SI (N, m). Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
from __future__ import annotations
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fem_core import ElementoBarra      # noqa: E402  (subclase aditiva)


def _skew(r):
    x, y, z = r
    return np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]], float)


def _G_offset(r_i, r_j):
    """Matriz 12x12 de rigid link para offsets r_i, r_j (nudo i, nudo j)."""
    G = np.eye(12)
    for b, r in ((0, r_i), (6, r_j)):
        G[b:b + 3, b + 3:b + 6] = -_skew(np.asarray(r, float))
    return G


class ElementoRigidizador(ElementoBarra):
    """Barra excentrica acoplada por offset rigido a dos nudos de lamina.

    offset: vector (3,) del nudo de lamina al eje de la barra (igual en i y j para
    un rigidizador recto), normalmente a lo largo de la normal del panel.
    """

    def __init__(self, eid, ni, nj, coord_i, coord_j, mat, sec,
                 offset=(0.0, 0.0, 0.0), releases=None, rotation=0.0):
        super().__init__(eid, ni, nj, coord_i, coord_j, mat, sec,
                         releases=releases, rotation=rotation)
        self.offset = np.asarray(offset, float)
        self.G = _G_offset(self.offset, self.offset)
        # rigidez de la barra (en global, en su eje) re-mapeada a los nudos de lamina
        K_axis = self.T.T @ self.k_cond @ self.T          # 12x12 global en el eje
        self.Kglobal = self.G.T @ K_axis @ self.G         # 12x12 en los nudos de lamina

    def fer_global(self, caso):
        # FER en el eje de la barra -> nudos de lamina por G^T (cargas de barra,
        # normalmente ninguna en un rigidizador; el peso se lleva en la lamina).
        fer_axis = super().fer_global(caso)               # 12x1 global en el eje
        return self.G.T @ fer_axis

    def esfuerzos(self, U, nindex, caso):
        """Esfuerzos de extremo de la barra (en su eje), recuperados desde los
        desplazamientos de los nudos de lamina via el offset rigido."""
        d_nodos = U[self.dofs(nindex)].reshape(12, 1)
        d_eje = self.G @ d_nodos                          # desplaz. en el eje barra
        d_local = self.T @ d_eje
        import barra as _barra
        fer_cond = _barra.condensar_fer(self.fer_local_unc(caso), self._k_unc, self.releases)
        return (self.k_cond @ d_local + fer_cond).flatten()
