"""
BASES DE DEMANDA -- ABASTECIMIENTO de agua (red a PRESION). Disciplina
`obras-lineales`, PT 6.3 (Ola 6). Es el "slot" C4 de la red de abastecimiento
(gemelo a presion de `bases_saneamiento.py`, que es lamina libre): rellena la clave
`demanda` del MODELO NEUTRO DE RED (prevista por el parser MEP de iso19650-openbim,
dejada en None) con los CAUDALES DE ABASTECIMIENTO y la PRESION DINAMICA MINIMA, y
fija la PRESION DE LA FUENTE (deposito por cota o grupo de bombeo).

El NUCLEO da la topologia; este modulo aporta la DEMANDA; el solver
(red/solver_presion, copia del Darcy de instalaciones) CALCULA. Frontera C1 (lectura,
iso19650) <-> C4 (demanda) <-> calculo (obras-lineales).

CAUDAL DE ABASTECIMIENTO (EN 805) por ACOMETIDA/nudo de consumo:
  - Caudal medio:  Q_medio = dotacion * habitantes_eq / 86400          (l/s)
  - Caudal punta:  Q_punta = Q_medio * coef_punta                      (l/s)
El dato del proyecto (IFC: `caudal_min` por terminal) PREVALECE sobre el calculo.

HIPOTESIS DE INCENDIO (hidrante) -- decision del ICCP (PT 6.3): por defecto SE
INCLUYE como hipotesis concurrente desfavorable. Cada terminal reconocido como
HIDRANTE recibe el caudal de incendio `caudal_incendio_l_s` (suma al consumo) y se
exige la presion minima `presion_min`. Si no hay hidrantes en la red, la hipotesis
no anade caudal (gancho inerte).

LA FUENTE (ancla de presion, al reves que el VERTIDO del saneamiento):
  - DEPOSITO POR COTA (caso e2e PT 6.3): lamina de agua libre -> presion relativa 0
    en su nudo (colocado a la cota de lamina); la CARGA ESTATICA la genera la
    propagacion por cota del solver (rho*g*dz). presion_fuente = 0 kPa [confirmar AN].
  - GRUPO DE BOMBEO: presion declarada en el nudo de cabecera (NDP) [confirmar AN].
Si el IFC trae la presion de la fuente (`fuentes[*].presion`) PREVALECE.

Bases por defecto (NDP, todos [confirmar AN] -- criterio del despacho / EN 805):
  dotacion 200 l/hab/dia | coef. de punta 2.5 | habitantes_eq por acometida 50 |
  presion dinamica minima 250 kPa (acometida/hidrante) | caudal de incendio por
  hidrante 16.7 l/s (~1000 l/min) | presion de bombeo por defecto 500 kPa.

NO calcula hidraulica (eso es el solver). Devuelve el modelo con `demanda` rellena.
Predimensionado/asistencia; revisar y firmar por tecnico competente (ICCP).
"""
import copy
import json

# --- bases por defecto (NDP [confirmar AN]) ----------------------------------
DOTACION_L_HAB_DIA = 200.0
COEF_PUNTA = 2.5
HABEQ_DEF = 50.0
PRESION_MIN_KPA = 250.0          # presion dinamica minima en acometida/hidrante (EN 805)
CAUDAL_INCENDIO_L_S = 16.7       # ~1000 l/min por hidrante
PRESION_BOMBEO_DEF_KPA = 500.0   # presion declarada por defecto de un grupo de bombeo
_CRITERIO = ("EN 805 (abastecimiento de agua, red a presion); dotacion, coef. de "
             "punta y caudal de incendio segun criterio del despacho/ordenanza "
             "[confirmar AN]")

# reconocimiento de hidrantes (terminal de incendio en la red de abastecimiento)
_HIDRANTE_KW = ("HYDRANT", "HIDRANTE", "FIREHYDRANT", "BIE", "COLUMNA")
# sistemas de abastecimiento (informativo; el parser es agnostico al sistema)
_SISTEMAS_ABASTECIMIENTO = {"WATERSUPPLY", "DOMESTICCOLDWATER", "POTABLEWATER",
                            "COLDWATER", "DOMESTICWATER", "DRINKINGWATER"}


def _es_hidrante(term):
    pred = str(term.get("tipo") or "").upper()
    nm = str(term.get("id") or "").upper()
    return any(k in pred for k in _HIDRANTE_KW) or any(k in nm for k in _HIDRANTE_KW)


def _caudal_medio_l_s(habeq, dotacion):
    return dotacion * float(habeq) / 86400.0


