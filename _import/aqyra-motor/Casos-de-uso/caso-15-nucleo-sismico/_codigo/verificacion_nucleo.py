"""
Verificacion sismica del NUCLEO DE PANTALLAS ACOPLADAS (caso 15, EC8/EC2 + AN).
Reutiliza las comprobaciones de pantalla del caso 11 (verificacion_sismo:
cortante de alma, elementos de borde, interaccion N-M, deriva) aplicadas a
CADA pantalla del nucleo, y anade la VERIFICACION DE LA VIGA DE ACOPLAMIENTO
(dintel, DCM, EC8 §5.5.3.5).

NDP [confirmar AN]: amplificacion de cortante DCM, sobrerresistencia de capacidad
del dintel, nu y limite de deriva, regimen de armado diagonal del dintel.
"""
import math
import verificacion_sismo as vs

GC = 1.50; GS = 1.15


def viga_acoplamiento(V_Ed_N, b, h, ln, fck_Pa, fyk_Pa=500e6, gamma_Rd=1.2, cover=0.04):
    """Dintel de acoplamiento (EC8 §5.5.3.5). Si l_n/h < 3 -> armadura DIAGONAL;
    si >= 3 -> armadura convencional (longitudinal+cercos). Comprueba el
    aplastamiento de la biela y dimensiona el armado.

    V_Ed_N: cortante del dintel del analisis (se amplifica por gamma_Rd para
    diseno por capacidad)."""
    fcd = fck_Pa / GC; fyd = fyk_Pa / GS; fck = fck_Pa / 1e6
    V_Ed = gamma_Rd * V_Ed_N
    d = h - cover
    z = 0.9 * d
    nu1 = 0.6 * (1.0 - fck / 250.0)
    V_Rd_max = nu1 * fcd * b * z                       # biela 45 (cot+tan=2)
    lh = ln / h
    diagonal = lh < 3.0
    if diagonal:
        # armadura diagonal: V_Ed = 2*As_d*fyd*sin(alpha)
        alpha = math.atan((h - 2.0 * cover) / ln)       # inclinacion de la diagonal
        As_d = V_Ed / (2.0 * fyd * math.sin(alpha))      # m2 por diagonal
        armado = ("armadura DIAGONAL (EC8 §5.5.3.5(3)); As_diag=%.1f cm2/grupo, "
                  "alpha=%.0f deg" % (As_d * 1e4, math.degrees(alpha)))
        As_report_cm2 = As_d * 1e4; alpha_deg = math.degrees(alpha)
    else:
        # convencional: cercos Asw/s = V_Ed/(z*fyd)
        Asw_s = V_Ed / (z * fyd) * 1e4                   # cm2/m
        armado = "armadura CONVENCIONAL (EC8 §5.5.3.5(2)); Asw/s=%.1f cm2/m" % Asw_s
        As_report_cm2 = Asw_s; alpha_deg = 0.0
    aprov = V_Ed / V_Rd_max if V_Rd_max > 0 else 99.0
    return {
        "V_Ed_analisis_kN": float(V_Ed_N / 1e3), "gamma_Rd": gamma_Rd,
        "V_Ed_diseno_kN": float(V_Ed / 1e3),
        "b_m": b, "h_m": h, "ln_m": ln, "l_n_sobre_h": float(lh),
        "regimen": "diagonal" if diagonal else "convencional",
        "V_Rd_max_kN": float(V_Rd_max / 1e3), "aprov_biela": float(aprov),
        "armado": armado, "As_cm2": float(As_report_cm2), "alpha_deg": float(alpha_deg),
        "ok": bool(aprov <= 1.0),
        "ref": "EC8 §5.5.3.5 (vigas de acoplamiento DCM) + EC2 §6.2 [confirmar AN gamma_Rd]",
    }


