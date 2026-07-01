"""
CASO R4 - EDIFICIO FISICO COMPLETO (el "caso 10 real"). Cuarto caso de la
DIRECCION 2: un UNICO IFC FISICO (entregable BIM real) por plantas con los CUATRO
subsistemas del caso 10 como elementos FISICOS con geometria Body
(IfcExtrudedAreaSolid, extrusion +Z), IfcMaterial(ProfileSet/LayerSet) y SIN
entidades de analisis ni cargas. El "puente" debe derivar TODO el modelo analitico
(barras + superficies horizontales/verticales + cimientos + asociaciones) desde la
geometria y enrutar CADA elemento a su modulo.

Subsistemas (geometria y datos = caso 10, para validar contra resultados conocidos),
separados en planta:
  A) PORTICO de acero -> 2 IfcColumn HEB 240 + 1 IfcBeam IPE 360 (S275), luz 6 m,
     altura 4 m. Perfil por IfcMaterialProfileSetUsage -> IfcIShapeProfileDef.
     Carga de hipotesis de linea en el dintel G=12 / Q=10 kN/m (Pset).
  B) FORJADO MIXTO / viga mixta -> 1 IfcSlab (losa C25/30 t=0,12) sobre 1 IfcBeam
     IPE 400 (S275), L=8 m, separacion 3,0 m. Espesor por IfcMaterialLayerSet.
     Conectores/chapa y cargas por fase en Pset (sin entidad fisica estandar,
     como en el caso 6/10).
  C) MURO de carga -> 1 IfcWall C30/37 (H=3,0 t=0,20, faja 1,0 m), plano medio
     VERTICAL. Carga de cabeza N_G=250 / N_Q=120 kN/m con e=25 mm (Pset).
  D) CIMENTACION -> 1 IfcColumn de hormigon C30/37 (rectangular 0,40) + 1
     IfcFooting (zapata C30/37 2,5x2,5 canto 0,60) sobre lecho Winkler. Cadena
     pilar->cimiento desde la geometria (pie del pilar sobre la huella). Terreno
     (k_s, R_d) y bajada de carga (N_G=700/N_Q=250 + M=80/40) en Pset.

Estructura espacial por PLANTAS: IfcProject -> IfcSite -> IfcBuilding ->
IfcBuildingStorey x3 (Cimentacion / Planta Baja / Planta Primera).

Unidades SI (m, N, Pa). Plano XY horizontal, Z vertical, gravedad -Z.
"""
import os
import math
import ifcopenshell
import ifcopenshell.guid

# --- materiales ---
STEEL = dict(name="S275", fy=275e6, E=210e9, nu=0.3, rho=7850.0, G=80.77e9)
C25 = dict(name="C25/30", fck=25e6, fctm=2.6e6, E=31.0e9, nu=0.2, rho=2500.0, G=31.0e9 / 2.4)
C30 = dict(name="C30/37", fck=30e6, fctm=2.9e6, E=32.84e9, nu=0.2, rho=2500.0, G=32.84e9 / 2.4)

# --- perfiles de acero (= caso 10) ---
HEB240 = dict(name="HEB 240", b=0.240, h=0.240, tw=0.010, tf=0.017, r=0.021)
IPE360 = dict(name="IPE 360", b=0.170, h=0.360, tw=0.008, tf=0.0127, r=0.018)
IPE400 = dict(name="IPE 400", b=0.180, h=0.400, tw=0.0086, tf=0.0135, r=0.021)

# --- geometria (= caso 10) ---
H_PORT, L_PORT = 4.0, 6.0       # portico altura / luz
L_MIX, SEP_MIX = 8.0, 3.0       # viga mixta luz / separacion
T_SLAB = 0.12                   # canto losa mixta
H_WALL, T_WALL, LW_WALL = 3.0, 0.20, 1.0   # muro de carga
B_FOOT, L_FOOT, T_FOOT = 2.5, 2.5, 0.60    # zapata
C_PILAR = 0.40                  # lado del pilar de hormigon
MESH_FOOT = 0.125

