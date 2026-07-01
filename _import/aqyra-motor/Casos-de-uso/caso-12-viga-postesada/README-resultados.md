# Caso 12 — Viga postesada isostática (EC2 §5.10) — Resultados

Viga simplemente apoyada C40/50, b=0,50 × h=1,30 m, L=20,0 m. 1 tendón postesado
13×Y1860S7 (Ap=1.950 mm²), trazado parabólico e=0,50 m. Cargas g2=5,0 / q=12,0 kN/m
(ψ₂=0,3); peso propio g0=16,25 kN/m.

## Veredicto: CUMPLE (aprovechamiento máximo 0,91 — cortante)

## Valores clave validados frente al chequeo de mano

| Magnitud | Calculado | Chequeo de mano | Estado |
|---|---|---|---|
| P_m,∞ | 2.125 kN (σp,∞=0,586·fpk) | 2.125 kN (0,59·fpk) | OK |
| P0 (transferencia) | 2.535 kN (σp0=0,699·fpk) | 2.535 kN (0,70·fpk) | OK |
| w_p (load balancing) | 21,25 kN/m | 21,25 kN/m | OK |
| Residual de equilibrio | 0,0 % | ≈ 0 % | OK |
| M_g0 / M_perm / M_q | 812,5 / 1.062,5 / 600 kN·m | 812 / 1.062 / 600 | OK |
| M_cuasiperm / M_rara | 1.242,5 / 1.662,5 kN·m | 1.242 / 1.662 | OK |
| M_Ed (ELU) | 2.334,4 kN·m | 2.334 | OK |
| σ transferencia sup/inf | −0,67 / −7,13 MPa | −0,67 / −7,13 | OK |
| σ cuasiperm sup/inf | −4,55 / −1,99 MPa | −4,55 / −1,99 | OK |
| σ rara sup/inf | −7,53 / **+0,99** MPa | −7,53 / +0,99 | OK |
| M_Rd (ELU fibras) | 2.908 kN·m (x/d=0,23) | ≥ M_Ed | OK |
| Cross-check cargas equiv. vs F+e | Δ = 0,0 MPa | mismo estado | OK |

Compresión transferencia ≤ 0,6·fck(t)=19,2 MPa (aprov. 0,37); cuasiperm ≤ 0,45·fck=18,0
MPa (aprov. 0,25, sin descompresión del fondo); rara: tracción de fondo +0,99 < fctm=3,5
(aprov. 0,28, fisuración controlada). ELU flexión aprov. 0,80. Cortante V_Rd,c con σcp
aprov. 0,91 (gobierna; por debajo, sin armadura de cortante mínima en predimensionado).

## Entregables en esta carpeta

- `ENUNCIADO.md` — enunciado del caso (estilo casos 11/R1).
- `generate_caso12_ifc.py` — generador del IFC ortodoxo (`caso-12.ifc`).
- `validacion-IFC.txt` — recuento de entidades del IFC y datos del Pset de pretensado.
- `modelo_neutro.json` — modelo neutro (sección, material, apoyos, cargas, pretensado).
- `verificacion_pretensado.json` — pérdidas, load balancing, momentos, validación cruzada,
  verificación completa y criterios de aceptación.
- `_codigo/` — código fuente del módulo `pretensado/`:
  - `solver_pretensado.py` — parser ortodoxo + lectura del Pset.
  - `ec2_pretensado.py` — biblioteca EC2 §5.10 (cargas equivalentes, F+e, pérdidas, combinaciones).
  - `verificacion_pretensado.py` — tensiones por fibra, ELU fibras, fisuración, cortante.
  - `run_all_pretensado.py` — orquestador end-to-end + validación cruzada.
  - `plots_pretensado.py` — diagramas (trazado, cargas equiv., M/V, tensiones, ELU, pérdidas).
  - `generate_memoria_pretensado.py` — memoria Word (python-docx).

## Estado de ejecución — COMPLETADO

Las fuentes del módulo (truncadas inicialmente por el editor, INC-04: faltaban el cierre del
`dict` final de `ec2_pretensado.py`, el `)` del `print` de `solver_pretensado.py` y se habían
añadido bytes nulos al generador de IFC) se **repararon** y validan con `ast.parse`. El flujo
se ejecutó end-to-end y reprodujo el chequeo de mano. Todo entregado:

- `caso-12.ifc` (IFC4, abre OK), `modelo_neutro.json` y `verificacion_pretensado.json`
  regenerados por ejecución real.
- `memoria_calculo_pretensado.docx` (40 párrafos, 7 diagramas embebidos) y los 7 `.png`
  (trazado del tendón, cargas equivalentes, leyes M/V, tensiones por fibra en transferencia y
  servicio, diagrama de interacción/ELU, pérdidas a lo largo del tendón).
- Módulo copiado a `scripts/pretensado/` y **reempaquetado acumulativo** del `.plugin`.

### Coordinación de versiones (hilos en paralelo, resuelta)

El caso 12 (Dirección 1) tomó **0.15.0**; en paralelo el caso **R2** (Dirección 2) amplió
`puente_analitico/` a superficies y tomó **0.16.0**. Tras una breve carrera de escritura sobre
la carpeta compartida, R2 reempaquetó **acumulativo partiendo del `.plugin` v0.15.0 con
`pretensado/` válido** y añadió sus ficheros. **`.plugin` instalado final: v0.16.0 (133
entradas) = casos 1–11 + `sismico/` (EC8) + `pretensado/` (EC2 §5.10, caso 12) +
`puente_analitico/` con R1 (barras) y R2 (superficies)**, sin `node_modules`/`__pycache__`.
Verificado: el `pretensado/` tal como va empaquetado en el v0.16.0 instalado ejecuta y
reproduce todos los valores del chequeo de mano.

Reproducción:

```bash
python3 generate_caso12_ifc.py                                  # -> caso-12.ifc
python3 pretensado/run_all_pretensado.py <proj> caso-12.ifc     # -> JSON + PNG
python3 pretensado/generate_memoria_pretensado.py <proj>        # -> memoria_calculo_pretensado.docx
```

> Resultado de PREDIMENSIONADO. Debe ser revisado y FIRMADO por técnico competente.
> NDP marcados [confirmar AN] (EC2 §5.10: μ/k de rozamiento, penetración de cuña, límites
> de tensión del acero activo, retracción y fluencia — Anejo Nacional de España).
