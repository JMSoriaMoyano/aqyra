# Cómo probar V3 (post-proceso bajo dos llaves)

Hay dos formas de probar: **(A) verlo en el navegador** (lo visual, lo que verá el Calculista) y **(B) el cálculo real por debajo** (las dos llaves, en Python — opcional, para los curiosos). No necesitas saber comandos: todo va con doble clic.

---

## A · Probar en el navegador (lo principal)

### 1. Arrancar el visor
Doble clic en **`INICIAR_VISOR_npm.bat`**. Se abre una ventana negra (déjala abierta) y, en unos segundos, el visor en:

> **http://localhost:5173/calculista.html**

Si no se abre solo, copia esa dirección en el navegador.

### 2. Cargar un modelo
**Arrastra un archivo `.ifc`** sobre la ventana del visor (cualquiera de tus proyectos; idealmente uno con estructura: pilares, vigas, forjados). Verás el modelo en 3D: girar = botón izquierdo, zoom = rueda, mover = rueda pulsada.

### 3. Hablarle (barra de comandos, abajo)
Escribe en lenguaje natural y pulsa Enter. Pulsa **`/`** para saltar al cuadro.

**Lo que ya existía (V1 / V2):**
- `clases` — lista los tipos de elemento.
- `aísla las vigas` · `oculta los muros` · `colorea los pilares de azul` · `muéstrame todo el modelo` · `deshacer`.
- `modelo analítico` — dibuja el modelo idealizado (barras y nudos) que el cálculo usa.
- (clic en un pilar) → `apoyo empotrado aquí` · (clic en una viga) → `sobrecarga de 5 kN/m`.
- `columna-cajón` / `4 láminas` — idealización de núcleos. `exporta el analítico` — guarda el IFC con cargas/apoyos.

**Lo NUEVO de V3 — esto es lo que conviene mirar:**

- **`estado de dato`** — abre la leyenda de las **dos llaves**. Verás los cuatro estados con su color:
  - **PROPUESTA** (gris) · **NO VERIFICADO** (rojo) · **QA OK · SIN FIRMAR** (ámbar) · **VERIFICADO · firma JM** (verde).
  - Haz clic en cada etiqueta para **previsualizar** cómo se vería ese estado en pantalla (chip arriba a la izquierda + marca de agua diagonal). Comprueba que **solo el verde** queda "limpio".

- **`deformada`** (o `aprovechamiento`, o `post-proceso`) — pinta la **deformada coloreada por aprovechamiento** sobre el modelo (verde = holgado → rojo = no cumple). Fíjate en que:
  - aparece el chip **rojo "NO VERIFICADO"** y la **marca de agua** (es un cálculo sin firmar);
  - en el panel de abajo a la derecha, el resumen dice cuántos elementos están **al límite (>0,9)** y cuántos **no cumplen (>1)**;
  - hay dos botones para **recorrer las dos llaves**:
    1. **"Pasar QA · 1.ª llave"** → el chip pasa a **ámbar** (la QA independiente reconcilió).
    2. **"Firmar (JM) · 2.ª llave"** → el chip vira a **VERDE**.
  - **La idea de gobierno que estás comprobando:** el verde **solo aparece tras la firma**. Antes, nunca. Eso es la regla inviolable de V3.

> ✅ **NUEVO (hilo de conexión):** si arrancas antes el **servicio de cálculo** (doble clic en **`INICIAR_SERVICIO_CALCULO.bat`**, deja su ventana abierta), la deformada/aprovechamiento muestra **números REALES** (PyNite) y los botones recorren las dos llaves **de verdad** (`/qa`, `/sign`). El panel indica el origen (`números REALES · pynite-provisional`) y, mientras el productor sea PyNite, un aviso de que la 2.ª llave **aún no es independiente** (lo será con motor-fem). Si **no** arrancas el servicio, el visor cae a **datos DEMO** (ilustrativos) y te avisa: el flujo de estado se ve igual, pero los números no son un cálculo.

### 4. Cerrar
Cierra el navegador y la ventana negra (o pulsa Ctrl+C en ella).

---

## B · Probar el cálculo real (las dos llaves, opcional)

Esto ejecuta el motor de comprobación de verdad (re-cálculo independiente con PyNite, equilibrio, EC3 y firma) sobre un caso patrón, y te enseña los **números reales** y los veredictos `qa-passed` / `qa-fail`.

Doble clic en **`VERIFICAR_CALCULO.bat`**. Instala lo necesario la primera vez y deja el resultado en **`VERIFICAR_CALCULO_resultado.txt`**. Verás, por ejemplo:
- la ménsula con carga hacia abajo (−Z) → **reacción hacia arriba** y **flecha hacia abajo** (física correcta);
- el flujo **computed → qa-passed → verified-signed** con un elemento que **no cumple** marcado;
- y que **no se puede firmar** algo que no ha pasado la QA, y que un resultado discrepante **bloquea** la firma.

Requiere tener **Python 3.10+** instalado (https://python.org). Si no lo tienes, este apartado es opcional: la lógica ya está probada y en verde por nuestro lado.

---

## ¿No tienes un IFC a mano?
Dímelo y te genero uno de prueba (un pórtico de acero tipo Decopak HQ) para que tengas algo que arrastrar.
