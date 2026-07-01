"""
Orquestador del ENCEPADO DE 2 PILOTES (bielas y tirantes EC2 §6.5).
  IFC -> N_Ed (ELU) -> verificacion STM (solver de barras) -> esquema -> memoria
Memoria: NODE_PATH=$(npm root -g) node generate_memoria_encepado.js <carpeta>
"""
import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ifcopenshell
import ec2_strut_tie
from combinaciones import GAMMA_G_SUP, GAMMA_Q_SUP
import plots_encepado


def parse(ifc_path):
    ifc = ifcopenshell.open(ifc_path)
    mats = {}
    for mp in ifc.by_type("IfcMaterialProperties"):
        d = {p.Name: p.NominalValue.wrappedValue for p in mp.Properties
             if p.is_a("IfcPropertySingleValue") and p.NominalValue}
        mats[mp.Material.Name] = {"fck": d.get("CompressiveStrength")}
    cap = ifc.by_type("IfcStructuralSurfaceMember")[0]
    ps = {}
    for rel in getattr(cap, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition.is_a("IfcPropertySet"):
            pd = rel.RelatingPropertyDefinition
            ps[pd.Name] = {p.Name: p.NominalValue.wrappedValue for p in pd.HasProperties
                           if p.is_a("IfcPropertySingleValue") and p.NominalValue}
    g = ps["Pset_Estructurando_Encepado"]
    cargas = {p["Caso"]: p["N_N"] for n, p in ps.items() if n.startswith("Pset_Estructurando_Carga_Pilar")}
    matn = None
    for rel in getattr(cap, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            matn = rel.RelatingMaterial.Name
    return {"geom": g, "cargas": cargas, "fck": mats[matn]["fck"]}


def run(proj="proyecto-encepado", ifc=None):
    ifc = ifc or os.path.join(proj, "encepado.ifc")
    print(f"[1/3] IFC: {ifc}")
    model = parse(ifc)
    g = model["geom"]
    N_Ed = GAMMA_G_SUP * model["cargas"].get("G", 0) + GAMMA_Q_SUP * model["cargas"].get("Q", 0)
    print(f"      N_Ed(ELU) = {N_Ed/1e3:.0f} kN")
    print("[2/3] Verificacion bielas y tirantes (solver de barras)...")
    out = ec2_strut_tie.verificar_encepado(
        N_Ed, g["SeparacionPilotes"], g["Canto"], g["Ancho"], model["fck"],
        g["LadoPilar"], g["DiametroPilote"])
    out["N_Ed_kN"] = N_Ed / 1e3
    out["geom_in"] = g
    oks = [out["biela"]["ok"], out["nudo_CCC"]["ok"], out["nudo_CCT"]["ok"]]
    out["veredicto"] = "CUMPLE" if all(oks) else "REVISAR"
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    ce = out["celosia"]
    print(f"      celosia: T={ce['T_kN']:.0f} kN  C={ce['C_kN']:.0f} kN  (vs cerrado err {ce['err_pct']:.2f}%)")
    print(f"      tirante As={out['tirante']['As_req_cm2']:.1f} cm²  "
          f"biela {out['biela']['u']*100:.0f}%  CCC {out['nudo_CCC']['u']*100:.0f}%  "
          f"CCT {out['nudo_CCT']['u']*100:.0f}%  -> {out['veredicto']}")
    print("[3/3] Esquema STM...")
    for fpath in plots_encepado.generar(out, proj):
        print("      ", fpath)
    print("Memoria: NODE_PATH=$(npm root -g) node scripts/generate_memoria_encepado.js", proj)
    return out


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "proyecto-encepado"
    ifc = sys.argv[2] if len(sys.argv) > 2 else None
    run(proj, ifc)
