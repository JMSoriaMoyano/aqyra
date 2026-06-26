"""
Biblioteca EC2 §5.10 - PRETENSADO de hormigon (EN 1992-1-1, AN Espana).

Para una viga isostatica biapoyada de luz L con un tendon de trazado PARABOLICO
(excentricidad e en centro de vano, 0 en apoyos), conducto adherente (postesado):

  - PRETENSADO COMO CARGAS EQUIVALENTES (load balancing, §5.10):
        w_p = 8*P*e / L^2   (uniforme hacia ARRIBA; equilibra cargas hacia abajo)
    mas el AXIL de compresion P (en el c.d.g., porque el tendon ancla en e=0 en
    apoyos) y, si hubiera anclaje excentrico, los momentos de anclaje P*e_anc.
  - PRETENSADO COMO FUERZA+EXCENTRICIDAD: tension directa en fibra
        sigma = -P/A -+ P*e*c / I  (+ contribucion de M exterior).
    Ambos metodos dan el MISMO estado tensional (validacion cruzada).

  - PERDIDAS INSTANTANEAS (§5.10.5): rozamiento mu*(theta + k*x), penetracion de
    cuna (reaccion en una longitud de influencia), acortamiento elastico.
  - PERDIDAS DIFERIDAS (§5.10.6): retraccion + fluencia + relajacion (formula
    combinada simplificada 5.46).

Sigmas: compresion NEGATIVA, traccion POSITIVA.
SI (N, m, Pa). [confirmar AN]: mu, k, limites de tension del acero activo.
"""
import math

GP_FAV = 1.0      # coef. del pretensado en ELU (favorable, P como accion)
ALPHA_E_DEF = 6.0  # n = Ep/Ecm tipico (acortamiento elastico)


# ----------------------------------------------------------------------------
# Trazado parabolico y geometria del tendon
# ----------------------------------------------------------------------------
def e_parabola(x, L, e_centro, e_apoyo=0.0):
    """Excentricidad (m, positiva hacia abajo) en x para parabola simetrica."""
    f_sag = e_centro - e_apoyo
    return e_apoyo + 4.0 * f_sag * (x / L) * (1.0 - x / L)


def angulo_acumulado(x, L, e_centro, e_apoyo=0.0):
    """Angulo acumulado theta(x) del tendon desde el anclaje activo (rad).
    Para parabola y = e_apoyo + 4f(x/L)(1-x/L): y' = 4f/L*(1-2x/L). El angulo
    desviado acumulado desde x=0 es |y'(0)-y'(x)| = (8f/L^2)*x para x<=L/2."""
    f_sag = e_centro - e_apoyo
    yp0 = 4.0 * f_sag / L            # pendiente en el anclaje (x=0)
    yp = 4.0 * f_sag / L * (1.0 - 2.0 * x / L)
    return abs(yp0 - yp)


def longitud_tendon(L, e_centro, e_apoyo=0.0):
    """Longitud del tendon (aprox. parabolica, ~ L para flechas pequenas)."""
    f_sag = e_centro - e_apoyo
    # longitud de arco de parabola, serie de primer orden
    return L * (1.0 + (8.0 / 3.0) * (f_sag / L) ** 2)


# ----------------------------------------------------------------------------
# Cargas equivalentes (load balancing)
# ----------------------------------------------------------------------------
def cargas_equivalentes(P, L, e_centro, e_apoyo=0.0):
    """Devuelve la carga equivalente del tendon parabolico.
    w_p = 8*P*f/L^2 (hacia ARRIBA, equilibra la carga gravitatoria), el axil de
    compresion N=P y los momentos de anclaje (0 si e_apoyo=0)."""
    f_sag = e_centro - e_apoyo
    w_p = 8.0 * P * f_sag / L ** 2          # N/m hacia arriba
    N = P                                    # axil de compresion (N)
    M_anc = P * e_apoyo                       # momento de anclaje en extremos (N*m)
    return {"w_p_N_m": w_p, "N_axil_N": N, "M_anclaje_Nm": M_anc,
            "flecha_f_m": f_sag,
            "formula": "w_p = 8*P*f/L^2 (hacia arriba)"}