# --- hipotesis de carga (= caso 10) ---
G_DINTEL, Q_DINTEL = 12.0, 10.0          # kN/m, dintel del portico
# mixta (kN/m2): hormigon fresco, ejecucion, carga muerta, uso
G_LOSA, QC_EJEC, G2_MIX, Q_USO = 2.5, 0.75, 2.0, 5.0
G_TOP_W, Q_TOP_W, E_CAB_W = 250.0, 120.0, 0.025   # muro carga de cabeza
KS, RD_SUELO = 40e6, 250e3
N_G_ZAP, N_Q_ZAP, M_G_ZAP, M_Q_ZAP = 700e3, 250e3, 80e3, 40e3

# separacion en planta de los subsistemas
X_PORT = 0.0
Y_MIX = 20.0
X_WALL = 30.0
X_FOOT = 40.0

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-R4.ifc")

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new


def dirn(v):
    return f.create_entity("IfcDirection", DirectionRatios=tuple(float(x) for x in v))


def pt(c):
    return f.create_entity("IfcCartesianPoint", Coordinates=tuple(float(x) for x in c))


def a2p3d(loc, axis=None, ref=None):
    kw = {"Location": pt(loc)}
    if axis is not None:
        kw["Axis"] = dirn(axis)
    if ref is not None:
        kw["RefDirection"] = dirn(ref)
    return f.create_entity("IfcAxis2Placement3D", **kw)


def local_placement(rel_to, a2p):
    return f.create_entity("IfcLocalPlacement", PlacementRelTo=rel_to, RelativePlacement=a2p)


# ---- unidades + contextos ----
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=a2p3d((0., 0., 0.)))
body = f.create_entity("IfcGeometricRepresentationSubContext", ContextIdentifier="Body",
                       ContextType="Model", ParentContext=ctx, TargetView="MODEL_VIEW")
project = f.create_entity("IfcProject", GlobalId=guid(),
                          Name="Caso R4 - Edificio fisico completo (puente IFC->analitico multi-elemento)",
                          UnitsInContext=ua, RepresentationContexts=[ctx])

# ---- estructura espacial por PLANTAS ----
site_pl = local_placement(None, a2p3d((0., 0., 0.)))
site = f.create_entity("IfcSite", GlobalId=guid(), Name="Parcela", ObjectPlacement=site_pl,
                       CompositionType="ELEMENT")
bld_pl = local_placement(site_pl, a2p3d((0., 0., 0.)))
building = f.create_entity("IfcBuilding", GlobalId=guid(), Name="Edificio R4", ObjectPlacement=bld_pl,
                           CompositionType="ELEMENT")


def storey(name, elev):
    pl = local_placement(bld_pl, a2p3d((0., 0., 0.)))   # placement en origen -> coords absolutas
    return f.create_entity("IfcBuildingStorey", GlobalId=guid(), Name=name,
                           ObjectPlacement=pl, CompositionType="ELEMENT", Elevation=float(elev)), pl


sto_cim, plc_cim = storey("Cimentacion", -0.60)
sto_baja, plc_baja = storey("Planta Baja", 0.0)
sto_prim, plc_prim = storey("Planta Primera", 4.0)
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=project, RelatedObjects=[site])
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=site, RelatedObjects=[building])
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=building,
                RelatedObjects=[sto_cim, sto_baja, sto_prim])


def material(M):
    m = f.create_entity("IfcMaterial", Name=M["name"])
    pairs = [("YoungModulus", M["E"]), ("ShearModulus", M["G"]),
             ("PoissonRatio", M["nu"]), ("MassDensity", M["rho"])]
    if "fy" in M:
        pairs.append(("YieldStress", M["fy"]))
    if "fck" in M:
        pairs += [("CompressiveStrength", M["fck"]), ("TensileStrength", M["fctm"])]
    props = [f.create_entity("IfcPropertySingleValue", Name=k,
                NominalValue=f.create_entity("IfcReal", wrappedValue=float(v))) for k, v in pairs]
    f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=m, Properties=props)
    return m


mat_steel = material(STEEL)
mat_c25 = material(C25)
mat_c30 = material(C30)


