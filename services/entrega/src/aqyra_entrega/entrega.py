# -*- coding: utf-8 -*-
"""componer_entrega — operador C7 · orquestador DETERMINISTA de la ENTREGA (D-C7-1, D-C7-3, D-C7-4).

    componer_entrega(solicitud, parametros?) -> Path(paquete)

C7 es la capa que convierte "sellar UN entregable" en "orquestar una ENTREGA": toma una
`solicitud-entrega` YA CONFORMADA (proyecto/hito + lista de entregables, cada uno {consumidor,
artefacto, descriptor}), ENVUELVE `documentos/export.componer_export` sobre cada entregable (no
reimplementa el sellado/firma), y emite UN `manifiesto-entrega` maestro que ata los N bundles al mismo
paquete por un roll-up (hash canonico de la lista ordenada de los sha256 de los manifiestos
individuales).

DETERMINISTA, SIN LLM: no interpreta intencion (eso es el companero IA, FUERA), no recalcula (LEE los
artefactos ya anclados que le entrega la solicitud), no lee el repo ni versions.lock (recibe
descriptores pre-resueltos). Mismos artefactos + misma solicitud + mismo sello => paquete byte a byte.
NUNCA certifica: dos llaves = golden (Llave 1) + firma GPG de JM del manifiesto-entrega (Llave 2).
"""
from __future__ import annotations

from pathlib import Path

import aqyra_documento_export as adx

from . import manifiesto_entrega as ME

NOMBRE_MANIFIESTO_ENTREGA = "manifiesto-entrega.json"
NOMBRE_MANIFIESTO_BUNDLE = adx.NOMBRE_MANIFIESTO   # "manifiesto.json" (del rail de export)


def _nombre_bundle(entregable: dict, indice: int) -> str:
    """Subcarpeta del bundle dentro del paquete: el consumidor (determinista y legible); si se repite,
    se desempata con el indice para no colisionar."""
    base = str(entregable.get("consumidor") or f"entregable-{indice}")
    return base


def componer_entrega(solicitud: dict, parametros: dict | None = None) -> Path:
    """Compone el PAQUETE de entrega y devuelve su carpeta.

    `parametros`: `salida` (carpeta del paquete). Cada entregable de la solicitud se compone con
    `componer_export(artefacto, descriptor, {salida: paquete/<nombre_bundle>})`; el sello de tiempo del
    paquete se PROPAGA a cada descriptor que no lo declare (un unico sello para todo el paquete). Se
    emite el `manifiesto-entrega` maestro en la raiz del paquete.

    v0 (D-C7-3): el operador compone SOLO desde `entregable['artefacto']` (dict inline, ya anclado, que
    el companero IA resuelve). Un entregable con solo `artefacto_ref` y sin `artefacto` es un error en
    v0 (la resolucion de refs vive FUERA del operador).
    """
    par = dict(parametros or {})
    paquete = Path(par.get("salida") or (Path.cwd() / "paquete_entrega"))
    paquete.mkdir(parents=True, exist_ok=True)

    entregables = solicitud.get("entregables")
    if not entregables:
        raise ValueError("solicitud-entrega sin entregables")
    sello = solicitud.get("sello_tiempo")

    nombres_vistos: dict[str, int] = {}
    resueltos: list[dict] = []
    for i, ent in enumerate(entregables):
        artefacto = ent.get("artefacto")
        if artefacto is None:
            ref = ent.get("artefacto_ref")
            raise ValueError(
                f"entregable {i} ({ent.get('consumidor')!r}) sin `artefacto` inline"
                + (f" (artefacto_ref={ref!r}: la resolucion de refs es del companero IA, no del operador v0)"
                   if ref else "")
            )
        descriptor = dict(ent.get("descriptor") or {})
        # el sello del paquete gobierna (determinismo); solo se propaga si el descriptor no lo trae.
        if sello is not None:
            descriptor.setdefault("sello_tiempo", sello)

        nombre = _nombre_bundle(ent, i)
        if nombre in nombres_vistos:
            nombres_vistos[nombre] += 1
            nombre = f"{nombre}-{nombres_vistos[nombre]}"
        else:
            nombres_vistos[nombre] = 0

        # ENVUELVE el rail de export (no reimplementa sellado/firma): produce el bundle firmable.
        bundle = adx.componer_export(artefacto, descriptor, {"salida": paquete / nombre})

        man_bytes = (bundle / NOMBRE_MANIFIESTO_BUNDLE).read_bytes()
        resueltos.append({
            "consumidor": str(ent.get("consumidor") or ""),
            "nombre_bundle": nombre,
            "content_sha256_manifiesto": ME.sha256_bytes(man_bytes),
            "artefacto_ref": ent.get("artefacto_ref"),
        })

    manifiesto = ME.construir_manifiesto_entrega(solicitud, resueltos)
    (paquete / NOMBRE_MANIFIESTO_ENTREGA).write_text(ME.serializar(manifiesto), encoding="utf-8")
    return paquete


def sha_por_bundle(paquete: Path, manifiesto_entrega: dict) -> dict[str, str]:
    """Recomputa el sha256 del manifiesto.json de cada bundle del paquete (para `integridad`)."""
    out: dict[str, str] = {}
    for e in (manifiesto_entrega.get("entregables") or []):
        nb = e.get("nombre_bundle")
        man = Path(paquete) / str(nb) / NOMBRE_MANIFIESTO_BUNDLE
        if man.exists():
            out[nb] = ME.sha256_bytes(man.read_bytes())
    return out
