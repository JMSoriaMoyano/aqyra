"""
Elemento BARRA 3D (6 GdL/nudo, 12 GdL) para el nucleo FEM propio (FEM-0).

Reproduce la formulacion de viga del oraculo PyNite (Member3D):
 - Rigidez local 12x12 de EULER-BERNOULLI por defecto (Phi = 0), identica a
   `Pynite.Member3D._k_unc()`, para garantizar la NO-REGRESION (oraculo EB).
 - Conmutador de cortante de TIMOSHENKO (`incluir_cortante=True` + areas de
   cortante Avy/Avz) para fases posteriores (FEM-1+); por defecto DESACTIVADO.
 - Terna local identica a `Member3D.T()` (vertical / horizontal / inclinada) +
   rotacion sobre el eje local x.
 - Liberaciones de extremo por CONDENSACION ESTATICA (idem PyNite).
 - Reacciones de empotramiento perfecto (FER) para cargas de barra
   uniforme/lineal (Fy/Fz/Fx locales y FX/FY/FZ globales), puntual, momento,
   torsor y TERMICA (axil uniforme + gradiente).

Convencion de ejes GLOBALES del ecosistema: X,Y horizontales, Z vertical,
gravedad -Z. SI (N, m). Esfuerzos de barra en ejes LOCALES:
   [N, Vy, Vz, T, My, Mz] en cada extremo (i, j).

Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
from __future__ import annotations
import numpy as np

GDL = 6  # grados de libertad por nudo


# --------------------------------------------------------------------------- #
#  Terna local (identica a Pynite.Member3D.T)                                  #
# --------------------------------------------------------------------------- #
def dir_cos(ni, nj, rotation=0.0):
    """Matriz 3x3 de cosenos directores (filas = ejes locales x,y,z globales)."""
    Xi, Yi, Zi = ni
    Xj, Yj, Zj = nj
    L = ((Xj - Xi) ** 2 + (Yj - Yi) ** 2 + (Zj - Zi) ** 2) ** 0.5
    x = np.array([(Xj - Xi) / L, (Yj - Yi) / L, (Zj - Zi) / L])

    def _close(a, b):
        return abs(a - b) < 1e-12

    if _close(Xi, Xj) and _close(Zi, Zj):          # vertical
        if Yj > Yi:
            y = np.array([-1.0, 0.0, 0.0]); z = np.array([0.0, 0.0, 1.0])
        else:
            y = np.array([1.0, 0.0, 0.0]); z = np.array([0.0, 0.0, 1.0])
    elif _close(Yi, Yj):                            # horizontal
        y = np.array([0.0, 1.0, 0.0])
        z = np.cross(x, y); z = z / np.linalg.norm(z)
    else:                                           # inclinada
        proj = np.array([Xj - Xi, 0.0, Zj - Zi])
        z = np.cross(proj, x) if Yj > Yi else np.cross(x, proj)
        z = z / np.linalg.norm(z)
        y = np.cross(z, x); y = y / np.linalg.norm(y)

    if rotation != 0.0:
        th = np.radians(rotation); c, s = np.cos(th), np.sin(th)
        # rotacion de y,z alrededor del eje local x
        y2 = c * y + s * z
        z2 = -s * y + c * z
        y, z = y2, z2

    return np.vstack([x, y, z])


def matriz_T(ni, nj, rotation=0.0):
    """Matriz de transformacion 12x12 (4 bloques 3x3 de cosenos directores)."""
    R = dir_cos(ni, nj, rotation)
    T = np.zeros((12, 12))
    for b in range(4):
        T[3 * b:3 * b + 3, 3 * b:3 * b + 3] = R
    return T


# --------------------------------------------------------------------------- #
#  Rigidez local (Euler-Bernoulli; Timoshenko opcional)                       #
# --------------------------------------------------------------------------- #
def k_local_unc(E, G, Iy, Iz, J, A, L, Avy=None, Avz=None, incluir_cortante=False):
    """Rigidez local 12x12 SIN condensar.

    Por defecto Euler-Bernoulli (Phi=0) -> identica a Pynite.Member3D._k_unc().
    Con `incluir_cortante=True` y areas de cortante -> Timoshenko.
    """
    if incluir_cortante and Avy and Avz:
        phiy = 12 * E * Iz / (G * Avy * L ** 2)   # cortante en plano xy (Iz)
        phiz = 12 * E * Iy / (G * Avz * L ** 2)   # cortante en plano xz (Iy)
    else:
        phiy = phiz = 0.0

    EAL = E * A / L
    GJL = G * J / L
    # flexion en plano local xy gobernada por Iz (giros/despl. y)
    az = E * Iz / (L ** 3 * (1 + phiy))
    kz1 = 12 * az
    kz2 = 6 * az * L
    kz3 = (4 + phiy) * az * L ** 2
    kz4 = (2 - phiy) * az * L ** 2
    # flexion en plano local xz gobernada por Iy (giros/despl. z)
    ay = E * Iy / (L ** 3 * (1 + phiz))
    ky1 = 12 * ay
    ky2 = 6 * ay * L
    ky3 = (4 + phiz) * ay * L ** 2
    ky4 = (2 - phiz) * ay * L ** 2

    k = np.zeros((12, 12))
    # axil
    k[0, 0] = k[6, 6] = EAL; k[0, 6] = k[6, 0] = -EAL
    # torsion
    k[3, 3] = k[9, 9] = GJL; k[3, 9] = k[9, 3] = -GJL
    # flexion xy (uy, rz)  -> dofs 1,5,7,11
    idx = [1, 5, 7, 11]
    sub = np.array([[kz1,  kz2, -kz1,  kz2],
                    [kz2,  kz3, -kz2,  kz4],
                    [-kz1, -kz2, kz1, -kz2],
                    [kz2,  kz4, -kz2,  kz3]])
    for a, ia in enumerate(idx):
        for b, ib in enumerate(idx):
            k[ia, ib] = sub[a, b]
    # flexion xz (uz, ry)  -> dofs 2,4,8,10 (signo de acople -k2 como PyNite)
    idy = [2, 4, 8, 10]
    suy = np.array([[ky1, -ky2, -ky1, -ky2],
                    [-ky2, ky3,  ky2,  ky4],
                    [-ky1, ky2,  ky1,  ky2],
                    [-ky2, ky4,  ky2,  ky3]])
    for a, ia in enumerate(idy):
        for b, ib in enumerate(idy):
            k[ia, ib] = suy[a, b]
    return k


def _partition(M, releases):
    keep = [i for i in range(12) if not releases[i]]
    rel = [i for i in range(12) if releases[i]]
    if M.ndim == 1:
        M = M.reshape(-1, 1)
    k11 = M[np.ix_(keep, keep)] if M.shape[1] > 1 else M[keep]
    if M.shape[1] == 1:
        return M[keep], M[rel]
    return (M[np.ix_(keep, keep)], M[np.ix_(keep, rel)],
            M[np.ix_(rel, keep)], M[np.ix_(rel, rel)])


def condensar_k(k_unc, releases):
    """Condensacion estatica de las liberaciones (idem PyNite.Member3D.k)."""
    if not any(releases):
        return k_unc
    k11, k12, k21, k22 = _partition(k_unc, releases)
    kc = k11 - k12 @ np.linalg.inv(k22) @ k21
    for i, r in enumerate(releases):
        if r:
            kc = np.insert(kc, i, 0.0, axis=0)
            kc = np.insert(kc, i, 0.0, axis=1)
    return kc


def condensar_fer(fer_unc, k_unc, releases):
    if not any(releases):
        return fer_unc
    k11, k12, k21, k22 = _partition(k_unc, releases)
    f1, f2 = _partition(fer_unc, releases)
    fc = f1 - k12 @ np.linalg.inv(k22) @ f2
    for i, r in enumerate(releases):
        if r:
            fc = np.insert(fc, i, 0.0, axis=0)
    return fc


# --------------------------------------------------------------------------- #
#  Reacciones de empotramiento perfecto (FER) -- formulas de PyNite           #
# --------------------------------------------------------------------------- #
def fer_dist(w1, w2, x1, x2, L, direction):
    """Carga linealmente distribuida en eje local 'Fy' o 'Fz'."""
    FER = np.zeros((12, 1))
    if direction == "Fy":
        FER[1, 0] = (x1 - x2)*(10*L**3*w1 + 10*L**3*w2 - 15*L*w1*x1**2 - 10*L*w1*x1*x2 - 5*L*w1*x2**2 - 5*L*w2*x1**2 - 10*L*w2*x1*x2 - 15*L*w2*x2**2 + 8*w1*x1**3 + 6*w1*x1**2*x2 + 4*w1*x1*x2**2 + 2*w1*x2**3 + 2*w2*x1**3 + 4*w2*x1**2*x2 + 6*w2*x1*x2**2 + 8*w2*x2**3)/(20*L**3)
        FER[5, 0] = (x1 - x2)*(20*L**2*w1*x1 + 10*L**2*w1*x2 + 10*L**2*w2*x1 + 20*L**2*w2*x2 - 30*L*w1*x1**2 - 20*L*w1*x1*x2 - 10*L*w1*x2**2 - 10*L*w2*x1**2 - 20*L*w2*x1*x2 - 30*L*w2*x2**2 + 12*w1*x1**3 + 9*w1*x1**2*x2 + 6*w1*x1*x2**2 + 3*w1*x2**3 + 3*w2*x1**3 + 6*w2*x1**2*x2 + 9*w2*x1*x2**2 + 12*w2*x2**3)/(60*L**2)
        FER[7, 0] = -(x1 - x2)*(-15*L*w1*x1**2 - 10*L*w1*x1*x2 - 5*L*w1*x2**2 - 5*L*w2*x1**2 - 10*L*w2*x1*x2 - 15*L*w2*x2**2 + 8*w1*x1**3 + 6*w1*x1**2*x2 + 4*w1*x1*x2**2 + 2*w1*x2**3 + 2*w2*x1**3 + 4*w2*x1**2*x2 + 6*w2*x1*x2**2 + 8*w2*x2**3)/(20*L**3)
        FER[11, 0] = (x1 - x2)*(-15*L*w1*x1**2 - 10*L*w1*x1*x2 - 5*L*w1*x2**2 - 5*L*w2*x1**2 - 10*L*w2*x1*x2 - 15*L*w2*x2**2 + 12*w1*x1**3 + 9*w1*x1**2*x2 + 6*w1*x1*x2**2 + 3*w1*x2**3 + 3*w2*x1**3 + 6*w2*x1**2*x2 + 9*w2*x1*x2**2 + 12*w2*x2**3)/(60*L**2)
    elif direction == "Fz":
        FER[2, 0] = (x1 - x2)*(10*L**3*w1 + 10*L**3*w2 - 15*L*w1*x1**2 - 10*L*w1*x1*x2 - 5*L*w1*x2**2 - 5*L*w2*x1**2 - 10*L*w2*x1*x2 - 15*L*w2*x2**2 + 8*w1*x1**3 + 6*w1*x1**2*x2 + 4*w1*x1*x2**2 + 2*w1*x2**3 + 2*w2*x1**3 + 4*w2*x1**2*x2 + 6*w2*x1*x2**2 + 8*w2*x2**3)/(20*L**3)
        FER[4, 0] = -(x1 - x2)*(20*L**2*w1*x1 + 10*L**2*w1*x2 + 10*L**2*w2*x1 + 20*L**2*w2*x2 - 30*L*w1*x1**2 - 20*L*w1*x1*x2 - 10*L*w1*x2**2 - 10*L*w2*x1**2 - 20*L*w2*x1*x2 - 30*L*w2*x2**2 + 12*w1*x1**3 + 9*w1*x1**2*x2 + 6*w1*x1*x2**2 + 3*w1*x2**3 + 3*w2*x1**3 + 6*w2*x1**2*x2 + 9*w2*x1*x2**2 + 12*w2*x2**3)/(60*L**2)
        FER[8, 0] = -(x1 - x2)*(-15*L*w1*x1**2 - 10*L*w1*x1*x2 - 5*L*w1*x2**2 - 5*L*w2*x1**2 - 10*L*w2*x1*x2 - 15*L*w2*x2**2 + 8*w1*x1**3 + 6*w1*x1**2*x2 + 4*w1*x1*x2**2 + 2*w1*x2**3 + 2*w2*x1**3 + 4*w2*x1**2*x2 + 6*w2*x1*x2**2 + 8*w2*x2**3)/(20*L**3)
        FER[10, 0] = -(x1 - x2)*(-15*L*w1*x1**2 - 10*L*w1*x1*x2 - 5*L*w1*x2**2 - 5*L*w2*x1**2 - 10*L*w2*x1*x2 - 15*L*w2*x2**2 + 12*w1*x1**3 + 9*w1*x1**2*x2 + 6*w1*x1*x2**2 + 3*w1*x2**3 + 3*w2*x1**3 + 6*w2*x1**2*x2 + 9*w2*x1*x2**2 + 12*w2*x2**3)/(60*L**2)
    return FER


def fer_axial_lin(p1, p2, x1, x2, L):
    FER = np.zeros((12, 1))
    FER[0, 0] = 1/(6*L)*(x1-x2)*(3*L*p1+3*L*p2-2*p1*x1-p1*x2-p2*x1-2*p2*x2)
    FER[6, 0] = 1/(6*L)*(x1-x2)*(2*p1*x1+p1*x2+p2*x1+2*p2*x2)
    return FER


def fer_pt(P, x, L, direction):
    b = L - x
    FER = np.zeros((12, 1))
    if direction == "Fy":
        FER[1, 0] = -P*b**2*(L+2*x)/L**3; FER[5, 0] = -P*x*b**2/L**2
        FER[7, 0] = -P*x**2*(L+2*b)/L**3; FER[11, 0] = P*x**2*b/L**2
    elif direction == "Fz":
        FER[2, 0] = -P*b**2*(L+2*x)/L**3; FER[4, 0] = P*x*b**2/L**2
        FER[8, 0] = -P*x**2*(L+2*b)/L**3; FER[10, 0] = -P*x**2*b/L**2
    return FER


def fer_axial_pt(P, x, L):
    FER = np.zeros((12, 1)); FER[0, 0] = -P*(L-x)/L; FER[6, 0] = -P*x/L
    return FER


def fer_termica_axil(E, A, alpha, dT, L):
    """Axil de coaccion por dilatacion uniforme impedida (N = E*A*alpha*dT)."""
    N = E * A * alpha * dT
    FER = np.zeros((12, 1)); FER[0, 0] = N; FER[6, 0] = -N
    return FER


def fer_termica_gradiente(E, Iz, alpha, dT_grad, h, L):
    """Momento de coaccion por gradiente termico (curvatura = alpha*dT/h).

    Aplica flexion en el plano local xy (Mz). M = E*Iz*alpha*dT_grad/h.
    """
    M = E * Iz * alpha * dT_grad / h
    FER = np.zeros((12, 1)); FER[5, 0] = M; FER[11, 0] = -M
    return FER
