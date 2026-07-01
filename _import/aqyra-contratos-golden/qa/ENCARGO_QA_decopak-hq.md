# Encargo de QA — Decopak HQ (verificación del cálculo estructural)

- **Para:** agente de QA independiente (ejecución separada, oráculo propio).
- **De:** rol build (producción). Este encargo y la evidencia los prepara build; **build no verifica ni firma**.
- **Fecha:** 2026-06-24 · **Estado del objeto a verificar:** PROPUESTA de predimensionado (docs `pilotos/decopak-hq/calculo/05–10`).

> **Regla de oro (Gobierno §B):** quien produce no aprueba. Corre en **ejecución separada**, con tu **propio oráculo**, sin ver ni reutilizar los solvers del build. Un fallo **no** se arregla aflojando tolerancia ni editando el valor esperado — solo arreglando el código/cálculo. **Tú emites el Informe de QA; JM firma.** La IA no certifica.

---

## 1. Por qué este encargo y dónde se ejecuta

El predimensionado del build se hizo por **fórmulas cerradas EC + parser STEP en numpy puro**, porque el sandbox de build **no puede instalar el motor FEM** (PyNite/ifcopenshell/scipy: `pip` > 45 s, disco lleno). Por eso el **análisis FEM nodal real es justamente el trabajo de QA**, y debe correr en un **entorno con dependencias instaladas** (ver `qa/setup_entorno_qa.md` y `qa/requirements.txt`). El build aporta los **valores a verificar** y propone **tolerancias**; QA los recalcula con su oráculo independiente.

## 2. Alcance

Verificar los **6 casos golden candidatos** (`pilotos/decopak-hq/calculo/08_candidatos_golden.md`) que cubren el camino de cargas completo (CLT → celosías de acero → muros → cimentación → sismo), aplicando las **tres capas** del Gobierno §B.2:

1. **Numérica (oráculo).** Recalcular cada caso contra una referencia **independiente del cálculo del build** (jerarquía §B.3: analítico cerrado → 2.º código FEM → MMS; **PyNite por defecto** para barras/celosías). Veredicto por tolerancia.
2. **Normativa.** Comprobador de reglas separado: clasificación de sección, pandeo, aprovechamiento ≤ 1, cuantías, flechas, fisuración, capacidad geotécnica (EC0/EC1/EC2/EC3/EC5/EC7, AN español).
3. **Regresión.** Los casos que JM apruebe como golden se congelan y corren en CI (`contratos-golden/golden/`).

## 3. Entradas (todo en el repo)

| Recurso | Ruta |
|---|---|
| Modelo IFC (semilla) | `pilotos/decopak-hq/modelo/DEC-PB-EBAN-HQ-Y-BIM-EST-02-EstructuraNucleoLateral-S1-v0.0.ifc` |
| Hipótesis de acciones (APROBADAS) | `pilotos/decopak-hq/calculo/02_bases_acciones_HIPOTESIS.md` |
| Síntesis geotécnica | `pilotos/decopak-hq/calculo/04_geotecnia_sintesis.md` |
| Resultados build a verificar | `pilotos/decopak-hq/calculo/05_…CLT`, `06_…acero`, `07_…hormigon_cimentacion_sismo` |
| Fichas golden (oráculo + tolerancia propuestos) | `pilotos/decopak-hq/calculo/08_candidatos_golden.md` |
| Motor de cálculo (FEM + EC) | plugin `motor-calculo-estructural` (`scripts/run_all_edificio.py`, `barras/`, `laminas/`, `cimentaciones/`, `bielas-tirantes/`, `pilotes/`) |

## 4. Protocolo por caso golden

Para cada caso: (1) **idealiza desde el IFC con los nudos reales** (no áreas tributarias); (2) **resuelve con tu oráculo**; (3) compara con el **valor build** dentro de la **tolerancia**; (4) ejecuta la **capa normativa**; (5) emite **APTO / NO APTO** con traza. Procede el caso solo si las dos primeras capas dan verde.

