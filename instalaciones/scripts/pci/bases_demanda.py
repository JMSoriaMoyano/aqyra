"""
BASES DE DEMANDA -- PCI (hueco H3, contrato C4 para disciplinas NO estructurales).
Disciplina `instalaciones`, PT 4.3 (Ola 4).

Rellena la clave `demanda` del MODELO NEUTRO DE RED (prevista por el parser MEP de
iso19650-openbim, PT 4.2, dejada en None) con las bases de demanda de PROTECCION
CONTRA INCENDIOS por BIE: caudal de calculo y presion dinamica minima por terminal
y la simultaneidad del sistema. Es el "slot" C4 de la disciplina (analogo a las
acciones EC0/EC1 de estructuras, aqui DEMANDAS en vez de cargas).

El NUCLEO da la topologia; este modulo aporta la DEMANDA; el solver (red/solver_red)
CALCULA. Frontera C1 (lectura, iso19650) <-> C4 (demanda) <-> calculo (instalaciones).

Bases por defecto (NDP, todos [confirmar AN] -- criterio del despacho):
  RIPCI (RD 513/2017, Anexo I) | UNE-EN 671-1/-2 (BIE) | UNE 23500 (abastecimiento)
  | DB-SI SI4 (dotacion de instalaciones de proteccion).
    - BIE-25 (manguera semirrigida DN25): caudal de calculo 1.6 l/s; presion
      dinamica minima 200 kPa (2 bar) en boquilla; n simultaneas = 2 (las 2 mas
      desfavorables).
    - BIE-45 (manguera plana DN45): caudal 3.3 l/s; presion minima 200 kPa;
      n simultaneas = 2.
  Si el modelo neutro ya trae `caudal_min`/`presion_min` por terminal (dato del
  proyecto en el IFC), ESE dato PREVALECE sobre el valor por defecto.
  Presion maxima en boquilla 500 kPa (5 bar); autonomia 60 min.

NO calcula hidraulica (eso es el solver). Devuelve el modelo con `demanda` rellena.

Predimensionado/asistencia; revisar y firmar por tecnico competente.
"""
import copy
import json
import math

# tabla de tipos de terminal PCI -> (caudal l/s, presion din. min kPa, n_simult.)
# NDP [confirmar AN]
_BIE = {
    "BIE25": {"caudal_l_s": 1.6, "presion_din_min_kPa": 200.0, "n_simultaneas": 2},
    "BIE45": {"caudal_l_s": 3.3, "presion_din_min_kPa": 200.0, "n_simultaneas": 2},
}
_PRESION_MAX_KPA = 500.0
_AUTONOMIA_MIN = 60
_CRITERIO = ("RIPCI RD 513/2017 Anexo I; UNE-EN 671-1/-2; UNE 23500; "
             "DB-SI SI4 [confirmar AN]")
_SISTEMAS_PCI = {"FIREPROTECTION", "FIRESUPPRESSION"}

# --- ROCIADORES automaticos (UNE-EN 12845) ----------------------------------
# Base de demanda por DENSIDAD de descarga x AREA DE OPERACION segun clase de
# riesgo. densidad (mm/min) = l/min por m2; area_op (m2) = area de operacion mas
# desfavorable (sistema humedo); cobertura (m2) = area protegida por rociador;
# K (l/min/bar^0.5) factor del rociador (Q = K*sqrt(p)); duracion (min).
# Todos los valores son NDP [confirmar AN] (criterio del despacho / UNE-EN 12845).
_ROCIADORES = {
    "LH":   {"densidad_mm_min": 2.25, "area_op_m2": 84.0,  "cobertura_m2": 21.0, "K": 57.0,  "duracion_min": 30},
    "OH1":  {"densidad_mm_min": 5.0,  "area_op_m2": 72.0,  "cobertura_m2": 12.0, "K": 80.0,  "duracion_min": 60},
    "OH2":  {"densidad_mm_min": 5.0,  "area_op_m2": 72.0,  "cobertura_m2": 12.0, "K": 80.0,  "duracion_min": 60},
    "OH3":  {"densidad_mm_min": 5.0,  "area_op_m2": 72.0,  "cobertura_m2": 12.0, "K": 80.0,  "duracion_min": 60},
    "OH4":  {"densidad_mm_min": 5.0,  "area_op_m2": 90.0,  "cobertura_m2": 12.0, "K": 80.0,  "duracion_min": 60},
    "HHP1": {"densidad_mm_min": 7.5,  "area_op_m2": 260.0, "cobertura_m2": 9.0,  "K": 115.0, "duracion_min": 90},
    "HHP2": {"densidad_mm_min": 10.0, "area_op_m2": 260.0, "cobertura_m2": 9.0,  "K": 115.0, "duracion_min": 90},
    "HHP3": {"densidad_mm_min": 12.5, "area_op_m2": 260.0, "cobertura_m2": 9.0,  "K": 115.0, "duracion_min": 90},
}
_CLASE_DEF = "OH1"               # clase de riesgo por defecto (la mas habitual)
_PRESION_MIN_FLOOR_KPA = 35.0    # presion minima en boquilla (0.35 bar) [confirmar AN]
_CRITERIO_ROC = ("UNE-EN 12845 (rociadores automaticos): densidad x area de "
                 "operacion por clase de riesgo; RIPCI RD 513/2017; DB-SI SI4 "
                 "[confirmar AN]")


