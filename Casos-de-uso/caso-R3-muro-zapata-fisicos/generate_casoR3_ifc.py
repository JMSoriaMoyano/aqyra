"""
CASO R3 - MURO + ZAPATA FISICOS. Tercer caso de la DIRECCION 2 (puente IFC fisico
-> modelo analitico con SUPERFICIES VERTICALES + CIMIENTOS). A diferencia de los
casos 1-13 (IFC ORTODOXO del dominio de ANALISIS) y como R1/R2, este es un IFC
FISICO como el que entrega una herramienta BIM:

  - Estructura espacial:  IfcProject -> IfcSite -> IfcBuilding -> IfcBuildingStorey
  - Elementos FISICOS con GEOMETRIA Body (IfcExtrudedAreaSolid, extrusion +Z):
      * IfcWall x1   (muro de carga C25/30, alzado H=3,0 m, espesor t=0,20 m, faja
        de calculo L=1,0 m en planta) -> perfil en planta = rectangulo 1,0 x 0,20,
        extrusion VERTICAL +Z de 3,0 m. Material/espesor por
        IfcMaterialLayerSetUsage -> IfcMaterialLayerSet (Sigma LayerThickness=0,20).
        El PLANO MEDIO del muro es VERTICAL (rectangulo L_w x H), NO horizontal.
      * IfcFooting x1 (zapata C30/37, B x L = 2,5 x 2,5 m, canto 0,60 m) ->
        perfil en planta = rectangulo 2,5 x 2,5, extrusion VERTICAL +Z de 0,60 m.
        Material/canto por IfcMaterialLayerSetUsage -> IfcMaterialLayerSet
        (Sigma LayerThickness=0,60). El PLANO MEDIO de la zapata es HORIZONTAL
        (footprint en planta) + canto.
  - El MURO APOYA sobre la ZAPATA: pie del muro (z=0,60) sobre la cara superior de
    la huella de la zapata, centrado en planta (offsets idealizados limpios).
  - NO hay entidades de analisis ni cargas: el modelo analitico (plano medio del
    muro, footprint de la zapata, cadena muro->cimiento) y las HIPOTESIS de carga
    /terreno/apoyo NO estan -> el "puente" debe DERIVARLOS de la GEOMETRIA. Las
    hipotesis se aportan como Pset.

GEOMETRIA y datos = casos validados (para validar el puente contra resultados
conocidos):
  - Muro de carga = caso 7: C25/30 H=3,0 t=0,20 faja 1,0 m; carga de cabeza
    G=250 / Q=120 kN/m con excentricidad e=25 mm (M = N*e). Esperado: lambda=52 >
    lambda_lim -> ESBELTO; M_Ed = M0Ed + M2 ~ 31,3 kN*m/m; phi10/200 c/cara;
    N-M ~ 47 %; equilibrio vertical ELU ~0,000 %.
  - Zapata = caso 5: C30/37 2,5x2,5 canto 0,60 m sobre lecho Winkler k_s=40 MN/m3,
    R_d=250 kPa; bajada de carga del soporte equivalente N_G=700 / N_Q=250 kN + M
    (e~0,075). Esperado: EC7 sigma_ef <= R_d (sin despegue, e<B/6); EC2
    flexion/punzonamiento/fisuracion; equilibrio del lecho ~0 %.

Lo que sale de GEOMETRIA (derivado del fisico) vs de PSET (hipotesis del calculista):
  - GEOMETRIA: huella B x L y canto de la zapata (IfcFooting + IfcMaterialLayerSet);
    plano medio del muro (L_w x H) y espesor (IfcWall + IfcMaterialLayerSet);
    material (fck) de los IfcMaterialProperties; cadena muro->cimiento por
    proximidad en planta (pie del muro sobre la huella).
  - PSET: carga de cabeza del muro (N_G/N_Q + e) -> Pset_Estructurando_CargaHipotesis;
    terreno (k_s, R_d) -> Pset_Estructurando_Suelo; cota de apoyo base ->
    Pset_Estructurando_ApoyoBase; bajada de carga del pilar/muro equivalente a la
    zapata (N_G=700/N_Q=250 + M) y lado de pilar/malla -> Pset_Estructurando_Zapata
    (geometria de la zapata caso-5 que no se deriva limpiamente del fisico del muro
    de faja 1,0 m); metadatos -> Pset_Estructurando_ProyectoAnalisis.

Unidades SI (m, N, Pa). Plano XY horizontal, Z vertical, gravedad -Z.
"""
import os
import ifcopenshell
import ifcopenshell.guid

