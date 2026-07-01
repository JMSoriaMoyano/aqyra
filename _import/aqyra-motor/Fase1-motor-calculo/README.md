# Fase 1 — Motor de cálculo estructural IFC → FEM → Eurocódigos

Prueba de concepto del flujo completo **de extremo a extremo**, limitada a
elementos de barra (pórtico plano de acero). Valida la cadena antes de invertir
en el plugin completo y en las losas (Fase 2).

## Resultado

Pórtico de un vano (L = 6 m, H = 4 m), pilares HEB 200 y dintel IPE 330 en acero
S275, biempotrado, con cargas G = 12 kN/m y Q = 9 kN/m sobre el dintel.

- **Autodiagnóstico** (viga biapoyada vs. solución cerrada): error < 0,02 %.
- **Validación cruzada** PyNite vs. anaStruct (solver independiente): error < 0,07 %.
- **Verificación EC3**: todas las barras CUMPLEN (aprovechamiento máx. 38,5 %).
- **Memoria de cálculo** en Word con geometría, materiales, acciones,
  combinaciones, diagramas, deformada y comprobaciones.

## Cómo ejecutar

```bash
# 1) (opcional) regenerar el IFC de prueba
python3 scripts/generate_test_ifc.py

# 2) cadena completa: IFC -> modelo -> FEM -> validación -> EC3 -> diagramas
python3 scripts/run_all.py proyecto-demo

# 3) memoria de cálculo (Word)
NODE_PATH=$(npm root -g) node scripts/generate_memoria.js proyecto-demo
```

Para un IFC propio: `python3 scripts/run_all.py <carpeta> <archivo.ifc>`
(el IFC debe contener el dominio de análisis estructural con la convención de
Psets `Pset_Estructurando_*`, ver `generate_test_ifc.py`).

## Arquitectura (capas)

| Script | Capa | Función |
|---|---|---|
| `generate_test_ifc.py` | datos | Genera el IFC4 con dominio de análisis estructural |
| `ifc_to_model.py` | parser | IFC → **modelo neutro JSON** (nodos, barras, secciones, materiales, cargas) |
| `combinaciones.py` | normativa | Combinaciones ELU/ELS según EC0 (AN España) |
| `solver.py` | cálculo | FEM con PyNite → N, V, M, T y flechas por combinación |
| `cross_validate.py` | QA | Validación cruzada independiente con anaStruct |
| `verificacion.py` | normativa | Comprobaciones EC3 + autodiagnóstico del solver |
| `plots.py` | salida | Diagramas de esfuerzos y deformada |
| `generate_memoria.js` | salida | Memoria de cálculo en Word |
| `run_all.py` | orquestador | Encadena todo el flujo |

## Stack

IfcOpenShell · PyNite · anaStruct (QA) · matplotlib · docx-js.

## Convenciones del solver (validadas)

- Modelo IFC en plano XZ (Y = 0), gravedad −Z; remapeo a PyNite con vertical = Y.
- Inercia mayor del perfil → slot `Iz` de PyNite ⇒ flexión en plano = `Mz`/`Fy`.
- GDL fuera de plano coaccionados en todos los nodos (modelo plano en solver 3D).
- Axil en convención estándar: **compresión negativa** (signo verificado contra anaStruct).

## Limitaciones de esta fase

Análisis lineal de barras; interacción N+M lineal conservadora; no se comprueban
pandeo lateral, abolladura ni uniones; láminas/losas (2D) → Fase 2.
**Todo cálculo debe ser revisado y firmado por técnico competente.**
