"""
Orquestador INTEGRADO del edificio (caso 10, cierre de INC-03).

Cadena:
  IFC multi-elemento -> clasificador (itera TODO el IFC, enruta cada elemento)
    -> sub-IFC por subsistema (su PORCION del modelo)
    -> run_all* de cada modulo (barras / mixtas / laminas / cimentaciones)
       en SUBPROCESO (aisla los modulos homonimos: solver_*, combinaciones,
       plots_*, run_all*, verificacion_* de cada paquete)
    -> consolidacion de resultados + indice integrado del edificio.

Cada run_all* se ejecuta sobre su sub-IFC, reproduciendo las condiciones de
sistema unico de los casos 1/5/6/7 (y evitando los by_type[0] de cada parser).

Uso:
  python3 run_all_edificio.py <proj_dir> <ifc> [--solo SUBSISTEMA] [--no-run]
    --solo  : ejecuta solo ese subsistema (util en sandbox por el limite de 45 s)
    --no-run: clasifica y extrae sub-IFC pero no lanza los run_all (solo enrutado)
  Sin --solo, ejecuta los 4 subsistemas y consolida.
"""
import sys
import os
import json
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import clasificador

# run_all especial para la cimentacion (predimensionado con ampliacion si procede)
RUN_OVERRIDE = {"cimentaciones/run_all_zapata.py": "cimentaciones/run_zapata_predim.py"}


