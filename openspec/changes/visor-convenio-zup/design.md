# Diseño técnico · Convenio Z-up del visor

## Enfoque

**Deshacer el swap de web-ifc en la ingesta.** web-ifc entrega la geometría del IFC (Z-up)
convertida a Y-up para three.js. En lugar de re-etiquetar ejes (incoherente), se **rota la
geometría +90° sobre X** al construir la escena (en `viewer.addIfcModel`, sobre las mallas que
salen de `IfcLoader.getMeshes`), de modo que el visor trabaje en **Z-up nativo del IFC**. A
partir de ahí:

- `camera.up = (0,0,1)` y OrbitControls configurados con ese «arriba».
- La cota de elemento es `box.*.z` (el AABB en marco de escena Z-up).
- `bcfCameraToViewer` se simplifica a **identidad**: el viewpoint BCF ya está en IFC Z-up y la
  escena también, así la cámara cae exactamente donde los meshes.

Alternativa descartada: mantener la geometría en Y-up y solo re-etiquetar la cota — deja el
visor y el IFC en marcos distintos, que es el problema que se quiere eliminar.

## Análisis de gobierno (evidencia)

| Artefacto | Marco de la cámara | ¿Cambia con Z-up? | Llave |
|---|---|---|---|
| Golden firmado `C4-FED-06` (D29) | IFC Z-up (`up=(−1,1,2)/√6`) | No | — |
| `test/federado-e2e.test.ts` (95–104) | IFC Z-up (parseViewpoint crudo) | No | 1 |
| `test/coste-5d-e2e.test.ts` | (no comprueba cámara) | No | 1 |
| `test/bcf.test.ts` (78–84) | marco visor (mapeado) | **Sí** (mapeo→identidad) | 1 |
| Tests de cota (`spatial-tree`, `saneamiento`, …) | eje de cota | **Sí** (`.y`→`.z`) | 1 |
| `test/ux-behavior.test.ts` (cámara) | marco visor (framing) | **Sí** (Y-up→Z-up) | 1 |

Conclusión: **ningún artefacto firmado cambia**; todo el re-baseline vive en tests internos del
visor (Llave 1). El golden D29 está en IFC Z-up, el marco destino.

## Decisiones y cuestiones abiertas

- **D-Zup-1** · La rotación se aplica en la ingesta de la escena (render), NO reescribe ficheros
  IFC ni fixtures → los md5 anclados (fixtures, golden) quedan intactos.
- **D-Zup-2** · `bcfCameraToViewer` se conserva como función pública (identidad) para no romper
  la superficie de `@aqyra/visor` ni `demo/main.ts`; su unitario se re-baselina.
- **Q-Zup-1** (para JM) · Ratificar la reclasificación del riesgo D29 (de Llave 2 a Llave 1) que
  la evidencia de código soporta, actualizando el ADR-018-DRAFT en consecuencia.
- **Q-Zup-2** (para JM/equipo) · Orden respecto a **slice-1**: ¿aterrizarlo en su PR previa
  (recomendado, el gizmo y el shell son superficie de este cambio) o integrarlo aquí?
