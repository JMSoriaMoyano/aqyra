"""
ESCRITOR GENERICO DE PSETS DE RESULTADO al IFC (mecanica IFC; contrato C1 §5).
Plugin iso19650-openbim (capa IFC transversal). PT 4.4 (Ola 4).

Cierra el ciclo IFC -> calculo -> IFC: enriquece un IFC existente con Psets de
RESULTADO calculados por una disciplina (estructuras: aprovechamientos/armado;
instalaciones: DN dimensionado, caudal, velocidad, presion, margen). Es AGNOSTICO
a la disciplina y al esquema: solo aporta la MECANICA (abrir IFC, localizar el
elemento, anadir el Pset, guardar). La SEMANTICA (que Pset y que propiedades) la
fija la disciplina y se pasa en un mapping JSON.

Frontera C1 (decision PT 4.4, opcion a): la ESCRITURA IFC vive aqui (iso19650);
QUE escribir lo decide la disciplina (`instalaciones`), que construye el mapping.

Formato del mapping (JSON):
  {
    "elementos": {
       "<Name o GlobalId>": { "<Pset>": { "<Prop>": <valor>, ... }, ... },
       ...
    }
  }
El elemento se localiza por Name (preferente) y, si no, por GlobalId. Los valores
se escriben como IfcPropertySingleValue (tipo deducido del valor Python).

Uso:  python3 escribir_psets_resultado.py entrada.ifc mapping.json salida.ifc
Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
import json
import sys

import ifcopenshell
from ifcopenshell.api import run


def _indice(ifc):
    """Indices Name->elemento y GlobalId->elemento de los productos IFC."""
    por_nombre, por_gid = {}, {}
    for el in ifc.by_type("IfcProduct"):
        nm = getattr(el, "Name", None)
        gid = getattr(el, "GlobalId", None)
        if nm and nm not in por_nombre:
            por_nombre[nm] = el
        if gid:
            por_gid[gid] = el
    return por_nombre, por_gid


def _limpiar(props):
    """Solo valores escribibles (numeros, str, bool); descarta None."""
    out = {}
    for k, v in (props or {}).items():
        if v is None:
            continue
        if isinstance(v, bool) or isinstance(v, (int, float, str)):
            out[k] = v
        else:
            out[k] = str(v)
    return out


def escribir(ifc_path, mapping, out_path):
    """Escribe los Psets del mapping en el IFC y lo guarda. Devuelve un resumen."""
    ifc = ifcopenshell.open(ifc_path)
    por_nombre, por_gid = _indice(ifc)
    elementos = mapping.get("elementos", mapping)  # admite el dict directo
    escritos, no_encontrados = [], []
    n_props = 0
    for clave, psets in elementos.items():
        el = por_nombre.get(clave) or por_gid.get(clave)
        if el is None:
            no_encontrados.append(clave)
            continue
        for pset_name, props in psets.items():
            props = _limpiar(props)
            if not props:
                continue
            ps = run("pset.add_pset", ifc, product=el, name=pset_name)
            run("pset.edit_pset", ifc, pset=ps, properties=props)
            n_props += len(props)
        escritos.append(clave)
    ifc.write(out_path)
    resumen = {"elementos_escritos": len(escritos), "propiedades": n_props,
               "no_encontrados": no_encontrados, "salida": out_path}
    print("Psets de resultado escritos: %d elemento(s), %d propiedad(es) -> %s"
          % (len(escritos), n_props, out_path))
    if no_encontrados:
        print("  ! no encontrados (%d): %s" % (len(no_encontrados),
              ", ".join(map(str, no_encontrados[:10]))))
    return resumen


def main(ifc_path, mapping_path, out_path):
    with open(mapping_path, encoding="utf-8") as fh:
        mapping = json.load(fh)
    escribir(ifc_path, mapping, out_path)
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
