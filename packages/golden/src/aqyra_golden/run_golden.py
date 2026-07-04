#!/usr/bin/env python3
"""Runner de la golden (Llave 1) — multi-contrato (C1 + C4 + C3).

Dos pasos de validación (ver CONTRATOS_estado-validacion-ubicacion.md §2):
  1. TODOS los esquemas de contrato (packages/contracts/C*/*.schema.json) son JSON Schema
     bien formados.
  2. La golden los ejercita, DESPACHADA POR CONTRATO (Fase II·h1):
     - C1: compile real (caso.alto.json → IFC con engines/ifc) + recompute de métricas
       contra expected.json (costura cerrada en Fase I·h1).
     - C4: RECOMPUTE con el service real (services/federacion, costura cerrada en
       Fase II·h2 — misma costura que C1 en Fase 0 → Fase I): federar+validar sobre
       las entradas congeladas contra el MISMO expected.json, con tolerancias; MÁS
       los checks ANCLADOS del 2.1 (conformidad de esquemas, identidad por hash y
       coherencia interna), que se conservan íntegros (D10: más checks, nunca menos).

Regla de oro: un fallo se corrige en el código, NUNCA aflojando la golden.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

# repo root = .../aqyra ; este fichero = aqyra/packages/golden/src/aqyra_golden/run_golden.py
_HERE = Path(__file__).resolve()
DEFAULT_GOLDEN_DIR = _HERE.parents[2]           # aqyra/packages/golden
DEFAULT_REPO = _HERE.parents[4]                 # aqyra
DEFAULT_CONTRACTS = DEFAULT_REPO / "packages" / "contracts"
DEFAULT_ENGINE = DEFAULT_REPO / "engines" / "ifc"   # engine C1 (compile narración→IFC)

# Familias de elemento que declaran las golden C1 y que deben llevar doble clasificación.
# (4 pilares → IfcColumn, 1 muro → IfcWall, 1 losa → IfcSlab, 1 ascensor → IfcTransportElement).
TARGET_CLASSES = {"IfcColumn", "IfcWall", "IfcSlab", "IfcTransportElement"}

GREEN = "\033[32m"; RED = "\033[31m"; DIM = "\033[2m"; RST = "\033[0m"


# --------------------------------------------------------------------------- #
# Esquemas de contrato                                                        #
# --------------------------------------------------------------------------- #
def load_c1_schemas(contracts_dir: Path) -> dict[str, dict]:
    base = contracts_dir / "C1-interoperabilidad"
    out = {}
    for key, fname in (("alto", "alto-spec.schema.json"),
                       ("neutro", "modelo-neutro.schema.json")):
        p = base / fname
        out[key] = json.loads(p.read_text(encoding="utf-8"))
    return out


def load_c4_schemas(contracts_dir: Path) -> dict[str, dict]:
    base = contracts_dir / "C4-federacion"
    out = {}
    for key, fname in (("reglas", "reglas-federacion.schema.json"),
                       ("manifiesto", "maestro-manifiesto.schema.json"),
                       ("informe", "informe-qa.schema.json")):
        out[key] = json.loads((base / fname).read_text(encoding="utf-8"))
    return out


def load_c3_schemas(contracts_dir: Path) -> dict[str, dict]:
    base = contracts_dir / "C3-cumplimiento"
    out = {}
    for key, fname in (("entrada", "entrada-cumplimiento.schema.json"),
                       ("veredicto", "veredicto-cumplimiento.schema.json")):
        out[key] = json.loads((base / fname).read_text(encoding="utf-8"))
    return out


def discover_schemas(contracts_dir: Path) -> dict[str, dict]:
    """TODOS los esquemas de contrato del registro (paso 1 es multi-contrato)."""
    out = {}
    for p in sorted(contracts_dir.glob("C*/*.schema.json")):
        out[f"{p.parent.name}/{p.name}"] = json.loads(p.read_text(encoding="utf-8"))
    return out


def check_schemas_wellformed(schemas: dict[str, dict]) -> list[tuple[str, bool, str]]:
    """Paso 1: los esquemas son JSON Schema bien formados (meta-validación)."""
    from jsonschema import Draft202012Validator
    results = []
    for key, schema in schemas.items():
        try:
            Draft202012Validator.check_schema(schema)
            results.append((f"esquema '{key}' bien formado", True, "JSON Schema 2020-12 válido"))
        except Exception as e:  # noqa: BLE001
            results.append((f"esquema '{key}' bien formado", False, str(e).splitlines()[0]))
    return results


def validate_against_schema(instance: dict, schema: dict) -> tuple[bool, str]:
    from jsonschema import Draft202012Validator
    v = Draft202012Validator(schema)
    errs = sorted(v.iter_errors(instance), key=lambda e: list(e.path))
    if not errs:
        return True, "conforma el esquema"
    e = errs[0]
    loc = "/".join(str(p) for p in e.path) or "(raíz)"
    return False, f"{loc}: {e.message}"


# --------------------------------------------------------------------------- #
# C1 · oráculo: compile real + métricas recomputadas                           #
# --------------------------------------------------------------------------- #
def _attr(seg, name, idx):
    try:
        return getattr(seg, name)
    except Exception:  # noqa: BLE001
        return seg[idx]


def compile_case(alto_path: Path, out_ifc: Path, engine_dir: Path = DEFAULT_ENGINE) -> None:
    """Cierra la costura: compila caso.alto.json → IFC con el engine (engines/ifc).

    El oráculo NO recibe ya un IFC congelado, sino el IFC que produce el compile real
    del canónico importado. Un fallo aquí se investiga en el compile, jamás en expected.json.
    """
    import json as _json
    p = str(engine_dir)
    if p not in sys.path:
        sys.path.insert(0, p)
    import compile_c1  # engines/ifc/compile_c1.py
    alto = _json.loads(alto_path.read_text(encoding="utf-8"))
    compile_c1.compilar_alto_a_ifc(alto, out_ifc)


def compute_metrics(ifc_path: Path) -> dict:
    import ifcopenshell  # lazy: no se necesita en --schema-only

    f = ifcopenshell.open(str(ifc_path))
    m: dict = {"esquema": f.schema}

    # huecos por tipo de elemento vaciado
    losa = muro = 0
    for r in f.by_type("IfcRelVoidsElement"):
        cls = r.RelatingBuildingElement.is_a()
        if cls == "IfcSlab":
            losa += 1
        elif cls == "IfcWall":
            muro += 1
    m["huecos"] = {"losa": losa, "muro": muro}

    # elementos de transporte (catálogo abierto)
    tes = f.by_type("IfcTransportElement")
    m["transporte"] = {
        "total": len(tes),
        "predefinidos": sorted({str(getattr(t, "PredefinedType", None)) for t in tes}),
    }

    # alineación horizontal
    segs = f.by_type("IfcAlignmentHorizontalSegment")
    tipos = [_attr(s, "PredefinedType", 8) for s in segs]
    longs = [float(_attr(s, "SegmentLength", 6)) for s in segs]
    clot_A = []
    for s in segs:
        if _attr(s, "PredefinedType", 8) == "CLOTHOID":
            r0 = float(_attr(s, "StartRadiusOfCurvature", 4) or 0.0)
            r1 = float(_attr(s, "EndRadiusOfCurvature", 5) or 0.0)
            R = r0 if r0 else r1
            L = float(_attr(s, "SegmentLength", 6))
            if R:
                clot_A.append(math.sqrt(L * R))
    m["alineacion"] = {
        "planta_secuencia": tipos,
        "longitud_total_m": round(sum(longs), 6),
        "clotoide_A": [round(a, 3) for a in clot_A],
    }

    # doble clasificación (bsDD + Uniclass) sobre las familias objetivo
    def system_of(ref):
        cur = ref
        for _ in range(8):
            rs = getattr(cur, "ReferencedSource", None)
            if rs is None:
                break
            cur = rs
        name = (getattr(cur, "Name", None) or getattr(cur, "Source", None) or "")
        n = name.lower()
        if "uniclass" in n:
            return "uniclass"
        if "bsdd" in n:
            return "bsdd"
        return "otro"

    sistemas: dict[int, set[str]] = {}
    targets = [o for o in f.by_type("IfcElement") if o.is_a() in TARGET_CLASSES]
    for o in targets:
        sistemas[o.id()] = set()
    for rel in f.by_type("IfcRelAssociatesClassification"):
        sys_tag = system_of(rel.RelatingClassification)
        for o in rel.RelatedObjects:
            if o.id() in sistemas:
                sistemas[o.id()].add(sys_tag)
    doble = sum(1 for s in sistemas.values() if {"uniclass", "bsdd"} <= s)
    sin_clasif = sum(1 for s in sistemas.values() if not s)
    m["doble_clasificacion"] = {
        "objetivo": len(targets), "elementos": doble, "sin_clasif": sin_clasif,
    }
    return m


# --------------------------------------------------------------------------- #
# C1 · comparación caso vs oráculo                                             #
# --------------------------------------------------------------------------- #
def compare(expected: dict, got: dict, tol: dict) -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []

    def chk(name, ok, detail):
        checks.append((name, bool(ok), detail))

    chk("esquema IFC", got["esquema"] == expected["esquema"],
        f"{got['esquema']} (esperado {expected['esquema']})")

    eh, gh = expected["huecos"], got["huecos"]
    chk("huecos losa", gh["losa"] == eh["losa"], f"{gh['losa']} (esperado {eh['losa']})")
    chk("huecos muro", gh["muro"] == eh["muro"], f"{gh['muro']} (esperado {eh['muro']})")

    et, gt = expected["transporte"], got["transporte"]
    chk("ascensor total", gt["total"] == et["total"], f"{gt['total']} (esperado {et['total']})")
    chk("ascensor predefinido", gt["predefinidos"] == et["predefinidos"],
        f"{gt['predefinidos']} (esperado {et['predefinidos']})")

    ea, ga = expected["alineacion"], got["alineacion"]
    chk("planta secuencia", ga["planta_secuencia"] == ea["planta_secuencia"],
        f"{ga['planta_secuencia']}")
    tolL = float(tol.get("longitud_total_m", 1e-6))
    okL = abs(ga["longitud_total_m"] - ea["longitud_total_m"]) <= tolL
    chk("longitud total (m)", okL,
        f"{ga['longitud_total_m']} (esperado {ea['longitud_total_m']} ±{tolL})")
    tolA = float(tol.get("clotoide_A", 0.1))
    A_ok = bool(ga["clotoide_A"]) and all(abs(a - ea["clotoide_A"]) <= tolA for a in ga["clotoide_A"])
    chk("clotoide A", A_ok, f"{ga['clotoide_A']} (esperado {ea['clotoide_A']} ±{tolA})")

    ec, gc = expected["doble_clasificacion"], got["doble_clasificacion"]
    chk("doble clasificación", gc["elementos"] == ec["elementos"],
        f"{gc['elementos']}/{gc['objetivo']} (esperado {ec['elementos']})")
    chk("sin clasificar", gc["sin_clasif"] == ec["sin_clasif"],
        f"{gc['sin_clasif']} (esperado {ec['sin_clasif']})")
    return checks


# --------------------------------------------------------------------------- #
# Casos por contrato                                                          #
# --------------------------------------------------------------------------- #
def run_case_c1(case_dir: Path, contracts_dir: Path, expected: dict, tol: dict) -> bool:
    """C1: conformidad del caso + compile real + recompute de métricas (Fase I·h1)."""
    schemas = load_c1_schemas(contracts_dir)
    case_ok = True

    alto_path = case_dir / "caso.alto.json"
    if alto_path.exists():
        alto = json.loads(alto_path.read_text(encoding="utf-8"))
        ok, detail = validate_against_schema(alto, schemas["alto"])
        print_checks([("caso conforma alto-spec", ok, detail)])
        case_ok &= ok
    else:
        print_checks([("caso.alto.json presente", False, "no encontrado (necesario para compilar)")])
        return False

    import tempfile
    try:
        with tempfile.TemporaryDirectory() as td:
            compiled = Path(td) / "compilado.ifc"
            compile_case(alto_path, compiled)
            print_checks([("compile narración→IFC", True, f"engine → {compiled.name}")])
            got = compute_metrics(compiled)
            checks = compare(expected, got, tol)
            print_checks(checks)
            case_ok &= all(ok for _, ok, _ in checks)
    except Exception as e:  # noqa: BLE001
        print_checks([("compile+oráculo", False, f"{type(e).__name__}: {e}")])
        case_ok = False
    return case_ok


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _ids_identifiers(ids_path: Path) -> set[str]:
    """Identificadores de las specifications del .ids (IDS 1.0, buildingSMART)."""
    import xml.etree.ElementTree as ET
    ns = "{http://standards.buildingsmart.org/IDS}"
    root = ET.parse(str(ids_path)).getroot()
    out = set()
    for spec in root.iter(f"{ns}specification"):
        out.add(spec.get("identifier") or spec.get("name") or "")
    return out - {""}


def _lock_packs_ids(repo: Path) -> dict:
    """Sección [packs.ids] de versions.lock (ancla del pack IDS)."""
    try:  # Python 3.11+
        import tomllib
    except ModuleNotFoundError:  # 3.10
        import tomli as tomllib
    with open(repo / "versions.lock", "rb") as f:
        lock = tomllib.load(f)
    return lock.get("packs", {}).get("ids", {})


# --------------------------------------------------------------------------- #
# C4 · recompute con el service real (Fase II·h2 — costura cerrada)            #
# --------------------------------------------------------------------------- #
DEFAULT_SERVICE_SRC = DEFAULT_REPO / "services" / "federacion" / "src"

# Campos de TEXTO LIBRE del contrato (presentación humana): se comprueban por
# esquema (presencia/tipo) pero NO se comparan literalmente en el recompute —
# la semántica del contrato son ids, resultados, conteos, GUIDs, estados,
# severidades y veredicto. Ídem claves '_*' (comentario, convención del repo).
_CAMPOS_LIBRES = {"titulo", "detalle"}


def _norm_contrato(x):
    if isinstance(x, dict):
        return {k: _norm_contrato(v) for k, v in x.items()
                if not k.startswith("_") and k not in _CAMPOS_LIBRES}
    if isinstance(x, list):
        return [_norm_contrato(v) for v in x]
    return x


def _norm_manifiesto(m: dict) -> dict:
    """Además de la normalización general, la procedencia es metadato de
    generación: se compara reglas_md5 (exacto) y la PRESENCIA de generado_por,
    no su literal (el expected lo generó el oráculo manual; el recompute, el service)."""
    m = _norm_contrato(m)
    p = m.get("procedencia", {}) or {}
    m["procedencia"] = {"reglas_md5": p.get("reglas_md5"),
                        "tiene_generado_por": bool(p.get("generado_por"))}
    return m


def _diffs(exp, got, tol_tras: float, tol_rot: float,
           path: str = "", clave=None, out=None) -> list[str]:
    """Comparación profunda expected vs recompute con las tolerancias del caso."""
    if out is None:
        out = []
    if isinstance(exp, dict) and isinstance(got, dict):
        for k in sorted(set(exp) | set(got)):
            if k not in exp:
                out.append(f"{path}/{k}: clave no esperada")
            elif k not in got:
                out.append(f"{path}/{k}: falta en el recompute")
            else:
                _diffs(exp[k], got[k], tol_tras, tol_rot, f"{path}/{k}", k, out)
    elif isinstance(exp, list) and isinstance(got, list):
        if len(exp) != len(got):
            out.append(f"{path}: longitud {len(exp)} vs {len(got)}")
        else:
            for i, (a, b) in enumerate(zip(exp, got)):
                _diffs(a, b, tol_tras, tol_rot, f"{path}[{i}]", clave, out)
    elif isinstance(exp, float) or isinstance(got, float):
        tol = tol_tras if clave == "traslacion" else (tol_rot if clave == "rotacion_deg" else 0.0)
        if abs(float(exp) - float(got)) > tol:
            out.append(f"{path}: {exp} vs {got} (tol ±{tol})")
    elif exp != got:
        out.append(f"{path}: {exp!r} vs {got!r}")
    return out


def _recompute_c4(case_dir: Path, reglas: dict, repo: Path) -> tuple[dict, dict]:
    """Cierra la costura: federar+validar con services/federacion (import de path,
    mismo patrón que engines/ifc). Un fallo aquí se investiga en el SERVICE,
    jamás en expected.json (regla de oro)."""
    p = str(repo / "services" / "federacion" / "src")
    if p not in sys.path:
        sys.path.insert(0, p)
    from aqyra_federacion import federar_fichero, validar
    manifiesto = federar_fichero(case_dir / "reglas.json")
    pack = reglas.get("ids_pack", {})
    pack_dir = (repo / "data" / "packs" / str(pack.get("familia", "ids"))
                / str(pack.get("id")) / str(pack.get("version")))
    informe = validar(manifiesto, pack_dir, case_dir)
    return manifiesto, informe


def _derivar_c4(case_dir: Path, expected: dict, man_rec: dict, checks: list,
                tmpdir: Path):
    """Fase II·h6 (D26/D30): paso de DERIVACIÓN, activado por el expected
    (presencia de maestro_manifiesto.ifc_derivado — patrón D14: 01–05 ni pasan
    por aquí). Deriva con el service en un directorio temporal, ancla el .ifc
    por md5 BYTE A BYTE (D26, cabecera determinista con time_stamp inyectado de
    derivado_generacion) y devuelve el manifiesto actualizado (con ifc_derivado,
    que el diff compara contra el expected — doble anclaje) + la ruta del
    derivado (la CÁMARA del BCF lo consume — D29)."""
    from aqyra_federacion import derivar
    exp_der = expected["maestro_manifiesto"]["ifc_derivado"]
    gen = expected.get("derivado_generacion", {})
    salida = tmpdir / exp_der.get("fichero", "federado.ifc")
    man_rec = derivar(man_rec, case_dir, salida, fecha=gen.get("fecha"))
    got = man_rec["ifc_derivado"]["md5"]
    exp_md5 = exp_der.get("md5")
    checks.append(("derivación IFC federado ejecuta", True,
                   f"'{salida.name}' escrito (cabecera SPF determinista)"))
    checks.append(("derivado md5 == expected (byte a byte)", got == exp_md5,
                   f"md5 {got[:12]}… (esperado {str(exp_md5)[:12]}…)"))
    return man_rec, salida


def _emitir_bcf_c4(inf_rec: dict, expected: dict, checks: list,
                   derivado: Path | None = None) -> dict:
    """Fase II·h3 (tarea 1.2, D14): paso de EMISIÓN, activado por el expected
    (informe_qa.bcf.emitido == true). Emite con el service en un directorio
    temporal, ancla el ÁRBOL BCF 3.0 por md5 de fichero (D12) y devuelve el
    informe actualizado (emitido=true) para el diff contra el expected.
    C4-FED-01 (emitido=false) ni pasa por aquí — su expected no se toca.
    Fase II·h6 (D29): si el caso derivó (paso anterior), la emisión recibe el
    derivado y cada viewpoint gana su CÁMARA determinista — 02/04 (sin derivado)
    quedan intactos POR CONSTRUCCIÓN."""
    import tempfile
    from aqyra_federacion import emitir_bcf
    gen = expected.get("bcf_generacion", {})
    nombre = expected.get("informe_qa", {}).get("bcf", {}).get("carpeta", "bcf")
    with tempfile.TemporaryDirectory() as td:
        carpeta = Path(td) / nombre
        inf_rec = emitir_bcf(inf_rec, carpeta, caso=expected.get("caso"),
                             autor=gen.get("autor"), fecha=gen.get("fecha"),
                             derivado=derivado)
        got = {q.relative_to(carpeta).as_posix(): _md5(q)
               for q in sorted(carpeta.rglob("*")) if q.is_file()}
    checks.append(("emisión BCF 3.0 ejecuta", True,
                   f"{len(got)} fichero/s en '{nombre}/' (un topic por incidencia)"))
    exp = {k: v for k, v in expected.get("bcf_md5", {}).items()
           if not k.startswith("_")}
    dif = sorted(set(exp.items()) ^ set(got.items()))
    checks.append(("árbol BCF == expected (md5/fichero)", got == exp,
                   f"{len(dif)} diff/s — {dif[0][0]}" if dif
                   else f"{len(exp)} fichero/s reproducidos byte a byte"))
    return inf_rec


def run_case_c4(case_dir: Path, contracts_dir: Path, expected: dict, tol: dict,
                repo: Path = DEFAULT_REPO) -> bool:
    """C4: recompute con el service (Fase II·h2) + checks anclados del 2.1 — ver ficha.

    0. RECOMPUTE (costura cerrada): federar+validar con services/federacion sobre
       las entradas congeladas → manifiesto e informe comparados contra el MISMO
       expected.json (tolerancias del caso; texto libre y procedencia normalizados).
       Fase II·h6: si el expected declara ifc_derivado, se ANTEPONE la derivación
       (md5 byte a byte, D26) y la emisión gana la cámara (D29).
    1. Conformidad de esquemas (reglas + manifiesto esperado + informe esperado).
    2. Identidad por hash de las entradas congeladas (triple coherencia de md5).
    3. Coherencia interna (modelos, pack IDS anclado, requisitos ⊆ .ids, veredicto).
    """
    checks: list[tuple[str, bool, str]] = []
    schemas = load_c4_schemas(contracts_dir)
    manifiesto = expected.get("maestro_manifiesto", {})
    informe = expected.get("informe_qa", {})

    reglas_path = case_dir / "reglas.json"
    if not reglas_path.exists():
        print_checks([("reglas.json presente", False, "no encontrado")])
        return False
    reglas = json.loads(reglas_path.read_text(encoding="utf-8"))

    # 0 · RECOMPUTE con el service real (Fase II·h2, D10) — se ANTEPONE al anclado
    tol_tras = float(tol.get("traslacion_m", 0.0))
    tol_rot = float(tol.get("rotacion_deg", 0.0))
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as td6:
            man_rec, inf_rec = _recompute_c4(case_dir, reglas, repo)
            checks.append(("service federar()+validar() ejecuta", True,
                           "services/federacion (import de path)"))
            derivado = None
            if manifiesto.get("ifc_derivado"):
                man_rec, derivado = _derivar_c4(case_dir, expected, man_rec,
                                                checks, Path(td6))   # Fase II·h6 (D26)
            if informe.get("bcf", {}).get("emitido"):
                inf_rec = _emitir_bcf_c4(inf_rec, expected, checks,
                                         derivado)   # Fase II·h3 (D14) + cámara (D29)
            for name, inst, key in (("manifiesto recomputado conforma", man_rec, "manifiesto"),
                                    ("informe recomputado conforma", inf_rec, "informe")):
                ok, detail = validate_against_schema(inst, schemas[key])
                checks.append((name, ok, detail))
            d_man = _diffs(_norm_manifiesto(manifiesto), _norm_manifiesto(man_rec),
                           tol_tras, tol_rot)
            checks.append(("recompute manifiesto == expected", not d_man,
                           f"{len(d_man)} diff/s — {d_man[0]}" if d_man
                           else f"reproducido (±{tol_tras} m, ±{tol_rot}°)"))
            d_inf = _diffs(_norm_contrato(informe), _norm_contrato(inf_rec),
                           tol_tras, tol_rot)
            checks.append(("recompute informe == expected", not d_inf,
                           f"{len(d_inf)} diff/s — {d_inf[0]}" if d_inf
                           else "reproducido (pass/fail, conteos, GUIDs, estados, veredicto)"))
    except Exception as e:  # noqa: BLE001
        checks.append(("recompute con el service", False, f"{type(e).__name__}: {e}"))

    # 1 · conformidad de esquemas
    for name, inst, key in (("reglas conforman esquema", reglas, "reglas"),
                            ("manifiesto esperado conforma", manifiesto, "manifiesto"),
                            ("informe esperado conforma", informe, "informe")):
        ok, detail = validate_against_schema(inst, schemas[key])
        checks.append((name, ok, detail))

    # 2 · identidad de las entradas congeladas (hash) + triple coherencia
    entradas = expected.get("entradas_md5", {})
    checks.append(("entradas declaradas", bool(entradas), f"{len(entradas)} fichero/s"))
    for rel, exp_md5 in sorted(entradas.items()):
        p = case_dir / rel
        if not p.exists():
            checks.append((f"identidad {rel}", False, "fichero no encontrado"))
            continue
        got = _md5(p)
        checks.append((f"identidad {rel}", got == exp_md5,
                       f"md5 {got[:12]}… (esperado {exp_md5[:12]}…)"))
    md5_reglas = {m["fichero"]: m.get("md5") for m in reglas.get("modelos", [])}
    md5_man = {m["fichero_origen"]: m.get("md5") for m in manifiesto.get("modelos", [])}
    checks.append(("md5 reglas == entradas", md5_reglas == entradas,
                   "los md5 de reglas.json anclan los mismos ficheros"))
    checks.append(("md5 manifiesto == entradas", md5_man == entradas,
                   "los md5 del manifiesto anclan los mismos ficheros"))

    # 3 · coherencia interna
    ids_reglas = {m["id"] for m in reglas.get("modelos", [])}
    ids_man = {m["id"] for m in manifiesto.get("modelos", [])}
    ids_estados = set(informe.get("estados", {}).get("por_modelo", {}))
    checks.append(("modelos coherentes", ids_reglas == ids_man == ids_estados,
                   f"reglas={sorted(ids_reglas)} manifiesto={sorted(ids_man)} informe={sorted(ids_estados)}"))

    pack_reglas = reglas.get("ids_pack", {})
    pack_informe = informe.get("ids", {})
    mismo_pack = (pack_reglas.get("id") == pack_informe.get("pack_id")
                  and pack_reglas.get("version") == pack_informe.get("pack_version"))
    checks.append(("pack IDS reglas == informe", mismo_pack,
                   f"{pack_reglas.get('id')}/{pack_reglas.get('version')}"))

    lock_ids = _lock_packs_ids(repo)
    anclado = (lock_ids.get("id") == pack_reglas.get("id")
               and lock_ids.get("version") == pack_reglas.get("version"))
    checks.append(("pack IDS anclado en versions.lock", anclado,
                   f"lock={lock_ids.get('id')}/{lock_ids.get('version')}"))

    pack_dir = repo / "data" / "packs" / "ids" / str(pack_reglas.get("id")) / str(pack_reglas.get("version"))
    ids_ok, ids_detail = False, "pack.json no encontrado"
    if (pack_dir / "pack.json").exists():
        pack = json.loads((pack_dir / "pack.json").read_text(encoding="utf-8"))
        ids_file = pack_dir / pack["contenido"]["fichero"]
        declarados = _ids_identifiers(ids_file)
        exigidos = {r["id"] for r in informe.get("requisitos", []) if r.get("origen", "ids") == "ids"}
        faltan = exigidos - declarados
        ids_ok = not faltan
        ids_detail = (f"{sorted(exigidos)} ⊆ .ids" if ids_ok
                      else f"requisitos SIN respaldo en el .ids: {sorted(faltan)}")
    checks.append(("requisitos (origen=ids) ⊆ .ids del pack", ids_ok, ids_detail))

    resultados = [r.get("resultado") for r in informe.get("requisitos", [])]
    esperado_veredicto = "no-conforme" if "fail" in resultados else "conforme"
    checks.append(("veredicto coherente", informe.get("veredicto") == esperado_veredicto,
                   f"{informe.get('veredicto')} (requisitos: "
                   f"{resultados.count('pass')} pass / {resultados.count('fail')} fail)"))

    print_checks(checks)
    return all(ok for _, ok, _ in checks)


# --------------------------------------------------------------------------- #
# C3 · cumplimiento — modo ANCLADO (contract-first, Fase III·h2 — sin engine)  #
# --------------------------------------------------------------------------- #
RESULTADOS_C3 = {"cumple", "no-cumple", "no-aplica", "no-verificable"}


def _lock_packs(repo: Path, clave: str) -> dict:
    """Sección [packs.<clave>] de versions.lock (ancla del pack)."""
    try:  # Python 3.11+
        import tomllib
    except ModuleNotFoundError:  # 3.10
        import tomli as tomllib
    with open(repo / "versions.lock", "rb") as f:
        lock = tomllib.load(f)
    return lock.get("packs", {}).get(clave, {})


# Casa del engine C3 (Fase III·h3, D6): engines/cumplimiento — importado por path (patrón
# engines/ifc y _recompute_c4). El runner regenera el Maestro y el engine da el veredicto (D7).
DEFAULT_ENGINE_C3 = DEFAULT_REPO / "engines" / "cumplimiento" / "src"

# Texto libre del veredicto C3 (presentación humana): se comprueba por esquema (presencia/tipo)
# pero NO se compara literalmente en el recompute (D9) — la semántica del contrato son ids,
# resultados, referencias, conteos y veredicto. Ídem claves '_*'.
_LIBRES_C3 = {"evidencia", "motivo_no_verificable", "exigencia", "detalle"}


def _norm_c3(x):
    if isinstance(x, dict):
        return {k: _norm_c3(v) for k, v in x.items()
                if not k.startswith("_") and k not in _LIBRES_C3}
    if isinstance(x, list):
        return [_norm_c3(v) for v in x]
    return x


def _recompute_c3(case_dir: Path, entrada: dict, repo: Path, tmpdir: Path) -> dict:
    """Cierra la costura C3 (Fase III·h3, D9): regenera el Maestro con services/federacion
    (federar+derivar — el engine NO federa, D7) y emite el veredicto con engines/cumplimiento
    (import de path). Un fallo aquí se investiga en el ENGINE, jamás en expected.json."""
    ps = str(repo / "services" / "federacion" / "src")
    if ps not in sys.path:
        sys.path.insert(0, ps)
    pe = str(DEFAULT_ENGINE_C3)
    if pe not in sys.path:
        sys.path.insert(0, pe)
    from aqyra_federacion import federar_fichero, derivar
    from aqyra_cumplimiento import verificar
    manifiesto = federar_fichero(case_dir / "reglas.json")
    derivado = Path(tmpdir) / "federado.ifc"
    manifiesto = derivar(manifiesto, case_dir, derivado)
    pack = entrada.get("pack_normativo", {})
    pack_dir = (repo / "data" / "packs" / "normativa"
                / str(pack.get("id")) / str(pack.get("version")))
    maestro = {"manifiesto": manifiesto, "base_dir": case_dir,
               "ifc_derivado": derivado, "proyecto": entrada.get("proyecto")}
    return verificar(maestro, entrada.get("uso", {}),
                     entrada.get("localizacion", {}), pack_dir)


def run_case_c3(case_dir: Path, contracts_dir: Path, expected: dict, tol: dict,
                repo: Path = DEFAULT_REPO) -> bool:
    """C3: RECOMPUTE con el engine (Fase III·h3, D9) + checks anclados del 3.2 — ver ficha.

    El engine `engines/cumplimiento` (D6) regenera el Maestro (federar+derivar con el service, D7)
    y emite el veredicto POR EXIGENCIA; el runner lo ANTEPONE contra el MISMO expected (el checklist
    FIRMADO que era el oráculo del modo anclado), normalizando el texto libre (D9). Conserva íntegros
    los checks anclados del 2.1/3.2 (D10: más checks, nunca menos):

      0. RECOMPUTE (costura cerrada): engine.verificar() == expected["veredicto_cumplimiento"].
      1. Conformidad de los 2 esquemas (entrada + veredicto).
      2. Identidad por hash (entradas del C4-FED-06 reutilizadas + derivado anclado; reglas
         regeneran el Maestro).
      3. Coherencia del pack (entrada == veredicto == versions.lock; exigencias ⊆ pack CTE).
      4. Taxonomía CERRADA de resultado (D4) + motivo en cada no-verificable.
      5. resumen == recuento real.
      6. Veredicto agregado según la regla D4.
      7. uso/localización coherentes entrada↔veredicto.
      8. por_modelo ⊆ modelos de la entrada.
    """
    from collections import Counter

    checks: list[tuple[str, bool, str]] = []
    schemas = load_c3_schemas(contracts_dir)

    entrada_path = case_dir / "entrada.json"
    if not entrada_path.exists():
        print_checks([("entrada.json presente", False, "no encontrado")])
        return False
    entrada = json.loads(entrada_path.read_text(encoding="utf-8"))
    vc = expected.get("veredicto_cumplimiento", {})

    # 0 · RECOMPUTE con el engine real (Fase III·h3, D9) — se ANTEPONE al anclado.
    # Regenera el Maestro (federar+derivar) y emite el veredicto con engines/cumplimiento
    # contra el MISMO expected (D10: más checks, nunca menos). Un fallo se investiga en el engine.
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            got = _recompute_c3(case_dir, entrada, repo, Path(td))
            checks.append(("engine cumplimiento verificar() ejecuta", True,
                           "engines/cumplimiento sobre el Maestro regenerado (federar+derivar)"))
            ok, detail = validate_against_schema(got, schemas["veredicto"])
            checks.append(("veredicto recomputado conforma", ok, detail))
            d_vc = _diffs(_norm_c3(vc), _norm_c3(got), 0.0, 0.0)
            checks.append(("recompute veredicto == expected", not d_vc,
                           f"{len(d_vc)} diff/s — {d_vc[0]}" if d_vc
                           else "reproducido (ids, resultados, referencias, por_modelo, resumen, veredicto)"))
    except Exception as e:  # noqa: BLE001
        checks.append(("recompute con el engine", False, f"{type(e).__name__}: {e}"))

    # 1 · conformidad de esquemas
    for name, inst, key in (("entrada conforma esquema", entrada, "entrada"),
                            ("veredicto conforma esquema", vc, "veredicto")):
        ok, detail = validate_against_schema(inst, schemas[key])
        checks.append((name, ok, detail))

    # 2 · identidad por hash (entradas del 06 + derivado anclado)
    entradas = expected.get("entradas_md5", {})
    checks.append(("entradas declaradas", bool(entradas), f"{len(entradas)} fichero/s"))
    for rel, exp_md5 in sorted(entradas.items()):
        p = case_dir / rel
        if not p.exists():
            checks.append((f"identidad {rel}", False, "fichero no encontrado"))
            continue
        got = _md5(p)
        checks.append((f"identidad {rel}", got == exp_md5,
                       f"md5 {got[:12]}… (esperado {exp_md5[:12]}…)"))
    md5_entrada = {m["fichero"]: m.get("md5")
                   for m in entrada.get("modelo", {}).get("modelos", [])}
    checks.append(("md5 entrada == entradas", md5_entrada == entradas,
                   "los md5 de entrada.json anclan los mismos ficheros"))
    der_ent = entrada.get("modelo", {}).get("ifc_derivado_md5")
    der_exp = expected.get("maestro", {}).get("ifc_derivado_md5")
    checks.append(("derivado (vista del Maestro) coherente", bool(der_ent) and der_ent == der_exp,
                   f"{str(der_ent)[:12]}… (entrada == expected)"))
    reglas_rel = entrada.get("modelo", {}).get("reglas")
    if reglas_rel:
        rp = case_dir / reglas_rel
        if not rp.exists():
            checks.append(("reglas.json presente", False, f"{reglas_rel} no encontrado"))
        else:
            reglas = json.loads(rp.read_text(encoding="utf-8"))
            md5_reglas = {m["fichero"]: m.get("md5") for m in reglas.get("modelos", [])}
            checks.append(("reglas regeneran el Maestro (md5 == entradas)", md5_reglas == entradas,
                           "las reglas de federación anclan los mismos IFC"))

    # 3 · coherencia del pack
    pack_ent = entrada.get("pack_normativo", {})
    pack_ver = vc.get("pack", {})
    mismo_pack = (pack_ent.get("id") == pack_ver.get("id")
                  and pack_ent.get("version") == pack_ver.get("version"))
    checks.append(("pack entrada == veredicto", mismo_pack,
                   f"{pack_ent.get('id')}/{pack_ent.get('version')}"))
    lock_norm = _lock_packs(repo, "normativa")
    anclado = (lock_norm.get("id") == pack_ent.get("id")
               and lock_norm.get("version") == pack_ent.get("version"))
    checks.append(("pack anclado en versions.lock", anclado,
                   f"lock={lock_norm.get('id')}/{lock_norm.get('version')}"))
    exigidos = [e.get("id") for e in vc.get("exigencias", [])]
    pack_dir = (repo / "data" / "packs" / "normativa"
                / str(pack_ent.get("id")) / str(pack_ent.get("version")))
    exig_ok, exig_detail = False, "pack.json no encontrado"
    if (pack_dir / "pack.json").exists():
        pack = json.loads((pack_dir / "pack.json").read_text(encoding="utf-8"))
        exig_file = pack_dir / pack["contenido"]["fichero"]
        declarados = {e["id"] for e in
                      json.loads(exig_file.read_text(encoding="utf-8")).get("exigencias", [])}
        faltan = set(exigidos) - declarados
        exig_ok = bool(exigidos) and not faltan
        exig_detail = (f"{sorted(exigidos)} ⊆ pack" if exig_ok
                       else f"exigencias SIN respaldo en el pack: {sorted(faltan)}")
    checks.append(("exigencias ⊆ pack CTE", exig_ok, exig_detail))

    # 4 · taxonomía CERRADA (D4) + motivo en no-verificable
    resultados = [e.get("resultado") for e in vc.get("exigencias", [])]
    checks.append(("taxonomía de resultado cerrada", all(r in RESULTADOS_C3 for r in resultados),
                   f"{sorted(set(resultados))}"))
    nv = [e for e in vc.get("exigencias", []) if e.get("resultado") == "no-verificable"]
    checks.append(("no-verificable declara motivo", all(e.get("motivo_no_verificable") for e in nv),
                   f"{len(nv)} no-verificable/s con motivo"))

    # 5 · resumen == recuento real
    cnt = Counter(resultados)
    resumen = vc.get("resumen", {})
    por = resumen.get("por_resultado", {})
    conteo_ok = (resumen.get("total") == len(resultados)
                 and all(por.get(k, 0) == cnt.get(k, 0) for k in RESULTADOS_C3)
                 and sum(por.get(k, 0) for k in RESULTADOS_C3) == len(resultados))
    checks.append(("resumen == recuento real", conteo_ok,
                   f"total {resumen.get('total')} · {dict(cnt)}"))

    # 6 · veredicto agregado (regla D4)
    if "no-cumple" in resultados:
        esperado = "no-conforme"
    elif "no-verificable" in resultados:
        esperado = "conforme-con-reservas"
    else:
        esperado = "conforme"
    checks.append(("veredicto agregado coherente", vc.get("veredicto") == esperado,
                   f"{vc.get('veredicto')} (esperado {esperado})"))

    # 7 · uso/localización coherentes entrada↔veredicto
    checks.append(("uso coherente entrada↔veredicto",
                   entrada.get("uso", {}).get("principal") == vc.get("uso", {}).get("principal"),
                   f"{vc.get('uso', {}).get('principal')}"))
    loc_e, loc_v = entrada.get("localizacion", {}), vc.get("localizacion", {})
    loc_keys = ("pais", "provincia", "municipio", "zona_climatica_he")
    checks.append(("localización coherente entrada↔veredicto",
                   all(loc_e.get(k) == loc_v.get(k) for k in loc_keys),
                   f"{loc_v.get('municipio')} ({loc_v.get('zona_climatica_he')})"))

    # 8 · por_modelo ⊆ modelos de la entrada
    ids_entrada = {m["id"] for m in entrada.get("modelo", {}).get("modelos", [])}
    pm_ids: set[str] = set()
    for e in vc.get("exigencias", []):
        pm_ids |= set((e.get("por_modelo") or {}).keys())
    checks.append(("por_modelo ⊆ modelos entrada", pm_ids <= ids_entrada,
                   f"por_modelo={sorted(pm_ids)} ⊆ {sorted(ids_entrada)}"))

    print_checks(checks)
    return all(ok for _, ok, _ in checks)


# --------------------------------------------------------------------------- #
# C5 · presupuesto — modo ANCLADO (contract-first, Fase IV·h1 — sin engine)     #
# --------------------------------------------------------------------------- #
ORIGEN_C5 = {"modelo", "regla", "manual"}

# Casa del engine C5 (hilo posterior): engines/presupuesto — se importará por path (patrón
# engines/ifc y _recompute_c4/_recompute_c3). El runner regenerará la medición desde los Qto
# (parser) y el motor dará el presupuesto; aquí, modo ANCLADO (oráculo congelado, sin engine).
DEFAULT_ENGINE_C5 = DEFAULT_REPO / "engines" / "presupuesto" / "src"


def load_c5_schemas(contracts_dir: Path) -> dict[str, dict]:
    base = contracts_dir / "C5-presupuesto"
    out = {}
    for key, fname in (("entrada", "entrada-presupuesto.schema.json"),
                       ("salida", "salida-presupuesto.schema.json")):
        out[key] = json.loads((base / fname).read_text(encoding="utf-8"))
    return out


def _pack_c5(repo: Path, familia: str, ref: dict) -> tuple[dict, Path]:
    """Carga el pack.json de un pack C5 (criterio/banco) y devuelve (manifiesto, dir)."""
    pack_dir = (repo / "data" / "packs" / familia
                / str(ref.get("id")) / str(ref.get("version")))
    return json.loads((pack_dir / "pack.json").read_text(encoding="utf-8")), pack_dir


def _pack_contenido_c5(repo: Path, familia: str, ref: dict) -> dict:
    """Contenido (criterio.json / banco.json) de un pack C5, por su manifiesto."""
    man, pdir = _pack_c5(repo, familia, ref)
    return json.loads((pdir / man["contenido"]["fichero"]).read_text(encoding="utf-8"))


# Texto libre del presupuesto C5 (presentación humana): se comprueba por esquema (presencia/tipo)
# pero NO se compara literalmente en el recompute (D9). La semántica del contrato son códigos,
# cantidades, precios, importes, capítulos y trazabilidad; descripciones y justificaciones (incluida
# la letra del nº1) son presentación.
_LIBRES_C5 = {"descripcion", "criterio_aplicado", "precio_en_letra", "nota", "proyecto"}


def _recompute_c5(case_dir: Path, entrada: dict, repo: Path) -> tuple[dict, dict]:
    """Cierra la costura C5 (Fase IV·h2, D9): el engine engines/presupuesto MIDE desde las fixtures
    con Qto (parser, módulo 1 — la medición NACE del modelo, D7) y PRESUPUESTA (motor). El runner lo
    ANTEPONE contra el MISMO expected. Un fallo aquí se investiga en el ENGINE, jamás en expected."""
    pe = str(DEFAULT_ENGINE_C5)
    if pe not in sys.path:
        sys.path.insert(0, pe)
    from aqyra_presupuesto import medir, presupuestar
    fuentes = [
        {"id": m.get("id"), "disciplina": m.get("disciplina"),
         "path": case_dir / m["fichero"], "fichero": m["fichero"]}
        for m in entrada.get("modelo", {}).get("fuente_maestro", {}).get("modelos", [])
    ]
    modelo = medir(fuentes)
    modelo["proyecto"] = entrada.get("proyecto")
    criterio = _pack_contenido_c5(repo, "criterio", entrada.get("criterio_ref", {}))
    banco = _pack_contenido_c5(repo, "banco", entrada.get("banco_ref", {}))
    return modelo, presupuestar(modelo, criterio, banco, entrada.get("parametros", {}))


def _diff_medicion_c5(medido: dict, entrada_modelo: dict, tol: dict) -> list[str]:
    """El parser reproduce las cantidades que el modelo neutro declara (la medición nace del Qto)."""
    rel = float(tol.get("cantidad_rel", 0.005))
    got = {o.get("guid"): o for o in medido.get("objetos", [])}
    diffs: list[str] = []
    for obj in entrada_modelo.get("objetos", []):
        gd = obj.get("guid")
        if gd not in got:
            diffs.append(f"objeto {gd} no medido por el parser")
            continue
        gmag = {c.get("magnitud"): c.get("valor") for c in got[gd].get("cantidades", [])}
        for c in obj.get("cantidades", []):
            mag = c.get("magnitud")
            if mag == "conteo":
                continue
            if mag not in gmag:
                diffs.append(f"{gd}: falta magnitud {mag}")
            elif abs(float(gmag[mag]) - float(c.get("valor", 0))) > rel * max(1.0, abs(float(c.get("valor", 0)))):
                diffs.append(f"{gd}.{mag} medido {gmag[mag]} != {c.get('valor')}")
    return diffs


def _diff_presupuesto_c5(got: dict, exp: dict, tol: dict) -> list[str]:
    """Compara el presupuesto recomputado contra el expected (D3): cantidades ±0,5%; mapeo, precios,
    importes y PEM…PEC EXACTOS (±0,01). Normaliza el texto libre (D9)."""
    rel = float(tol.get("cantidad_rel", 0.005))
    ia = float(tol.get("importe_abs", 0.01))
    diffs: list[str] = []

    def approx(a, b, t) -> bool:
        try:
            return abs(float(a) - float(b)) <= t
        except (TypeError, ValueError):
            return False

    g = {p["codigo"]: p for p in got.get("estado_mediciones", [])}
    e = {p["codigo"]: p for p in exp.get("estado_mediciones", [])}
    if set(g) != set(e):
        diffs.append(f"partidas: faltan {sorted(set(e) - set(g))} / sobran {sorted(set(g) - set(e))}")
    for cod in sorted(set(e) & set(g)):
        a, b = g[cod], e[cod]
        for k in ("capitulo", "unidad", "origen"):
            if a.get(k) != b.get(k):
                diffs.append(f"{cod}.{k}: {a.get(k)} != {b.get(k)}")
        if not approx(a.get("cantidad"), b.get("cantidad"), rel * max(1.0, abs(float(b.get("cantidad", 0))))):
            diffs.append(f"{cod}.cantidad: {a.get('cantidad')} != {b.get('cantidad')}")
        if not approx(a.get("precio_unitario"), b.get("precio_unitario"), ia):
            diffs.append(f"{cod}.precio_unitario: {a.get('precio_unitario')} != {b.get('precio_unitario')}")
        if not approx(a.get("importe"), b.get("importe"), ia):
            diffs.append(f"{cod}.importe: {a.get('importe')} != {b.get('importe')}")
        if set(a.get("trazabilidad", [])) != set(b.get("trazabilidad", [])):
            diffs.append(f"{cod}.trazabilidad != expected")

    g1 = {c["codigo"]: c for c in got.get("cuadro_precios_1", [])}
    for cod, c in {c["codigo"]: c for c in exp.get("cuadro_precios_1", [])}.items():
        if cod not in g1:
            diffs.append(f"nº1 falta {cod}")
        elif not approx(g1[cod].get("precio"), c.get("precio"), ia) or g1[cod].get("unidad") != c.get("unidad"):
            diffs.append(f"nº1 {cod}: precio/unidad")

    g2 = {c["codigo"]: c for c in got.get("cuadro_precios_2", [])}
    for cod, c in {c["codigo"]: c for c in exp.get("cuadro_precios_2", [])}.items():
        if cod not in g2:
            diffs.append(f"nº2 falta {cod}")
            continue
        if not approx(g2[cod].get("precio_total"), c.get("precio_total"), ia):
            diffs.append(f"nº2 {cod}.precio_total")
        if not approx(g2[cod].get("costes_indirectos"), c.get("costes_indirectos"), ia):
            diffs.append(f"nº2 {cod}.costes_indirectos")
        gc, ec = g2[cod].get("componentes", []), c.get("componentes", [])
        if len(gc) != len(ec):
            diffs.append(f"nº2 {cod}.componentes: {len(gc)} != {len(ec)}")
        else:
            for i, (x, y) in enumerate(zip(gc, ec)):
                if x.get("tipo") != y.get("tipo") or not approx(x.get("subtotal"), y.get("subtotal"), ia):
                    diffs.append(f"nº2 {cod}.comp[{i}]")

    gr, er = got.get("resumen", {}), exp.get("resumen", {})
    for k in ("PEM", "gg", "bi", "base", "iva", "PEC", "gg_pct", "bi_pct", "iva_pct"):
        if not approx(gr.get(k), er.get(k), ia):
            diffs.append(f"resumen.{k}: {gr.get(k)} != {er.get(k)}")
    if gr.get("moneda") != er.get("moneda"):
        diffs.append("resumen.moneda")
    gcp = {c["codigo"]: c for c in gr.get("capitulos", [])}
    for cod, c in {c["codigo"]: c for c in er.get("capitulos", [])}.items():
        if cod not in gcp:
            diffs.append(f"capítulo falta {cod}")
            continue
        if not approx(gcp[cod].get("importe"), c.get("importe"), ia):
            diffs.append(f"capítulo {cod}.importe")
        if set(gcp[cod].get("partidas", [])) != set(c.get("partidas", [])):
            diffs.append(f"capítulo {cod}.partidas")
    return diffs


def _checks_5d(f, pres: dict, cost: dict, ia: float) -> list[tuple[str, bool, str]]:
    """Comprueba que el cost schedule del IFC 5D CASA con el presupuesto (D14, semántica)."""
    out: list[tuple[str, bool, str]] = []

    def approx(a, b) -> bool:
        try:
            return abs(float(a) - float(b)) <= ia
        except (TypeError, ValueError):
            return False

    def _val(cv):
        av = cv.AppliedValue
        return float(getattr(av, "wrappedValue", av))

    scheds = f.by_type("IfcCostSchedule")
    out.append(("IfcCostSchedule (BUDGET) presente",
                len(scheds) == 1 and getattr(scheds[0], "PredefinedType", None) == cost.get("predefined_type", "BUDGET"),
                f"{len(scheds)} schedule/s"))
    munits = f.by_type("IfcMonetaryUnit")
    out.append(("IfcMonetaryUnit == moneda",
                any(getattr(u, "Currency", None) == cost.get("moneda", "EUR") for u in munits),
                f"{[getattr(u, 'Currency', None) for u in munits]}"))

    items = {ci.Identification: ci for ci in f.by_type("IfcCostItem")
             if getattr(ci, "Identification", None)}
    em = pres.get("estado_mediciones", [])

    malos = []
    for l in em:
        ci = items.get(l["codigo"])
        if ci is None or not ci.CostValues or not approx(_val(ci.CostValues[0]), l["importe"]):
            malos.append(l["codigo"])
    out.append(("IfcCostItem por partida con IfcCostValue == importe", not malos,
                "todas las partidas" if not malos else f"descuadran: {malos}"))

    asg: dict[str, set] = {}
    for rel in f.by_type("IfcRelAssignsToControl"):
        cod = getattr(rel.RelatingControl, "Identification", None)
        if not cod:
            continue
        guids = set()
        for o in rel.RelatedObjects or []:
            try:
                guids.add(o.GlobalId)
            except Exception:  # noqa: BLE001
                pass
        asg[cod] = guids
    mal_asg, n_asg = [], 0
    for l in em:
        tz = set(l.get("trazabilidad", []))
        if not tz:
            continue
        n_asg += 1
        if asg.get(l["codigo"], set()) != tz:
            mal_asg.append(l["codigo"])
    out.append(("IfcRelAssignsToControl == trazabilidad por partida (por GUID)", not mal_asg,
                f"{n_asg} partidas asignadas a sus elementos" if not mal_asg else f"descuadran: {mal_asg}"))
    if "n_partidas_con_asignacion" in cost:
        out.append(("nº de partidas con asignación", n_asg == cost["n_partidas_con_asignacion"],
                    f"{n_asg} (esperado {cost['n_partidas_con_asignacion']})"))

    suma = sum(_val(items[l["codigo"]].CostValues[0]) for l in em
               if items.get(l["codigo"]) and items[l["codigo"]].CostValues)
    PEM = float(pres.get("resumen", {}).get("PEM", 0))
    out.append(("Σ IfcCostValue de partida == PEM", approx(suma, PEM),
                f"Σ {round(suma, 2)} vs PEM {PEM}"))

    res = pres.get("resumen", {})
    res_item = items.get("RESUMEN")
    cat = {}
    if res_item:
        for cv in res_item.CostValues or []:
            cat[str(getattr(cv, "Category", None)).upper()] = _val(cv)
    claves = {"PEM": "PEM", "GG": "gg", "BI": "bi", "BASE": "base", "IVA": "iva", "PEC": "PEC"}
    mal_res = [k for k, rk in claves.items() if rk in res and not approx(cat.get(k), res[rk])]
    out.append(("IfcCostItem resumen == PEM/GG/BI/base/IVA/PEC",
                res_item is not None and not mal_res,
                "coherente" if res_item is not None and not mal_res else f"descuadran: {mal_res}"))

    n_items = len(f.by_type("IfcCostItem"))
    if "n_partidas" in cost and "n_capitulos" in cost:
        esperado = cost["n_partidas"] + cost["n_capitulos"] + 1
        out.append(("nº de IfcCostItem == partidas+capítulos+resumen", n_items == esperado,
                    f"{n_items} (esperado {esperado})"))
    return out


def _run_c5_5d(case_dir: Path, contracts_dir: Path, expected: dict, tol: dict, repo: Path) -> bool:
    """C5 write-back 5D (Fase IV·h3, D11–D14): el coste vuelve al modelo. Ancla por DETERMINISMO
    (escribir 2× = bytes idénticos) + SEMÁNTICA (el cost schedule casa con el presupuesto). Opción b:
    sin md5 hardcodeado — el gate genera y verifica el 5D con ifcopenshell. Un fallo se investiga en
    el ENGINE (escritura.py), jamás aflojando el check."""
    import tempfile

    checks: list[tuple[str, bool, str]] = []
    schemas = load_c5_schemas(contracts_dir)
    entrada = json.loads((case_dir / "entrada.json").read_text(encoding="utf-8"))
    ia = float(tol.get("importe_abs", 0.01))
    cost = expected.get("cost_5d", {})

    # 1 · identidad por hash de las fixtures con Qto (reutilizadas del 4.1; intactas)
    for rel, exp_md5 in sorted(expected.get("entradas_md5", {}).items()):
        p = case_dir / rel
        got = _md5(p) if p.exists() else None
        checks.append((f"identidad {rel}", got == exp_md5,
                       f"md5 {str(got)[:12]}… (esperado {exp_md5[:12]}…)"))

    pe = str(DEFAULT_ENGINE_C5)
    if pe not in sys.path:
        sys.path.insert(0, pe)
    ps = str(repo / "services" / "federacion" / "src")
    if ps not in sys.path:
        sys.path.insert(0, ps)
    try:
        import ifcopenshell

        from aqyra_federacion import derivar, federar_fichero
        from aqyra_presupuesto import escribir_coste, medir, presupuestar
    except Exception as e:  # noqa: BLE001
        checks.append(("import engine/servicio/ifcopenshell", False, f"{type(e).__name__}: {e}"))
        print_checks(checks)
        return False

    # 2 · presupuesto (reproduce GOL-PRE-01) desde la medición de las fixtures con Qto
    fuentes = [{"id": m.get("id"), "disciplina": m.get("disciplina"),
                "path": case_dir / m["fichero"], "fichero": m["fichero"]}
               for m in entrada.get("modelo", {}).get("fuente_maestro", {}).get("modelos", [])]
    modelo = medir(fuentes)
    modelo["proyecto"] = entrada.get("proyecto")
    criterio = _pack_contenido_c5(repo, "criterio", entrada.get("criterio_ref", {}))
    banco = _pack_contenido_c5(repo, "banco", entrada.get("banco_ref", {}))
    pres = presupuestar(modelo, criterio, banco, entrada.get("parametros", {}))
    ok, detail = validate_against_schema(pres, schemas["salida"])
    checks.append(("presupuesto (para el 5D) conforma esquema", ok, detail))
    checks.append(("presupuesto reproduce PEM…PEC del oráculo",
                   abs(float(pres.get("resumen", {}).get("PEM", 0)) - float(cost.get("PEM", 0))) <= ia
                   and abs(float(pres.get("resumen", {}).get("PEC", 0)) - float(cost.get("PEC", 0))) <= ia,
                   f"PEM {pres.get('resumen', {}).get('PEM')} PEC {pres.get('resumen', {}).get('PEC')}"))

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        # 3 · federar + derivar el Maestro (el engine ABRE el derivado, no federa — D7)
        manifiesto = federar_fichero(case_dir / "reglas.json", base_dir=case_dir)
        derivado = tdp / "federado.ifc"
        derivar(manifiesto, case_dir, derivado)
        checks.append(("federar+derivar el Maestro", derivado.exists(),
                       "derivado federado de las fixtures con Qto"))
        # 4 · escribir_coste 2× → DETERMINISMO (D14); mismo basename, dirs distintas
        r1 = escribir_coste(pres, derivado, tdp / "a" / "federado_5d.ifc")
        r2 = escribir_coste(pres, derivado, tdp / "b" / "federado_5d.ifc")
        checks.append(("5D determinista (escribir 2× = bytes idénticos)", r1["md5"] == r2["md5"],
                       f"md5 {r1['md5'][:12]}… (== {r2['md5'][:12]}…); {r1['n_cost_items']} cost items, "
                       f"{r1['n_asignaciones']} asignaciones"))
        # 5 · SEMÁNTICA — el cost schedule casa con el presupuesto
        f = ifcopenshell.open(str(tdp / "a" / "federado_5d.ifc"))
        checks.extend(_checks_5d(f, pres, cost, ia))

    print_checks(checks)
    return all(ok for _, ok, _ in checks)


def run_case_c5(case_dir: Path, contracts_dir: Path, expected: dict, tol: dict,
                repo: Path = DEFAULT_REPO) -> bool:
    """C5: presupuesto trazable — modo ANCLADO (contract-first, Fase IV·h1 — ver ficha/DECISIONES).

    El presupuesto esperado (`expected["presupuesto"]`) es el ORÁCULO (medición manual congelada,
    verificada x2). El engine `engines/presupuesto` (hilo posterior) ANTEPONDRÁ el recompute (parser
    de Qto + motor) contra este MISMO expected (costura C1/C3/C4). Modo anclado — más checks que hoy:

      1. Conformidad de los 2 esquemas (entrada + salida).
      2. Identidad por hash de las fixtures con Qto (entradas_md5 == ficheros == modelo neutro).
      3. Packs criterio + banco anclados en versions.lock; refs de la entrada == lock.
      4. Partidas origen=modelo ⊆ banco (precio == banco) y ⊆ criterio; origen=regla no exige banco.
      5. importe == cantidad × precio_unitario (±importe_abs).
      6. precio_unitario == cuadro nº1; nº1 == nº2 (Σ componentes + indirectos).
      7. PEM == Σ importes == Σ capítulos; GG/BI/base/IVA/PEC según parametros.
      8. trazabilidad ⊆ GUIDs del modelo (origen=modelo) / vacía (origen=regla); taxonomía cerrada.
      9. S&S (origen=regla) == ratio del criterio × PEM medible.
    """
    # Dispatch por modo (Fase IV·h3): GOL-PRE-02 (write-back 5D) tiene su propia rama.
    if expected.get("modo") == "5d" or "cost_5d" in expected:
        return _run_c5_5d(case_dir, contracts_dir, expected, tol, repo)

    checks: list[tuple[str, bool, str]] = []
    schemas = load_c5_schemas(contracts_dir)

    entrada_path = case_dir / "entrada.json"
    if not entrada_path.exists():
        print_checks([("entrada.json presente", False, "no encontrado")])
        return False
    entrada = json.loads(entrada_path.read_text(encoding="utf-8"))
    pres = expected.get("presupuesto", {})
    ia = float(tol.get("importe_abs", 0.01))

    def approx(a, b) -> bool:
        try:
            return abs(float(a) - float(b)) <= ia
        except (TypeError, ValueError):
            return False

    # 0 · RECOMPUTE con el engine real (Fase IV·h2, D9) — se ANTEPONE al anclado.
    # engines/presupuesto MIDE desde las fixtures con Qto (la medición nace del modelo, D7) y
    # PRESUPUESTA; se compara contra el MISMO expected (D10 del C4: más checks, nunca menos).
    # Un fallo se investiga en el ENGINE (parser/motor), jamás en el expected.
    try:
        modelo_medido, got_pres = _recompute_c5(case_dir, entrada, repo)
        checks.append(("engine presupuesto medir()+presupuestar() ejecuta", True,
                       "engines/presupuesto sobre las fixtures con Qto"))
        ok, detail = validate_against_schema(got_pres, schemas["salida"])
        checks.append(("presupuesto recomputado conforma", ok, detail))
        d_med = _diff_medicion_c5(modelo_medido, entrada.get("modelo", {}), tol)
        checks.append(("medición nace del modelo (parser reproduce cantidades)", not d_med,
                       f"{len(d_med)} diff/s — {d_med[0]}" if d_med
                       else "cantidades leídas de los Qto del IFC"))
        d_pre = _diff_presupuesto_c5(got_pres, pres, tol)
        checks.append(("recompute presupuesto == expected", not d_pre,
                       f"{len(d_pre)} diff/s — {d_pre[0]}" if d_pre
                       else "reproducido (cantidad/precio/importe/capítulos/PEM…PEC/trazabilidad)"))
    except Exception as e:  # noqa: BLE001
        checks.append(("recompute con el engine", False, f"{type(e).__name__}: {e}"))

    # 1 · conformidad de esquemas
    for name, inst, key in (("entrada conforma esquema", entrada, "entrada"),
                            ("presupuesto conforma esquema", pres, "salida")):
        ok, detail = validate_against_schema(inst, schemas[key])
        checks.append((name, ok, detail))

    # 2 · identidad por hash de las fixtures con Qto
    entradas = expected.get("entradas_md5", {})
    checks.append(("entradas declaradas", bool(entradas), f"{len(entradas)} fichero/s"))
    for rel, exp_md5 in sorted(entradas.items()):
        p = case_dir / rel
        if not p.exists():
            checks.append((f"identidad {rel}", False, "fichero no encontrado"))
            continue
        got = _md5(p)
        checks.append((f"identidad {rel}", got == exp_md5,
                       f"md5 {got[:12]}… (esperado {exp_md5[:12]}…)"))
    md5_modelo = {m["fichero"]: m.get("md5")
                  for m in entrada.get("modelo", {}).get("fuente_maestro", {}).get("modelos", [])}
    checks.append(("md5 modelo neutro == entradas", md5_modelo == entradas,
                   "las fixtures del modelo neutro anclan los mismos IFC con Qto"))

    # 3 · packs criterio + banco anclados en versions.lock
    crit_ref = entrada.get("criterio_ref", {})
    banco_ref = entrada.get("banco_ref", {})
    lock_crit = _lock_packs(repo, "criterio")
    lock_banco = _lock_packs(repo, "banco")
    checks.append(("criterio anclado en versions.lock",
                   lock_crit.get("id") == crit_ref.get("id")
                   and lock_crit.get("version") == crit_ref.get("version"),
                   f"lock={lock_crit.get('id')}/{lock_crit.get('version')}"))
    checks.append(("banco anclado en versions.lock",
                   lock_banco.get("id") == banco_ref.get("id")
                   and lock_banco.get("version") == banco_ref.get("version"),
                   f"lock={lock_banco.get('id')}/{lock_banco.get('version')}"))

    # cargar contenido de los packs (banco.json + criterio.json)
    banco = criterio = None
    try:
        bman, bdir = _pack_c5(repo, "banco", banco_ref)
        banco = json.loads((bdir / bman["contenido"]["fichero"]).read_text(encoding="utf-8"))
        cman, cdir = _pack_c5(repo, "criterio", crit_ref)
        criterio = json.loads((cdir / cman["contenido"]["fichero"]).read_text(encoding="utf-8"))
        checks.append(("packs criterio + banco cargados", True,
                       f"{len(banco.get('partidas', []))} partidas de banco"))
    except Exception as e:  # noqa: BLE001
        checks.append(("packs criterio + banco cargados", False, f"{type(e).__name__}: {e}"))

    precio_banco = {p["codigo"]: p["precio"] for p in (banco or {}).get("partidas", [])}
    codigos_criterio = set()
    for regla in (criterio or {}).get("reglas_por_clase", []):
        for p in regla.get("partidas", []):
            codigos_criterio.add(p["codigo"])
    codigos_sin_geo = {p["codigo"] for p in (criterio or {}).get("reglas_sin_geometria", [])}

    em = pres.get("estado_mediciones", [])
    cp1 = {c["codigo"]: c for c in pres.get("cuadro_precios_1", [])}
    cp2 = {c["codigo"]: c for c in pres.get("cuadro_precios_2", [])}

    # 4 · partidas origen=modelo ⊆ banco (precio) y ⊆ criterio; origen=regla no exige banco
    faltan_banco = [l["codigo"] for l in em
                    if l.get("origen") == "modelo" and l["codigo"] not in precio_banco]
    checks.append(("partidas origen=modelo ⊆ banco", not faltan_banco,
                   "todas con precio en el banco" if not faltan_banco
                   else f"sin respaldo en banco: {faltan_banco}"))
    faltan_crit = [l["codigo"] for l in em
                   if l.get("origen") == "modelo" and l["codigo"] not in codigos_criterio]
    checks.append(("partidas origen=modelo ⊆ criterio", not faltan_crit,
                   "todas mapeadas por el criterio" if not faltan_crit
                   else f"sin regla de medición: {faltan_crit}"))

    # 5 · importe == cantidad × precio_unitario ; 6 · precio == cuadro nº1 == cuadro nº2
    malos_importe, malos_p1, malos_p2 = [], [], []
    for l in em:
        cod = l["codigo"]
        if not approx(l.get("importe"), float(l.get("cantidad", 0)) * float(l.get("precio_unitario", 0))):
            malos_importe.append(cod)
        if cod in cp1 and not approx(l.get("precio_unitario"), cp1[cod].get("precio")):
            malos_p1.append(cod)
        # precio del banco (solo origen=modelo)
        if l.get("origen") == "modelo" and cod in precio_banco and not approx(l.get("precio_unitario"), precio_banco[cod]):
            malos_p1.append(cod + "(banco)")
    checks.append(("importe == cantidad × precio", not malos_importe,
                   "todos" if not malos_importe else f"descuadran: {malos_importe}"))
    checks.append(("precio_unitario == cuadro nº1 (y banco)", not malos_p1,
                   "coherentes" if not malos_p1 else f"descuadran: {malos_p1}"))
    for cod, c2 in cp2.items():
        suma = sum(float(x.get("subtotal", 0)) for x in c2.get("componentes", []))
        suma += float(c2.get("costes_indirectos", 0))
        if not approx(c2.get("precio_total"), suma):
            malos_p2.append(cod)
        if cod in cp1 and not approx(c2.get("precio_total"), cp1[cod].get("precio")):
            malos_p2.append(cod + "(!=nº1)")
    checks.append(("cuadro nº2 == Σ componentes + indirectos == nº1", not malos_p2,
                   "descompuesto cuadra" if not malos_p2 else f"descuadran: {malos_p2}"))
    # todas las partidas medidas tienen cuadro nº1; las origen=modelo, cuadro nº2
    sin_p1 = [l["codigo"] for l in em if l["codigo"] not in cp1]
    sin_p2 = [l["codigo"] for l in em if l.get("origen") == "modelo" and l["codigo"] not in cp2]
    checks.append(("cuadros cubren las partidas", not sin_p1 and not sin_p2,
                   "nº1 todas, nº2 las de modelo" if not sin_p1 and not sin_p2
                   else f"sin nº1: {sin_p1} · sin nº2: {sin_p2}"))

    # 7 · PEM == Σ importes == Σ capítulos ; GG/BI/base/IVA/PEC
    res = pres.get("resumen", {})
    par = entrada.get("parametros", {})
    suma_imp = sum(float(l.get("importe", 0)) for l in em)
    PEM = float(res.get("PEM", 0))
    checks.append(("PEM == Σ importes", approx(PEM, suma_imp),
                   f"PEM {PEM} vs Σ {round(suma_imp, 2)}"))
    caps = res.get("capitulos", [])
    imp_por_cod = {l["codigo"]: float(l.get("importe", 0)) for l in em}
    cap_ok = True
    for c in caps:
        suma_c = sum(imp_por_cod.get(cod, 0) for cod in c.get("partidas", []))
        if not approx(c.get("importe"), suma_c):
            cap_ok = False
    checks.append(("capítulos == Σ partidas y Σ capítulos == PEM",
                   cap_ok and approx(sum(float(c.get("importe", 0)) for c in caps), PEM),
                   f"{len(caps)} capítulos"))
    gg = float(par.get("gg_pct", 0)) * PEM
    bi = float(par.get("bi_pct", 0)) * PEM
    base = PEM + gg + bi
    iva = float(par.get("iva_pct", 0)) * base
    pec = base + iva
    econ_ok = (approx(res.get("gg"), gg) and approx(res.get("bi"), bi)
               and approx(res.get("base"), base) and approx(res.get("iva"), iva)
               and approx(res.get("PEC"), pec))
    checks.append(("GG/BI/base/IVA/PEC según parametros", econ_ok,
                   f"PEC {res.get('PEC')} (esperado {round(pec, 2)})"))

    # 8 · trazabilidad ⊆ GUIDs del modelo (origen=modelo) / vacía (origen=regla); taxonomía cerrada
    guids = {o["guid"] for o in entrada.get("modelo", {}).get("objetos", [])}
    traza_ok = True
    origen_ok = True
    for l in em:
        org = l.get("origen")
        if org not in ORIGEN_C5:
            origen_ok = False
        tz = set(l.get("trazabilidad", []))
        if org == "modelo" and not (tz and tz <= guids):
            traza_ok = False
        if org == "regla" and tz:
            traza_ok = False
    checks.append(("origen taxonomía cerrada (modelo/regla/manual)", origen_ok,
                   f"{sorted({l.get('origen') for l in em})}"))
    checks.append(("trazabilidad ⊆ GUIDs del modelo", traza_ok,
                   f"{len(guids)} objetos en el modelo neutro"))

    # 9 · S&S (origen=regla) == ratio del criterio × PEM medible
    pem_medible = sum(float(l.get("importe", 0)) for l in em if l.get("origen") == "modelo")
    reglas_sg = {p["codigo"]: p for p in (criterio or {}).get("reglas_sin_geometria", [])}
    sys_ok, sys_detail = True, "sin partidas de regla"
    for l in em:
        if l.get("origen") == "regla" and l["codigo"] in reglas_sg:
            ratio = float(reglas_sg[l["codigo"]].get("ratio", 0))
            esperado = ratio * pem_medible
            sys_ok = approx(l.get("importe"), esperado)
            sys_detail = f"{l['codigo']} {l.get('importe')} (esperado {round(esperado, 2)} = {ratio}×{round(pem_medible, 2)})"
    checks.append(("partida por regla == ratio × PEM medible", sys_ok, sys_detail))

    print_checks(checks)
    return all(ok for _, ok, _ in checks)


CASE_RUNNERS = {"C1": run_case_c1, "C4": run_case_c4, "C3": run_case_c3, "C5": run_case_c5}


# --------------------------------------------------------------------------- #
# Orquestación                                                                #
# --------------------------------------------------------------------------- #
def discover_cases(golden_dir: Path) -> list[Path]:
    cases = []
    for contract_dir in sorted(golden_dir.glob("C*")):
        if not contract_dir.is_dir():
            continue
        for case_dir in sorted(contract_dir.iterdir()):
            if case_dir.is_dir() and (case_dir / "expected.json").exists():
                cases.append(case_dir)
    return cases


def print_checks(checks, indent="    "):
    for name, ok, detail in checks:
        mark = f"{GREEN}[OK]{RST}" if ok else f"{RED}[FALLA]{RST}"
        print(f"{indent}{mark} {name:<38} {DIM}{detail}{RST}")


def run(golden_dir: Path, contracts_dir: Path, schema_only: bool) -> int:
    print(f"{DIM}contracts: {contracts_dir}{RST}")
    print(f"{DIM}golden:    {golden_dir}{RST}\n")

    schemas = discover_schemas(contracts_dir)
    schema_checks = check_schemas_wellformed(schemas)
    print("Paso 1 · esquemas de contrato (JSON Schema válido):")
    print_checks(schema_checks)
    all_ok = all(ok for _, ok, _ in schema_checks)

    if schema_only:
        verdict = "VERDE" if all_ok else "ROJO"
        color = GREEN if all_ok else RED
        print(f"\n{color}SCHEMA-CHECK: {verdict}{RST}")
        return 0 if all_ok else 1

    cases = discover_cases(golden_dir)
    if not cases:
        print(f"{RED}No hay casos golden con expected.json bajo {golden_dir}{RST}")
        return 1

    print(f"\nPaso 2 · golden ({len(cases)} caso/s):")
    for case_dir in cases:
        contract = case_dir.parent.name
        expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
        tol_path = case_dir / "tolerancias.json"
        tol = json.loads(tol_path.read_text(encoding="utf-8")) if tol_path.exists() else {}
        name = expected.get("caso", case_dir.name)
        runner = CASE_RUNNERS.get(contract)
        print(f"\n  ▶ {name} {DIM}[{contract}]{RST}")
        if runner is None:
            print_checks([("contrato con runner", False,
                           f"'{contract}' sin modo de ejecución en CASE_RUNNERS")])
            all_ok = False
            continue
        all_ok &= runner(case_dir, contracts_dir, expected, tol)

    verdict = "VERDE" if all_ok else "ROJO"
    color = GREEN if all_ok else RED
    print(f"\n{color}VEREDICTO GOLDEN (Llave 1): {verdict}{RST}")
    print(f"{DIM}La firma (Llave 2) es humana; el CI nunca certifica.{RST}")
    return 0 if all_ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Runner de la golden (Llave 1) — multi-contrato.")
    ap.add_argument("--golden-dir", type=Path, default=DEFAULT_GOLDEN_DIR)
    ap.add_argument("--contracts-dir", type=Path, default=None,
                    help="por defecto: <repo>/packages/contracts")
    ap.add_argument("--schema-only", action="store_true",
                    help="solo el paso 1 (esquemas bien formados)")
    args = ap.parse_args()

    golden_dir = args.golden_dir.resolve()
    contracts_dir = (args.contracts_dir or (golden_dir.parent / "contracts")).resolve()
    return run(golden_dir, contracts_dir, args.schema_only)


if __name__ == "__main__":
    raise SystemExit(main())
# Fase I · hilo 1: costura cerrada (compile real narración→IFC). Ver engines/ifc/compile_c1.py.
# Fase II · hilo 1: dispatch por contrato (CASE_RUNNERS); C4 en modo ANCLADO hasta el service (1.1).
# Fase II · hilo 2: costura C4 CERRADA — recompute federar+validar con services/federacion (D10).
# Fase II · hilo 3: emisión BCF 3.0 (tarea 1.2) — paso activado por el expected (C4-FED-02, D14).
# Fase II · hilo 6: derivación IFC (D26/D30) — paso activado por el expected (C4-FED-06); cámara BCF (D29).
# Fase III · hilo 2: contrato C3 (cumplimiento) contract-first — run_case_c3 en modo ANCLADO (D5); el
#                    engine engines/cumplimiento (3.3) antepondrá el recompute contra el MISMO expected.
