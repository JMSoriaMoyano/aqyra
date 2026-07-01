"""
Biblioteca EC2 §5.10 / §5.5 - PRETENSADO en VIGA CONTINUA (HIPERESTATICA).

Amplia la biblioteca del caso 12 (isostatica) a estructuras hiperestaticas:

  - TRAZADO PARABOLICO POR VANO  e(x) (m, positiva HACIA ABAJO): en cada vano una
    parabola con flecha (drape) a sobre la cuerda de excentricidades de apoyo:
        e(x) = cuerda(x) + 4*a*(s/L)*(1 - s/L)      (s = abscisa local del vano)
    curvatura constante e'' = -8*a/L^2  ->  carga equivalente UNIFORME
        w_p = -P*e'' = 8*P*a/L^2  (hacia ARRIBA, equilibra la gravedad).

  - FEM de viga continua (Euler-Bernoulli, 2 GDL/nodo) para los esfuerzos de las
    cargas externas y de las CARGAS EQUIVALENTES del pretensado -> M_p,tot(x).

  - MOMENTOS DE PRETENSADO (lo nuevo de la hiperestaticidad):
        M1(x)   = -P*e(x)              (PRIMARIO, estructura liberada/isostatica)
        M_p,tot = momento de las cargas equivalentes en la viga CONTINUA (FEM)
        M_sec   = M_p,tot - M1         (SECUNDARIO/HIPERESTATICO, lineal entre
                                        apoyos, nulo en los apoyos extremos)
    Contraste por el METODO DE LAS FUERZAS (1 incognita: reaccion del apoyo
    central) -> debe coincidir con el FEM.

  - LINEA DE PRESIONES  e_p(x) = M_p,tot / P = e(x) + M_sec/P. Tendon CONCORDANTE
    si M_sec = 0 (la linea de presiones coincide con el tendon).

Sigmas: compresion NEGATIVA, traccion POSITIVA. Sagging (+) = traccion abajo.
SI (N, m, Pa). [confirmar AN].
"""
import numpy as np


# ---------------------------------------------------------------------------
# Trazado del tendon (parabola por vano)
# ---------------------------------------------------------------------------
def e_tendon(x, L, nv, e_ext, e_cen, drape):
    """Excentricidad e(x) (m, positiva hacia abajo) del tendon parabolico por vano.
    Vanos identicos de luz L; e en apoyos extremos = e_ext, en apoyo(s) interior =
    e_cen, drape = flecha de la parabola de vano sobre la cuerda."""
    x = np.atleast_1d(np.asarray(x, dtype=float))
    e = np.zeros_like(x)
    for k in range(nv):
        x0 = k * L
        s = x - x0
        m = (x >= x0 - 1e-9) & (x <= x0 + L + 1e-9)
        # extremos de excentricidad del vano k
        eL = e_ext if k == 0 else e_cen
        eR = e_ext if k == nv - 1 else e_cen
        cuerda = eL + (eR - eL) * (s / L)
        sag = 4.0 * drape * (s / L) * (1.0 - s / L)
        e[m] = cuerda[m] + sag[m]
    return e if e.size > 1 else float(e[0])


def curvatura_vano(drape, L):
    """e'' constante de la parabola de vano (1/m)."""
    return -8.0 * drape / L ** 2


def w_equivalente(P, drape, L):
    """Carga equivalente uniforme por vano (N/m, positiva hacia ARRIBA)."""
    return 8.0 * P * drape / L ** 2


