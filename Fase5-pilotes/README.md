# Fase 5 — Pilotes (cimentación profunda)

Tercer caso del bloque de cimentaciones de la hoja de ruta v2. Combina lo ya
construido: **geotecnia EC7**, el **solver de barras** (pilote como viga sobre
muelles laterales) y, para el encepado, las **bielas y tirantes** de la Fase 4.

## Caso: pilote individual bajo carga vertical + horizontal

Subcarpeta `proyecto-pilote/`. Pilote C30/37 Ø600 mm, L = 12 m; terreno con módulo
de balasto horizontal kh = 15 MN/m³ y resistencias unitarias de fuste/punta; cargas
en cabeza N_G = 900, N_Q = 300 kN y H = 80 kN (lateral).

Se desacoplan las dos físicas (práctica habitual de predimensionado):

**A) Capacidad axil (EC7):** R_c,d = R_s,k/γ_s + R_b,k/γ_b.
- R_s,k (fuste) = 1357 kN, R_b,k (punta) = 707 kN → **R_c,d = 1876 kN**.
- N_Ed = 1665 kN → **89 %** → OK.

**B) Comportamiento lateral (viga sobre muelles):** el pilote se discretiza en
elementos de barra con muelles horizontales (kh·D·trib) en cada nodo — **reutiliza
el solver de la Fase 1**.
- M_max = 118 kN·m (a ~2,2 m de profundidad), V_max = 101 kN.
- Flecha en cabeza = 5,7 mm ≤ 10 mm (**57 %**), equilibrio lateral 0,00 %.

**Sección EC2 (flexo-compresión):** e/D = 0,12; armadura mínima de pilote (EN 1536,
0,5 % A_c) = 14,1 cm²; u_N 27 %, u_M 22 %. **CUMPLE**.

```bash
python3 scripts/generate_test_ifc_pilote.py
python3 scripts/run_all_pilote.py proyecto-pilote
NODE_PATH=$(npm root -g) node scripts/generate_memoria_pilote.js proyecto-pilote
```

## Arquitectura

| Script | Función |
|---|---|
| `generate_test_ifc_pilote.py` | IFC4: pilote (curve member) + terreno (kh, qs, qb) + cargas |
| `solver_pilote.py` | **EC7** capacidad axil + **viga sobre muelles laterales** (solver de barras) |
| `verificacion_pilote.py` | EC7 axil + flecha lateral + sección EC2 flexo-compresión |
| `plots_pilote.py` | Diagramas M(z) y deformada lateral dx(z) en profundidad |
| `generate_memoria_pilote.js` | Memoria de cálculo en Word |
| `run_all_pilote.py` | Orquestador |

> El **encepado** sobre los pilotes se calcula con el módulo de **bielas y tirantes**
> de la Fase 4 (`ec2_strut_tie`). Pilote + encepado cubren la cimentación profunda.

## Convenciones y decisiones

- **Axil y lateral desacoplados** (predimensionado estándar).
- **Lateral = viga sobre muelles horizontales** Winkler (kh·D·trib por nodo); el
  diagrama M(z) y la flecha de cabeza salen del solver de barras.
- **EC7 axil**: R_c,d con γ_s = γ_b = 1,10 [confirmar AN / enfoque de cálculo].

## Limitaciones

Análisis lineal y físicas desacopladas; balasto y resistencias del estudio geotécnico;
no se incluye rozamiento negativo, efecto grupo, P-Δ ni la interacción N-M completa por
diagrama. **Revisión y firma por técnico competente.**
