# PUE-17 — Cajón postesado (IFC-driven, FEM-2)

**Ola 7 · PT 7.4.** Primer vertical avanzado de puentes sobre el peldaño **FEM-2**
(lámina curva MITC4 + rigidizadores + pared delgada) del motor `motor-fem`. Tablero
de **viga-cajón de hormigón postesado** de 3 vanos, calculado **de extremo a extremo
arrancando del IFC**.

> Predimensionado/asistencia. **A revisar y firmar por técnico competente (ICCP).**
> Los NDP se marcan `[confirmar AN]`.

## Cadena IFC-driven

```
gen_cases.py cajon  ─►  caso-PUE-17.ifc  (IFC4X3_ADD2)
        │                IfcBeam + IfcArbitraryProfileDefWithVoids (cajón unicelular)
        │                Pset_Estructurando_Cajon (bs/bi/h/t_top/t_bot/t_web, n_vanos, cargas)
        │                Pset_Estructurando_Postesado (P0, pérdidas, e_p, f, Ap, fpk, As)
        ▼
ifc_to_model_estructural.parse   ─►  tipología = «cajon»  (sección con celda cerrada)
        ▼
desde_ifc.leer  ─►  entrada_caso_desde_ifc.json   (adaptador _cajon)
        ▼
run_all_cajon.ejecutar
   1) idealizacion/cajon.py        → malla de LÁMINA PURA (MITC4) + diafragmas (rigidizadores)
   2) postesado evolutivo (balance) + IAP-11 (g1, g2, LM1)
   3) motor-fem (C5, FEM-2): estático + envolventes LM1 (esfuerzo_lamina) + modal
   4) comprobacion/ec2_cajon.py    → tensiones por FASE, descompresión, flexión ELU,
                                      cortante+torsión de Bredt, shear lag
        ▼
resultado.json  +  mapping_resultado_ifc.json
        ▼
writeback_ifc.aplicar  ─►  caso-PUE-17-resultados.ifc
        Pset_Estructurando_ResultadoPuente sobre el IfcBeam (Veredicto_global = CUMPLE)
```

## Cómo reproducirlo

```bash
export TMPDIR=/tmp HOME=/tmp
PP=/tmp/ifclib:/tmp/pylibs:<motor-fem/scripts>:<motor-fem/scripts/elementos>:<puentes/scripts/*>:<iso19650/scripts/*>
export MOTOR_FEM_SCRIPTS=<motor-fem/scripts>

# 1) generar el IFC4X3
python3 gen_cases.py cajon entrada_caso.json caso-PUE-17.ifc
# 2) cálculo IFC-driven (lee el .ifc directamente)
PYTHONPATH=$PP python3 run_all_cajon.py caso-PUE-17.ifc resultado.json
# 3) write-back de resultados al IFC
python3 writeback_ifc.py caso-PUE-17.ifc mapping_resultado_ifc.json caso-PUE-17-resultados.ifc
```

## Datos del tablero

| Parámetro | Valor |
|---|---|
| Vanos | 3 × 40 m (continuo) |
| Sección | cajón unicelular trapezoidal: b_sup 11,0 m · b_inf 6,0 m · canto 2,5 m |
| Espesores | losa sup 0,30 m · losa inf 0,25 m · almas 0,45 m |
| Material | HP-40 (E = 35 GPa, ν = 0,2, ρ = 2500 kg/m³) |
| Postesado | P0 = 70 000 kN, pérdidas 18 % → P∞ = 57 400 kN; flecha f = 1,1 m |
| Acciones | g1 (peso propio), g2 = 3,0 kN/m², LM1 (3 carriles) |

## Sección (pared delgada vs geometría real)

| Magnitud | Modelo de láminas (líneas medias) | Polígono IFC (área bruta) |
|---|---|---|
| A | 7,98 m² | 6,43 m² |
| I_y | 8,56 m⁴ | 15,19 m⁴ |
| J (Bredt) | 17,76 m⁴ | 14,44 m⁴ |

La diferencia es la esperada entre la **idealización de pared delgada** (con la que se
malla el cajón, fuente de verdad del FEM) y el **polígono macizo** del IFC (geometría
extruida real, cross-check). El modelo de láminas reproduce la **deflexión de viga-cajón
de Euler al 0,77 %** y el **momento de sección al 5,3 %** (la diferencia restante es
*shear lag* real) — ver `validacion/cajon_vs_viga.py`.

## Resultado — **CUMPLE** (aprovechamiento máx. 0,754)

555 nodos · 540 elementos · f₁ = 3,14 Hz · sección crítica: vano 2.

| Comprobación EC2 (sección crítica) | Aprov. | Veredicto |
|---|---|---|
| Construcción — compresión fibra inferior | 0,754 | CUMPLE |
| Construcción — tracción fibra superior | 0,000 | CUMPLE |
| Servicio — compresión fibra superior | 0,330 | CUMPLE |
| Servicio — tracción fibra inferior | 0,000 | CUMPLE |
| Descompresión (cuasipermanente) | 0,000 | CUMPLE |
| Flexión ELU (M_Ed 55 224 / M_Rd 166 232 kN·m) | 0,332 | CUMPLE |
| Cortante + torsión (interacción V/T de Bredt) | 0,532 | CUMPLE |

Tensiones (MPa): construcción σ_inf −12,67 / σ_sup −6,66; servicio σ_sup −7,91 /
σ_inf −6,32 (toda la sección en compresión → descompresión holgada). *Shear lag*:
ancho eficaz b_eff/b = 0,84.

## Archivos

- `entrada_caso.json` — datos paramétricos del cajón y del postesado.
- `caso-PUE-17.ifc` — IFC4X3 del cajón (geometría extruida real + Psets).
- `entrada_caso_desde_ifc.json` — `entrada_caso` reconstruido por el lector desde el IFC.
- `resultado.json` — comprobaciones EC2 por sección, tensiones por fase, modal.
- `mapping_resultado_ifc.json` — Psets de resultado para el write-back.
- `caso-PUE-17-resultados.ifc` — IFC con `Pset_Estructurando_ResultadoPuente`.
- `memoria-cajon-PUE17.md` — memoria de cálculo.
