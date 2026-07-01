"""
Elemento LAMINA cuadrilatera de 4 nudos (6 GdL/nudo, 24 GdL) para FEM-0.

Reproduce el quad del oraculo PyNite (`Pynite.Quad3D`): flexion+cortante por la
formulacion DKMQ (Katili) -- valida para placa delgada y gruesa y mallas
distorsionadas -- combinada con membrana de tension plana y un GdL de DRILLING
(rigidez ficticia 1/1000 del menor termino rotacional, regla de Bathe). Esto
garantiza la NO-REGRESION frente a la placa actual (certificada vs Timoshenko).

Esfuerzos por unidad de ancho, en ejes LOCALES de la lamina:
   membrana [Nx, Ny, Nxy] = [Sx, Sy, Txy] * t     (fuerzas/long.)
   flexion  [Mx, My, Mxy]                          (momentos/long.)
   cortante [Qx, Qy]
El triangulo se trata como quad degenerado (n_node == m_node) -- respaldo.

SI (N, m). Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
from __future__ import annotations
import numpy as np
from numpy.linalg import inv, det, norm

GP = 1.0 / 3 ** 0.5  # punto de Gauss 2x2


class LaminaQuad:
    """Quad DKMQ + membrana + drilling. Orden de nudos i, j, m, n (antihorario)."""

    def __init__(self, xi_n, xj_n, xm_n, xn_n, t, E, nu, kx_mod=1.0, ky_mod=1.0):
        self.Xi = np.asarray(xi_n, float)
        self.Xj = np.asarray(xj_n, float)
        self.Xm = np.asarray(xm_n, float)
        self.Xn = np.asarray(xn_n, float)
        self.t = float(t)
        self.E = float(E)
        self.nu = float(nu)
        self.kx_mod = kx_mod
        self.ky_mod = ky_mod
        self._local_coords()

    # --- coordenadas locales (idem Quad3D._local_coords) ------------------- #
    def _local_coords(self):
        X1, X2, X3, X4 = self.Xi, self.Xj, self.Xm, self.Xn
        v12 = X2 - X1; v13 = X3 - X1; v14 = X4 - X1
        x_axis = v12
        z_axis = np.cross(x_axis, v13)
        y_axis = np.cross(z_axis, x_axis)
        x_axis = x_axis / norm(x_axis)
        y_axis = y_axis / norm(y_axis)
        self.x1, self.y1 = 0.0, 0.0
        self.x2 = float(np.dot(v12, x_axis)); self.y2 = float(np.dot(v12, y_axis))
        self.x3 = float(np.dot(v13, x_axis)); self.y3 = float(np.dot(v13, y_axis))
        self.x4 = float(np.dot(v14, x_axis)); self.y4 = float(np.dot(v14, y_axis))

    # --- geometria DKMQ ---------------------------------------------------- #
    def L_k(self, k):
        c = {5: (self.x2 - self.x1, self.y2 - self.y1),
             6: (self.x3 - self.x2, self.y3 - self.y2),
             7: (self.x4 - self.x3, self.y4 - self.y3),
             8: (self.x1 - self.x4, self.y1 - self.y4)}[k]
        return (c[0] ** 2 + c[1] ** 2) ** 0.5

    def dir_cos(self, k):
        L = self.L_k(k)
        c = {5: (self.x2 - self.x1, self.y2 - self.y1),
             6: (self.x3 - self.x2, self.y3 - self.y2),
             7: (self.x4 - self.x3, self.y4 - self.y3),
             8: (self.x1 - self.x4, self.y1 - self.y4)}[k]
        return c[0] / L, c[1] / L

    def phi_k(self, k):
        kappa = 5 / 6
        return 2 / (kappa * (1 - self.nu)) * (self.t / self.L_k(k)) ** 2

    def J(self, xi, eta):
        x1, y1, x2, y2 = self.x1, self.y1, self.x2, self.y2
        x3, y3, x4, y4 = self.x3, self.y3, self.x4, self.y4
        return 1 / 4 * np.array([
            [x1*(eta-1) - x2*(eta-1) + x3*(eta+1) - x4*(eta+1),
             y1*(eta-1) - y2*(eta-1) + y3*(eta+1) - y4*(eta+1)],
            [x1*(xi-1) - x2*(xi+1) + x3*(xi+1) - x4*(xi-1),
             y1*(xi-1) - y2*(xi+1) + y3*(xi+1) - y4*(xi-1)]])

    def N_gamma(self, xi, eta):
        return np.array([[1/2*(1-eta), 0, 1/2*(1+eta), 0],
                         [0, 1/2*(1+xi), 0, 1/2*(1-xi)]])

    def A_gamma(self):
        L5, L6, L7, L8 = (self.L_k(k) for k in (5, 6, 7, 8))
        return np.array([[L5/2, 0, 0, 0], [0, L6/2, 0, 0],
                         [0, 0, -L7/2, 0], [0, 0, 0, -L8/2]])

    def A_u(self):
        L5, L6, L7, L8 = (self.L_k(k) for k in (5, 6, 7, 8))
        C5, S5 = self.dir_cos(5); C6, S6 = self.dir_cos(6)
        C7, S7 = self.dir_cos(7); C8, S8 = self.dir_cos(8)
        return 1/2*np.array([
            [-2/L5, C5, S5,  2/L5, C5, S5,   0,   0,  0,   0,   0,  0],
            [  0,   0,  0, -2/L6, C6, S6,  2/L6, C6, S6,   0,   0,  0],
            [  0,   0,  0,   0,   0,  0, -2/L7, C7, S7,  2/L7, C7, S7],
            [ 2/L8, C8, S8,   0,   0,  0,   0,   0,  0, -2/L8, C8, S8]])

    def A_Delta_inv(self):
        p = [self.phi_k(k) for k in (5, 6, 7, 8)]
        return -3/2*np.diag([1/(1+p[0]), 1/(1+p[1]), 1/(1+p[2]), 1/(1+p[3])])

    def A_phi_Delta(self):
        p = [self.phi_k(k) for k in (5, 6, 7, 8)]
        return np.diag([p[0]/(1+p[0]), p[1]/(1+p[1]), p[2]/(1+p[2]), p[3]/(1+p[3])])

    def B_b_beta(self, xi, eta):
        Ji = inv(self.J(xi, eta)); j11, j12, j21, j22 = Ji[0,0], Ji[0,1], Ji[1,0], Ji[1,1]
        N1x, N1e = 0.25*(eta-1), 0.25*(xi-1)
        N2x, N2e = -0.25*(eta-1), -0.25*(xi+1)
        N3x, N3e = 0.25*(eta+1), 0.25*(xi+1)
        N4x, N4e = -0.25*(eta+1), -0.25*(xi-1)
        def gx(a, b): return j11*a + j12*b
        def gy(a, b): return j21*a + j22*b
        N1X, N1Y = gx(N1x, N1e), gy(N1x, N1e)
        N2X, N2Y = gx(N2x, N2e), gy(N2x, N2e)
        N3X, N3Y = gx(N3x, N3e), gy(N3x, N3e)
        N4X, N4Y = gx(N4x, N4e), gy(N4x, N4e)
        return np.array([[0, N1X, 0, 0, N2X, 0, 0, N3X, 0, 0, N4X, 0],
                         [0, 0, N1Y, 0, 0, N2Y, 0, 0, N3Y, 0, 0, N4Y],
                         [0, N1Y, N1X, 0, N2Y, N2X, 0, N3Y, N3X, 0, N4Y, N4X]])

    def B_b_Delta_beta(self, xi, eta):
        Ji = inv(self.J(xi, eta)); j11, j12, j21, j22 = Ji[0,0], Ji[0,1], Ji[1,0], Ji[1,1]
        P5x, P5e = xi*(eta-1), 0.5*(xi-1)*(xi+1)
        P6x, P6e = -0.5*(eta-1)*(eta+1), -eta*(xi+1)
        P7x, P7e = -xi*(eta+1), -0.5*(xi-1)*(xi+1)
        P8x, P8e = 0.5*(eta-1)*(eta+1), eta*(xi-1)
        def gx(a, b): return j11*a + j12*b
        def gy(a, b): return j21*a + j22*b
        P5X, P5Y = gx(P5x, P5e), gy(P5x, P5e)
        P6X, P6Y = gx(P6x, P6e), gy(P6x, P6e)
        P7X, P7Y = gx(P7x, P7e), gy(P7x, P7e)
        P8X, P8Y = gx(P8x, P8e), gy(P8x, P8e)
        C5, S5 = self.dir_cos(5); C6, S6 = self.dir_cos(6)
        C7, S7 = self.dir_cos(7); C8, S8 = self.dir_cos(8)
        return np.array([
            [P5X*C5, P6X*C6, P7X*C7, P8X*C8],
            [P5Y*S5, P6Y*S6, P7Y*S7, P8Y*S8],
            [P5Y*C5+P5X*S5, P6Y*C6+P6X*S6, P7Y*C7+P7X*S7, P8Y*C8+P8X*S8]])

    def B_b(self, xi, eta):
        return self.B_b_beta(xi, eta) + self.B_b_Delta_beta(xi, eta) @ self.A_Delta_inv() @ self.A_u()

    def B_s(self, xi, eta):
        return inv(self.J(xi, eta)) @ self.N_gamma(xi, eta) @ self.A_gamma() @ self.A_phi_Delta() @ self.A_u()

    def B_m(self, xi, eta):
        dH = inv(self.J(xi, eta)) @ (1/4*np.array([[eta-1, -eta+1, eta+1, -eta-1],
                                                   [xi-1, -xi-1, xi+1, -xi+1]]))
        return np.array([
            [dH[0,0], 0, dH[0,1], 0, dH[0,2], 0, dH[0,3], 0],
            [0, dH[1,0], 0, dH[1,1], 0, dH[1,2], 0, dH[1,3]],
            [dH[1,0], dH[0,0], dH[1,1], dH[0,1], dH[1,2], dH[0,2], dH[1,3], dH[0,3]]])

    def Hb(self):
        nu, E, h = self.nu, self.E, self.t
        return E*h**3/(12*(1-nu**2))*np.array([[1, nu, 0], [nu, 1, 0], [0, 0, (1-nu)/2]])

    def Hs(self):
        k, E, h, nu = 5/6, self.E, self.t, self.nu
        return E*h*k/(2*(1+nu))*np.eye(2)

    def Cm(self):
        Ex, Ey = self.E*self.kx_mod, self.E*self.ky_mod
        nu = self.nu; G = self.E/(2*(1+self.nu))
        return 1/(1-nu*nu)*np.array([[Ex, nu*Ex, 0], [nu*Ey, Ey, 0], [0, 0, (1-nu*nu)*G]])

    # --- rigidez local ----------------------------------------------------- #
    def k_b(self):
        Hb, Hs = self.Hb(), self.Hs()
        dJ = [det(self.J(a, b)) for a, b in [(-GP,-GP), (GP,-GP), (GP,GP), (-GP,GP)]]
        Bb = [self.B_b(a, b) for a, b in [(-GP,-GP), (GP,-GP), (GP,GP), (-GP,GP)]]
        k = sum((Bb[i].T @ Hb @ Bb[i])*dJ[i] for i in range(4))
        Bs = [self.B_s(a, b) for a, b in [(-GP,-GP), (GP,-GP), (GP,GP), (-GP,GP)]]
        k = k + sum((Bs[i].T @ Hs @ Bs[i])*dJ[i] for i in range(4))
        k_rz = min(abs(k[1,1]), abs(k[2,2]), abs(k[4,4]), abs(k[5,5]),
                   abs(k[7,7]), abs(k[8,8]), abs(k[10,10]), abs(k[11,11]))/1000
        k_exp = np.zeros((24, 24))
        for i in range(12):
            m = 2*i+2 if i in (0,3,6,9) else (2*i+1 if i in (1,4,7,10) else 2*i)
            for j in range(12):
                n = 2*j+2 if j in (0,3,6,9) else (2*j+1 if j in (1,4,7,10) else 2*j)
                k_exp[round(m), round(n)] = k[i, j]
        for d in (5, 11, 17, 23):
            k_exp[d, d] = k_rz
        # invertir signo de flexion +y (idem PyNite)
        k_exp[[4,10,16,22], :] *= -1; k_exp[:, [4,10,16,22]] *= -1
        # intercambiar x<->y (idem PyNite)
        sw = [4,3,10,9,16,15,22,21]; orig = [3,4,9,10,15,16,21,22]
        k_exp[orig, :] = k_exp[sw, :]; k_exp[:, orig] = k_exp[:, sw]
        return k_exp

    def k_m(self):
        t, Cm = self.t, self.Cm()
        dJ = [det(self.J(a, b)) for a, b in [(-GP,-GP), (GP,-GP), (GP,GP), (-GP,GP)]]
        Bm = [self.B_m(a, b) for a, b in [(-GP,-GP), (GP,-GP), (GP,GP), (-GP,GP)]]
        k = t*sum((Bm[i].T @ Cm @ Bm[i])*dJ[i] for i in range(4))
        k_exp = np.zeros((24, 24))
        for i in range(8):
            m = i*3 if i in (0,2,4,6) else i*3-2
            for j in range(8):
                n = j*3 if j in (0,2,4,6) else j*3-2
                k_exp[round(m), round(n)] = k[i, j]
        return k_exp

    def k_local(self):
        return self.k_b() + self.k_m()

    # --- transformacion global (idem Quad3D.T) ----------------------------- #
    def T(self):
        x = self.Xj - self.Xi; x = x / norm(x)
        xy = self.Xn - self.Xi
        z = np.cross(x, xy); z = z / norm(z)
        y = np.cross(z, x); y = y / norm(y)
        R = np.array([x, y, z])
        T = np.zeros((24, 24))
        for b in range(8):
            T[3*b:3*b+3, 3*b:3*b+3] = R
        return T

    def K(self):
        T = self.T()
        return T.T @ self.k_local() @ T

    def fer_presion(self, p):
        """Vector global de carga por presion uniforme p (en +z local)."""
        def Hw(xi, eta):
            return 1/4*np.array([[(1-xi)*(1-eta), 0, 0, (1+xi)*(1-eta), 0, 0,
                                  (1+xi)*(1+eta), 0, 0, (1-xi)*(1+eta), 0, 0]])
        pp = -p
        fer = sum(Hw(a, b).T*pp*det(self.J(a, b))
                  for a, b in [(-GP,-GP), (GP,-GP), (GP,GP), (-GP,GP)])
        fer_exp = np.zeros((24, 1))
        for i in range(12):
            m = 2*i+2 if i in (0,3,6,9) else (2*i+1 if i in (1,4,7,10) else 2*i)
            fer_exp[round(m), 0] = fer[i, 0]
        return self.T().T @ fer_exp

    # --- recuperacion de esfuerzos (en el centro xi=eta=0) ----------------- #
    def _d_local(self, d_glob):
        return self.T() @ np.asarray(d_glob, float).reshape(24, 1)

    def moment(self, d_glob, xi=0.0, eta=0.0):
        d = self._d_local(d_glob)
        d[[3, 9, 15, 21], :] *= -1
        d = d[[2,4,3,8,10,9,14,16,15,20,22,21], :]
        xe, ye = xi/GP, eta/GP
        H = 1/4*np.array([(1-xe)*(1-ye), (1+xe)*(1-ye), (1+xe)*(1+ye), (1-xe)*(1+ye)])
        Hb = self.Hb()
        m = [Hb @ (self.B_b(a, b) @ d) for a, b in [(-GP,-GP), (GP,-GP), (GP,GP), (-GP,GP)]]
        Mx = sum(H[i]*m[i][0, 0] for i in range(4))
        My = sum(H[i]*m[i][1, 0] for i in range(4))
        Mxy = sum(H[i]*m[i][2, 0] for i in range(4))
        return np.array([Mx, My, Mxy])

    def shear(self, d_glob, xi=0.0, eta=0.0):
        d = self._d_local(d_glob)
        d[[3, 9, 15, 21], :] *= -1
        d = d[[2,4,3,8,10,9,14,16,15,20,22,21], :]
        xe, ye = xi/GP, eta/GP
        H = 1/4*np.array([(1-xe)*(1-ye), (1+xe)*(1-ye), (1+xe)*(1+ye), (1-xe)*(1+ye)])
        Hs = self.Hs()
        q = [Hs @ (self.B_s(a, b) @ d) for a, b in [(-GP,-GP), (GP,-GP), (GP,GP), (-GP,GP)]]
        Qx = sum(H[i]*q[i][0, 0] for i in range(4))
        Qy = sum(H[i]*q[i][1, 0] for i in range(4))
        return np.array([Qx, Qy])

    def membrane(self, d_glob, xi=0.0, eta=0.0):
        """Tensiones de membrana [Sx, Sy, Txy] (multiplicar por t para N/long.)."""
        d = self._d_local(d_glob)[[0,1,6,7,12,13,18,19], :]
        xe, ye = xi/GP, eta/GP
        H = 1/4*np.array([(1-xe)*(1-ye), (1+xe)*(1-ye), (1+xe)*(1+ye), (1-xe)*(1+ye)])
        Cm = self.Cm()
        s = [Cm @ (self.B_m(a, b) @ d) for a, b in [(-GP,-GP), (GP,-GP), (GP,GP), (-GP,GP)]]
        Sx = sum(H[i]*s[i][0, 0] for i in range(4))
        Sy = sum(H[i]*s[i][1, 0] for i in range(4))
        Txy = sum(H[i]*s[i][2, 0] for i in range(4))
        return np.array([Sx, Sy, Txy])
