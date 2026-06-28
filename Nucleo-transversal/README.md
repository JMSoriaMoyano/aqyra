# Núcleo transversal — contratos del ecosistema

Capa compartida por **todas las disciplinas** (estructuras, instalaciones, obra civil…). Una
disciplina nueva "enchufa" al núcleo cumpliendo estos contratos, **sin reescribir la fontanería**.
Ver la arquitectura completa en `../Hoja-de-ruta_Ecosistema-ingenieria.md`.

> **Numeración reconciliada 2026-06-27 (firmada por JM).** El **registro único de la verdad** es el de la zona protegida `Estructurando 2.0/contratos-golden/`. Esquema vigente: **interfaces C1–C8** · **convenciones de núcleo CN-***. Las antiguas C2/C3 de esta carpeta se renumeraron a CN-1/CN-2 (sus ficheros `C2_…`/`C3_…` quedan como punteros). La antigua «C4 — acciones» de esta tabla **NO** es el C4 canónico (C4 canónico = red): queda como convención de núcleo pendiente de número (ver propuesta de seguimiento de coordinación).

| Contrato | Qué fija | Archivo |
|---|---|---|
| **C1 — IFC / modelo neutro** | E/S en IFC y modelo neutro común (incl. plan de extensión MEP) | `C1_Contrato-IFC-modelo-neutro.md` |
| **CN-1 — Memoria del despacho** | Aprendizaje entre hilos: criterios + memoria por proyecto | `CN-1_Convencion-memoria-despacho.md` *(antes C2)* |
| **CN-2 — Entregables / documentación** | Estructura homogénea de memoria y documentación | `CN-2_Convencion-entregables-documentacion.md` *(antes C3)* |
| **CN-3 — Acciones / bases de cálculo / demanda** | EC0/EC1 + DB-SE-AE (estructuras), bases de demanda (MEP), tráfico/hidrología (lineal) | `CN-3_Convencion-acciones-bases-de-calculo.md` *(antes rotulada «C4»; C4 canónico = red, interfaz)* |
| **C5 — Motor FEM** *(spec de ingeniería)* | Modelo de análisis FEM + API del solver | `C5_Contrato-motor-FEM.md` — *interfaz canónica en `contratos-golden/contratos/C5_motor-fem.md`* |

Plantillas listas para copiar al crear una disciplina:
- `plantilla-criterios-disciplina.md` → raíz de la carpeta de trabajo
- `plantilla-memoria.md` → subcarpeta de cada proyecto

> Todo cálculo y entregable es de predimensionado/asistencia y debe ser **revisado y firmado por
> técnico competente** (Ingeniero de Caminos).
