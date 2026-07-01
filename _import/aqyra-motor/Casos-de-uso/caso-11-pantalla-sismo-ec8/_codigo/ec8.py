"""
Biblioteca EC8 (EN 1998-1) reutilizable - Caso 11 (familia sismica).

Contiene, de forma autocontenida y validable:
  - Espectro de calculo Sd(T) con las CUATRO ramas (EN 1998-1 §3.2.2.5,
    ec. 3.13 a 3.16), con limite inferior beta*ag (beta=0.2 recomendado
    [confirmar AN]).
  - Analisis modal de un voladizo equivalente (stick) con rigidez de
    flexion (Euler-Bernoulli) + flexibilidad de CORTANTE de la pared
    (Timoshenko), masas concentradas. Resuelve el autoproblema con
    scipy.linalg.eigh -> T_i, modos, factores de participacion Gamma_i y
    masas modales efectivas M_eff,i. Combinacion modal SRSS / CQC.
  - Metodo de fuerzas laterales equivalentes (§4.3.3.2).
  - Esfuerzos en altura (cortante/momento de voladizo), derivas (§4.3.4) y
    N-M en base.

Convencion de unidades internas: SI (N, m, kg, s). Las salidas para JSON van
en kN, kN*m, m, s, % segun convenga (se documenta en cada campo).

NDP (parametros nacionales) marcados [confirmar AN] (NCSE-02 / EC8 NDP Espana).
"""
import math
import numpy as np

try:
    from scipy.linalg import eigh as _eigh
    _HAS_SCIPY = True
except Exception:
    _HAS_SCIPY = False

G = 9.81  # m/s2


# --------------------------------------------------------------------------
# 1) Espectro de calculo Sd(T)  (EN 1998-1 §3.2.2.5, ec. 3.13-3.16)
# --------------------------------------------------------------------------
def Sd(T, ag, S, TB, TC, TD, q, beta=0.2):
    """Espectro de calculo horizontal Sd(T) en m/s2.

    ag en m/s2 (NO en g). Las cuatro ramas:
      0   <= T < TB : ag*S*[2/3 + (T/TB)*(2.5/q - 2/3)]            (3.13)
      TB  <= T < TC : ag*S*2.5/q                                   (3.14)
      TC  <= T < TD : ag*S*(2.5/q)*(TC/T)         >= beta*ag       (3.15)
      TD  <= T      : ag*S*(2.5/q)*(TC*TD/T^2)     >= beta*ag      (3.16)
    """
    if T < 0:
        T = 0.0
    if T < TB:
        val = ag * S * (2.0 / 3.0 + (T / TB) * (2.5 / q - 2.0 / 3.0))
    elif T < TC:
        val = ag * S * 2.5 / q
    elif T < TD:
        val = ag * S * (2.5 / q) * (TC / T)
        val = max(val, beta * ag)
    else:
        val = ag * S * (2.5 / q) * (TC * TD / (T * T))
        val = max(val, beta * ag)
    return val


def Sd_meseta(ag, S, q):
    """Valor de meseta (rama 3.14) en m/s2."""
    return ag * S * 2.5 / q


def espectro_curva(ag, S, TB, TC, TD, q, beta=0.2, Tmax=4.0, n=400):
    """Devuelve (T[], Sd[]) en m/s2 para graficar."""
    Ts = np.linspace(0.0, Tmax, n)
    Ss = np.array([Sd(t, ag, S, TB, TC, TD, q, beta) for t in Ts])
    return Ts, Ss


# --------------------------------------------------------------------------
# 2) Matrices del stick: rigidez lateral condensada a GDL laterales
# --------------------------------------------------------------------------
def _element_stiffness_timoshenko(E, I, A_v, Gsh, L):
    """Matriz 4x4 de rigidez de viga Timoshenko (gdl: v1,th1,v2,th2)."""
    phi = 12.0 * E * I / (Gsh * A_v * L * L) if A_v > 0 else 0.0
    c = E * I / ((1.0 + phi) * L ** 3)
    k = np.array([
        [12.0,        6.0 * L,            -12.0,       6.0 * L],
        [6.0 * L,     (4.0 + phi) * L * L, -6.0 * L,   (2.0 - phi) * L * L],
        [-12.0,      -6.0 * L,             12.0,      -6.0 * L],
        [6.0 * L,     (2.0 - phi) * L * L, -6.0 * L,   (4.0 + phi) * L * L],
    ]) * c
    return k


