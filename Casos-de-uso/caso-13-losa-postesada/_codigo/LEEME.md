# Código fuente — Caso 13 (losa plana postesada, EC2 §5.10 + §6.4.4)

Código nuevo del plugin `motor-calculo-estructural` v0.17.0 (lleva el pretensado a 2D).
Reutiliza `laminas/flat` (placa MITC4 + punzonamiento, caso 3) y `pretensado/` (EC2 §5.10, caso 12).

## Ficheros
- `run_all_losa_postesada.py` — orquestador end-to-end (IFC ortodoxo losa+9 pilares →
  modelo neutro + `Pset_Estructurando_Pretensado` de la superficie → balance 2D →
  placa MITC4 con caso P → pérdidas → verificación → JSON + diagramas).
- `solver_losa_postesada.py` — placa MITC4 sobre apoyos puntuales con el **caso P** del
  pretensado (presión equivalente hacia arriba w_p) + G0 (peso propio g0=t·25, NO viene
  del IFC), G (g2) y Q; combinaciones ELU/ELS con P y combo de transferencia (g0+P0).
- `balance_2d.py` — biblioteca de balance de cargas 2D: w_p por dirección (8·P·a/L²),
  banded(X)+distribuido(Y), σcp biaxial, V_p (componente vertical de tendones que cruzan u1).
- `verificacion_losa_postesada.py` — tensiones por fibra por franja (transferencia/
  cuasiperm/rara, momentos NETOS del FEM), contraste cargas-equiv vs fuerza+excentricidad
  por franja, punzonamiento §6.4.4 con/sin efecto favorable, ELU flexión por fibras
  (activa+pasiva, dimensiona la pasiva superior), fisuración §7.3, flecha.
- `plots_losa_postesada.py` — 8 diagramas.
- `generate_memoria_losa_postesada.py` — memoria Word.
- `ec2_punz_fis_AMPLIADO.py` — copia de `laminas/ec2_punz_fis.py` ampliado retrocompatible:
  `punzonamiento(..., sigma_cp=0.0, V_p=0.0, k1=0.1)` → v_Rd,c += k1·σcp y V_Ed,red = V_Ed − V_p.
  Con los defaults reproduce EXACTAMENTE el caso 3 (sin pretensado).

## Ejecución (sandbox, plugin desempaquetado en `scripts/`)
```bash
python3 pretensado/run_all_losa_postesada.py <proyecto> <ruta>/caso-13.ifc
python3 pretensado/generate_memoria_losa_postesada.py <proyecto>
```
Malla MITC4 1,0 m (coincide con las 9 cabezas en {0,8,16} m; 0,5 m queda como refinamiento).

## Resultados validados (FEM MITC4, este hilo)
- Balance 2D: w_px=w_py=4,505 → w_p=9,01 kN/m² ≈ permanente 9,0 (**residual 0,11 %**);
  P/m=212 kN/m; **σcp=0,848 MPa**; σp,∞=0,600·fpk, σp0=0,720·fpk (pérdidas dif. 16,7 %).
- Equilibrio ELU sobre carga neta **0,000 %**. Contraste métodos **Δ=0,000 MPa** por franja.
- Tensiones por fibra dentro de límites (rara inf +1,64 < fctm=3,5).
- ELU flexión: campo 0,68 / apoyo 0,99 (As sup. dimensionada 9,50 cm²/m ≈ φ16/200).
- Punzonamiento §6.4.4: interior V_Ed=1.258 kN (tributaria; pico elástico 1.937 kN como
  envolvente); efecto favorable relaja 2,61→2,27 (−13 %). La losa de 0,25 m a 8 m
  **requiere ábaco/capitel/Asw** (dimensionado: h≈0,47 m / capitel ≈2,18 m / Asw·sr≈110 cm²/m).
- Flecha 5,2 mm ≪ L/250=32 mm. **Veredicto: CUMPLE con solución de punzonamiento;
  aprov. estructural máx 0,99.** Predimensionado, a revisar y firmar por técnico competente.
  NDP `[confirmar AN]` (EC2 §5.10/§6.4.4 — España): k1=0,10, μ/k, penetración de cuña,
  límites del acero activo.
