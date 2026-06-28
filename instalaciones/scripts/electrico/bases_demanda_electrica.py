"""
BASES DE DEMANDA -- ELECTRICAS / BAJA TENSION (REBT). Disciplina `instalaciones`,
PT 4.5 (Ola 4). Segundo vertical, analogo a `pci/bases_demanda.py`.

Rellena la clave `demanda` del MODELO NEUTRO DE RED (emitido por el parser MEP de
iso19650-openbim, PT 4.2, sistema ELECTRICAL) con las bases de demanda ELECTRICA:
potencia, factor de potencia (cosphi) y nº de fases (mono/tri) por terminal, y la
tension nominal + simultaneidad + grado de electrificacion por sistema. Es el "slot"
CN-3 de la disciplina (analogo a las acciones EC0/EC1 en estructuras; aqui POTENCIAS).

El NUCLEO da la topologia (iso19650); este modulo aporta la DEMANDA; el solver
(electrico/solver_electrico) CALCULA intensidades, caidas de tension y secciones.
Frontera C1 (lectura, iso19650) <-> CN-3 (demanda) <-> calculo (instalaciones).

Dos modos (dispatcher `aplicar_demanda_electrica`):
  - VIVIENDA (ITC-BT-25): circuitos C1..C12, electrificacion basica/elevada. Cada
    terminal se mapea a un circuito por su `tipo`/`id` (C1, C2, ...).
  - RECEPTORES (terciario/industrial): catalogo por tipo de receptor (luminaria,
    toma, motor...) con cosphi y fases; previsiones por defecto ITC-BT-10/44/47.

Normas (NDP, todos [confirmar AN] -- criterio del despacho):
  REBT RD 842/2002 | ITC-BT-10 (prevision de cargas) | ITC-BT-25 (viviendas:
  circuitos y electrificacion) | ITC-BT-19 (caidas de tension admisibles, secciones)
  | ITC-BT-44 (receptores de alumbrado) | ITC-BT-47 (motores).
  El DATO DEL PROYECTO (IFC: potencia/cosphi por terminal) PREVALECE sobre el valor
  por defecto (clave `potencia_W`/`cosphi` del terminal o Pset propio).

NO calcula intensidades ni secciones (eso es el solver). Devuelve el modelo con
`demanda` rellena. Predimensionado/asistencia; revisar y firmar por tecnico competente.
"""
import copy
import json

# --- tensiones nominales (V) y limites de caida de tension [confirmar AN] -----
U_MONO = 230.0    # tension fase-neutro (monofasico)
U_TRI = 400.0     # tension fase-fase  (trifasico)

# Caida de tension maxima admisible (%) en instalaciones interiores (ITC-BT-19):
# 3 % para alumbrado, 5 % para los demas usos (fuerza/tomas). En suministros con
# contador unico se cuenta desde el origen; con DI/LGA, la reparte el reglamento.
DU_MAX_ALUMBRADO_PCT = 3.0
DU_MAX_FUERZA_PCT = 5.0

_SISTEMAS_ELEC = {"ELECTRICAL", "POWER", "LIGHTING"}

