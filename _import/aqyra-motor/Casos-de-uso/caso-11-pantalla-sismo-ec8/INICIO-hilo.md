# Texto de inicio del Caso 11 — para pegar en un hilo nuevo

> Copia y pega el bloque siguiente al iniciar el hilo del Caso 11 en el proyecto
> **Estructurando**. Da todo el contexto necesario sin información adicional.

---

Proyecto Estructurando. Ejecuta el **Caso 11 — Pantalla de cortante + sísmico EC8** (primer peldaño de la **segunda tanda**, abre la familia sísmica) del programa de aprendizaje. Lee primero `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md`, `CHANGELOG-plugin.md` y `Hoja-de-ruta_v2_Motor-calculo-estructural.md` (v3.0, Dirección 1); luego `Casos-de-uso/caso-11-pantalla-sismo-ec8/ENUNCIADO.md` y trabaja sobre `caso-11.ifc` con el agente `ingeniero-estructurista`.

**Punto de partida:** plugin **motor-calculo-estructural v0.12.0** (primera tanda 1–10 cerrada: vía ortodoxa `parse_ortodoxo()` en todos los módulos + **clasificador/enrutador multi-elemento** y orquestador integrado `run_all_edificio.py`; INC-03 resuelto). El parser genérico `scripts/laminas/ifc_to_model_3d.py` **ya lee** sobre `caso-11.ifc` la pantalla (superficie vertical C30/37 Lw=4,0 tw=0,30 H=15,0) y los 6 nodos (base empotrada + 5 de planta); las **5 masas sísmicas** de planta (`IfcStructuralPointAction`, grupo `Sismo_masas`) y los **parámetros EC8** (`Pset_Estructurando_Sismo`) están en el modelo —verificado (ver `validacion-IFC.txt`)—. Lo que **falta** es un **tipo de análisis nuevo**: el motor v0.12.0 **no tiene módulo sísmico ni biblioteca EC8**.

**El modelo (sintético, realista):** sistema de estabilización lateral de un edificio de 5 plantas — una **pantalla de hormigón armado** C30/37, **Lw=4,0 m, tw=0,30 m, H=15,0 m** (5×3,0 m), empotrada en base, trabajando a cortante en su plano. **Masas sísmicas por planta** W=1200 kN (plantas 1–4) y 900 kN (cubierta), ΣW=5700 kN (m=581 t). **EC8** (`Pset_Estructurando_Sismo`): ag=0,20 g, suelo C, espectro tipo 1 (S=1,15, TB=0,20, TC=0,60, TD=2,0), clase importancia II (γI=1,0), **q=3,0** (DCM muros), amortiguamiento 5%, λ=0,85. Datos sísmicos y geometría de pantalla en Pset (respaldo y marcador), igual que casos 5/6/7/9. Marcar **[confirmar AN]** (NCSE-02 / EC8 España).

**Trabajo del hilo (apertura de la familia sísmica):**

1. **Nuevo módulo `sismico/` (o `pantallas/`)**: parser de la pantalla + masas + Pset sísmico; **voladizo equivalente** (stick) con masas concentradas por planta (flexión + cortante de la sección de pared).

2. **Nueva biblioteca EC8 (EN 1998-1)**: **espectro de respuesta de cálculo** `Sd(T)` (cuatro ramas, q, λ); **análisis modal** (PyNite tiene modal) — periodos, modos, masas modales efectivas, **combinación SRSS/CQC**; **método de fuerzas laterales** (§4.3.3.2) como contraste; **combinación sísmica** (EC0 §6.4.3.4).

3. **Verificación de la pantalla**: **cortante del alma** + armadura (EC2/EC8), **elementos de borde** confinados (EC8 §5.4.3.4), **N-M en la base**, **deriva entre plantas** (limitación de daño §4.4.3.2). Aprovechamientos ≤ 1; picos como envolvente.

4. **Validación**: T1 ≈ 0,4–0,6 s (meseta), Sd=0,192 g, **cortante basal Fb ≈ 929 kN** = Σ fuerzas de planta (~0 %), momento de vuelco base ≈ 9.900 kN·m; contraste modal espectral vs fuerzas laterales.

5. **Entregables** en `caso-11-pantalla-sismo-ec8/`: `modelo_neutro.json`, `verificacion_sismo.json`, memoria(s) Word y diagramas (espectro, modos, fuerzas/cortante/momento en altura, deriva, N-M).

6. **Registra**: lección del caso 11 y fila de métricas en `REPOSITORIO-aprendizaje.md` (apertura de la segunda tanda), corrección en `CHANGELOG-plugin.md`, sube el plugin a **0.13.0** (minor: módulo sísmico + biblioteca EC8) y reempaqueta el `.plugin` (excluyendo `node_modules`/`__pycache__`). El **núcleo** (pantallas acopladas) queda como extensión de la misma familia para un caso posterior.

**Notas de método (casos 1–10):** escribe el código del plugin por heredoc en el sandbox y valida con `ast.parse` (el editor trunca líneas largas, INC-04); empaqueta el `.plugin` con `zipfile` en una carpeta escribible y copia con extensión `.plugin`; instala `ifcopenshell`/`PyNiteFEA`/`numpy`/`matplotlib` (pip `--break-system-packages`) y `docx` localmente para la memoria; cuidado con los módulos homónimos entre paquetes (carga por ruta explícita con salvaguarda de `sys.path` o ejecuta por subproceso); el análisis modal/malla puede ser lento en el sandbox (ejecuta por partes si superas 45 s); **las herramientas de fichero (Read/Write/Edit) son la fuente de verdad de la carpeta conectada — el shell del sandbox puede ver copias truncadas de ficheros markdown preexistentes (no los edites por shell)**; no uses el pico singular como valor de diseño; resultado de **predimensionado**, a revisar y firmar por técnico competente, con los NDP marcados `[confirmar AN]`.