def prop(name, val):
    nv = (f.create_entity("IfcText", wrappedValue=val) if isinstance(val, str)
          else f.create_entity("IfcReal", wrappedValue=float(val)))
    return f.create_entity("IfcPropertySingleValue", Name=name, NominalValue=nv)


def pset_for(obj, name, props):
    ps = f.create_entity("IfcPropertySet", GlobalId=guid(), Name=name,
                         HasProperties=[prop(k, v) for k, v in props.items()])
    f.create_entity("IfcRelDefinesByProperties", GlobalId=guid(),
                    RelatedObjects=[obj], RelatingPropertyDefinition=ps)


def ishape(P):
    return f.create_entity("IfcIShapeProfileDef", ProfileType="AREA", ProfileName=P["name"],
                           Position=f.create_entity("IfcAxis2Placement2D",
                               Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0.))),
                           OverallWidth=P["b"], OverallDepth=P["h"],
                           WebThickness=P["tw"], FlangeThickness=P["tf"], FilletRadius=P["r"])


def rect_profile(name, bx, ly, cx, cy):
    return f.create_entity("IfcRectangleProfileDef", ProfileType="AREA", ProfileName=name,
                           Position=f.create_entity("IfcAxis2Placement2D",
                               Location=f.create_entity("IfcCartesianPoint", Coordinates=(cx, cy))),
                           XDim=bx, YDim=ly)


def member(kind, name, p0, p1, profile, mat, refdir, sto_pl):
    """IfcColumn/IfcBeam fisico: barrido del perfil a lo largo del eje p0->p1."""
    v = [p1[i] - p0[i] for i in range(3)]
    L = math.sqrt(sum(c * c for c in v))
    axis = [c / L for c in v]
    solid = f.create_entity("IfcExtrudedAreaSolid", SweptArea=profile,
                            Position=a2p3d((0., 0., 0.)), ExtrudedDirection=dirn((0., 0., 1.)), Depth=L)
    shape = f.create_entity("IfcShapeRepresentation", ContextOfItems=body,
                            RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[solid])
    pds = f.create_entity("IfcProductDefinitionShape", Representations=[shape])
    pl = local_placement(sto_pl, a2p3d(p0, axis=axis, ref=refdir))
    cls = "IfcColumn" if kind == "col" else "IfcBeam"
    el = f.create_entity(cls, GlobalId=guid(), Name=name, ObjectPlacement=pl, Representation=pds,
                         PredefinedType="COLUMN" if kind == "col" else "BEAM")
    mp = f.create_entity("IfcMaterialProfile", Name=name + "_perfil", Material=mat, Profile=profile)
    mps = f.create_entity("IfcMaterialProfileSet", Name=profile.ProfileName, MaterialProfiles=[mp])
    usage = f.create_entity("IfcMaterialProfileSetUsage", ForProfileSet=mps, CardinalPoint=5)
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[el], RelatingMaterial=usage)
    return el


def layerset(obj, mat, thickness, name):
    layer = f.create_entity("IfcMaterialLayer", Material=mat, LayerThickness=thickness, Name=name)
    mls = f.create_entity("IfcMaterialLayerSet", MaterialLayers=[layer], LayerSetName=name + "_capas")
    usage = f.create_entity("IfcMaterialLayerSetUsage", ForLayerSet=mls, LayerSetDirection="AXIS3",
                            DirectionSense="POSITIVE", OffsetFromReferenceLine=0.0)
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[obj], RelatingMaterial=usage)


def slab(name, x0, y0, z0, bx, ly, t, mat, sto_pl):
    """IfcSlab horizontal: perfil en planta bx (X) x ly (Y) centrado, extrusion +Z de t."""
    rectp = rect_profile(name + "_planta", bx, ly, bx / 2.0, ly / 2.0)
    solid = f.create_entity("IfcExtrudedAreaSolid", SweptArea=rectp,
                            Position=a2p3d((0., 0., 0.)), ExtrudedDirection=dirn((0., 0., 1.)), Depth=t)
    shape = f.create_entity("IfcShapeRepresentation", ContextOfItems=body,
                            RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[solid])
    pds = f.create_entity("IfcProductDefinitionShape", Representations=[shape])
    pl = local_placement(sto_pl, a2p3d((x0, y0, z0)))
    el = f.create_entity("IfcSlab", GlobalId=guid(), Name=name, ObjectPlacement=pl,
                         Representation=pds, PredefinedType="FLOOR")
    layerset(el, mat, t, name)
    return el


