"""
Modelo de BIELAS Y TIRANTES (EN 1992-1-1 §6.5) — región D.
Caso base: ENCEPADO DE 2 PILOTES bajo pilar centrado.

La celosía (2 bielas a compresión + 1 tirante a tracción) se resuelve con el
SOLVER DE BARRAS (PyNite, celosía articulada), y se contrasta con la estática
cerrada. Después se comprueban según EC2 §6.5:
  - Tirante: As = T / fyd
  - Bielas: sigma_c <= sigma_Rd,max,biela = 0.6 * nu' * fcd   (con tracción transversal)
  - Nudos:  CCC (bajo pilar) <= nu'*fcd ;  CCT (sobre pilote) <= 0.85*nu'*fcd
SI (N, m, Pa).
"""
import math
from Pynite import FEModel3D

GC, GS = 1.50, 1.15
FYK = 500e6
FYD = FYK / GS


def fuerzas_celosia(N_Ed, a, z):
    """Resuelve la celosía del encepado de 2 pilotes con el solver de barras.
    a: separacion entre pilotes (m) ; z: brazo mecanico (m) ; N_Ed centrado (N)."""
    m = FEModel3D()
    # material/seccion ficticios (celosia: solo importan los axiles)
    m.add_material("m", 30e9, 12e9, 0.2, 0)
    m.add_section("s", 0.1, 1e-3, 1e-3, 1e-3)
    m.add_node("T", 0.0, 0.0, z)          # nudo superior (bajo pilar)
    m.add_node("P1", -a / 2, 0.0, 0.0)    # pilote 1
    m.add_node("P2", a / 2, 0.0, 0.0)     # pilote 2
    for n in ("T", "P1", "P2"):
        m.def_support(n, False, True, False, True, True, True)  # plano XZ
    m.def_support("P1", True, True, True, True, True, True)
    m.def_support("P2", False, True, True, True, True, True)
    for nm, i, j in [("S1", "T", "P1"), ("S2", "T", "P2"), ("TIE", "P1", "P2")]:
        m.add_member(nm, i, j, "m", "s")
        m.def_releases(nm, Ryi=True, Rzi=True, Ryj=True, Rzj=True)  # celosia
    m.add_node_load("T", "FZ", -N_Ed, case="C")
    m.add_load_combo("c", {"C": 1.0})
    m.analyze_linear(check_stability=False)
    axial = {nm: m.members[nm].axial(0.0, "c") for nm in ("S1", "S2", "TIE")}
    # cerrado: R=N/2 ; theta=atan(z/(a/2)) ; T=R/tan ; C=R/sin
    R = N_Ed / 2
    th = math.atan(z / (a / 2))
    T_cf = R / math.tan(th)
    C_cf = R / math.sin(th)
    return axial, {"theta_deg": math.degrees(th), "T_cerrado_kN": T_cf / 1e3,
                   "C_cerrado_kN": C_cf / 1e3, "R_pilote_kN": R / 1e3}


def verificar_encepado(N_Ed, a, h, b, fck, c_col, d_pilote, cover=0.05, phi=0.020):
    """Comprobacion EC2 §6.5 del encepado de 2 pilotes."""
    d = h - cover - phi
    z = 0.9 * d
    axial, cf = fuerzas_celosia(N_Ed, a, z)
    th = math.radians(cf["theta_deg"])
    T = float(abs(axial["TIE"])); C = float(max(abs(axial["S1"]), abs(axial["S2"])))
    R = N_Ed / 2

    fcd = fck / GC
    nu_p = 1 - fck / 1e6 / 250
    sRd_strut = 0.6 * nu_p * fcd
    sRd_CCC = 1.0 * nu_p * fcd
    sRd_CCT = 0.85 * nu_p * fcd

    # tirante
    As_req = T / FYD
    # biela: ancho en el nudo inferior (sobre pilote) w = lp*sin + u*cos
    u = 2 * (cover + phi / 2)                 # canto del tirante (anclaje)
    w_strut = d_pilote * math.sin(th) + u * math.cos(th)
    sigma_strut = C / (b * w_strut)
    # nudo CCC bajo pilar (apoyo del pilar)
    sigma_CCC = N_Ed / (c_col * c_col)
    # nudo CCT sobre pilote (apoyo del pilote, area ~ pilote cuadrado equiv)
    A_pile = math.pi * (d_pilote / 2) ** 2
    sigma_CCT = R / A_pile

    return {
        "geom": {"d_mm": d * 1e3, "z_mm": z * 1e3, "theta_deg": cf["theta_deg"]},
        "celosia": {"T_kN": T / 1e3, "C_kN": C / 1e3, "R_pilote_kN": R / 1e3,
                    "T_cerrado_kN": cf["T_cerrado_kN"], "C_cerrado_kN": cf["C_cerrado_kN"],
                    "err_pct": abs(T - cf["T_cerrado_kN"] * 1e3) / (cf["T_cerrado_kN"] * 1e3) * 100},
        "tirante": {"T_kN": T / 1e3, "As_req_cm2": As_req * 1e4,
                    "fyd_MPa": FYD / 1e6},
        "biela": {"sigma_MPa": sigma_strut / 1e6, "sRd_MPa": sRd_strut / 1e6,
                  "w_mm": w_strut * 1e3, "u": float(sigma_strut / sRd_strut), "ok": bool(sigma_strut <= sRd_strut)},
        "nudo_CCC": {"sigma_MPa": sigma_CCC / 1e6, "sRd_MPa": sRd_CCC / 1e6,
                     "u": float(sigma_CCC / sRd_CCC), "ok": bool(sigma_CCC <= sRd_CCC)},
        "nudo_CCT": {"sigma_MPa": sigma_CCT / 1e6, "sRd_MPa": sRd_CCT / 1e6,
                     "u": float(sigma_CCT / sRd_CCT), "ok": bool(sigma_CCT <= sRd_CCT)},
    }


if __name__ == "__main__":
    import json
    r = verificar_encepado(N_Ed=2000e3, a=1.8, h=0.9, b=0.9, fck=30e6,
                           c_col=0.40, d_pilote=0.45)
    print(json.dumps({k: ({kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items()}
                          if isinstance(v, dict) else v) for k, v in r.items()},
                     indent=1, ensure_ascii=False))
