# Memoria de obra lineal — Trazado (caso-LIN-02)

> Predimensionado/asistencia. **Debe ser revisado y firmado por técnico competente
> (Ingeniero de Caminos).** NDP marcados **[confirmar AN]**.

## 1. Datos del proyecto

- Eje: **Eje C-001** (Carretera C-001), modelo neutro lineal IFC 4.3 (`IfcAlignment`),
  longitud 400 m (PK 0+000 a 0+400), georreferenciado EPSG:25830 (ETRS89/UTM 30N).
- Geometría en planta: recta (100 m) · clotoide (A=134,2) · curva circular (R=300 m,
  80 m) · clotoide (A=134,2) · recta (100 m).
- Alzado: rampa 2 % · acuerdo convexo parabólico Kv=2000 (L=100 m) · pendiente −3 %.
- Peralte: transición 0 → 7 % en las clotoides, 7 % en la curva.

## 2. Normativa

- **Norma 3.1-IC, Trazado** (Orden FOM/273/2016) — radios, clotoides, acuerdos
  verticales, pendientes y visibilidad. [confirmar AN] edición vigente y grupo de
  carretera.
- Lectura/coherencia geométrica del IFC: `iso19650-openbim` v0.5.0 (PT 5.1).

## 3. Datos de proyecto / acciones (C4)

- **Velocidad de proyecto Vp = 60 km/h** (dato de proyecto; el del IFC prevalece, si no
  se inyecta). [confirmar AN].

## 4. Comprobaciones (3.1-IC) para Vp = 60 km/h

Umbrales: radio mínimo **130 m**; pendiente máxima **6 %**; distancia de parada Dp
**69,7 m**; Kv mínimo convexo **1085 m**; cóncavo **1414 m**.

| Elemento | Magnitud | Valor | Umbral | Veredicto |
|---|---|---|---|---|
| Curva PK 160 | radio R | 300 m | ≥ 130 m | CUMPLE |
| Clotoides PK 100 / 240 | parámetro A | 134,2 | [100, 300] | CUMPLE |
| Clotoides PK 100 / 240 | longitud (confort) | 60 m | ≥ 30,9 m | CUMPLE |
| Acuerdo convexo PK 150 | Kv | 2000 m | ≥ 1085 m | CUMPLE |
| Rasantes | pendiente | ≤ 3 % | ≤ 6 % | CUMPLE |

**Aviso (informativo, cap.7):** el acuerdo vertical PK 150–250 queda próximo a la
transición en planta del PK 240 — revisar guiado óptico (coordinación planta-alzado).

**Veredicto global: CUMPLE** (12/12 comprobaciones).

> Sensibilidad: a **Vp = 100 km/h** el trazado **NO CUMPLE** (R 300 < 450; clotoides
> cortas por confort; Kv 2000 < 7125). La Vp es el parámetro gobernante.

## 5. Registro fechado

- **2026-06-22** — Trazado 3.1-IC, eje C-001, Vp 60 → **CUMPLE** (run_all_trazado).
  Herramienta: `obras-lineales` v0.1.0, `scripts/trazado`.

## 6. Conclusiones

El trazado del eje C-001 cumple la 3.1-IC para Vp = 60 km/h. Para velocidades de
proyecto superiores (≥ 80–100 km/h) deberían aumentarse el radio en planta, la longitud
de las clotoides y el parámetro Kv del acuerdo convexo. Predimensionado a revisar y
firmar por técnico competente (ICCP).
