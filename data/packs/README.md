# data/packs — conocimiento externo versionado (esqueleto)

Un **pack** es una unidad versionada de conocimiento externo que un engine consume; **no es
código**. Cambiar de mercado, localidad o año = cambiar de pack, no de engine.

Cuatro familias (se llenan en **0.6**):

| Familia | Contenido | Lo consume |
|---|---|---|
| **Códigos** | coeficientes/curvas/fórmulas de dimensionamiento | C9 · C10 · C11+ |
| **Normativa** | reglas de cumplimiento + referencias de artículo | C3 |
| **Banco de precios** | partidas descompuestas + mapeo clasificación→partida | C5 |
| **Requisitos (IDS)** | Psets/clasif/valores exigidos | C4 · C7 |

Todo pack se ancla en `versions.lock` con su versión exacta y trae su **golden de pack**.
Datos grandes: git-lfs o referencia externa versionada — a decidir en 0.6.
Ver `../../Aqyra-Raiz/FUNDACION_C6_golden_y_packs.md`.
