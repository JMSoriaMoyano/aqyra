"""Librería FINITA de evaluadores deterministas del C3 (D8).

El pack declara, por exigencia, cuál usar (`evaluador` + `parametros`); el engine mapea
nombre→función (`EVALUADORES`). Añadir una exigencia de método conocido = solo pack; un método
genuinamente nuevo = un evaluador nuevo aquí (honesto, raro). Esto es lo que hace real el lema
"el código es un PACK anclado, no un `if`": el `if` que quedara cableado sería exactamente el
`if id == ...` que este registro evita.

Cada evaluador recibe el contexto del Maestro (`ctx`) y los `parametros` del pack y devuelve un
FRAGMENTO de exigencia: `{resultado, evidencia?, motivo_no_verificable?, por_modelo?}`. El
`resultado` pertenece a la taxonomía CERRADA de 4 (D4). El texto libre (`evidencia`, `motivo`,
`detalle`) es presentación humana: el runner lo normaliza y NO lo compara literalmente (D9).

ctx = {
  "derivado":  ifcopenshell.file,        # la vista del Maestro (D7)
  "guid2mod":  {GlobalId: id_modelo},    # procedencia (modelo.guid_a_modelo)
  "modelos":   [id_modelo, ...],         # orden del manifiesto
  "uso":       {"principal": ...},       # DECLARADO (ADR)
  "localizacion": {...},                 # DECLARADA
}
"""
from __future__ import annotations

from collections import defaultdict

from . import modelo as M

# Taxonomía CERRADA del resultado (D4) — el enum del veredicto-cumplimiento.schema.json.
RESULTADOS = ("cumple", "no-cumple", "no-aplica", "no-verificable")

# Clases estructurales por defecto (parametrizable desde el pack).
CLASES_ESTRUCTURALES = (
    "IfcColumn", "IfcWall", "IfcWallStandardCase",
    "IfcSlab", "IfcFooting", "IfcBeam", "IfcMember",
)


def presencia_tipo_ifc(ctx: dict, params: dict) -> dict:
    """cumple si el derivado contiene ≥1 entidad de `clase` (opcional `predefined_type`).

    Uso típico (E-SUA-ACCESO): ¿hay un medio accesible de comunicación vertical? →
    presencia de IfcTransportElement con PredefinedType=ELEVATOR.
    """
    clase = params["clase"]
    pdt = params.get("predefined_type")
    encontrados = [e for e in ctx["derivado"].by_type(clase)
                   if pdt is None or str(getattr(e, "PredefinedType", None)) == pdt]
    etiqueta = clase + (f"/{pdt}" if pdt else "")
    if encontrados:
        nombres = ", ".join(str(getattr(e, "Name", None)) for e in encontrados[:5])
        return {"resultado": "cumple",
                "evidencia": f"El Maestro federado contiene {len(encontrados)} {etiqueta} "
                             f"({nombres}); requisito satisfecho."}
    return {"resultado": "no-cumple",
            "evidencia": f"El Maestro federado no contiene ningún {etiqueta}."}