# --- materiales ---
CONC_WALL = dict(name="C25/30", E=31e9, nu=0.2, rho=2500.0, fck=25e6, fctm=2.6e6,
                 G=31e9 / (2 * (1 + 0.2)))
CONC_FOOT = dict(name="C30/37", E=32.84e9, nu=0.2, rho=2500.0, fck=30e6, fctm=2.9e6,
                 G=13.68e9)

# --- geometria del MURO (caso 7) ---
H_WALL = 3.0       # alzado (extrusion +Z)
T_WALL = 0.20      # espesor (lado fino de la huella = Sigma LayerThickness)
LW_WALL = 1.0      # faja de calculo / longitud del muro en planta

# --- geometria de la ZAPATA (caso 5) ---
B_FOOT = 2.5       # lado en planta (X)
L_FOOT = 2.5       # lado en planta (Y)
T_FOOT = 0.60      # canto (extrusion +Z)
C_PILAR = 0.40     # lado del soporte equivalente (Pset)
MESH_FOOT = 0.125  # malla de la zapata (Pset)

# --- hipotesis MURO (caso 7): carga de cabeza N + e ---
G_TOP = 250.0      # kN/m permanente en cabeza
Q_TOP = 120.0      # kN/m variable en cabeza
E_CAB = 0.025      # excentricidad de cabeza (m) -> M = N*e

# --- hipotesis TERRENO (caso 5) ---
KS = 40e6          # modulo de balasto (N/m3)
RD_SUELO = 250e3   # resistencia de calculo del terreno (Pa)

# --- bajada de carga a la zapata (caso 5), via Pset ---
N_G_ZAP = 700e3    # axil permanente que baja a la zapata (N)
N_Q_ZAP = 250e3    # axil variable que baja a la zapata (N)
M_G_ZAP = 80e3     # momento permanente de cabeza (N*m) -> excentricidad ELU e~0,075
                   #   (e = 1,35*M_G / N_ELU = 1,35*80 / 1444 = 0,075 m; caso 5)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-R3.ifc")

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
bodyctx = f.create_entity("IfcGeometricRepresentationSubContext", ContextIdentifier="Body",
                          ContextType="Model", ParentContext=ctx, TargetView="MODEL_VIEW")
project = f.create_entity("IfcProject", GlobalId=guid(),
                          Name="Caso R3 - Muro + zapata fisicos (puente IFC->analitico, superficies verticales + cimientos)",
                          UnitsInContext=ua, RepresentationContexts=[ctx])

# ---- estructura espacial ----
site_pl = local_placement(None, a2p3d((0., 0., 0.)))
site = f.create_entity("IfcSite", GlobalId=guid(), Name="Parcela", ObjectPlacement=site_pl,
                       CompositionType="ELEMENT")
bld_pl = local_placement(site_pl, a2p3d((0., 0., 0.)))
building = f.create_entity("IfcBuilding", GlobalId=guid(), Name="Edificio R3", ObjectPlacement=bld_pl,
                           CompositionType="ELEMENT")
sto_pl = local_placement(bld_pl, a2p3d((0., 0., 0.)))
storey = f.create_entity("IfcBuildingStorey", GlobalId=guid(), Name="Cimentacion nivel -0,60",
                         ObjectPlacement=sto_pl, CompositionType="ELEMENT", Elevation=0.0)
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=project, RelatedObjects=[site])
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=site, RelatedObjects=[building])
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=building, RelatedObjects=[storey])


