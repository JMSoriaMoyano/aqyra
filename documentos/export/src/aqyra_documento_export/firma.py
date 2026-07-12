# -*- coding: utf-8 -*-
"""Las dos capas de firma del export firmable (D-EX-3, opcion A) — reparto real de las dos llaves.

Llave 1 (GATE, pure-python): INTEGRIDAD. El manifiesto casa byte a byte con el artefacto anclado
(manifiesto.integridad) + determinismo. Prueba que los numeros son los anclados, NO manipulados.
NO usa GPG: la clave privada de JM no entra en CI y meter gnupg romperia la hermeticidad del gate.

Llave 2 (RELEASE, humana): AUTORIA. JM firma el manifiesto con su GPG en local (firmar_detached,
patron release.yml). El CI NUNCA firma ni certifica.

`estado_firmable` implementa la regla de isCertified del visor (data-state.ts): SOLO
`verified-signed` es certificado, y solo lo acuna una firma verificada. Sin .asc verificado ->
`computed` (propone). El gate comprueba que el bundle SIN firmar NO es verified-signed.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ASC = "manifiesto.json.asc"
MANIFIESTO = "manifiesto.json"


def firmar_detached(bundle_dir: Path, key: str | None = None) -> Path:
    """RELEASE-TIME (Llave 2, humana): firma detached GPG del manifiesto. Requiere la clave de JM en
    local; NO se invoca en el gate. Genera `manifiesto.json.asc` junto al manifiesto."""
    bundle_dir = Path(bundle_dir)
    man = bundle_dir / MANIFIESTO
    asc = bundle_dir / ASC
    cmd = ["gpg", "--armor", "--detach-sign", "--batch", "--yes", "--output", str(asc)]
    if key:
        cmd[1:1] = ["--local-user", key]
    cmd.append(str(man))
    subprocess.run(cmd, check=True)
    return asc


def estado_firmable(bundle_dir: Path, verificador=None) -> str:
    """DataState del bundle (espeja isCertified del visor): `verified-signed` SOLO si hay `.asc` y un
    VERIFICADOR lo confirma. Sin verificador (caso del gate, hermetico) nunca acuna el verde: devuelve
    `computed`. La AUTORIA se prueba en el release con la clave publica de JM, no en CI."""
    bundle_dir = Path(bundle_dir)
    asc = bundle_dir / ASC
    if not asc.exists():
        return "computed"
    if verificador is None:
        # sin cripto en el gate: presencia de .asc no basta para el verde.
        return "computed"
    return "verified-signed" if verificador(bundle_dir / MANIFIESTO, asc) else "computed"


def es_certificado(bundle_dir: Path, verificador=None) -> bool:
    """Regla dura D-021/D-EX-5: certificado <=> verified-signed. Unica fuente del verde del export."""
    return estado_firmable(bundle_dir, verificador) == "verified-signed"
