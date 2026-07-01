# Caso 4 — Cubierta / forjado inclinado (`laminas` incl, EC2 + membrana)

> Cuarto peldaño del programa. Antes de empezar, lee
> `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md` y
> `CHANGELOG-plugin.md`. Trabaja con el agente `ingeniero-estructurista`.
> Plugin de partida: **motor-calculo-estructural v0.5.0** (el parser de `laminas`
> ya lee superficies ortodoxas —incluidas las **inclinadas** (esquinas con z≠0)—,
> la sección rectangular de pilar (`IfcRectangleProfileDef`) y resuelve la losa
> plana apoyada en una retícula de pilares con punzonamiento EC2).

## 1. Contexto y objetivo

Se entrega un **modelo IFC ortodoxo** (`caso-04.ifc`) de un **faldón de cubierta de
hormigón inclinado** (superficie plana con normal **no vertical**), apoyado en
alero y cumbrera. Doble objetivo:

1. **Calcular** el faldón con el módulo `laminas` incl: **flexión EC2** (normal al
   plano del faldón) y, sobre todo, los **esfuerzos de membrana** (n_x, n_y, n_xy)
   que aparecen porque la carga gravitatoria sobre un plano inclinado tiene
   componente en el propio plano de la lámina; más flecha y fisuración, con su
   validación y memoria.
2. **Cerrar la siguiente brecha del motor**: leer la **superficie inclinada
   ortodoxa** (esquinas con z≠0 de `IfcFaceSurface`/`IfcPolyLoop`; deducir L_u, L_v
   y el ángulo de la geometría; orientar el mallado y los esfuerzos al **plano
   local** de la lámina) y aplicar los **apoyos lineales** de alero y cumbrera
   desde los `IfcStructuralPointConnection` + `IfcBoundaryNodeCondition`, en lugar
   del `Pset_Estructurando_Superficie_Inclinada` que usa hoy `solver_incl.py`.

## 2. Descripción del modelo (lo que contiene el IFC)

Faldón de losa maciza de hormigón **C30/37**, espesor **0,20 m**:

- **Geometría inclinada**: ancho L_v = **8,0 m** (eje X, horizontal) y longitud de
  faldón L_u = **6,0 m** medida sobre la pendiente, inclinación **θ = 30°**.
  Esquinas (plano XY horizontal, Z vertical):
  alero `(0,0,0)`·`(8,0,0)`; cumbrera `(8, 5.196, 3.0)`·`(0, 5.196, 3.0)`
  (proyección horizontal L_u·cos30 = 5,196 m; altura L_u·sin30 = 3,0 m).
- **Apoyos lineales** simplemente apoyados en **alero** (z=0, traslaciones
  coartadas) y **cumbrera** (z=3,0; vertical + lateral coartadas, giro libre),
  definidos por `IfcStructuralPointConnection` + `IfcBoundaryNodeCondition` en las
  cuatro esquinas.
- **Cargas de superficie** verticales (gravedad −Z, *true-length*):
  **G = 6,0 kN/m²** (p.p. losa 0,20·25 = 5,0 + cubrición 1,0) y
  **Q = 1,0 kN/m²** (nieve) `[confirmar AN/zona]`.

**El IFC es ortodoxo** (entidades estándar; **sin** `Pset_Estructurando_*`):
`IfcStructuralSurfaceMember` con `Thickness` y representación `IfcFaceSurface`
(`IfcPlane` con normal inclinada); material por `IfcRelAssociatesMaterial`;
cargas por `IfcStructuralLoadGroup` (G, Q) + `IfcStructuralSurfaceAction` +
`IfcStructuralLoadPlanarForce`. Ver `validacion-IFC.txt`.

## 3. Brecha conocida (lo que hay que corregir) — superficie inclinada ortodoxa

Con el plugin v0.5.0:

- El parser genérico `ifc_to_model_3d.py` **ya lee** las esquinas inclinadas
  (z≠0), el espesor, el material y las cargas G/Q. *Verificado.*