def material(M):
    m = f.create_entity("IfcMaterial", Name=M["name"])
    pairs = [("YoungModulus", M["E"]), ("ShearModulus", M["G"]),
             ("PoissonRatio", M["nu"]), ("MassDensity", M["rho"]),
             ("CompressiveStrength", M["fck"]), ("TensileStrength", M["fctm"])]
    props = [f.create_entity("IfcPropertySingleValue", Name=k,
                NominalValue=f.create_entity("IfcReal", wrappedValue=float(v))) for k, v in pairs]
    f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=m, Properties=props)
    return m


mat_wall = material(CONC_WALL)
mat_foot = material(CONC_FOOT)


def prop(name, val):
    if isinstance(val, str):
        nv = f.create_entity("IfcText", wrappedValue=val)
    else:
        nv = f.create_entity("IfcReal", wrappedValue=float(val))
    return f.create_entity("IfcPropertySingleValue", Name=name, NominalValue=nv)


def pset_for(obj, name, props):
    ps = f.create_entity("IfcPropertySet", GlobalId=guid(), Name=name,
                         HasProperties=[prop(k, v) for k, v in props.items()])
    f.create_entity("IfcRelDefinesByProperties", GlobalId=guid(),
                    RelatedObjects=[obj], RelatingPropertyDefinition=ps)


def _rect_profile(name, bx, ly, cx, cy):
    """Rectangulo bx (X) x ly (Y) centrado en (cx,cy) por su Position 2D."""
    return f.create_entity("IfcRectangleProfileDef", ProfileType="AREA", ProfileName=name,
                           Position=f.create_entity("IfcAxis2Placement2D",
                               Location=f.create_entity("IfcCartesianPoint", Coordinates=(cx, cy))),
                           XDim=bx, YDim=ly)


def _layerset(obj, mat, thickness, name):
    """Material/espesor por IfcMaterialLayerSetUsage -> IfcMaterialLayerSet."""
    layer = f.create_entity("IfcMaterialLayer", Material=mat, LayerThickness=thickness, Name=name)
    mls = f.create_entity("IfcMaterialLayerSet", MaterialLayers=[layer], LayerSetName=name + "_capas")
    usage = f.create_entity("IfcMaterialLayerSetUsage", ForLayerSet=mls, LayerSetDirection="AXIS3",
                            DirectionSense="POSITIVE", OffsetFromReferenceLine=0.0)
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[obj], RelatingMaterial=usage)


def wall(name, x0, y0, z0, lw, t, h):
    """Muro vertical: perfil en planta lw (X) x t (Y), extrusion VERTICAL +Z de h.
    Origen del placement en (x0,y0,z0); rectangulo centrado en (lw/2, t/2)."""
    rect = _rect_profile(name + "_planta", lw, t, lw / 2.0, t / 2.0)
    solid = f.create_entity("IfcExtrudedAreaSolid", SweptArea=rect,
                            Position=a2p3d((0., 0., 0.)), ExtrudedDirection=dirn((0., 0., 1.)), Depth=h)
    shape = f.create_entity("IfcShapeRepresentation", ContextOfItems=bodyctx,
                            RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[solid])
    pds = f.create_entity("IfcProductDefinitionShape", Representations=[shape])
    pl = local_placement(sto_pl, a2p3d((x0, y0, z0)))
    el = f.create_entity("IfcWall", GlobalId=guid(), Name=name, ObjectPlacement=pl,
                         Representation=pds, PredefinedType="SOLIDWALL")
    _layerset(el, mat_wall, t, name)
    return el


def footing(name, x0, y0, z0, bx, ly, t):
    """Zapata horizontal: perfil en planta bx (X) x ly (Y), extrusion VERTICAL +Z
    de t (canto). Origen del placement en (x0,y0,z0); rectangulo centrado."""
    rect = _rect_profile(name + "_planta", bx, ly, bx / 2.0, ly / 2.0)
    solid = f.create_entity("IfcExtrudedAreaSolid", SweptArea=rect,
                            Position=a2p3d((0., 0., 0.)), ExtrudedDirection=dirn((0., 0., 1.)), Depth=t)
    shape = f.create_entity("IfcShapeRepresentation", ContextOfItems=bodyctx,
                            RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[solid])
    pds = f.create_entity("IfcProductDefinitionShape", Representations=[shape])
    pl = local_placement(sto_pl, a2p3d((x0, y0, z0)))
    el = f.create_entity("IfcFooting", GlobalId=guid(), Name=name, ObjectPlacement=pl,
                         Representation=pds, PredefinedType="PAD_FOOTING")
    _layerset(el, mat_foot, t, name)
    return el