def P_balance(w_obj, L, e_centro, e_apoyo=0.0):
    """Fuerza de pretensado que equilibra una carga uniforme w_obj (N/m)."""
    f_sag = e_centro - e_apoyo
    return w_obj * L ** 2 / (8.0 * f_sag)


# ----------------------------------------------------------------------------
# Tensiones por fibra (fuerza + excentricidad)
# ----------------------------------------------------------------------------
def tensiones_fibra(P, e, M_ext, A, I, c_sup, c_inf):
    """Tension en fibra superior e inferior (Pa). Compresion negativa.
    sigma = -P/A + (P*e - M_ext)*c/I con c medida desde c.d.g.
    Convenio: e positiva hacia abajo, M_ext positivo (sagging) tracciona el fondo.
    Momento del pretensado M_p = -P*e (hogging, contraflecha) -> tracciona arriba.
    Momento total M = M_ext + M_p = M_ext - P*e.
        sigma_sup = -P/A - M*c_sup/I
        sigma_inf = -P/A + M*c_inf/I
    """
    M = M_ext - P * e
    sigma_sup = -P / A - M * c_sup / I
    sigma_inf = -P / A + M * c_inf / I
    return sigma_sup, sigma_inf


# ----------------------------------------------------------------------------
# Perdidas instantaneas (§5.10.5)
# ----------------------------------------------------------------------------
def perdida_rozamiento(sigma_pmax, x, theta, mu, k):
    """Perdida por rozamiento (§5.10.5.2, ec. 5.45):
       sigma_p(x) = sigma_pmax * exp(-mu*(theta + k*x))
       delta_sigma = sigma_pmax*(1 - exp(-mu*(theta+k*x)))."""
    factor = math.exp(-mu * (theta + k * x))
    return sigma_pmax * (1.0 - factor), sigma_pmax * factor


def perdida_penetracion_cuna(sigma_pmax, slip_m, Ep, mu, k, L, e_centro):
    """Perdida media por penetracion de cuna (§5.10.5.3). El deslizamiento del
    anclaje retesa hacia atras una longitud de influencia x_set donde la perdida
    de friccion de ida iguala el area perdida por el reentrado:
        Ep*slip = integral_0^xset (sigma_ida - sigma_vuelta) dx
    Con perdida de friccion por unidad de longitud p = sigma_pmax*mu*(8f/L^2 + k)
    (aprox. lineal cerca del anclaje), la zona afectada x_set = sqrt(Ep*slip/p) y
    la perdida media de fuerza repartida en el tendon es 2*p*x_set^2/L_tendon."""
    # gradiente de tension por friccion cerca del anclaje (rad/m + parasito)
    grad_theta = 8.0 * e_centro / L ** 2       # d(theta)/dx cerca del anclaje
    p = sigma_pmax * mu * (grad_theta + k)      # Pa/m
    if p <= 0:
        return 0.0, 0.0, 0.0
    x_set = math.sqrt(Ep * slip_m / p)          # longitud de influencia (m)
    x_set = min(x_set, L)                        # no excede la viga
    dsigma_anc = 2.0 * p * x_set                 # perdida en el anclaje (Pa)
    # perdida media a lo largo del tendon (triangulo de base x_set)
    dsigma_media = (p * x_set ** 2) / L
    return dsigma_anc, dsigma_media, x_set


