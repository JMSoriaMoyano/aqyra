# Memoria de calculo — Pila sobre encepado de 2 pilotes — cimentacion profunda en grupo (biela-tirante) (caso PUE-12)

**Disciplina `puentes` (Ola 7, PT 7.3.1, IFC-driven).** El calculo arranca de un IFC4X3
leido por el lector estructural (geometria extruida real + Psets no geometricos).
**Predimensionado/asistencia; debe ser revisado y firmado por tecnico competente (ICCP).**

## 1. Objeto y normativa
Tipologia: **pila + apoyo + cimentacion**. Acciones IAP-11; comprobacion segun Eurocodigos
(EC2/EC3/EC7 con Anejo Nacional espanol [confirmar AN]).

## 2. Flujo (IFC-driven)
`caso-PUE-12-pila-encepado/PUE-12.ifc` → `ifc_to_model_estructural`
(parser C1) → `desde_ifc` (adaptador) → idealizacion → `motor-fem` (C5) → IAP-11 →
comprobacion → resultado + write-back al IFC (`Pset_Estructurando_ResultadoPuente`).

## 3. Resultado
- **VEREDICTO: CUMPLE** · aprovechamiento maximo **0.563**.
- Frecuencia fundamental f1 = **4.51 Hz**.

## 4. Conclusion
El predimensionado **CUMPLE**. Resultado de asistencia; revisar y firmar (ICCP).
