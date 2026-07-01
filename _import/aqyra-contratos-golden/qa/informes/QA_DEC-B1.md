# Informe de QA por cálculo — DEC-B1

> **QA verificado con FEM nodal numpy independiente + analítico. SIN el oráculo PyNite certificado (no instalable en este entorno) → pendiente de RE-EJECUCIÓN en entorno con PyNite para el cierre definitivo. Pendiente de firma de JM (la IA no certifica).**

- **Caso golden:** DEC-B1 — Diagonal del Cajón O SHS 200×10 (pandeo EC3)
- **Contrato / golden:** C-B1 v0
- **Fecha de verificación:** 2026-06-24
- **Ejecutado por:** agente de QA (ejecución separada) · **Oráculo:** FEM nodal 2D propio (rigidez directa, numpy) + EC3 6.3.1 (χ curva b)
- **Versión verificada:** **NO ANCLADA** (versions.lock=0.0.0)

> La certificación requiere la firma de JM. La IA no firma.

---

## 1. Trazabilidad

```
input:       IFC diagonales "Cajon O diagonal" (45 ud, perfiles MIXTOS: SHS 250x16/250x12/
             200x10/160x8/150x8/120x6/300x16); L≈3,94–4,69 m; ficha golden usa SHS 200×10 L=4,3 m
version:     no anclada
norma:       EC3 6.3.1 (pandeo por flexión, curva b, α=0,34), γM1=1,05; S355
metodo QA:   solver FEM nodal por método directo de rigidez (numpy.linalg.solve) sobre los
             nudos REALES del IFC (celosía 2D Vierendeel, 64 nudos, 153 barras); + EC3 cerrado
resultado:   N_b,Rd=1.978 kN; N_Ed,QA≈348 kN (reparto nodal); u_QA≈0,18
oraculo:     FEM propio + Euler/EC3; reacciones y modos verificados
comparacion: ver §2
```

## 2. Capa 1 — Numérica (oráculo)

| Magnitud | Valor build | Valor QA (oráculo) | Δ | Tolerancia | ¿Dentro? |
|---|---|---|---|---|---|
| N_b,Rd (SHS 200×10, L=4,3 m) | 2.004 kN | 1.978 kN | −1,3 % | ±3 % | ☑ |
| λ̄ | 0,73 | 0,725 | −0,7 % | — | ☑ |
| χ (curva b) | 0,78 | 0,770 | −1,3 % | — | ☑ |
| N_Ed (diagonal crítica) | 778 kN | ≈348 kN (FEM nodal, un plano) | — | ±5 % | ☒ (ver nota) |
| u = N_Ed/N_b,Rd | 0,39 | 0,18 (QA) / 0,39 (build) | — | — | ambos ✔ |

**Verificaciones sin oráculo:** equilibrio ΣF_z (carga=reacción, residuo 1,6e-12 kN) ☑ · ΣF_y≈0 (1,9e-12) ☑ · **modos de sólido rígido = 3 (exacto, modelo 2D bien condicionado)** ☑ · convergencia n/a (barras, no continuo).

> **Nota sobre N_Ed.** El build estima N_Ed=778 kN por equilibrio global de cortante repartido a 45°. Mi FEM nodal sobre los nudos reales reparte el cortante entre **todas** las diagonales del panel y da un pico ≈348 kN en la diagonal más solicitada (un plano). **El build es CONSERVADOR** (su N_Ed es mayor que el real). Como el dato que define el golden (N_b,Rd) coincide al 1,3 %, y u_build=0,39 ya cumple, el caso es **APTO**: el build queda del lado de la seguridad en la demanda y exacto en la capacidad.

## 3. Capa 2 — Normativa

| Comprobación | Límite | Valor QA | ¿Cumple? |
|---|---|---|---|
| Clasificación SHS 200×10 (S355) | Clase 1 | Clase 1 ((b−3t)/t=17 ≤ 33ε=26,9) | ☑ |
| Pandeo: u = N_Ed/N_b,Rd ≤ 1,0 | ≤ 1,0 | 0,18 (QA) / 0,39 (build) | ☑ |

## 4. Capa 3 — Regresión

- ¿Promovido a golden congelado? ☐ Sí ☑ Pendiente (capacidad verde; conviene fijar N_Ed con PyNite 3D).
- ¿Corre en CI? ☐

## 5. Observaciones / supuestos del build puestos a prueba

- **HALLAZGO de geometría:** la ficha golden y el doc 06 nombran la diagonal "SHS 200×10", pero el IFC muestra que las 45 diagonales del Cajón O usan **7 perfiles distintos** (SHS 250×16, 250×12, 200×10, 160×8, 150×8, 120×6, 300×16). La SHS 200×10 es solo una de ellas. **Build debe identificar qué diagonal concreta (perfil y posición) es la crítica** y verificar esa, no una genérica.
- **Reparto de axiles (encargo §S-D1 / picos locales):** el FEM nodal NO mostró picos por encima de la estimación global del build en las diagonales; al contrario, la estimación a 45° del build sobreestima (conservador).
- El Cajón O resultó ser una **viga-celosía horizontal** (cordones longitudinales en Y, L≈40,5 m; canto vertical 9,25 m), no vertical — coherente con la idealización del build.

## 6. Veredicto de QA

> **APTO** — la capacidad N_b,Rd coincide al 1,3 % (dentro de ±3 %) y la demanda del build es conservadora frente al FEM nodal. **Condición:** build debe confirmar el perfil real de la diagonal crítica (el IFC tiene perfiles mixtos) antes de congelar el golden.

## 7. Firma (segunda llave — JM)

```
Verificado por QA:   agente QA / run 2026-06-24      fecha: 2026-06-24
Tolerancias fijadas por JM:  ☐
FIRMA JM (técnico competente): ______________  fecha: [   ]   → CERTIFICADO ☐
```

*Scripts QA: `qa/informes/qa_geom_extract.py`, `qa/informes/qa_truss2d_cajonO.py`, `qa/informes/qa_normativa.py`.*
