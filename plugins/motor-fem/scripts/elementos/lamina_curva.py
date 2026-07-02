"""
Elemento LAMINA CURVA isoparametrica de 4 nudos (6 GdL/nudo, 24 GdL) -- FEM-2.

Cuadrilatero de Reissner-Mindlin con cortante transversal asumido **MITC4**
(Dvorkin-Bathe 1984): libre de bloqueo por cortante, valido para lamina delgada
y gruesa y mallas distorsionadas, y -- por su terna LOCAL por elemento -- capaz
de mallar superficies CURVAS/ALABEADAS como faceta de lamina (Scordelis-Lo,
cilindro pinzado, semiesfera; almas/losas del cajon como placas plegadas).

Capa ADITIVA de FEM-2: NO toca la DKMQ de FEM-0 (`lamina.py`) ni `fem_core`. La
clase expone la MISMA interfaz publica que `LaminaQuad` (`T()`, `K()`,
`fer_presion(p)`, `moment/shear/membrane(d_glob)`, atributos `Xi..Xn`, `t`), de
modo que un envoltorio `ElementoLaminaCurva` (subclase de `ElementoLamina`) la
use sin cambiar el ensamblaje, el modal ni el movil.

Formulacion (en la terna LOCAL del elemento):
 - MEMBRANA: Q4 tension plana (u,v) + GdL de DRILLING (rigidez ficticia, Bathe).
 - FLEXION: Mindlin, curvaturas kx=d(thy)/dx, ky=-d(thx)/dy, kxy=d(thy)/dy-d(thx)/dx.
 - CORTANTE: MITC4 -- deformaciones covariantes atadas en puntos medios de lado:
     gam_xi = dw/dxi + x_xi*thy - y_xi*thx   (atado en A(0,-1), C(0,1))
     gam_eta= dw/deta + x_eta*thy - y_eta*thx (atado en D(-1,0), B(1,0))
   recuperando el cartesiano por [gxz;gyz]=J^-1[gam_xi;gam_eta].
GdL local por nudo: [u, v, w, thx, thy, thz]. Esfuerzos por unidad de ancho en
ejes LOCALES, en el centro (xi=eta=0):
   membrana [Nx,Ny,Nxy]=t*[Sx,Sy,Txy] ; flexion [Mx,My,Mxy] ; cortante [Qx,Qy].

SI (N, m). Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
from __future__ import annotations
import numpy as np
from numpy.linalg import inv, det, norm

_GP = 1.0 / 3 ** 0.5                       # Gauss 2x2
_NAT = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)]   # nudos i,j,m,n
_KAPPA = 5.0 / 6.0                          # factor de cortante de placa


class LaminaCurvaMITC4:
    """Lamina curva MITC4. Orden de nudos i, j, m, n (antihorario)."""

    def __init__(self, xi_n, xj_n, xm_n, xn_n, t, E, nu, kx_mod=1.0, ky_mod=1.0):
        self.Xi = np.asarray(xi_n, float); self.Xj = np.asarray(xj_n, float)
        self.Xm = np.asarray(xm_n, float); self.Xn = np.asarray(xn_n, float)
        self.t = float(t); self.E = float(E); self.nu = float(nu)
        self.kx_mod = float(kx_mod); self.ky_mod = float(ky_mod)
        self._frame()

    # --- terna local del elemento (faceta) y coords locales 2D ------------- #
    def _frame(self):
        X1, X2, X3, X4 = self.Xi, self.Xj, self.Xm, self.Xn
        # ejes a partir de las diagonales (robusto para quad alabeado)
        d1 = X3 - X1; d2 = X4 - X2
        nrm = np.cross(d1, d2); nrm = nrm / norm(nrm)
        ex = (X2 + X3 - X1 - X4)            # direccion media lado i->j / n->m
        ex = ex - np.dot(ex, nrm) * nrm; ex = ex / norm(ex)
        ey = np.cross(nrm, ex)
        self.ex, self.ey, self.ez = ex, ey, nrm
        self.R = np.vstack([ex, ey, nrm])  # filas = ejes locales en globales
        c = 0.25 * (X1 + X2 + X3 + X4)
        self.xy = np.array([[np.dot(P - c, ex), np.dot(P - c, ey)]
                            for P in (X1, X2, X3, X4)])   # 4x2 coords locales

    # --- funciones de forma y jacobiano ------------------------------------ #
    def _N(self, xi, eta):
        return np.array([0.25 * (1 + s * xi) * (1 + r * eta) for (s, r) in _NAT])

    def _dN(self, xi, eta):
        dxi = np.array([0.25 * s * (1 + r * eta) for (s, r) in _NAT])
        det_ = np.array([0.25 * r * (1 + s * xi) for (s, r) in _NAT])
        return dxi, det_                                   # d/dxi, d/deta (4,)

    def _jac(self, xi, eta):
        dxi, det_ = self._dN(xi, eta)
        J = np.array([[dxi @ self.xy[:, 0], dxi @ self.xy[:, 1]],
                      [det_ @ self.xy[:, 0], det_ @ self.xy[:, 1]]])
        return J, dxi, det_

    # --- B de membrana (3x8 en u,v) ---------------------------------------- #
    def _Bm(self, xi, eta):
        J, dxi, det_ = self._jac(xi, eta)
        Ji = inv(J)
        dNx = Ji[0, 0] * dxi + Ji[0, 1] * det_
        dNy = Ji[1, 0] * dxi + Ji[1, 1] * det_
        B = np.zeros((3, 8))
        for i in range(4):
            B[0, 2 * i] = dNx[i]; B[1, 2 * i + 1] = dNy[i]
            B[2, 2 * i] = dNy[i]; B[2, 2 * i + 1] = dNx[i]
        return B, det(J), dNx, dNy

    def _Cm(self):
        E, nu = self.E, self.nu
        Ex, Ey = E * self.kx_mod, E * self.ky_mod; G = E / (2 * (1 + nu))
        return 1.0 / (1 - nu * nu) * np.array([[Ex, nu * Ex, 0],
                                               [nu * Ey, Ey, 0],
                                               [0, 0, (1 - nu * nu) * G]])

    # --- B de flexion (3x12 en w,thx,thy) ---------------------------------- #
    def _Bb(self, xi, eta):
        J, dxi, det_ = self._jac(xi, eta)
        Ji = inv(J)
        dNx = Ji[0, 0] * dxi + Ji[0, 1] * det_
        dNy = Ji[1, 0] * dxi + Ji[1, 1] * det_
        B = np.zeros((3, 12))
        for i in range(4):
            # dofs locales por nudo en el subvector de placa: [w, thx, thy]
            thx = 3 * i + 1; thy = 3 * i + 2
            B[0, thy] = dNx[i]            # kx = d(thy)/dx
            B[1, thx] = -dNy[i]           # ky = -d(thx)/dy
            B[2, thy] = dNy[i]; B[2, thx] = -dNx[i]   # kxy
        return B
        
    def _Db(self):
        E, nu, h = self.E, self.nu, self.t
        return E * h ** 3 / (12 * (1 - nu * nu)) * np.array(
            [[1, nu, 0], [nu, 1, 0], [0, 0, (1 - nu) / 2]])

    # --- B de cortante MITC4 (2x12 en w,thx,thy) --------------------------- #
    def _gamma_nat(self, xi, eta, comp):
        """Vector fila (12,) de la deformacion natural covariante gam_xi (comp=0)
        o gam_eta (comp=1) en (xi,eta), en terminos de [w,thx,thy] por nudo."""
        N = self._N(xi, eta); dxi, det_ = self._dN(xi, eta)
        J, _, _ = self._jac(xi, eta)
        # x_xi,y_xi (fila 0 de J) ; x_eta,y_eta (fila 1)
        xg, yg = (J[0, 0], J[0, 1]) if comp == 0 else (J[1, 0], J[1, 1])
        dN = dxi if comp == 0 else det_
        row = np.zeros(12)
        for i in range(4):
            w = 3 * i; thx = 3 * i + 1; thy = 3 * i + 2
            row[w] = dN[i]                 # dw/dnat
            row[thy] += xg * N[i]          # + x_nat*thy
            row[thx] += -yg * N[i]         # - y_nat*thx
        return row

    def _Bs(self, xi, eta):
        # puntos de atado: A(0,-1) C(0,1) para gam_xi ; D(-1,0) B(1,0) para gam_eta
        gA = self._gamma_nat(0.0, -1.0, 0); gC = self._gamma_nat(0.0, 1.0, 0)
        gD = self._gamma_nat(-1.0, 0.0, 1); gB = self._gamma_nat(1.0, 0.0, 1)
        gxi = 0.5 * (1 - eta) * gA + 0.5 * (1 + eta) * gC
        geta = 0.5 * (1 - xi) * gD + 0.5 * (1 + xi) * gB
        J, _, _ = self._jac(xi, eta)
        Ji = inv(J)
        # [gxz;gyz] = J^-1 [gam_xi; gam_eta]
        Bs = Ji @ np.vstack([gxi, geta])
        return Bs

    def _Ds(self):
        return _KAPPA * self.E / (2 * (1 + self.nu)) * self.t * np.eye(2)

    # --- rigidez local 24x24 (en GdL [u,v,w,thx,thy,thz] por nudo) ---------- #
    def k_local(self):
        K = np.zeros((24, 24))
        Cm = self._Cm(); Db = self._Db(); Ds = self._Ds(); t = self.t
        # indices locales
        idx_m = [(6 * i + 0, 6 * i + 1) for i in range(4)]      # u,v
        idx_p = [(6 * i + 2, 6 * i + 3, 6 * i + 4) for i in range(4)]  # w,thx,thy
        flat_m = [d for pair in idx_m for d in pair]            # 8
        flat_p = [d for tri in idx_p for d in tri]              # 12
        gps = [(-_GP, -_GP), (_GP, -_GP), (_GP, _GP), (-_GP, _GP)]
        Km = np.zeros((8, 8)); Kb = np.zeros((12, 12)); Ks = np.zeros((12, 12))
        for (xi, eta) in gps:
            Bm, dJ, _, _ = self._Bm(xi, eta)
            Km += (Bm.T @ Cm @ Bm) * t * dJ
            Bb = self._Bb(xi, eta)
            Kb += (Bb.T @ Db @ Bb) * dJ
            Bs = self._Bs(xi, eta)
            J, _, _ = self._jac(xi, eta)
            Ks += (Bs.T @ Ds @ Bs) * det(J)
        Kp = Kb + Ks
        for a in range(8):
            for b in range(8):
                K[flat_m[a], flat_m[b]] += Km[a, b]
        for a in range(12):
            for b in range(12):
                K[flat_p[a], flat_p[b]] += Kp[a, b]
        # drilling (thz local): rigidez ficticia ~ 1/1000 del menor termino
        # ROTACIONAL de FLEXION (regla de Bathe, idem DKMQ). Usar la membrana
        # aqui sobre-rigidiza las laminas delgadas doblemente curvas (bloqueo) ->
        # se toman las diagonales de thx,thy (posiciones 3i+1,3i+2 del subv. placa).
        rot = [Kp[3 * i + r, 3 * i + r] for i in range(4) for r in (1, 2)]
        kdr = min(d for d in rot if d > 0) / 1000.0
        for i in range(4):
            K[6 * i + 5, 6 * i + 5] += kdr
        return K

    # --- transformacion a global (24x24) ----------------------------------- #
    def T(self):
        T = np.zeros((24, 24))
        for b in range(8):
            T[3 * b:3 * b + 3, 3 * b:3 * b + 3] = self.R
        return T

    def K(self):
        T = self.T()
        return T.T @ self.k_local() @ T

    # --- carga por presion uniforme p (en +z local) ------------------------ #
    def fer_presion(self, p):
        gps = [(-_GP, -_GP), (_GP, -_GP), (_GP, _GP), (-_GP, _GP)]
        f = np.zeros(24)
        for (xi, eta) in gps:
            N = self._N(xi, eta); J, _, _ = self._jac(xi, eta)
            dJ = det(J)
            for i in range(4):
                f[6 * i + 2] += N[i] * p * dJ        # w local
        # FER = -f convencion? presion p hacia +z aporta carga; usamos signo + y
        # el solver resta fer_global. Mantener coherencia con DKMQ (pp = -p):
        return (self.T().T @ (-f)).reshape(24, 1)

    # --- recuperacion de esfuerzos (centro xi=eta=0) ----------------------- #
    def _d_local(self, d_glob):
        return (self.T() @ np.asarray(d_glob, float).reshape(24, 1)).flatten()

    def _split(self, dl):
        m = np.array([dl[6 * i + j] for i in range(4) for j in (0, 1)])   # u,v
        p = np.array([dl[6 * i + j] for i in range(4) for j in (2, 3, 4)])  # w,thx,thy
        return m, p

    def moment(self, d_glob, xi=0.0, eta=0.0):
        dl = self._d_local(d_glob); _, p = self._split(dl)
        return self._Db() @ (self._Bb(xi, eta) @ p)

    def shear(self, d_glob, xi=0.0, eta=0.0):
        dl = self._d_local(d_glob); _, p = self._split(dl)
        Ds = _KAPPA * self.E / (2 * (1 + self.nu)) * self.t * np.eye(2)
        return Ds @ (self._Bs(xi, eta) @ p)

    def membrane(self, d_glob, xi=0.0, eta=0.0):
        dl = self._d_local(d_glob); m, _ = self._split(dl)
        Bm, _, _, _ = self._Bm(xi, eta)
        return self._Cm() @ (Bm @ m)
