"""emitir_bcf(informe, carpeta) → contenedor BCF 3.0 (un topic por incidencia).

BCF 3.0 de buildingSMART POR REFERENCIA (D2: no se re-esquematiza; la versión se
ancla en versions.lock [contracts.C4] bcf="3.0"). La emisión es un paso SEPARADO
de validar() (D11): la salida por defecto del service sigue declarando
bcf.emitido=false (D8) y el expected de C4-FED-01 queda intocado por construcción.

Determinismo — garantía del contrato (D13):
- GUID de topic     = uuid5(NAMESPACE_AQYRA, f"{caso}/{incidencia.id}")
- GUID de viewpoint = uuid5(NAMESPACE_AQYRA, f"{caso}/{incidencia.id}/viewpoint")
  con NAMESPACE_AQYRA = uuid5(NAMESPACE_DNS, "aqyra.bcf"): estable entre
  ejecuciones y ANCLABLE en la golden (C4-FED-02).
- autor/fecha son metadatos de generación INYECTABLES (misma filosofía que la
  `procedencia` del manifiesto); la golden los fija en su expected
  (bcf_generacion) y el runner los inyecta en el recompute.

Contenedor — el ÁRBOL descomprimido es lo que se ancla (D12, md5 por fichero):
    <carpeta>/bcf.version                  VersionId 3.0
    <carpeta>/<topic-guid>/markup.bcf      Topic: Guid, TopicType=Issue,
                                           TopicStatus=Open, Title, Priority ←
                                           severidad (literal), Labels =
                                           requisito + modelo:<id>,
                                           CreationDate/Author, Description
    <carpeta>/<topic-guid>/viewpoint.bcfv  Components → GUIDs afectados; SIN
                                           cámara en v0 (no hay IFC federado
                                           derivado — D6; la cámara llega con él
                                           en v0.x). Solo si la incidencia trae
                                           GUIDs (las reglas de módulo a nivel de
                                           proyecto emiten topic sin viewpoint).
El `.bcfzip` de intercambio es un DERIVADO sin anclar (un zip no es determinista
byte a byte); lo genera el CLI con --bcfzip.
"""
from __future__ import annotations

import copy
import uuid
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

NAMESPACE_AQYRA = uuid.uuid5(uuid.NAMESPACE_DNS, "aqyra.bcf")

_DECL = '<?xml version="1.0" encoding="utf-8"?>\n'
_VERSION_XML = _DECL + '<Version VersionId="3.0"/>\n'


def guid_topic(caso: str, incidencia_id: str) -> str:
    return str(uuid.uuid5(NAMESPACE_AQYRA, f"{caso}/{incidencia_id}"))


def guid_viewpoint(caso: str, incidencia_id: str) -> str:
    return str(uuid.uuid5(NAMESPACE_AQYRA, f"{caso}/{incidencia_id}/viewpoint"))


def _markup(inc: dict, topic_guid: str, vp_guid: str | None,
            autor: str, fecha: str) -> str:
    """markup.bcf (BCF 3.0): orden de elementos del XSD de buildingSMART
    (Title, Priority?, Labels?, CreationDate, CreationAuthor, Description?,
    Viewpoints?). Priority ← severidad LITERAL; el requisito y el modelo van
    como Labels (referencia al requisito sin re-esquematizar nada)."""
    L = [_DECL, "<Markup>\n",
         f'  <Topic Guid={quoteattr(topic_guid)} TopicType="Issue" TopicStatus="Open">\n',
         f"    <Title>{escape(inc['titulo'])}</Title>\n",
         f"    <Priority>{escape(inc['severidad'])}</Priority>\n",
         "    <Labels>\n",
         f"      <Label>{escape(inc['requisito'])}</Label>\n",
         f"      <Label>modelo:{escape(inc['modelo'])}</Label>\n",
         "    </Labels>\n",
         f"    <CreationDate>{escape(fecha)}</CreationDate>\n",
         f"    <CreationAuthor>{escape(autor)}</CreationAuthor>\n",
         f"    <Description>Requisito {escape(inc['requisito'])} no conforme "
         f"en el modelo {escape(inc['modelo'])}.</Description>\n"]
    if vp_guid:
        L += ["    <Viewpoints>\n",
              f"      <ViewPoint Guid={quoteattr(vp_guid)}>\n",
              "        <Viewpoint>viewpoint.bcfv</Viewpoint>\n",
              "      </ViewPoint>\n",
              "    </Viewpoints>\n"]
    L += ["  </Topic>\n", "</Markup>\n"]
    return "".join(L)


def _viewpoint(vp_guid: str, guids: list[str]) -> str:
    """viewpoint.bcfv (BCF 3.0): Components/Selection con los GUIDs afectados.
    SIN cámara (D6: no hay IFC federado derivado en v0)."""
    L = [_DECL, f"<VisualizationInfo Guid={quoteattr(vp_guid)}>\n",
         "  <Components>\n", "    <Selection>\n"]
    L += [f"      <Component IfcGuid={quoteattr(g)}/>\n" for g in guids]
    L += ["    </Selection>\n",
          '    <Visibility DefaultVisibility="true"/>\n',
          "  </Components>\n", "</VisualizationInfo>\n"]
    return "".join(L)


def emitir_bcf(informe: dict, carpeta: Path, caso: str | None = None,
               autor: str | None = None, fecha: str | None = None) -> dict:
    """Emite el contenedor BCF 3.0 del informe QA: un topic por incidencia.

    `carpeta` ES el contenedor (bcf.version en su raíz). Devuelve un informe
    NUEVO (no muta el de entrada) con bcf = {…, emitido: true, carpeta:
    <nombre>} y `bcf_topic_guid` en cada incidencia — el informe solo refleja
    emitido=true cuando la emisión ocurre de verdad.

    `caso`: semilla de los GUIDs deterministas (por defecto, informe.proyecto).
    `autor`/`fecha`: metadatos de generación (por defecto, el service y hoy).
    """
    carpeta = Path(carpeta)
    if caso is None:
        caso = informe["proyecto"]
    if autor is None:
        from . import __version__
        autor = f"services/federacion {__version__}"
    if fecha is None:
        fecha = f"{date.today().isoformat()}T00:00:00Z"

    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "bcf.version").write_text(_VERSION_XML, encoding="utf-8", newline="\n")

    out = copy.deepcopy(informe)
    for inc in out.get("incidencias", []):
        tg = guid_topic(caso, inc["id"])
        vg = guid_viewpoint(caso, inc["id"]) if inc.get("guids") else None
        d = carpeta / tg
        d.mkdir(exist_ok=True)
        (d / "markup.bcf").write_text(_markup(inc, tg, vg, autor, fecha),
                                      encoding="utf-8", newline="\n")
        if vg:
            (d / "viewpoint.bcfv").write_text(_viewpoint(vg, inc["guids"]),
                                              encoding="utf-8", newline="\n")
        inc["bcf_topic_guid"] = tg

    out["bcf"] = {"estandar": "BCF",
                  "version": str(informe.get("bcf", {}).get("version", "3.0")),
                  "emitido": True,
                  "carpeta": carpeta.name}
    return out


def empaquetar_bcfzip(carpeta: Path, destino: Path) -> Path:
    """DERIVADO de intercambio (D12): zip del contenedor. NO se ancla en la
    golden (un zip no es determinista byte a byte: timestamps/orden)."""
    import zipfile
    carpeta, destino = Path(carpeta), Path(destino)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(carpeta.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(carpeta).as_posix())
    return destino