# ---- los elementos (zapata abajo, muro encima, centrados en planta) ----
# zapata: huella X[0,2.5] Y[0,2.5], base z=0, cara superior z=0.60
zap = footing("Zapata_aislada", 0.0, 0.0, 0.0, B_FOOT, L_FOOT, T_FOOT)
# muro: faja 1.0 (X) x 0.20 (Y), centrada en (1.25,1.25), pie en z=0.60 (sobre la
# cara superior de la zapata), extrusion +Z de 3.0 -> cabeza en z=3.60
wx0 = B_FOOT / 2.0 - LW_WALL / 2.0    # 0.75
wy0 = L_FOOT / 2.0 - T_WALL / 2.0     # 1.15
mur = wall("Muro_carga", wx0, wy0, T_FOOT, LW_WALL, T_WALL, H_WALL)

# ---- datos NO geometricos (no existen en un IFC fisico) -> Pset hipotesis ----
# MURO: carga de cabeza N + e (caso 7)
pset_for(mur, "Pset_Estructurando_CargaHipotesis",
         {"Descripcion": "carga vertical de cabeza del muro de carga (forjados) con excentricidad",
          "N_G_kN_m": G_TOP, "N_Q_kN_m": Q_TOP, "Excentricidad_cabeza_m": E_CAB,
          "Direccion": "-Z", "Arriostrado": "si"})
pset_for(mur, "Pset_Estructurando_ApoyoBase",
         {"Cota_z_m": T_FOOT, "Tipo": "base_empotrada_cabeza_arriostrada",
          "Ubicacion": "pie_del_muro_sobre_zapata"})

# ZAPATA: terreno + bajada de carga del soporte equivalente (caso 5)
pset_for(zap, "Pset_Estructurando_Suelo",
         {"ModuloBalasto_N_m3": KS, "Rd_suelo_Pa": RD_SUELO,
          "Descripcion": "terreno medio: k_s=40 MN/m3, R_d=250 kPa"})
pset_for(zap, "Pset_Estructurando_ApoyoBase",
         {"Cota_z_m": 0.0, "Tipo": "lecho_elastico_winkler",
          "Ubicacion": "base_de_la_zapata"})
pset_for(zap, "Pset_Estructurando_Zapata",
         {"LadoPilar": C_PILAR, "TamanoMalla": MESH_FOOT, "xpilar": B_FOOT / 2.0, "ypilar": L_FOOT / 2.0,
          "N_G_N": N_G_ZAP, "N_Q_N": N_Q_ZAP, "M_G_Nm": M_G_ZAP,
          "Descripcion": "bajada de carga del soporte equivalente a la zapata (caso 5)"})

# proyecto
pset_for(building, "Pset_Estructurando_ProyectoAnalisis",
         {"Norma": "EC2+EC7", "Material_muro": "C25/30", "Material_zapata": "C30/37",
          "Sistema": "muro_de_carga_sobre_zapata_aislada",
          "Nota": "IFC fisico: derivar plano medio VERTICAL del IfcWall + footprint/canto del IfcFooting "
                  "(IfcMaterialLayerSet); clasificar superficies por orientacion; cadena muro->cimiento (puente Direccion 2)"})

# ---- contener los elementos en la planta ----
f.create_entity("IfcRelContainedInSpatialStructure", GlobalId=guid(),
                RelatingStructure=storey, RelatedElements=[zap, mur])

f.write(OUT)

