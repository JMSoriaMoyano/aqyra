# Decopak HQ — Subsistemas B y C: celosías y enlaces de acero S355 (EC3)

> **PROPUESTA — pendiente de verificación QA independiente y firma de JM. Versión de núcleo no anclada (versions.lock=0.0.0).**

- **Rol:** build (producción). QA la ejecuta un agente independiente con su propio oráculo.
- **Norma:** EN 1993-1-1 (EC3) + AN España; γM0=γM1=1,05, γM2=1,25; S355 (fy=355 MPa).
- **Fecha:** 2026-06-24. **Restricción:** Python puro + fórmulas EC documentadas; reglas EC3 tomadas de `barras/verificacion.py` y `barras/perfiles_db.py` del motor (sin PyNite en este entorno).

---

## 1. Idealización desde el IFC — topología de las celosías

**Cajón O (viga-celosía vertical principal, núcleo lateral):**

| Componente | Perfil (IFC) | Geometría | Función |
|---|---|---|---|
| Cordones ext/int | **SHS 180×8** (#40) | longitudinales en Y, **L=40,86 m**, en X=5,27/6,47, cotas Z=5,75/8,833/11,917/15 (8 ud) | cordones de la viga-pared |
| Montantes ext/int | **SHS 120×6** (#113) | verticales, **h=9,25 m** (Z 5,75→15), paso ΔY≈3,0 m (32 ud) | montantes |
| Diafragmas inf/sup | SHS 120×6 | horizontales en X, L=1,20 m (separación cordones), 32 ud | cierre del cajón |
| Diagonales | SHS 150×8 / 160×8 / 200×10 (#774/#746) | triangulación (45 ud) | cortante de la celosía |

→ El **Cajón O** es una **viga Vierendeel/celosía de gran canto (9,25 m) y luz 40,86 m**, de doble plano (ancho 1,2 m), que forma el núcleo lateral. Apoya sobre los **muros HA-30** (NC-Lab en Y≈0–3, NC-Vest en Y≈25–32) y **vuela** en los extremos. De ella cuelgan, vía dinteles de conexión, los **forjados cassette en voladizo transversal**.

**Cercha E** (cordones SHS, montantes, 45 diagonales) y **Alma C** (4 cordones, 15 montantes): celosías secundarias de arriostramiento/reparto en las otras caras del núcleo. Misma familia EC3.

**Enlaces (subsistema C):**
- **Conexión dintel O** (SHS 250×12, #718): L=3,86 m; **dintel E** (SHS 250×12): L=2,35 m. Transfieren el forjado al cajón.
- **Conexión montante** (SHS 250×12): verticales h=9,25 m. **Conexión diagonal** (SHS): arriostran.
- **Tirantes altillo** (SHS 80×8, #3626): verticales L=2,85 m (cuelgan el altillo-lab de la P1).

---

## 2. Propiedades de sección (SHS, geometría del IFC) y resistencias S355

Tubo cuadrado hueco lado b, espesor t:  A=b²−(b−2t)²; I=[b⁴−(b−2t)⁴]/12; W_el=I/(b/2); W_pl=(b³−(b−2t)³)/6; i=√(I/A).
f_yd = 355/1,05 = **338,1 MPa**.

| Perfil | b,t [mm] | A [cm²] | I [cm⁴] | W_pl [cm³] | i [cm] | clase* |
|---|---|---|---|---|---|---|
| SHS 180×8 | 180,8 | 55,0 | 2689 | 339 | 6,99 | 1 |
| SHS 120×6 | 120,6 | 27,4 | 581 | 113 | 4,61 | 1 |
| SHS 150×8 | 150,8 | 45,4 | 1491 | 226 | 5,73 | 1 |
| SHS 160×8 | 160,8 | 48,6 | 1831 | 259 | 6,14 | 1 |
| SHS 200×10 | 200,10 | 76,0 | 4500 | 489 | 7,70 | 1 |
| SHS 250×12 | 250,12 | 114,2 | 10620 | 925 | 9,64 | 1 |
| SHS 80×8 | 80,8 | 23,0 | 196 | 65 | 2,92 | 1 |

*(c/t = (b−3t)/t ≤ 33ε con ε=√(235/355)=0,814 → 33ε=26,9; p. ej. SHS 180×8: (180−24)/8=19,5 ≤ 26,9 → Clase 1. Todos los SHS listados son Clase 1 en compresión y flexión.)*

---

## 3. Camino de cargas y esfuerzos

### 3.1 Carga descendente sobre el Cajón O (desde los forjados cassette)

Carga ELU del forjado (doc 02, oficinas B): w_d = 1,35·(g_losa+g_muerta) + 1,50·q = 1,35·(0,67+2,0)+1,50·2,0 = **6,60 kN/m²**.
Área tributaria de forjado hacia el Cajón O por planta: las costillas (vuelo ≈6,2 m) descargan ≈ mitad sobre el cajón. Ancho colaborante de fachada por planta ≈ 6,3 m × longitud 40,86 m. Carga lineal sobre el cajón por planta:
- q_planta ≈ 6,60 · (6,3/2) = 20,8 kN/m. Con **4 plantas** (P1–PC) colgando: q_cajón ≈ **83 kN/m** (envolvente; incluye reacción de voladizo y peso propio del acero ≈ +3 kN/m).

### 3.2 Viga-celosía Cajón O — esfuerzos globales (canto h=9,25 m; cordones a Δ=1,2 m en cada plano)

Modelo: **viga de gran canto biapoyada en los dos muros** (NC-Lab y NC-Vest), con luz entre apoyos L_v y voladizos en los extremos. Distancia entre centros de muros ≈ (28,4 − 1,5) = **26,9 m**; voladizos extremos a ≈ (40,86 − 28,4)/... → se adopta **luz biapoyada equivalente L = 27 m con voladizos a ≈ 7 m** (envolvente).

Momento flector máximo de la viga-celosía (vano, conservador como biapoyada L=27 m):
M_global = q·L²/8 = 83·27²/8 = **7.563 kN·m** (vano). En voladizo extremo (a=7 m): M_vol = q·a²/2 = 83·49/2 = **2.034 kN·m**.

**Axil en cordones** (par mecánico, brazo z = h = 9,25 m, repartido en 2 planos):
N_cordón = M_global / (z · n_planos) = 7.563 / (9,25·2) = **±409 kN** por cordón (vano).
Cortante global V = q·L/2 = 83·13,5 = 1.120 kN → **diagonales**: N_diag = V/(n_planos·sin θ). Con diagonal a ≈45° (paso 3 m, canto 9,25 → más tendida; sin θ ≈ 3,0/√(3,0²+9,25²)... la diagonal real triangula el paso de 3 m sobre 9,25 m de canto → se idealiza el panel con θ medido sobre el plano vertical). Tomando el panel de cortante con diagonal de longitud √(3²+3,08²)=4,3 m (entre montantes y nivel de planta), sin θ ≈ 0,72:
N_diag ≈ 1.120/(2·0,72) = **778 kN** (diagonal más solicitada, junto al apoyo).

### 3.3 Comprobación EC3 de los elementos críticos

**(B1) Cordón SHS 180×8 — flexocompresión (vano):** N_Ed=409 kN.
- N_c,Rd = A·f_yd = 55,0e-4·338,1e6 = **1.860 kN** → u_N = 409/1.860 = **0,22**.
- Pandeo (L_pandeo = paso de montantes ≈3,0 m, i=6,99 cm): λ̄ = (L/i)/(93,9ε) = (3,0/0,0699)/(93,9·0,814) = 42,9/76,4 = 0,56. Curva b (α=0,34): φ=0,5(1+0,34(0,56−0,2)+0,56²)=0,72; χ=1/(0,72+√(0,72²−0,56²))=0,86. N_b,Rd=0,86·1.860=**1.600 kN** → **u_buck=0,26 ✔**.

**(B2) Cordón en voladizo extremo + flexión local:** M_vol=2.034 kN·m sobre el par → N_cordón,vol=2.034/(9,25·2)=110 kN. Menos solicitado que el vano. ✔

**(B3) Diagonal SHS 200×10 a compresión (pandeo, EC3 6.3.1):** N_Ed=778 kN, L=4,3 m, i=7,70 cm.
- λ̄ = (4,3/0,077)/76,4 = 55,8/76,4 = 0,73. Curva b: φ=0,5(1+0,34(0,73−0,2)+0,73²)=0,86; χ=1/(0,86+√(0,86²−0,73²))=0,78.
- N_b,Rd = 0,78·76,0e-4·338,1e6 = **2.004 kN** → **u_buck = 778/2.004 = 0,39 ✔**.
  *(Si la diagonal fuese SHS 150×8: N_b,Rd≈0,72·45,4e-4·338,1e6=1.105 kN → u=0,70 ✔, aún cumple.)*

**(B4) Montante SHS 120×6 (h=9,25 m) a compresión:** recibe la carga vertical de un paso (≈83·3,0=249 kN por cada plano = 125 kN/montante) + componente de diagonales.
- N_Ed ≈ 250 kN (envolvente, montante junto a apoyo). L_pandeo=9,25 m (arriostrado por diafragmas y forjados cada planta ≈3,08 m → L_cr=3,08 m). i=4,61 cm: λ̄=(3,08/0,0461)/76,4=66,8/76,4=0,87. χ: φ=0,5(1+0,34(0,87−0,2)+0,87²)=0,99; χ=1/(0,99+√(0,99²−0,87²))=0,68. N_b,Rd=0,68·27,4e-4·338,1e6=**630 kN** → **u=0,40 ✔**.
  > **Supuesto S-B1:** montante arriostrado a pandeo cada planta (3,08 m) por los forjados/diafragmas. Si NO lo estuviera (L_cr=9,25 m): λ̄=2,61, χ≈0,13, N_b,Rd≈120 kN → **u=2,1 ❌**. **Decisión de JM / verificar arriostramiento real.**

### 3.4 Enlaces (subsistema C)

**(C1) Dintel O SHS 250×12 (L=3,86 m, biapoyado):** recibe la franja de forjado tributaria (≈6,3 m de vuelo / 2 lados → ancho ≈3,15 m): w=6,60·3,15=20,8 kN/m.
- M_Ed=w·L²/8=20,8·3,86²/8=**38,7 kN·m**; M_c,Rd=W_pl·f_yd=925e-6·338,1e6=**312,7 kN·m** → **u_M=0,12 ✔**.
- Flecha ELS: δ=5·w_k·L⁴/(384EI), w_k=(2,67+2,0)·3,15=14,7 kN/m → δ=5·14,7e3·3,86⁴/(384·210e9·10620e-8)=0,0019 m=1,9 mm; L/300=12,9 mm → u=0,15 ✔.

**(C2) Dintel E SHS 250×12 (L=2,35 m):** M_Ed=20,8·2,35²/8=14,4 kN·m → u_M=0,05 ✔.

**(C3) Conexión montante SHS 250×12 (h=9,25 m):** soporte vertical principal del enlace, baja la carga de plantas al núcleo. N_Ed (envolvente 4 plantas de su área tributaria ≈ 6,3×3,0 m): ≈ 6,60·6,3·3,0·4/... reparto ≈ **800 kN**.
- L_cr=3,08 m (arriostrado por planta), i=9,64 cm: λ̄=(3,08/0,0964)/76,4=31,9/76,4=0,42; χ: φ=0,5(1+0,34·0,22+0,42²)=0,63; χ=0,92. N_b,Rd=0,92·114,2e-4·338,1e6=**3.553 kN** → **u=0,23 ✔**.

**(C4) Tirante altillo SHS 80×8 (tracción, cuelga el altillo de P1):** área de altillo (sala formación C1, 4,98×10 m, qk=3,0) repartida en 6 tirantes.
- Carga ELU altillo: w=1,35·(0,30·25+2,0)+1,50·3,0=1,35·9,5+4,5=**17,3 kN/m²** (losa HA e=0,30: 0,30·25=7,5; +muerta 2,0 → g=9,5). Área/tirante=49,8/6=8,3 m² → N_Ed=17,3·8,3=**143,6 kN** (tracción).
- N_t,Rd=A·f_yd=23,0e-4·338,1e6=**777,6 kN** → **u_t=143,6/777,6=0,18 ✔**.

---

## 4. Tabla de aprovechamientos — Subsistemas B y C

| id | Elemento | Perfil | Comprobación | Ed | Rd | **u** | Veredicto |
|---|---|---|---|---|---|---|---|
| B1 | Cordón Cajón O (vano) | SHS 180×8 | Pandeo+axil | 409 kN | 1.600 | **0,26** | ✔ |
| B3 | Diagonal Cajón O | SHS 200×10 | Pandeo compresión | 778 kN | 2.004 | **0,39** | ✔ |
| B4 | Montante Cajón O (arriostrado) | SHS 120×6 | Pandeo | 250 kN | 630 | **0,40** | ✔ |
| B4' | Montante Cajón O (**no arriostrado**) | SHS 120×6 | Pandeo L=9,25 m | 250 kN | 120 | **2,1** | ❌ ver S-B1 |
| C1 | Dintel O | SHS 250×12 | Flexión | 38,7 kN·m | 312,7 | **0,12** | ✔ |
| C1 | Dintel O | SHS 250×12 | Flecha L/300 | 1,9 mm | 12,9 | 0,15 | ✔ |
| C2 | Dintel E | SHS 250×12 | Flexión | 14,4 kN·m | 312,7 | 0,05 | ✔ |
| C3 | Conexión montante | SHS 250×12 | Pandeo | 800 kN | 3.553 | **0,23** | ✔ |
| C4 | Tirante altillo | SHS 80×8 | Tracción | 143,6 kN | 777,6 | **0,18** | ✔ |

**Aprovechamiento máximo (modelo con montantes arriostrados): u ≈ 0,40.** Con holgura amplia → coherente con el nombre del modelo IFC «v3 OPTIMIZADO (EC3)» (perfiles ya dimensionados). El único punto crítico es el **arriostramiento del montante** (S-B1).

---

## 5. Evidencia para QA

```
elementos: Cajon O (cordon SHS180x8, diagonal SHS200x10, montante SHS120x6),
           Cercha E, Alma C, dinteles SHS250x12, tirantes SHS80x8
entrada:   IFC perfiles #40/#113/#746/#718/#3626; geometria L y placements (texto STEP)
version:   versions.lock=0.0.0 (NO ANCLADA)
norma:     EC3 6.2.4/6.2.5/6.2.6 (seccion), 6.3.1 (pandeo curva b), EC0 (combinaciones)
metodo:    equilibrio de viga-celosia (par mecanico cordones, cortante->diagonales) +
           comprobacion EC3 segun barras/verificacion.py; SIN PyNite (entorno)
resultado: u_max ~ 0,40 (montante arriostrado); HALLAZGO B4': montante no arriostrado u=2,1
oraculo:   QA: solver matricial de celosia (PyNite/anaStruct) sobre los nudos reales del
           IFC + EC3; golden DEC-B1 (diagonal pandeo) y DEC-B2 (cordon flexo-axil)
SUPUESTOS: areas tributarias estimadas; luz biapoyada equiv. 27 m + voladizo 7 m;
           reparto de cortante en diagonales a 45deg idealizado
```

## 6. Puntos para JM
1. **S-B1 (CRÍTICO):** confirmar que los montantes SHS 120×6 del Cajón O están **arriostrados a pandeo a nivel de cada planta (≈3,08 m)** por los forjados/diafragmas. Si no, no cumplen (u=2,1) y hay que rigidizar o aumentar perfil.
2. Confirmar el **esquema de apoyos del Cajón O** sobre los muros HA (luz biapoyada + voladizos) — gobierna el axil de cordón.
3. QA debe resolver la celosía con los **nudos reales del IFC** (este predimensionado usa equilibrio global); pueden aparecer picos locales en barras concretas.

---
**Aviso:** PREDIMENSIONADO. Debe revisarlo y firmarlo un técnico competente. Pendiente de verificación QA independiente + firma de JM.
