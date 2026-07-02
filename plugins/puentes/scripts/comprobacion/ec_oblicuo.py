"""
Comprobacion EC2 (losa) o EC3 (metalico) de un tablero OBLICUO (PT 7.5, Ola 7).

Para losa de hormigon: flexion por unidad de ancho en la franja central (Mx, My
del FEM por lamina), armado a flexion EC2 (recubrimiento, canto util, As, cuantia
minima, M_Rd con bloque rectangular), y se REPORTA el efecto de esviaje: factor de
concentracion de la REACCION en la esquina OBTUSA y el reparto transversal.
Para tablero metalico: flexion de placa vs M_c,Rd elastico (EC3).

SI (N, m). Predimensionado/asistencia; revisar y firmar por tecnico competente (ICCP).
"""
from __future__ import annotations
import math

GC = 1.5; GS = 1.15


def armado_flexion_losa(M_Ed, t, fck, fyk, rec=0.035, phi_arm=0.020, ancho=1.0):
    """Armado a flexion de losa por metro (EC2 §6.1, bloque rectangular). M_Ed en
    Nm/m. Devuelve As, cuantia, M_Rd con el As dispuesto (predim, lever 0.9d)."""
    fcd = fck / GC; fyd = fyk / GS
    d = t - rec - phi_arm / 2.0
    z = 0.9 * d
    As = M_Ed / (z * fyd) if M_Ed > 0 else 0.0
    fctm = 0.30 * (fck / 1e6) ** (2.0 / 3.0) * 1e6 if fck <= 50e6 else 2.12e6 * math.log(1 + (fck / 1e6 + 8) / 10)
    As_min = max(0.26 * fctm / fyk, 0.0013) * ancho * d
    As_prov = max(As, As_min)
    x = As_prov * fyd / (0.8 * fcd * ancho)
    z_real = d - 0.4 * x
    M_Rd = As_prov * fyd * z_real
    return {"d_m": d, "As_req_cm2_m": As * 1e4, "As_min_cm2_m": As_min * 1e4,
            "As_prov_cm2_m": As_prov * 1e4, "x_m": x, "z_m": z_real,
            "M_Rd_Nm_m": M_Rd, "M_Ed_Nm_m": M_Ed, "u": M_Ed / M_Rd if M_Rd > 0 else 9.99}


def comprobar(obl, esfuerzos, reacciones):
    """obl: {'material'{fck,fyk} (losa) o {'fy','Wel'} (metalico),'t','tipo'?}.
    esfuerzos: {'Mx_max_Nm_m','My_max_Nm_m','factor_reparto'}.
    reacciones: salida de reacciones_esquinas (concentracion obtusa)."""
    mat = obl["material"]; t = obl["t"]
    metalico = ("fy" in mat and "fck" not in mat)
    checks = []
    detalle = {}
    if metalico:
        fy = mat["fy"]; Wel = mat.get("Wel", t ** 2 / 6.0)   # por metro si placa
        Mc_Rd = Wel * fy / 1.0
        for comp, lab in (("Mx_max_Nm_m", "long"), ("My_max_Nm_m", "transv")):
            M = esfuerzos.get(comp, 0.0); u = M / Mc_Rd if Mc_Rd > 0 else 9.99
            checks.append({"nombre": "Flexion placa %s (EC3)" % lab, "valor": M,
                           "limite": Mc_Rd, "aprov": u, "cumple": bool(u <= 1.0)})
        detalle["Mc_Rd_Nm_m"] = Mc_Rd
    else:
        fck = mat["fck"]; fyk = mat["fyk"]
        ar_x = armado_flexion_losa(esfuerzos.get("Mx_max_Nm_m", 0.0), t, fck, fyk,
                                   rec=obl.get("recubrimiento", 0.035))
        ar_y = armado_flexion_losa(esfuerzos.get("My_max_Nm_m", 0.0), t, fck, fyk,
                                   rec=obl.get("recubrimiento", 0.035))
        checks.append({"nombre": "Flexion losa long. M_Rd (EC2)", "valor": ar_x["M_Ed_Nm_m"],
                       "limite": ar_x["M_Rd_Nm_m"], "aprov": ar_x["u"], "cumple": bool(ar_x["u"] <= 1.0)})
        checks.append({"nombre": "Flexion losa transv. M_Rd (EC2)", "valor": ar_y["M_Ed_Nm_m"],
                       "limite": ar_y["M_Rd_Nm_m"], "aprov": ar_y["u"], "cumple": bool(ar_y["u"] <= 1.0)})
        detalle["armado_long"] = ar_x; detalle["armado_transv"] = ar_y

    # efecto de esviaje: informativo + aviso si concentracion obtusa alta
    conc = reacciones.get("concentracion_obtusa", 0.0)
    detalle["concentracion_obtusa"] = conc
    detalle["factor_reparto_transversal"] = esfuerzos.get("factor_reparto", 1.0)
    aviso_esviaje = conc > 1.5
    detalle["aviso_esquina_obtusa"] = bool(aviso_esviaje)

    aprov = max(c["aprov"] for c in checks)
    veredicto = "CUMPLE" if all(c["cumple"] for c in checks) else "NO CUMPLE"
    return {"checks": checks, "veredicto": veredicto, "aprovechamiento_max": aprov,
            "detalle": detalle, "esviaje": True}
