# Golden C1-APERTURA-01 (ficha de record)

```
id:           C1-APERTURA-01
contrato:     C1 (interoperabilidad) · iso19650-openbim 0.10.0 (firmado aguas arriba)
entrada:      caso.alto.json
              (huecos en LOSA + MURO · IfcTransportElement=ELEVATOR · alineación
               clotoide + acuerdo vertical · doble clasificación bsDD+Uniclass)
esperado:     expected.json — IFC IFC4X3 válido en el que:
                - LOSA vaciada (1 IfcRelVoidsElement sobre IfcSlab) y MURO vaciado (1)
                - ASCENSOR presente (IfcTransportElement, PredefinedType=ELEVATOR)
                - planta = LINE · CLOTHOID · CIRCULARARC · CLOTHOID · LINE ; L=400.000 m ;
                  A_clotoide = 134.164 (= sqrt(300*60))
                - doble clasificación bsDD (URI) + Uniclass 2015 (EF): 7/7
                  (4 pilares, 1 muro, 1 losa, 1 ascensor)
oráculo:      compilar_spec → spec_to_ifc → { ifc_to_model_lineal + validación } + validar (interno)
              [run aguas arriba: 2026-06-28 · VEREDICTO GOLDEN VERDE]
tolerancia:   conteos EXACTOS; L=400.000 m (±1e-6); A_clotoide=134.164 (±0.1); secuencia exacta.
responsable:  JM (firma = Llave 2)
```

## Cómo la ejercita el runner en Fase 0

El oráculo real de C1 es *compilar→parsear→contar*; la transformación (compile) vive en
`engines/ifc`, que se importa en **0.5**. En Fase 0 el runner hace lo máximo fiel sin el motor:

1. Valida `caso.alto.json` contra `contracts/C1/alto-spec.schema.json` (conformidad de esquema).
2. Reparsea `golden.ifc` (congelado) con ifcopenshell y **recomputa** los conteos del oráculo,
   comparándolos con `expected.json` dentro de `tolerancias.json`.

**Costura marcada:** al aterrizar `engines/ifc` (0.5), se antepone el paso *compile*
(`caso.alto.json` → IFC) contra el **mismo** `expected.json`. El esperado no cambia.

## Ficheros

- `caso.alto.json` — entrada patrón (lo que emitiría el cebo).
- `golden.ifc` — IFC4X3 congelado (la verdad compilada aguas arriba).
- `expected.json` — el oráculo (procedencia independiente del runner).
- `tolerancias.json` — tolerancias + la regla de oro.

*Predimensionado/asistencia; a revisar y firmar por técnico competente (Llave 2).*
