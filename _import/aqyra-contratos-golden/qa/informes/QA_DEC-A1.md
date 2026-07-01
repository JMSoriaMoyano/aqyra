# Informe de QA por cálculo — DEC-A1

> **QA verificado con FEM nodal numpy independiente + analítico. SIN el oráculo PyNite certificado (no instalable en este entorno) → pendiente de RE-EJECUCIÓN en entorno con PyNite para el cierre definitivo. Pendiente de firma de JM (la IA no certifica).**

- **Caso golden:** DEC-A1 — Costilla cassette IPE 160 (flexión + vibración) + tablero CLT
- **Contrato / golden:** C-A1 v0 (golden v0 valida contrato v0)
- **Fecha de verificación:** 2026-06-24
- **Ejecutado por:** agente de QA (ejecución separada del build) · **Oráculo:** analítico cerrado (M, δ, f₁) + EC5 §7.3
- **Versión verificada:** motor/plugins — **versión NO ANCLADA** (versions.lock=0.0.0)

> QA prepara la evidencia y emite el veredicto técnico. **La certificación requiere la firma de JM** (segunda llave). La IA no firma.

---

## 1. Trazabilidad

```
input:       IFC #1857 (IPE 160; b=82,h=160,tw=5,tf=7,4 mm); nervio biapoyado L=3,86 m;
             w_d=8,80 kN/m (1,35·3,63+1,50·2,60); w_k=6,23 kN/m; w_cuasi=4,41 kN/m
version:     no anclada
norma:       EC3 6.2.5 (nervio acero); EC5 7.3 (vibración); EC0 7.4 (flecha); EC0/EC1 (acciones doc 02)
metodo QA:   fórmulas cerradas derivadas independientemente (numpy), IPE160 de catálogo
resultado:   u_M=0,39; δ=9,87 mm; f₁=6,7–7,7 Hz
oraculo:     viga biapoyada M=wL²/8, δ=5wL⁴/384EI, f₁=(π/2)√(EI/mL⁴)
comparacion: ver tabla §2
```

## 2. Capa 1 — Numérica (oráculo)

| Magnitud | Valor build | Valor QA (oráculo) | Δ | Tolerancia | ¿Dentro? |
|---|---|---|---|---|---|
| M_Ed (flexión) | 16,4 kN·m | 16,4 kN·m | 0 % | ±2 % | ☑ |
| u_M | 0,39 | 0,39 | 0 % | ±2 % | ☑ |
| δ (flecha ELS car.) | **2,6 mm** | **9,87 mm** | **+280 %** | ±2 % | ☒ |
| f₁ (frecuencia propia) | **8,5 Hz** | **6,7 Hz** (m=450) / **7,7 Hz** (m=346 del build) | **−21 % / −10 %** | ±5 % | ☒ |

**Verificaciones sin oráculo:** equilibrio ΣF/ΣM ☑ (viga biapoyada, trivial) · sólido rígido n/a · convergencia n/a · patch test n/a.

> **Hallazgo numérico (errores de aritmética del build):**
> 1. **Flecha.** La expresión que el propio build escribe — `δ = 5·6,23e3·3,86⁴/(384·210e9·8,69e-6)` — vale **9,87 mm**, no 2,6 mm. El build evaluó mal su propia fórmula (×3,8). La flecha correcta (9,87 mm) **sí cumple** L/300=12,9 mm (u=0,77), pero el **valor a verificar es erróneo**.
> 2. **Frecuencia.** Con la masa del propio build (346 kg/m) la fórmula da **7,66 Hz**, no 8,5 Hz. Con la masa cuasipermanente realista (≈450 kg/m, incluye CLT + carga muerta) da **6,7 Hz**. **En ambos casos f₁ < 8 Hz → NO cumple el criterio EC5 §7.3**, que es el ELS gobernante del caso.

## 3. Capa 2 — Normativa

| Comprobación | Límite | Valor QA | ¿Cumple? |
|---|---|---|---|
| Clasificación de sección IPE 160 (S355) | Clase 1 | Clase 1 | ☑ |
| Aprovechamiento flexión u_M ≤ 1,0 | ≤ 1,0 | 0,39 | ☑ |
| Flecha δ ≤ L/300 | 12,9 mm | 9,87 mm (u=0,77) | ☑ (cumple, pero valor build erróneo) |
| Vibración f₁ ≥ 8 Hz (EC5 §7.3) | ≥ 8 Hz | **6,7–7,7 Hz** | ☒ **NO CUMPLE** |

## 4. Capa 3 — Regresión

- ¿Promovido a golden congelado? ☐ Sí ☑ **No** (no procede: dos magnitudes fuera de tolerancia).
- ¿Corre en CI sin desviación? ☐

## 5. Observaciones / supuestos del build puestos a prueba

- **S-A2 (luz real de la costilla):** la geometría del IFC confirma costillas de extrusión 6,21–6,55 m; el modelo de **ménsula aislada de 6,55 m daba u_M=4,5 (no resiste)**, descartado correctamente por el build. El **nervio biapoyado L=3,86 m** entre dinteles de conexión es coherente con la retícula real (dinteles O a 3,86 m); QA lo acepta como idealización razonable **a condición de que el voladizo de fachada lo materialice la celosía Cajón O** (verificado en B1/B2: el cajón sí lo toma).
- La flexión (u_M=0,39) está bien. Los **dos errores están en los ELS** (flecha y vibración), que son justamente las magnitudes que gobiernan un voladizo CLT ligero.

## 6. Veredicto de QA

> **NO APTO** — la flexión coincide, pero la flecha del build (2,6 mm) es un error aritmético (correcto ≈ 9,87 mm) y la frecuencia propia recalculada (6,7–7,7 Hz) **incumple el criterio f₁ ≥ 8 Hz** (EC5 §7.3), que es el ELS gobernante.

- **Devolución a build (no se ajusta tolerancia ni esperado):**
  1. Corregir la flecha a δ≈9,87 mm (sigue cumpliendo L/300, pero el número debe ser correcto).
  2. **Resolver la vibración:** con f₁≈6,7–7,7 Hz el forjado NO cumple el umbral de 8 Hz. Aumentar canto/rigidez del nervio, contar la sección mixta acero-CLT (conexión), o justificar por criterio de aceleración (no solo frecuencia). Es una decisión de proyecto para JM.

## 7. Firma (segunda llave — JM)

```
Verificado por QA:   agente QA / run 2026-06-24      fecha: 2026-06-24
Tolerancias fijadas por JM:  ☐
FIRMA JM (técnico competente): ______________  fecha: [   ]   → CERTIFICADO ☐
```

*Scripts QA: `qa/informes/qa_normativa.py` (cálculo A1); evidencia de la geometría en `qa/informes/qa_geom_extract.py`.*
