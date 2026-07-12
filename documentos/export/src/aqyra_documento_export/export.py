# -*- coding: utf-8 -*-
"""componer_export — NUCLEO transversal del export firmable (D-EX-1, D-EX-3, D-EX-4).

    componer_export(artefacto, descriptor, parametros?) -> Path(bundle)

Entrada VERTICAL-AGNOSTICA: un `artefacto` autoritativo (cualquier JSON anclado de una vertical) + un
`descriptor` con `artefacto.tipo`. El nucleo elige el CONSUMIDOR por ese tipo (registro
`_CONSUMIDORES`), construye el MANIFIESTO de procedencia (hash del artefacto + versiones + sello
determinista) y deja que el consumidor renderice los formatos declarados. Determinista, sin LLM: no
recalcula, LEE el artefacto ya anclado.

Consumidores (redireccion 2026-07-12, JM): el PRIMARIO es CONTRACTUAL — `presupuesto-obra` (presupuesto
por partidas + cuadros + medicion + BC3). `proyeccion-valor` queda como export de GESTION (secundario).
El pliego entra como slice siguiente (envolviendo componer_pliego, mismo patron).
"""
from __future__ import annotations

from pathlib import Path

from . import manifiesto as M
from . import presupuesto_doc as PD
from . import proyeccion as PR

NOMBRE_MANIFIESTO = "manifiesto.json"

# consumidor por tipo de artefacto. Cada consumidor: {formato: (nombre_fichero, fn(art,desc,man,salida))}.
_CONSUMIDORES = {
    "presupuesto-obra": PD.FORMATOS,   # CONTRACTUAL (primario)
    "proyeccion-valor": PR.FORMATOS,   # gestion (secundario)
}


def consumidor_de(tipo: str) -> dict | None:
    return _CONSUMIDORES.get(tipo)


def componer_export(artefacto: dict, descriptor: dict, parametros: dict | None = None) -> Path:
    """Compone el bundle firmable y devuelve su carpeta. `parametros`: salida (carpeta del bundle).
    Formatos: los que declare `descriptor['formatos']` (por defecto, todos los del consumidor). Un
    formato no soportado por el consumidor se OMITE (forward), nunca error."""
    par = dict(parametros or {})
    bundle = Path(par.get("salida") or (Path.cwd() / "export_bundle"))
    bundle.mkdir(parents=True, exist_ok=True)

    man = M.construir_manifiesto(artefacto, descriptor)
    (bundle / NOMBRE_MANIFIESTO).write_text(M.serializar(man), encoding="utf-8")

    tipo = str((descriptor.get("artefacto") or {}).get("tipo", ""))
    consumidor = _CONSUMIDORES.get(tipo)
    if consumidor is None:
        raise ValueError(f"tipo de artefacto sin consumidor: {tipo!r} "
                         f"(conocidos: {sorted(_CONSUMIDORES)})")
    formatos = list(descriptor.get("formatos") or list(consumidor))
    for fmt in formatos:
        entry = consumidor.get(fmt)
        if entry is None:
            continue
        nombre, fn = entry
        fn(artefacto, descriptor, man, bundle / nombre)
    return bundle