# ============================================================================
# MODO VIVIENDA -- circuitos ITC-BT-25
# ============================================================================
# Por circuito: uso (alumbrado/fuerza -> limite ΔU), potencia prevista (W) de la
# instalacion, factor de utilizacion Fu, factor de simultaneidad Fs, seccion minima
# normativa (mm2), fases. La POTENCIA DE CALCULO del circuito = P_prevista*Fu*Fs.
# Valores de la tabla 1 de la ITC-BT-25 (electrificacion elevada) [confirmar AN].
_CIRCUITOS_BT25 = {
    "C1":  {"uso": "alumbrado", "desc": "Iluminacion",              "p_prevista_W": 4140.0,  "Fu": 0.75, "Fs": 0.50, "seccion_min_mm2": 1.5, "fases": "mono"},
    "C2":  {"uso": "fuerza",    "desc": "Tomas de uso general",     "p_prevista_W": 7360.0,  "Fu": 0.20, "Fs": 0.25, "seccion_min_mm2": 2.5, "fases": "mono"},
    "C3":  {"uso": "fuerza",    "desc": "Cocina y horno",           "p_prevista_W": 5400.0,  "Fu": 0.50, "Fs": 0.75, "seccion_min_mm2": 6.0, "fases": "mono"},
    "C4":  {"uso": "fuerza",    "desc": "Lavadora, lavavajillas, termo", "p_prevista_W": 3450.0, "Fu": 0.66, "Fs": 0.75, "seccion_min_mm2": 4.0, "fases": "mono"},
    "C5":  {"uso": "fuerza",    "desc": "Tomas banos y cocina",     "p_prevista_W": 3450.0,  "Fu": 0.40, "Fs": 0.50, "seccion_min_mm2": 2.5, "fases": "mono"},
    "C6":  {"uso": "alumbrado", "desc": "Iluminacion (adicional)",  "p_prevista_W": 4140.0,  "Fu": 0.75, "Fs": 0.50, "seccion_min_mm2": 1.5, "fases": "mono"},
    "C7":  {"uso": "fuerza",    "desc": "Tomas uso general (adic.)", "p_prevista_W": 7360.0, "Fu": 0.20, "Fs": 0.25, "seccion_min_mm2": 2.5, "fases": "mono"},
    "C8":  {"uso": "fuerza",    "desc": "Calefaccion",              "p_prevista_W": 5750.0,  "Fu": 1.00, "Fs": 1.00, "seccion_min_mm2": 6.0, "fases": "mono"},
    "C9":  {"uso": "fuerza",    "desc": "Aire acondicionado",       "p_prevista_W": 5750.0,  "Fu": 1.00, "Fs": 1.00, "seccion_min_mm2": 6.0, "fases": "mono"},
    "C10": {"uso": "fuerza",    "desc": "Secadora",                 "p_prevista_W": 3450.0,  "Fu": 1.00, "Fs": 1.00, "seccion_min_mm2": 2.5, "fases": "mono"},
    "C11": {"uso": "fuerza",    "desc": "Automatizacion/gestion",   "p_prevista_W": 2300.0,  "Fu": 0.66, "Fs": 0.50, "seccion_min_mm2": 1.5, "fases": "mono"},
    "C12": {"uso": "fuerza",    "desc": "Circuito adicional",       "p_prevista_W": 3450.0,  "Fu": 0.50, "Fs": 0.50, "seccion_min_mm2": 2.5, "fases": "mono"},
}

# Grado de electrificacion (ITC-BT-10): potencia minima prevista por vivienda (W).
_ELECTRIFICACION = {
    "basica":  {"p_min_W": 5750.0, "circuitos": ["C1", "C2", "C3", "C4", "C5"]},
    "elevada": {"p_min_W": 9200.0, "circuitos": ["C1", "C2", "C3", "C4", "C5",
                                                 "C8", "C9", "C10", "C11", "C12"]},
}
_GRADO_DEF = "elevada"
_CRITERIO_BT25 = ("REBT RD 842/2002; ITC-BT-25 (circuitos y electrificacion de "
                  "viviendas); ITC-BT-10 (prevision de cargas); ITC-BT-19 (caidas "
                  "de tension) [confirmar AN]")

# ============================================================================
# MODO RECEPTORES -- terciario / industrial (catalogo por tipo)
# ============================================================================
# Por tipo de receptor: potencia (W), cosphi, fases, uso (alumbrado/fuerza). Para
# motores, ITC-BT-47 manda dimensionar la linea al 125 % del de mayor potencia.
_RECEPTORES = {
    "LUMINARIA":  {"potencia_W": 58.0,   "cosphi": 0.90, "fases": "mono", "uso": "alumbrado"},
    "ALUMBRADO":  {"potencia_W": 58.0,   "cosphi": 0.90, "fases": "mono", "uso": "alumbrado"},
    "LAMP":       {"potencia_W": 58.0,   "cosphi": 0.90, "fases": "mono", "uso": "alumbrado"},
    "LIGHTFIXTURE": {"potencia_W": 58.0, "cosphi": 0.90, "fases": "mono", "uso": "alumbrado"},
    "TOMA":       {"potencia_W": 3680.0, "cosphi": 0.95, "fases": "mono", "uso": "fuerza"},
    "OUTLET":     {"potencia_W": 3680.0, "cosphi": 0.95, "fases": "mono", "uso": "fuerza"},
    "ENCHUFE":    {"potencia_W": 3680.0, "cosphi": 0.95, "fases": "mono", "uso": "fuerza"},
    "MOTOR":      {"potencia_W": 7500.0, "cosphi": 0.85, "fases": "tri",  "uso": "fuerza"},
    "CLIMA":      {"potencia_W": 5000.0, "cosphi": 0.90, "fases": "tri",  "uso": "fuerza"},
}
_RECEPTOR_DEF = "TOMA"
_CRITERIO_REC = ("REBT RD 842/2002; ITC-BT-10 (prevision de cargas); ITC-BT-44 "
                 "(alumbrado); ITC-BT-47 (motores); ITC-BT-19 (caidas de tension) "
                 "[confirmar AN]")


