> **Reconciliación de numeración (2026-06-27, firmada por JM).** El contrato de interfaz **C5 canónico** (el que valida la golden firmada) vive en la zona protegida: `Estructurando 2.0/contratos-golden/contratos/C5_motor-fem.md`. **Este fichero NO es un duplicado a archivar:** es la **especificación de ingeniería detallada** del motor (FEM-2, §1–§8) que consumen los hilos de desarrollo del motor (PT7.*); se conserva íntegro y activo. Pendiente (tarea del hilo motor-fem, no de esta reconciliación): verificar que la interfaz aquí descrita y la del contrato canónico no han divergido y, si procede, dejar una sola como fuente de la interfaz.

# C5 — Contrato del Motor FEM (modelo de análisis + API del solver)

**Núcleo transversal del ecosistema · PT 7.0–7.1 (Ola 7).** Define cómo cualquier disciplina
(puentes, estructuras singulares, tensoestructuras, y por migración estructuras de
edificación) **pide cálculo de elementos finitos** de forma estable y agnóstica a la
disciplina. Lo implementa el plugin **`motor-fem`** (núcleo `numpy`/`scipy`). Estado a
24/06/2026 · **FEM-2** (estático lineal + **modal** + **cargas móviles/líneas de influencia**
+ **lámina curva MITC4** + **rigidizador con offset rígido** + **pared delgada** Bredt/shear lag;
v0.3.0, PT 7.4: módulos aditivos sin regresión FEM-0/1, benchmarks NAFEMS ±5 %).

> Principio: el **modelo de análisis FEM** *extiende* el **modelo neutro estructural** (C1 §2)
> añadiendo **solo claves nuevas** (modelo hermano, retrocompatible). El núcleo **no conoce
> normativa ni tipologías**: recibe geometría+materiales+cargas y devuelve esfuerzos,
> desplazamientos y reacciones. La normativa (EC2/EC3/EC4/IAP-11…) vive en los verticales.

> Todo cálculo es de **predimensionado/asistencia**; revisar y firmar por técnico competente
> (ICCP). NDP marcados `[confirmar AN]`.

---

## 1. Frontera con los demás contratos

- **C1 (`iso19650-openbim`):** lectura/escritura IFC y **modelo neutro físico/estructural**.
  No cambia. El FEM **consume** el modelo neutro estructural (C1 §2).
- **C5 (`motor-fem`, este contrato):** **mallado + ensamblaje + solver**. Toma el modelo
  neutro estructural, lo **malla** y lo **resuelve**. Es donde migra, por *strangler*, la
  mecánica hoy en PyNite (en `motor-calculo-estructural`).
- **`motor-calculo-estructural`:** pasa a ser **consumidor** del núcleo (sus verticales
  llamarán a C5 en vez de a PyNite, sin cambiar su normativa). **No se migra en este PT**: el
  núcleo se construye y valida en paralelo.
- **`puentes` (Ola 7, nuevo):** primer consumidor pleno de C5 (PT 7.1+).

---

## 2. Modelo de análisis FEM (extiende C1 §2)

Sobre el modelo neutro estructural (bloques `unidades`/`materiales`/`secciones`/`nodos`/
`barras`/`superficies`/`cargas`), C5 **añade** (solo claves nuevas):

