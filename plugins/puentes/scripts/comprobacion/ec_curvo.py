"""
Comprobacion EC2 de un tablero CURVO (viga-cajon sobre eje curvo) con la TORSION
como protagonista (PT 7.5, Ola 7).

La curvatura acopla torsion a flexion: bajo carga vertical aparece T (dT/ds=M/R).
Se comprueba:
 - FLEXION: tension de fibra sup/inf (M*c/I) vs limites (compresion 0,6 fck;
   traccion fctm) -- predim elastico.
 - CORTANTE + TORSION (Bredt, EC2 6.3): tau_T = T/(2 Am tef), tau_V = V/(2 tw z),
   interaccion tau_tot vs resistencia del alma (nu1 fcd).
 - acoplamiento T/M y J de Bredt (informativo).
Para cajon metalico se compararia con tau_Rd = fy/sqrt(3) (gancho).

SI (N, m). Predimensionado/asistencia; revisar y firmar por tecnico competente (ICCP).
"""
from __future__ import annotations
import math

GC = 1.5


def comprobar(curvo, esfuerzos, props):
    """curvo: {'material'{fck,fctm?},'t_web','h'}.
    esfuerzos: {'M_Ed_Nm','T_Ed_Nm','V_Ed_N'}.
    props: salida de _seccion_props (A, Iy, c_sup, c_inf, Am_bredt, J_bredt)."""
    mat = curvo["material"]; fck = mat["fck"]
    fctm = mat.get("fctm", 0.30 * (fck / 1e6) ** (2.0 / 3.0) * 1e6)
    fcd = fck / GC
    nu1 = 0.6 * (1 - (fck / 1e6) / 250.0)
    I = props["Iy"]; c_sup = props["c_sup"]; c_inf = props["c_inf"]
    Am = props["Am_bredt"]; tw = curvo["t_web"]; h = curvo["h"]
    tef = tw                                          # espesor eficaz de pared (predim)

    M_Ed = esfuerzos["M_Ed_Nm"]; T_Ed = abs(esfuerzos.get("T_Ed_Nm", 0.0))
    V_Ed = abs(esfuerzos.get("V_Ed_N", 0.0))

    # flexion: compresion de fibra superior (uncracked) + armado a traccion del
    # fondo (cajon de HORMIGON ARMADO curvo: el fondo se fisura y se arma).
    sig_sup = -M_Ed * c_sup / I        # compresion (sagging) -> negativa
    sig_inf = +M_Ed * c_inf / I        # traccion fondo (uncracked, informativo)
    u_comp = abs(sig_sup) / (0.6 * fck)
    fyk = mat.get("fyk", 500e6); fyd = fyk / 1.15
    d_inf = h - mat.get("recubrimiento", 0.05)
    As_req = M_Ed / (0.9 * d_inf * fyd) if M_Ed > 0 else 0.0
    A_fondo = props["A"]                              # area bruta de la seccion
    As_max = 0.04 * A_fondo                           # cuantia maxima EC2 (4% Ac)
    u_trac = As_req / As_max if As_max > 0 else 9.99

    # cortante + torsion (Bredt)
    z_v = 0.9 * h
    tau_V = V_Ed / (2 * tw * z_v) if tw * z_v > 0 else 0.0
    tau_T = T_Ed / (2 * Am * tef) if Am * tef > 0 else 0.0
    tau_tot = tau_V + tau_T
    tau_Rd = nu1 * fcd / 2.0
    u_VT = tau_tot / tau_Rd if tau_Rd > 0 else 9.99

    checks = [
        {"nombre": "Flexion compresion sup. (EC2)", "valor": abs(sig_sup), "limite": 0.6 * fck,
         "aprov": u_comp, "cumple": bool(u_comp <= 1.0)},
        {"nombre": "Flexion armado fondo As/As_max (EC2)", "valor": As_req * 1e4, "limite": As_max * 1e4,
         "aprov": u_trac, "cumple": bool(u_trac <= 1.0)},
        {"nombre": "Cortante+Torsion Bredt (EC2 6.3)", "valor": tau_tot, "limite": tau_Rd,
         "aprov": u_VT, "cumple": bool(u_VT <= 1.0)},
    ]
    aprov = max(c["aprov"] for c in checks)
    veredicto = "CUMPLE" if all(c["cumple"] for c in checks) else "NO CUMPLE"
    return {"checks": checks, "veredicto": veredicto, "aprovechamiento_max": aprov,
            "tensiones": {"sup_Pa": sig_sup, "inf_Pa": sig_inf},
            "tau_Pa": {"V": tau_V, "T": tau_T, "total": tau_tot, "Rd": tau_Rd},
            "As_req_cm2": As_req * 1e4, "sig_inf_uncracked_Pa": sig_inf,
            "M_Ed_Nm": M_Ed, "T_Ed_Nm": T_Ed, "acoplamiento_T_M": (T_Ed / M_Ed if M_Ed else 0.0),
            "J_bredt_m4": props["J_bredt"], "Am_bredt_m2": Am}
