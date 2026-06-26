"""
HIDROLOGIA -- Norma 5.2-IC (Drenaje superficial). Plugin obras-lineales. PT 6.1 (Ola 6).

Es el "slot" C4 de la disciplina aplicado al DRENAJE: la hidrologia (CAUDALES DE
CALCULO) que gobierna el dimensionado de cunetas (drenaje superficial) y obras de
drenaje transversal (ODT). Analogo a bases_firme (firmes) y bases_demanda
(instalaciones): NO dimensiona el elemento; provee el CAUDAL que cuneta.py / odt.py
contrastan contra la capacidad.

METODO RACIONAL MODIFICADO (5.2-IC, apdo. 2.2), valido para cuencas pequenas
(tiempo de concentracion tc < ~6 h):

    Q = (C * I * A * Kt) / 3.6            [m3/s]   (A en km2, I en mm/h)

  - tc  : tiempo de concentracion (Temez)      tc = 0.3 * (L / J^0.25)^0.76   [h]
  - I   : intensidad de la curva IDF de la 5.2-IC para (T, tc):
              I(tc) = Id * (I1/Id)^[(28^0.1 - tc^0.1)/(28^0.1 - 1)]
          con Id = Pd/24 (intensidad media diaria) y Pd = max. lluvia diaria del
          periodo de retorno T (mapa "Maximas lluvias diarias en la Espana peninsular").
  - C   : coeficiente de escorrentia (umbral de escorrentia Po, 5.2-IC apdo. 2.5):
              Pd' = Pd * KA  (KA reduccion areal);  si Pd' <= Po -> C = 0; si no:
              C = (Pd'/Po - 1) * (Pd'/Po + 23) / (Pd'/Po + 11)^2
  - Kt  : coeficiente de uniformidad temporal   Kt = 1 + tc^1.25 / (tc^1.25 + 14)
  - KA  : factor reductor por area de la cuenca  KA = 1 - log10(A_km2)/15   (A>1 km2)

FRONTERA (C1/C4): la CUENCA (area A, longitud L, pendiente J) es un DATO hidrologico:
si esta en el GIS/Pset PREVALECE; si falta, lo inyecta el agente y se documenta
[confirmar AN]. La lluvia de proyecto (Pd, I1/Id, Po) son datos REGIONALES del
proyecto (mapa/estudio pluviometrico), NDP [confirmar AN]. La 5.2-IC y los valores
por defecto se confirman con el Anejo Nacional / la edicion vigente -> [confirmar AN].

Todo es predimensionado; revisar y firmar por tecnico competente (ICCP).
"""
import math

# --- Periodos de retorno de proyecto por tipo de elemento (anos) -- 5.2-IC,
#     tabla 3.1/3.2 (segun tipo de via e IMD). NDP [confirmar AN].
PERIODO_RETORNO_DEF = {
    "plataforma": 25,      # drenaje de plataforma y margenes (cunetas)
    "cuneta": 25,
    "odt": 100,            # obras de drenaje transversal (caso general)
    "odt_secundaria": 25,
}

# --- Lluvia de proyecto por defecto (regional; NDP [confirmar AN]) --------------
#     Pd: maxima precipitacion diaria del periodo de retorno T (mm). Por defecto se
#     deja None: DEBE aportarla el proyecto (mapa de maximas lluvias diarias).
PD_DEFECTO_MM = None
# I1/Id: indice de torrencialidad (cociente intensidad horaria/diaria). 5.2-IC fig.
#     A.1; ~9-11 en la mitad N peninsular, hasta ~11-12 en el SE. NDP [confirmar AN].
I1_ID_DEFECTO = 9.0
# Po: umbral de escorrentia (mm) de la cuenca (5.2-IC tabla 2.3, segun uso del suelo,
#     pendiente, grupo hidrologico y humedad), corregido por el coef. regional beta.
#     Plataforma de carretera (impermeable) ~ 1 mm. NDP [confirmar AN].
PO_DEFECTO_MM = 1.0

G = 9.81


def periodo_retorno(tipo_elemento="plataforma"):
    """Periodo de retorno de proyecto (anos) por tipo de elemento (5.2-IC)."""
    return PERIODO_RETORNO_DEF.get(tipo_elemento, 25)


def tiempo_concentracion(longitud_km, pendiente, tc_min_h=0.0):
    """Tiempo de concentracion de Temez (5.2-IC):  tc = 0.3*(L/J^0.25)^0.76  [h].
    L en km (longitud del cauce principal), J pendiente media (m/m). Un suelo de tc
    muy bajo (cuencas urbanas/plataforma) se acota con tc_min_h. [confirmar AN]."""
    L = float(longitud_km)
    J = max(float(pendiente), 1e-6)
    tc = 0.3 * (L / J ** 0.25) ** 0.76
    return max(tc, float(tc_min_h))


def coef_uniformidad(tc_h):
    """Coeficiente de uniformidad temporal Kt (5.2-IC):
        Kt = 1 + tc^1.25 / (tc^1.25 + 14)   (tc en horas)."""
    t = max(float(tc_h), 1e-6)
    return 1.0 + t ** 1.25 / (t ** 1.25 + 14.0)


def reduccion_areal(area_km2):
    """Factor reductor por area de la cuenca KA (5.2-IC):
        KA = 1 - log10(A)/15   (A en km2, A>1);  KA=1 para A<=1 km2."""
    A = float(area_km2)
    if A <= 1.0:
        return 1.0
    return max(1.0 - math.log10(A) / 15.0, 0.0)


