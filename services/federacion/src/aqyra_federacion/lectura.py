"""Lectura ENDURECIDA de IFC para modelos reales ("sucios") — tarea 1.3 (D16–D20).

El engine C1 produce IFC limpio por construcción; los exports reales (Revit/Archicad/
Tekla) no. Este módulo es la única puerta de entrada de ifcopenshell en el service
(D16: el endurecimiento vive en el CONSUMIDOR) y aplica la política de fallo de D17:

- Suciedad TOLERABLE → se lee, se degrada y se DECLARA (aviso `{modelo, codigo,
  detalle}`; taxonomía cerrada en `informe-qa.schema.json` $defs/aviso_lectura).
- Suciedad BLOQUEANTE → `LecturaIfcError` con diagnóstico accionable (fichero,
  entidad, campo, motivo) — nunca stack trace pelado.

(El módulo se llama lectura.py: sin colisión de NOMBRE con el guardián anti-espejo
del engine — comprobado contra CORTE_ENGINE y NUCLEO antes de nombrarlo.)
"""
from __future__ import annotations

from pathlib import Path

import ifcopenshell

# Política de tamaño (D17): declarar, no optimizar. Umbral fijo de v0.3.
_LIMITE_MB = 256

# Niveles de estructura espacial que federar() unifica (mismo orden que federar._NIVELES).
_NIVELES_EE = ("IfcSite", "IfcBuilding", "IfcBuildingStorey")

SIN_NOMBRE = "(sin nombre)"


class LecturaIfcError(ValueError):
    """Suciedad BLOQUEANTE al leer un IFC de entrada.

    Subclase de ValueError (compatibilidad: la integridad md5 ya era ValueError).
    Siempre lleva diagnóstico accionable: fichero, motivo y, si aplica, entidad y campo.
    """

    def __init__(self, fichero, motivo: str, entidad: str | None = None,
                 campo: str | None = None):
        self.fichero = str(fichero)
        self.motivo = motivo
        self.entidad = entidad
        self.campo = campo
        partes = [f"lectura IFC bloqueada en '{self.fichero}'"]
        if entidad:
            partes.append(f"entidad {entidad}")
        if campo:
            partes.append(f"campo {campo}")
        partes.append(motivo)
        super().__init__(" — ".join(partes))


def abrir_ifc(path: Path) -> "ifcopenshell.file":
    """Abre un IFC con diagnóstico (BLOQUEANTE si no existe o no parsea)."""
    path = Path(path)
    if not path.is_file():
        raise LecturaIfcError(path, "el fichero no existe (revisa la ruta de las reglas)")
    try:
        return ifcopenshell.open(str(path))
    except Exception as e:  # noqa: BLE001 — el wrapper lanza tipos variados y crípticos
        raise LecturaIfcError(
            path, f"ifcopenshell no puede parsearlo ({type(e).__name__}: {e}); "
                  f"¿es un IFC SPF válido?") from None


def by_type_seguro(ifc, clase: str, include_subtypes: bool = True) -> list:
    """`by_type` que devuelve [] si la clase NO existe en el esquema del fichero.

    (ifcopenshell LANZA si se pide p. ej. IfcMapConversion a un IFC2X3 — hallazgo #7
    de la auditoría 2.4: era un crash de validar(), no un fail diagnosticado.)
    """
    try:
        return list(ifc.by_type(clase, include_subtypes=include_subtypes))
    except Exception:  # noqa: BLE001 — clase inexistente en el esquema del fichero
        return []


def nombre_seguro(ent) -> tuple[str | None, bool]:
    """(Name, legible). legible=False si el atributo revienta (entidad corrupta)."""
    try:
        return ent.Name, True
    except Exception:  # noqa: BLE001
        return None, False


def _id_entidad(ent) -> str:
    try:
        return f"#{ent.id()}"
    except Exception:  # noqa: BLE001
        return "#?"


def _aviso(modelo: str, codigo: str, detalle: str) -> dict:
    return {"modelo": modelo, "codigo": codigo, "detalle": detalle}