def _du_max(uso):
    return DU_MAX_ALUMBRADO_PCT if uso == "alumbrado" else DU_MAX_FUERZA_PCT


def _tension(fases):
    return U_TRI if str(fases).lower().startswith("tri") else U_MONO


# --- clasificadores ---------------------------------------------------------
def _circuito_de(term):
    """Deduce el circuito ITC-BT-25 (C1..C12) del terminal por su `tipo`/`id`.
    Acepta `C3`, `circuito C3`, `ROC...` no aplica. Def. None (no es vivienda)."""
    txt = ("%s %s" % (term.get("tipo") or "", term.get("id") or "")).upper()
    for c in _CIRCUITOS_BT25:
        # busca el token de circuito aislado (C3) evitando que C1 case con C12
        for tok in txt.replace("-", " ").replace("_", " ").split():
            if tok == c:
                return c
    return None


def _receptor_de(term):
    """Deduce el tipo de receptor del terminal por su `tipo`/`id`; def. TOMA."""
    txt = ("%s %s" % (term.get("tipo") or "", term.get("id") or "")).upper()
    for clave in _RECEPTORES:
        if clave in txt:
            return clave
    if "LUM" in txt or "ALUM" in txt:
        return "LUMINARIA"
    if "MOT" in txt:
        return "MOTOR"
    return _RECEPTOR_DEF


def _potencia_ifc(term):
    """Potencia (W) y cosphi declarados en el modelo neutro / IFC, si los hay.
    Respaldo: clave `potencia_W`/`cosphi` directa o el Pset propio del terminal."""
    p = term.get("potencia_W")
    if p is None:
        p = term.get("potencia")        # alias
    cphi = term.get("cosphi")
    return (float(p) if p else None, float(cphi) if cphi else None)


# ============================================================================
# APLICADORES
# ============================================================================
def aplicar_vivienda(modelo, grado=None):
    """Rellena `demanda` para una instalacion de VIVIENDA (ITC-BT-25). Cada
    terminal se asocia a su circuito (C1..C12) por `tipo`/`id`; los no reconocidos
    se reparten al C2 (tomas de uso general). `modelo` no se muta (copia)."""
    m = copy.deepcopy(modelo)
    sis = m.get("sistema", {}) or {}
    grado = str(grado or sis.get("grado_electrificacion")
                or (sis.get("demanda") or {}).get("grado_electrificacion")
                or _GRADO_DEF).lower()
    if grado not in _ELECTRIFICACION:
        grado = _GRADO_DEF

    p_calc_total = 0.0
    for term in m.get("terminales", []):
        c = _circuito_de(term) or "C2"
        base = _CIRCUITOS_BT25[c]
        fases = base["fases"]
        u = _tension(fases)
        # potencia de calculo del circuito = P_prevista * Fu * Fs (def.); el dato
        # del proyecto (IFC) prevalece sobre la prevision normativa.
        p_ifc, cphi_ifc = _potencia_ifc(term)
        p_calc = p_ifc if p_ifc else round(base["p_prevista_W"] * base["Fu"] * base["Fs"], 1)
        cphi = cphi_ifc if cphi_ifc else 0.95 if base["uso"] == "fuerza" else 0.90
        fuente_dato = "IFC" if p_ifc else "normativa"
        term["demanda"] = {
            "disciplina": "REBT",
            "circuito": c,
            "descripcion": base["desc"],
            "uso": base["uso"],
            "potencia_W": p_calc,
            "cosphi": cphi,
            "fases": fases,
            "tension_V": u,
            "seccion_min_mm2": base["seccion_min_mm2"],
            "du_max_pct": _du_max(base["uso"]),
            "fuente_dato": fuente_dato,
            "criterio": _CRITERIO_BT25,
        }
        p_calc_total += p_calc

    p_min = _ELECTRIFICACION[grado]["p_min_W"]
    p_prevista = max(p_calc_total, p_min)
    sis["demanda"] = {
        "disciplina": "REBT",
        "modo": "vivienda",
        "grado_electrificacion": grado,
        "tension_V": U_MONO,
        "potencia_prevista_W": round(p_prevista, 1),
        "potencia_calculo_W": round(p_calc_total, 1),
        "du_max_alumbrado_pct": DU_MAX_ALUMBRADO_PCT,
        "du_max_fuerza_pct": DU_MAX_FUERZA_PCT,
        "criterio": _CRITERIO_BT25,
    }
    m["sistema"] = sis
    return m


