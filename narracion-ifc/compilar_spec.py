#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compilar_spec.py  --  Expansor determinista del compilador narracion->IFC (v0.2)

spec de alto nivel (macros) -> spec canonico (coordenadas) + validacion.
    python3 compilar_spec.py  entrada.alto.json  salida.spec.json

Macros: niveles {plantas,altura,base}; edificios [{ancho,largo,luz_max | luz_max_x/luz_max_y,
seccion_pilar,espesor_muro,espesor_forjado,material,pilares,muros_perimetrales,forjados}];
reticulas_pilares; y pilares/muros/losas/rampas canonicos (passthrough).
"""
import sys, json, math
from jsonschema import validate, ValidationError

HERE = __file__.rsplit("/", 1)[0]
DEF_SECCION = [0.40, 0.40]; DEF_ESP_MURO = 0.25; DEF_ESP_FORJ = 0.30; DEF_MAT = "HA-30"


def _linspace(a, b, n):
    return [a, b] if n <= 1 else [a + (b - a) * k / n for k in range(n + 1)]

def resolver_niveles(nv):
    if isinstance(nv, list):
        return sorted([{"nombre": n["nombre"], "cota": float(n["cota"])} for n in nv], key=lambda x: x["cota"])
    plantas = int(nv["plantas"]); H = float(nv.get("altura", 3.0)); base = float(nv.get("base", 0.0))
    nombres = nv.get("nombres"); out = []
    for i in range(plantas):
        nombre = nombres[i] if nombres and i < len(nombres) else ("Planta Baja" if i == 0 else f"Planta {i}")
        out.append({"nombre": nombre, "cota": base + i * H})
    return out

def _alturas(niveles):
    cotas = [n["cota"] for n in niveles]
    h = [cotas[i+1]-cotas[i] for i in range(len(cotas)-1)]; h.append(h[-1] if h else 3.0); return h

def _objetivo(spec_niv, niveles):
    if spec_niv in (None, "todas"): return list(range(len(niveles)))
    nombres = [n["nombre"] for n in niveles]; return [nombres.index(x) for x in spec_niv if x in nombres]


def expandir_edificio(ed, niveles, pilares, muros, losas):
    pref = ed.get("nombre", "Ed"); ox, oy = ed.get("origen", [0., 0.])
    W = float(ed["ancho"]); D = float(ed["largo"])
    sec = ed.get("seccion_pilar", DEF_SECCION); e_muro = float(ed.get("espesor_muro", DEF_ESP_MURO))
    e_forj = float(ed.get("espesor_forjado", DEF_ESP_FORJ)); material = ed.get("material", DEF_MAT)
    q_pil = ed.get("pilares", True); q_mur = ed.get("muros_perimetrales", True); q_for = ed.get("forjados", True)
    lux = ed.get("luz_max"); luxx = ed.get("luz_max_x", lux); luxy = ed.get("luz_max_y", lux)

    if luxx or luxy:
        xs = _linspace(ox, ox+W, max(1, math.ceil(W/float(luxx)))) if luxx else [ox, ox+W]
        ys = _linspace(oy, oy+D, max(1, math.ceil(D/float(luxy)))) if luxy else [oy, oy+D]
        rejilla = [(x, y) for x in xs for y in ys]
    else:
        rejilla = [(ox,oy),(ox+W,oy),(ox+W,oy+D),(ox,oy+D)]

    h = _alturas(niveles); objetivo = _objetivo(ed.get("niveles"), niveles)
    estr = [i for i in objetivo if i < len(niveles)-1] or objetivo[:-1] or objetivo
    esquinas = [(ox,oy),(ox+W,oy),(ox+W,oy+D),(ox,oy+D)]
    for i in estr:
        nivel = niveles[i]["nombre"]
        if q_pil:
            for k,(x,y) in enumerate(rejilla, 1):
                pilares.append({"nombre": f"{pref}_Pil{k}_N{i}", "nivel": nivel,
                                "pos":[round(x,4),round(y,4)], "seccion": sec, "altura": h[i], "material": material})
        if q_mur:
            for s,(a,b) in enumerate(zip(esquinas, esquinas[1:]+esquinas[:1]), 1):
                muros.append({"nombre": f"{pref}_Muro{s}_N{i}", "nivel": nivel,
                              "inicio":[round(a[0],4),round(a[1],4)], "fin":[round(b[0],4),round(b[1],4)],
                              "espesor": e_muro, "altura": h[i], "material": material, "exterior": True})
    if q_for:
        for i in objetivo:
            if i == 0: continue
            losas.append({"nombre": f"{pref}_Forjado_N{i}", "nivel": niveles[i]["nombre"],
                          "contorno":[[ox,oy],[ox+W,oy],[ox+W,oy+D],[ox,oy+D]], "espesor": e_forj, "material": material})


def expandir_reticula(rt, niveles, pilares):
    pref = rt.get("nombre","R"); ox, oy = rt.get("origen",[0.,0.])
    nx, ny = int(rt["nx"]), int(rt["ny"]); sx, sy = float(rt["sep_x"]), float(rt["sep_y"])
    sec = rt.get("seccion", DEF_SECCION); material = rt.get("material", DEF_MAT)
    h = _alturas(niveles); objetivo = _objetivo(rt.get("niveles"), niveles)
    estr = [i for i in objetivo if i < len(niveles)-1] or objetivo
    for i in estr:
        nivel = niveles[i]["nombre"]; k = 1
        for ix in range(nx):
            for iy in range(ny):
                pilares.append({"nombre": f"{pref}_Pil{k}_N{i}", "nivel": nivel,
                                "pos":[round(ox+ix*sx,4),round(oy+iy*sy,4)], "seccion": sec, "altura": h[i], "material": material})
                k += 1


def compilar(alto):
    niveles = resolver_niveles(alto["niveles"])
    pilares = list(alto.get("pilares", [])); muros = list(alto.get("muros", []))
    losas = list(alto.get("losas", [])); rampas = list(alto.get("rampas", []))
    escaleras = list(alto.get("escaleras", []))
    elementos = list(alto.get("elementos", []))
    for ed in alto.get("edificios", []): expandir_edificio(ed, niveles, pilares, muros, losas)
    for rt in alto.get("reticulas_pilares", []): expandir_reticula(rt, niveles, pilares)
    canon = {"proyecto": alto.get("proyecto","Proyecto"), "esquema": alto.get("esquema","IFC4"),
             "unidades":"m", "niveles": niveles, "pilares": pilares, "muros": muros, "losas": losas}
    if rampas: canon["rampas"] = rampas
    if escaleras: canon["escaleras"] = escaleras
    if elementos: canon["elementos"] = elementos
    if "georef" in alto: canon["georef"] = alto["georef"]
    return canon


def comprobar_geometria(canon):
    errs = []; nombres = {n["nombre"] for n in canon["niveles"]}
    for w in canon["muros"]:
        if math.hypot(w["fin"][0]-w["inicio"][0], w["fin"][1]-w["inicio"][1]) < 1e-6:
            errs.append(f"muro '{w['nombre']}' de longitud nula")
        if w["nivel"] not in nombres: errs.append(f"muro '{w['nombre']}' nivel inexistente '{w['nivel']}'")
    for c in canon["pilares"]:
        if c["nivel"] not in nombres: errs.append(f"pilar '{c['nombre']}' nivel inexistente '{c['nivel']}'")
    for s in canon["losas"]:
        if s["nivel"] not in nombres: errs.append(f"losa '{s['nombre']}' nivel inexistente '{s['nivel']}'")
        if len(s["contorno"]) < 3: errs.append(f"losa '{s['nombre']}' contorno <3 vertices")
    for r in canon.get("rampas", []):
        d = math.dist(r["inicio"], r["fin"]) if hasattr(math,"dist") else math.sqrt(sum((a-b)**2 for a,b in zip(r["inicio"],r["fin"])))
        if d < 1e-6: errs.append(f"rampa '{r['nombre']}' de longitud nula")
        if abs(r["fin"][2]-r["inicio"][2]) < 1e-6: errs.append(f"rampa '{r['nombre']}' sin desnivel (no sube)")
    return errs


def main():
    if len(sys.argv) < 3:
        print("Uso: python3 compilar_spec.py entrada.alto.json salida.spec.json"); sys.exit(1)
    alto = json.load(open(sys.argv[1], encoding="utf-8"))
    canon = compilar(alto)
    schema = json.load(open(f"{HERE}/spec.schema.json", encoding="utf-8"))
    try:
        validate(instance=canon, schema=schema)
    except ValidationError as e:
        print("ERROR de esquema:", e.message); sys.exit(2)
    errs = comprobar_geometria(canon)
    if errs:
        print("ERRORES geometricos:"); [print("  -", e) for e in errs]; sys.exit(3)
    json.dump(canon, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"OK  spec canonico -> {sys.argv[2]}")
    print(f"    niveles={len(canon['niveles'])}  pilares={len(canon['pilares'])}  "
          f"muros={len(canon['muros'])}  losas={len(canon['losas'])}  rampas={len(canon.get('rampas',[]))}")

if __name__ == "__main__":
    main()