def avisos_de_modelo(ifc, path: Path, modelo: str) -> list[dict]:
    """Avisos de lectura (suciedad TOLERABLE, D17) de un modelo, en orden fijo.

    Determinista: mismo fichero → mismos avisos en el mismo orden (taxonomía →
    entidad por id). La clave `avisos_lectura` del informe solo existe si hay avisos
    (D20: los casos limpios ni se enteran).
    """
    avisos: list[dict] = []
    path = Path(path)

    # 1 · tamaño (política declarada, sin optimización)
    mb = path.stat().st_size / (1024 * 1024)
    if mb > _LIMITE_MB:
        avisos.append(_aviso(modelo, "fichero-grande",
                             f"{mb:.0f} MB > límite declarado {_LIMITE_MB} MB"))

    # 2 · esquema
    esquema = ifc.schema
    if not str(esquema).startswith("IFC4X3"):
        avisos.append(_aviso(modelo, "esquema-no-4x3",
                             f"esquema {esquema}: lectura tolerada; el contrato C4 "
                             f"declara IFC4X3"))

    # 3 · proyectos
    proyectos = by_type_seguro(ifc, "IfcProject", include_subtypes=False)
    if len(proyectos) > 1:
        ids = ", ".join(_id_entidad(p) for p in proyectos)
        avisos.append(_aviso(modelo, "multi-proyecto",
                             f"{len(proyectos)} IfcProject ({ids}); se esperaba 1"))

    # 4 · unidades de longitud
    avisos += _avisos_unidades(ifc, modelo, proyectos)

    # 5 · estructura espacial: niveles ausentes, nombres vacíos y duplicados
    for clase in _NIVELES_EE:
        ents = by_type_seguro(ifc, clase, include_subtypes=False)
        if not ents:
            avisos.append(_aviso(modelo, "nivel-ausente",
                                 f"sin {clase} (la estructura espacial no es canónica)"))
            continue
        vistos: dict[str, list[str]] = {}
        for ent in ents:
            nombre, legible = nombre_seguro(ent)
            if not legible:
                avisos.append(_aviso(modelo, "entidad-corrupta",
                                     f"{clase} {_id_entidad(ent)}: Name ilegible "
                                     f"(atributo roto); nodo tratado como {SIN_NOMBRE!r}"))
            if not nombre:
                avisos.append(_aviso(modelo, "nombre-vacio",
                                     f"{clase} {_id_entidad(ent)} sin Name; nodo "
                                     f"{SIN_NOMBRE!r} en la estructura espacial"))
            vistos.setdefault(nombre or SIN_NOMBRE, []).append(_id_entidad(ent))
        for nombre, ids in vistos.items():
            if len(ids) > 1:
                avisos.append(_aviso(modelo, "nombre-duplicado",
                                     f"{clase} {nombre!r} aparece {len(ids)} veces "
                                     f"({', '.join(ids)}); unificados en un nodo"))
    return avisos


def _avisos_unidades(ifc, modelo: str, proyectos: list) -> list[dict]:
    """LENGTHUNIT del proyecto: métrica (IfcSIUnit METRE) o aviso."""
    unidades = []
    for p in proyectos:
        try:
            ua = p.UnitsInContext
            unidades += list(ua.Units) if ua is not None else []
        except Exception:  # noqa: BLE001 — proyecto corrupto: ya se avisa por entidad
            continue
    longitud = None
    for u in unidades:
        try:
            if getattr(u, "UnitType", None) == "LENGTHUNIT":
                longitud = u
                break
        except Exception:  # noqa: BLE001
            continue
    if longitud is None:
        return [_aviso(modelo, "sin-unidades",
                       "sin LENGTHUNIT en IfcUnitAssignment; se asume metro SIN "
                       "convertir (v0 no convierte unidades)")]
    es_metro = (longitud.is_a("IfcSIUnit")
                and getattr(longitud, "Name", None) == "METRE"
                and getattr(longitud, "Prefix", None) in (None, "NONE"))
    if not es_metro:
        desc = getattr(longitud, "Name", None) or longitud.is_a()
        return [_aviso(modelo, "unidades-no-metricas",
                       f"LENGTHUNIT = {desc}: v0 NO convierte unidades; las longitudes "
                       f"se leen tal cual")]
    return []
