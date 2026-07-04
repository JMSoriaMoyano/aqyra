"""Parser de medición del C5 (módulo 1, D7): IFC(+Qto) → modelo neutro de medición.

`medir(fuentes)` abre cada IFC con `Qto` y produce el modelo neutro (`{clase, objetos:[...]}`)
que conforma `entrada-presupuesto.schema.json`. La medición NACE del modelo: cada `cantidad` sale
de un `Qto` del elemento (no se teclea, no se adivina geometría — D_modelo). Los huecos se
detectan (`IfcRelVoidsElement`) para poder tenerlos en cuenta de forma auditable (D7); la magnitud
NETA (`NetSideArea`) ya los descuenta por el propio `Qto`.

En el golden el runner entrega las fixtures congeladas; en producción, el Maestro federado de C4.
"""
from __future__ import annotations

from pathlib import Path

from . import modelo as M

# Clases medibles del corte (superset del criterio v1; el criterio decide cuáles tienen partida).
# El ascensor (IfcTransportElement) entra en el modelo neutro para no falsear la vista de medición
# aunque el criterio v1 no le dé partida.
CLASES_MEDIBLES = (
    "IfcWall", "IfcWallStandardCase", "IfcSlab", "IfcColumn",
    "IfcFooting", "IfcDoor", "IfcTransportElement", "IfcBeam", "IfcMember",
)


def _objeto_neutro(elemento, disciplina: str | None) -> dict:
    guid = M.guid_de(elemento)
    clase = elemento.is_a()
    cantidades = M.cantidades_qto(elemento)
    # `conteo` sintético (ud): toda entidad medible cuenta 1 — habilita el criterio de conteo
    # (puertas, ascensores) sin depender de un Qto numérico.
    cantidades.append({"magnitud": "conteo", "tipo": "ud", "valor": 1, "fuente_qto": "conteo"})
    obj: dict = {
        "guid": guid,
        "clase": clase,
        "nombre": getattr(elemento, "Name", None),
        "clasificacion": M.clasificacion_de(elemento),
        "cantidades": cantidades,
        "ubicacion": M.ubicacion_de(elemento, disciplina),
    }
    huecos = M.huecos_de(elemento)
    if huecos:
        obj["_huecos"] = len(huecos)
    return obj


def medir(fuentes: list[dict]) -> dict:
    """Modelo neutro de medición a partir de las fuentes IFC(+Qto).

    `fuentes`: [{"id", "disciplina"?, "path"}] — orden significativo (procedencia y traza). El
    modelo neutro preserva el orden de las fuentes y, dentro de cada IFC, el orden de declaración.
    """
    objetos: list[dict] = []
    modelos_fuente: list[dict] = []
    md5_derivado = None
    for f in fuentes:
        path = Path(f["path"])
        disciplina = f.get("disciplina")
        ifc = M.abrir(path)
        # recorrido determinista: por clase medible y, dentro, por id de entidad (orden de fichero)
        vistos: set = set()
        for clase in CLASES_MEDIBLES:
            for e in ifc.by_type(clase):
                if e.is_a() != clase:  # evita doble conteo de subtipos (WallStandardCase)
                    continue
                g = M.guid_de(e)
                if g in vistos:
                    continue
                vistos.add(g)
                objetos.append(_objeto_neutro(e, disciplina))
        modelos_fuente.append({
            "id": f.get("id"),
            "disciplina": disciplina,
            "fichero": f.get("fichero", path.name),
            "qto_declarados": True,
        })
    modelo: dict = {"clase": "modelo-neutro-medicion", "objetos": objetos}
    fuente_maestro: dict = {"modelos": modelos_fuente}
    if md5_derivado:
        fuente_maestro["ifc_derivado_md5"] = md5_derivado
    modelo["fuente_maestro"] = fuente_maestro
    return modelo
