"""
Nucleo FEM (FEM-0): ensamblador disperso + solver estatico lineal.

Reune los elementos (barra 3D + lamina cuadrilatera DKMQ) en una matriz de
rigidez global DISPERSA (`scipy.sparse`, tripletes COO), aplica apoyos (incl.
RESORTES) y cargas, resuelve el sistema estatico lineal con
`scipy.sparse.linalg.spsolve`, recupera esfuerzos y REACCIONES y comprueba el
EQUILIBRIO global (sum F ~ 0). Multiples CASOS de carga se resuelven una sola vez
y las COMBINACIONES por SUPERPOSICION (valido en regimen lineal).

Convencion de ejes GLOBALES: X,Y horizontales, Z vertical, gravedad -Z. SI (N, m).
Esfuerzos de barra como esfuerzo INTERNO (convencion PyNite): axial(0)=axial_i,
N_i = -axial_i (compresion negativa). Esfuerzos de lamina por unidad de ancho.

Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
from __future__ import annotations
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "elementos"))
import barra as _barra            # noqa: E402
from lamina import LaminaQuad     # noqa: E402

GDL = 6


# --------------------------------------------------------------------------- #
#  Elementos (envoltorio sobre la libreria de elementos)                      #
# --------------------------------------------------------------------------- #
class ElementoBarra:
    def __init__(self, eid, ni, nj, coord_i, coord_j, mat, sec, releases=None, rotation=0.0):
        self.eid = eid; self.ni = ni; self.nj = nj
        self.ci = coord_i; self.cj = coord_j; self.mat = mat; self.sec = sec
        self.releases = releases or [False] * 12
        self.rotation = rotation
        self.L = float(np.linalg.norm(np.array(coord_j) - np.array(coord_i)))
        self.cargas = []
        self.T = _barra.matriz_T(coord_i, coord_j, rotation)
        k_unc = _barra.k_local_unc(mat["E"], mat["G"], sec["Iy"], sec["Iz"], sec["J"],
                                   sec["A"], self.L, sec.get("Avy"), sec.get("Avz"),
                                   incluir_cortante=sec.get("timoshenko", False))
        self._k_unc = k_unc
        self.k_cond = _barra.condensar_k(k_unc, self.releases)
        self.Kglobal = self.T.T @ self.k_cond @ self.T

    def dofs(self, nindex):
        bi, bj = nindex[self.ni] * GDL, nindex[self.nj] * GDL
        return list(range(bi, bi + GDL)) + list(range(bj, bj + GDL))

    def fer_local_unc(self, caso):
        fer = np.zeros((12, 1)); L = self.L
        for c in self.cargas:
            if c["caso"] != caso:
                continue
            tp = c["tipo"]
            if tp == "uniforme":
                fer += _barra.fer_dist(c["q"], c["q"], 0.0, L, L, c.get("direccion", "Fy"))
            elif tp == "lineal":
                fer += _barra.fer_dist(c["q1"], c["q2"], c.get("x1", 0.0), c.get("x2", L), L,
                                       c.get("direccion", "Fy"))
            elif tp == "global_uniforme":
                R = self.T[:3, :3]
                wv = R @ np.array([c.get("qx", 0.0), c.get("qy", 0.0), c.get("qz", 0.0)])
                fer += _barra.fer_axial_lin(wv[0], wv[0], 0.0, L, L)
                fer += _barra.fer_dist(wv[1], wv[1], 0.0, L, L, "Fy")
                fer += _barra.fer_dist(wv[2], wv[2], 0.0, L, L, "Fz")
            elif tp == "puntual":
                fer += _barra.fer_pt(c["P"], c["x"], L, c.get("direccion", "Fy"))
            elif tp == "axial_puntual":
                fer += _barra.fer_axial_pt(c["P"], c["x"], L)
            elif tp == "termica_axil":
                fer += _barra.fer_termica_axil(self.mat["E"], self.sec["A"], c["alpha"], c["dT"], L)
            elif tp == "termica_gradiente":
                fer += _barra.fer_termica_gradiente(self.mat["E"], self.sec["Iz"], c["alpha"],
                                                    c["dT"], c["h"], L)
        return fer

    def fer_global(self, caso):
        fer_cond = _barra.condensar_fer(self.fer_local_unc(caso), self._k_unc, self.releases)
        return self.T.T @ fer_cond

    def esfuerzos(self, U, nindex, caso):
        d = U[self.dofs(nindex)].reshape(12, 1)
        d_local = self.T @ d
        fer_cond = _barra.condensar_fer(self.fer_local_unc(caso), self._k_unc, self.releases)
        return (self.k_cond @ d_local + fer_cond).flatten()


class ElementoLamina:
    def __init__(self, eid, nodos, coords, t, E, nu):
        self.eid = eid; self.nodos = nodos
        self.quad = LaminaQuad(coords[0], coords[1], coords[2], coords[3], t, E, nu)
        self.Kglobal = self.quad.K()
        self.cargas = []

    def dofs(self, nindex):
        out = []
        for n in self.nodos:
            b = nindex[n] * GDL
            out += list(range(b, b + GDL))
        return out

    def fer_global(self, caso):
        fer = np.zeros((24, 1))
        for c in self.cargas:
            if c["caso"] == caso:
                fer = fer + self.quad.fer_presion(c["p"])
        return fer

    def esfuerzos(self, U, nindex, caso=None):
        d = U[self.dofs(nindex)]
        M = self.quad.moment(d); Q = self.quad.shear(d); S = self.quad.membrane(d)
        t = self.quad.t
        cen = np.mean([self.quad.Xi, self.quad.Xj, self.quad.Xm, self.quad.Xn], axis=0)
        return {"x": float(cen[0]), "y": float(cen[1]), "z": float(cen[2]),
                "Mx": float(M[0]), "My": float(M[1]), "Mxy": float(M[2]),
                "Qx": float(Q[0]), "Qy": float(Q[1]),
                "Nx": float(S[0] * t), "Ny": float(S[1] * t), "Nxy": float(S[2] * t)}


# --------------------------------------------------------------------------- #
#  Modelo FEM (ensamblaje + solucion)                                         #
# --------------------------------------------------------------------------- #
class ModeloFEM:
    def __init__(self):
        self.nodos = {}; self.norden = []; self.elementos = []
        self.apoyos = {}; self.resortes = {}; self.cargas_nodales = []

    def add_nodo(self, name, x, y, z):
        if name not in self.nodos:
            self.nodos[name] = (x, y, z); self.norden.append(name)

    def add_elemento(self, el): self.elementos.append(el)
    def set_apoyo(self, name, vec): self.apoyos[name] = list(vec)
    def add_resorte(self, name, vec): self.resortes[name] = list(vec)

    def add_carga_nodal(self, caso, nodo, F):
        self.cargas_nodales.append({"caso": caso, "nodo": nodo, "F": list(F)})

    def _nindex(self): return {n: i for i, n in enumerate(self.norden)}

    def _casos(self):
        cs = set()
        for el in self.elementos:
            for c in getattr(el, "cargas", []):
                cs.add(c["caso"])
        for c in self.cargas_nodales:
            cs.add(c["caso"])
        return sorted(cs)

    def resolver(self, combos=None):
        """Resuelve por casos y combina. `combos` = {nombre:{caso:factor}}.

        Devuelve dict con desplazamientos, reacciones, esfuerzos y equilibrio
        por combinacion (o por caso si combos es None)."""
        nindex = self._nindex(); ndof = len(self.norden) * GDL; casos = self._casos()
        if combos is None:
            combos = {c: {c: 1.0} for c in casos}

        # --- ensamblaje disperso por tripletes (COO), vectorizado por elemento ---
        rows = []; cols = []; data = []
        for el in self.elementos:
            dofs = np.asarray(el.dofs(nindex)); Kg = np.asarray(el.Kglobal); n = len(dofs)
            rows.append(np.repeat(dofs, n)); cols.append(np.tile(dofs, n)); data.append(Kg.flatten())
        for name, kv in self.resortes.items():
            base = nindex[name] * GDL
            for i in range(6):
                if kv[i]:
                    rows.append(np.array([base + i])); cols.append(np.array([base + i]))
                    data.append(np.array([float(kv[i])]))
        K = coo_matrix((np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
                       shape=(ndof, ndof)).tocsr()

        # --- dofs fijos ---
        fixed = []
        for name, vec in self.apoyos.items():
            base = nindex[name] * GDL
            for i in range(6):
                if vec[i]:
                    fixed.append(base + i)
        fixed = set(sorted(set(fixed)))
        free = np.array([d for d in range(ndof) if d not in fixed])

        # --- vector de carga por caso ---
        Fc = {c: np.zeros(ndof) for c in casos}
        for el in self.elementos:
            dofs = el.dofs(nindex)
            for c in casos:
                fg = el.fer_global(c).flatten()
                for a, ia in enumerate(dofs):
                    Fc[c][ia] -= fg[a]
        for cn in self.cargas_nodales:
            base = nindex[cn["nodo"]] * GDL
            for i in range(6):
                Fc[cn["caso"]][base + i] += cn["F"][i]

        # --- resolver por caso ---
        Kff = K[np.ix_(free, free)]
        Uc = {}
        for c in casos:
            U = np.zeros(ndof); U[free] = spsolve(Kff, Fc[c][free]); Uc[c] = U

        # --- recuperacion por combinacion (superposicion) ---
        res = {"combos": {}, "nodos": list(self.norden)}
        for cname, factors in combos.items():
            U = np.zeros(ndof); F = np.zeros(ndof)
            for c, f in factors.items():
                if c in Uc:
                    U += f * Uc[c]; F += f * Fc[c]
            disp = {}
            for n in self.norden:
                b = nindex[n] * GDL; disp[n] = U[b:b + GDL].tolist()
            R = K.dot(U) - F
            reac = {}
            for name, vec in self.apoyos.items():
                base = nindex[name] * GDL
                reac[name] = [R[base + i] if vec[i] else 0.0 for i in range(6)]
            esf_b, esf_l = {}, {}
            for el in self.elementos:
                if isinstance(el, ElementoBarra):
                    acc = np.zeros(12)
                    for c, f in factors.items():
                        if c in Uc:
                            acc += f * el.esfuerzos(Uc[c], nindex, c)
                    # esfuerzo interno (convencion PyNite): extremo i = f[0:6];
                    # extremo j = -f[6:12]. axial(0)=axial_i; N_i = -axial_i (compresion neg.).
                    esf_b[el.eid] = {
                        "axial_i": acc[0], "Vy_i": acc[1], "Vz_i": acc[2],
                        "T_i": acc[3], "My_i": acc[4], "Mz_i": acc[5],
                        "axial_j": -acc[6], "Vy_j": -acc[7], "Vz_j": -acc[8],
                        "T_j": -acc[9], "My_j": -acc[10], "Mz_j": -acc[11],
                        "N_i": -acc[0], "N_j": acc[6]}
                else:
                    acc = None
                    for c, f in factors.items():
                        if c in Uc:
                            e = el.esfuerzos(Uc[c], nindex)
                            if acc is None:
                                acc = dict(e)
                                for k in e:
                                    if k not in ("x", "y", "z"):
                                        acc[k] = f * e[k]
                            else:
                                for k in e:
                                    if k not in ("x", "y", "z"):
                                        acc[k] += f * e[k]
                    esf_l[el.eid] = acc
            eq = self._equilibrio(F, R, nindex)
            res["combos"][cname] = {"desplazamientos": disp, "reacciones": reac,
                                    "esfuerzos_barra": esf_b, "esfuerzos_lamina": esf_l,
                                    "equilibrio": eq}
        return res

    def _equilibrio(self, F, R, nindex):
        appF = np.array([F[nindex[n] * GDL:nindex[n] * GDL + 3] for n in self.norden]).sum(axis=0)
        sumR = np.zeros(3)
        for name, vec in self.apoyos.items():
            base = nindex[name] * GDL; sumR += np.array([R[base + i] for i in range(3)])
        total = appF + sumR
        return {"sumF_aplicada_N": appF.tolist(), "sumF_reaccion_N": sumR.tolist(),
                "residuo_N": total.tolist(), "norma_residuo_N": float(np.linalg.norm(total))}