def wall(name, x0, y0, z0, lw, t, h, mat, sto_pl):
    rectp = rect_profile(name + "_planta", lw, t, lw / 2.0, t / 2.0)
    solid = f.create_entity("IfcExtrudedAreaSolid", SweptArea=rectp,
                            Position=a2p3d((0., 0., 0.)), ExtrudedDirection=dirn((0., 0., 1.)), Depth=h)
    shape = f.create_entity("IfcShapeRepresentation", ContextOfItems=body,
                            RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[solid])
    pds = f.create_entity("IfcProductDefinitionShape", Representations=[shape])
    pl = local_placement(sto_pl, a2p3d((x0, y0, z0)))
    el = f.create_entity("IfcWall", GlobalId=guid(), Name=name, ObjectPlacement=pl,
                         Representation=pds, PredefinedType="SOLIDWALL")
    layerset(el, mat, t, name)
    return el


def footing(name, x0, y0, z0, bx, ly, t, mat, sto_pl):
    rectp = rect_profile(name + "_planta", bx, ly, bx / 2.0, ly / 2.0)
    solid = f.create_entity("IfcExtrudedAreaSolid", SweptArea=rectp,
                            Position=a2p3d((0., 0., 0.)), ExtrudedDirection=dirn((0., 0., 1.)), Depth=t)
    shape = f.create_entity("IfcShapeRepresentation", ContextOfItems=body,
                            RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[solid])
    pds = f.create_entity("IfcProductDefinitionShape", Representations=[shape])
    pl = local_placement(sto_pl, a2p3d((x0, y0, z0)))
    el = f.create_entity("IfcFooting", GlobalId=guid(), Name=name, ObjectPlacement=pl,
                         Representation=pds, PredefinedType="PAD_FOOTING")
    layerset(el, mat, t, name)
    return el


# ============ A) PORTICO DE ACERO ============
col1 = member("col", "Portico_Pilar_1", (X_PORT, 0., 0.), (X_PORT, 0., H_PORT), ishape(HEB240),
              mat_steel, (1., 0., 0.), plc_baja)
col2 = member("col", "Portico_Pilar_2", (X_PORT + L_PORT, 0., 0.), (X_PORT + L_PORT, 0., H_PORT),
              ishape(HEB240), mat_steel, (1., 0., 0.), plc_baja)
dintel = member("beam", "Portico_Dintel", (X_PORT, 0., H_PORT), (X_PORT + L_PORT, 0., H_PORT),
                ishape(IPE360), mat_steel, (0., 1., 0.), plc_prim)
pset_for(dintel, "Pset_Estructurando_CargaHipotesis",
         {"Descripcion": "carga gravitatoria de servicio sobre el dintel del portico",
          "G_kN_m": G_DINTEL, "Q_kN_m": Q_DINTEL, "Direccion": "-Z"})
for c in (col1, col2):
    pset_for(c, "Pset_Estructurando_ApoyoBase", {"Cota_z_m": 0.0, "Tipo": "biarticulado"})
pset_for(col1, "Pset_Estructurando_Portico", {"Sistema": "portico_acero", "Norma": "EC3"})

# ============ B) FORJADO MIXTO / viga mixta ============
vmix = member("beam", "Mixta_Viga", (0., Y_MIX, 0.), (L_MIX, Y_MIX, 0.), ishape(IPE400),
              mat_steel, (0., 1., 0.), plc_baja)
for c in (vmix,):
    pset_for(c, "Pset_Estructurando_ApoyoBase", {"Cota_z_m": 0.0, "Tipo": "biarticulado"})
pset_for(vmix, "Pset_Estructurando_Conectores",
         {"TipoPerno": "headed", "Diametro_m": 0.019, "Altura_m": 0.100, "fu_Pa": 450e6,
          "nr_por_nervio": 1, "Apeado": "no"})