| Caso | Elemento | Oráculo a usar (independiente) | Valor build a verificar | Tolerancia propuesta |
|---|---|---|---|---|
| **DEC-A1** | Costilla CLT IPE 160 (flexión + vibración) | Analítico cerrado (M=wL²/8, δ=5wL⁴/384EI, f₁) + EC5 §7.3 | u_M=0,39; δ=2,6 mm; f₁=8,5 Hz (u_vib≈0,94) | ±2 % M y δ; **±5 % f₁** |
| **DEC-B1** | Diagonal Cajón O SHS 200×10 (pandeo) | **PyNite** (celosía articulada con nudos reales) + EC3 6.3.1 (χ curva b) | N_Ed=778 kN; N_b,Rd=2.004 kN; u=0,39 | ±3 % N_b,Rd; ±5 % N_Ed |
| **DEC-B2** | Cordón Cajón O SHS 180×8 (flexo-axil) | **PyNite** (nudos reales) + EC3 6.2/6.3 | N_Ed=409 kN; N_b,Rd=1.600 kN; u=0,26 | ±5 % |
| **DEC-B4** | Montante Cajón O SHS 120×6 (**arriostramiento**) | EC3 6.3.1 con **L_cr=3,08 m vs 9,25 m** | arriostrado u=0,40 ✔ / no arriostrado u=2,1 ❌ | **binaria** (según hipótesis de arriostramiento) |
| **DEC-E1** | Encepado bielas y tirantes (EC2 §6.5) | Analítico (modelo de bielas) + EC2 §6.5 | NC-Lab T=809 kN, u_CCT=0,46; NC-Vest T=864 kN | ±3 % T/C; As a Ø comercial |
| **DEC-E2** | Pilote D650 (EC7) | Analítico EC7 (R_punta+R_fuste, SOCOTEC) | R_adm≈2.396 kN; N_serv=988 kN; u=0,41 | ±5 % (promedio de zona <6D) |

> **DEC-B4 es el punto crítico.** El cálculo del montante **cambia de seguro a inseguro** según esté o no arriostrado a pandeo por planta. QA debe (a) reproducir ambos escenarios y (b) **señalar que el veredicto depende de un dato de proyecto** (arriostramiento real) que JM/proyecto debe confirmar. No lo des por bueno por defecto.

### Verificaciones transversales sin oráculo (Gobierno §B.3)
Donde uses FEM (DEC-B1/B2 y la celosía global), añade: **equilibrio global** (ΣF, ΣM = reacciones), **modos de sólido rígido**, y un **estudio de convergencia** si mallas la celosía como continuo. Para la lámina del forjado/losa, si la abordas, **patch test** y comparación NAFEMS donde aplique.

## 5. Cosas que QA debe poner especialmente a prueba (supuestos del build)

El build avisa de estos supuestos; son los candidatos a que el FEM real desmienta:
- **S-A2** — la costilla se modeló como **nervio biapoyado (≈3,86 m)**, no como ménsula de 6,55 m (que daba u=4,5). Verifica con la geometría/conectividad real qué luz toma realmente la costilla y qué toma la celosía.
- **S-B1** — **montantes arriostrados por planta**. Resolución nodal real: ¿la longitud de pandeo efectiva es 3,08 m?
- **S-D1** — reparto de carga vertical Vest/Lab 65/35 por área; QA debe obtener las **reacciones reales** del modelo global sobre cada muro/encepado.
- **S-F1** — sismo por **estático equivalente**; falta modal con torsión por irregularidad (voladizos). Verifica si el modo fundamental y la torsión cambian algo (con ac=0,046 g se espera que no gobierne).
- **Camino de cargas por áreas tributarias** (no nodal): pueden aparecer **picos locales** en barras concretas que solo el FEM nodal captura.

## 6. Versión y reproducibilidad

`versions.lock` está en **0.0.0** (núcleo sin primer tag, N1.1). Registra en cada informe la **versión/commit real** del motor y plugins que uses. Hasta anclar, marca el resultado de QA como **«verificado sobre versión no anclada»**.

## 7. Salida que debe producir QA

- Un **Informe de QA por cálculo** por caso golden, en `qa/informes/` (plantilla `qa/informes/PLANTILLA_informe_QA.md`), con la traza `input → versión → norma → resultado → oráculo → comparación → veredicto APTO/NO APTO`.
- Un **índice/resumen** de los 6 casos con su veredicto.
- Para los casos verdes que JM apruebe: la **ficha golden congelada** propuesta a `contratos-golden/golden/` (entrada · salida esperada · oráculo · tolerancia · responsable JM).
- **No firma:** el informe queda **a la espera de la firma de JM** (segunda llave). Certificado = golden verde + informe limpio + firma JM.

---
**Procedencia:** encargo preparado por build (PM/estructurista) el 2026-06-24 para lanzar la verificación independiente del cálculo de Decopak HQ. Las tolerancias son **propuestas**; las fija JM (Gobierno §B.5).
