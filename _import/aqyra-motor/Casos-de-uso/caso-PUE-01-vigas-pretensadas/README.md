# caso-PUE-01 — Tablero de vigas pretensadas (emparrillado)

Primer caso e2e de la disciplina **`puentes`** (Ola 7, PT 7.1). Demuestra el flujo
completo **IFC/Alignment (modelo neutro) → emparrillado → motor-fem (FEM-1) →
IAP-11 → EC2 → memoria + write-back**, consumiendo el núcleo `motor-fem` v0.2.0
(contrato C5, peldaño FEM-1).

> Predimensionado/asistencia. **Revisar y firmar por técnico competente (ICCP).**

## Tablero

Luz **L = 25 m**, **4 vigas** pretensadas doble-T (canto 1.50 m, A = 0.70 m², I = 0.22 m⁴),
separación 2.5 m, ancho total 8.75 m (**2 carriles** virtuales de 3 m), 3 riostras
(estribos + centro). Hormigón **HP-45** (fck = 45 MPa; fck(t) = 32 MPa en transferencia).

## Flujo y ficheros

| Paso | Script (`puentes`) | Salida |
|---|---|---|
| Idealización emparrillado | `idealizacion/emparrillado.py` | `modelo_neutro.json` (84 nodos, 89 barras) |
| Acciones IAP-11 (G, LM1, T, V) | `acciones/iap11.py` | casos + `cargas_moviles` |
| Pretensado (cargas equiv.) | `pretensado/inyeccion_pretensado.py` | caso `P` |
| Cálculo (estático+móvil+modal) | `motor-fem` v0.2.0 (C5) | esfuerzos, envolventes, f₁ |
| Comprobación EC2 | `comprobacion/ec2_tablero.py` | aprovechamientos |
| Write-back | `comun/resultado_ifc_puente.py` | `mapping_resultado_puente.json` |

- `entrada_caso.json` — datos del tablero y del tendón.
- `resultado_puente.json` — resultado completo (por viga, pérdidas, modal, veredicto).
- `mapping_resultado_puente.json` — `Pset_Estructurando_ResultadoPuente` (write-back).
- `memoria-puente-PUE01.md` — memoria de cálculo.

## Veredicto

**CUMPLE.** Aprovechamiento máximo **0.81** (gobierna el cortante por bielas; flexión 0.72).
Pérdidas de pretensado **21.2 %** (P₀ = 5200 kN → P∞ = 4098 kN). Frecuencia fundamental
**f₁ = 2.24 Hz** (modal, masa concentrada peso propio + cuasipermanente).

## Reproducir

```
PYTHONPATH=/tmp/pylibs:<motor-fem>/scripts:<motor-fem>/scripts/elementos:<motor-calculo>/scripts/pretensado \
  python3 puentes/scripts/run_all_viga_pretensada.py entrada_caso.json resultado_puente.json
```
