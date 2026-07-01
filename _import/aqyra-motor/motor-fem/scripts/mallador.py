"""
Mallador: modelo neutro estructural (C1 §2) -> malla FEM (C5).

Dos vias:
 - `desde_modelo_neutro(model)`: API de produccion. Barras 1D -> elementos barra;
   `superficies` -> malla estructurada de laminas. Estabiliza modelos planos.
 - `desde_pynite(m)`: ADAPTADOR ESPEJO para el *strangler*. Toma un `FEModel3D`
   de PyNite (el que construye cada solver de produccion) y lo replica en el
   nucleo propio, para la NO-REGRESION (mismo modelo, dos motores). Es la pieza
   clave del arnes: prueba que el nucleo propio reproduce a PyNite sin tocar los
   solvers de produccion.

SI (N, m). Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
from __future__ import annotations
import numpy as np
from fem_core import ModeloFEM, ElementoBarra, ElementoLamina


# --------------------------------------------------------------------------- #
#  Adaptador espejo: FEModel3D (PyNite) -> ModeloFEM (nucleo propio)          #
# --------------------------------------------------------------------------- #
def desde_pynite(m):
    """Replica un modelo PyNite ya construido en el nucleo propio.

    Devuelve (ModeloFEM, combos) listos para `resolver(combos)`. Reproduce
    nodos, apoyos, resortes, barras (seccion/material/releases/rotacion/cargas)
    y laminas (espesor/material/presiones). Soporta las cargas que emiten los
    solvers de produccion: distribuidas globales FX/FY/FZ uniformes, lineales
    locales Fy/Fz, puntuales y presiones de quad. Lanza ante una carga no
    contemplada (no falla en silencio)."""
    M = ModeloFEM()
    for name, nd in m.nodes.items():
        M.add_nodo(name, nd.X, nd.Y, nd.Z)
    for name, nd in m.nodes.items():
        vec = [nd.support_DX, nd.support_DY, nd.support_DZ,
               nd.support_RX, nd.support_RY, nd.support_RZ]
        if any(vec):
            M.set_apoyo(name, [bool(v) for v in vec])
        spr = [nd.spring_DX, nd.spring_DY, nd.spring_DZ,
               nd.spring_RX, nd.spring_RY, nd.spring_RZ]
        kv = [(float(s[0]) if s[0] not in (None, False) else 0.0) for s in spr]
        if any(kv):
            M.add_resorte(name, kv)
    for name, mb in m.members.items():
        sec = mb.section; mat = mb.material
        matd = {"E": mat.E, "G": mat.G, "nu": mat.nu, "rho": getattr(mat, "rho", 0.0)}
        secd = {"A": sec.A, "Iy": sec.Iy, "Iz": sec.Iz, "J": sec.J}
        el = ElementoBarra(name, mb.i_node.name, mb.j_node.name,
                           (mb.i_node.X, mb.i_node.Y, mb.i_node.Z),
                           (mb.j_node.X, mb.j_node.Y, mb.j_node.Z),
                           matd, secd, releases=list(mb.Releases), rotation=mb.rotation)
        L = el.L
        for dl in mb.DistLoads:
            direction, w1, w2, x1, x2, case = dl[0], dl[1], dl[2], dl[3], dl[4], dl[5]
            if direction in ("FX", "FY", "FZ"):
                if abs(w1 - w2) > 1e-9 or abs(x1) > 1e-9 or abs(x2 - L) > 1e-6:
                    raise NotImplementedError("carga global no uniforme/parcial no contemplada en FEM-0")
                key = {"FX": "qx", "FY": "qy", "FZ": "qz"}[direction]
                el.cargas.append({"caso": case, "tipo": "global_uniforme", key: w1})
            elif direction in ("Fy", "Fz"):
                el.cargas.append({"caso": case, "tipo": "lineal", "direccion": direction,
                                  "q1": w1, "q2": w2, "x1": x1, "x2": x2})
            else:
                raise NotImplementedError("direccion de carga de barra no contemplada: %s" % direction)
        for pl in mb.PtLoads:
            direction, P, x, case = pl[0], pl[1], pl[2], pl[3]
            if direction in ("Fy", "Fz"):
                el.cargas.append({"caso": case, "tipo": "puntual", "direccion": direction, "P": P, "x": x})
            elif direction == "Fx":
                el.cargas.append({"caso": case, "tipo": "axial_puntual", "P": P, "x": x})
            else:
                raise NotImplementedError("punto de carga no contemplado: %s" % direction)
        M.add_elemento(el)
    for name, q in m.quads.items():
        el = ElementoLamina(name, [q.i_node.name, q.j_node.name, q.m_node.name, q.n_node.name],
                            [(q.i_node.X, q.i_node.Y, q.i_node.Z),
                             (q.j_node.X, q.j_node.Y, q.j_node.Z),
                             (q.m_node.X, q.m_node.Y, q.m_node.Z),
                             (q.n_node.X, q.n_node.Y, q.n_node.Z)], q.t, q.E, q.nu)
        for pr in q.pressures:
            el.cargas.append({"caso": pr[1], "p": pr[0]})
        M.add_elemento(el)
    combos = {name: dict(lc.factors) for name, lc in m.load_combos.items()}
    return M, combos


# --------------------------------------------------------------------------- #
#  Mallador desde el modelo neutro estructural (C1 §2)                         #
# --------------------------------------------------------------------------- #
def desde_modelo_neutro(model, estabilizar_plano=True):
    """Construye el ModeloFEM desde el modelo neutro (barras 1D + superficies).

    Convencion: X,Y horizontales, Z vertical; `direccion:"GZ"` -> global uniforme
    en Z. Si el modelo es plano se coaccionan los GdL fuera de plano (como el
    solver de barras de produccion)."""
    M = ModeloFEM()
    mats = model["materiales"]; secs = model.get("secciones", {}); nodos = model["nodos"]
    for nid, n in nodos.items():
        M.add_nodo(nid, n["x"], n["y"], n["z"])
    for bid, b in model.get("barras", {}).items():
        ni, nj = nodos[b["ni"]], nodos[b["nj"]]
        matd = mats[b["material"]]; secd = secs[b["seccion"]]
        el = ElementoBarra(bid, b["ni"], b["nj"], (ni["x"], ni["y"], ni["z"]),
                           (nj["x"], nj["y"], nj["z"]),
                           {"E": matd["E"], "G": matd["G"], "nu": matd["nu"], "rho": matd.get("rho", 0.0)},
                           {"A": secd["A"], "Iy": secd["Iy"], "Iz": secd["Iz"], "J": secd["J"],
                            "Avy": secd.get("Avy"), "Avz": secd.get("Avz")},
                           releases=_releases(b.get("tipo")))
        M.add_elemento(el)
    for c in model.get("cargas", []):
        bid = c.get("barra")
        if bid is None:
            continue
        for el in M.elementos:
            if isinstance(el, ElementoBarra) and el.eid == bid:
                dirn = c.get("direccion", "GZ")
                key = {"GX": "qx", "GY": "qy", "GZ": "qz"}.get(dirn, "qz")
                el.cargas.append({"caso": c["caso"], "tipo": "global_uniforme", key: c["qz"]})
    for nid, n in nodos.items():
        ap = n.get("apoyo")
        if ap and any(ap):
            M.set_apoyo(nid, [bool(v) for v in ap])
    if estabilizar_plano:
        _estabilizar(M, nodos)
    return M


def _releases(tipo):
    if tipo in ("PIN_JOINED_MEMBER", "TRUSS", "articulado"):
        r = [False] * 12
        for i in (4, 5, 10, 11):
            r[i] = True
        return r
    return [False] * 12


def _estabilizar(M, nodos):
    xs = {round(n["x"], 9) for n in nodos.values()}
    ys = {round(n["y"], 9) for n in nodos.values()}
    zs = {round(n["z"], 9) for n in nodos.values()}
    out = None
    if len(ys) == 1:
        out = [1, 3, 5]
    elif len(zs) == 1:
        out = [2, 3, 4]
    elif len(xs) == 1:
        out = [0, 4, 5]
    if out is None:
        return
    for name in M.norden:
        vec = list(M.apoyos.get(name, [0] * 6))
        for i in out:
            vec[i] = 1
        M.set_apoyo(name, vec)
