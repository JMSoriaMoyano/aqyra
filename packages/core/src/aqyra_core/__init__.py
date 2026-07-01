"""aqyra_core — núcleo compartido, agnóstico al solver (esqueleto de Fase 0).

En 0.5 se extrae aquí el núcleo real y se retira el espejo byte-a-byte:
  - ifc_utils: psets(element), length_scale(ifc), pset_value(...), álgebra 4x4.
  - grafo_red: RegistroNodos, punto_en_segmento, cortes_por_interseccion,
               filtrar_componentes_desconectadas, construir_grafo(segmentos, tol).
Devuelve topología, no calcula. No habla IFC de dominio; no tiene contrato pesado.
"""

__version__ = "0.0.0"