def stick_lateral_stiffness(z_nodes, E, I, A_v, Gsh, base_fixed=True):
    """Ensambla la rigidez del voladizo (flexion+cortante Timoshenko) con
    2 gdl por nodo (v, theta), empotrado en base, y condensa estaticamente
    (Guyan) a los GDL laterales v de las plantas (z>0).

    z_nodes: lista ordenada [0, z1, ..., zN] (z=0 base).
    Devuelve K_ll (n_plantas x n_plantas) en N/m.
    """
    nn = len(z_nodes)
    ndof = 2 * nn
    K = np.zeros((ndof, ndof))
    for e in range(nn - 1):
        L = z_nodes[e + 1] - z_nodes[e]
        ke = _element_stiffness_timoshenko(E, I, A_v, Gsh, L)
        dofs = [2 * e, 2 * e + 1, 2 * (e + 1), 2 * (e + 1) + 1]
        for a in range(4):
            for b in range(4):
                K[dofs[a], dofs[b]] += ke[a, b]
    # base empotrada: elimina gdl del nodo 0 (v0, th0)
    if base_fixed:
        keep = list(range(2, ndof))
        K = K[np.ix_(keep, keep)]
    # gdl restantes: por planta i (1..N): v_i = idx 2*(i-1), th_i = 2*(i-1)+1
    npl = nn - 1
    lat = [2 * i for i in range(npl)]          # indices de v_i
    rot = [2 * i + 1 for i in range(npl)]       # indices de theta_i
    Kll = K[np.ix_(lat, lat)]
    Klr = K[np.ix_(lat, rot)]
    Krl = K[np.ix_(rot, lat)]
    Krr = K[np.ix_(rot, rot)]
    # condensacion estatica (Guyan): theta no tiene masa -> se condensa
    Kcond = Kll - Klr.dot(np.linalg.solve(Krr, Krl))
    return Kcond


# --------------------------------------------------------------------------
# 3) Analisis modal
# --------------------------------------------------------------------------
def modal(Kll, masses):
    """Resuelve K*phi = w^2 * M * phi con M lumped diagonal (masses en kg).

    Devuelve dict con periodos, frecuencias, modos (normalizados a M),
    factores de participacion Gamma_i, masas modales efectivas M_eff,i (kg)
    y su fraccion respecto a la masa total.
    """
    M = np.diag(np.asarray(masses, dtype=float))
    npl = len(masses)
    if _HAS_SCIPY:
        w2, phi = _eigh(Kll, M)
    else:
        # generalizado via Cholesky de M (M diagonal positiva)
        Minv_sqrt = np.diag(1.0 / np.sqrt(np.diag(M)))
        A = Minv_sqrt.dot(Kll).dot(Minv_sqrt)
        w2, y = np.linalg.eigh(A)
        phi = Minv_sqrt.dot(y)
    w2 = np.clip(w2, 0.0, None)
    omega = np.sqrt(w2)
    T = np.where(omega > 0, 2.0 * math.pi / np.where(omega > 0, omega, 1.0), 0.0)
    # normalizacion a masa: phi_i^T M phi_i = 1
    for i in range(npl):
        m_i = phi[:, i].dot(M).dot(phi[:, i])
        if m_i > 0:
            phi[:, i] /= math.sqrt(m_i)
    # vector de influencia (lateral) = 1
    r = np.ones(npl)
    Mr = M.dot(r)
    Gamma = phi.T.dot(Mr)            # = phi_i^T M r (con norma a masa)
    Meff = Gamma ** 2                 # masa modal efectiva (kg) (norma a masa)
    Mtot = float(np.sum(masses))
    order = np.argsort(T)[::-1]       # de mayor periodo (modo 1) a menor
    modes = []
    for k, idx in enumerate(order):
        modes.append({
            "modo": k + 1,
            "T_s": float(T[idx]),
            "omega_rad_s": float(omega[idx]),
            "f_hz": float(omega[idx] / (2.0 * math.pi)) if omega[idx] > 0 else 0.0,
            "phi": [float(x) for x in phi[:, idx]],
            "Gamma": float(Gamma[idx]),
            "Meff_kg": float(Meff[idx]),
            "Meff_frac": float(Meff[idx] / Mtot) if Mtot > 0 else 0.0,
        })
    return {"modos": modes, "M_total_kg": Mtot,
            "suma_Meff_frac": float(sum(m["Meff_frac"] for m in modes))}


