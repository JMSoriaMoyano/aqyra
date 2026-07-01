# Decopak HQ — Subsistema A: forjado CLT cassette (EC5)

> **PROPUESTA — pendiente de verificación QA independiente y firma de JM. Versión de núcleo no anclada (versions.lock=0.0.0).**

- **Rol:** build (producción). La QA la ejecuta un agente independiente con su propio oráculo.
- **Norma:** EN 1995-1-1 (EC5) + AN España; acciones EC0/EC1 (doc `02_bases_acciones_HIPOTESIS.md`, APROBADO).
- **Fecha:** 2026-06-24.
- **Restricción de entorno:** cálculo en Python puro + fórmulas EC documentadas (sin PyNite/ifcopenshell; ver `08_candidatos_golden.md` para el oráculo de QA). Geometría parseada del IFC por texto STEP.

---

## 1. Idealización desde el IFC

| Dato (IFC) | Valor | Entidad |
|---|---|---|
| Costillas «Costilla cassette» (JOIST) | 128 ud, perfil **IPE 160** (#1857) | IFCBEAM .JOIST. |
| Longitud de costilla (extrusión) | **6,21–6,55 m** (voladizo en X) | p. ej. #1859=6,21 m; #1868=6,379 m |
| Paso entre costillas (dir. Y) | **≈ 1,30 m** | placements #1863→#1872: ΔY=1,30 m |
| Cota de arranque | Z=5,75 (P1), y réplicas en P2/P3/PC | placements |
| Losas «Losa CLT cassette» (FLOOR) | 4 ud, sección genérica | IFCSLAB .FLOOR. (#2160, #2461, #2762, #3063) |
| Material | CLT fm,k=24 MPa, ρ≈480 kg/m³ (#30) | IfcMaterialProperties |

**Interpretación de ingeniería.** El conjunto **cassette CLT + costilla IPE 160** trabaja como **forjado nervado en voladizo transversal** de ≈ 6,2–6,5 m, que arranca del núcleo (celosías de acero) y vuela hacia la fachada. Las costillas (IPE 160) son el nervio metálico; la losa CLT actúa como tablero y reparte la carga a las costillas. Se idealiza la costilla más larga (L=6,55 m) como **ménsula (empotrada en el núcleo, libre en punta)**, hipótesis del lado de la seguridad para flecha y momento de empotramiento (es el corazón del caso: el voladizo ligero).

> **Supuesto S-A1:** se adopta el **modelo de viga mixta no conectada conservador** = la costilla IPE 160 resiste sola la flexión del nervio (la losa CLT colabora a favor de seguridad; no se contabiliza la sección mixta acero-CLT por falta de detalle de conexión en el IFC). El ancho tributario por costilla = paso = 1,30 m.

---

## 2. Acciones sobre el nervio (ancho tributario b = 1,30 m)

Cargas por m² (doc 02) y carga lineal sobre la costilla (q = carga·b):

| Acción | q [kN/m²] | sobre nervio [kN/m] |
|---|---|---|
| PP losa CLT (canto ≈ 0,14 m × 4,8 kN/m³) | 0,67 | 0,87 |
| PP costilla IPE 160 (15,8 kg/m) | — | 0,16 |
| Carga muerta (solado, techo, instalac.) | 2,0 | 2,60 |
| **G (permanente) total** | — | **g = 3,63 kN/m** |
| Sobrecarga uso oficinas B | 2,0 | **q_B = 2,60 kN/m** |

(En zonas de cubierta H qk=0,4 → menos exigente; gobierna la planta de oficinas B.)

**Combinación ELU (EC0 AN):** w_d = 1,35·g + 1,50·q_B = 1,35·3,63 + 1,50·2,60 = **8,80 kN/m**.
**Combinación ELS característica:** w_k = g + q_B = 6,23 kN/m. **ELS cuasipermanente:** g + ψ2·q = 3,63 + 0,3·2,60 = 4,41 kN/m.

---

## 3. Esfuerzos en la ménsula (L = 6,55 m, voladizo)

Solución cerrada de ménsula con carga uniforme (oráculo analítico para QA):
- Momento de empotramiento: **M_Ed = w·L²/2 = 8,80·6,55²/2 = 188,8 kN·m**
- Cortante en empotramiento: **V_Ed = w·L = 8,80·6,55 = 57,6 kN**
- Flecha en punta (ELS car.): δ = w·L⁴/(8·E·I)

---

## 4. Comprobación EC5 de la costilla IPE 160 (acero, EC3) y del cassette CLT (EC5)

> **Aclaración normativa.** El nervio resistente es **acero IPE 160** (no madera): su comprobación es **EC3**. La **losa CLT** se comprueba a flexión transversal local entre nervios (EC5) y a vibración global (EC5/EC1). El material «CLT fm,k=24» del IFC aplica a la losa, no al nervio.

### 4.1 Nervio IPE 160 (EC3, S355) — geometría del IFC (#1857: b=82, h=160, tw=5, tf=7,4 mm)

Propiedades (geometría de placas, perfiles_db.from_ishape_geometry):
- A = 2·0,082·0,0074 + (0,16−2·0,0074)·0,005 = 1,949e-3 m²
- I_y = (0,082·0,16³)/12 − (0,082−0,005)·0,1452³/12 = 8,71e-6 m⁴ → catálogo IPE 160 ≈ **8,69e-6 m⁴** ✔
- W_pl,y ≈ b·tf·(h−tf) + tw·hw²/4 = 0,082·0,0074·0,1526 + 0,005·0,1452²/4 = **1,236e-4 m³** (catálogo 123,9 cm³ ✔)
- f_yd = 355/1,05 = 338,1 MPa (γM0=1,05, AN)

**Flexión:** M_c,Rd = W_pl·f_yd = 1,236e-4 · 338,1e6 = **41,8 kN·m**.
→ **u_M = 188,8 / 41,8 = 4,52 ❌ NO CUMPLE** con una sola IPE 160 trabajando aislada en ménsula de 6,55 m.

**Diagnóstico de ingeniería.** El resultado confirma que **la costilla IPE 160 NO resiste sola** un voladizo de 6,55 m: el modelo de "costilla biempotrada/ménsula aislada" no es el correcto. La geometría del IFC indica que **el voladizo real lo resuelve la celosía Cajón O** (canto ≈ 3,08 m entre cordones), y la costilla cassette es un **nervio de forjado entre apoyos del entramado**, no la ménsula completa. Reinterpretación:

> **Supuesto S-A2 (idealización corregida):** la costilla cassette es un **nervio biapoyado / con pequeño vuelo** sobre la retícula de la celosía y los dinteles de conexión (apoyos cada ≈ 2,35–3,86 m, según dinteles O/E). El gran voladizo de fachada lo materializa la **celosía Cajón O** (subsistema B), no la costilla aislada.

### 4.2 Costilla como nervio biapoyado L = 3,86 m (luz entre dinteles de conexión O)

- M_Ed = w·L²/8 = 8,80·3,86²/8 = **16,4 kN·m** → **u_M = 16,4/41,8 = 0,39 ✔**
- V_Ed = w·L/2 = 8,80·3,86/2 = 17,0 kN; V_pl,Rd = A_vz·f_yd/√3. A_vz ≈ A − 2·b·tf + (tw+2r)·tf ≈ 9,66e-4 m² → V_pl,Rd = 9,66e-4·338,1e6/√3 = 188,6 kN → **u_V = 0,09 ✔**
- Flecha ELS car. δ = 5·w_k·L⁴/(384·E·I) = 5·6,23e3·3,86⁴/(384·210e9·8,69e-6) = 0,0026 m = **2,6 mm** ; límite L/300 = 12,9 mm → **u_δ = 0,20 ✔**

### 4.3 Tablero CLT entre nervios (EC5, flexión transversal local, luz 1,30 m)

- Carga ELU sobre 1 m de ancho transversal: w = 1,35·(0,67+2,0)+1,50·2,0 = 6,60 kN/m².
- M_Ed (continua sobre nervios, ≈ w·s²/10) = 6,60·1,30²/10 = **1,12 kN·m/m**.
- CLT 5 capas ≈ 100 mm, capa exterior 20 mm en dirección porte: W ≈ b·h²/6 con h_ef ≈ 0,10 → W=1000·100²/6=1,67e5 mm³/m=1,67e-4 m³/m.
- f_m,d = k_mod·f_m,k/γM = 0,8·24/1,25 = 15,4 MPa (clase servicio 1, carga media duración).
- σ_m,d = 1,12e3/1,67e-4 = 6,7 MPa → **u = 6,7/15,4 = 0,44 ✔**

### 4.4 Vibración del forjado (EC5 §7.3 / confort)

- Frecuencia propia del nervio biapoyado L=3,86 m: f₁ = (π/2)·√(EI/(m·L⁴)).
- m (masa permanente + cuasiperm.) ≈ 4,41 kN/m /9,81 = 0,45 kN·s²/m² → 450 kg/m sobre 1,30 m ancho.
- f₁ = (π/2)·√(210e9·8,69e-6/(346·3,86⁴)) ≈ (1,571)·√(1825/76700)=1,571·0,154 = **8,5 Hz ≥ 8 Hz ✔** (criterio EC5).
  > Marginal; **[confirmar AN]** y verificar con masa real del cassette y rigidez transversal de la losa CLT.

---

## 5. Tabla de aprovechamientos — Subsistema A

| Elemento | Comprobación | Ed | Rd | u | Veredicto | Art. |
|---|---|---|---|---|---|---|
| Costilla IPE 160 (ménsula 6,55 m, **modelo descartado**) | Flexión | 188,8 kN·m | 41,8 | 4,52 | ❌ (no es el modelo) | EC3 6.2.5 |
| Costilla IPE 160 (nervio 3,86 m, **modelo adoptado**) | Flexión | 16,4 kN·m | 41,8 | **0,39** | ✔ | EC3 6.2.5 |
| Costilla IPE 160 | Cortante | 17,0 kN | 188,6 | 0,09 | ✔ | EC3 6.2.6 |
| Costilla IPE 160 | Flecha L/300 | 2,6 mm | 12,9 | 0,20 | ✔ | EC0 7.4 |
| Tablero CLT | Flexión local | 1,12 kN·m/m | 2,57 | 0,44 | ✔ | EC5 6.1.6 |
| Forjado CLT | Vibración f₁ | 8,5 Hz | 8,0 | ~0,94 | ✔ (marginal) | EC5 7.3 |

**Aprovechamiento máximo del subsistema (modelo adoptado): u ≈ 0,94 (vibración).**

---

## 6. Evidencia para QA

```
elemento:  Costilla cassette IPE 160 (JOIST) + losa CLT
entrada:   IFC #1857 (IPE 160), L_extr 6,21-6,55 m, paso 1,30 m; cargas doc 02 (B oficinas)
version:   versions.lock=0.0.0 (NO ANCLADA)
norma:     EC3 6.2 (nervio acero), EC5 6.1.6 + 7.3 (tablero CLT, vibración), EC0 (combinaciones)
metodo:    fórmulas cerradas ménsula/biapoyado (sin solver: entorno sin PyNite)
resultado: nervio biapoyado L=3,86 m -> u_M=0,39; vibración f1=8,5 Hz (u~0,94)
oraculo:   analítico ménsula (M=wL²/2; δ=wL⁴/8EI) y biapoyado (M=wL²/8; δ=5wL⁴/384EI);
           QA debe contrastar con PyNite + EC5 (golden DEC-A1)
HALLAZGO:  el voladizo de 6,5 m NO lo resiste la costilla aislada -> lo resuelve la
           celosía Cajón O (subsistema B). Decisión de modelo a confirmar por JM.
```

## 7. Puntos para JM
1. **Confirmar el modelo de voladizo (S-A2):** el gran vuelo lo toma la celosía Cajón O y la costilla es nervio entre apoyos. Verificar con los planos de detalle del cassette.
2. **Vibración marginal (8,5 Hz):** confirmar masa real del cassette CLT y rigidez de la losa; si f₁ < 8 Hz, evaluar criterio de aceleración o aumentar canto.
3. Límite de flecha de voladizo CLT (doc 02 §8 lo dejó [CONFIRMAR JM]).

---
**Aviso:** documento de PREDIMENSIONADO. Debe revisarlo y firmarlo un técnico competente. Pendiente de verificación QA independiente + firma de JM.