def _clasificar_terminal(term):
    """Deduce el tipo de BIE del terminal (por su `tipo`/`id`); def. BIE25."""
    txt = ("%s %s" % (term.get("tipo") or "", term.get("id") or "")).upper()
    if "45" in txt:
        return "BIE45"
    return "BIE25"   # def.: BIE-25 (el mas habitual)


def aplicar(modelo, criterio_simultaneas=None):
    """Rellena `demanda` en terminales y sistema para una red PCI. `modelo` no se
    muta (se devuelve copia). `criterio_simultaneas` fuerza n simultaneas (si None,
    se toma de la tabla por tipo de terminal)."""
    m = copy.deepcopy(modelo)
    sis = m.get("sistema", {}) or {}
    tipo_sis = str(sis.get("tipo") or "").upper()
    es_pci = tipo_sis in _SISTEMAS_PCI

    n_sim_sistema = 0
    for term in m.get("terminales", []):
        clase = _clasificar_terminal(term)
        base = _BIE.get(clase, _BIE["BIE25"])
        # el dato del proyecto (IFC) prevalece sobre el valor por defecto
        q = term.get("caudal_min")
        q = float(q) if q else base["caudal_l_s"]
        p = term.get("presion_min")
        p = float(p) if p else base["presion_din_min_kPa"]
        fuente_dato = "IFC" if (term.get("caudal_min") or term.get("presion_min")) else "normativa"
        term["demanda"] = {
            "tipo_terminal": clase,
            "caudal_l_s": q,
            "presion_din_min_kPa": p,
            "presion_max_kPa": _PRESION_MAX_KPA,
            "fuente_dato": fuente_dato,
            "criterio": _CRITERIO,
        }
        n_sim_sistema = max(n_sim_sistema, base["n_simultaneas"])

    if criterio_simultaneas:
        n_sim_sistema = int(criterio_simultaneas)
    if not es_pci:
        # sistema no-PCI: dejamos demanda de sistema marcada pero sin simultaneidad PCI
        n_sim_sistema = n_sim_sistema or None

    sis["demanda"] = {
        "disciplina": "PCI" if es_pci else "GENERICA",
        "n_simultaneas": n_sim_sistema,
        "autonomia_min": _AUTONOMIA_MIN if es_pci else None,
        "presion_max_kPa": _PRESION_MAX_KPA,
        "criterio": _CRITERIO,
    }
    m["sistema"] = sis
    return m


def _es_rociador(term):
    """True si el terminal es un rociador (por su `tipo`/`id`)."""
    txt = ("%s %s" % (term.get("tipo") or "", term.get("id") or "")).upper()
    return ("SPRINKLER" in txt or "ROCIADOR" in txt or txt.strip().startswith("ROC")
            or txt.strip().startswith("SPR"))


def _clase_riesgo(modelo, clase=None):
    """Clase de riesgo (UNE-EN 12845): argumento explicito > sistema.clase_riesgo
    > sistema.demanda.clase_riesgo > defecto OH1. Normaliza mayusculas."""
    if not clase:
        sis = modelo.get("sistema", {}) or {}
        clase = sis.get("clase_riesgo") or (sis.get("demanda") or {}).get("clase_riesgo")
    clase = str(clase or _CLASE_DEF).upper()
    return clase if clase in _ROCIADORES else _CLASE_DEF


