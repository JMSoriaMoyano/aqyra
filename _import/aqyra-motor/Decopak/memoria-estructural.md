# Memoria estructural - DECOPAK

> Memoria por obra (no mezclar con otros proyectos).
> Leída por las skills del plugin `estructuras-eurocodigos` al iniciar.
> Documento de trabajo: **todo cálculo debe ser revisado y firmado por técnico competente**.
> Criterios transversales heredados de `../criterios-despacho.md`.

## Datos del proyecto
- Proyecto / emplazamiento: **Decopak** — Rubí (Vallès Occidental), provincia de Barcelona
- Tipología y uso (categorías EC1, EN 1991-1-1 §6.3): **Edificio de oficinas — Categoría B**
  - qk y Qk de sobrecarga de uso a fijar con la geometría (EN 1991-1-1 tabla 6.2 + AN) [confirmar AN]
- Anejo Nacional aplicado: **España**
- Clase de exposición / durabilidad (EC2, EN 1992-1-1 §4.2, tabla 4.1):
  - **Elementos interiores (vigas, pilares, forjados en ambiente seco): XC1**
  - **Cimentación y elementos en contacto con el terreno: XC2** (revisar agresividad química del terreno con informe geotécnico → posible clase XA)
  - **Elementos exteriores: XC3 (protegidos de lluvia) / XC4 (expuestos a lluvia)**
  - Justificación: emplazamiento interior (~30 km de la costa), sin ambiente marino ni sales de deshielo → no procede XS ni XD. [confirmar con condiciones reales del edificio]
- Zona / acción sísmica (NCSE-02 / EC8 EN 1998):
  - Coeficiente de contribución **K = 1,0** (Cataluña).
  - Aceleración sísmica básica **ab < 0,04·g**: Rubí no figura en el Anejo 1 de NCSE-02 (que solo lista municipios con ab ≥ 0,04·g). [confirmar NCSE-02 Anejo 1]
  - Importancia de la construcción: **normal** (oficinas, NCSE-02 §1.2.2).
  - Conclusión: por NCSE-02 §1.2.3, **la aplicación de la norma sismorresistente no es obligatoria** en construcciones de importancia normal cuando ab < 0,04·g → no se considera acción sísmica de cálculo en el predimensionado.
  - Recomendación: confirmar ab exacto de Rubí en el Anejo 1; vigilar la futura **NCSR-22** (en tramitación), que puede modificar parámetros. [confirmar AN]

## Materiales adoptados
- Hormigón estructural: **C30/37** (fck = 30 MPa) — recubrimientos según clase de exposición por elemento (EC2 tabla 4.4N + AN).
- Acero pasivo (armaduras): **B500S** (fyk = 500 MPa).
- Acero estructural: **S275JR** (fy = 275 MPa, t ≤ 16 mm).
- (Madera u otros: a definir si la solución lo requiere.)

## Hipótesis y criterios
- Acciones y combinaciones de referencia: EC0 (EN 1990) §6.4 (ELU) y §6.5 (ELS); cargas EC1 (EN 1991-1-1 cat. B, viento EN 1991-1-4, nieve EN 1991-1-3). A concretar con la geometría. [confirmar AN]
- Coeficientes parciales y de flecha: heredados de `../criterios-despacho.md` (flecha total L/300, activa L/500).
- Sismo: no determinante en predimensionado según conclusión anterior (revisar si cambia la importancia o el uso).

## Registro de comprobaciones (fechado)
- **[2026-06-18] Configuración del proyecto / skill `criterios-memoria`**
  - Materiales adoptados: hormigón **C30/37**, acero pasivo **B500S**, acero estructural **S275JR**.
  - Exposición: **XC1** (interior) / **XC2** (cimentación) / **XC3–XC4** (exteriores) — EC2 §4.2.
  - Acción sísmica: **ab < 0,04·g, K = 1,0**, importancia normal → no obligatoria la consideración sísmica de cálculo (NCSE-02 §1.2.3) [confirmar Anejo 1].
  - Resultado (aprovechamiento de la viga): **no procede** — en este hilo no se dimensiona viga. Se decide pasar a **planteamiento comparativo de soluciones estructurales** sobre la geometría que se aportará en el siguiente hilo.
  - Decisión / próximo paso: recibir geometría del edificio y proponer alternativas estructurales (forjados/pórticos en hormigón EC2, acero EC3, mixto EC4) para comparación.
