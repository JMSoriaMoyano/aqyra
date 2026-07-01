# ROADMAP cebo / anzuelo — Aqyra

**Horizontes Ahora / Siguiente / Después · Cuña de entrada: Autónomo (volumen + dato)**
*v0 — 2026-06-26. Plano hacia delante del hilo de estrategia. Sustituye a ninguna versión previa.*

> Disciplina del roadmap: cada ítem responde a **¿ensancha el embudo (cebo) o profundiza el foso (anzuelo)?** y **¿preserva el salto abierto→valor?**. Cada ítem se entrega como **evolución de contrato** bajo el sello de dos llaves: **bump → golden → adoptar si verde**. Este hilo corre en paralelo a la ejecución de N1.1; no depende de ella.
>
> ✅ **Bindings reconciliados contra `contratos-golden/` (2026-06-26).** Esquema vigente del ecosistema: **C1** parser/IFC · **C4** red · **C5** motor-fem · **C6** corpus golden · **C7** operador IA · **C8** intercambio CDE. **(C2–C3 sin asignar.)** Tres ítems caen **fuera** del esquema de contratos de interfaz —son capa operativa/comercial o contrato nuevo a crear— y van marcados como tal.
>
> **Dos hallazgos del cruce que reordenan el plan:**
> 1. **C5 v0 CERTIFICADO — dos llaves cumplidas.** `contratos/C5_motor-fem.md` (incluye familia lámina) + **golden 7/7 VERDE** (Llave 1, QA). **Llave 2: firma GPG de JM (EDDSA 8FD1…E0942, 2026-06-26 12:53 UTC) sobre `release.manifest.json`**, verificada en su máquina ("Good signature [ultimate]"). Cadena confirmada byte a byte: la firma sella el manifiesto, que ancla la golden C5 v0 (run_id N1.1-decopak-2026-06-26) y el sha256 de `motor-fem-v0.1.0.plugin` (`9239c2…866ae`, recomputado y coincidente). El motor del anzuelo no hay que construirlo ni firmarlo: hay que **surfacarlo** como entregable firmable. *(Pendiente solo cosmético: los docs de estado de `contratos-golden` y el texto del manifiesto aún rezan "pendiente" — reconciliar SOLO en los docs sin firmar; NO editar el manifiesto firmado o se invalida la firma.)*
> 2. **El mismo motor sirve el cebo y el anzuelo.** Predim gratis y memoria firmable usan **el mismo C5/C4**; lo que los separa **no es el motor, es la doble puerta del muro**: (a) **pago** (capa comercial) + (b) **certificación** (dos llaves de C8 §6: golden verde + QA + firma JM). El cebo es el motor sin puerta; el anzuelo es el motor con las dos puertas.

---

## 1. Decisiones de monetización consolidadas (cierre del bloque)

1. **Dos mostradores, no uno.**
   - **Mostrador A — productores** (autónomo, despacho): **licencia por PROYECTO, por banda de PEM**. Desbloquea todos los entregables firmables del proyecto. Habla el idioma del sector (% de PEM), escala con el valor.
   - **Mostrador B — validadores e institucional / alta frecuencia** (ayuntamiento, tier "Pro" del autónomo y del random): **suscripción** (por puesto o por volumen de revisiones). Captura a quien **nunca cruza el muro de producción**.
2. **El token es COGS interno + guardarraíl de margen, jamás precio.** El cliente paga por valor (el proyecto), no por consumo. El COGS de un proyecto completo de 3 M€ PEM (~90 M tokens) es ~500 €, calderilla frente a 150–250 k€ de honorarios → margen bruto objetivo **88–91 %**.
3. **Muro de cobro = el export del entregable firmable.** Por debajo del muro (visor, editor, auditoría, predimensionado, ver resultados) el producto **se siente gratis**. El muro vincula en el instante en que el documento adquiere valor legal/contractual.
4. **Foso-conocimiento, distinción quirúrgica:** el **dato crudo** es del cliente y **abierto**; los **patrones/criterios aprendidos (anonimizados)** son de Aqyra. El moat es el modelo entrenado, no el dato en bruto. Requiere contrato de datos explícito desde el día uno.

**Tarjeta de precios de referencia (Mostrador A):** <0,5 M€ → 1.500 € · 0,5–2 M€ → 4.000 € · 2–5 M€ → 9.000 € · 5–20 M€ → 20.000 € · >20 M€ → 40.000 €. (≈ 0,2–0,6 % del PEM. A calibrar con datos reales de los primeros clientes.)

---

## 2. La cuña elegida: Autónomo, y qué reordena

**Por qué.** Es la cuña más barata de adquirir y la que más rápido hace crecer el foso real —dato y aprendizaje de la IA— mientras el ingreso madura por detrás. El autónomo usa el cebo en ~26 proyectos/año y paga en ~6; ese 77 % de uso gratis no es desperdicio, es el volante que alimenta el modelo.