def presencia_propiedad_pset(ctx: dict, params: dict) -> dict:
    """cumple si TODOS los elementos de las clases objetivo DECLARAN `propiedad` en algún Pset.

    Reparte por modelo (procedencia, D2): `n_comprobados` / `n_fallos` por id de modelo. Uso
    típico (E-SI-RF-DECL): ¿cada elemento estructural declara su resistencia al fuego (FireRating)?
    Verifica la DECLARACIÓN del dato; el valor R exigido por cálculo es tarea de un motor (aparte).
    """
    clases = set(params.get("clases", CLASES_ESTRUCTURALES))
    prop = params["propiedad"]
    guid2mod = ctx["guid2mod"]

    comprob: dict = defaultdict(int)
    fallos: dict = defaultdict(int)
    tipos: dict = defaultdict(lambda: defaultdict(int))

    # by_type("IfcElement") + filtro por clase EXACTA: sin doble conteo de subtipos.
    elementos = [e for e in ctx["derivado"].by_type("IfcElement") if e.is_a() in clases]
    for e in elementos:
        mid = guid2mod.get(M.guid_de(e), "?")
        comprob[mid] += 1
        tipos[mid][e.is_a()] += 1
        if not _declara_propiedad(e, prop):
            fallos[mid] += 1

    n_total = sum(comprob.values())
    n_fallos = sum(fallos.values())
    por_modelo: dict = {}
    for mid in sorted(comprob):
        det = " + ".join(f"{c}×{n}" for c, n in sorted(tipos[mid].items()))
        por_modelo[mid] = {
            "resultado": "no-cumple" if fallos[mid] else "cumple",
            "n_comprobados": comprob[mid],
            "n_fallos": fallos[mid],
            "detalle": (f"{det} sin {prop}" if fallos[mid] else f"{det} con {prop}"),
        }

    resultado = "no-cumple" if n_fallos else "cumple"
    evidencia = (f"{n_fallos} de {n_total} elementos estructurales del Maestro no declaran "
                 f"{prop} en su Pset común."
                 if n_fallos else
                 f"Los {n_total} elementos estructurales del Maestro declaran {prop}.")
    return {"resultado": resultado, "evidencia": evidencia, "por_modelo": por_modelo}


def aplica_solo_uso(ctx: dict, params: dict) -> dict:
    """no-aplica si el `uso` declarado NO está entre los usos objetivo de la exigencia.

    Uso típico (E-RSCIEI): el reglamento industrial no rige para un uso residencial. Si SÍ
    aplicara, el fragmento devuelve `resultado_si_aplica` (por defecto no-verificable, forward-open:
    la verificación del propio código industrial es materia de otro pack/motor).
    """
    objetivo = [u.lower() for u in params.get("usos", [])]
    principal = (ctx["uso"].get("principal") or "")
    aplica = any(u in principal.lower() for u in objetivo)
    if not aplica:
        return {"resultado": "no-aplica",
                "evidencia": f"Uso declarado '{principal}'; la exigencia rige para usos "
                             f"{params.get('usos')}. No aplica a este edificio."}
    frag = {"resultado": params.get("resultado_si_aplica", "no-verificable"),
            "evidencia": f"Uso declarado '{principal}'; la exigencia aplica."}
    if frag["resultado"] == "no-verificable":
        frag["motivo_no_verificable"] = params.get(
            "motivo", "La exigencia aplica al uso declarado, pero su verificación requiere el "
                      "desarrollo del código correspondiente (no disponible en v0).")
    return frag


def requiere_motor(ctx: dict, params: dict) -> dict:
    """no-verificable + motivo: la exigencia exige un motor/dato no derivable del IFC en v0.

    Es la esencia multi-código HONESTA del C3 (D4): forward-open — un engine futuro (evacuación,
    térmico, hidráulico…) la reclasifica en cumple/no-cumple SIN cambiar el esquema. El `motivo`
    (qué motor/dato lo cerraría) viaja en el pack.
    """
    return {
        "resultado": "no-verificable",
        "motivo_no_verificable": params.get(
            "motivo", "Requiere un motor de cálculo o datos no derivables del IFC en v0; un engine "
                      "futuro lo reclasifica sin cambiar el esquema (D4)."),
        "evidencia": params.get(
            "evidencia", "El Maestro aporta geometría y estructura espacial, pero esta exigencia "
                         "exige cálculo no disponible en v0."),
    }


# --------------------------------------------------------------------------- #
# Registro (nombre del pack → función). La única "tabla de verdad" del engine. #
# --------------------------------------------------------------------------- #
EVALUADORES = {
    "presencia-tipo-ifc": presencia_tipo_ifc,
    "presencia-propiedad-pset": presencia_propiedad_pset,
    "aplica-solo-uso": aplica_solo_uso,
    "requiere-motor": requiere_motor,
}


def _declara_propiedad(elemento, prop: str) -> bool:
    """True si algún Pset del elemento trae `prop` con valor no vacío."""
    for pset in M.psets(elemento).values():
        if isinstance(pset, dict) and prop in pset and pset[prop] not in (None, ""):
            return True
    return False