def pantalla_check(pan, V_Ed_N, M_Ed_Nm, N_Ed_N, fck_Pa, eps_amplif=1.5,
                   rho_v_alma=0.0025, N_nm_N=None):
    """Comprobacion de una pantalla del nucleo (reusa verificacion_sismo).
    N_Ed_N: axil real (puede ser de TRACCION neta en el machon a barlovento por
    el acoplamiento) -> gobierna la armadura de borde. N_nm_N: axil para la
    frontera N-M (gravitatorio si hay traccion neta; por defecto = N_Ed_N)."""
    Lw = pan["Lw_m"]; tw = pan["tw_m"]
    if N_nm_N is None:
        N_nm_N = N_Ed_N
    N_nm_N = max(N_nm_N, 0.0)
    cort = vs.cortante_alma(V_Ed_N, Lw, tw, fck_Pa, eps_amplif=eps_amplif)
    borde = vs.elemento_borde(N_Ed_N, M_Ed_Nm, Lw, tw, fck_Pa)
    nm = vs.interaccion_NM(N_nm_N, M_Ed_Nm, Lw, tw, fck_Pa,
                           As_borde_m2=borde["As_borde_diseno_cm2"] / 1e4,
                           rho_v_alma=rho_v_alma)
    aprovs = {"cortante_alma": cort["aprov_biela"], "compr_borde": borde["aprov_compr_borde"],
              "flexocompresion_NM": nm["aprov_flexocompresion"]}
    ok = cort["ok"] and borde["ok_compr"] and nm["ok"]
    return {"nombre": pan["nombre"], "rol": pan["rol"], "resiste": pan["resiste"],
            "Lw_m": Lw, "tw_m": tw, "N_Ed_kN": N_Ed_N / 1e3, "N_NM_kN": N_nm_N / 1e3,
            "traccion_neta": bool(N_Ed_N < 0), "M_Ed_kNm": M_Ed_Nm / 1e3,
            "V_Ed_kN": V_Ed_N / 1e3, "cortante_alma": cort, "elemento_borde": borde,
            "interaccion_NM": nm, "aprovechamientos": aprovs,
            "aprov_max": max(aprovs.values()), "veredicto": "CUMPLE" if ok else "REVISAR"}


def verificar(model, esfuerzos_pantalla, coupling, deriva_res, eps_amplif=1.5,
              nu_dr=0.5, limite_dr=0.0075):
    """esfuerzos_pantalla: lista de dicts {pan, V_Ed_N, M_Ed_Nm, N_Ed_N}.
    coupling: dict de nucleo.acoplados (o None). deriva_res: dict de
    nucleo.derivas_globales (gobernante)."""
    fck = model["material"]["fck_Pa"] or 30e6
    pantallas_ver = []
    for e in esfuerzos_pantalla:
        pantallas_ver.append(pantalla_check(e["pan"], e["V_Ed_N"], e["M_Ed_Nm"],
                                            e["N_Ed_N"], fck, eps_amplif=eps_amplif,
                                            N_nm_N=e.get("N_nm_N")))
    dintel = None
    if coupling is not None:
        d = model["dinteles"]
        dintel = viga_acoplamiento(coupling["V_lintel_max_kN"] * 1e3, d["b_m"], d["h_m"],
                                   d["ln_m"], fck)
    der = vs.deriva(deriva_res, nu=nu_dr, limite_rel=limite_dr)
    aprovs = {}
    for p in pantallas_ver:
        aprovs["pantalla_%s" % p["nombre"]] = p["aprov_max"]
    if dintel is not None:
        aprovs["viga_acoplamiento"] = dintel["aprov_biela"]
    aprovs["deriva"] = der["aprov_max"]
    ok = (all(p["veredicto"] == "CUMPLE" for p in pantallas_ver)
          and (dintel is None or dintel["ok"]) and der["ok"])
    return {"pantallas": pantallas_ver, "viga_acoplamiento": dintel, "deriva": der,
            "aprovechamientos": aprovs, "aprov_max": max(aprovs.values()),
            "veredicto": "CUMPLE" if ok else "NO CUMPLE (predimensionar)"}