**Tres reordenamientos que la cuña fuerza:**

- **El tope de uso justo deja de ser opcional.** Con volumen de autónomos en predim gratis, el COGS de free-riders es la única fuga. El guardarraíl de token va en la **primera entrega**.
- **El primer anzuelo NO es el motor C5.** El autónomo *sobre todo* necesita redacción documental (urbanística, CTE). Es su máxima disposición a pagar **y** el de menor coste de construir (las skills CTE ya existen, no requieren FEM). → Primer entregable firmable = **memoria CTE + justificación urbanística**. El motor pesado **C5 se difiere a Siguiente**.
- **El ayuntamiento baja a Después.** Es el efecto-red más fuerte (el regulador adopta → arrastra productores), pero la elección de cuña lo pospone. Queda marcado como **palanca pull-forward**: si el volante de dato madura antes de lo previsto, se adelanta.

---

## 3. PISTA CEBO — ensanchar el embudo

*Trabajo: adopción, baja fricción, confianza, dato que entra. Debe seguir siendo genuinamente abierto y útil aunque no se pague.*

| Horizonte | Ítem | Contrato | Golden previsto (verde = adoptar) |
|---|---|---|---|
| **AHORA** | Visor/editor IFC robusto (navegación 3D, propiedades, Psets, árbol espacial, color/visibilidad por clase) | **C1** (parser/IFC) | Abre y navega el IFC de referencia sin romper; propiedades coherentes con el modelo |
| **AHORA** | **Skin Diseño** (presentación de dominio; renombrada desde "Arquitectura", JM 2026-06-26) | **C1** (parser/IFC) | La skin presenta su vista sin degradar el visor base |
| **AHORA** | **Predim GRATIS estructuras** (motor a baja fidelidad, sin export) | **C5** (motor-fem) | Predim de referencia coincide con el golden de su familia dentro de tolerancia |
| **AHORA** | **Predim GRATIS instalaciones** (red, sin export) | **C4** (red) | Predim de red de referencia cierra balance dentro de tolerancia |
| **AHORA** | Auditoría IFC básica (nomenclatura, Psets, calidad) — cebo de confianza | **C1** (parser/IFC) | Reporta no-conformidades correctas del IFC de referencia |
| **AHORA** | **Tope de uso justo (guardarraíl de token)** — protege el COGS del volumen autónomo | *fuera del esquema — capa operativa* | Un free que supera el cap es frenado/derivado a Pro; COGS/usuario acotado |
| **SIGUIENTE** | BCF / IDS / incidencias — colaboración sobre el modelo abierto | **C8** (O3 BCF, O4 IDS) | Ciclo de incidencia (crear→asignar→cerrar) sobre el modelo de referencia |
| **SIGUIENTE** | Skins adicionales: Instalaciones, BIM Manager | **C1** (+ **C4** red) | Cada skin presenta su dominio sin degradar el visor base |
| **SIGUIENTE** | Predim multidisciplinar más rico | **C5** + **C4** | Predim coherente cruzando 2+ disciplinas |
| **DESPUÉS** | Write-back de propuestas al modelo abierto | **C1** (Psets) + **C8** (O2) | Propuesta escrita al IFC y publicada sin pérdida de información |
| **DESPUÉS** | Integración CDE (repositorio del equipo paralelo) | **C8** (intercambio CDE) | Estados S0–S7 sincronizados; entregables trazados |
| **DESPUÉS** | Skins Puentes / Obras lineales | **C1** + **C5** (puentes) / **C4** (lineales) | Cada skin abre su tipología de referencia |

---

## 4. PISTA ANZUELO — profundizar el foso

*Trabajo: defensibilidad, valor que se firma y se cobra. Vive entero aquí, porque el cebo es abierto por diseño.*

