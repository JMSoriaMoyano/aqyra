# Memoria de obra lineal — Firmes (caso-LIN-03)

> Predimensionado/asistencia. **Debe ser revisado y firmado por técnico competente
> (Ingeniero de Caminos).** NDP marcados **[confirmar AN]**.

## 1. Datos del proyecto

- Eje: **Eje C-001** (Carretera C-001), modelo neutro lineal IFC 4.3, 400 m,
  georreferenciado EPSG:25830. Calzada única (carretera convencional, 2 carriles).

## 2. Normativa

- **Norma 6.1-IC, Secciones de firme** — categoría de tráfico pesado, categoría de
  explanada y catálogo de secciones. [confirmar AN] edición vigente.
- Write-back/validación IFC: `iso19650-openbim` v0.5.0.

## 3. Datos de proyecto / acciones (C4 — acción del tráfico)

- IMD total **8000 veh/día**; pesados **12 %**; calzada única (reparto 50 % por
  sentido) → **IMDp ≈ 480** vehículos pesados/día en el carril de proyecto. [confirmar AN].
- Explanada: módulo **Ev2 = 150 MPa**. [confirmar AN] según formación de explanada.

## 4. Comprobaciones (6.1-IC)

- Categoría de tráfico pesado: **T2** (IMDp 200–799).
- Categoría de explanada: **E2** (Ev2 ≥ 120 MPa).
- Combinación T2 × E2: **permitida**.
- Sección del catálogo: **221** (firme flexible).

| Capa | Material | Espesor |
|---|---|---|
| Rodadura/intermedia/base bituminosa | Mezcla bituminosa (MB) | 18 cm |
| Subbase | Zahorra artificial (ZA) | 30 cm |
| **Total** | | **48 cm** |

- Espesor de MB 18 cm ≥ mínimo de la categoría (18 cm). **CUMPLE**.
- Ganchos del modelo neutro rellenos: `firme` (sección 221) y `secciones_tipo`
  (plataforma básica: calzada 7,0 m, arcenes 1,5/0,5 m; peralte máx 7 %). `terreno`
  queda en `None` (Ola 6).

## 5. Registro fechado

- **2026-06-22** — Firmes 6.1-IC, eje C-001: IMDp 480 → T2, Ev2 150 → E2, sección **221**
  (MB 18 + ZA 30, 48 cm) → **CUMPLE**. Write-back `Pset_Estructurando_ResultadoLineal`
  (9 props) + GeoJSON. Herramienta: `obras-lineales` v0.1.0, `scripts/firmes`.

## 6. Conclusiones

Para el tráfico T2 y la explanada E2 del eje C-001 procede la sección de firme **221**
del catálogo 6.1-IC (MB 18 cm sobre ZA 30 cm). La sección se ha volcado al modelo neutro
lineal y al IFC. Predimensionado por catálogo (no dimensionado por fatiga) a revisar y
firmar por técnico competente (ICCP).
