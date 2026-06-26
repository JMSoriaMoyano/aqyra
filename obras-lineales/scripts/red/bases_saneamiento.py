"""
BASES DE DEMANDA -- SANEAMIENTO (aguas residuales). Disciplina `obras-lineales`,
PT 6.2 (Ola 6). Es el "slot" C4 de la red de saneamiento (analogo a las acciones
EC0/EC1 de estructuras o a las bases de demanda PCI de instalaciones): rellena la
clave `demanda` del MODELO NEUTRO DE RED (prevista por el parser MEP de
iso19650-openbim, dejada en None) con los CAUDALES DE AGUAS RESIDUALES.

El NUCLEO da la topologia; este modulo aporta la DEMANDA; el solver
(red/solver_lamina_libre) CALCULA. Frontera C1 (lectura, iso19650) <-> C4 (demanda)
<-> calculo (obras-lineales).

CAUDAL DE AGUAS RESIDUALES (separativo) por ACOMETIDA/nudo de aporte:
  - Caudal medio:  Q_medio = dotacion * habitantes_eq * coef_retorno / 86400  (l/s)
  - Caudal punta:  Q_punta = Q_medio * coef_punta + Q_infiltracion           (l/s)
El dato del proyecto (IFC: `caudal_min` por terminal) PREVALECE sobre el calculo.

REGIMEN: por defecto SEPARATIVO de aguas residuales (fecales). La componente
PLUVIAL (red unitaria) reutiliza la hidrologia racional 5.2-IC de `drenaje/
hidrologia.py` (gancho `aplicar_pluviales`, no usado en el caso base [confirmar AN]).

Bases por defecto (NDP, todos [confirmar AN] -- criterio del despacho / EN 752):
  dotacion 200 l/hab/dia | coef. de retorno 0.80 | coef. de punta 2.5 |
  caudal de infiltracion 0 l/s | habitantes_eq por acometida 50 (si no hay dato).

NO calcula hidraulica (eso es el solver). Devuelve el modelo con `demanda` rellena.
Predimensionado/asistencia; revisar y firmar por tecnico competente (ICCP).
"""
import copy
import json

# --- bases por defecto (NDP [confirmar AN]) ----------------------------------
DOTACION_L_HAB_DIA = 200.0
COEF_RETORNO = 0.80
COEF_PUNTA = 2.5
Q_INFILTRACION_L_S = 0.0
HABEQ_DEF = 50.0
_CRITERIO = ("EN 752 (redes de saneamiento); dotacion y coef. de punta segun "
             "criterio del despacho/ordenanza municipal [confirmar AN]")
_SISTEMAS_SANEAMIENTO = {"SEWAGE", "WASTEWATER", "DRAINAGE", "STORMWATER",
                         "SANITARY", "FOULWATER"}


def _caudal_medio_l_s(habeq, dotacion, retorno):
    return dotacion * float(habeq) * retorno / 86400.0


def aplicar(modelo, dotacion=DOTACION_L_HAB_DIA, retorno=COEF_RETORNO,
            coef_punta=COEF_PUNTA, q_infiltracion=Q_INFILTRACION_L_S,
            habeq_def=HABEQ_DEF):
    """Rellena `demanda` (residuales) en terminales y sistema. `modelo` no se muta
    (copia). El dato del IFC (`caudal_min`) prevalece por terminal."""
    m = copy.deepcopy(modelo)
    sis = m.get("sistema", {}) or {}
    q_total = 0.0
    for term in m.get("terminales", []):
        # 1) dato del proyecto (IFC) si esta
        q_ifc = term.get("caudal_min")
        if q_ifc:
            q = float(q_ifc)
            habeq = term.get("habitantes_eq")
            term["demanda"] = {
                "tipo_aporte": "acometida",
                "caudal_l_s": round(q, 4),
                "fuente_dato": "IFC",
                "criterio": _CRITERIO,
            }
        else:
            habeq = term.get("habitantes_eq")
            habeq = float(habeq) if habeq else habeq_def
            q_med = _caudal_medio_l_s(habeq, dotacion, retorno)
            q = q_med * coef_punta + q_infiltracion
            term["demanda"] = {
                "tipo_aporte": "acometida",
                "habitantes_eq": habeq,
                "dotacion_l_hab_dia": dotacion,
                "coef_retorno": retorno,
                "coef_punta": coef_punta,
                "caudal_medio_l_s": round(q_med, 4),
                "caudal_infiltracion_l_s": q_infiltracion,
                "caudal_l_s": round(q, 4),
                "fuente_dato": "normativa",
                "criterio": _CRITERIO,
            }
        q_total += q

    sis["demanda"] = {
        "disciplina": "saneamiento",
        "regimen": "separativo-residuales",
        "dotacion_l_hab_dia": dotacion,
        "coef_retorno": retorno,
        "coef_punta": coef_punta,
        "caudal_infiltracion_l_s": q_infiltracion,
        "caudal_total_l_s": round(q_total, 4),
        "criterio": _CRITERIO,
    }
    m["sistema"] = sis
    return m


def aplicar_pluviales(modelo, cuencas=None):
    """GANCHO (red unitaria/pluvial): la componente pluvial reutiliza la hidrologia
    racional 5.2-IC de `drenaje/hidrologia.py` (caudal por cuenca -> aporte en el
    nudo de la acometida pluvial). No implementado en el caso base; se documenta la
    via [confirmar AN]. Para una red unitaria se sumaria al caudal residual."""
    raise NotImplementedError(
        "Componente pluvial: reutilizar drenaje/hidrologia.py (racional 5.2-IC) y "
        "sumar el caudal de cuenca al nudo de aporte. Gancho del PT 6.2 [confirmar AN].")


def aplicar_demanda(modelo, regimen="residuales", **kw):
    """Dispatcher: por ahora SEPARATIVO de residuales (EN 752). El regimen unitario
    (residuales + pluviales) queda como gancho `aplicar_pluviales`."""
    if regimen in ("residuales", "separativo", "fecales"):
        return aplicar(modelo, **kw)
    raise NotImplementedError("Regimen %r no implementado (solo residuales en el "
                              "caso base del PT 6.2)." % regimen)


def main(modelo_path, out=None):
    with open(modelo_path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    m = aplicar_demanda(modelo)
    sd = m["sistema"]["demanda"]
    print("BASES DE DEMANDA SANEAMIENTO -- sistema %s | regimen %s"
          % (m["sistema"].get("tipo"), sd["regimen"]))
    print("  caudal total: %.3f l/s (dotacion %.0f l/hab/dia, punta %.1f)"
          % (sd["caudal_total_l_s"], sd["dotacion_l_hab_dia"], sd["coef_punta"]))
    for t in m["terminales"]:
        d = t["demanda"]
        print("  %s: Q=%.3f l/s (dato=%s)"
              % (t["id"], d["caudal_l_s"], d["fuente_dato"]))
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