def aplicar(modelo, dotacion=DOTACION_L_HAB_DIA, coef_punta=COEF_PUNTA,
            habeq_def=HABEQ_DEF, presion_min=PRESION_MIN_KPA,
            tipo_fuente="deposito", incluir_incendio=True,
            caudal_incendio=CAUDAL_INCENDIO_L_S,
            presion_bombeo=PRESION_BOMBEO_DEF_KPA):
    """Rellena `demanda` (abastecimiento) en terminales y sistema y fija la presion
    de la fuente. `modelo` no se muta (copia). El dato del IFC (`caudal_min`,
    `fuentes[*].presion`) prevalece."""
    m = copy.deepcopy(modelo)
    sis = m.get("sistema", {}) or {}
    q_total = 0.0
    q_incendio_total = 0.0
    n_hidrantes = 0

    for term in m.get("terminales", []):
        es_hid = _es_hidrante(term)
        # 1) caudal de consumo: dato del IFC si esta; si no, dotacion*hab-eq*punta.
        #    Un HIDRANTE sin dato no aporta consumo domestico (solo caudal de
        #    incendio); su consumo punta solo se considera si el IFC lo declara.
        q_ifc = term.get("caudal_min")
        if q_ifc:
            q_consumo = float(q_ifc)
            base_dato = "IFC"
            det = {"caudal_consumo_l_s": round(q_consumo, 4)}
        elif es_hid:
            q_consumo = 0.0
            base_dato = "normativa"
            det = {"caudal_consumo_l_s": 0.0}
        else:
            habeq = term.get("habitantes_eq")
            habeq = float(habeq) if habeq else habeq_def
            q_med = _caudal_medio_l_s(habeq, dotacion)
            q_consumo = q_med * coef_punta
            base_dato = "normativa"
            det = {"habitantes_eq": habeq, "dotacion_l_hab_dia": dotacion,
                   "coef_punta": coef_punta, "caudal_medio_l_s": round(q_med, 4),
                   "caudal_consumo_l_s": round(q_consumo, 4)}
        # 2) hipotesis de incendio concurrente (hidrante)
        q_inc = 0.0
        if incluir_incendio and es_hid:
            q_inc = float(caudal_incendio)
            n_hidrantes += 1
            q_incendio_total += q_inc
        q = q_consumo + q_inc
        det.update({
            "tipo_terminal": "hidrante" if es_hid else "acometida",
            "caudal_incendio_l_s": round(q_inc, 4),
            "caudal_l_s": round(q, 4),
            "presion_din_min_kPa": float(presion_min),
            "fuente_dato": base_dato,
            "criterio": _CRITERIO,
        })
        term["demanda"] = det
        q_total += q

    # 3) fuente: presion del IFC si esta; si no, segun el tipo de fuente
    p_fuente_inyectada = None
    for f_ in m.get("fuentes", []):
        if f_.get("presion") is None:
            if tipo_fuente == "deposito":
                f_["presion"] = 0.0   # lamina libre: la cota genera la carga
                p_fuente_inyectada = 0.0
            else:                      # bombeo
                f_["presion"] = float(presion_bombeo)
                p_fuente_inyectada = float(presion_bombeo)
            f_["modelo_fuente"] = tipo_fuente
            f_["criterio"] = _CRITERIO

    sis["demanda"] = {
        "disciplina": "abastecimiento",
        "norma": "EN 805",
        "tipo_fuente": tipo_fuente,
        "dotacion_l_hab_dia": dotacion,
        "coef_punta": coef_punta,
        "presion_din_min_kPa": float(presion_min),
        "incluir_incendio": bool(incluir_incendio),
        "caudal_incendio_l_s": float(caudal_incendio) if incluir_incendio else 0.0,
        "n_hidrantes": n_hidrantes,
        "caudal_incendio_total_l_s": round(q_incendio_total, 4),
        "caudal_total_l_s": round(q_total, 4),
        "presion_fuente_inyectada_kPa": p_fuente_inyectada,
        "criterio": _CRITERIO,
        # red a presion: por defecto se exige el caso simultaneo COMPLETO (consumo
        # punta en todas las acometidas + hidrante concurrente). El solver puede
        # acotar n_simultaneas si el despacho lo decide [confirmar AN].
    }
    m["sistema"] = sis
    return m


def aplicar_demanda(modelo, **kw):
    """Dispatcher: abastecimiento a presion (EN 805). Homogeneo con el
    `aplicar_demanda` de `bases_saneamiento.py` (lamina libre)."""
    return aplicar(modelo, **kw)


def main(modelo_path, out=None):
    with open(modelo_path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    m = aplicar_demanda(modelo)
    sd = m["sistema"]["demanda"]
    print("BASES DE DEMANDA ABASTECIMIENTO -- sistema %s | fuente %s"
          % (m["sistema"].get("tipo"), sd["tipo_fuente"]))
    print("  caudal total: %.3f l/s (dotacion %.0f l/hab/dia, punta %.1f; incendio %d "
          "hidrante(s) = %.3f l/s)"
          % (sd["caudal_total_l_s"], sd["dotacion_l_hab_dia"], sd["coef_punta"],
             sd["n_hidrantes"], sd["caudal_incendio_total_l_s"]))
    for t in m["terminales"]:
        d = t["demanda"]
        print("  %s [%s]: Q=%.3f l/s (consumo %.3f + incendio %.3f) p_min=%.0f kPa (dato=%s)"
              % (t["id"], d["tipo_terminal"], d["caudal_l_s"], d["caudal_consumo_l_s"],
                 d["caudal_incendio_l_s"], d["presion_din_min_kPa"], d["fuente_dato"]))
    for f_ in m.get("fuentes", []):
        print("  fuente %s: presion=%s kPa (%s)"
              % (f_.get("id"), f_.get("presion"), f_.get("modelo_fuente", "dato IFC")))
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