def perdida_acortamiento_elastico(sigma_c_qp, Ep, Ecm, n_tendones=1):
    """Perdida por acortamiento elastico (§5.10.5.1). Postesado con varios
    tendones tesados sucesivamente: delta = (n-1)/(2n) * (Ep/Ecm) * sigma_c.
    Con n=1 tendon (o tesado simultaneo) la perdida tiende a 0; aqui se adopta el
    valor conservador 0.5*(Ep/Ecm)*sigma_c (un solo tendon, valor medio)."""
    alpha_e = Ep / Ecm
    if n_tendones <= 1:
        factor = 0.5
    else:
        factor = (n_tendones - 1) / (2.0 * n_tendones)
    return factor * alpha_e * abs(sigma_c_qp)


# ----------------------------------------------------------------------------
# Perdidas diferidas (§5.10.6, ec. 5.46)
# ----------------------------------------------------------------------------
def perdidas_diferidas(eps_cs, Ep, dsigma_pr, phi, sigma_c_qp, Ecm,
                       Ap, Ac, Ic, zcp):
    """Perdida diferida combinada (retraccion + fluencia + relajacion), ec. 5.46:

      d_sigma = (eps_cs*Ep + 0.8*d_sigma_pr + (Ep/Ecm)*phi*sigma_c,QP)
                / (1 + (Ep/Ecm)*(Ap/Ac)*(1 + Ac/Ic*zcp^2)*(1 + 0.8*phi))

    eps_cs deformacion de retraccion total; dsigma_pr perdida por relajacion;
    phi coef. de fluencia; sigma_c_qp tension del hormigon a la cota del tendon
    bajo cuasipermanente+pretensado (negativa=compresion); zcp distancia c.d.g.-
    tendon. Devuelve la perdida de tension del acero (Pa, positiva=perdida)."""
    alpha = Ep / Ecm
    num = eps_cs * Ep + 0.8 * dsigma_pr + alpha * phi * abs(sigma_c_qp)
    den = 1.0 + alpha * (Ap / Ac) * (1.0 + Ac / Ic * zcp ** 2) * (1.0 + 0.8 * phi)
    return num / den


def relajacion(sigma_pi, fpk, rho1000, clase=2, t_horas=500000.0):
    """Perdida por relajacion a tiempo infinito (§3.3.2, ec. 3.29 clase 2):
       d_sigma_pr/sigma_pi = 0.66*rho1000*exp(9.1*mu)*(t/1000)^(0.75*(1-mu))*1e-5
    con mu = sigma_pi/fpk. t en horas (t->inf ~ 500000 h)."""
    mu = sigma_pi / fpk
    if clase == 1:
        c1, c2 = 5.39, 6.7
    elif clase == 3:
        c1, c2 = 1.98, 8.0
    else:
        c1, c2 = 0.66, 9.1
    ratio = c1 * rho1000 * math.exp(c2 * mu) * (t_horas / 1000.0) ** (0.75 * (1.0 - mu)) * 1e-5
    return ratio * sigma_pi


# ----------------------------------------------------------------------------
# Combinaciones de acciones (con el pretensado como accion P)
# ----------------------------------------------------------------------------
def momento_isostatico(w, L, x=None):
    """Momento flector de una carga uniforme en viga biapoyada. Si x=None,
    devuelve el maximo en centro de vano w*L^2/8."""
    if x is None:
        x = L / 2.0
    return w * x * (L - x) / 2.0


def combinaciones_momentos(M_g0, M_g2, M_q, psi2, psi0=0.7, psi1=0.5):
    """Momentos de las combinaciones de servicio y ELU (kN*m de entrada -> mismas
    unidades de salida). M_perm=M_g0+M_g2."""
    M_perm = M_g0 + M_g2
    return {
        "M_g0": M_g0, "M_g2": M_g2, "M_perm": M_perm, "M_q": M_q,
        "M_caracteristica_rara": M_perm + M_q,
        "M_frecuente": M_perm + psi1 * M_q,
        "M_cuasipermanente": M_perm + psi2 * M_q,
        "M_ELU": 1.35 * M_perm + 1.5 * M_q,
     }
