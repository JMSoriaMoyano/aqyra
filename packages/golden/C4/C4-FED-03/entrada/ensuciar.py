#!/usr/bin/env python3
"""Genera SUCIO.ifc — el IFC sucio CONGELADO de la golden C4-FED-03 (D18).

Parte del ARQ.ifc congelado de C4-FED-01 (md5 653a359154112146d82ca02de0fde2ee)
e inyecta, ADREDE y por separado, tres suciedades TOLERABLES de la taxonomía D17:

  S1 · Storey 'Planta 1' → Name = None        → nodo "(sin nombre)" + aviso nombre-vacio
  S2 · segundo Storey 'Planta Baja' (nuevo)   → aviso nombre-duplicado (unificados)
  S3 · segundo IfcProject 'FANTASMA' (nuevo)  → aviso multi-proyecto (R4 cuenta 2)

Determinista: GUIDs nuevos por uuid5 (semilla fija) y timestamp de cabecera SPF
normalizado. El artefacto que rige es el SUCIO.ifc CONGELADO (md5 en expected.json);
regenerarlo requiere el mismo ifcopenshell que lo congeló (misma situación que los
IFC de entrada de C4-FED-01/02, que embeben la versión del serializador).

Uso:  python ensuciar.py <ruta/ARQ.ifc-de-C4-FED-01> <salida/SUCIO.ifc>
"""
from __future__ import annotations

import hashlib
import re
import sys
import uuid
from pathlib import Path

import ifcopenshell
import ifcopenshell.guid

MD5_ORIGEN = "653a359154112146d82ca02de0fde2ee"          # ARQ.ifc de C4-FED-01
_SEMILLA = uuid.uuid5(uuid.NAMESPACE_DNS, "aqyra.golden.C4-FED-03")
FECHA_SPF = "2026-07-02T00:00:00"                        # cabecera normalizada


def _guid(n: int) -> str:
    return ifcopenshell.guid.compress(uuid.uuid5(_SEMILLA, f"nuevo/{n}").hex)


def ensuciar(origen: Path, destino: Path) -> str:
    got = hashlib.md5(origen.read_bytes()).hexdigest()
    if got != MD5_ORIGEN:
        raise SystemExit(f"origen no es el ARQ.ifc congelado: md5 {got} != {MD5_ORIGEN}")
    f = ifcopenshell.open(str(origen))

    # S1 · Name=None en 'Planta 1'
    p1 = [s for s in f.by_type("IfcBuildingStorey") if s.Name == "Planta 1"][0]
    p1.Name = None

    # S2 · Storey duplicado 'Planta Baja' bajo el mismo Building
    bld = f.by_type("IfcBuilding")[0]
    dup = f.create_entity("IfcBuildingStorey", GlobalId=_guid(1), Name="Planta Baja",
                          Elevation=6.0)
    f.create_entity("IfcRelAggregates", GlobalId=_guid(2),
                    RelatingObject=bld, RelatedObjects=[dup])

    # S3 · segundo IfcProject (huérfano, como los deja algún export roto)
    f.create_entity("IfcProject", GlobalId=_guid(3), Name="FANTASMA")

    f.write(str(destino))
    # normaliza el timestamp de FILE_NAME (único no-determinismo de la cabecera SPF)
    txt = destino.read_text(encoding="utf-8")
    txt = re.sub(r"(FILE_NAME\('[^']*',')[^']*(',)", rf"\g<1>{FECHA_SPF}\g<2>", txt, count=1)
    destino.write_text(txt, encoding="utf-8", newline="\n")
    return hashlib.md5(destino.read_bytes()).hexdigest()


if __name__ == "__main__":
    origen, destino = Path(sys.argv[1]), Path(sys.argv[2])
    print(f"SUCIO.ifc md5 = {ensuciar(origen, destino)}")
