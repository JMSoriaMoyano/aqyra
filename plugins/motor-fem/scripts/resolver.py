"""
API estable del nucleo FEM (contrato C5).

`resolver(modelo, analisis="estatico_lineal", combos=None)` es la unica puerta
de entrada que cualquier disciplina (puentes, estructuras singulares,
tensoestructuras) usa para pedir calculo, de forma AGNOSTICA a la disciplina.

- `modelo`: dict del modelo de analisis (C5) -- extiende el modelo neutro
  estructural (C1 §2) -- o un objeto `ModeloFEM` ya construido.
- `analisis`:
  - "estatico_lineal" (FEM-0): combinaciones ELU/ELS por superposicion.
  - "modal"  (FEM-1): frecuencias propias, modos y masa participante. Lee la
     clave `masas` del modelo (desde_peso_propio / casos_masa / nodales).
  - "movil"  (FEM-1): lineas de influencia + envolventes por tren de cargas.
     Lee la clave `cargas_moviles` (lineas/objetivos/tren).
  - "pandeo_lineal", "no_lineal": ganchos reservados (FEM-3+; NotImplementedError).
- Devuelve la salida del analisis correspondiente (ver C5 §3).

Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from fem_core import ModeloFEM       # noqa: E402
import mallador                       # noqa: E402
import fem1                           # noqa: E402

ANALISIS_ESTATICO = ("estatico_lineal",)
ANALISIS_FEM1 = ("modal", "movil")
ANALISIS_GANCHO = ("pandeo_lineal", "no_lineal")


def resolver(modelo, analisis="estatico_lineal", combos=None):
    if analisis in ANALISIS_GANCHO:
        raise NotImplementedError(
            "Analisis '%s' es un gancho reservado del contrato C5; se implementa "
            "en FEM-3+ (pandeo/no lineal). Disponibles: %s."
            % (analisis, ", ".join(ANALISIS_ESTATICO + ANALISIS_FEM1)))
    if analisis not in (ANALISIS_ESTATICO + ANALISIS_FEM1):
        raise ValueError("analisis desconocido: %s" % analisis)

    # construir/obtener el ModeloFEM
    if isinstance(modelo, ModeloFEM):
        M = modelo; mdict = None
    elif isinstance(modelo, dict):
        M = mallador.desde_modelo_neutro(modelo); mdict = modelo
    else:
        raise TypeError("modelo debe ser dict (modelo de analisis C5) o ModeloFEM")

    # --- FEM-1: modal ---
    if analisis == "modal":
        cfg = (mdict or {}).get("masas", {}) if mdict is not None else {}
        return fem1.modal(M, nmodos=int(cfg.get("nmodos", 6)),
                          peso_propio=bool(cfg.get("desde_peso_propio", True)),
                          masas_casos=cfg.get("casos_masa"),
                          masas_nodales=cfg.get("nodales"))

    # --- FEM-1: cargas moviles / lineas de influencia ---
    if analisis == "movil":
        cm = (mdict or {}).get("cargas_moviles") if mdict is not None else None
        if cm is None:
            raise ValueError("analisis 'movil' requiere la clave 'cargas_moviles' en el modelo")
        return fem1.movil(M, cm)

    # --- FEM-0: estatico lineal ---
    if mdict is not None and combos is None:
        combos = _combos_por_defecto(mdict)
    return M.resolver(combos)


def _combos_por_defecto(modelo):
    """Combinaciones EC0/AN-ES por defecto si el modelo declara casos G/Q."""
    casos = set()
    for c in modelo.get("cargas", []):
        casos.add(c.get("caso"))
    has_g, has_q = "G" in casos, "Q" in casos
    if has_g and has_q:
        return {"ELU": {"G": 1.35, "Q": 1.50}, "ELU_G": {"G": 1.35},
                "ELS_car": {"G": 1.0, "Q": 1.0}, "ELS_fre": {"G": 1.0, "Q": 0.5},
                "ELS_cp": {"G": 1.0, "Q": 0.3}, "ELS_act": {"Q": 1.0}}
    if has_g:
        return {"ELU": {"G": 1.35}, "ELS_car": {"G": 1.0}}
    return None
