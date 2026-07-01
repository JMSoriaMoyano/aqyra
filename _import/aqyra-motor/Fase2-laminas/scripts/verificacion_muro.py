"""
Verificacion EC2 del MURO de carga:
  - Compresion con esbeltez (ec2_muro, metodo §12.6.5.2 + clasificacion §5.8.3.1)
  - Flexion fuera de plano (viento) -> armadura
  - Armadura minima de muro (§9.6)
  - Flecha fuera de plano (ELS)
El axil de diseño se toma como carga vertical total / longitud (evita la
singularidad local de la membrana en las esquinas de la base empotrada).
"""
import sys
import json
import ec2_muro
from verificacion_ec2 import armado_direccion, _to_native

GC = 1.50
C_NOM = 0.030
PHI = 0.012
LIM_DEF = 250.0   # flecha fuera de plano L/250


def verificar(model, results):
    info = results["info"]
    mp = model["materiales"][info["material"]]
    fck = mp["fck"]; fctm = mp["fctm"]; fcd = fck / GC
    t = info["espesor"]; H = info["H"]; L = info["L"]; beta = info["beta"]
    d = t - C_NOM - PHI / 2

    out = {"info": info, "equilibrio": results["equilibrio"]}

    # axil de diseño (ELU) por metro = carga vertical total / longitud
    N_Ed = results["equilibrio"]["aplicada_vert_ELU_kN"] * 1e3 / L
    # momento fuera de plano (viento) por metro: maximo
    q = results["muro"]["ELU"]["quads"]
    M_out = max(max(abs(qq["Mx"]), abs(qq["My"])) for qq in q)

    out["compresion"] = ec2_muro.comprobar_compresion(N_Ed, M_out, t, H, fck, beta)
    if not out["compresion"]["ok"]:
        out["compresion"]["dimensionado"] = ec2_muro.dimensionar(N_Ed, M_out, t, H, fck, beta)

    # flexion fuera de plano -> armadura horizontal (resiste flexion vertical del muro)
    out["flexion_fuera_plano"] = armado_direccion(M_out, d, fcd, fctm, t)

    # armadura minima de muro
    out["armadura_minima"] = ec2_muro.armadura_minima(t, fck)

    # flecha fuera de plano
    f_out = max(abs(p["dy"]) for p in results["muro"]["ELS_car"]["deformada"])
    out["flecha"] = {"L_m": H, "f_mm": f_out * 1e3, "lim_mm": H / LIM_DEF * 1e3,
                     "u": f_out / (H / LIM_DEF), "ok": f_out <= H / LIM_DEF}

    # veredicto
    out["veredicto"] = "CUMPLE" if (out["compresion"]["ok"] and out["flecha"]["ok"]) else "REVISAR"
    return _to_native(out)


if __name__ == "__main__":
    mp_ = sys.argv[1] if len(sys.argv) > 1 else "proyecto-muro/modelo_neutro.json"
    rp_ = sys.argv[2] if len(sys.argv) > 2 else "proyecto-muro/resultados.json"
    op_ = sys.argv[3] if len(sys.argv) > 3 else "proyecto-muro/verificacion.json"
    model = json.load(open(mp_, encoding="utf-8"))
    results = json.load(open(rp_, encoding="utf-8"))
    out = verificar(model, results)
    json.dump(out, open(op_, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    c = out["compresion"]
    print(f"MURO t={out['info']['espesor']*1e3:.0f}mm H={out['info']['H']}m  -> {out['veredicto']}")
    print(f"  COMPRESION: N_Ed={c['N_Ed_kN_m']:.0f} kN/m  lambda={c['lambda']:.0f} (lim {c['lambda_lim']:.0f}, "
          f"{'esbelto' if c['esbelto'] else 'no esbelto'})")
    print(f"    Phi={c['Phi']:.3f}  N_Rd={c['N_Rd_kN_m']:.0f} kN/m  aprov={c['u']*100:.0f}%  "
          f"{'OK' if c['ok'] else 'NO'}")
    if "dimensionado" in c:
        print(f"    -> espesor minimo {c['dimensionado']['t_min_mm']} mm")
    fx = out["flexion_fuera_plano"]
    print(f"  FLEXION fuera de plano: M={fx['m_Ed_kNm_m']:.1f} kN·m/m -> {fx['armado']}")
    am = out["armadura_minima"]
    print(f"  ARMADURA MINIMA (§9.6): vertical {am['As_v_min_cm2_m']:.1f} cm²/m, horizontal {am['As_h_min_cm2_m']:.1f} cm²/m")
    fl = out["flecha"]
    print(f"  FLECHA fuera de plano: {fl['f_mm']:.2f}/{fl['lim_mm']:.1f} mm ({fl['u']*100:.0f}%)")
    print(f"  EQUILIBRIO vert: error {out['equilibrio']['error_pct']:.2f}%")