pset_for(vmix, "Pset_Estructurando_Losa",
         {"Canto_m": 0.12, "CantoChapa_hp_m": 0.058, "CantoHorm_hc_m": 0.062, "b0_m": 0.10,
          "Orientacion": "perpendicular", "Material": C25["name"]})
# losa mixta: footprint 8 (X) x 3 (Y) centrada en y=Y_MIX, base z=0
losaM = slab("Mixta_Losa", 0.0, Y_MIX - SEP_MIX / 2.0, 0.0, L_MIX, SEP_MIX, T_SLAB, mat_c25, plc_baja)
pset_for(losaM, "Pset_Estructurando_Mixta",
         {"Sistema": "viga_mixta", "Norma": "EC4", "VigaAsociada": "Mixta_Viga"})
pset_for(losaM, "Pset_Estructurando_CargasMixta",
         {"Descripcion": "cargas por fase del forjado mixto (hipotesis)",
          "G_losa_kN_m2": G_LOSA, "Qc_ejec_kN_m2": QC_EJEC,
          "G2_kN_m2": G2_MIX, "Q_uso_kN_m2": Q_USO})

# ============ C) MURO DE CARGA ============
muro = wall("Muro_Carga", X_WALL, 0.0, 0.0, LW_WALL, T_WALL, H_WALL, mat_c30, plc_baja)
pset_for(muro, "Pset_Estructurando_CargaHipotesis",
         {"Descripcion": "carga vertical de cabeza del muro de carga con excentricidad",
          "N_G_kN_m": G_TOP_W, "N_Q_kN_m": Q_TOP_W, "Excentricidad_cabeza_m": E_CAB_W,
          "Direccion": "-Z", "Arriostrado": "si"})
pset_for(muro, "Pset_Estructurando_ApoyoBase",
         {"Cota_z_m": 0.0, "Tipo": "base_empotrada_cabeza_arriostrada", "Ubicacion": "pie_del_muro"})

# ============ D) CIMENTACION: pilar HA + zapata ============
# zapata centrada en (X_FOOT, 0), base z=0, cara superior z=0.60
zap = footing("Zapata_Aislada", X_FOOT - B_FOOT / 2.0, -L_FOOT / 2.0, 0.0, B_FOOT, L_FOOT, T_FOOT,
              mat_c30, plc_cim)
# pilar de hormigon 0,40x0,40, pie sobre la cara superior de la zapata (z=0.60)
pilarHA = member("col", "Cim_Pilar", (X_FOOT, 0., T_FOOT), (X_FOOT, 0., T_FOOT + 1.0),
                 rect_profile("Pilar 400x400", C_PILAR, C_PILAR, 0.0, 0.0), mat_c30, (1., 0., 0.), plc_cim)
pset_for(pilarHA, "Pset_Estructurando_PilarCimiento", {"Sistema": "pilar_zapata", "Lado_m": C_PILAR})
pset_for(zap, "Pset_Estructurando_Suelo",
         {"ModuloBalasto_N_m3": KS, "Rd_suelo_Pa": RD_SUELO,
          "Descripcion": "terreno medio: k_s=40 MN/m3, R_d=250 kPa"})
pset_for(zap, "Pset_Estructurando_ApoyoBase",
         {"Cota_z_m": 0.0, "Tipo": "lecho_elastico_winkler", "Ubicacion": "base_de_la_zapata"})
pset_for(zap, "Pset_Estructurando_Zapata",
         {"LadoPilar": C_PILAR, "TamanoMalla": MESH_FOOT, "xpilar": X_FOOT, "ypilar": 0.0,
          "N_G_N": N_G_ZAP, "N_Q_N": N_Q_ZAP, "M_G_Nm": M_G_ZAP, "M_Q_Nm": M_Q_ZAP,
          "Descripcion": "bajada de carga del pilar a la zapata (caso 10)"})

