"""
Inyeccion del PRETENSADO como cargas equivalentes en el modelo de analisis C5.

REUTILIZA el pretensado existente (`motor-calculo-estructural/scripts/pretensado/
ec2_pretensado.py`, EC2 §5.10) -- NO lo reescribe. Calcula las perdidas
(instantaneas + diferidas simplificadas, ec. 5.46) y anade a cada viga el caso de
carga 'P' con la carga equivalente del tendon parabolico:

    w_p = 8*P_inf*f / L^2   (hacia ARRIBA)   +   axil de precompresion P_inf

El axil no flecta la viga isostatica (se usa en la comprobacion tensional EC2).
El caso 'P' entra en las combinaciones de `iap11.combinaciones` (gamma_P=1.0).

Import de `ec2_pretensado` por PYTHONPATH (el agente lo provee; frontera de reuso
entre plugins). [confirmar AN]: limites de tension del acero activo, mu, k, phi,
eps_cs. Pérdidas diferidas: modelo SIMPLIFICADO por coeficientes (decision nº5).
SI (N, m, Pa). Predimensionado/asistencia; revisar y firmar por tecnico competente.
"""
from __future__ import annotations
import ec2_pretensado as ec2p


def calcular_perdidas(tendon, L):
    """Perdidas del tendon (Pa de tension). tendon requiere: P0 (N, fuerza de
    tesado por viga), Ap (m2), e_centro, e_apoyo, fpk, Ep, Ecm, A, Ic(=Iy),
    Ac(=A), zcp(=e_centro), mu, k, slip, phi, eps_cs, rho1000."""
    Ap = tendon["Ap"]; sigma_p0 = tendon["P0"] / Ap
    L_t = L
    # --- instantaneas ---
    theta = ec2p.angulo_acumulado(L / 2, L, tendon["e_centro"], tendon.get("e_apoyo", 0.0))
    dfric, _ = ec2p.perdida_rozamiento(sigma_p0, L / 2, theta, tendon.get("mu", 0.19), tendon.get("k", 0.0075))
    _, dwedge, _ = ec2p.perdida_penetracion_cuna(sigma_p0, tendon.get("slip", 0.006), tendon["Ep"],
                                                 tendon.get("mu", 0.19), tendon.get("k", 0.0075), L, tendon["e_centro"])
    sigma_pmi = sigma_p0 - dfric - dwedge
    Pmi = sigma_pmi * Ap
    # tension del hormigon a la cota del tendon bajo P+g (cuasiperm.) (compresion neg.)
    A = tendon["A"]; Ic = tendon["Ic"]; zcp = tendon.get("zcp", tendon["e_centro"])
    M_g = tendon.get("M_g_qp", 0.0)
    sigma_c_qp = -Pmi / A - (Pmi * zcp - M_g) * zcp / Ic
    dela = ec2p.perdida_acortamiento_elastico(sigma_c_qp, tendon["Ep"], tendon["Ecm"], tendon.get("n_tendones", 1))
    sigma_pmi -= dela; Pmi = sigma_pmi * Ap
    # --- diferidas (5.46) ---
    dpr = ec2p.relajacion(sigma_pmi, tendon["fpk"], tendon.get("rho1000", 0.025), clase=2)
    ddif = ec2p.perdidas_diferidas(tendon.get("eps_cs", 3.0e-4), tendon["Ep"], dpr, tendon.get("phi", 2.0),
                                   sigma_c_qp, tendon["Ecm"], Ap, A, Ic, zcp)
    sigma_pinf = sigma_pmi - ddif; P_inf = sigma_pinf * Ap
    return {"sigma_p0_Pa": sigma_p0, "P0_N": tendon["P0"],
            "dfric_Pa": dfric, "dwedge_Pa": dwedge, "delastico_Pa": dela,
            "Pmi_N": Pmi, "drelaj_Pa": dpr, "ddiferida_Pa": ddif,
            "sigma_pinf_Pa": sigma_pinf, "P_inf_N": P_inf,
            "perdidas_totales_pct": (1 - P_inf / tendon["P0"]) * 100.0}


def inyectar(model, meta, tendon):
    """Anade el caso 'P' a cada viga con la carga equivalente del tendon (P_inf).
    Devuelve el dict de perdidas (para la memoria y la comprobacion EC2)."""
    L = meta["L"]
    per = calcular_perdidas(tendon, L)
    ce = ec2p.cargas_equivalentes(per["P_inf_N"], L, tendon["e_centro"], tendon.get("e_apoyo", 0.0))
    w_p = ce["w_p_N_m"]                       # N/m hacia arriba
    for bid, b in model["barras"].items():
        if b.get("tipo") == "viga":
            model["cargas"].append({"caso": "P", "barra": bid, "direccion": "GZ", "qz": +w_p})
    per["w_p_N_m"] = w_p; per["cargas_equivalentes"] = ce
    return per
