"""
VALIDACION DE RED (arnes propio, analogo al de equilibrio estructural).
PT 4.2 (Ola 4, hueco H2). NO calcula hidraulica: solo TOPOLOGIA y unidades.

Comprueba sobre el modelo neutro de red MEP (emitido por ifc_to_model_mep.py):
  1. UNIDADES: bloque `unidades` presente y SI coherente (longitud = m).
  2. FUENTES: existe al menos una fuente (ancla de la red) mapeada a un nodo.
  3. CONTINUIDAD: el grafo es CONEXO desde la(s) fuente(s) -- todo nodo alcanzable
     (BFS por tramos). Reutiliza el nucleo: grafo_red.filtrar_componentes_
     desconectadas(es_ancla = nodo fuente) para detectar componentes HUERFANAS.
  4. TERMINALES: todo terminal esta conectado (su nodo es alcanzable desde fuente).
  5. INTEGRIDAD: cada tramo referencia nodos existentes; sin tramos sueltos.

Veredicto CUMPLE solo si no hay errores bloqueantes. Es predimensionado/asistencia
y debe ser revisado y firmado por tecnico competente.

Uso:  python3 validacion_red.py modelo_neutro_mep.json [salida_verificacion.json]
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_NUCLEO = os.path.join(_HERE, "..", "nucleo")
if _NUCLEO not in sys.path:
    sys.path.insert(0, _NUCLEO)
import grafo_red   # noqa: E402  (filtrar_componentes_desconectadas, union-find)


def _bfs_alcanzables(nodos, tramos, fuentes_nodos):
    """Conjunto de nodos alcanzables desde cualquier nodo fuente por los tramos."""
    ady = {nm: set() for nm in nodos}
    for t in tramos.values():
        ni, nj = t.get("ni"), t.get("nj")
        if ni in ady and nj in ady:
            ady[ni].add(nj)
            ady[nj].add(ni)
    visto = set()
    pila = [n for n in fuentes_nodos if n in nodos]
    while pila:
        u = pila.pop()
        if u in visto:
            continue
        visto.add(u)
        pila.extend(ady[u] - visto)
    return visto


def validar(modelo):
    errores, avisos, info = [], [], []
    nodos = modelo.get("nodos", {})
    tramos = modelo.get("tramos", {})
    terminales = modelo.get("terminales", [])
    fuentes = modelo.get("fuentes", [])
    vertidos = modelo.get("vertidos", []) or []

    # 1) unidades SI
    u = modelo.get("unidades", {})
    if not u:
        errores.append("Falta el bloque 'unidades'.")
    elif u.get("longitud") != "m":
        errores.append("Unidad de longitud no SI (esperado 'm'): %r" % u.get("longitud"))
    else:
        info.append("Unidades SI declaradas: %s" % u)

    # 5) integridad de tramos
    sueltos = [tid for tid, t in tramos.items()
               if t.get("ni") not in nodos or t.get("nj") not in nodos]
    if sueltos:
        errores.append("Tramos que referencian nodos inexistentes: %s" % sueltos)

    # 2) anclas: fuentes (red a presion) o VERTIDOS/outfall (saneamiento por gravedad)
    fuentes_nodos = [f.get("nodo") for f in fuentes if f.get("nodo")]
    vertidos_nodos = [v.get("nodo") for v in vertidos if v.get("nodo")]
    anclas = fuentes_nodos + vertidos_nodos
    if not anclas:
        errores.append("No hay fuentes ni vertidos mapeados a un nodo (la red no "
                       "tiene ancla).")
    elif vertidos_nodos:
        info.append("Vertido(s)/outfall: %d (nodos %s); fuentes: %d"
                    % (len(vertidos_nodos), vertidos_nodos, len(fuentes_nodos)))
    else:
        info.append("Fuentes: %d (nodos %s)" % (len(fuentes), fuentes_nodos))

    # marcar es_ancla = nodo fuente (por 'tipo' o por estar en fuentes_nodos)
    set_fuentes = set(fuentes_nodos) | set(vertidos_nodos)
    for nm, n in nodos.items():
        if n.get("tipo") in ("fuente", "vertido"):
            set_fuentes.add(nm)

    # 3) continuidad / componentes huerfanas (union-find del nucleo)
    drop_t, drop_n = grafo_red.filtrar_componentes_desconectadas(
        nodos, tramos, lambda nm, nd: nm in set_fuentes)
    if drop_t:
        errores.append("Componentes HUERFANAS (no conectadas a fuente): %d tramos %s, "
                       "%d nodos %s" % (len(drop_t), drop_t[:6], len(drop_n), drop_n[:6]))
    else:
        info.append("Sin componentes huerfanas (todos los tramos cuelgan de una fuente).")

    # BFS de cobertura
    alcanzables = _bfs_alcanzables(nodos, tramos, set_fuentes) if set_fuentes else set()
    n_total = len(nodos)
    cobertura = (100.0 * len(alcanzables) / n_total) if n_total else 0.0
    info.append("Cobertura desde fuente: %d/%d nodos (%.1f %%)"
                % (len(alcanzables), n_total, cobertura))
    if set_fuentes and cobertura < 100.0:
        errores.append("Grafo NO conexo desde la fuente: %.1f %% de nodos alcanzables"
                       % cobertura)

    # 4) terminales conectados
    n_term_desc = 0
    for term in terminales:
        nm = term.get("nodo")
        if nm is None:
            avisos.append("Terminal %s sin nodo mapeado." % term.get("id"))
            n_term_desc += 1
        elif nm not in alcanzables:
            errores.append("Terminal %s (nodo %s) NO conectado a la fuente."
                           % (term.get("id"), nm))
            n_term_desc += 1
    if terminales and n_term_desc == 0:
        info.append("Terminales conectados: %d/%d." % (len(terminales), len(terminales)))
    if not terminales:
        avisos.append("La red no declara terminales.")

    veredicto = "CUMPLE" if not errores else "NO CUMPLE"
    return {
        "veredicto": veredicto,
        "sistema": modelo.get("sistema", {}).get("tipo"),
        "resumen": {
            "nodos": n_total, "tramos": len(tramos),
            "terminales": len(terminales), "fuentes": len(fuentes),
            "cobertura_pct": round(cobertura, 2),
            "huerfanas_tramos": len(drop_t),
        },
        "errores": errores, "avisos": avisos, "info": info,
    }


def main(path, out=None):
    with open(path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    res = validar(modelo)
    print("=" * 64)
    print("VALIDACION DE RED MEP --", os.path.basename(path))
    print("=" * 64)
    for i in res["info"]:
        print("  i ", i)
    for w in res["avisos"]:
        print("  ! ", w)
    for e in res["errores"]:
        print("  X ", e)
    print("\nVEREDICTO:", res["veredicto"], "| sistema:", res["sistema"],
          "| resumen:", res["resumen"])
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2, ensure_ascii=False)
        print("Verificacion escrita en", out)
    return 0 if res["veredicto"] == "CUMPLE" else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
