# Memoria de calculo — Pila alta esbelta sobre 4 pilotes — H=14 m, 2.o orden relevante, cimentacion profunda (caso PUE-11)

**Disciplina `puentes` (Ola 7, PT 7.3.1, IFC-driven).** El calculo arranca de un IFC4X3
leido por el lector estructural (geometria extruida real + Psets no geometricos).
**Predimensionado/asistencia; debe ser revisado y firmado por tecnico competente (ICCP).**

## 1. Objeto y normativa
Tipologia: **pila + apoyo + cimentacion**. Acciones IAP-11; comprobacion segun Eurocodigos
(EC2/EC3/EC7 con Anejo Nacional espanol [confirmar AN]).

## 2. Flujo (IFC-driven)
`caso-PUE-11-pila-pilotes/PUE-11.ifc` → `ifc_to_model_estructural`
(parser C1) → `desde_ifc` (adaptador) → idealizacion → `motor-fem` (C5) → IAP-11 →
comprobacion → resultado + write-back al IFC (`Pset_Estructurando_ResultadoPuente`).

## 3. Resultado
- **VEREDICTO: CUMPLE** · aprovechamiento maximo **0.893**.
- Frecuencia fundamental f1 = **1.90 Hz**.

## 4. Conclusion
El predimensionado **CUMPLE**. Resultado de asistencia; revisar y firmar (ICCP).
