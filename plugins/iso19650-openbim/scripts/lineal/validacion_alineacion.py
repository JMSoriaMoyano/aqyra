"""
VALIDACION DE ALINEACION / GEORREFERENCIA (arnes propio, analogo al de
equilibrio/continuidad de red). PT 5.1 (Ola 5). NO calcula trazado: comprueba
COHERENCIA GEOMETRICA y georreferencia sobre el modelo neutro lineal emitido por
ifc_to_model_lineal.py.

Comprobaciones (BLOQUEANTES salvo donde se indica):
  1. UNIDADES: bloque `unidades` presente y SI (longitud = m).
  2. PK MONOTONO: pk_ini estrictamente creciente y CONTIGUO en planta, alzado y
     peralte (pk_ini[i+1] == pk_ini[i] + longitud[i]).
  3. CONTINUIDAD + TANGENCIA en planta: integrando cada segmento (curvatura lineal
     en s) desde su (x_ini,y_ini,acimut_ini), el punto y el acimut FINALES coinciden
     con el (x_ini,y_ini,acimut_ini) del segmento siguiente (sin saltos ni quiebros).
  4. CONTINUIDAD en alzado: la cota final de un segmento == cota inicial del
     siguiente; las pendientes ENCADENAN en los acuerdos (pend_fin == pend_ini).
  5. GEORREFERENCIA: bloque `georref` presente con CRS (EPSG) y origen E/N.
  6. RADIOS / CLOTOIDES (INFORMATIVO, Norma 3.1-IC): A de clotoide en [R/3, R];
     se reporta como AVISO, no bloquea (el dimensionado lo hace la disciplina).

Veredicto CUMPLE solo si no hay errores bloqueantes. Predimensionado/asistencia;
a revisar y firmar por tecnico competente (ICCP).

Uso:  python3 validacion_alineacion.py modelo_neutro_lineal.json [salida.json]
"""
import json
import math
import os
import sys

TOL_XY = 0.05      # m  (tolerancia de continuidad de puntos en planta)
TOL_AZ = 1e-3      # rad (tolerancia de tangencia)
TOL_Z = 1e-3       # m  (tolerancia de continuidad de cotas)
TOL_PK = 1e-3      # m  (tolerancia de contiguidad de PK)
TOL_G = 1e-6       # rad/m (tolerancia de encadenamiento de pendientes)


def _kappa(radio):
    return 0.0 if not radio else 1.0 / float(radio)


def _integrar(x0, y0, az0, radio_ini, radio_fin, longitud, n=400):
    """Integra (x,y,acimut) al final del segmento (misma ley que el generador)."""
    k0, k1 = _kappa(radio_ini), _kappa(radio_fin)
    L = float(longitud)
    if L <= 0:
        return x0, y0, az0
    x, y, az = x0, y0, az0
    ds = L / n
    for i in range(n):
        s = i * ds
        k = k0 + (k1 - k0) * (s / L)
        az_m = az + k * (ds / 2)
        x += math.cos(az_m) * ds
        y += math.sin(az_m) * ds
        az += k * ds + (k1 - k0) / L * ds * (ds / 2)
    return x, y, az


def _pk_contiguo(segs, longclave, etiqueta, errores):
    """PK monotono creciente y contiguo en una lista de segmentos."""
    for i in range(len(segs) - 1):
        a, b = segs[i], segs[i + 1]
        esperado = (a["pk_ini"] or 0.0) + (a.get(longclave) or 0.0)
        if b["pk_ini"] <= a["pk_ini"]:
            errores.append("%s: PK no creciente en seg %d->%d (%.3f -> %.3f)"
                           % (etiqueta, i, i + 1, a["pk_ini"], b["pk_ini"]))
        elif abs(b["pk_ini"] - esperado) > TOL_PK:
            errores.append("%s: PK no contiguo en seg %d->%d (esperado %.3f, "
                           "encontrado %.3f)" % (etiqueta, i, i + 1, esperado, b["pk_ini"]))


