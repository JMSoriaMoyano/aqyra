"""
Idealizacion por EMPARRILLADO (grillage) barra+barra de un tablero de vigas.

Construye el modelo de analisis C5 (modelo neutro estructural + claves FEM) a
partir de la geometria del tablero: N vigas longitudinales (sobre el eje, con su
separacion transversal) discretizadas en barras, unidas por RIOSTRAS/losa
transversal (barras transversales). El eje puede venir del Alignment (lista de
puntos por PK) o ser recto. Apoyos isostaticos en estribos.

Frontera (C5 / C1): NO calcula la mecanica; entrega el modelo para `motor-fem`.
La losa colaborante se incorpora a la INERCIA de la viga (seccion en T/doble-T)
-- no se modela como lamina (decision: emparrillado barra+barra, [confirmar AN]).

SI (N, m). Predimensionado/asistencia; revisar y firmar por tecnico competente.
"""
from __future__ import annotations


def _ejes_vigas(n_vigas, sep, eje=None, L=None, ne=None):
    if eje is None:
        eje = [(L * i / ne, 0.0, 0.0) for i in range(ne + 1)]
    y0 = -(n_vigas - 1) * sep / 2.0
    vigas = []
    for g in range(n_vigas):
        yg = y0 + g * sep
        vigas.append([(x, y + yg, z) for (x, y, z) in eje])
    return vigas


def construir_emparrillado(tablero):
    """tablero = {'L','n_vigas','sep','ne','n_riostras','material','viga_sec',
       'riostra_sec','eje'(opc)}. Devuelve (model_C5, meta)."""
    L = tablero['L']; n = tablero['n_vigas']; sep = tablero['sep']
    ne = tablero['ne']; nr = tablero.get('n_riostras', 2); eje = tablero.get('eje')
    vigas_xyz = _ejes_vigas(n, sep, eje=eje, L=L, ne=ne)

    materiales = {'HORM': dict(tablero['material'])}
    secciones = {'VIGA': {k: tablero['viga_sec'][k] for k in ('A', 'Iy', 'Iz', 'J')},
                 'RIOSTRA': {k: tablero['riostra_sec'][k] for k in ('A', 'Iy', 'Iz', 'J')}}
    for s in secciones.values():
        s.setdefault('Avz', None); s.setdefault('Avy', None)

    nodos = {}; barras = {}; girders = []
    for g, linea in enumerate(vigas_xyz):
        nids = []
        for i, (x, y, z) in enumerate(linea):
            nid = "N_%d_%d" % (g, i)
            nodos[nid] = {"x": float(x), "y": float(y), "z": float(z), "apoyo": [0, 0, 0, 0, 0, 0]}
            nids.append(nid)
        girders.append(nids)
        for i in range(ne):
            barras["G_%d_%d" % (g, i)] = {"ni": nids[i], "nj": nids[i + 1],
                                          "seccion": "VIGA", "material": "HORM", "tipo": "viga"}

    estaciones = sorted(set([0, ne] + [round(ne * k / (nr - 1)) for k in range(nr)])) if nr >= 2 else [0, ne]
    for est in estaciones:
        for g in range(n - 1):
            barras["R_%d_%d" % (g, est)] = {"ni": girders[g][est], "nj": girders[g + 1][est],
                                            "seccion": "RIOSTRA", "material": "HORM", "tipo": "riostra"}

    centro = n // 2; nodos_apoyo = []
    for g in range(n):
        a = girders[g][0]; b = girders[g][ne]
        nodos[a]["apoyo"] = [1 if g == centro else 0, 1, 1, 1, 0, 0]
        nodos[b]["apoyo"] = [0, 1, 1, 1, 0, 0]
        nodos_apoyo += [a, b]

    model = {"unidades": {"longitud": "m", "fuerza": "N", "momento": "N*m"},
             "materiales": materiales, "secciones": secciones,
             "nodos": nodos, "barras": barras, "cargas": []}
    meta = {"girders": girders, "nodos_apoyo": nodos_apoyo, "estaciones_riostra": estaciones,
            "caminos": [list(girders[g]) for g in range(n)], "ne": ne, "n_vigas": n,
            "L": L, "sep": sep, "centro": centro}
    return model, meta
