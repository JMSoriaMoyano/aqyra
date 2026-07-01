# Continuar el motor de cálculo estructural en un hilo nuevo

Copia y pega el bloque de abajo al iniciar un hilo nuevo en el proyecto **Estructurando**.
Da el contexto de lo ya construido y propone los siguientes casos de uso.

---

## Mensaje para pegar en el hilo nuevo

Estoy desarrollando, dentro de Estructurando, un **motor de cálculo estructural
IFC → FEM → Eurocódigos** que ya está empaquetado como plugin
(`motor-calculo-estructural.plugin`) con el agente **ingeniero-estructurista**.

**Lo ya construido y validado** (núcleo estable + catálogo de casos, cada uno con
IFC de prueba → modelo neutro → solver FEM (PyNite) → combinaciones ELU/ELS →
verificación Eurocódigos → mapas/diagramas → memoria Word):

- **Barras / pórtico de acero** (EC3, sección + pandeo), validado contra anaStruct.
- **Láminas (placa MITC4, certificada vs Timoshenko):**
  - Losa sobre vigas (EC2: flexión, flecha, punzonamiento, fisuración).
  - Losa plana sobre pilares (+ **dimensionamiento de punzonamiento**: canto/armadura/capitel).
  - Cubierta / forjado inclinado (flexión + membrana).
  - Muro de carga (compresión + esbeltez §12/§5.8).
- **Cimentación superficial:** zapata aislada sobre lecho elástico (EC7 + EC2).
- **Regiones D:** encepado por **bielas y tirantes** (EC2 §6.5), reutilizando el solver de barras.
- **Cimentación profunda:** pilote (EC7 axil + lateral viga-sobre-muelles + sección EC2).

**Convenciones validadas:** ejes X,Y horizontales y Z vertical; placa con momentos
[Mx,My,Mxy] (carga gravitatoria → sagging negativo = tracción inferior); peso propio
como A·ρ·g; los picos en apoyos/cargas puntuales son singularidades (usar valor en
sección crítica). Todo es **predimensionado**, a revisar y firmar por técnico competente;
Anejo Nacional España, NDP marcados como [confirmar AN].

**El enfoque** es "núcleo estable + catálogo que crece caso a caso" (ver
`Hoja-de-ruta_v2_Motor-calculo-estructural.md`). Cada caso nuevo sigue la misma receta
de 7 pasos y reutiliza el núcleo.

**Quiero seguir incorporando casos de uso.** Propón el orden y empecemos por el que
indiques abajo. Candidatos de la hoja de ruta:

1. **Forjado colaborante / viga mixta acero-hormigón (EC4)** — sección mixta, conexión
   a cortante (conectores), ancho eficaz, flecha con coeficiente de equivalencia,
   fases constructivas.
2. **Muro de contención y muro con anclajes al terreno (EC7)** — empujes, estabilidad
   (vuelco/deslizamiento/hundimiento), fuerzas de anclaje, flexión del muro.
3. **Losa de cimentación (raft) sobre lecho elástico** — extensión directa de la zapata.
4. **Pantallas / núcleos a cortante en su plano + sísmico EC8** (modal/espectral).
5. **Pretensado (EC2 §5.10)**, **uniones**, **fuego/fatiga**, **no-lineal/2º orden**
   (algunos pueden requerir OpenSeesPy).

Empecemos por: **[ELIGE UNO]**.

---

## Notas internas (para mí)

- Estructura del trabajo en carpetas `Fase1..Fase5` con `scripts/` y `proyecto-*`.
- Plugin en la raíz del proyecto: `motor-calculo-estructural.plugin` (instalable).
- Archivos temporales de previsualización (`pg-*.jpg`, `p-*.jpg`, `*.pdf`) en algunas
  carpetas `proyecto-*` se pueden borrar; los creó LibreOffice.
- Patrón por caso: `generate_test_ifc_*.py` → `run_all_*.py` (parser+solver+verificación+plots)
  → `generate_memoria_*.js`. Validación: autodiagnóstico / cruzada + equilibrio ~0 %.
- Dependencias: `pip install ifcopenshell PyNiteFEA anastruct matplotlib numpy --break-system-packages`;
  `npm install docx` (memorias, usar `NODE_PATH=$(npm root -g)`).
