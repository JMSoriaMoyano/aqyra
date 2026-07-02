"""Helper CLI de los run_all_*: carga el cfg desde un JSON de caso o, si el argumento
es un .ifc, desde el LECTOR estructural (parser C1 -> adaptador desde_ifc por tipologia).
Asi `run_all_X.py modelo.ifc resultado.json` calcula directamente desde el IFC.
Predimensionado; revisar y firmar por tecnico competente (ICCP)."""
import json, os, sys

def load_cfg(path):
    if str(path).lower().endswith(".ifc"):
        _here = os.path.dirname(os.path.abspath(__file__))
        if _here not in sys.path:
            sys.path.insert(0, _here)
        import desde_ifc
        return desde_ifc.leer(path)
    with open(path) as f:
        return json.load(f)