# ---- validacion: reabrir el IFC y volcar el recuento de entidades ----
VAL = os.path.join(HERE, "validacion-IFC.txt")
g2 = ifcopenshell.open(OUT)
clases = ["IfcProject", "IfcSite", "IfcBuilding", "IfcBuildingStorey",
          "IfcWall", "IfcFooting", "IfcSlab", "IfcExtrudedAreaSolid",
          "IfcRectangleProfileDef", "IfcMaterial", "IfcMaterialProperties",
          "IfcMaterialLayerSet", "IfcMaterialLayerSetUsage", "IfcRelAssociatesMaterial",
          "IfcPropertySet", "IfcRelDefinesByProperties",
          "IfcStructuralSurfaceMember", "IfcStructuralPointAction",
          "IfcStructuralCurveMember", "IfcBoundaryNodeCondition"]
lines = []
lines.append("VALIDACION IFC - caso-R3.ifc (IFC FISICO: muro IfcWall + zapata IfcFooting)")
lines.append("schema=%s  archivo=%s" % (g2.schema, OUT))
lines.append("")
lines.append("Recuento de entidades:")
for c in clases:
    lines.append("  %-32s %d" % (c, len(g2.by_type(c))))
lines.append("")
lines.append("Elementos fisicos (con geometria Body, SIN entidades de analisis):")
for w in g2.by_type("IfcWall"):
    sol = w.Representation.Representations[0].Items[0]
    lines.append("  IfcWall '%s'  PredefinedType=%s  Depth(extrusion)=%.3f m  ExtrudedDirection=%s" % (
        w.Name, w.PredefinedType, float(sol.Depth), sol.ExtrudedDirection.DirectionRatios))
for ft in g2.by_type("IfcFooting"):
    sol = ft.Representation.Representations[0].Items[0]
    lines.append("  IfcFooting '%s'  PredefinedType=%s  Depth(canto)=%.3f m  ExtrudedDirection=%s" % (
        ft.Name, ft.PredefinedType, float(sol.Depth), sol.ExtrudedDirection.DirectionRatios))
lines.append("")
lines.append("Material/espesor por IfcMaterialLayerSet (Sigma LayerThickness):")
for u in g2.by_type("IfcMaterialLayerSet"):
    tot = sum(float(l.LayerThickness) for l in u.MaterialLayers)
    m0 = u.MaterialLayers[0].Material.Name if u.MaterialLayers[0].Material else "?"
    lines.append("  %s  t=%.3f m  material=%s" % (u.LayerSetName, tot, m0))
lines.append("")
lines.append("Comprobacion: entidades de ANALISIS (deben ser 0 en un IFC fisico):")
for c in ("IfcStructuralSurfaceMember", "IfcStructuralPointAction",
          "IfcStructuralCurveMember", "IfcBoundaryNodeCondition", "IfcStructuralAnalysisModel"):
    lines.append("  %-32s %d" % (c, len(g2.by_type(c))))
with open(VAL, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print("Validacion IFC escrita en:", VAL)

print("IFC caso R3 (FISICO, muro + zapata, puente IFC->analitico, superficies verticales + cimientos) en:", OUT)
print("  IfcWall x1 (C25/30 H=%.1f t=%.0f mm faja %.1f m, plano medio VERTICAL)" % (H_WALL, T_WALL * 1e3, LW_WALL))
print("  IfcFooting x1 (C30/37 %.1fx%.1f canto %.0f mm, footprint HORIZONTAL)" % (B_FOOT, L_FOOT, T_FOOT * 1e3))
print("  Muro sobre zapata: pie del muro z=%.2f (cara superior de la zapata)" % T_FOOT)
print("  Hipotesis (Pset): muro G=%.0f/Q=%.0f kN/m e=%.0f mm ; terreno k_s=%.0f MN/m3 Rd=%.0f kPa ; zapata N_G=%.0f/N_Q=%.0f kN" % (
    G_TOP, Q_TOP, E_CAB * 1e3, KS / 1e6, RD_SUELO / 1e3, N_G_ZAP / 1e3, N_Q_ZAP / 1e3))
print("  Estructura espacial: Project->Site->Building->Storey; sin entidades de analisis ni cargas")