def intensidad_idf(tc_h, pd_mm, i1_id=I1_ID_DEFECTO):
    """Intensidad de la curva IDF de la 5.2-IC (mm/h) para (T via Pd, tc):
        Id = Pd/24 ;  I(tc) = Id * (I1/Id)^[(28^0.1 - tc^0.1)/(28^0.1 - 1)]
    Pd = max. lluvia diaria del periodo de retorno T (mm). [confirmar AN]."""
    if pd_mm is None:
        raise ValueError("Falta Pd (max. lluvia diaria del periodo de retorno T).")
    Id = float(pd_mm) / 24.0
    tc = max(float(tc_h), 1e-6)
    exp = (28.0 ** 0.1 - tc ** 0.1) / (28.0 ** 0.1 - 1.0)
    return Id * (float(i1_id)) ** exp


def coef_escorrentia(pd_mm, po_mm=PO_DEFECTO_MM, ka=1.0):
    """Coeficiente de escorrentia C (5.2-IC, umbral de escorrentia Po):
        Pd' = Pd*KA ;  si Pd' <= Po -> 0 ;  si no
        C = (Pd'/Po - 1)*(Pd'/Po + 23) / (Pd'/Po + 11)^2
    Po = umbral de escorrentia corregido (mm). [confirmar AN]."""
    if pd_mm is None:
        raise ValueError("Falta Pd para el coeficiente de escorrentia.")
    Po = max(float(po_mm), 1e-6)
    Pd = float(pd_mm) * float(ka)
    r = Pd / Po
    if r <= 1.0:
        return 0.0
    return (r - 1.0) * (r + 23.0) / (r + 11.0) ** 2


def _area_km2(cuenca):
    if cuenca.get("area_km2") is not None:
        return float(cuenca["area_km2"])
    if cuenca.get("area_m2") is not None:
        return float(cuenca["area_m2"]) / 1e6
    if cuenca.get("area_ha") is not None:
        return float(cuenca["area_ha"]) / 100.0
    raise ValueError("La cuenca no declara area (area_km2/area_m2/area_ha).")


def _longitud_km(cuenca):
    if cuenca.get("longitud_km") is not None:
        return float(cuenca["longitud_km"])
    if cuenca.get("longitud_m") is not None:
        return float(cuenca["longitud_m"]) / 1000.0
    raise ValueError("La cuenca no declara longitud (longitud_km/longitud_m).")


def caudal_cuenca(cuenca, periodo_retorno_anos=None, tipo_elemento="plataforma",
                  i1_id=None, po_mm=None, tc_min_h=0.0):
    """Caudal de calculo de una CUENCA por el metodo racional modificado (5.2-IC).

    cuenca: dict con area (km2/m2/ha), longitud (km/m), pendiente (m/m) y, si los
            aporta el proyecto/GIS (PREVALECEN): pd_mm, i1_id, po_mm, periodo_retorno.
    Devuelve un dict con tc, I, C, Kt, KA y Q (m3/s) + trazabilidad de entradas.
    """
    A = _area_km2(cuenca)
    L = _longitud_km(cuenca)
    J = float(cuenca.get("pendiente", cuenca.get("pendiente_media", 0.0)))
    if J <= 0:
        raise ValueError("La cuenca no declara pendiente (m/m > 0).")

    T = (periodo_retorno_anos if periodo_retorno_anos is not None
         else cuenca.get("periodo_retorno", periodo_retorno(tipo_elemento)))
    pd = cuenca.get("pd_mm", PD_DEFECTO_MM)
    if pd is None:
        raise ValueError("Falta Pd (max. lluvia diaria del periodo de retorno T): "
                         "aportala en la cuenca (pd_mm) o desde el GIS/estudio pluviometrico.")
    i1 = i1_id if i1_id is not None else cuenca.get("i1_id", I1_ID_DEFECTO)
    po = po_mm if po_mm is not None else cuenca.get("po_mm", PO_DEFECTO_MM)

    tc = tiempo_concentracion(L, J, tc_min_h=tc_min_h)
    KA = reduccion_areal(A)
    I = intensidad_idf(tc, pd, i1)
    C = coef_escorrentia(pd, po, KA)
    Kt = coef_uniformidad(tc)
    Q = C * I * A * Kt / 3.6

    return {
        "cuenca": cuenca.get("id", "cuenca"),
        "tipo_elemento": tipo_elemento,
        "periodo_retorno_anos": T,
        "area_km2": round(A, 5),
        "longitud_km": round(L, 4),
        "pendiente_m_m": round(J, 5),
        "pd_mm": float(pd),
        "i1_id": float(i1),
        "po_mm": float(po),
        "tc_h": round(tc, 4),
        "intensidad_mm_h": round(I, 2),
        "coef_escorrentia": round(C, 4),
        "factor_reductor_KA": round(KA, 4),
        "coef_uniformidad_Kt": round(Kt, 4),
        "caudal_m3_s": round(Q, 4),
        "metodo": "Racional modificado 5.2-IC (Temez)",
        "nota": "Predimensionado 5.2-IC. Pd/I1Id/Po regionales; cuenca del GIS/Pset si "
                "existe. NDP [confirmar AN].",
    }


if __name__ == "__main__":
    demo = {"id": "C-plataforma", "area_m2": 9000.0, "longitud_m": 300.0,
            "pendiente": 0.02, "pd_mm": 80.0, "i1_id": 9.0, "po_mm": 1.0}
    import json
    print(json.dumps(caudal_cuenca(demo, periodo_retorno_anos=25,
                                   tipo_elemento="plataforma", tc_min_h=0.0),
                     indent=2, ensure_ascii=False))