def validar(modelo):
    errores, avisos, info = [], [], []
    u = modelo.get("unidades", {})
    if not u:
        errores.append("Falta el bloque 'unidades'.")
    elif u.get("longitud") != "m":
        errores.append("Unidad de longitud no SI (esperado 'm'): %r" % u.get("longitud"))
    else:
        info.append("Unidades SI declaradas: %s" % u)

    ali = modelo.get("alineacion", {})
    planta = ali.get("planta", [])
    alzado = ali.get("alzado", [])
    peralte = ali.get("peralte", [])

    if not planta:
        errores.append("La alineacion no tiene PLANTA (sin IfcAlignmentHorizontal).")
    else:
        info.append("Planta: %d segmentos, L=%.3f m" % (len(planta), modelo.get("longitud_total", 0.0)))

    # 2) PK monotono y contiguo
    _pk_contiguo(planta, "longitud", "Planta", errores)
    _pk_contiguo(alzado, "longitud_h", "Alzado", errores)
    _pk_contiguo(peralte, "longitud", "Peralte", errores)

    # 3) continuidad + tangencia en planta (integracion)
    max_gap, max_kink = 0.0, 0.0
    for i in range(len(planta) - 1):
        a, b = planta[i], planta[i + 1]
        if a.get("x_ini") is None or b.get("x_ini") is None:
            avisos.append("Planta: seg %d sin coordenadas; no se comprueba continuidad." % i)
            continue
        xe, ye, aze = _integrar(a["x_ini"], a["y_ini"], a["acimut_ini_rad"],
                                a.get("radio_ini"), a.get("radio_fin"), a["longitud"])
        gap = math.hypot(xe - b["x_ini"], ye - b["y_ini"])
        kink = abs((aze - b["acimut_ini_rad"] + math.pi) % (2 * math.pi) - math.pi)
        max_gap, max_kink = max(max_gap, gap), max(max_kink, kink)
        if gap > TOL_XY:
            errores.append("Planta: SALTO de %.4f m entre seg %d y %d (PK %.1f)"
                           % (gap, i, i + 1, b["pk_ini"]))
        if kink > TOL_AZ:
            errores.append("Planta: QUIEBRO de tangencia %.5f rad entre seg %d y %d (PK %.1f)"
                           % (kink, i, i + 1, b["pk_ini"]))
    if planta:
        info.append("Planta: continuidad max %.4f m, tangencia max %.5f rad (umbral %.3f m / %.0e rad)"
                    % (max_gap, max_kink, TOL_XY, TOL_AZ))

    # 4) continuidad de alzado (cota + pendientes)
    max_dz, max_dg = 0.0, 0.0
    for i in range(len(alzado) - 1):
        a, b = alzado[i], alzado[i + 1]
        cota_fin = a["cota_ini"] + (a["pendiente_ini"] + a["pendiente_fin"]) / 2.0 * a["longitud_h"]
        dz = abs(cota_fin - b["cota_ini"])
        dg = abs(a["pendiente_fin"] - b["pendiente_ini"])
        max_dz, max_dg = max(max_dz, dz), max(max_dg, dg)
        if dz > TOL_Z:
            errores.append("Alzado: SALTO de cota %.4f m entre seg %d y %d (PK %.1f)"
                           % (dz, i, i + 1, b["pk_ini"]))
        if dg > TOL_G:
            errores.append("Alzado: pendiente no encadena entre seg %d y %d (%.5f vs %.5f)"
                           % (i, i + 1, a["pendiente_fin"], b["pendiente_ini"]))
    if alzado:
        info.append("Alzado: %d segmentos, continuidad cota max %.4f m, pendiente max %.6f"
                    % (len(alzado), max_dz, max_dg))

    # 5) georreferencia
    g = modelo.get("georref")
    if not g:
        errores.append("Falta la GEORREFERENCIA (sin IfcMapConversion/IfcProjectedCRS).")
    else:
        if not g.get("epsg"):
            errores.append("Georref sin CRS/EPSG (IfcProjectedCRS.Name).")
        if g.get("origen_e") is None or g.get("origen_n") is None:
            errores.append("Georref sin origen E/N (IfcMapConversion).")
        if not errores or g.get("epsg"):
            info.append("Georref: %s, origen E=%s N=%s, rotacion=%s rad"
                        % (g.get("epsg"), g.get("origen_e"), g.get("origen_n"),
                           g.get("rotacion_rad")))

    # 6) radios / clotoides frente a 3.1-IC (INFORMATIVO)
    for i, s in enumerate(planta):
        if s["tipo"] == "CLOTHOID" and s.get("A_clotoide"):
            R = s.get("radio_fin") or s.get("radio_ini")
            if R:
                A, R = s["A_clotoide"], abs(R)
                if A < R / 3.0 - 1e-6:
                    avisos.append("[3.1-IC] Clotoide seg %d: A=%.1f < R/3=%.1f (parametro corto)"
                                  % (i, A, R / 3.0))
                elif A > R + 1e-6:
                    avisos.append("[3.1-IC] Clotoide seg %d: A=%.1f > R=%.1f (parametro largo)"
                                  % (i, A, R))
        if s["tipo"] == "CIRCULARARC":
            R = abs(s.get("radio_ini") or 0.0)
            if R and R < 50.0:
                avisos.append("[3.1-IC] Curva seg %d: R=%.1f m muy ajustado (revisar Vp)" % (i, R))

    veredicto = "CUMPLE" if not errores else "NO CUMPLE"
    return {
        "veredicto": veredicto,
        "eje": (modelo.get("eje") or {}).get("nombre"),
        "resumen": {
            "planta": len(planta), "alzado": len(alzado), "peralte": len(peralte),
            "longitud_total_m": modelo.get("longitud_total"),
            "continuidad_max_m": round(max_gap, 4),
            "tangencia_max_rad": round(max_kink, 6),
            "georref": bool(g),
        },
        "errores": errores, "avisos": avisos, "info": info,
    }


def main(path, out=None):
    with open(path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    res = validar(modelo)
    print("=" * 64)
    print("VALIDACION DE ALINEACION --", os.path.basename(path))
    print("=" * 64)
    for i in res["info"]:
        print("  i ", i)
    for w in res["avisos"]:
        print("  ! ", w)
    for e in res["errores"]:
        print("  X ", e)
    print("\nVEREDICTO:", res["veredicto"], "| eje:", res["eje"],
          "| resumen:", res["resumen"])
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2, ensure_ascii=False)
        print("Verificacion escrita en", out)
    return 0 if res["veredicto"] == "CUMPLE" else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