# --------------------------------------------------------------------------
# 4) Fuerzas modales espectrales (SRSS) por modo y respuesta combinada
# --------------------------------------------------------------------------
def fuerzas_modales(modal_res, masses, z_nodes_plant, sd_func):
    """Fuerzas laterales por modo: f_i = Gamma * phi_i * m * Sd(T) y SRSS.

    z_nodes_plant: alturas de las plantas (z>0), longitud n_plantas.
    sd_func: callable T->Sd(T) [m/s2].
    Devuelve dict con, por modo, fuerzas de planta, cortante basal, momento;
    y la envolvente SRSS de fuerzas/cortante/momento en altura.
    """
    masses = np.asarray(masses, float)
    z = np.asarray(z_nodes_plant, float)
    npl = len(masses)
    por_modo = []
    F_modos = []      # fuerzas de planta por modo (matriz)
    for m in modal_res["modos"]:
        T = m["T_s"]
        Sd_T = sd_func(T)
        phi = np.asarray(m["phi"], float)
        Gamma = m["Gamma"]
        f = Gamma * Sd_T * (masses * phi)   # fuerza de planta (N)
        Fb = float(np.sum(f))
        por_modo.append({
            "modo": m["modo"], "T_s": T, "Sd_T_ms2": float(Sd_T),
            "Sd_T_g": float(Sd_T / G),
            "F_i_kN": [float(x / 1e3) for x in f],
            "Fb_kN": float(Fb / 1e3),
            "Meff_frac": m["Meff_frac"],
        })
        F_modos.append(f)
    F_modos = np.array(F_modos)               # (nmodos, npl)
    # SRSS de cortante y momento en altura, combinando por modo los esfuerzos
    Vmod = np.zeros((len(F_modos), npl))      # cortante en arranque de cada planta
    Mmod = np.zeros((len(F_modos), npl))
    z_full = np.concatenate(([0.0], z))       # incluye base
    for k in range(len(F_modos)):
        f = F_modos[k]
        # cortante en la base de la planta j = suma de fuerzas en >= j
        for j in range(npl):
            Vmod[k, j] = np.sum(f[j:])
        # momento en cada nivel j (arranque de tramo j) por fuerzas superiores:
        for j in range(npl):
            Mmod[k, j] = np.sum(f[j:] * (z[j:] - z_full[j]))
    # SRSS
    V_srss = np.sqrt(np.sum(Vmod ** 2, axis=0))         # por planta (N)
    Fb_srss = math.sqrt(sum((np.sum(f)) ** 2 for f in F_modos))
    # momento de vuelco en base (z=0): SRSS de M de cada modo en base
    Mbase_mod = np.array([np.sum(F_modos[k] * z) for k in range(len(F_modos))])
    Mbase_srss = math.sqrt(np.sum(Mbase_mod ** 2))
    # ley de momento en altura (envolvente SRSS) en cota z_full[j]
    M_srss_levels = []
    for j in range(npl + 1):
        zc = z_full[j]
        Mmod_j = np.array([np.sum(F_modos[k] * np.maximum(z - zc, 0.0)) for k in range(len(F_modos))])
        M_srss_levels.append(math.sqrt(np.sum(Mmod_j ** 2)))
    return {
        "por_modo": por_modo,
        "Fb_SRSS_kN": float(Fb_srss / 1e3),
        "V_SRSS_kN": [float(v / 1e3) for v in V_srss],
        "Mbase_SRSS_kNm": float(Mbase_srss / 1e3),
        "z_niveles_m": [float(x) for x in z_full],
        "M_SRSS_niveles_kNm": [float(x / 1e3) for x in M_srss_levels],
    }


