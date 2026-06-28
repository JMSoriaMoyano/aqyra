# Informe de QA por cálculo — DEC-B4 (CRÍTICO)

> **QA verificado con FEM nodal numpy independiente + analítico. SIN el oráculo PyNite certificado (no instalable en este entorno) → pendiente de RE-EJECUCIÓN en entorno con PyNite para el cierre definitivo. Pendiente de firma de JM (la IA no certifica).**

- **Caso golden:** DEC-B4 — Montante del Cajón O SHS 120×6 (pandeo según arriostramiento)
- **Contrato / golden:** C-B4 v0
- **Fecha de verificación:** 2026-06-24
- **Ejecutado por:** agente de QA (ejecución separada) · **Oráculo:** FEM nodal 2D propio (numpy) + EC3 6.3.1
- **Versión verificada:** **NO ANCLADA**

> La certificación requiere la firma de JM. La IA no firma. **Este es el punto crítico de decisión del cálculo.**

---

## 1. Trazabilidad

```
input:       IFC #113 SHS 120×6 (A=27,4 cm², i=4,61 cm); montante vertical h=9,25 m
             (Z=5,75→15,0); nudos REALES en Z=5,75/8,833/11,917/15,0 (cordones cruzan)
version:     no anclada
norma:       EC3 6.3.1 (pandeo curva b), γM1=1,05; S355
metodo QA:   FEM nodal 2D con conectividad real -> L de pandeo efectiva del montante;
             EC3 cerrado para ambos escenarios (arriostrado vs no arriostrado)
resultado:   L_cr REAL = 3,08 m (segmento entre nudos de cordón); N_b,Rd=632 kN;
             N_Ed,QA(FEM)≈392 kN -> u=0,62; N_Ed,build=250 kN -> u=0,40
oraculo:     FEM nodal (determina la L de pandeo por la conectividad) + EC3
comparacion: ver §2 y §5 (binario)
```

## 2. Capa 1 — Numérica (oráculo) — veredicto BINARIO

| Escenario | L_cr | λ̄ | χ | N_b,Rd | u (build N=250) | u (QA FEM N=392) | Veredicto |
|---|---|---|---|---|---|---|---|
| **Arriostrado por planta** | **3,08 m** | 0,87 | 0,684 | **632 kN** | **0,40 ✔** | **0,62 ✔** | **CUMPLE** |
| **NO arriostrado** | 9,25 m | 2,60 | 0,130 | 120 kN | 2,08 ❌ | 3,26 ❌ | **NO CUMPLE** |

**Verificaciones sin oráculo:** equilibrio ΣF/ΣM ☑ · sólido rígido = 3 ☑ · conectividad nodal real ☑.

> **HALLAZGO PRINCIPAL DEL ENCARGO — longitud de pandeo real del montante.**
> Extraje los nudos reales del IFC: el montante (Z=5,75→15,0) **comparte nudo con los cordones en Z = 5,75 · 8,833 · 11,917 · 15,0**, es decir queda **dividido en 3 segmentos de ≈3,08 m**. En el FEM nodal, esos nudos de cordón (que a su vez reciben diagonales y diafragmas) **coaccionan lateralmente el montante**. Por tanto la **longitud de pandeo efectiva real es L_cr ≈ 3,08 m**, NO 9,25 m. **El supuesto S-B1 del build queda CONFIRMADO por la geometría/conectividad real**, no asumido.

## 3. Capa 2 — Normativa

| Comprobación | Límite | Valor QA | ¿Cumple? |
|---|---|---|---|
| Clasificación SHS 120×6 (S355) | Clase 1 | Clase 1 ((120−18)/6=17 ≤ 26,9) | ☑ |
| Pandeo (arriostrado, L_cr=3,08): u ≤ 1,0 | ≤ 1,0 | 0,40 (build) / **0,62 (QA con N_Ed real)** | ☑ |
| Pandeo (no arriostrado, L_cr=9,25): u ≤ 1,0 | ≤ 1,0 | 2,08 / 3,26 | ☒ |

## 4. Capa 3 — Regresión

- ¿Promovido a golden congelado? ☐ Sí ☑ **Pendiente de decisión de JM** sobre el arriostramiento (ver §6).

## 5. Observaciones / supuestos del build puestos a prueba

- **S-B1 (arriostramiento) — CONFIRMADO geométricamente.** Los nudos de cordón a Z=8,833 y 11,917 dividen el montante en segmentos de 3,08 m. En la celosía real estos nudos están triangulados por diagonales y cerrados por diafragmas, por lo que dan arriostramiento lateral efectivo. **L_cr=3,08 m es físicamente justificado.**
- **DISCREPANCIA de demanda relevante.** El build adopta N_Ed=250 kN (área tributaria). Mi **FEM nodal da el montante más comprimido a ≈392 kN** (+57 %). Aun así, con N_b,Rd=632 kN, **u=0,62 < 1,0 → sigue CUMPLIENDO**, pero el margen real es menor del que indica el build (0,62 vs 0,40). **Build debe revisar N_Ed del montante** (el reparto nodal carga más los montantes próximos a apoyos que la estimación tributaria).
- El veredicto NO depende ya de una hipótesis sin verificar: la conectividad real respalda el arriostramiento. La única reserva es que el **proyecto de detalle (uniones soldadas, conexión forjado-cordón-montante) materialice efectivamente esa coacción lateral** — eso es lo que JM debe confirmar en planos de taller.

## 6. Veredicto de QA

> **APTO (condicionado)** — Con el arriostramiento por planta CONFIRMADO por la geometría real (L_cr=3,08 m), el montante cumple: u=0,62 con la demanda nodal real (N_Ed≈392 kN) y 0,40 con la del build. **Condiciones para el cierre por JM:**
> 1. Confirmar en planos de detalle que las uniones cordón–montante–diagonal–forjado materializan la coacción lateral cada 3,08 m (la geometría lo soporta; falta el detalle constructivo).
> 2. **Devolución a build:** revisar N_Ed del montante (FEM nodal ≈392 kN > 250 kN del build); el aprovechamiento real es 0,62, no 0,40.
>
> Si el arriostramiento NO se materializase (L_cr=9,25 m): u≥2 → **NO APTO** y habría que rigidizar o aumentar el perfil. **El veredicto sigue siendo una decisión de proyecto de JM**, ahora respaldada por la conectividad real.

## 7. Firma (segunda llave — JM)

```
Verificado por QA:   agente QA / run 2026-06-24      fecha: 2026-06-24
Tolerancias fijadas por JM:  ☐
DECISIÓN JM sobre arriostramiento (planos de detalle):  ☐ arriostrado  ☐ no arriostrado
FIRMA JM (técnico competente): ______________  fecha: [   ]   → CERTIFICADO ☐
```

*Scripts QA: `qa/informes/qa_geom_extract.py` (nudos reales y conectividad del montante), `qa/informes/qa_truss2d_cajonO.py` (L_cr y N_Ed nodal), `qa/informes/qa_normativa.py` (EC3 ambos escenarios).*
