# Informe de QA por cálculo — DEC-E2

> **QA verificado con FEM nodal numpy independiente + analítico. SIN el oráculo PyNite certificado (no instalable en este entorno) → pendiente de RE-EJECUCIÓN en entorno con PyNite para el cierre definitivo. Pendiente de firma de JM (la IA no certifica).**

- **Caso golden:** DEC-E2 — Pilote D650 (capacidad EC7)
- **Contrato / golden:** C-E2 v0
- **Fecha de verificación:** 2026-06-24
- **Ejecutado por:** agente de QA (ejecución separada) · **Oráculo:** analítico EC7 (R = R_punta + R_fuste)
- **Versión verificada:** **NO ANCLADA**

> La certificación requiere la firma de JM. La IA no firma.

---

## 1. Trazabilidad

```
input:       IFC pilote D650 (Ø0,65, L=7 m, empotramiento ≈3 m en UG3); doc 04 SOCOTEC:
             fuste UG2=62 kPa, UG3=98 kPa; punta UG3 (promedio de zona, <6D) ≈1.290 kN
version:     no anclada
norma:       EN 1997 (EC7), capacidades admisibles SOCOTEC (FS aplicado, Tabla 25)
metodo QA:   R_adm = R_punta + R_fuste; A_punta=πD²/4; perímetro=πD;
             R_fuste = f_UG2·per·4m + f_UG3·per·3m
resultado:   D650 R_adm=2.397 kN (con punta promedio de zona); D450 R_adm=1.381 kN
oraculo:     analítico EC7 cerrado, datos SOCOTEC
comparacion: ver §2
```

## 2. Capa 1 — Numérica (oráculo)

| Magnitud | Valor build | Valor QA (oráculo) | Δ | Tolerancia | ¿Dentro? |
|---|---|---|---|---|---|
| D650 R_fuste | 1.106 kN | 1.107 kN | +0,1 % | ±5 % | ☑ |
| D650 R_punta (promedio zona) | 1.290 kN | 1.288–1.290 kN | ≈0 % | ±5 % | ☑ |
| **D650 R_adm** | **2.396 kN** | **2.397 kN** | +0,04 % | ±5 % | ☑ |
| D650 N_servicio | 988 kN | 988 kN (N_ELU/1,4) | 0 % | — | ☑ |
| D650 u = N_serv/R_adm | 0,41 | 0,41 | 0 % | ±5 % | ☑ |
| D450 R_adm | 1.380 kN | 1.381 kN | +0,07 % | ±5 % | ☑ |
| D450 u | 0,57 | 0,57 | 0 % | — | ☑ |

**Verificaciones sin oráculo:** consistencia de áreas y perímetros con D del IFC ☑ · empotramiento <6D tratado con promedio de zona (criterio SOCOTEC) ☑.

## 3. Capa 2 — Normativa

| Comprobación | Límite | Valor QA | ¿Cumple? |
|---|---|---|---|
| Capacidad geotécnica u = N/R_adm ≤ 1,0 | ≤ 1,0 | 0,41 (D650) / 0,57 (D450) | ☑ |
| Pilote estructural (EC2 axil) u | ≤ 1,0 | ≈0,15 (D650) / 0,25 (D450) | ☑ |

## 4. Capa 3 — Regresión

- ¿Promovido a golden congelado? ☐ Sí ☑ Pendiente firma JM (verde, con la reserva de formato §5).

## 5. Observaciones / supuestos del build puestos a prueba

- **Formato EC7 (admisible vs parcial):** el build trabaja con **capacidades admisibles SOCOTEC (FS ya aplicado)** y las compara con **cargas de servicio** (N_ELU/1,4). Es coherente, pero **mezcla formatos**: lo riguroso en EC7 sería R_d con γ_R parciales y E_d en ELU. El resultado en formato admisible cuadra al 0,04 %; **JM debe fijar el formato** (admisible o parcial) — afecta al margen reportado pero no a que el pilote cumple con holgura.
- **Reparto del núcleo (S-D1):** el N_servicio=988 kN/pilote sale de N_Ed,Vest=8.300 kN ÷ 6 ÷ 1,4. Mi FEM nodal del Cajón O **confirma el reparto 65 % NC-Vest / 35 % NC-Lab** (reacciones reales sobre los muros), validando la base del reparto. La magnitud absoluta total (12.700 kN) depende de la bajada de cargas global (pendiente PyNite).
- **Empotramiento <6D:** para D650, 6D=3,9 m > los ≈3,0 m disponibles en UG3; el uso del **promedio de zona** para la punta (1.290 kN en vez de 1.288 kN nominal) es correcto y conservador.

## 6. Veredicto de QA

> **APTO** — R_adm coincide con el build al 0,04 % (D650) y 0,07 % (D450), muy dentro del ±5 %; u=0,41/0,57. Reserva: **JM debe fijar el formato EC7** (admisible SOCOTEC vs parcial con γ_R) para el cierre; el reparto 65/35 está verificado por el FEM nodal.

## 7. Firma (segunda llave — JM)

```
Verificado por QA:   agente QA / run 2026-06-24      fecha: 2026-06-24
Tolerancias fijadas por JM:  ☐
Formato EC7 fijado por JM (admisible / parcial):  ☐
FIRMA JM (técnico competente): ______________  fecha: [   ]   → CERTIFICADO ☐
```

*Scripts QA: `qa/informes/qa_normativa.py` (EC7 pilotes), `qa/informes/qa_truss2d_cajonO.py` (reacciones a muros).*
