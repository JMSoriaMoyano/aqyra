# Memoria de cálculo — Estribo de puente (caso PUE-06)

> **Predimensionado/asistencia. Debe ser revisado y firmado por técnico competente
> (Ingeniero de Caminos, Canales y Puertos).** NDP marcados `[confirmar AN]`.

## 1. Objeto y normativa
Predimensionado de un **estribo** de puente de carretera, tratado como **muro ménsula
con cargas de tablero**, según EN 1997-1 (EC7), EN 1992-1-1 (EC2) e **IAP-11**
(acciones). Reutiliza el dimensionado de muros de contención de `motor-calculo`.

## 2. Idealización (consume motor-fem, contrato C5)
Estribo tipo muro ménsula: alzado Hm = 4,5 m, espesor 0,85 m; zapata B = 7,85 m
(puntera 3,4 + alzado 0,85 + talón 3,6), canto 1,8 m; HA-30. Las **reacciones del
tablero** se inyectan en la **coronación**: vertical permanente N_G = 600 kN, vertical
de tráfico N_LM1 = 250 kN, **horizontal de frenado** H = 80 kN. El **fuste (alzado)**
se resuelve como ménsula vertical con **motor-fem** (no PyNite).

## 3. Acciones (IAP-11 + EC7)
- **Empuje de tierras activo Ka = 0,307** (Rankine, φ = 32°) — estribo abierto/con
  junta (con movilidad). Selector a **reposo K0 = 1 − sin φ** para estribo
  cerrado/integral. `[confirmar AN]`
- **Sobrecarga de tráfico** tras el trasdós q = 10 kPa (variable).
- **Frenado del tablero** (80 kN) incluido en la **estabilidad global** (extensión del
  estribo sobre un muro de contención estándar).
- Coeficientes parciales DA-2*/EQU (AN España) según `verificacion_muro`. `[confirmar AN]`

## 4. Comprobación EC7 — estabilidad geotécnica
| Estado límite | Aprovechamiento | Verificación |
|---|---|---|
| **Vuelco** (EQU) | 0,20 | CUMPLE |
| **Deslizamiento** (GEO, DA-2*) | 0,35 | CUMPLE |
| **Hundimiento** (GEO, Meyerhof B') | 0,51 | CUMPLE — q_Ed = 330 kPa ≤ Rd = 650 kPa |

Excentricidad e = 0,27 m ≤ B/6 (sin despegue).

## 5. Comprobación EC2 — alzado, puntera y talón
| Elemento | Cortante (aprov) | Armado |
|---|---|---|
| **Alzado** (arranque) | 0,77 | Ø25/225 trasdós (As = 21,8 cm²/m) |
| **Puntera** | **0,97** (gobierna) | Ø25 inferior |
| **Talón** | 0,36 | Ø superior |

El cortante de puntera se comprueba por **V_Rd,c sin armadura de cortante** (zapata
superficial), que gobierna el predimensionado.

## 6. Conclusión
**VEREDICTO: CUMPLE** · aprovechamiento máximo **0,971** (cortante de puntera). El
predimensionado del estribo es satisfactorio para las acciones consideradas, con la
puntera próxima a su capacidad a cortante. Pendiente: empuje en servicio del relleno,
acción sísmica y dimensionado de detalle. **Revisar y firmar por ICCP.**

---
*Registro: 2026-06-23 · estribo PUE-06 · run_all_estribo · aprov 0,971 · CUMPLE.*
