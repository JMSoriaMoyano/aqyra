"""
PARAMETROS DE TRAZADO -- Norma 3.1-IC (Trazado, Orden FOM/273/2016).
Plugin obras-lineales (disciplina vertical). PT 5.2 (Ola 5).

Tablas y formulas normativas en funcion de la VELOCIDAD DE PROYECTO Vp para
comprobar el trazado en PLANTA y ALZADO. Es la capa de "bases" de la disciplina
(analoga a bases_demanda de instalaciones): NO calcula geometria; provee los
umbrales que comprobacion_trazado.py contrasta contra el eje real.

Frontera: la lectura del IFC y la COHERENCIA geometrica (continuidad/tangencia)
las hace iso19650-openbim (validacion_alineacion.py); AQUI vive el cumplimiento
NORMATIVO frente a Vp (radios minimos, clotoides, acuerdos verticales, pendientes,
visibilidad). Todo es predimensionado y debe revisarse/firmarse por tecnico
competente (ICCP). Los valores marcados NDP se confirman con el Anejo Nacional /
la edicion vigente de la 3.1-IC -> [confirmar AN].
"""
import math

# --- Velocidades de proyecto contempladas (km/h) -------------------------------
VP_VALIDAS = [40, 50, 60, 70, 80, 90, 100, 110, 120]

# --- Radio minimo en planta (m) por Vp -- 3.1-IC, peralte maximo ~7% (grupo 2/3,
#     carreteras convencionales). [confirmar AN] (edicion vigente / autovias 8%).
RADIO_MIN_PLANTA = {
    40: 50, 50: 85, 60: 130, 70: 190, 80: 250,
    90: 350, 100: 450, 110: 560, 120: 700,
}

# --- Pendiente longitudinal MAXIMA (m/m) por Vp -- 3.1-IC (convencionales).
#     [confirmar AN] segun grupo de carretera y excepciones.
PENDIENTE_MAX = {
    40: 0.07, 50: 0.07, 60: 0.06, 70: 0.055, 80: 0.05,
    90: 0.05, 100: 0.04, 110: 0.04, 120: 0.04,
}
# Pendiente MINIMA recomendada por drenaje longitudinal (m/m). [confirmar AN].
PENDIENTE_MIN = 0.005      # 0,5 %
PENDIENTE_MIN_ABS = 0.002  # 0,2 % minimo absoluto en tramos especiales

# --- Coeficiente de rozamiento longitudinal movilizado fl(Vp) -- 3.1-IC, para la
#     distancia de parada. [confirmar AN].
FL_PARADA = {
    40: 0.432, 50: 0.411, 60: 0.390, 70: 0.369, 80: 0.348,
    90: 0.334, 100: 0.320, 110: 0.306, 120: 0.292,
}

# --- Parametros de visibilidad / acuerdos verticales (NDP de despacho) ----------
TIEMPO_PERCEPCION_REACCION = 2.0   # s  (tp), 3.1-IC
ALTURA_OJO = 1.10                  # m  (h1) altura del punto de vista del conductor
ALTURA_OBSTACULO = 0.20            # m  (h2) altura del obstaculo para visibilidad de parada
ALTURA_FAROS = 0.50                # m  (acuerdos concavos, visibilidad nocturna)
ANGULO_FAROS_RAD = math.radians(1.0)


def _norm_vp(vp):
    """Devuelve la Vp tabulada >= vp (la inmediatamente superior contemplada)."""
    vp = float(vp)
    for v in VP_VALIDAS:
        if vp <= v:
            return v
    return VP_VALIDAS[-1]


def radio_minimo(vp):
    """Radio minimo en planta (m) para la Vp (3.1-IC)."""
    return RADIO_MIN_PLANTA[_norm_vp(vp)]


def pendiente_maxima(vp):
    """Pendiente longitudinal maxima (m/m) para la Vp (3.1-IC)."""
    return PENDIENTE_MAX[_norm_vp(vp)]


def distancia_parada(vp, i=0.0):
    """Distancia de PARADA Dp (m) -- 3.1-IC:
        Dp = Vp*tp/3.6 + Vp^2 / (254*(fl +/- i))
    con Vp en km/h, i pendiente en m/m (+ rampa, - pendiente; el caso mas
    desfavorable para la parada es la BAJADA, i<0). [confirmar AN]."""
    v = float(vp)
    fl = FL_PARADA[_norm_vp(vp)]
    return v * TIEMPO_PERCEPCION_REACCION / 3.6 + v * v / (254.0 * (fl + i))


def kv_min_convexo(vp, i=0.0):
    """Parametro Kv MINIMO de acuerdo CONVEXO (cresta) por visibilidad de parada.
        Kv = Dp^2 / (2*(sqrt(h1)+sqrt(h2))^2)     (caso Dp < L, gobernante)
    h1=altura del ojo, h2=altura del obstaculo (3.1-IC). [confirmar AN]."""
    dp = distancia_parada(vp, i)
    den = 2.0 * (math.sqrt(ALTURA_OJO) + math.sqrt(ALTURA_OBSTACULO)) ** 2
    return dp * dp / den


def kv_min_concavo(vp, i=0.0):
    """Parametro Kv MINIMO de acuerdo CONCAVO (vaguada) por visibilidad nocturna
    (faros):  Kv = Dp^2 / (2*(h_faros + Dp*tan(beta)))   (caso Dp < L).
    [confirmar AN]."""
    dp = distancia_parada(vp, i)
    den = 2.0 * (ALTURA_FAROS + dp * math.tan(ANGULO_FAROS_RAD))
    return dp * dp / den


def limites_clotoide(radio):
    """Limites del parametro A de la clotoide (3.1-IC):
       - A >= R/3   (limite minimo por percepcion/estetica)
       - A <= R     (limite maximo recomendado; A>R la curva 'parece' recta)
    Devuelve (A_min, A_max). [confirmar AN]."""
    R = abs(float(radio))
    return R / 3.0, R


def longitud_min_clotoide_jerk(vp, radio, J=0.5):
    """Longitud MINIMA de clotoide por variacion de la aceleracion centrifuga
    (confort dinamico), 3.1-IC:
        L_min = Vp^3 / (46.656 * R * J)
    Vp en km/h, R en m, J variacion de aceleracion (m/s^3, def. 0,5). [confirmar AN]."""
    v = float(vp)
    return v ** 3 / (46.656 * abs(float(radio)) * J)


if __name__ == "__main__":
    print("Parametros 3.1-IC por Vp (predimensionado; [confirmar AN]):")
    print("%4s %8s %8s %8s %10s %10s" % ("Vp", "Rmin", "imax%", "Dp", "Kv_conv", "Kv_conc"))
    for v in VP_VALIDAS:
        print("%4d %8.0f %8.1f %8.1f %10.0f %10.0f" % (
            v, radio_minimo(v), pendiente_maxima(v) * 100,
            distancia_parada(v), kv_min_convexo(v), kv_min_concavo(v)))
