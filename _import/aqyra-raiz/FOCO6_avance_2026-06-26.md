# Foco 6 — Avance del hilo de cierre N1.1 (2026-06-26)

> Ejecutado en este hilo por la IA (prepara y propone; **no certifica**). Para ratificación de JM.

## Lo hecho

- **P0 — Entorno PyNite: NO instalable aquí.** El volumen de sesión está al 100 % (0 B libres) y el
  del sistema con ~700 MB; `pip install PyNiteFEA` descarga pero falla al instalar scipy por falta de
  disco — el mismo muro que la QA previa. **P3 (re-ejecución con PyNite) sigue esperando** a un entorno apto.
  P1 y P2 han avanzado igualmente, como prevé la hoja de ruta.

- **P1 — Corpus golden sembrado.** Creadas las 6 fichas formales en
  `Estructurando 2.0/contratos-golden/golden/`, atadas a **C5 v0**, con el formato del README
  (id · entrada · esperado · oráculo · tolerancia · responsable):
  `DEC-A1, DEC-B1, DEC-B2, DEC-B4, DEC-E1, DEC-E2` + `README.md` (índice). Los valores son los del
  oráculo de los informes QA (verificada la consistencia ficha↔informe). El corpus ya **no está vacío**:
  hay un blanco que validar (semilla, pendiente de tu ratificación).

- **P2 — DEC-A1 recalculado** en `golden/DEC-A1_recalculo_P2.md`:
  - Flecha: el valor correcto es **9,87 mm** (el build escribió 2,6; error ×3,8). El correcto **cumple** L/300.
  - Vibración: **f₁ = 7,66 Hz** (masa build) / **6,71 Hz** (masa realista) → **< 8 Hz, NO CUMPLE** EC5 §7.3.
  - Es defecto de **diseño**, no solo de número. Opciones cuantificadas: **(A) mixta acero-CLT** (basta EI≥1,42×, sobra),
    **(B) subir perfil** (IPE 180→8,26 Hz justo; **IPE 200→10,0 Hz** holgado), **(C) reducir luz/apoyo intermedio**,
    **(D) justificar por respuesta** EC5 §7.3.3. Recomendación IA: A o B(IPE 200). **Decisión tuya.**

## Estado del DoD de N1.1

| Paso | Estado |
|---|---|
| P1 Corpus golden poblado y atado a C5 v0 | **Hecho (semilla)** — falta tu ratificación de valores/tolerancias |
| P2 DEC-A1 corregido y re-verificado APTO | **Recálculo y opciones listos** — falta tu decisión de modelo + corregir build + re-verificar |
| P3 Golden en verde con PyNite | **Bloqueado** por entorno (disco lleno) |
| P4 `versions.lock` con el tag real que pasa la golden | Pendiente (hoy ambos anclan motor-fem 0.1.0) |
| P5 Tag GPG firmado por JM + evidencia | Pendiente (tu firma) |

## Decisiones que solo cierras tú (JM)

1. **DEC-A1** — ~~elegir el modelo para f₁ ≥ 8 Hz~~ **RESUELTO 2026-06-26: Opción A (sección mixta acero-CLT).**
   Pendiente: el build implementa la sección mixta (objetivo EI_eff ≥ 1,42×, f₁ ≥ 8 Hz con m≈450) y se re-verifica con PyNite (P3).
2. **DEC-A1** — ratificar la masa de cálculo (build 346 vs realista ≈450 kg/m); afecta a f₁.
3. **DEC-B4** — confirmar en planos la coacción lateral del montante cada 3,08 m (si no → NO APTO).
4. **DEC-B1** — identificar el perfil real de la diagonal crítica (el IFC tiene 7 perfiles).
5. **DEC-E2** — ~~fijar el formato EC7~~ **RESUELTO: parcial DA-2 español (4b)**; re-baseline del esperado pendiente de R_b,k/R_s,k.
6. ~~Ratificar valores y tolerancias~~ **RATIFICADO JM 2026-06-26:** tolerancias de las 7 fichas + tabla NDP (α_cc=1,0) + masa DEC-A1=450 kg/m.
7. **Contrato C5** — borrador + **puntos abiertos 1–6 cerrados** (schemas JSON canónicos, Psets de resultado, alcance lámina, EC7 DA-2, sismo diferido, NDP). Pendiente: tu firma para elevarlo a C5 v0 ratificado.
8. **Política de versión y firma + mapeo build↔release** — **PREPARADO** (`Estructurando 2.0/POLITICA_VERSION_Y_FIRMA_N1.1.md`).
   Recomendaciones a ratificar: M1 (espacios separados + manifiesto), 0.x pre-estable, firma GPG sobre manifiesto (S1) ahora / tag git (S2) después, montar monorepo git. Clave: `motor-calculo 0.1.0` se corta en P4 del build que pase la golden, no hoy.

## Estado del contrato C5 (2026-06-26)

Borrador `contratos/C5_motor-fem.md` con los **6 puntos abiertos cerrados**:
schemas canónicos (`schemas/C5_*.schema.json`), Psets de resultado (`C5_psets_resultado.md`), alcance lámina
(golden **DEC-S1**), EC7 **DA-2** parcial, sismo **diferido** (5a), y **NDP español** tabulados
(`C5_NDP_anejo_nacional_ES.md`). La suite golden pasa de 6 a **7 fichas**.

## Siguiente paso sugerido

Para congelar la golden y dejar C5 firmable faltan acciones de ejecución, no de diseño:
(a) **ratificar la tabla de NDP** y las 7 fichas; (b) **re-baseline de DEC-E2** en DA-2 (aportar R_b,k/R_s,k);
(c) corregir **DEC-A1** (Opción A) en el build; (d) **P3** con PyNite (pendiente de entorno).
Reencuadre del hilo: `N1.1_es_el_piloto_del_gobierno.md`.
