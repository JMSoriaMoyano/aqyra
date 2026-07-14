# -*- coding: utf-8 -*-
"""Manifiesto de entrega MAESTRO del operador C7 (roll-up de procedencia, D-C7-2/D-C7-4).

El manifiesto-entrega ata los N bundles firmables del paquete a un mismo proyecto/Maestro por un
ROLL-UP DETERMINISTA. Por cada entregable ancla el `content_sha256_manifiesto` = sha256 del
`manifiesto.json` individual del bundle (el fichero entero, que ya incluye el hash del artefacto +
versiones + sello); `paquete_sha256` = sha256 de la forma canonica de la lista ORDENADA de esos
sha256. Asi el maestro liga los N bundles con una sola huella y el gate (Llave 1) comprueba que el
paquete entero no esta manipulado.

Determinista: mismos artefactos + misma solicitud + mismo sello => manifiesto-entrega byte a byte. El
sello de tiempo es SIEMPRE un parametro (viene de la solicitud), NUNCA now(). NO recalcula nada del
artefacto: solo describe y ata lo que el rail de export ya produjo. NO usa GPG: la integridad (roll-up
no manipulado) es del gate; la AUTORIA (firma de JM) es del release (dos llaves, patron documentos/export).
"""
from __future__ import annotations

import hashlib
import json

GENERADOR = "aqyra-entrega"
VERSION = "0.1.0"
ESQUEMA = "manifiesto-entrega/v0"


def sha256_bytes(data: bytes) -> str:
    """sha256 hex de unos bytes (el manifiesto.json individual serializado, determinista)."""
    return hashlib.sha256(data).hexdigest()


def roll_up(content_sha256_manifiestos: list[str]) -> str:
    """paquete_sha256 = sha256 de la forma canonica de la lista ORDENADA de sha256 de manifiestos.

    Se ORDENA la lista (lexicografico) para que el roll-up sea independiente del orden de entrada: el
    mismo conjunto de bundles da siempre la misma huella de paquete.
    """
    canon = json.dumps(sorted(content_sha256_manifiestos), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def construir_manifiesto_entrega(solicitud: dict, entregables_resueltos: list[dict]) -> dict:
    """Manifiesto-entrega DETERMINISTA a partir de la solicitud y los entregables ya compuestos.

    `entregables_resueltos`: lista de dicts `{consumidor, nombre_bundle, content_sha256_manifiesto,
    artefacto_ref?}` (uno por bundle). El sello, el proyecto, el hito, el maestro_ref y las versiones
    los aporta la solicitud (el operador no lee el repo). Los entregables se ORDENAN por
    (consumidor, nombre_bundle) para que el manifiesto sea reproducible con independencia del orden de
    entrada; el `paquete_sha256` (roll-up) es igualmente independiente del orden.
    """
    ordenados = sorted(entregables_resueltos, key=lambda e: (e.get("consumidor", ""), e.get("nombre_bundle", "")))
    entregables = []
    for e in ordenados:
        item = {
            "consumidor": str(e.get("consumidor", "")),
            "nombre_bundle": str(e.get("nombre_bundle", "")),
            "content_sha256_manifiesto": str(e.get("content_sha256_manifiesto", "")),
        }
        if e.get("artefacto_ref"):
            item["artefacto_ref"] = str(e["artefacto_ref"])
        entregables.append(item)

    manifiesto = {
        "esquema": ESQUEMA,
        "generador": GENERADOR,
        "version_generador": VERSION,
        "sello_tiempo": str(solicitud.get("sello_tiempo") or "-"),
        "proyecto": str(solicitud.get("proyecto") or "-"),
        "entregables": entregables,
        "paquete_sha256": roll_up([e["content_sha256_manifiesto"] for e in entregables]),
        "versiones_ancladas": dict(solicitud.get("versiones_ancladas") or {}),
    }
    if solicitud.get("hito"):
        manifiesto["hito"] = str(solicitud["hito"])
    if solicitud.get("maestro_ref"):
        manifiesto["maestro_ref"] = str(solicitud["maestro_ref"])
    return manifiesto


def serializar(manifiesto: dict) -> str:
    """Texto DETERMINISTA del manifiesto-entrega (claves ordenadas, UTF-8, con salto final)."""
    return json.dumps(manifiesto, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def integridad(manifiesto: dict, sha_por_bundle: dict[str, str]) -> tuple[bool, str]:
    """Comprobacion pure-python (Llave 1 / gate): el manifiesto-entrega CASA con los bundles del paquete.

    `sha_por_bundle`: mapa `nombre_bundle -> sha256 recomputado del manifiesto.json de ese bundle` (el
    caller lo recomputa leyendo el paquete). Comprueba:
      (a) cada entregable declara el sha256 recomputado de su bundle;
      (b) `paquete_sha256` == roll-up recomputado de la lista de sha256 declarados;
      (c) hay versiones ancladas.
    NO usa GPG: la integridad (roll-up no manipulado) es del gate; la AUTORIA (firma de JM) es del release.
    """
    entregables = manifiesto.get("entregables") or []
    if not entregables:
        return False, "manifiesto-entrega sin entregables"
    for e in entregables:
        nb = e.get("nombre_bundle")
        got = sha_por_bundle.get(nb)
        exp = e.get("content_sha256_manifiesto")
        if got is None:
            return False, f"bundle '{nb}' del manifiesto no esta en el paquete"
        if got != exp:
            return False, f"content_sha256_manifiesto de '{nb}' no casa: {str(got)[:12]}... vs {str(exp)[:12]}..."
    esperado_rollup = roll_up([e.get("content_sha256_manifiesto", "") for e in entregables])
    if esperado_rollup != manifiesto.get("paquete_sha256"):
        return False, (f"paquete_sha256 no casa con el roll-up: "
                       f"{str(esperado_rollup)[:12]}... vs {str(manifiesto.get('paquete_sha256'))[:12]}...")
    if not manifiesto.get("versiones_ancladas"):
        return False, "faltan versiones ancladas"
    return True, (f"integro ({len(entregables)} bundles, paquete_sha256 {esperado_rollup[:12]}...)")
