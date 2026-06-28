# golden/ — corpus golden (C6) del primer corte N1.1

> **Qué es:** los casos patrón que dan el *blanco a validar* del núcleo. Cada ficha registra
> entrada · esperado · oráculo · tolerancia · responsable, y queda atada a la versión de contrato
> que valida (**golden vN valida CN vN**). Sembrado a partir de la QA de Decopak HQ (2026-06-24).
>
> **Regla rectora:** un fallo de QA **no** se resuelve aflojando tolerancia ni editando el valor
> esperado — solo arreglando el código. **Solo JM** cambia valores golden o tolerancias, vía PR con traza.

> ✅ **Tolerancias de las 7 fichas y NDP RATIFICADOS por JM (2026-06-26).** Masa de DEC-A1 fijada en 450 kg/m;
> α_cc=1,0. Queda pendiente solo lo de ejecución: corregir DEC-A1 (Opción A), re-baseline de DEC-E2 en DA-2,
> y la golden verde con PyNite (P3) para congelar.

## Estado del corpus — ✅ CERTIFICADO (dos llaves, 2026-06-26)

> 🟢 **P3 EJECUTADO 2026-06-26 (entorno con PyNite 2.0.2): suite golden VERDE 7/7.** DEC-A1 corregido (Opción A mixta) APTO y DEC-E2 re-baseline DA-2 con FS=3 ratificado por JM (u=0,33, holgado; alerta previa anulada). Oráculos: barra/celosía→PyNite, lámina→folded-plate/Navier, EC7→analítico DA-2. Evidencia: `../../qa/informes/golden_run_report.json` y `golden_run_consola.txt`. **Llave 1 (QA) lista; ✅ Llave 2 CERRADA — firma GPG de JM (EDDSA 8FD1…E0942, 2026-06-26 12:53 UTC) sobre `release.manifest.json`; re-baseline (DEC-A1 Opción A, DEC-E2 DA-2) ratificados.**

Estas fichas se sembraron como **SEMILLA redactada por la IA** (valores de oráculo y tolerancias propuestas en QA). **✅ Ahora CERTIFICADAS (dos llaves) el 2026-06-26.** Los tres pasos que faltaban para el cierre de N1.1, ya resueltos:

1. ✅ **Ratificación de JM** (segunda llave) — firma GPG sobre `release.manifest.json` (EDDSA `8FD1…E0942`, 2026-06-26 12:53 UTC); re-baseline DEC-A1 (Opción A) y DEC-E2 (DA-2) ratificados.
2. ✅ **Re-ejecución con PyNite** (P3) — suite VERDE 7/7 con PyNite 2.0.2 (ver el 🟢 de arriba).
3. ✅ **Versión anclada** (P4) — fijada en el manifiesto firmado (motor-fem 0.1.0; motor-calculo build 0.23.0 → tag 0.1.0).

> *Reconciliación transcrita por la IA el 2026-06-26 como reflejo de la firma de JM (que vive en `Estructurando/release.manifest.json.asc`). La IA transcribe, no certifica. **El manifiesto firmado no se edita** — su texto interno conserva el placeholder pre-firma; el `.asc` es la prueba de la Llave 2.*

## Las 7 fichas (todas atadas a C5 v0)

| Ficha | Elemento | Magnitud clave | Veredicto de referencia |
|---|---|---|---|
| [DEC-A1](DEC-A1.md) | Costilla IPE 160 + CLT mixta | δ flecha · f₁ vibración | **APTO** (mixta: f₁=10,57 Hz, δ=3,98 mm; PyNite) |
| [DEC-B1](DEC-B1.md) | Diagonal SHS 200×10 | N_b,Rd pandeo | APTO (cond.: identificar perfil crítico real) |
| [DEC-B2](DEC-B2.md) | Cordón SHS 180×8 | N_b,Rd compr.+pandeo | APTO |
| [DEC-B4](DEC-B4.md) | Montante SHS 120×6 | L_cr=3,08 m · N_b,Rd | APTO (cond.: arriostramiento, decisión JM) |
| [DEC-E1](DEC-E1.md) | Encepados bielas-tir. | T tirante (Lab/Vest) | APTO |
| [DEC-E2](DEC-E2.md) | Pilote D650 (EC7) | R_d (DA-2) | **APTO** (DA-2 FS=3 ratificado, u=0,33) |
| [DEC-S1](DEC-S1.md) | Cubierta cajón (lámina) | M vano/esquina · cierre nudo | APTO con observaciones (lámina; gates JM) |

Resumen ejecutivo de la QA: `../../qa/informes/QA_RESUMEN.md`. Informe por caso: `../../qa/informes/QA_DEC-*.md`.

## Nota de contrato C5 (hueco a cerrar)

El esquema de contratos del ecosistema reserva **C5 = motor-fem** (ver `../contratos/C8_intercambio_CDE.md`
§nota de numeración: «C1 parser/IFC · C4 red · C5 motor-fem · C6 corpus golden · C7 operador IA · C8 CDE»).
Estas 6 fichas validan **C5 v0**. El documento de contrato ya existe en **borrador**:
`contratos/C5_motor-fem.md` (v0.1.0 DRAFT, 2026-06-26) — define l