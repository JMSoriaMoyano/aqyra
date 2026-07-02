"""
Comprobacion EC3 de una CELOSIA de acero (EN 1993-1-1, AN Espana).

Por barra, sobre la envolvente del AXIL (motor-fem):
 - TRACCION: N_t,Rd = A*fy/gM0.
 - COMPRESION: PANDEO por flexion N_b,Rd = chi*A*fy/gM1 (curva b, alpha=0.34),
   longitud de pandeo Lcr = longitud de la barra (extremos articulados), inercia
   minima de la seccion. Lambda_bar = sqrt(A*fy/N_cr), N_cr = pi^2 E Imin / Lcr^2.
 - UNIONES (simplificado): la union se dimensiona para el axil de la barra; se
   comprueba N_Ed <= N_u (resistencia de union dada o, por defecto, capacidad de la
   barra -> union de resistencia completa). [confirmar AN]
 - FATIGA (EN 1993-1-9): GANCHO DIFERIDO a un PT de fatiga (LM3 + categorias de
   detalle + dano Palmgren-Miner). Aqui NO se calcula; se reporta como pendiente.

[confirmar AN]: gM0=1.0, gM1=1.0 (AN-ES), curva de pandeo, Lcr, resistencia de union.
SI (N, m, Pa). Predimensionado/asistencia; revisar y firmar por tecnico (ICCP).
"""
from __future__ import annotations
import math

GM0 = 1.0; GM1 = 1.0


def chi_pandeo(lam_bar, alpha=0.34):
    """Coeficiente de reduccion por pandeo (curva b por defecto, EC3 6.3.1.2)."""
    phi = 0.5 * (1 + alpha * (lam_bar - 0.2) + lam_bar ** 2)
    chi = 1.0 / (phi + math.sqrt(max(phi ** 2 - lam_bar ** 2, 0.0))) if phi > 0 else 1.0
    return min(chi, 1.0)


def comprobar_barra(m):
    """m = {'nombre','N_Ed','A','Imin','L','E','fy','curva'?,'N_u'?}. N_Ed>0 traccion,
    <0 compresion. Devuelve dict con N_Rd, modo, aprov, cumple."""
    A = m['A']; fy = m['fy']; E = m['E']; L = m['L']; Imin = m['Imin']; N_Ed = m['N_Ed']
    alpha = {"a0": 0.13, "a": 0.21, "b": 0.34, "c": 0.49, "d": 0.76}.get(m.get('curva', 'b'), 0.34)
    if N_Ed >= 0:
        N_Rd = A * fy / GM0; modo = "traccion"; lam_bar = 0.0; chi = 1.0
    else:
        N_cr = math.pi ** 2 * E * Imin / L ** 2 if L > 0 else 1e30
        lam_bar = math.sqrt(A * fy / N_cr) if N_cr > 0 else 9.99
        chi = chi_pandeo(lam_bar, alpha)
        N_Rd = chi * A * fy / GM1; modo = "compresion_pandeo"
    aprov = abs(N_Ed) / N_Rd if N_Rd else 9.99
    res = {"nombre": m['nombre'], "N_Ed_N": N_Ed, "N_Rd_N": N_Rd, "modo": modo,
           "lambda_bar": lam_bar, "chi": chi, "aprov": aprov,
           "cumple": bool(abs(N_Ed) <= N_Rd * (1 + 1e-6))}
    # union (simplificado): resistencia completa si no se da N_u
    N_u = m.get('N_u', N_Rd)
    res["union_aprov"] = abs(N_Ed) / N_u if N_u else 9.99
    res["union_cumple"] = bool(abs(N_Ed) <= N_u * (1 + 1e-6))
    return res


def comprobar(c, miembros):
    """miembros: lista de dicts (ver comprobar_barra). Devuelve resumen + critico."""
    chks = [comprobar_barra(m) for m in miembros]
    for ch in chks:
        ch["veredicto"] = "CUMPLE" if (ch["cumple"] and ch["union_cumple"]) else "NO CUMPLE"
    crit = max(chks, key=lambda x: max(x["aprov"], x["union_aprov"]))
    veredicto = "CUMPLE" if all(x["veredicto"] == "CUMPLE" for x in chks) else "NO CUMPLE"
    aprov_max = max(max(x["aprov"], x["union_aprov"]) for x in chks)
    return {"barras": chks, "barra_critica": crit, "veredicto": veredicto,
            "aprovechamiento_max": aprov_max,
            "fatiga_nota": "EN 1993-1-9: gancho diferido (LM3 + categorias de detalle + Palmgren-Miner)."}
