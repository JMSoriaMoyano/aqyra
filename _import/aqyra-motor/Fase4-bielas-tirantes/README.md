# Fase 4 — Bielas y tirantes (regiones D)

Segundo caso del catálogo de la hoja de ruta v2. Implementa el método de **bielas y
tirantes (EN 1992-1-1 §6.5)** para regiones de discontinuidad (regiones D), que
desbloquea **encepados de pilotes, vigas de gran canto y ménsulas**.

Punto clave: el modelo de celosía (bielas a compresión + tirantes a tracción)
**reutiliza el solver de barras de la Fase 1**, cerrando el círculo del enfoque
"núcleo estable + catálogo de casos".

## Caso: encepado de 2 pilotes

Subcarpeta `proyecto-encepado/`. Encepado C30/37, separación de pilotes a = 1,8 m,
canto 0,9 m, ancho 0,9 m; pilar 400×400, pilotes Ø450; N_G = 1300, N_Q = 450 kN.

**Resultados (N_Ed = 2430 kN):**
- Celosía resuelta con el solver de barras: **T = 1464 kN, C = 1902 kN**, que
  **coincide con la estática cerrada (error 0,00 %)** → validación.
- **Tirante**: As = 33,7 cm² (B500S).
- **Biela** (compresión con tracción transversal): 53 % → OK.
- **Nudo CCC** (bajo pilar): 86 % → OK. **Nudo CCT** (sobre pilote): 51 % → OK.
- **CUMPLE**. Esquema del modelo de bielas y tirantes con esfuerzos.

```bash
python3 scripts/generate_test_ifc_encepado.py
python3 scripts/run_all_encepado.py proyecto-encepado
NODE_PATH=$(npm root -g) node scripts/generate_memoria_encepado.js proyecto-encepado
```

## Arquitectura

| Script | Función |
|---|---|
| `generate_test_ifc_encepado.py` | IFC4: encepado (geometría) + 2 pilotes + carga de pilar |
| `ec2_strut_tie.py` | **Núcleo**: celosía 2 pilotes (solver de barras) + checks §6.5 (biela, nudos CCC/CCT, tirante) |
| `plots_encepado.py` | Esquema del modelo de bielas y tirantes |
| `generate_memoria_encepado.js` | Memoria de cálculo en Word |
| `run_all_encepado.py` | Orquestador (IFC → ELU → STM → esquema) |

## Método (EC2 §6.5)

- **Celosía**: nudo superior bajo el pilar, dos pilotes abajo; θ = atan(z / (a/2)),
  z = brazo mecánico ≈ 0,9·d. Reacción por pilote = N/2 (carga centrada).
- **Tirante**: T = (N/2)/tan θ → As = T/fyd.
- **Bielas**: σc ≤ σRd,max = 0,6·ν'·fcd (con tracción transversal).
- **Nudos**: CCC (bajo pilar) ≤ ν'·fcd; CCT (sobre pilote, ancla el tirante) ≤ 0,85·ν'·fcd.
- ν' = 1 − fck/250.

## Reutilización para otras regiones D

El mismo `ec2_strut_tie` (forma de la celosía + checks de biela/nudo/tirante) cubre:
- **Vigas de gran canto** (deep beams): celosía con biela diagonal + tirante inferior.
- **Ménsulas / cartelas** (corbels): biela inclinada + tirante horizontal superior.
- **Encepados de 3–4 pilotes**: ampliar la celosía a 3D.
- **Zonas de apoyo y aberturas**: modelos locales.

## Limitaciones

Celosía estáticamente determinada (carga centrada); cargas excéntricas o más pilotes
amplían el modelo. No se incluye el detalle de anclaje del tirante ni armadura de piel.
La orientación del modelo puede semiautomatizarse desde el campo de tensiones FE.
**Revisión y firma por técnico competente.**
