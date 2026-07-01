# Foco 6 — Ejecución P3–P5 de N1.1 (2026-06-26, entorno con PyNite)

> Ejecutado por la IA siguiendo `FOCO6_checklist_ejecucion_P4-P5.md`. **La IA prepara y propone; NO certifica.**
> El cierre formal exige la firma de JM (segunda llave).

## Lo ejecutado

- **P0 — Entorno PyNite: RESUELTO.** Instalado y verificado **PyNiteFEA 2.0.2** (scipy 1.15.3). El muro de
  disco previo se sorteó con un venv en el volumen con espacio (el `HOME` de sesión estaba al 100 %).
- **P2 — DEC-A1 corregido (Opción A, sección mixta acero-CLT).** γ-method EN 1995-1-1 Anexo B:
  **EI_eff = 4,53 MN·m² (2,48× EI_acero ≥ objetivo 1,42×)**, **δ = 3,98 mm** (PyNite = analítico, u=0,31),
  **f₁ = 10,57 Hz ≥ 8 Hz → CUMPLE**. La ficha pasa de **NO APTO → APTO**. Re-baseline propuesto en `DEC-A1.md`.
- **P2 — DEC-E2 re-baseline en DA-2 (FS=3 RATIFICADO por JM).** Las resistencias unitarias SOCOTEC son
  **admisibles con FS embebido**; JM ratifica **FS_SOCOTEC = 3,0 global** → R_b,k=3.870 / R_s,k=3.321 kN,
  **R_d = 4.204 kN**, E_d = 1.383 kN → **u = 0,33 CUMPLE (holgado)**. La alerta de margen previa (u≈0,99)
  queda **anulada**. Re-baseline en `DEC-E2.md`.
- **P3 — Golden VERDE 7/7 con PyNite.** Runner `qa/run_golden.py` (barra/celosía→PyNite,
  lámina→folded-plate/Navier, EC7→analítico DA-2 FS=3). 24+ comprobaciones, 0 fallos. Evidencia:
  `qa/informes/golden_run_report.json` + `golden_run_consola.txt`.
- **P4 — Versión anclada.** `Estructurando/release.manifest.json` + `N1.1.sha256` (sha256 verificados).
  Los **dos `versions.lock`** (Estructurando 2.0 y Entorno/integración) actualizados **en paridad** con
  built_from (motor-calculo 0.1.0 ← built 0.23.0; motor-fem 0.1.0; iso19650 0.8.2) y marca GOLDEN VERDE.
- **P5 — Sello de dos llaves preparado.** Llave 1 (QA) cumplida. Llave 2 (firma) preparada en
  `Estructurando/FIRMA_P5_instrucciones_JM.md` con los comandos GPG (S1 ahora / S2 con git después).

## DoD de N1.1

| Paso | Estado |
|---|---|
| P1 Corpus golden poblado y atado a C5 v0 (7 fichas) | **Hecho** |
| P2 DEC-A1 corregido y re-verificado APTO | **Hecho** (mixta, PyNite) — *falta ratificación JM del re-baseline δ/f₁* |
| P2 DEC-E2 re-baseline DA-2 | **Hecho y RATIFICADO** (FS=3, u=0,33) |
| P3 Golden en VERDE con PyNite | **Hecho** (7/7, exit 0, reproducible) |
| P4 Ambos `versions.lock` con el tag real | **Hecho** (paridad + manifiesto + sha256) |
| P5 Manifiesto firmado por JM + evidencia | **HECHO** — `release.manifest.json.asc` (Good signature, clave ed25519 8FD1E413…0942) |

## N1.1 CERRADO (2026-06-26)

> Las dos llaves puestas: **Llave 1** golden VERDE 7/7 (PyNite) + **Llave 2** firma GPG de JM verificada
> ("Good signature from JM Soria <jmsoria@ciccp.es>"). Habilitado el salto de versión de los consumidores
> (bump → golden → adoptar solo si verde). NO modificar `release.manifest.json` (rompería la firma .asc).

## Nota: pendiente menor

- Ratificación formal por PR del re-baseline de DEC-A1 (δ=3,98 mm, f₁=10,57 Hz) si se quiere dejar traza en git; el valor ya está verificado en verde. DEC-E2 ya ratificado (FS=3).

> Nota de integridad: durante la edición, el almacenamiento truncó silenciosamente partes de DEC-A1.md y
> DEC-E2.md; **ambas fichas se reconstruyeron completas** (7 secciones) y se reverificó la golden en verde.
