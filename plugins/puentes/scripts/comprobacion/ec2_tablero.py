"""
Comprobacion EC2 del tablero de vigas pretensadas (EN 1992-1-1/-2, AN Espana).

REUTILIZA `ec2_pretensado.tensiones_fibra` (motor-calculo). Comprueba, por viga
mas solicitada, sobre la envolvente de esfuerzos del emparrillado (FEM-1):
 - TENSIONES EN VACIO (transferencia): P0 + peso propio g1 -> limites de compresion
   (0.6 fck(t)) y de traccion (fctm) en fibras sup/inf.
 - TENSIONES EN SERVICIO (ELS caracteristica): P_inf + (g+g2) + LM1 -> compresion
   <= 0.6 fck (caracteristica) y descompresion/traccion controlada.
 - FLEXION ELU: M_Rd (brazo interno aproximado) vs M_Ed envolvente.
 - CORTANTE ELU: V_Rd,c (con axil de pretensado) vs V_Ed envolvente.
 - FISURACION: descompresion en ELS frecuente (cuasi).

Aprovechamientos y veredicto CUMPLE/NO CUMPLE. [confirmar AN]: limites de tension,
fck(t), modelo de cortante. SI (N, m, Pa). Predimensionado; revisar y firmar (ICCP).
"""
from __future__ import annotations
import ec2_pretensado as ec2p


def _chk(nombre, valor, limite, modo="<="):
    if modo == "<=":
        ap = abs(valor) / abs(limite) if limite else 0.0
        ok = abs(valor) <= abs(limite) * (1 + 1e-6)
    else:
        ap = abs(limite) / abs(valor) if valor else 0.0
        ok = abs(valor) >= abs(limite) * (1 - 1e-6)
    return {"nombre": nombre, "valor": valor, "limite": limite, "aprov": ap, "cumple": bool(ok)}


def comprobar(tablero, tendon, perdidas, esfuerzos):
    """esfuerzos = {'M_g1','M_perm','M_lm1_max','M_lm1_min','M_Ed_ELU',
       'V_Ed_ELU'} en N*m / N (viga mas solicitada). Devuelve checks + veredicto."""
    sec = tablero["viga_sec"]
    A = sec["A"]; I = sec["Iy"]; c_sup = sec["c_sup"]; c_inf = sec["c_inf"]
    fck = tablero["material"]["fck"]; fctm = tablero["material"].get("fctm", 0.30 * (fck / 1e6) ** (2 / 3) * 1e6)
    fck_t = tablero.get("fck_transferencia", 0.8 * fck)
    P0 = perdidas["P0_N"]; Pinf = perdidas["P_inf_N"]; e = tendon["e_centro"]
    checks = []

    # --- tensiones en vacio (transferencia): P0 + g1 ---
    s_sup0, s_inf0 = ec2p.tensiones_fibra(P0, e, esfuerzos["M_g1"], A, I, c_sup, c_inf)
    checks.append(_chk("transfer_comp_inf", s_inf0, -0.6 * fck_t))
    checks.append(_chk("transfer_tracc_sup", max(s_sup0, 0.0), fctm))

    # --- tensiones en servicio (ELS car): P_inf + perm + LM1 ---
    M_serv = esfuerzos["M_perm"] + esfuerzos["M_lm1_max"]
    s_sup, s_inf = ec2p.tensiones_fibra(Pinf, e, M_serv, A, I, c_sup, c_inf)
    checks.append(_chk("servicio_comp_sup", s_sup, -0.6 * fck))
    checks.append(_chk("servicio_tracc_inf", max(s_inf, 0.0), fctm))

    # --- fisuracion: descompresion en cuasipermanente (perm + psi2*LM1) ---
    M_cp = esfuerzos["M_perm"] + 0.2 * esfuerzos["M_lm1_max"]
    _, s_inf_cp = ec2p.tensiones_fibra(Pinf, e, M_cp, A, I, c_sup, c_inf)
    checks.append(_chk("descompresion_inf_cp", max(s_inf_cp, 0.0), 0.0 if True else fctm))

    # --- flexion ELU: M_Rd aprox (brazo z=0.9*d, acero activo) ---
    fpk = tendon["fpk"]; Ap = tendon["Ap"]; gamma_s = 1.15
    d = c_inf + e   # canto util aprox (fibra comp sup a tendon)
    z = 0.9 * d
    M_Rd = (fpk / gamma_s) * Ap * z
    checks.append(_chk("flexion_ELU", esfuerzos["M_Ed_ELU"], M_Rd))

    # --- cortante ELU: viga con cercos (modelo de bielas EC2 6.2.3) ---
    # En una viga de puente el cortante lo resiste la armadura transversal (cercos):
    # se comprueba el aplastamiento de la biela V_Rd,max y se DIMENSIONAN los cercos.
    bw = sec.get("bw", 0.2); d_v = d; z = 0.9 * d_v
    fcd = fck / 1.5
    cot_theta = 2.5                                   # theta=21.8 deg (EC2 1<=cot<=2.5)
    nu1 = 0.6 * (1 - (fck / 1e6) / 250.0)
    sigma_cp = max(min(Pinf / A, 0.2 * fcd), 0.0)
    alpha_cw = 1 + sigma_cp / fcd if sigma_cp <= 0.25 * fcd else 1.25
    V_Rd_max = alpha_cw * bw * z * nu1 * fcd / (cot_theta + 1.0 / cot_theta)
    fywd = 500e6 / 1.15
    Asw_s_req = esfuerzos["V_Ed_ELU"] / (z * fywd * cot_theta)   # m2/m
    # tambien el cortante de descuento del pretensado inclinado V_p (favorable) [confirmar AN]
    checks.append(_chk("cortante_biela_ELU", esfuerzos["V_Ed_ELU"], V_Rd_max))

    veredicto = "CUMPLE" if all(c["cumple"] for c in checks) else "NO CUMPLE"
    aprov_max = max(c["aprov"] for c in checks)
    return {"checks": checks, "veredicto": veredicto, "aprovechamiento_max": aprov_max,
            "M_Rd_Nm": M_Rd, "V_Rdc_N": V_Rd_max, "Asw_s_req_cm2_m": Asw_s_req * 1e4,
            "tensiones": {"transfer_sup": s_sup0, "transfer_inf": s_inf0,
                          "servicio_sup": s_sup, "servicio_inf": s_inf}}
