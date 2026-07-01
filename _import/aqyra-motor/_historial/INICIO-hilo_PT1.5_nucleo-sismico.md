# Texto de inicio — PT 1.5: núcleo de pantallas acopladas + sísmico integrado en el edificio

> Copia y pega el bloque siguiente al iniciar el hilo nuevo en el proyecto **Estructurando**.
> Da todo el contexto necesario sin información adicional.

---

Proyecto Estructurando. Ejecuta el **PT 1.5 de la Ola 1** (cerrar la estabilización lateral de
edificación): **núcleo de pantallas acopladas + integración del sísmico EC8 en el orquestador
de edificio**. Es el siguiente peldaño de la **familia sísmica**, que el caso 11 dejó anotado
como extensión. Trabaja con el agente `ingeniero-estructurista`.

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ecosistema-ingenieria.md` (documento maestro del ecosistema; este hilo es el PT 1.5 de la Ola 1).
2. `Nucleo-transversal/` — contratos C1 (IFC/modelo neutro), C2 (memoria-despacho), C3 (entregables). Este caso debe cumplirlos.
3. `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md`, `CHANGELOG-plugin.md` y `Hoja-de-ruta_v2_Motor-calculo-estructural.md`.
4. `Casos-de-uso/caso-11-pantalla-sismo-ec8/ENUNCIADO.md` y sus resultados (la base sísmica ya construida).

**Punto de partida — lo que YA existe (no rehacer):** plugin **motor-calculo-estructural
v0.21.0**, con el módulo **`scripts/sismico/`** completo creado en el caso 11: biblioteca
**EC8** (`ec8.py`: espectro de cálculo Sd(T), 4 ramas, q, λ), **análisis modal** + combinación
**SRSS/CQC**, **método de fuerzas laterales**, verificación de **pantalla aislada** (cortante de
alma, elementos de borde §5.4.3.4, N-M en base, deriva §4.4.3.2) y memoria Word. El caso 11
(pantalla C30/37 Lw=4,0 tw=0,30 H=15,0, 5 plantas, q=3,0 DCM) está **cerrado y validado**
(Fb≈929 kN, equilibrio ~0 %). El clasificador/enrutador multi-elemento (`clasificador.py`,
`run_all_edificio.py`) y la lectura de IFC ortodoxo + físico→analítico (serie R) también están.

**Lo que FALTA (objetivo de este hilo):**

1. **Núcleo de pantallas acopladas.** Extender `sismico/` de la pantalla aislada (voladizo
   stick) al **núcleo**: varias pantallas en planta acopladas por dinteles/forjados, con
   **rigidez a torsión** y reparto de cortante por rigidez+excentricidad (centro de rigidez vs
   centro de masa). Idealización 3D del núcleo (cajón) o pantallas acopladas con vigas de
   acoplamiento. Verificación EC8: cortante por pantalla, vigas de acoplamiento (DCM), N-M,
   **deriva** y **efectos de torsión accidental** (§4.3.2).

2. **Integrar el sísmico en el orquestador de edificio.** Que `run_all_edificio.py` (que hoy
   clasifica y enruta cada elemento bajo gravedad) **aplique también el caso sísmico**: derivar
   masas de planta del modelo, montar el modelo lateral (pórticos + pantallas/núcleo),
   distribuir el cortante sísmico al sistema de estabilización y verificar derivas globales.
   Combinación sísmica EC0 §6.4.3.4. Reutiliza el módulo `sismico/` existente.

**Receta (DoD del programa de aprendizaje):** genera un **IFC de prueba** del caso (núcleo +
plantas + masas + Pset EC8; ortodoxo y, si procede, una variante física para la serie R) →
parser al **modelo neutro** (contrato C1; extiende con claves nuevas, sin romper las
existentes) → solver + verificación EC8 → **validación** (equilibrio del cortante basal ~0 %,
contraste modal espectral vs fuerzas laterales, rangos físicos de T1 y deriva) → diagramas +
**memoria Word** (estructura del contrato C3) → **registra**: lección y métricas en
`REPOSITORIO-aprendizaje.md`, entrada en `CHANGELOG-plugin.md`, sube el plugin (minor: núcleo +
sísmico en orquestador) y **reempaqueta** el `.plugin` (excluyendo `node_modules`/`__pycache__`,
acumulativo sobre v0.21.0). Actualiza `criterios-despacho.md` si fijas algún criterio nuevo.

**Notas de método (casos 1–14 / serie R):** escribe el código del plugin por heredoc en el
sandbox y valida con `ast.parse` (el editor trunca líneas largas, INC-04); cuidado con módulos
homónimos entre paquetes (carga por ruta explícita o subproceso); el análisis modal/malla puede
ser lento (ejecuta por partes si superas ~45 s); **las herramientas de fichero (Read/Write/Edit)
son la fuente de verdad de la carpeta conectada** — no edites markdown preexistente por shell;
no uses el pico singular como valor de diseño. Todo es **predimensionado, a revisar y firmar por
técnico competente**; Anejo Nacional España, NDP marcados `[confirmar AN]` (NCSE-02 / EC8;
vigilar NCSR-22).

**Empieza** leyendo los documentos indicados y proponiendo el modelo del núcleo (geometría y
disposición de pantallas) antes de generar el IFC.
