"""federar(ifcs[], reglas) → Maestro (manifiesto de federación).

El artefacto autoritativo es el MANIFIESTO (D1): refs a los IFC fuente por hash,
transformación al CRS destino por el punto base DECLARADO (ADR: nunca adivinado),
estructura espacial unificada por nombre con procedencia (`aportado_por`), GUIDs
preservados, elementos sin deduplicar (v0.1). El IFC federado derivado NO se emite
en v0 (D6 — llega en v0.x con su anclaje decidido entonces).

Determinista: mismos IFC + mismas reglas → mismo manifiesto. La fecha de la
procedencia es opcional (metadato de generación, no contenido federado).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from . import lectura
from .lectura import SIN_NOMBRE, LecturaIfcError

# Política de estructura espacial (documentada, v0):
# - El nivel Project SIEMPRE se unifica en el proyecto de federación (nombre =
#   reglas.proyecto, aportado por todos los modelos): el Maestro tiene UN proyecto
#   por definición; los Project de origen llevan nombres por disciplina.
# - Site / Building / Storey se unifican POR NOMBRE (política de las reglas):
#   mismo nombre → un nodo con la procedencia acumulada; nombre distinto → nodos
#   separados (nada se funde en silencio).
_NIVELES = {"IfcSite": "Site", "IfcBuilding": "Building", "IfcBuildingStorey": "Storey"}
_RANGO_NIVEL = {"Project": 0, "Site": 1, "Building": 2, "Storey": 3}

_POLITICA_EE = {
    "unificar-por-nombre": "unificada-por-nombre",
    "mantener-separada": "mantenida-separada",
}


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def federar(reglas: dict, base_dir: Path, reglas_md5: str | None = None,
            fecha: str | None = None) -> dict:
    """Federa los N IFC declarados en las reglas → manifiesto (fuente de verdad).

    `base_dir`: directorio contra el que resuelven los `fichero` de las reglas.
    `reglas_md5` / `fecha`: metadatos de procedencia (opcionales, no afectan al
    contenido federado).
    """
    base_dir = Path(base_dir)
    dedup = reglas.get("deduplicacion", {})
    if dedup.get("elementos", "nunca") != "nunca":
        raise ValueError("v0.1 solo admite deduplicacion.elementos = 'nunca' (ADR)")
    politica_ee = _POLITICA_EE.get(dedup.get("estructura_espacial", "unificar-por-nombre"))
    if politica_ee is None:
        raise ValueError(f"política de estructura espacial no soportada: "
                         f"{dedup.get('estructura_espacial')!r}")

    modelos_out: list[dict] = []
    # nodos de estructura espacial: (nivel, nombre) → aportado_por (orden de inserción)
    nodos: dict[tuple[str, str], list[str]] = {}

    for m in reglas["modelos"]:
        ruta = base_dir / m["fichero"]
        if not ruta.is_file():
            raise LecturaIfcError(ruta, f"el fichero del modelo {m['id']!r} no existe "
                                        f"(revisa 'fichero' en las reglas)")
        md5 = _md5(ruta)
        declarado = m.get("md5")
        if declarado and declarado != md5:
            raise LecturaIfcError(ruta, f"integridad: md5={md5} ≠ declarado {declarado} "
                                        f"(el fichero no es el que anclan las reglas)",
                                  campo="md5")
        ifc = lectura.abrir_ifc(ruta)
        pb = m["punto_base"]
        modelos_out.append({
            "id": m["id"],
            "disciplina": m["disciplina"],
            "fichero_origen": m["fichero"],
            "md5": md5,
            "transformacion": {
                "traslacion": [pb["e"], pb["n"], pb["cota"]],
                "rotacion_deg": pb.get("rotacion_deg", 0.0),
                "escala": 1.0,
            },
            "estado_entrada": m.get("estado_entrada", "S0"),
            "n_elementos": len(ifc.by_type("IfcElement")),
        })
        for clase, nivel in _NIVELES.items():
            for ent in lectura.by_type_seguro(ifc, clase, include_subtypes=False):
                nombre, _legible = lectura.nombre_seguro(ent)   # 1.3: Name=None/roto
                clave = (nivel, nombre or SIN_NOMBRE)           # → nodo declarado
                nodos.setdefault(clave, [])
                if m["id"] not in nodos[clave]:
                    nodos[clave].append(m["id"])

    todos = [m["id"] for m in reglas["modelos"]]
    agregados = [{"nivel": "Project", "nombre": reglas["proyecto"], "aportado_por": todos}]
    for idx, ((nivel, nombre), aportado) in enumerate(nodos.items()):
        agregados.append({"nivel": nivel, "nombre": nombre, "aportado_por": aportado,
                          "_idx": idx})
    agregados.sort(key=lambda a: (_RANGO_NIVEL[a["nivel"]], a.pop("_idx", -1)))

    crs = reglas["crs_destino"]
    procedencia: dict = {"generado_por": f"services/federacion {_version()}"}
    if fecha:
        procedencia["fecha"] = fecha
    if reglas_md5:
        procedencia["reglas_md5"] = reglas_md5

    return {
        "proyecto": reglas["proyecto"],
        "crs": {k: crs[k] for k in ("epsg", "descripcion", "datum_vertical") if k in crs},
        "modelos": modelos_out,
        "estructura_espacial": {"politica": politica_ee, "agregados": agregados},
        "guids": {"politica": "preservados"},
        "procedencia": procedencia,
    }


def federar_fichero(reglas_path: Path, base_dir: Path | None = None,
                    fecha: str | None = None) -> dict:
    """Federa desde un reglas.json en disco (calcula su md5 para la procedencia)."""
    import json
    reglas_path = Path(reglas_path)
    reglas = json.loads(reglas_path.read_text(encoding="utf-8"))
    return federar(reglas, base_dir or reglas_path.parent,
                   reglas_md5=_md5(reglas_path), fecha=fecha)


def _version() -> str:
    from . import __version__
    return __version__
