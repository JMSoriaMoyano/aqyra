# Memoria de calculo — Paso superior de vigas artesa pretensadas — L=30 m, 5 vigas, HP-45, 2 carriles LM1 (caso PUE-07)

**Disciplina `puentes` (Ola 7, PT 7.3.1, IFC-driven).** El calculo arranca de un IFC4X3
leido por el lector estructural (geometria extruida real + Psets no geometricos).
**Predimensionado/asistencia; debe ser revisado y firmado por tecnico competente (ICCP).**

## 1. Objeto y normativa
Tipologia: **vigas pretensadas (artesa)**. Acciones IAP-11; comprobacion segun Eurocodigos
(EC2/EC3/EC7 con Anejo Nacional espanol [confirmar AN]).

## 2. Flujo (IFC-driven)
`caso-PUE-07-vigas-artesa/PUE-07.ifc` → `ifc_to_model_estructural`
(parser C1) → `desde_ifc` (adaptador) → idealizacion → `motor-fem` (C5) → IAP-11 →
comprobacion → resultado + write-back al IFC (`Pset_Estructurando_ResultadoPuente`).

## 3. Resultado
- **VEREDICTO: CUMPLE** · aprovechamiento maximo **0.807**.
- Frecuencia fundamental f1 = **2.87 Hz**.

## 4. Conclusion
El predimensionado **CUMPLE**. Resultado de asistencia; revisar y firmar (ICCP).