def aplicar_receptores(modelo):
    """Rellena `demanda` para una instalacion de RECEPTORES (terciario/industrial)
    por catalogo de tipo. `modelo` no se muta (copia)."""
    m = copy.deepcopy(modelo)
    sis = m.get("sistema", {}) or {}

    p_total = 0.0
    hay_tri = False
    for term in m.get("terminales", []):
        clave = _receptor_de(term)
        base = _RECEPTORES[clave]
        fases = base["fases"]
        if fases.startswith("tri"):
            hay_tri = True
        u = _tension(fases)
        p_ifc, cphi_ifc = _potencia_ifc(term)
        p = p_ifc if p_ifc else base["potencia_W"]
        cphi = cphi_ifc if cphi_ifc else base["cosphi"]
        fuente_dato = "IFC" if p_ifc else "normativa"
        term["demanda"] = {
            "disciplina": "REBT",
            "tipo_receptor": clave,
            "uso": base["uso"],
            "potencia_W": p,
            "cosphi": cphi,
            "fases": fases,
            "tension_V": u,
            "du_max_pct": _du_max(base["uso"]),
            "fuente_dato": fuente_dato,
            "criterio": _CRITERIO_REC,
        }
        p_total += p

    sis["demanda"] = {
        "disciplina": "REBT",
        "modo": "receptores",
        "tension_V": U_TRI if hay_tri else U_MONO,
        "potencia_prevista_W": round(p_total, 1),
        "du_max_alumbrado_pct": DU_MAX_ALUMBRADO_PCT,
        "du_max_fuerza_pct": DU_MAX_FUERZA_PCT,
        "criterio": _CRITERIO_REC,
    }
    m["sistema"] = sis
    return m


def aplicar_demanda_electrica(modelo, modo=None, grado=None):
    """Dispatcher: enruta a VIVIENDA (ITC-BT-25) o a RECEPTORES (terciario). El
    modo se toma del argumento, de `sistema.modo`/`sistema.demanda.modo`, o se
    deduce: si la mayoria de terminales se reconocen como circuitos C1..C12 ->
    vivienda; si no -> receptores."""
    sis = modelo.get("sistema", {}) or {}
    modo = (modo or sis.get("modo") or (sis.get("demanda") or {}).get("modo")
            or "").lower()
    if modo == "vivienda":
        return aplicar_vivienda(modelo, grado)
    if modo == "receptores":
        return aplicar_receptores(modelo)
    terms = modelo.get("terminales", []) or []
    n_circ = sum(1 for t in terms if _circuito_de(t))
    if terms and n_circ >= len(terms) / 2.0:
        return aplicar_vivienda(modelo, grado)
    return aplicar_receptores(modelo)


def main(modelo_path, out=None):
    with open(modelo_path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    m = aplicar_demanda_electrica(modelo)
    sd = m["sistema"]["demanda"]
    print("BASES DE DEMANDA REBT -- sistema %s (modo %s)"
          % (m["sistema"].get("tipo"), sd.get("modo")))
    print("  Tension: %s V | P prevista: %s W" % (sd["tension_V"], sd["potencia_prevista_W"]))
    for t in m["terminales"]:
        d = t["demanda"]
        print("  %s [%s]: P=%.0f W | cosphi=%.2f | %s | %s V | dato=%s"
              % (t["id"], d.get("circuito") or d.get("tipo_receptor"),
                 d["potencia_W"], d["cosphi"], d["fases"], d["tension_V"],
                 d["fuente_dato"]))
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(m, fh, indent=2, ensure_ascii=False)
        print("Modelo con demanda escrito en", out)
    return m


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