| Horizonte | Ítem | Contrato | Golden previsto (verde = adoptar) |
|---|---|---|---|
| **AHORA** | **Primer entregable firmable: memoria CTE + justificación urbanística** (cumplimiento de códigos técnicos). Máxima WTP del autónomo, menor coste de build (no usa FEM) | **C7 v0** (operador IA) — *DRAFT redactado 2026-06-26* | `GOL-CTE-01` / `GOL-URB-01` verdes (conformidad + grounding) + firma JM |
| **AHORA** | **Acción de muro: export del entregable firmable** (el clic de pago) | *capa comercial (pago)* + **C8 §6** (certificación, dos llaves) | Export bloqueado sin licencia; certificación solo con golden verde + QA + firma JM |
| **AHORA** | **Contrato de datos** (crudo del cliente y abierto / patrones aprendidos anonimizados) | **C2 v0** (datos) — *DRAFT redactado 2026-06-26; C3 reservado* | `GOL-DAT-01` verde (ataque de re-identificación fracasa) + revisión jurídica + firma JM |
| **SIGUIENTE** | **Surfacar C5 v0 como memoria de cálculo firmable** (barra/lámina/modal + EC2/3/5/7). *El motor YA existe y está firmado: DRAFT + golden 7/7 verde + Llave 2 GPG de JM (2026-06-26); el trabajo restante es solo productizarlo* | **C5 v0** (firmado) | ✅ 7 fichas DEC-* verdes + firma GPG JM. Pendiente: anclar versión (P4) y reflejar firma en docs de estado |
| **SIGUIENTE** | Memoria automática en **formato del despacho** (caratula/veredicto, tablas, diagramas N/V/M) | **C7** (operador IA) + **C8** (O7 documental) | Maquetada en formato despacho; el veredicto refleja las comprobaciones |
| **SIGUIENTE** | Presupuesto + mediciones del proyecto de ejecución; pliego de condiciones | **C1** (mediciones del modelo) + **C7** (precios/doc) | Mediciones del modelo + presupuesto cuadran con el caso de referencia |
| **DESPUÉS** | **Mostrador B: suscripción institucional de validación (ayuntamiento)** — la cuña diferida que arrastra demanda | **C1** + **C8** (O4 IDS) + *capa comercial* | El técnico municipal valida urbanística+CTE de un proyecto recibido y emite veredicto |
| **DESPUÉS** | Más tipologías empaquetadas: puentes, obras lineales, instalaciones avanzadas | **C5+** (puentes) / **C4** (lineales, instalaciones) | Cada tipología verde en su caso de referencia |
| **DESPUÉS** | Sismo (el 5c diferido) | **C5c** (extensión motor-fem) | Combinación sísmica verde en el caso de referencia |
| **DESPUÉS** | Certificación | **C8 §6** (dos llaves) + *gobierno* | Sello emitido sobre un entregable firmable con las dos llaves |

---

## 5. Ruta crítica: el embudo Decopak de punta a punta

La cuña autónomo se demuestra con **una sola ruta excelente**, no con seis skins a medias. Esa ruta ya existe y es **Decopak**:

> **IFC de masas → predim de solución (arquitectura + estructura) [cebo, gratis] → memoria CTE/urbanística [anzuelo, muro] → export firmable [pago].**

Todo el horizonte "Ahora" debe converger en hacer esta ruta impecable antes de abanicar a otras disciplinas o tipologías. Es la demo de conversión, no un caso de uso más.

---

## 6. Asunción más arriesgada (a probar primero)

**La tesis de conversión del autónomo:** que un autónomo que usa el predim gratis en ~90 % de sus proyectos **cruce el muro** en los que sí se contratan, en lugar de quedarse para siempre en el lado gratis. Todo el agregado depende de la **tasa de conversión free→muro** y de la **tasa de maduración** (cuántos autónomos llegan a pagar). Son los dos números que mueven el ARR proporcionalmente.

**Siguiente paso sugerido:** un research plan / experimento barato para medir la disposición real del autónomo a pagar por la memoria CTE/urbanística al contratar un proyecto — antes de invertir en el motor C5.

---

## 7. Qué falta confirmar

**Huecos de contrato (estado):**
- ✅ **C7 v0 (operador IA) REDACTADO** (`contratos/C7_operador-ia.md`, DRAFT 2026-06-26). Garantías sustitutivas del no-determinismo: propuesta / trazabilidad / grounding / conformidad. Falta: **sembrar `GOL-CTE-01` y `GOL-URB-01`** (golden de conformidad) + firma JM.
- ✅ **C2 v0 (datos) REDACTADO** (`contratos/C2_datos.md`, DRAFT 2026-06-26; C3 reservado). Distinción crudo/aprendido con de-identificación como golden anti-re-identificación. Falta: **sembrar `GOL-DAT-01`** + **revisión jurídica** (RGPD / PI / responsabilidad civil) + firma JM.
- **C5 v0 — CERTIFICADO (dos llaves).** Llave 2 firmada y **verificada**: firma GPG sella `release.manifest.json`, que ancla la golden C5 v0 y el sha256 de `motor-fem-v0.1.0.plugin` (recomputado, coincidente). Solo queda lo **cosmético**: reconciliar los docs de estado sin firmar (`C5_motor-fem.md` PROPUESTA→FIRMADO, `golden/README.md` Llave 2) para que apunten al `.asc`. **No tocar el manifiesto firmado** (invalidaría la firma). La versión que pasa la golden ya está anclada en el manifiesto (motor-fem 0.1.0 / motor-calculo 0.23.0→tag 0.1.0).
- **C2–C3 sin asignar** en el esquema del ecosistema: decidir si el contrato de datos ocupa uno de ellos.

**Decisiones de negocio aún abiertas:**
- **Calibrar la tarjeta de precios por banda de PEM** con los primeros clientes (hoy fijada en ~0,3 % del PEM).
- **Suscripción del despacho vs pago por proyecto** dentro del Mostrador A (recurrencia vs barrera de entrada baja).
- **Diseño del tope de uso justo**: dónde cae el cap y cómo se deriva a Pro sin estrangular el cebo.
