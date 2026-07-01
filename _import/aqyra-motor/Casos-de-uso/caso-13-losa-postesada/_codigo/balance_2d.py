"""
Biblioteca de BALANCE DE CARGAS 2D para losa plana POSTESADA (EC2 §5.10 a 2D).

Extiende el load balancing 1D del caso 12 (ec2_pretensado.cargas_equivalentes) a
una losa con tendones en DOS direcciones:

  - banded (sobre lineas de pilares) en X, fuerza por metro de ancho P_x  (N/m)
  - distribuidos en Y, fuerza por metro de ancho P_y                        (N/m)

Cada familia de tendones parabolicos con flecha (drape) 'a' equilibra una presion
uniforme hacia arriba

      w_p = 8 * P * a / L^2     [N/m2]   (P en N/m de ancho)

La presion total equilibrada por el pretensado es w_p = w_p_x + w_p_y; el
residual es (carga a equilibrar) - w_p. El AXIL de precompresion en el plano es
sigma_cp = P / t por direccion (P en N/m, t espesor) -> N/m2.

Componente vertical de los tendones (para el descuento de punzonamiento §6.4.4):
la pendiente de la parabola en el punto de paso del perimetro de control define
la fuerza vertical hacia arriba que el tendon introduce; de forma integral, la
suma de la presion hacia arriba w_p actuando dentro del area encerrada por el
perimetro de control u1 equivale a la componente vertical V_p de los tendones que
lo cruzan (equilibrio del trozo de losa interior a u1).

Convenio: cargas hacia abajo positivas; w_p hacia arriba. SI (N, m, Pa).
[confirmar AN]: reparto de la carga a equilibrar entre direcciones, k1 de §6.4.4.
"""
import math


def w_balance_direccion(P_m, L, a):
    """Presion hacia arriba (N/m2) equilibrada por una familia parabolica.
    P_m: fuerza de pretensado por metro de ancho (N/m); a: drape (m); L: vano (m)."""
    return 8.0 * P_m * a / L ** 2


def P_para_equilibrar(w_obj_dir, L, a):
    """Fuerza de pretensado por metro de ancho (N/m) que equilibra w_obj_dir."""
    return w_obj_dir * L ** 2 / (8.0 * a)


def balance_2d(P_x, P_y, Lx, Ly, a_x, a_y, w_equilibrar, t):
    """Balance de cargas 2D.
    P_x, P_y : fuerza de pretensado por metro de ancho en X / Y (N/m).
    Lx, Ly   : vanos en X / Y (m).
    a_x, a_y : drapes (m).
    w_equilibrar : carga gravitatoria objetivo a equilibrar (N/m2, p.ej. permanente).
    t        : espesor de la losa (m).
    """
    w_px = w_balance_direccion(P_x, Lx, a_x)
    w_py = w_balance_direccion(P_y, Ly, a_y)
    w_p = w_px + w_py
    residual = w_equilibrar - w_p
    residual_pct = abs(residual) / w_equilibrar * 100.0 if w_equilibrar else 0.0
    sigma_cp_x = P_x / t
    sigma_cp_y = P_y / t
    sigma_cp = 0.5 * (sigma_cp_x + sigma_cp_y)   # precompresion media biaxial
    return {
        "w_px_N_m2": w_px, "w_py_N_m2": w_py, "w_p_N_m2": w_p,
        "w_equilibrar_N_m2": w_equilibrar,
        "residual_N_m2": residual, "residual_pct": residual_pct,
        "sigma_cp_x_Pa": sigma_cp_x, "sigma_cp_y_Pa": sigma_cp_y,
        "sigma_cp_Pa": sigma_cp,
        "P_x_para_equilibrar_N_m": P_para_equilibrar(0.5 * w_equilibrar, Lx, a_x),
        "P_y_para_equilibrar_N_m": P_para_equilibrar(0.5 * w_equilibrar, Ly, a_y),
    }


def Vp_perimetro_control(w_px, w_py, u1_lados, posicion="interior"):
    """Componente vertical de los tendones que cruzan el perimetro de control u1
    (EC2 §6.4.4). Por equilibrio del trozo de losa interior a u1, V_p = integral
    de la presion hacia arriba dentro del area encerrada por u1:

        V_p = (w_px + w_py) * A_dentro_de_u1

    Se adopta el area del rectangulo de control (lado del pilar + 2*2d por cara
    presente). 'u1_lados' = (lado_x, lado_y, d) en m. Para 'interior' el control
    rodea el pilar a 2d en las cuatro caras; para 'edge'/'corner' se reduce.
    Aproximacion conservadora con el rectangulo de control (en vez del perimetro
    redondeado), del lado de la seguridad para el descuento.
    """
    cx, cy, d = u1_lados
    # rectangulo de control basico (a 2d de cada cara presente)
    if posicion == "interior":
        ax = cx + 4.0 * d
        ay = cy + 4.0 * d
    elif posicion == "edge":
        ax = cx + 4.0 * d
        ay = cy + 2.0 * d
    else:  # corner
        ax = cx + 2.0 * d
        ay = cy + 2.0 * d
    A = ax * ay
    V_p = (w_px + w_py) * A
    return {"area_control_m2": A, "ax_m": ax, "ay_m": ay, "V_p_N": V_p}


def tensiones_fibra_franja(P_m, w_net_dir, L, t, c, I_m4_m, posicion="campo"):
    """Tension por fibra (Pa) en una franja unitaria (por metro de ancho) bajo el
    estado de servicio en una direccion: precompresion -P/t mas la flexion del
    momento NETO (carga no equilibrada) en el vano.

    P_m: pretensado por metro (N/m); w_net_dir: carga neta no equilibrada en esa
    direccion (N/m2 -> N/m por metro de ancho); L: vano; t: espesor; c: distancia
    al borde (m); I_m4_m: inercia por metro de ancho.
    'posicion': 'campo' (centro de vano, M positivo sagging) o 'apoyo'
    (sobre pilar, M negativo hogging).
    """
    # momento de la carga neta por metro de ancho en centro de vano (banda continua
    # aproximada como vano aislado): M = w*L^2/8 en campo; hogging similar en apoyo
    M_campo = w_net_dir * L ** 2 / 8.0       # N*m/m (sagging, tracciona el fondo)
    sigma_cp = -P_m / t                       # compresion (negativa)
    if posicion == "campo":
        # sagging: tracciona fibra inferior
        s_sup = sigma_cp - M_campo * c / I_m4_m
        s_inf = sigma_cp + M_campo * c / I_m4_m
    else:
        # hogging: tracciona fibra superior (M de signo opuesto)
        s_sup = sigma_cp + M_campo * c / I_m4_m
        s_inf = sigma_cp - M_campo * c / I_m4_m
    return {"M_net_kNm_m": M_campo / 1e3, "sigma_cp_MPa": sigma_cp / 1e6,
            "sigma_sup_MPa": s_sup / 1e6, "sigma_inf_MPa": s_inf / 1e6}
