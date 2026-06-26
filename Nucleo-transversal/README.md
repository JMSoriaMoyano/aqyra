# Núcleo transversal — contratos del ecosistema

Capa compartida por **todas las disciplinas** (estructuras, instalaciones, obra civil…). Una
disciplina nueva "enchufa" al núcleo cumpliendo estos contratos, **sin reescribir la fontanería**.
Ver la arquitectura completa en `../Hoja-de-ruta_Ecosistema-ingenieria.md`.

| Contrato | Qué fija | Archivo |
|---|---|---|
| **C1 — IFC / modelo neutro** | E/S en IFC y modelo neutro común (incl. plan de extensión MEP) | `C1_Contrato-IFC-modelo-neutro.md` |
| **C2 — Memoria del despacho** | Aprendizaje entre hilos: criterios + memoria por proyecto | `C2_Contrato-memoria-despacho.md` |
| **C3 — Entregables / memoria** | Estructura homogénea de memoria y documentación | `C3_Contrato-entregables-memoria.md` |
| **C4 — Acciones / bases de cálculo** | EC0/EC1 + DB-SE-AE como entrada compartida | *(skill `bases-acciones` en `estructuras-eurocodigos`)* |

Plantillas listas para copiar al crear una disciplina:
- `plantilla-criterios-disciplina.md` → raíz de la carpeta de trabajo
- `plantilla-memoria.md` → subcarpeta de cada proyecto

> Todo cálculo y entregable es de predimensionado/asistencia y debe ser **revisado y firmado por
> técnico competente** (Ingeniero de Caminos).
