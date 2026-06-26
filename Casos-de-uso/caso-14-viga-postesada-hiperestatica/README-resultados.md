# Caso 14 — Resultados (viga postesada continua hiperestática)

**Veredicto: CUMPLE · aprovechamiento máximo 0,79 · plugin → v0.20.0**

Viga postesada continua C40/50, b=0,50 × h=1,30 m, **2 vanos de L=20 m** (3 apoyos),
14×Y1860S7 (Ap=2.100 mm², P_m,∞=2.344 kN), trazado parabólico por vano
(e_vano=+0,30 / e_apoyo central=−0,30 m, drape 0,45 m).

## Lo nuevo del caso: la hiperestaticidad

| Magnitud | Apoyo central | Centro de vano |
|---|---|---|
| Primario M₁ = −P·e | +703 kN·m | −725 kN·m |
| Total M_p,tot (FEM) | +1.055 | −593 |
| **Secundario M_sec = M_p,tot − M₁** | **+351,5** | +132 |

- **M_sec lineal** (R² = 1,000000) y **nula en los apoyos extremos** (0,00/0,00 kN·m).
- **FEM vs método de las fuerzas**: 351,5 vs 351,5 kN·m (**Δ = 0,000 %**).
- Identidad M_p,tot = M₁ + M_sec verificada (error 5,8·10⁻¹¹).
- **Línea de presiones** e_p = e + M_sec/P → tendón **NO concordante**
  (la línea de presiones se separa del tendón +0,15 m en el apoyo central).

## Balance y servicio

- **Balance**: w_p = 8·P·a/L² = 21,09 kN/m equilibra la permanente g0+g2 = 21,25
  (residual −0,74 %). σp0/fpk = 0,720, σp,∞/fpk = 0,600 (pérdidas diferidas 16,7 %).
- **Tensiones por fibra con M_sec** dentro de límites: apoyo rara top +0,71 < fctm = 3,5;
  resto comprimido en todos los estados.

## ELU con el momento secundario (γ_P = 1,0, §5.10.8)

- M_Ed = γ_G·M_g + γ_Q·M_q + **1,0·M_sec** (el primario va en la resistencia por fibras).
- **Apoyo central** (hogging): M_Ed = −2.334 + 1,0·(+352) = **−1.983 kN·m**
  (el secundario **alivia**), M_Rd = 2.509 → **u = 0,79**, x/d = 0,296.
- **Centro de vano** (sagging): M_Ed = 1.614, M_Rd = 2.537 → **u = 0,64**, x/d = 0,293.
- **Redistribución §5.5**: δ_min = 0,81 disponible (no aplicada, u < 1).
- **Flecha** residual 1,02 mm ≪ L/250 = 80 mm.

## Entregables

`caso-14.ifc`, `validacion-IFC.txt`, `modelo_neutro.json`,
`verificacion_pretensado_continua.json`, `memoria_calculo_pretensado_continua.docx`,
8 diagramas (`alzado_tendon`, `cargas_equivalentes`, `momentos_M1_Mptot_Msec`,
`linea_presiones`, `leyes_MV`, `interaccion_ELU`, `tensiones_fibra`, `flecha`),
código en `_codigo/`.

> Predimensionado, a revisar y firmar por técnico competente. NDP del Anejo Nacional
> España `[confirmar AN]`: coeficientes de pérdidas, límites del acero activo, μ/k, δ.
