# Criterios de despacho - Instalaciones

> Capa transversal de memoria (se acumula entre todos los proyectos de instalaciones).
> Las skills del plugin `instalaciones` LEEN este archivo al iniciar: mantener formato y ubicación estables.
> Todo resultado derivado debe ser **revisado y firmado por técnico competente** (Ingeniero de Caminos).
>
> **Formato de las memorias:** seguir `formato-memoria-calculo.md` (raíz) y la plantilla
> Word `Plantilla_Memoria_Calculo.docx`, comunes a todas las disciplinas.

## Normativa
- Anejo Nacional / reglamento por defecto: **España**
- Normas de referencia (PCI): **RIPCI** (RD 513/2017), **UNE-EN 671-1/-2** (BIE),
  **UNE 23500** (abastecimiento de agua contra incendios), **DB-SI SI4** (dotación de
  instalaciones de protección). Rociadores: **UNE-EN 12845** (pendiente).
- Eléctricas: **REBT** (RD 842/2002) ✅ — **ITC-BT-10** (previsión de cargas), **ITC-BT-25**
  (circuitos de vivienda C1–C12, electrificación básica/elevada), **ITC-BT-19** (caídas de
  tensión e intensidades admisibles), **ITC-BT-44/-47** (receptores/motores). Clima:
  **RITE / DB-HE** (esbozado).

## Materiales / componentes habituales
- Tubería de acero (galvanizado), rugosidad absoluta ~0,045–0,15 mm (def. 0,045 mm) [confirmar AN].
- BIE-25 (manguera semirrígida DN25) y BIE-45 (manguera plana DN45).
- Grupo de presión contra incendios (fuente) según UNE 23500.

## Coeficientes y criterios
- **Pérdida de carga: Darcy-Weisbach** (fricción Swamee-Jain, aprox. de Colebrook-White) [confirmar criterio].
- Fluido agua a 20 °C: ρ=998 kg/m³, ν=1,01·10⁻⁶ m²/s [confirmar AN].
- **Mayoración por accesorios** (pérdidas localizadas): +20 % sobre la fricción (def.), a falta de longitudes equivalentes [confirmar AN].
- **Velocidad máxima admisible**: 6,0 m/s [confirmar AN].
- **PCI–BIE**: 2 BIE hidráulicamente más desfavorables **simultáneas**; presión dinámica mínima 200 kPa (2 bar), máxima 500 kPa (5 bar); caudal de cálculo por BIE-25 1,6 l/s; autonomía 60 min [confirmar AN]. El **dato del proyecto** (IFC) prevalece sobre el valor por defecto.
- **PCI–rociadores (UNE-EN 12845)**: demanda por **densidad de descarga × área de operación** según clase de riesgo (LH 2,25 mm/min·84 m²; **OH1–OH3 5,0 mm/min·72 m²**; OH4 5,0·90; HHP1/2/3 7,5/10,0/12,5 mm/min·260 m²); cobertura por rociador LH 21 / OH 12 / HHP 9 m²; **K** del rociador (Q=K·√p; LH 57 / OH 80 / HHP 115); nº rociadores del área desfavorable n=⌈A_op/A_cob⌉; presión en boquilla del más desfavorable (Q_min/K)² con piso 0,35 bar; duración LH 30 / OH 60 / HHP 90 min [confirmar AN].
- **Reparto en red mallada**: **Hardy-Cross** (corrección por lazo, n=2) — continuidad en nudos + pérdida de carga nula por lazo [confirmar criterio].
- **Eléctricas (REBT)**: redes de BT **radiales (árbol)**; método **híbrido** — sección propuesta
  por **momentos eléctricos** sobre catálogo normalizado (1,5…240 mm²) + **intensidad admisible**
  (ITC-BT-19, Cu/Al, PVC/XLPE, 2 cond. mono / 3 cond. tri), comprobación vinculante de **caída de
  tensión** por el **método de las intensidades** (ΔU=2·L·I·cosφ/(γ·S) mono / √3·L·I·cosφ/(γ·S) tri),
  acumulada y con **redimensionado** automático. Conductividad γ Cu 56 / Al 35 m/Ω·mm² (20 °C);
  caída máx. **3 % alumbrado / 5 % fuerza** (interior); tensiones 230 V mono / 400 V tri. Reactancia
  despreciada (gancho para añadirla) [confirmar AN].

