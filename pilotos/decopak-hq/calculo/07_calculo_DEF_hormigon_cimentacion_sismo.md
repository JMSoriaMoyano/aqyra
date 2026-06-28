# Decopak HQ — Subsistemas D, E, F: muros HA, cimentación profunda y sismo (EC2 / EC7 / NCSE-02)

> **PROPUESTA — pendiente de verificación QA independiente y firma de JM. Versión de núcleo no anclada (versions.lock=0.0.0).**

- **Rol:** build (producción). QA la ejecuta un agente independiente con su propio oráculo.
- **Norma:** EN 1992-1-1 (EC2, muros §12/§5.8, bielas-tirantes §6.5), EN 1997-1 (EC7, pilotes), NCSE-02/EC8 (sismo). Materiales: HA-30 (γc=1,5), B500S (γs=1,15). Geotecnia: doc `04`.
- **Fecha:** 2026-06-24. **Restricción:** Python puro + fórmulas EC; reglas EC2 muro de `laminas/ec2_muro.py` y bielas-tirantes de `bielas-tirantes/ec2_strut_tie.py`.

---

## 1. Idealización desde el IFC

| Elemento | Geometría (IFC) | Material |
|---|---|---|
| **Muro NC-Lab** | planta ≈ 2,40×2,40 m (perimetral con hueco), e=0,30, **H=15 m** (#3582) | HA-30 |
| **Muro NC-Vest** | planta 3,20×7,0 m (con 2 huecos), e=0,30, **H=15 m** (#3605) | HA-30 |
| **Encepado NC-Vest** | 3,20×7,0 m planta, **canto 1,5 m** (Z −3,0→−1,5), 6 pilotes | HA-30 |
| **Encepado NC-Lab** | 2,40×3,0 m planta, **canto 1,2 m** (Z −2,7→−1,5), 4 pilotes | HA-30 |
| **Pilotes D650** | Ø0,65 m, **L=7,0 m** (Z −8,5→−1,5), 6 ud (NC-Vest) | HA-30, BORED |
| **Pilotes D450** | Ø0,45 m, **L=7,0 m**, 4 ud (NC-Lab) | HA-30, BORED |

Datum (doc 04): cota cim. −1,5 = +152 msnm; UG2 −1,5→−5,5; **UG3 (portante) desde −5,5**; puntas −8,5 → empotramiento ≈ **3,0 m en UG3**.

---

## 2. Camino de cargas vertical hasta la cimentación (envolvente ELU)

El núcleo lateral (Cajón O + Cercha E + Alma C + muros) recibe la práctica totalidad de la carga gravitatoria (forjados cassette en voladizo descargan en el núcleo). Estimación de la **carga vertical ELU total** que baja a los muros y de ahí a los pilotes:

- Superficie de forjado servida por planta ≈ longitud del cajón × vuelo medio ≈ 40,86 × 6,3 ≈ 257 m²/planta.
- Carga ELU forjado oficinas: 6,60 kN/m² (ver doc 06 §3). Plantas P1–P3 + altillo + cubierta (cub. menos): ≈ 4 plantas equivalentes.
- N_forjados ≈ 6,60 · 257 · 4 ≈ **6.785 kN**.
- PP muros HA (2 muros, perímetro ≈ (2,4·4 + (3,2+7)·2)·0,30·15·25): NC-Lab ≈ 9,6·0,30·15·25=1.080 kN; NC-Vest ≈ 20,4·0,30·15·25... (perímetro real con huecos ≈ 17 m) ≈ 17·0,30·15·25=1.913 kN. PP muros ≈ **3.000 kN** → ELU ·1,35 ≈ 4.050 kN.
- PP acero celosías (≈ 35 t) ≈ 343 kN ·1,35 ≈ 463 kN.
- PP encepados (Vest 3,2·7·1,5·25=840; Lab 2,4·3·1,2·25=216) ≈ 1.056 kN ·1,35 ≈ 1.426 kN.

**N_Ed,total cimentación ≈ 6.785 + 4.050 + 463 + 1.426 ≈ 12.700 kN.**

Reparto entre los dos núcleos (NC-Vest mayor, ≈ 65 %; NC-Lab ≈ 35 %, por superficie de muro y nº de pilotes):
- **NC-Vest (6 D650): N_Ed ≈ 8.300 kN.**
- **NC-Lab (4 D450): N_Ed ≈ 4.400 kN.**

> **Supuesto S-D1:** reparto por superficie tributaria de núcleo; la QA debe afinar con el reparto real de reacciones de la celosía sobre cada muro.

---

## 3. Subsistema D — Muros HA-30 (EC2 §12.6.5.2 + §5.8)

Por metro de muro (b=1,0 m, t=0,30 m, H=15 m, fck=30 MPa). Longitud resistente de cada núcleo:
- NC-Vest: longitud de muro en compresión ≈ perímetro eficaz ≈ 17 m → N_Ed/m = 8.300/17 = **488 kN/m**.
- NC-Lab: ≈ 9,6 m → N_Ed/m = 4.400/9,6 = **458 kN/m**.

**EC2 §12.6.5.2 (método simplificado, ec2_muro.comprobar_compresion):**
- f_cd = 30/1,5 = 20 MPa; A_c = 1,0·0,30 = 0,30 m²; i = t/√12 = 0,0866 m.
- l_0 = β·H. Muro arriostrado por forjados cada planta → **altura libre por planta H_planta ≈ 3,08 m**, β=1,0 (arriostrado top/bottom) → l_0 = 3,08 m. **(No 15 m: el muro está coaccionado por los 4 forjados.)**
- λ = l_0/i = 3,08/0,0866 = 35,6.
- n = N_Ed/(A_c·f_cd) = 488e3/(0,30·20e6) = 0,081 → λ_lim = 20·0,7·1,1·0,7/√0,081 = 10,78/0,285 = **37,8** → λ=35,6 < 37,8 → **no esbelto** (justo).
- Excentricidades: M fuera de plano pequeño (muro de núcleo, carga ≈ centrada). e0≈0,02 m (viento/excentricidad de forjado), e_i = l_0/400 = 0,0077 m → e_tot ≈ 0,028 m.
- Φ = min(1,14·(1−2·0,028/0,30) − 0,02·3,08/0,30 ; 1−2·0,028/0,30) = min(1,14·0,813 − 0,205 ; 0,813) = min(0,722 ; 0,813) = **0,722**.
- N_Rd = b·t·f_cd·Φ = 1,0·0,30·20e6·0,722 = **4.332 kN/m**.
- **u = 488/4.332 = 0,11 ✔** (NC-Vest). NC-Lab: u = 458/4.332 = 0,11 ✔.

**Cortante en plano (sismo/viento lateral) — comprobación:** ver §5 (sismo). Los muros tienen amplísima reserva a compresión; gobierna el esfuerzo rasante por acción horizontal.

**Armadura mínima (§9.6):** A_s,v,min = 0,002·A_c = 6,0 cm²/m (3,0 cm²/m por cara); A_s,h,min = max(0,25·A_s,v ; 0,001·A_c) = 3,0 cm²/m. → **Ø12@375 mm por cara (vertical) + Ø10@250 (horizontal)** cubre el mínimo. La compresión no exige más.

---

## 4. Subsistema E — Cimentación profunda

### 4.1 Pilotes — capacidad geotécnica (EC7, datos SOCOTEC doc 04, FS ya aplicado)

Capacidad admisible por pilote (punta en UG3 + fuste en UG2 4 m + UG3 ≈ 3 m):

**D650 (A_punta=0,332 m², perímetro 2,04 m):**
- Punta UG3 (con empotramiento <6D → promedio de zona, doc 04): R_p ≈ **1.290 kN** (orientativo doc 04).
- Fuste: UG2 (62 kPa·2,04·4=506 kN) + UG3 (98 kPa·2,04·3=600 kN) = **1.106 kN**.
- **R_adm,D650 ≈ 1.290 + 1.106 ≈ 2.396 kN** (admisible, FS incluido).

**D450 (A_punta=0,159 m², perímetro 1,41 m):**
- Punta UG3: ≈ **615 kN** (doc 04).
- Fuste: UG2 (62·1,41·4=350) + UG3 (98·1,41·3=415) = **765 kN**.
- **R_adm,D450 ≈ 615 + 765 ≈ 1.380 kN.**

**Demanda por pilote (carga en servicio ≈ N_ELU/1,4 para comparar con admisible):**
- NC-Vest: 6 D650, N_servicio ≈ 8.300/1,4 = 5.929 kN / 6 = **988 kN/pilote** → u = 988/2.396 = **0,41 ✔**.
- NC-Lab: 4 D450, N_servicio ≈ 4.400/1,4 = 3.143 kN / 4 = **786 kN/pilote** → u = 786/1.380 = **0,57 ✔**.

> **Nota:** las capacidades del doc 04 son **admisibles (FS aplicado)**, por eso se comparan con cargas de servicio (N_ELU/≈1,4). Si QA trabaja en formato EC7 con R_d y γ parciales, recalcular. **[confirmar AN]** el formato (admisible vs. parcial).

**Pilote como elemento estructural (EC2, axil + cabeceo lateral):** D650 HA-30, A=0,332 m², N_c,Rd=A·f_cd+A_s·f_yd. Solo hormigón: 0,332·20e6=6.640 kN ≫ 988 kN → **u_estructural=0,15 ✔** (con armadura mínima 0,4 % = 13,3 cm²). D450: 0,159·20e6=3.180 kN ≫ 786 → u=0,25 ✔.

### 4.2 Encepados — modelo de bielas y tirantes (EC2 §6.5)

**Encepado NC-Lab (4 D450, planta 2,40×3,0, canto h=1,2 m):** modelo de 4 pilotes → se descompone en dos celosías de 2 pilotes. Separación entre ejes de pilotes a=1,5 m (X: 7,0/8,2; Y: 0,75/2,25 → a≈1,5 m). N_Ed por par ≈ 4.400/2 = 2.200 kN.
- d = h − recubr. − Ø/2 ≈ 1,2 − 0,05 − 0,02 = 1,13 m; z = 0,9·d = 1,02 m.
- θ = atan(z/(a/2)) = atan(1,02/0,75) = 53,7°.
- R_pilote = 2.200/2 = 1.100 kN; **Tirante T = R/tanθ = 1.100/1,36 = 809 kN**; Biela C = R/sinθ = 1.100/0,806 = 1.365 kN.
- **Tirante:** A_s = T/f_yd = 809e3/(500e6/1,15) = 809e3/434,8e6 = 18,6e-4 m² = **18,6 cm²** → 6Ø20 (18,8 cm²) ✔.
- **Biela:** σ_Rd,max = 0,6·ν'·f_cd; ν'=1−30/250=0,88 → σ_Rd=0,6·0,88·20=10,56 MPa. Ancho biela sobre pilote w=D·sinθ+u·cosθ=0,45·0,806+0,14·0,592=0,446 m; σ_c=C/(b·w), b=ancho encepado por par ≈ 1,2 m → σ_c=1.365e3/(1,2·0,446)=2,55 MPa → **u=2,55/10,56=0,24 ✔**.
- **Nudo CCT sobre pilote:** σ=R/A_pilote=1.100e3/0,159=6,92 MPa; σ_Rd,CCT=0,85·0,88·20=14,96 MPa → **u=0,46 ✔**.

**Encepado NC-Vest (6 D650, planta 3,20×7,0, canto h=1,5 m):** 3 filas de 2 pilotes en Y; a_X=1,6 m (6,8/8,4). N_Ed por par ≈ 8.300/3 = 2.767 kN.
- d=1,5−0,05−0,025=1,425 m; z=1,28 m; θ=atan(1,28/0,8)=58,0°.
- R=1.383 kN; **T=R/tanθ=1.383/1,60=864 kN**; C=R/sinθ=1.383/0,848=1.631 kN.
- **Tirante:** A_s=864e3/434,8e6=19,9 cm² → 7Ø20 (22,0 cm²) ✔ por par; armar malla en ambas direcciones.
- **Biela:** w=0,65·0,848+0,14·0,530=0,626 m; b por par ≈ 2,33 m → σ_c=1.631e3/(2,33·0,626)=1,12 MPa → u=0,11 ✔.
- **Nudo CCT:** σ=1.383e3/0,332=4,17 MPa → u=4,17/14,96=0,28 ✔.

---

## 5. Subsistema F — Sismo (NCSE-02, ac=0,046 g, estático equivalente)

**Acción sísmica (NCSE-02 §3.4, estático equivalente):**
- Peso sísmico W = G + Σψ2·Q ≈ carga cuasipermanente. W ≈ (PP+muerta)·superficie·plantas + PP estructura ≈ (2,67·257·4) + 3.000 + 343 = 2.745 + 3.343 = **6.088 kN** ≈ G; +ψ2·Q (0,3·2,0·257·4=617 kN) → **W ≈ 6.700 kN**.
- Cortante basal (espectro NCSE-02, edificio rígido por muros+celosía, ductilidad baja μ=2): coef. sísmico c ≈ ac·(α/μ). Con ac=0,046g, α(T) máx≈2,5, μ=2 → c ≈ 0,046·2,5/2 = **0,0575**. Conservador sin reducir por μ: c=ac·α=0,115.
- **V_basal = c·W = 0,0575·6.700 = 385 kN** (con μ=2) ó 770 kN (sin ductilidad).

**Reparto a los muros (los muros HA + celosías toman el cortante):**
- Los dos muros HA en plano tienen inercia enorme; toman ≈ todo V. V_muro ≈ 385/2 = 193 kN (o 385 kN sin μ).
- **Cortante en plano del muro:** v_Ed = V/(l·t). NC-Vest (l≈7,0 m, t=0,30): v_Ed=385e3/(7,0·0,30)=183 kPa = 0,18 MPa. Resistencia a cortante del muro HA (V_Rd,c sin armar + armadura): con cuantía mínima horizontal 3,0 cm²/m, V_Rd,s = 0,9·d·(A_sw/s)·f_yd·cotθ ≫ V_Ed. **u ≈ 0,15 ✔** (amplia reserva).
- **Vuelco/momento sísmico en la base:** M = V·h_eq ≈ 385·10 = 3.850 kN·m; resistido por el par de pilotes y el peso → tracción adicional en pilote a barlovento ≈ M/(a·n) modesta frente a la compresión (988 kN). Sin tracción neta en pilotes. ✔

**Deriva (ELS sísmico):** estructura muy rígida (muros 15 m + celosía de gran canto) → deriva ≪ H/500. No gobierna.

**Conclusión sismo:** con ac=0,046 g, **el sismo NO gobierna**; los muros HA y las celosías tienen reserva amplia (u≤0,15). Confirma la previsión del doc 02 (viento y gravedad gobiernan). Se deja documentada la comprobación.

> **Supuesto S-F1:** análisis estático equivalente simplificado (NCSE-02), edificio asimilado a rígido con muros+celosía. Dada la **irregularidad** (voladizos, masas excéntricas, doc 02 §5), la QA debería confirmar con un **modal espectral** que capte la torsión por excentricidad. El bajo ac hace improbable que cambie el veredicto, pero la torsión debe verificarse.

---

## 6. Tabla de aprovechamientos — Subsistemas D, E, F

| Elemento | Comprobación | Ed | Rd | **u** | Veredicto | Art. |
|---|---|---|---|---|---|---|
| Muro NC-Vest | Flexocompresión (esbeltez) | 488 kN/m | 4.332 | **0,11** | ✔ | EC2 12.6.5.2 |
| Muro NC-Lab | Flexocompresión | 458 kN/m | 4.332 | 0,11 | ✔ | EC2 12.6.5.2 |
| Muro NC-Vest | Cortante sísmico en plano | 0,18 MPa | ~1,2 | 0,15 | ✔ | EC2 6.2 / NCSE |
| Pilote D650 | Geotécnico (EC7) | 988 kN | 2.396 | **0,41** | ✔ | EC7 |
| Pilote D450 | Geotécnico (EC7) | 786 kN | 1.380 | **0,57** | ✔ | EC7 |
| Pilote D650 | Estructural (EC2 axil) | 988 kN | 6.640 | 0,15 | ✔ | EC2 6.1 |
| Encepado NC-Lab | Tirante (bielas-tir.) | 809 kN | →18,6 cm² | (6Ø20) | ✔ | EC2 6.5 |
| Encepado NC-Lab | Biela / Nudo CCT | — | — | 0,24 / 0,46 | ✔ | EC2 6.5 |
| Encepado NC-Vest | Tirante | 864 kN | →19,9 cm² | (7Ø20) | ✔ | EC2 6.5 |
| Encepado NC-Vest | Biela / Nudo CCT | — | — | 0,11 / 0,28 | ✔ | EC2 6.5 |
| Global | Sismo (cortante basal) | 385 kN | — | ≤0,15 | ✔ | NCSE-02 |

**Aprovechamiento máximo (D/E/F): u ≈ 0,57 (pilote D450, geotécnico).**

---

## 7. Evidencia para QA

```
elementos: muros NC-Vest/NC-Lab (HA-30 e=0,30), 6 D650 + 4 D450, 2 encepados, sismo
entrada:   IFC #3582/#3605 (muros), #3686/#3699 (encepados), #3703.. (pilotes); doc 04 geotecnia
version:   versions.lock=0.0.0 (NO ANCLADA)
norma:     EC2 12.6.5.2 (muro), EC2 6.5 (encepado bielas-tirantes), EC7 (pilote), NCSE-02 (sismo)
metodo:    camino de cargas por areas tributarias + ec2_muro.py + ec2_strut_tie.py (fórmulas);
           SIN PyNite/scipy (entorno); capacidad pilote = admisible SOCOTEC (FS aplicado)
resultado: u_max~0,57 (pilote D450). Sismo no gobierna (u<=0,15)
oraculo:   QA: golden DEC-E1 (encepado 6 pilotes bielas-tirantes, analítico) y DEC-E2 (pilote EC7);
           reparto de reacciones del nucleo a confirmar con modelo global
SUPUESTOS: S-D1 reparto 65/35 Vest/Lab; S-F1 estatico equivalente (falta modal/torsion);
           formato EC7 admisible vs parcial [confirmar AN]
```

## 8. Puntos para JM
1. **Formato geotécnico (EC7):** confirmar si se usan capacidades **admisibles** (FS, doc 04) o **resistencias de diseño con γ parciales**. Afecta el aprovechamiento del pilote.
2. **S-D1:** reparto de carga vertical Vest/Lab — afinar con reacciones reales del núcleo.
3. **S-F1:** sismo por estático equivalente; dado el edificio irregular, confirmar con **modal espectral** que la **torsión** no penalice (aunque el bajo ac lo hace improbable).
4. Armaduras propuestas (encepados 6Ø20/7Ø20; muros malla mínima) son de predimensionado: detallar anclajes y armado de borde.

---
**Aviso:** PREDIMENSIONADO. Debe revisarlo y firmarlo un técnico competente. Pendiente de verificación QA independiente + firma de JM.
