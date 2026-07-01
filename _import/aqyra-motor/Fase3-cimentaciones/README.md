# Fase 3 — Cimentaciones superficiales

Primer caso del catálogo de la hoja de ruta v2. Reutiliza el núcleo (lámina + nueva
capacidad de **muelles de suelo Winkler**) y añade la verificación **EC7 (geotecnia)**
junto a EC2.

## Caso: zapata aislada sobre lecho elástico

Subcarpeta `proyecto-zapata/`. Zapata C30/37 de 2,5×2,5 m y canto 50 cm bajo pilar
400×400 mm; terreno con módulo de balasto ks = 40 MN/m³ y resistencia de cálculo
Rd = 250 kPa. Carga de pilar N_G = 600, N_Q = 200 kN y momento M_G = 60 kN·m.

**Capacidad nueva del núcleo:** placa sobre **muelles verticales Winkler** (k = ks·área
tributaria por nodo), con la carga del pilar repartida en su huella (evita la
concentración del nudo). Reutiliza punzonamiento (`ec2_punz_fis`) y armado a flexión.

**Resultados (todos validados):**
- Equilibrio vertical exacto (**0,00 %**): Σ reacciones del suelo = carga aplicada (1110 kN ELU).
- **EC7**: presión del terreno trapezoidal **141–207 kPa** < Rd 250 (aprov. 83 %), sin despegue.
- **EC2 flexión** (momento en la cara del pilar, integrando la presión): Mx ≈ 114, My ≈ 99 kN·m/m → **φ10/100** en ambas direcciones (d = 434 mm).
- **EC2 punzonamiento**: V_Ed neto (axil − presión dentro del perímetro) → 37 % → OK.
- **EC2 cortante** a un canto de la cara: 64 % → OK.
- **CUMPLE**. Mapas de presión del terreno, momento de placa y planta.

```bash
python3 scripts/generate_test_ifc_zapata.py
python3 scripts/run_all_zapata.py proyecto-zapata
NODE_PATH=$(npm root -g) node scripts/generate_memoria_zapata.js proyecto-zapata
```

## Arquitectura

| Script | Función |
|---|---|
| `generate_test_ifc_zapata.py` | IFC4: superficie zapata + pilar + terreno (ks, Rd) + cargas |
| `solver_zapata.py` | Placa sobre **muelles Winkler**; carga de pilar en huella; presión del suelo |
| `ec2_punz_fis.py` | (reuso) punzonamiento §6.4 + dimensionamiento |
| `verificacion_zapata.py` | **EC7** (tensión admisible, excentricidad) + **EC2** (flexión en cara, punzonamiento, cortante) |
| `plots_zapata.py` | Mapas de presión, momento y planta |
| `generate_memoria_zapata.js` | Memoria de cálculo en Word |
| `run_all_zapata.py` | Orquestador |

## Convenciones y decisiones validadas

- **Muelles Winkler**: k_nodo = ks · área tributaria; presión = ks · asiento.
- **Carga de pilar en su huella** (no puntual) para evitar concentración local.
- **Momento de diseño en la cara del pilar** integrando la presión del terreno
  (sección crítica EC2), evitando el pico FE bajo el pilar.
- **Punzonamiento neto**: V_Ed = axil del pilar − presión del suelo dentro del perímetro de control.

## Limitaciones

Muelles lineales (el despegue se controla por p_min ≥ 0; muelles solo-compresión sería
la refinación). ks y Rd proceden del estudio geotécnico. No se incluye vuelco/deslizamiento
global ni asientos a largo plazo. Análisis lineal. **Revisión y firma por técnico competente.**

---

## Caso 2: losa de cimentación (raft) sobre lecho elástico

Subcarpeta `proyecto-losa-cimentacion/`. Extensión directa de la zapata: la misma placa
MITC4 sobre muelles Winkler, ahora **12 × 9 m, canto 0,70 m**, bajo una **retícula de 9
pilares** (esquina/borde/interior con cargas crecientes). Terreno ks = 40 MN/m³,
Rd = 300 kPa, hormigón C30/37.

**Resultados (validados):**
- Equilibrio vertical **0,00 %**: Σ reacciones del suelo = carga aplicada (11 310 kN ELU).
- **EC7 presión**: trapezoidal **72–177 kPa** (con peso propio) < Rd 300 → 59 %, sin despegue.
- **EC7 asientos**: máx 2,78 / mín 1,70 mm; diferencial 1,08 mm → distorsión **1/2783 < 1/500** → OK.
- **EC2 flexión** (en la sección crítica, excluido el pico singular bajo pilares):
  inferior X ≈ 311, Y ≈ 261 kN·m/m → ~11–16 cm²/m; superior = mínimo (malla).
- **EC2 punzonamiento** por pilar (interior/borde/esquina): crítico el pilar interior,
  V_Ed,neto = 1280 kN → **64 %** de v_Rd,c (sin armadura de punzonamiento), biela 25 %.
- **CUMPLE**. Mapas de presión del terreno y de momentos Mx/My con la posición de pilares.

```bash
python3 scripts/generate_test_ifc_raft.py
python3 scripts/run_all_raft.py proyecto-losa-cimentacion
NODE_PATH=$(npm root -g) node scripts/generate_memoria_raft.js proyecto-losa-cimentacion
```

| Script | Función |
|---|---|
| `generate_test_ifc_raft.py` | IFC4: placa + retícula de pilares (x,y,lado,N_G,N_Q) + terreno (ks, Rd) |
| `solver_raft.py` | Placa MITC4 sobre muelles Winkler, multi-pilar; presión, asientos, momentos |
| `verificacion_raft.py` | **EC7** (presión vs Rd, asiento diferencial) + **EC2** (flexión 2D sup./inf. + punzonamiento por pilar con dimensionamiento) |
| `plots_raft.py` | Mapas de presión y de momentos Mx/My con marcas de pilares |
| `generate_memoria_raft.js` | Memoria de cálculo en Word |
| `run_all_raft.py` | Orquestador |

**Decisiones clave de la raft:** clasificación automática de cada pilar (interior/borde/
esquina) por su distancia al borde para el punzonamiento; **momento de diseño en la sección
crítica** (se excluyen los quads dentro de la huella + 0,5·d del pilar, donde el pico es una
singularidad); el peso propio se añade a la presión del terreno solo para la capacidad (no
genera flexión al ir equilibrado por la reacción uniforme).

## Limitaciones de la raft

Modelo elástico-lineal de Winkler con un único ks (sin acoplamiento entre resortes ni
variación del terreno); muelles bidireccionales (el despegue se controla por p_min ≥ 0);
no se incluyen subpresión por agua, fases de carga ni interacción con la superestructura.
**Predimensionado: revisión y firma por técnico competente.**

## Próximos casos de cimentación (hoja de ruta v2)

Zapata combinada/corrida, y — ya en cimentación profunda (hechas en Fase 4–5) — encepados
de pilotes (bielas y tirantes) y pilotes (viga sobre muelles + EC7).