# proyecto
pset_for(building, "Pset_Estructurando_ProyectoAnalisis",
         {"Norma": "EC2+EC3+EC4+EC7", "Sistema": "edificio_multi_elemento",
          "Nota": "IFC fisico por plantas: derivar TODO el modelo analitico (barras + superficies "
                  "horizontales/verticales + cimientos + asociaciones) y enrutar cada elemento (puente Direccion 2, R4)"})

# ---- contener en plantas ----
f.create_entity("IfcRelContainedInSpatialStructure", GlobalId=guid(),
                RelatingStructure=sto_cim, RelatedElements=[zap, pilarHA])
f.create_entity("IfcRelContainedInSpatialStructure", GlobalId=guid(),
                RelatingStructure=sto_baja, RelatedElements=[col1, col2, vmix, losaM, muro])
f.create_entity("IfcRelContainedInSpatialStructure", GlobalId=guid(),
                RelatingStructure=sto_prim, RelatedElements=[dintel])

f.write(OUT)
print("IFC caso R4 (FISICO, edificio multi-elemento por plantas) en:", OUT)

# ---- validacion ----
VAL = os.path.join(HERE, "validacion-IFC.txt")
g2 = ifcopenshell.open(OUT)
clases = ["IfcProject", "IfcSite", "IfcBuilding", "IfcBuildingStorey",
          "IfcColumn", "IfcBeam", "IfcSlab", "IfcWall", "IfcFooting",
          "IfcExtrudedAreaSolid", "IfcIShapeProfileDef", "IfcRectangleProfileDef",
          "IfcMaterial", "IfcMaterialProperties", "IfcMaterialProfileSetUsage",
          "IfcMaterialLayerSet", "IfcMaterialLayerSetUsage", "IfcRelAssociatesMaterial",
          "IfcPropertySet", "IfcRelDefinesByProperties", "IfcRelContainedInSpatialStructure"]
lines = ["VALIDACION IFC - caso-R4.ifc (IFC FISICO: edificio multi-elemento por plantas)",
         "schema=%s  archivo=%s" % (g2.schema, OUT), "", "Recuento de entidades:"]
for c in clases:
    lines.append("  %-34s %d" % (c, len(g2.by_type(c))))
lines.append("")
lines.append("Plantas (IfcBuildingStorey):")
for s in g2.by_type("IfcBuildingStorey"):
    cont = [r for r in g2.by_type("IfcRelContainedInSpatialStructure") if r.RelatingStructure == s]
    els = [e.Name for r in cont for e in r.RelatedElements]
    lines.append("  '%s' elev=%.2f m -> %s" % (s.Name, float(s.Elevation), els))
lines.append("")
lines.append("Elementos fisicos (geometria Body, extrusion +Z, SIN entidades de analisis):")
for cls in ("IfcColumn", "IfcBeam", "IfcSlab", "IfcWall", "IfcFooting"):
    for el in g2.by_type(cls):
        sol = el.Representation.Representations[0].Items[0]
        sa = sol.SweptArea
        prof = sa.ProfileName if hasattr(sa, "ProfileName") else sa.is_a()
        lines.append("  %-10s '%s'  Depth=%.3f  perfil=%s" % (cls, el.Name, float(sol.Depth), prof))
lines.append("")
lines.append("Material/espesor por IfcMaterialLayerSet (losa/muro/zapata):")
for u in g2.by_type("IfcMaterialLayerSet"):
    tot = sum(float(l.LayerThickness) for l in u.MaterialLayers)
    m0 = u.MaterialLayers[0].Material.Name if u.MaterialLayers[0].Material else "?"
    lines.append("  %s  t=%.3f m  material=%s" % (u.LayerSetName, tot, m0))
lines.append("")
lines.append("Comprobacion: entidades de ANALISIS (deben ser 0 en un IFC fisico):")
for c in ("IfcStructuralCurveMember", "IfcStructuralSurfaceMember", "IfcStructuralPointAction",
          "IfcStructuralLoadGroup", "IfcBoundaryNodeCondition", "IfcStructuralAnalysisModel"):
    lines.append("  %-34s %d" % (c, len(g2.by_type(c))))
with open(VAL, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print("Validacion IFC escrita en:", VAL)