# ---------------------------------------------------------------------------
# FEM de viga continua (Euler-Bernoulli)
# ---------------------------------------------------------------------------
def _beam_fem(EI, L, nv, supports_x, w_por_vano, n_el_vano=40):
    """Resuelve una viga continua de nv vanos de luz L con carga uniforme
    w_por_vano (N/m, signo +hacia abajo) en TODOS los vanos indicados.
    supports_x: lista de abscisas de apoyo (restriccion vertical w=0).
    Devuelve (x_nodos, M_nodos, V_nodos, w_desplaz). Sagging M>0.
    w_por_vano puede ser escalar (igual en todos) o lista por vano."""
    Ltot = nv * L
    n_el = nv * n_el_vano
    nodes = np.linspace(0.0, Ltot, n_el + 1)
    le = Ltot / n_el
    ndof = 2 * (n_el + 1)
    K = np.zeros((ndof, ndof))
    F = np.zeros(ndof)
    # rigidez de elemento viga (w, theta) x2
    c = EI / le ** 3
    ke = c * np.array([
        [12.0, 6.0 * le, -12.0, 6.0 * le],
        [6.0 * le, 4.0 * le ** 2, -6.0 * le, 2.0 * le ** 2],
        [-12.0, -6.0 * le, 12.0, -6.0 * le],
        [6.0 * le, 2.0 * le ** 2, -6.0 * le, 4.0 * le ** 2],
    ])
    if np.isscalar(w_por_vano):
        w_por_vano = [float(w_por_vano)] * nv
    # carga de cada elemento segun el vano al que pertenece
    we = np.zeros(n_el)
    for ie in range(n_el):
        xc = 0.5 * (nodes[ie] + nodes[ie + 1])
        kv = min(int(xc // L), nv - 1)
        we[ie] = w_por_vano[kv]
    for ie in range(n_el):
        w = we[ie]
        dof = [2 * ie, 2 * ie + 1, 2 * ie + 2, 2 * ie + 3]
        for a in range(4):
            for b in range(4):
                K[dof[a], dof[b]] += ke[a, b]
        # cargas consistentes de UDL (w hacia abajo +): fuerzas nodales -w*le/2,
        # momentos -+w*le^2/12. (vertical positivo hacia arriba en el sistema)
        fe = np.array([-w * le / 2.0, -w * le ** 2 / 12.0,
                       -w * le / 2.0, w * le ** 2 / 12.0])
        for a in range(4):
            F[dof[a]] += fe[a]
    # apoyos: w=0 en los nodos de apoyo
    fixed = []
    for sx in supports_x:
        idx = int(round(sx / le))
        fixed.append(2 * idx)
    free = [d for d in range(ndof) if d not in fixed]
    Kff = K[np.ix_(free, free)]
    Ff = F[free]
    Uf = np.linalg.solve(Kff, Ff)
    U = np.zeros(ndof)
    U[free] = Uf
    # momentos en nodos (sagging +): M = EI * w'' ; recuperamos de fuerzas de elem.
    Mnod = np.zeros(n_el + 1)
    Vnod = np.zeros(n_el + 1)
    cnt = np.zeros(n_el + 1)
    for ie in range(n_el):
        dof = [2 * ie, 2 * ie + 1, 2 * ie + 2, 2 * ie + 3]
        ue = U[dof]
        w = we[ie]
        # fuerzas de extremo = ke*ue - fe_empotramiento
        fe_fix = np.array([w * le / 2.0, w * le ** 2 / 12.0,
                           w * le / 2.0, -w * le ** 2 / 12.0])
        fend = ke.dot(ue) + fe_fix  # reacciones de empotramiento perfecto (signo)
        # momento flector sagging: en nodo i = -M_end_i ; en nodo j = +M_end_j
        Mi = -fend[1]
        Mj = fend[3]
        Mnod[ie] += Mi; cnt[ie] += 1
        Mnod[ie + 1] += Mj; cnt[ie + 1] += 1
        Vnod[ie] += fend[0]
        Vnod[ie + 1] += -fend[2]
    Mnod /= np.maximum(cnt, 1)
    wdisp = U[0::2]
    return nodes, Mnod, Vnod, wdisp


def esfuerzos_externos(EI, L, nv, supports_x, cargas, n_el_vano=40):
    """Calcula M(x) por caso de carga externa (dict nombre->w N/m hacia abajo) y
    tambien con la sobrecarga SOLO en patrones (no necesario aqui: ambos vanos)."""
    out = {}
    x = None
    for nombre, w in cargas.items():
        x, M, V, wd = _beam_fem(EI, L, nv, supports_x, w, n_el_vano)
        out[nombre] = {"M": M, "V": V, "w": wd}
    out["x"] = x
    return out


def momentos_pretensado(EI, L, nv, supports_x, P, drape, e_ext, e_cen, n_el_vano=40):
    """Momentos del pretensado en la viga continua.
       - cargas equivalentes: w_p hacia ARRIBA (signo - en el FEM, que toma +abajo)
       - M_p,tot = FEM(cargas equivalentes)
       - M1 = -P*e(x)
       - M_sec = M_p,tot - M1
    Devuelve dict con x, e, M1, M_p_tot, M_sec, w_p, linea_presiones."""
    wp = w_equivalente(P, drape, L)               # N/m hacia arriba (magnitud)
    x, Mptot, V, wd = _beam_fem(EI, L, nv, supports_x, -wp, n_el_vano)  # -w = hacia arriba
    e = e_tendon(x, L, nv, e_ext, e_cen, drape)
    M1 = -P * e
    Msec = Mptot - M1
    ep = Mptot / P                                  # linea de presiones (m, +abajo)
    return {"x": x, "e": e, "M1": M1, "M_p_tot": Mptot, "M_sec": Msec,
            "w_p_N_m": wp, "linea_presiones": ep, "V_p": V, "w_balance": wd}


# ---------------------------------------------------------------------------
# Metodo de las fuerzas (contraste del M_sec en viga continua de 2 vanos)
# ---------------------------------------------------------------------------
def metodo_fuerzas_2vanos(L, P, drape, e_ext, e_cen):
    """Para una continua simetrica de 2 vanos iguales con carga equivalente
    uniforme w_p (hacia arriba) en ambos vanos, el momento hiperestatico en el
    apoyo central por el metodo de las fuerzas:
       Estructura liberada = viga biapoyada de luz 2L (se quita el apoyo central).
       Redundante X1 = reaccion vertical del apoyo central.
       d10 = flecha en el centro de la liberada bajo las cargas equivalentes.
       d11 = flecha en el centro bajo X1=1.
       X1 = -d10/d11. Momento secundario en el centro = X1*L/2 ... (se deduce de
       la reaccion). Aqui devolvemos M_sec,centro = M_p,tot,centro - M1,centro con
       M_p,tot,centro = w_p*L^2/8 (resultado clasico de 2 vanos, sagging +)."""
    wp = w_equivalente(P, drape, L)            # hacia arriba
    # M_p,tot en el apoyo central de una continua de 2 vanos con carga uniforme
    # (hacia arriba -> sagging +): |M| = w*L^2/8
    Mptot_c = wp * L ** 2 / 8.0
    M1_c = -P * e_cen
    Msec_c = Mptot_c - M1_c
    return {"w_p_N_m": wp, "M_p_tot_centro_Nm": Mptot_c,
            "M1_centro_Nm": M1_c, "M_sec_centro_Nm": Msec_c,
            "metodo": "fuerzas (2 vanos simetricos): M_p,tot,c = w_p*L^2/8"}