def _resumen_subsistema(sub_id, modulo, vpath):
    """Extrae veredicto + aprovechamientos clave de cada verificacion.json."""
    if not os.path.exists(vpath):
        return {"veredicto": "SIN RESULTADO", "detalle": {}}
    o = json.load(open(vpath, encoding="utf-8"))
    d = {}
    ver = o.get("veredicto", "?")
    if modulo == "barras":
        elems = o.get("barras", {})
        ver = "CUMPLE" if all(b.get("veredicto") == "CUMPLE" for b in elems.values()) else "REVISAR"
        d = {bid: {"veredicto": b["veredicto"], "aprov_max_pct": round(b["aprovechamiento_max"] * 100, 1)}
             for bid, b in elems.items()}
    elif modulo == "mixtas":
        fm = o.get("flexion_mixta", {}); cx = o.get("conexion", {}); fl = o.get("flecha", {})
        d = {"M_Ed_kNm": round(fm.get("M_Ed_kNm", 0), 1), "M_Rd_kNm": round(fm.get("M_Rd_kNm", 0), 1),
             "u_flexion_pct": round(fm.get("M_Ed_kNm", 0) / fm.get("M_Rd_kNm", 1) * 100, 1),
             "grado_conexion_eta": round(cx.get("grado_eta", 0), 2),
             "u_flecha_pct": round(fl.get("u_total", 0) * 100, 1)}
    elif modulo == "laminas":
        es = o.get("esbeltez", {}); co = o.get("compresion", {})
        d = {"lambda": round(co.get("lambda", 0), 0), "esbelto": co.get("esbelto"),
             "M_Ed_kNm_m": round(es.get("M_Ed_kNm_m", 0), 1), "M_Rd_kNm_m": round(es.get("M_Rd_kNm_m", 0), 1),
             "u_NM_pct": round(es.get("u", 0) * 100, 1), "armado": es.get("armado")}
    elif modulo == "cimentaciones":
        g = o.get("geotecnia", {}); pz = o.get("predimensionado_zapata", {})
        d = {"sigma_ef_kPa": round(g.get("sigma_ef_kPa", 0), 0), "Rd_kPa": round(g.get("Rd_kPa", 0), 0),
             "u_Rd_pct": round(g.get("u_Rd", 0) * 100, 1),
             "u_punz_pct": round(o.get("punzonamiento", {}).get("u_vRdc", 0) * 100, 1),
             "u_cortante_pct": round(o.get("cortante", {}).get("u", 0) * 100, 1),
             "u_fisuracion_pct": round(o.get("fisuracion", {}).get("u", 0) * 100, 1),
             "zapata": pz}
    return {"veredicto": ver, "detalle": d}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    proj = args[0]
    ifc = args[1]
    solo = None
    for f in flags:
        if f.startswith("--solo"):
            i = sys.argv.index(f)
            solo = sys.argv[i + 1] if i + 1 < len(sys.argv) else None
    no_run = "--no-run" in flags
    os.makedirs(proj, exist_ok=True)
    sub_dir = os.path.join(proj, "subifc")
    os.makedirs(sub_dir, exist_ok=True)

    print("=" * 70)
    print("ORQUESTADOR INTEGRADO DEL EDIFICIO  (caso 10 -- cierre de INC-03)")
    print("=" * 70)
    print("[A] Clasificacion/enrutado multi-elemento (itera TODO el IFC)...")
    res = clasificador.clasificar(ifc)
    json.dump(res["modelo_neutro"], open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    rut = {k: res[k] for k in ("ifc", "n_barras", "n_superficies", "asociaciones", "elementos", "subsistemas")}
    json.dump(rut, open(os.path.join(proj, "clasificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("    %-18s %-22s %-14s %s" % ("ELEMENTO", "CLASE", "MODULO", "SUBSISTEMA"))
    for e in res["elementos"]:
        print("    %-18s %-22s %-14s %s" % (e["elemento"], e["clase"], e["modulo"], e["subsistema"]))

    print("[B] Extraccion de sub-IFC por subsistema...")
    subs = res["subsistemas"]
    for sub in subs:
        p = os.path.join(sub_dir, "%s.ifc" % sub["id"])
        sub["_subifc"] = p
        if solo and sub["id"] != solo:
            continue   # con --solo solo se extrae el sub-IFC necesario
        clasificador.extraer_subifc(ifc, sub["curves"], sub["surfaces"], sub["actions"], p)
        print("    %-26s -> %s" % (sub["id"], os.path.basename(p)))

    if no_run:
        print("[--no-run] enrutado y sub-IFC listos; no se lanzan los run_all.")
        return

    print("[C] Ejecucion de cada subsistema (subproceso aislado)...")
    resumen = {}
    for sub in subs:
        if solo and sub["id"] != solo:
            continue
        runner = RUN_OVERRIDE.get(sub["run_all"], sub["run_all"])
        sp = os.path.join(proj, sub["id"])
        os.makedirs(sp, exist_ok=True)
        cmd = [sys.executable, os.path.join(HERE, runner), sp, sub["_subifc"]]
        print("    -> %s  (%s)" % (sub["id"], runner))
        r = subprocess.run(cmd, capture_output=True, text=True)
        tail = (r.stdout.strip().splitlines() or [""])[-1]
        print("       %s" % tail)
        if r.returncode != 0:
            print("       STDERR:", (r.stderr.strip().splitlines() or [""])[-1])

    print("[D] Consolidacion / indice integrado del edificio...")
    for sub in subs:
        if solo and sub["id"] != solo:
            continue
        vpath = os.path.join(proj, sub["id"], "verificacion.json")
        resumen[sub["id"]] = {"modulo": sub["modulo"], "descripcion": sub["descripcion"],
                              **_resumen_subsistema(sub["id"], sub["modulo"], vpath)}
    # si es --solo, fusiona con un resumen previo si existe
    rp = os.path.join(proj, "resumen_edificio.json")
    if solo and os.path.exists(rp):
        prev = json.load(open(rp, encoding="utf-8"))
        prev.update(resumen)
        resumen = prev
    json.dump(resumen, open(rp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("\n    %-28s %-14s %s" % ("SUBSISTEMA", "MODULO", "VEREDICTO"))
    for sid, r in resumen.items():
        print("    %-28s %-14s %s" % (sid, r["modulo"], r["veredicto"]))
    glob_ok = all(r["veredicto"] == "CUMPLE" for r in resumen.values())
    print("\n    EDIFICIO:", "TODOS LOS SUBSISTEMAS CUMPLEN" if glob_ok else "ALGUN SUBSISTEMA A REVISAR")
    print("    (predimensionado -- a revisar y firmar por tecnico competente)")


if __name__ == "__main__":
    main()
