"""
Combinaciones de acciones segun EN 1990 (EC0) con Anejo Nacional Espana.
Caso Fase 1: una accion permanente G y una variable Q.

Coeficientes parciales (AN ES):
  gamma_G = 1.35 (permanente desfavorable) ; 1.00 (favorable)
  gamma_Q = 1.50 (variable desfavorable)   ; 0.00 (favorable)

Factores de simultaneidad psi (Tabla A1.1, Cat. B - oficinas por defecto):
  psi0 = 0.7 ; psi1 = 0.5 ; psi2 = 0.3
"""

# Coeficientes por defecto (parametrizables por proyecto)
GAMMA_G_SUP = 1.35
GAMMA_G_INF = 1.00
GAMMA_Q_SUP = 1.50

PSI = {"psi0": 0.7, "psi1": 0.5, "psi2": 0.3}  # Cat. B oficinas


def build_combos(casos, psi=PSI):
    """
    Devuelve dict {nombre_combo: {caso: factor}} y metadatos por combo.
    'casos' = lista de nombres de casos presentes (p.ej. ['G','Q']).
    """
    has_G = "G" in casos
    has_Q = "Q" in casos
    combos = {}
    meta = {}

    if has_G and has_Q:
        # --- ELU (STR) ---
        combos["ELU"] = {"G": GAMMA_G_SUP, "Q": GAMMA_Q_SUP}
        meta["ELU"] = {"tipo": "ELU", "expr": "1.35*G + 1.50*Q", "norma": "EC0 6.10"}

        combos["ELU_G"] = {"G": GAMMA_G_SUP}
        meta["ELU_G"] = {"tipo": "ELU", "expr": "1.35*G", "norma": "EC0 6.10"}

        # --- ELS caracteristica (flecha total) ---
        combos["ELS_car"] = {"G": 1.0, "Q": 1.0}
        meta["ELS_car"] = {"tipo": "ELS", "expr": "G + Q", "norma": "EC0 6.14b",
                           "uso": "flecha total"}

        # --- ELS frecuente ---
        combos["ELS_fre"] = {"G": 1.0, "Q": psi["psi1"]}
        meta["ELS_fre"] = {"tipo": "ELS", "expr": f"G + {psi['psi1']}*Q", "norma": "EC0 6.15b"}

        # --- ELS casi-permanente ---
        combos["ELS_cp"] = {"G": 1.0, "Q": psi["psi2"]}
        meta["ELS_cp"] = {"tipo": "ELS", "expr": f"G + {psi['psi2']}*Q", "norma": "EC0 6.16b"}

        # --- ELS activa (proxy: solo variable, flecha activa) ---
        combos["ELS_act"] = {"Q": 1.0}
        meta["ELS_act"] = {"tipo": "ELS", "expr": "Q", "norma": "criterio despacho",
                           "uso": "flecha activa (proxy variable)"}
    elif has_G:
        combos["ELU"] = {"G": GAMMA_G_SUP}
        meta["ELU"] = {"tipo": "ELU", "expr": "1.35*G", "norma": "EC0 6.10"}
        combos["ELS_car"] = {"G": 1.0}
        meta["ELS_car"] = {"tipo": "ELS", "expr": "G", "norma": "EC0 6.14b", "uso": "flecha total"}

    return combos, meta
