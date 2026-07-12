# -*- coding: utf-8 -*-
"""Manifiesto de procedencia del export firmable (NUCLEO transversal, D-EX-3).

El manifiesto es la pieza reutilizable del muro de cobro: liga el bundle al ARTEFACTO AUTORITATIVO
por su hash y ancla la procedencia (versiones, modelo, eje/corte, generador, sello de tiempo). Es
DETERMINISTA: mismo artefacto + mismo descriptor + mismo sello => mismo manifiesto (byte a byte). El
sello de tiempo es SIEMPRE un parametro (nunca now()).

NO recalcula nada: lee el artefacto ya anclado y lo describe. El content_sha256 es la huella canonica
del artefacto autoritativo (JSON con claves ordenadas), de modo que el gate (Llave 1) pueda comprobar
que las cifras del export son las ancladas y no estan manipuladas.
"""
from __future__ import annotations

import hashlib
import json

GENERADOR = "aqyra-documento-export"
VERSION = "0.1.0"
ESQUEMA = "manifiesto-export/v0"


def hash_canonico(artefacto: dict) -> str:
    """sha256 de la forma canonica (claves ordenadas, sin espacios) del artefacto autoritativo."""
    canon = json.dumps(artefacto, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def _suma_declarada(artefacto: dict):
    """Invariante Sigma del artefacto de proyeccion (la suma de la 1a vista o del bloque cost)."""
    vistas = artefacto.get("vistas") or []
    if vistas:
        return float(vistas[0].get("suma", 0.0))
    cost = artefacto.get("cost") or {}
    return float(cost.get("PEM", 0.0)) if cost else None


def construir_manifiesto(artefacto: dict, descriptor: dict) -> dict:
    """Manifiesto de procedencia DETERMINISTA a partir del artefacto autoritativo y el descriptor.

    El sello de tiempo se toma del descriptor (`sello_tiempo`), NUNCA de now(). Las versiones ancladas
    y las referencias las aporta el CALLER via el descriptor (nucleo vertical-agnostico): el manifiesto
    no lee versions.lock ni el repo, para que cualquier vertical entre sin tocar el nucleo.
    """
    art_desc = dict(descriptor.get("artefacto") or {})
    manifiesto = {
        "esquema": ESQUEMA,
        "generador": GENERADOR,
        "version_generador": VERSION,
        "sello_tiempo": str(descriptor.get("sello_tiempo") or "-"),
        "artefacto": {
            "tipo": str(art_desc.get("tipo") or "artefacto-autoritativo"),
            "id": str(art_desc.get("id") or artefacto.get("proyecto") or "-"),
            "content_sha256": hash_canonico(artefacto),
        },
        "modelo_md5": dict(artefacto.get("entradas_md5") or {}),
        "versiones_ancladas": dict(descriptor.get("versiones_ancladas") or {}),
        "seleccion": {
            "eje": descriptor.get("eje"),
            "corte": descriptor.get("corte"),
        },
        "formatos": list(descriptor.get("formatos") or []),
    }
    suma = _suma_declarada(artefacto)
    if suma is not None:
        manifiesto["invariante"] = {
            "suma_declarada": round(suma, 2),
            "n_vistas": len(artefacto.get("vistas") or []),
        }
    return manifiesto


def serializar(manifiesto: dict) -> str:
    """Texto DETERMINISTA del manifiesto (claves ordenadas, UTF-8, con salto final)."""
    return json.dumps(manifiesto, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def integridad(manifiesto: dict, artefacto: dict) -> tuple[bool, str]:
    """Comprobacion pure-python (Llave 1 / gate): el manifiesto CASA con el artefacto autoritativo.

    (a) el content_sha256 del manifiesto == hash canonico recomputado del artefacto;
    (b) el modelo_md5 == entradas_md5 del artefacto (si el artefacto las trae);
    (c) hay versiones ancladas.
    NO usa GPG: la integridad (numeros no manipulados) es del gate; la AUTORIA (firma de JM) es del
    release (D-EX-3, opcion A).
    """
    got = hash_canonico(artefacto)
    exp = (manifiesto.get("artefacto") or {}).get("content_sha256")
    if got != exp:
        return False, f"content_sha256 no casa: {str(got)[:12]}... vs {str(exp)[:12]}..."
    art_md5 = artefacto.get("entradas_md5")
    if art_md5 is not None and dict(art_md5) != dict(manifiesto.get("modelo_md5") or {}):
        return False, "modelo_md5 del manifiesto != entradas_md5 del artefacto"
    if not (manifiesto.get("versiones_ancladas")):
        return False, "faltan versiones ancladas"
    return True, f"integro (sha256 {got[:12]}..., {len(manifiesto.get('modelo_md5') or {})} md5 de modelo)"
