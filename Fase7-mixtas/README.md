# Fase 7 — Estructuras mixtas: viga mixta acero-hormigón (EC4)

Caso del Grupo B de la hoja de ruta v2 que **cierra el catálogo de "estructura de
edificación" habitual**. Es un caso **a nivel de sección**: reutiliza el **solver de
barras** (PyNite) para los esfuerzos de la viga biapoyada y añade la verificación EC4
(EN 1994-1-1, AN España) sobre la sección mixta.

## Caso: viga mixta secundaria con forjado colaborante

Subcarpeta `proyecto-viga-mixta/`. Viga **IPE 360 (S275)** biapoyada de **8,0 m**,
separación entre vigas **3,0 m**, con **forjado colaborante** (chapa nervada
perpendicular, canto total 120 mm, hormigón sobre nervios 62 mm, C25/30) y conectores
de espigo **Ø19/100 mm** a paso de nervio (≈207 mm). **Construcción sin apear**.

Dos fases de carga sobre la misma viga (esfuerzos independientes de la sección):

- **Construcción** (acero solo): peso del hormigón fresco + sobrecarga de ejecución.
- **Mixta** (servicio): permanentes totales + sobrecarga de uso.

**Resultados (validados):**
- **Ancho eficaz** b_eff = 2,10 m.
- **Flexión mixta**: PNA en el ala superior; M_pl,Rd (conexión total) = 511 kN·m;
  como la conexión es **parcial** (η = 0,66 ≥ η_min 0,40, con 1 conector/nervio no caben
  más), el momento resistente se interpola (EC4 §6.2.1.3): **M_Rd = 432 kN·m** ≥
  M_Ed = 244 kN·m (**56 %**).
- **Conexión a cortante**: P_Rd = 62,7 kN/perno (k_t = 0,85 por chapa perpendicular);
  rasante N_c = 1844 kN; 29,4 conectores para conexión total / 19,3 dispuestos en media luz.
- **Cortante vertical**: V_Ed = 122 / V_pl,Rd = 558 kN (**22 %**).
- **Fase de construcción** (acero solo): M_Ed = 114 / M_c,Rd = 280 kN·m (**41 %**).
- **Flecha**: total 19,5 mm ≤ L/250 = 32 mm (**61 %**); de uso 4,2 mm ≤ L/350 = 22,9 mm
  (**18 %**), con n₀ = 6,8 (corto plazo) y n_L = 20,3 (largo plazo, fluencia).
- Veredicto: **CUMPLE**.

```bash
python3 scripts/generate_test_ifc_mixta.py
python3 scripts/run_all_mixta.py proyecto-viga-mixta
NODE_PATH=$(npm root -g) node scripts/generate_memoria_mixta.js proyecto-viga-mixta
```

## Arquitectura

| Script | Función |
|---|---|
| `generate_test_ifc_mixta.py` | IFC4: viga (curve member) + perfil + losa colaborante + conectores + cargas por fase |
| `solver_mixta.py` | Viga biapoyada con el **solver de barras** (PyNite); M(x)/V(x) en fase construcción y mixta |
| `verificacion_mixta.py` | EC4: b_eff, M_pl,Rd (fibras) + M_Rd con grado de conexión, conexión a cortante, V_pl,Rd, construcción, flecha |
| `plots_mixta.py` | Sección mixta con PNA + leyes M(x)/V(x) de ambas fases |
| `generate_memoria_mixta.js` | Memoria de cálculo en Word |
| `run_all_mixta.py` | Orquestador |

## Convenciones y decisiones validadas

- **Esfuerzos por el solver de barras**: la viga es isostática, M(x)/V(x) no dependen de
  la sección; se resuelven las dos fases con las cargas respectivas.
- **M_pl,Rd por modelo de fibras** (acero a f_yd, hormigón de cobertura a 0,85 f_cd): cubre
  el PNA en losa, ala o alma. Desprecia los acuerdos del perfil (≈4 % de área), del lado
  de la seguridad; verificado contra descomposición analítica (510,5 vs 511 kN·m).
- **Conexión parcial**: M_Rd = M_a,Rd + η·(M_pl,Rd − M_a,Rd), con η ≥ η_min (§6.6.1.2).
- **Construcción sin apear**: la flecha de la fase de construcción queda "bloqueada" y se
  suma a la mixta; las cargas permanentes usan n_L (fluencia) y la sobrecarga n₀.
- **Chapa perpendicular**: reducción k_t de la resistencia del conector (§6.6.4.2).

## Limitaciones / siguiente paso

Viga **biapoyada** (momento positivo); no se cubren viga **continua** (momento negativo,
fisuración del hormigón y armadura del ala traccionada), **pandeo lateral en construcción**
(se asume ala superior arriostrada por la chapa una vez fijada), ni vibraciones de forjado.
Extensiones naturales: viga continua, forjado colaborante (comprobación de la chapa como
encofrado y losa mixta), y conexión a nivel de servicio. **Predimensionado: revisión y
firma por técnico competente.**