- `solver_incl.py` **todavía lee** `L_u`, `L_v`, el ángulo y las cargas de
  `Pset_Estructurando_Superficie_Inclinada`/`Pset_Estructurando_Carga_Vertical`.
  Hay que **añadir una vía ortodoxa** que deduzca L_u, L_v y θ de las esquinas
  (longitud de los bordes y normal del plano) y tome material/cargas del camino
  estándar, **manteniendo el Pset como respaldo** (igual que casos 1–3).
- **Apoyos de alero/cumbrera (continuación de INC-03):** aplicar los apoyos
  lineales a partir de los nodos `IfcStructuralPointConnection` situados en alero y
  cumbrera (clasificar bordes por geometría), en vez de generarlos por convención.
- **Esfuerzos de membrana:** asegurar que se extraen y verifican n_x, n_y, n_xy en
  el plano local del faldón además de los momentos de flexión.

Corregir de forma **acotada** (superficie inclinada ortodoxa + apoyos de borde,
sin romper la lectura de los IFC con Psets ni de los casos 2 y 3). Anotar en
`CHANGELOG-plugin.md` y subir el plugin a **0.5.1** (patch) o **0.6.0** (minor)
según el alcance.

## 4. Criterios de aceptación

1. **Modelo neutro** del IFC ortodoxo con: material C30/37, 1 superficie inclinada
   (C30/37, t=0,20 m, 4 esquinas con z = 0 y 3,0 m, θ≈30°, 2 cargas G/Q) y los
   nodos de apoyo de alero y cumbrera.
2. **Flexión (EC2)**: momento de vano del faldón coherente con una losa
   simplemente apoyada de luz L_u = 6,0 m (orden m ≈ q_n·L_u²/8 con la componente
   **normal** q_n = q·cos θ); armadura y fisuración dentro de rangos; flecha ≤
   límite; aprovechamientos ≤ 1.
3. **Membrana**: esfuerzos n (en el plano del faldón) coherentes con la componente
   **tangencial** q·sen θ de la gravedad, transmitida a alero/cumbrera.
4. **Equilibrio global**: carga total ELU = (1,35·6,0 + 1,50·1,0)·(8,0·6,0) ≈
   **461 kN** ≈ Σ reacciones de alero + cumbrera (error < 1 %). Validación de placa
   (autodiagnóstico MITC4) OK.
5. **Memoria** Word y diagramas (mapa de momentos y de esfuerzos de membrana del
   faldón, deformada).

## 5. Entregables del hilo

- Parser/solver de `laminas` incl ampliado (superficie inclinada ortodoxa + apoyos
  de borde) + plugin reempaquetado **v0.5.1/0.6.0** y `CHANGELOG-plugin.md`
  actualizado.
- En `caso-04-cubierta-inclinada/`: `modelo_neutro.json`, `verificacion.json`,
  memoria y diagramas.
- `REPOSITORIO-aprendizaje.md`: lección del caso 4 (plano inclinado: flexión +
  membrana) y fila de métricas.
- **Caso 5 preparado**: `caso-05-soporte-zapata/ENUNCIADO.md` + su IFC ortodoxo
  (soporte de hormigón + zapata aislada; cadena pilar→cimiento, lecho elástico)
  con su generador y validación.

## 6. Cómo ejecutar (orientación)

```bash
# 1) (ya hecho) generar el IFC del caso:  python3 generate_caso04_ifc.py
# 2) tras ampliar el parser/solver incl a superficie inclinada ortodoxa:
cd <plugin>/scripts/laminas
python3 run_all_incl.py proyecto-caso04 <ruta>/caso-04.ifc
#    faldon inclinado: flexion EC2 + MEMBRANA + flecha + fisuracion + diagramas
#    (apoyos lineales en alero y cumbrera; mallado orientado al plano del faldon)
```

> Recuerda: resultado de **predimensionado**, a revisar y firmar por técnico
> competente; marcar `[confirmar AN]` los NDP.