## Lecciones aprendidas (crece hilo a hilo)
- [2026-06-22] El **núcleo da la topología, el solver calcula** (frontera PT 4.1/4.2): el grafo nodos+tramos y la lectura IFC MEP son del núcleo / `iso19650-openbim`; demanda y solver son de `instalaciones`. / Reúso sin reescribir la fontanería. [caso PCI-01]
- [2026-06-22] **Bases de demanda = el "slot" C4** de las disciplinas no estructurales (análogo a las acciones EC0/EC1 en estructuras): simultaneidad, caudales y presiones de cálculo. [caso PCI-01]
- [2026-06-22] El **dato del proyecto (IFC)** de caudal/presión por terminal prevalece sobre el valor normativo por defecto; documentar `fuente_dato`. [caso PCI-01]
- [2026-06-22] **Mallas por Hardy-Cross** (PT 4.4): el núcleo da la topología y el nº de lazos (m−n+componentes); el solver resuelve el reparto hiperestático imponiendo continuidad + cierre de pérdida por lazo. El **árbol es el caso de 0 lazos** (sin regresión). El arnés añade el **cierre por lazo ≈0** al balance de caudales. [caso PCI-02]
- [2026-06-22] **Rociadores = demanda por densidad×área** (UNE-EN 12845), no por simultaneidad fija como BIE: n=⌈A_op/A_cob⌉ rociadores del área más desfavorable, p_min de boquilla derivada de Q=K·√p, y **curva demanda vs abastecimiento** (punto de funcionamiento). Redes típicamente malladas. [caso PCI-02]
- [2026-06-22] **Write-back IFC→cálculo→IFC** (PT 4.4): la **mecánica** de escritura de Psets vive en `iso19650-openbim` (genérica, opción a); la **semántica** (`Pset_Estructurando_ResultadoRed`: DN/caudal/velocidad/presión/margen) en `instalaciones`; la orquestación, en el agente (aislamiento de runtime → no hay import entre plugins). [caso PCI-02]
- [2026-06-22] **Segundo solver sobre el mismo grafo** (PT 4.5, REBT): el grafo nodos+tramos del núcleo es **agnóstico al solver**; el vertical eléctrico reutiliza la **propagación por árbol** del hidráulico (BT radial) y solo aporta su física (intensidades, caída de tensión, sección). Patrón replicable a clima (RITE). [caso REBT-01/02]
- [2026-06-22] **La sección del conductor es variable de DISEÑO, no dato de geometría BIM** (decisión PT 4.5): nace en la capa de demanda/criterios de `instalaciones` (el solver la propone), no en el parser de `iso19650`. Por eso el parser NO se tocó; sí se hizo **sistema-aware el validador** (Pset de segmento Pipe/Cable/Duct según `sistema.tipo`). Mismo Pset de resultado (`Pset_Estructurando_ResultadoRed`) con propiedades eléctricas. [caso REBT-01]
- [2026-06-22] **Método híbrido eléctrico**: momentos para PROPONER sección + intensidades (I·R con cosφ) para COMPROBAR (ΔU acumulada) — calca el patrón PCI demanda→proponer DN→verificar Darcy. El arnés es el análogo: balance de potencias (≈0 %) + ΔU ≤ límite + I ≤ admisible. [caso REBT-01]
- [2026-06-22] **Fixtures eléctricos**: el parser MEP casa la clase EXACTA (`el.is_a()`), así que cables/luminarias deben crearse como `IfcFlowSegment`/`IfcFlowTerminal` (no `IfcCableSegment`/`IfcLightFixture`) para que el parser intacto los lea. Evitar tramos **colineales solapados** (el grafo los trocea por intersección T/X → lazo espurio). [caso REBT-02]
- [2026-06-22] **La clase de riesgo PCI (UNE-EN 12845) es un dato de proyecto que el parser lee del IFC si está, y el agente inyecta si no** (INC-12, PT 4.6, `iso19650-openbim` v0.4.3): el dispatcher `aplicar_demanda` enruta a rociadores solo si `sistema.clase_riesgo` está presente (si no, cae a BIE). Convención: el modelador puede dejarla en `Pset_Estructurando_SistemaPCI.ClaseRiesgo` del `IfcDistributionSystem` (el dato del IFC prevalece, como con caudal/presión de terminal); en su defecto la aporta el agente. Sin el Pset (o la inyección), una red de rociadores se predimensiona como BIE → error silencioso (CUMPLE pero con demanda equivocada). [caso PCI-02]

## Formato de memoria
- Una memoria por obra, en su subcarpeta.
- Citar siempre el artículo del reglamento aplicado (RIPCI/UNE/DB-SI).
- Marcar como **[confirmar AN]** los valores NDP no verificados.
- Registro de comprobaciones fechado (AAAA-MM-DD): sistema / solver / parámetros / resultado (caudales, presiones, margen, veredicto) / decisión.
- Unidades SI (longitud m, caudal l/s, presión kPa, DN mm).