def aplicar_rociadores(modelo, clase_riesgo=None):
    """Rellena `demanda` para una red de ROCIADORES automaticos (UNE-EN 12845)
    por DENSIDAD x AREA DE OPERACION. `modelo` no se muta (copia). Calcula:
      - n rociadores del area de operacion mas desfavorable: n = ceil(A_op/A_cob),
      - caudal minimo por rociador Q_min = densidad * A_cob (l/min -> l/s),
      - presion en boquilla del rociador mas desfavorable p = (Q_min/K)^2 (bar,
        Q=K*sqrt(p)), con piso _PRESION_MIN_FLOOR_KPA,
      - caudal de diseno total Q_dis = densidad * A_op (l/min -> l/s).
    El dato del proyecto (IFC: caudal_min/presion_min por terminal) PREVALECE."""
    m = copy.deepcopy(modelo)
    clase = _clase_riesgo(m, clase_riesgo)
    base = _ROCIADORES[clase]
    dens = base["densidad_mm_min"]; a_op = base["area_op_m2"]
    a_cob = base["cobertura_m2"]; K = base["K"]
    n = int(math.ceil(a_op / a_cob))
    q_min_lmin = dens * a_cob                    # l/min por rociador
    q_min_ls = q_min_lmin / 60.0                 # l/s
    p_bar = (q_min_lmin / K) ** 2 if K else 0.0  # Q = K*sqrt(p)  -> p = (Q/K)^2 (bar)
    p_min_kpa = max(p_bar * 100.0, _PRESION_MIN_FLOOR_KPA)
    q_dis_ls = dens * a_op / 60.0                # caudal de diseno total l/s

    for term in m.get("terminales", []):
        q = term.get("caudal_min")
        q = float(q) if q else round(q_min_ls, 4)
        p = term.get("presion_min")
        p = float(p) if p else round(p_min_kpa, 3)
        fuente_dato = "IFC" if (term.get("caudal_min") or term.get("presion_min")) else "normativa"
        term["demanda"] = {
            "tipo_terminal": "Rociador %s" % clase,
            "caudal_l_s": q,
            "presion_din_min_kPa": p,
            "presion_max_kPa": _PRESION_MAX_KPA,
            "K_factor_lmin_bar": K,
            "densidad_mm_min": dens,
            "cobertura_m2": a_cob,
            "fuente_dato": fuente_dato,
            "criterio": _CRITERIO_ROC,
        }

    sis = m.get("sistema", {}) or {}
    sis["demanda"] = {
        "disciplina": "PCI-rociadores",
        "clase_riesgo": clase,
        "densidad_mm_min": dens,
        "area_operacion_m2": a_op,
        "cobertura_rociador_m2": a_cob,
        "n_simultaneas": n,
        "caudal_diseno_l_s": round(q_dis_ls, 4),
        "K_factor_lmin_bar": K,
        "presion_din_min_kPa": round(p_min_kpa, 3),
        "presion_max_kPa": _PRESION_MAX_KPA,
        "autonomia_min": base["duracion_min"],
        "criterio": _CRITERIO_ROC,
    }
    m["sistema"] = sis
    return m


def aplicar_demanda(modelo, clase_riesgo=None, criterio_simultaneas=None):
    """Dispatcher: si la red es de ROCIADORES (mayoria de terminales rociador o
    clase de riesgo declarada) aplica UNE-EN 12845; si no, BIE (RIPCI/UNE-EN 671)."""
    terms = modelo.get("terminales", []) or []
    sis = modelo.get("sistema", {}) or {}
    hay_clase = bool(sis.get("clase_riesgo") or (sis.get("demanda") or {}).get("clase_riesgo")
                     or clase_riesgo)
    n_roc = sum(1 for t in terms if _es_rociador(t))
    if hay_clase or (terms and n_roc >= len(terms) / 2.0):
        return aplicar_rociadores(modelo, clase_riesgo)
    return aplicar(modelo, criterio_simultaneas)


def main(modelo_path, out=None):
    with open(modelo_path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    m = aplicar_demanda(modelo)
    sd = m["sistema"]["demanda"]
    print("BASES DE DEMANDA PCI -- sistema %s" % m["sistema"].get("tipo"))
    print("  n simultaneas:", sd["n_simultaneas"], "| autonomia:", sd["autonomia_min"], "min")
    for t in m["terminales"]:
        d = t["demanda"]
        print("  %s [%s]: Q=%.2f l/s | p_min=%.0f kPa | dato=%s"
              % (t["id"], d["tipo_terminal"], d["caudal_l_s"],
                 d["presion_din_min_kPa"], d["fuente_dato"]))
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