```jsonc
{
  // ... (todo el modelo neutro C1 §2: unidades SI, materiales, secciones, nodos, barras) ...

  "elementos": {                 // malla FEM explícita (la genera el mallador)
    "E1": { "tipo": "barra",  "nodos": ["N1","N2"], "seccion": "...", "material": "...",
            "releases": [false,...12], "rotation": 0.0 },
    "Q1": { "tipo": "lamina", "nodos": ["N1","N2","N3","N4"], "espesor": 0.2, "material": "..." }
  },

  "laminados": {                 // [gancho] capas para lámina/mixto multicapa
    "L1": [ { "material": "...", "espesor":, "z": } ]
  },

  "nodos": {
    "N1": { "x":,"y":,"z":,
            "apoyo":   [DX,DY,DZ,RX,RY,RZ],     // booleanos (C1, invariable)
            "resorte": [kx,ky,kz,krx,kry,krz] } // NUEVO: resortes (suelo Winkler, apoyos)
  },

  "casos":        ["G","Q","V","N","T", ...],            // casos de carga
  "combinaciones": { "ELU": {"G":1.35,"Q":1.50}, ... },  // factores por caso (EC0/AN-ES)

  "cargas": [      // cargas de barra (lista raíz, C1) + tipos FEM:
    { "caso":"G", "barra":"E1", "tipo":"global_uniforme", "qz": -12000 },
    { "caso":"Q", "barra":"E1", "tipo":"lineal", "direccion":"Fy", "q1":, "q2":, "x1":, "x2": },
    { "caso":"Q", "barra":"E1", "tipo":"puntual", "direccion":"Fz", "P":, "x": },
    { "caso":"T", "barra":"E1", "tipo":"termica_axil", "alpha":, "dT": },
    { "caso":"T", "barra":"E1", "tipo":"termica_gradiente", "alpha":, "dT":, "h": }
  ],
  "superficies": [ { "esquinas":[...], "espesor":, "malla":, "material":,
                     "cargas":[ {"caso":"G","p":} ] } ],   // presión por superficie

  // --- FEM-1 (PT 7.1): IMPLEMENTADO ---
  "masas": {                // análisis modal: fuentes de masa (lumped)
    "nmodos": 6, "desde_peso_propio": true,
    "casos_masa": {"G": 1.0, "Q": 0.3},   // |Fz|/g de casos gravitatorios
    "nodales": { "N7": [mx,my,mz, Ix,Iy,Iz] } },
  "cargas_moviles": {       // movil: tren sobre un camino (líneas de influencia)
    "posiciones": 41,
    "objetivos": [ {"id":"M","tipo":"esfuerzo_barra","elem":"E5","comp":"My_j"} ],
    "lineas":   [ {"id":"carril1","camino":["N0", "..."],
                   "tren":{"axles":[{"P":300e3,"offset":0.0}],"udl":9e3}} ] },

  // --- ganchos reservados (FEM-3/4) ---
  "no_lineal": null         // 2.º orden / pandeo / cables-membranas (FEM-3/4)
}
```

**Convenciones invariables (heredadas de C1, imprescindibles para la no-regresión):**
- Ejes **globales** X,Y horizontales, **Z vertical**, gravedad −Z. **SI** (N, m).
- Apoyos: vector booleano de 6 GdL `[DX,DY,DZ,RX,RY,RZ]` (True = coacción).
- Barras: `Iy` = inercia **mayor**; placa: esfuerzos `[Mx,My,Mxy]` por unidad de ancho.
- Cargas en **dos colocaciones** (C1 §2): lista raíz para barras; anidadas en
  `superficies[].cargas` para presiones.

---

## 3. API del solver (estable, agnóstica)

```python
from resolver import resolver
res = resolver(modelo, analisis="estatico_lineal", combos=None)
```

- `modelo`: dict del modelo de análisis (§2) **o** un objeto `ModeloFEM` ya construido.
- `analisis`:
  - **`"estatico_lineal"`** — implementado (FEM-0).
  - **`"modal"`** — implementado (FEM-1, PT 7.1): frecuencias, modos y **masa participante**.
    Lee la clave `masas` (`desde_peso_propio`/`casos_masa`/`nodales`); masa **concentrada**
    (lumped); `scipy.sparse.linalg.eigsh` shift-invert (σ=0).
  - **`"movil"`** — implementado (FEM-1, PT 7.1): **líneas de influencia** (barrido de carga
    unidad reutilizando `splu(Kff)`) + **envolventes** por tren (tándem + UDL) con posiciones
    pésimas. Lee la clave `cargas_moviles` (`lineas`/`objetivos`/`tren`).
  - `"pandeo_lineal"`, `"no_lineal"` — **ganchos** reservados; lanzan `NotImplementedError`
    (FEM-3+).
- `combos`: `{nombre: {caso: factor}}`. Si `None` y el modelo declara `combinaciones`, se usan;
  si declara casos G/Q, se aplican las combinaciones EC0/AN-ES por defecto (ELU/ELS).

**Salida:**
```jsonc
{ "nodos": ["N1", ...],
  "combos": { "ELU": {
     "desplazamientos": { "N1": [dx,dy,dz,rx,ry,rz], ... },
     "reacciones":      { "N1": [Rx,Ry,Rz,Mx,My,Mz], ... },   // en nudos con apoyo
     "esfuerzos_barra": { "E1": { "axial_i","Vy_i","Vz_i","T_i","My_i","Mz_i",
                                  "axial_j","Vy_j","Vz_j","T_j","My_j","Mz_j",
                                  "N_i","N_j" } },              // esfuerzo interno (conv. PyNite)
     "esfuerzos_lamina": { "Q1": { "x","y","z","Mx","My","Mxy","Qx","Qy","Nx","Ny","Nxy" } },
     "equilibrio":      { "sumF_aplicada_N","sumF_reaccion_N","residuo_N","norma_residuo_N" }
  } } }
```