# --------------------------------------------------------------------------
# 5) Metodo de fuerzas laterales equivalentes (§4.3.3.2)
# --------------------------------------------------------------------------
def fuerzas_laterales(T1, masses, z_nodes_plant, ag, S, TB, TC, TD, q,
                      lam=0.85, beta=0.2):
    """Cortante basal Fb=Sd(T1)*m*lambda y distribucion lineal F_i.

    Distribucion §4.3.3.2.3 ec.(4.11) con forma aproximada lineal s_i=z_i:
       F_i = Fb * (z_i*m_i) / sum(z_j*m_j)
    """
    masses = np.asarray(masses, float)
    z = np.asarray(z_nodes_plant, float)
    Mtot = float(np.sum(masses))
    Sd_T1 = Sd(T1, ag, S, TB, TC, TD, q, beta)
    Fb = Sd_T1 * Mtot * lam                      # N
    num = z * masses
    F = Fb * num / np.sum(num)                    # N por planta
    # leyes de cortante y momento (voladizo)
    npl = len(masses)
    z_full = np.concatenate(([0.0], z))
    V = np.array([np.sum(F[j:]) for j in range(npl)])         # cortante en arranque de tramo j
    M_levels = np.array([np.sum(F * np.maximum(z - z_full[j], 0.0)) for j in range(npl + 1)])
    Mbase = float(np.sum(F * z))
    z_eff = Mbase / Fb if Fb > 0 else 0.0
    return {
        "T1_s": float(T1), "Sd_T1_ms2": float(Sd_T1), "Sd_T1_g": float(Sd_T1 / G),
        "Fb_kN": float(Fb / 1e3),
        "F_i_kN": [float(x / 1e3) for x in F],
        "V_kN": [float(x / 1e3) for x in V],
        "z_niveles_m": [float(x) for x in z_full],
        "M_niveles_kNm": [float(x / 1e3) for x in M_levels],
        "Mbase_kNm": float(Mbase / 1e3),
        "z_eficaz_m": float(z_eff),
        "suma_Fi_kN": float(np.sum(F) / 1e3),
        "equilibrio_error_pct": float(abs(np.sum(F) - Fb) / Fb * 100.0) if Fb > 0 else 0.0,
    }


# --------------------------------------------------------------------------
# 6) Derivas (desplazamientos elasticos * q, §4.3.4)
# --------------------------------------------------------------------------
def derivas(Kll, F_planta_N, z_nodes_plant, q):
    """Desplazamientos del sistema reducido bajo las fuerzas de planta F (N),
    deriva de calculo d_r = q*d_e por planta (§4.3.4 ec.4.23) y desplaz.
    elasticos.

    Devuelve por planta: d_elastico (m), d_diseno=q*d_e (m), deriva entre
    plantas d_r (m) = diferencia de d_diseno entre niveles consecutivos.
    """
    F = np.asarray(F_planta_N, float)
    d_e = np.linalg.solve(Kll, F)        # desplaz. elasticos (m)
    d_d = q * d_e                          # desplaz. de diseno (inelasticos)
    z = np.asarray(z_nodes_plant, float)
    npl = len(z)
    h = np.diff(np.concatenate(([0.0], z)))   # altura de cada planta
    dr = np.zeros(npl)
    prev = 0.0
    for i in range(npl):
        dr[i] = d_d[i] - prev
        prev = d_d[i]
    return {
        "d_elastico_mm": [float(x * 1e3) for x in d_e],
        "d_diseno_mm": [float(x * 1e3) for x in d_d],
        "dr_entreplanta_mm": [float(x * 1e3) for x in dr],
        "h_planta_m": [float(x) for x in h],
        "deriva_rel": [float(dr[i] / h[i]) for i in range(npl)],
    }
