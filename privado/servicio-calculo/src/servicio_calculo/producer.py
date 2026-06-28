"""Productor de resultados `computed` para POST /solve (anzuelo · servicio).

El servicio NO calcula: delega en un *productor* inyectable. Esto deja un
ÚNICO punto de swap entre el productor PROVISIONAL (PyNite) y el de PRODUCCIÓN
(`motor-fem 0.1.0` anclado, vía `puente_calculo.MotorFemBinding`).

D-019·C.4 / decisión de hilo V3-CONEXIÓN (PyNite provisional):
- El productor por defecto es PyNite (`pynite_producer`), para tener YA números
  reales en pantalla y poder reproducir los casos de uso de Estructurando.
- SALVEDAD de gobierno (D-023): la 2.ª llave (QA) exige un motor DISTINTO del que
  produjo. Mientras el productor sea PyNite y la QA también PyNite, la
  reconciliación NO es independiente (sí lo es el gate de equilibrio). El meta del
  servicio lo marca explícito (`independent: false`). La independencia real llega
  al cablear `motor-fem` (cambiar SOLO `default_producer`).

Importación PEREZOSA de PyNite: importar este módulo NO requiere PyNite; solo
`pynite_producer(...)` lo necesita (lo importa `solve_pynite` en su interior). Así
el servicio y sus tests cargan sin el solver instalado (los tests inyectan un fake).
"""
from __future__ import annotations

from typing import Callable

from puente_calculo import contract as c

#: Un productor toma una petición C5 y devuelve un grupo `computed` por combinación.
Producer = Callable[[c.CalcRequest], list[c.ResultGroup]]

#: Identificador del productor PROVISIONAL (para meta/telemetría y el chip del visor).
PROVISIONAL_ID = "pynite-provisional"

#: Aviso de gobierno que acompaña a cada resultado producido en modo provisional.
PROVISIONAL_WARNING = (
    "Números reales con PyNite (productor provisional). La 2.ª llave (QA) aún NO es "
    "independiente: la independencia real (D-023) llega al cablear motor-fem. "
    "El verde solo lo acuña la firma de JM."
)


def _combos(req: c.CalcRequest) -> list[c.Combination]:
    return req.combinations or [c.Combination(id="ELU1", name="ELU", limitState="ULS", terms={})]


def pynite_producer(req: c.CalcRequest) -> list[c.ResultGroup]:
    """Productor PROVISIONAL: resuelve cada combinación con PyNite -> `computed`.

    Reutiliza el solver de la QA (`qa_pynite.solve_pynite`), que re-ensambla desde
    el contrato C5 con convenio D-018. Importa PyNite de forma perezosa.
    """
    from qa_pynite import solve_pynite

    groups: list[c.ResultGroup] = []
    for cb in _combos(req):
        rg = solve_pynite(req, cb.id)
        # solve_pynite ya nace state="computed" (0 llaves, D-021).
        groups.append(rg)
    return groups


def motorfem_producer(req: c.CalcRequest) -> list[c.ResultGroup]:
    """Productor de PRODUCCIÓN: `motor-fem 0.1.0` anclado vía el binding.

    No usable hasta que `motor-fem` esté disponible/cableado (entrypoint + signo
    confirmados). Es el punto único de swap respecto a `pynite_producer`.
    """
    from puente_calculo import solve_request
    from puente_calculo.engine import MotorFemBinding

    return solve_request(req, MotorFemBinding())


#: Productor por defecto del servicio. Cambiar AQUÍ (y solo aquí) a
#: `motorfem_producer` cuando motor-fem esté cableado (independencia real D-023).
default_producer: Producer = pynite_producer
