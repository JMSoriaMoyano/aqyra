# services/

Servicios del ecosistema (se desarrollan por fase, contract-first):

- **C4 federación** — `federacion/` (paquete uv `aqyra-federacion` 0.1.0, Fase II·h2):
  `federar(ifcs[], reglas) → manifiesto` + `validar(maestro, ids) → informe QA` contra el
  contrato `packages/contracts/C4-federacion` y la golden `C4-FED-01` (recompute en el
  runner). Motor IDS propio mínimo (D7). Pendiente v0.x: IFC federado derivado (D6);
  tarea 1.2: emisión de topics BCF 3.0 (D8).
- **C7 operador IA** — draft v0.1.0.

El **CDE (C8) se desarrolla fuera** del monorepo y solo cumple la API de C8 en runtime; por
eso `contracts` **no se publica** a ningún registro (sin infraestructura de paquetes por ahora).
