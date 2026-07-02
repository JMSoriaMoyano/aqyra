#!/usr/bin/env python3
"""Runner de la golden (Llave 1) — multi-contrato (C1 + C4).

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


def _emitir_bcf_c4(inf_rec: dict, expected: dict, checks: list) -> dict:
    """Fase II·h3 (tarea 1.2, D14): paso de EMISIÓN, activado por el expected
    (informe_qa.bcf.emitido == true). Emite con el service en un directorio
    temporal, ancla el ÁRBOL BCF 3.0 por md5 de fichero (D12) y devuelve el
    informe actualizado (emitido=true) para el diff contra el expected.
    C4-FED-01 (emitido=false) ni pasa por aquí — su expected no se toca."""
    import tempfile
    from aqyra_federacion import emitir_bcf
    gen = expected.get("bcf_generacion", {})
    nombre = expected.get("informe_qa", {}).get("bcf", {}).get("carpeta", "bcf")
    with tempfile.TemporaryDirectory() as td:
        carpeta = Path(td) / nombre
        inf_rec = emitir_bcf(inf_rec, carpeta, caso=expected.get("caso"),
                             autor=gen.get("autor"), fecha=gen.get("fecha"))
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
        man_rec, inf_rec = _recompute_c4(case_dir, reglas, repo)
        checks.append(("service federar()+validar() ejecuta", True,
                       "services/federacion (import de path)"))
        if informe.get("bcf", {}).get("emitido"):
            inf_rec = _emitir_bcf_c4(inf_rec, expected, checks)   # Fase II·h3 (D14)
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


CASE_RUNNERS = {"C1": run_case_c1, "C4": run_case_c4}


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
