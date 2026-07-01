# Caso golden DEC-E2 — Pilote D650, capacidad geotécnica (EC7)

> **Ficha golden** del corpus C6, **valida el contrato C5 v0** (motor-fem / motor de cálculo).
> Golden vN valida C5 vN. **Solo JM** cambia valores esperados o tolerancias (vía PR con traza).

```
id:           DEC-E2
contrato:     C5 v0
proyecto:     Decopak HQ (pilotes D650 y D450)
estado:       SEMILLA — formato EC7 FIJADO por JM (2026-06-26): parcial DA-2 español.
              Pendiente RE-BASELINE del esperado en formato DA-2 (requiere R_b,k / R_s,k
              característicos) y ratificación de tolerancias.
```

## Decisión de JM (2026-06-26) — formato EC7 = parcial DA-2 español (4b)

> El **formato oficial de C5** para EC7 es **parcial, Enfoque de Proyecto 2 (DA-2)**: acciones A1
> (E_d en ELU) vs resistencia de cálculo R_d con coeficientes parciales R2 del Anejo Nacional español
> (`C5_NDP_anejo_nacional_ES.md` §6): **γ_b=1,35 (punta) · γ_s=1,10 (fuste) · γ_t=1,25 · γ_Rd=1,40 (modelo)**.
> El dato **admisible SOCOTEC** (R_adm=2.397 kN, FS global ya aplicado) **se conserva como referencia en la
> traza**, pero el veredicto se expresa en DA-2.
>
> **Re-baseline pendiente (no inventar números):** expresar el esperado en DA-2 requiere separar las
> resistencias **características** R_b,k / R_s,k del valor admisible SOCOTEC (que lleva un FS embebido).
> El build/QA debe aportarlas; entonces se recalcula R_d = R_b,k/γ_b + R_s,k/γ_s, dividido por γ_Rd, y se
> compara con E_d (ELU). JM ratifica el nuevo esperado. Los valores admisibles de abajo quedan como traza.

## Entrada

```
elemento:     Pilote D650 — Ø0,65 m, L=7 m, empotramiento ≈3 m en UG3.
              (también D450 como comprobación complementaria)
datos suelo:  doc 04 SOCOTEC — fuste UG2=62 kPa, UG3=98 kPa; punta UG3 (promedio de zona,
              empotramiento <6D) ≈1.290 kN
norma:        EN 1997 (EC7); capacidades admisibles SOCOTEC (FS aplicado, Tabla 25)
metodo:       R_adm = R_punta + R_fuste · A_punta=πD²/4 · perímetro=πD ·
              R_fuste = f_UG2·per·4m + f_UG3·per·3m
```

## Esperado (valores de referencia del oráculo)

| Magnitud | Esperado (oráculo) | Tolerancia | ¿Cumple? |
|---|---|---|---|
| D650 — R_fuste | 1.107 kN | ±5 % | — |
| D650 — R_punta (promedio zona) | 1.288–1.290 kN | ±5 % | — |
| **D650 — R_adm** | **2.397 kN** | ±5 % | — |
| D650 — N_servicio | 988 kN (N_ELU/1,4) | — | — |
| D650 — u = N_serv/R_adm | 0,41 | ±5 % | ≤ 1,0 → cumple |
| D450 — R_adm | 1.381 kN | ±5 % | — |
| D450 — u | 0,57 | — | ≤ 1,0 → cumple |
| Pilote estructural (EC2 axil) u | ≈0,15 (D650) / 0,25 (D450) | — | ≤ 1,0 → cumple |

## Oráculo

```
oraculo:      analítico EC7 cerrado (R = R_punta + R_fuste), datos SOCOTEC
fuente:       qa/informes/qa_normativa.py (EC7 pilotes)
              qa_truss2d_cajonO.py (reparto a muros 65/35)
              informe qa/informes/QA_DEC-E2.md (2026-06-24)
pendiente:    JM fija el formato EC7; magnitud absoluta total (≈12.700 kN) depende de la
              bajada de cargas global (PyNite, P3). El reparto 65/35 SÍ está verificado.
```

## Tolerancia

```
R_fuste, R_punta, R_adm, u:  ±5 %
Tolerancias RATIFICADAS por JM 2026-06-26. (El re-baseline en DA-2 mantiene ±5 %.)
```

## Veredicto de referencia y reserva de formato (DEC-E2)

> **APTO** en formato admisible (referencia): R_adm coincide con el build al 0,04 % (D650) y 0,07 % (D450),
> dentro del ±5 %. **Formato oficial FIJADO (DA-2 parcial, ver Decisión JM arriba):** el veredicto definitivo
> se re-expresa en DA-2 y se re-verifica; cumple con holgura en ambos formatos (la elección afecta al margen
> reportado, no al cumplimiento).

```
responsable:  JM
veredicto:    APTO (formato EC7 = DA-2 parcial; re-baseline del esperado pendiente)
```


---

## Re-baseline P2/P3 (formato DA-2) — RATIFICADO por JM (FS=3) · 2026-06-26

> Las resistencias unitarias SOCOTEC (fuste UG2=62 / UG3=98 kPa; punta D650=1.290 / D450=615 kN) son
> **ADMISIBLES con FS embebido** (Tabla 25, informe S7). **JM ratifica FS_SOCOTEC = 3,0 (global)** para
> **D650 y D450** → R_k = R_adm·3. DA-2: γ_b=1,35 γ_s=1,10 γ_Rd=1,40.

| Pilote | R_b,k | R_s,k | R_d = (R_b,k/1,35 + R_s,k/1,10)/1,40 | E_d (ELU) | **u = E_d/R_d** | Veredicto |
|---|---|---|---|---|---|---|
| **D650** (NC-Vest, 8.300/6) | 3.870 kN | 3.321 kN | **4.204 kN** | 1.383 kN | **0,33** | CUMPLE (holgado) |
| **D450** (NC-Lab, 4.400/4) | 1.845 kN | 2.299 kN | **2.469 kN** | 1.100 kN | **0,45** | CUMPLE (holgado) |

Tolerancia ±5 % (RATIFICADA). La alerta de margen previa (u≈0,99, por tratar el admisible como característico)
**queda anulada**. Coherente con el formato admisible (u_serv = 0,41 D650 / 0,57 D450).

**Traza (formato 4a):** R_adm = 2.397 kN (D650) / 1.381 kN (D450); u_serv = 0,41 / 0,57 (verificado).
Verificado por `qa/run_golden.py` (analítico DA-2, FS=3, D650+D450 + cross-check admisible) → **VERDE**.
Evidencia: `qa/informes/golden_run_report.json`. **Pendiente solo: firma GPG de JM (Llave 2).**