Esfuerzo de barra: convención de esfuerzo **interno** de PyNite —`axial(0)=axial_i`,
`N_i = -axial_i` (compresión negativa)—; extremo j con signo invertido respecto al vector de
fuerzas de extremo. Esfuerzos de lámina **por unidad de ancho** en ejes **locales** de la
lámina, evaluados en el centro.

---

## 4. Librería de elementos (FEM-0)

| Elemento | Formulación | Notas |
|---|---|---|
| **Barra 3D** (12 GdL) | **Euler-Bernoulli** por defecto (reproduce `Member3D.k()` de PyNite); **conmutador Timoshenko** (Φ, áreas de cortante `Avy/Avz`) para FEM-1+ | terna local = PyNite; liberaciones por condensación estática; FER uniforme/lineal/puntual/axial/**térmica** |
| **Lámina quad** (4 nudos, 24 GdL) | **DKMQ** (flexión+cortante Mindlin, Katili) + **membrana** tensión plana + GdL de **drilling** (1/1000, Bathe) — reproduce `Quad3D` de PyNite | triángulo como quad degenerado (respaldo) |
| **Lámina curva** (4 nudos, 24 GdL) — **FEM-2** | **MITC4** (Dvorkin-Bathe): membrana + flexión Mindlin con **cortante transversal asumido** (libre de bloqueo) + drilling 1/1000; terna local por elemento → mallas curvas/alabeadas | `elementos/lamina_curva.py`; misma interfaz que `LaminaQuad` → ensamblaje/modal/móvil sin cambios |
| **Rigidizador** (barra excéntrica) — **FEM-2** | barra 3D acoplada por **offset rígido** (`u = u_nudo + θ×r`); subclase de `ElementoBarra` (no añade nudos) | `elementos/rigidizador.py`; diafragmas, almas rigidizadas, conexión losa-alma |

> **Por qué EB y DKMQ:** el oráculo PyNite es **EB** en barras (su `k()` no incluye cortante)
> y **DKMQ** en placas (no MITC4 clásico). FEM-0 reproduce ambos para garantizar la
> no-regresión exacta; la física de cortante (Timoshenko) y la lámina curva quedan para FEM-1/2.

---

## 5. Ensamblaje y solución

- Matriz de rigidez global **dispersa** (tripletes COO → CSR, `scipy.sparse`), 6 GdL/nudo.
- Apoyos por eliminación de filas/columnas; **resortes** sumados a la diagonal.
- Solver **estático lineal** directo `scipy.sparse.linalg.spsolve` (suficiente para
  predimensionado; gancho para iterativo CG/AMG en mallas grandes) `[confirmar AN]`.
- Recuperación de esfuerzos por elemento y **reacciones** (residuo en GdL coaccionados).
- **Cierre interno de equilibrio** (ΣF aplicada + ΣF reacción ≈ 0).
- Multi-caso resuelto **una vez**; combinaciones por **superposición** (válido en lineal).

---

## 6. Arnés de validación (puerta de calidad del núcleo)

El núcleo solo se da por bueno si pasa, dentro de tolerancia documentada `[confirmar AN]`:

| Capa | Referencia | Tolerancia | Resultado FEM-0 |
|---|---|---|---|
| Parche analítico — viga/voladizo/axil/torsión | solución cerrada EB | ≤ 1e-6 | exacto (≤ 1e-13) |
| Parche analítico — placa | Timoshenko (nu=0.3) | ≤ 5 % | 1–2.5 % |
| Patch test de membrana | tensión constante | ≤ 1e-9 | 5.6e-16 |
| **Oráculo PyNite** | mismo modelo, dos motores | ≤ 1e-6 rel | despl 2e-17, reac/esf 3e-11; placa exacta |
| **No-regresión casos 1–15** | `resultados.json` de referencia | despl 1e-3, esf barra 1e-3, esf placa 1e-2 | caso-01 4e-11; caso-03 (2646 GdL) Rz 0.0, M rel 1.3e-11 |
| **FEM-1 modal** (PT 7.1) | frecuencias cerradas viga (βₙL) | 5 % (lumped) | biapoyada < 4e-5; voladizo f1–f3 0.1–0.7 % |
| **FEM-1 líneas de influencia** (PT 7.1) | IL analíticas viga isost./continua | 1e-3 / 1e-2 | IL reacción 3.5e-13; IL M centro = a·b/L exacto; Σ(IL) continua = −1 (6.3e-13) |

El oráculo PyNite vive en otro plugin (aislamiento de runtime) → el contraste se hace **en
desarrollo/test** (`PYTHONPATH=/tmp/pylibs`), **nunca en producción** del núcleo nuevo.

---

## 7. Núcleo común espejado

`motor-fem` **espeja byte a byte** `scripts/nucleo/` (`ifc_utils.py` + `grafo_red.py` [+ test
+ README]) como el resto de plugins (decisión nº4). La puerta
`Nucleo-transversal/verificar_espejo_nucleo.py` debe dar **ESPEJOS IDÉNTICOS**. Aunque el
grafo de red no sea la parte principal del FEM, el espejo mantiene la coherencia del
ecosistema y deja la puerta lista para futuras vías IFC del dominio de análisis.

---

## 8. Extensión sin romper (FEM-1 … FEM-5)

Regla: **añadir claves nuevas, nunca cambiar la semántica de las existentes**.

- **FEM-1:** ✅ **(PT 7.1)** `cargas_moviles` (líneas de influencia + envolventes por tren) +
  `analisis="modal"` (masa concentrada + masa participante). Aditivo (módulo `fem1.py`), sin
  tocar el estático FEM-0 → no-regresión por construcción. Validado: modal viga biapoyada
  (err < 4e-5) y voladizo (0.1–0.7 %); IL reacción isostática 3.5e-13; IL momento centro
  exacto (a·b/L); equilibrio de IL en viga continua 6.3e-13.
- **FEM-1 · v0.2.1 (PT 7.2):** ✅ extensión **aditiva menor** del barrido móvil — nuevo
  objetivo **`esfuerzo_lamina`** en `cargas_moviles.objetivos` (`{"tipo":"esfuerzo_lamina",
  "elem":<lámina>,"comp":"Mx|My|Mxy|Qx|Qy|Nx|Ny|Nxy"}`): líneas de influencia y envolventes
  LM1 de un **esfuerzo de placa** (por unidad de ancho) de una lámina DKMQ objetivo, para
  losas postesadas. El motor **no sube de peldaño** (sigue en FEM-1); solo se añade una rama
  en `_eval_objetivo`, sin tocar el estático ni el móvil de barra/reacción/desplazamiento.
  Validado (`validacion/fem1.py::il_lamina`): la IL del barrido coincide con el esfuerzo de
  placa de un *solve* estático directo (**consistencia 8.6e-15**) y es nula en los apoyos.
- **FEM-2:** ✅ **(PT 7.4)** elementos `tipo:"lamina_curva"` (**MITC4**) y `tipo:"rigidizador"`
  (**offset rígido**) + **pared delgada** (`fem2.bredt_J`, `shear_lag_beff`, `indicador_distorsion`).
  Módulos aditivos (`elementos/lamina_curva.py`, `elementos/rigidizador.py`, `fem2.py`), sin tocar
  `fem_core`/`barra`/`lamina`/`fem1` → no-regresión FEM-0/1 **exacta por construcción**. Validado con
  **benchmarks NAFEMS** (`validacion/nafems2.py`): Scordelis-Lo 1,6 %, pinched cylinder 2,8 %,
  hemispherical shell 0,4 %, placa rigidizada 1,3 %, cajón vs Bredt 3,4 % (tolerancia ±5 %).
  `LaminaCurvaMITC4` y `ElementoRigidizador` conservan `isinstance` con las clases base → el
  ensamblaje, el modal y el móvil del núcleo los usan sin ramas nuevas. Primer consumidor: el
  **cajón postesado** de `puentes` (lámina pura). Habilita las **cubiertas laminares** de la Ola 3.
- **FEM-3:** `analisis="pandeo_lineal"`/`"no_lineal"` (2.º orden, corotacional/arc-length).
- **FEM-4:** elementos `tipo:"cable"`/`"membrana"` + `form-finding`.
- **FEM-5:** dinámica en el tiempo (horizonte).

---
*Predimensionado/asistencia; a revisar y firmar por técnico competente (ICCP).*
