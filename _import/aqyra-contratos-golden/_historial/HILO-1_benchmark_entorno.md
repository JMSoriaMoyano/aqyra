# Benchmark de mercado — Entorno abierto openBIM (Visor + CDE + Gestión de incidencias)

**Proyecto "Entorno" · HILO-1 · Analista de producto (IA) · Documento de insumo para decisión (no decide) · pendiente de lectura de JM**
**Fecha de elaboración: 2026-06-24.** Todas las fuentes se consultaron en esa fecha. *Este documento sustituye al brief de HILO-1: es el contenido del benchmark, ejecutado search-first.*

## Nota de método

- **Search-first**: cada capacidad relevante (IFC, BCF, IDS, API, ISO 19650, precio, licencia) se verificó contra fuente, priorizando webs de producto, documentación de desarrollador y buildingSMART.
- Se marca cada afirmación como **[V] verificado** (fuente oficial localizada) o **[I] inferido / incierto** (no confirmado en fuente primaria; se señala). **No se ha inventado ningún precio, funcionalidad ni licencia.** Las licencias OSS se leyeron del fichero `LICENSE` del repo.
- En este sector el precio es casi siempre *contactar ventas*: se dice explícitamente cuando es así. Los precios de terceros (agregadores) se marcan como orientativos/inciertos.
- **Correcciones a la lista semilla** detectadas durante la investigación:
  - "Open IFC Viewer (ifcopenshell)" mezcla dos cosas distintas: **openifcviewer.com es de Open Design Alliance (ODA)**, propietario-gratuito; el toolkit open source es **IfcOpenShell (LGPL-3.0)**. Se documentan ambos.
  - **Solibri Anywhere** es legacy / no se vende a nuevos clientes (sustituido por tiers Starter/Essential).
- **Marco normativo de referencia** (verificado en buildingSMART/ISO): IFC = **ISO 16739-1:2024**, con **IFC4.3** aprobado como estándar final (anuncio bSI 2024-01-04). **BCF 3.0** es la versión vigente (release final GitHub jun-2021, presentación ago-2021); coexiste BCF 2.1. **IDS 1.0** es estándar oficial buildingSMART desde el **1-jun-2024**. Los **4 estados ISO 19650** (WIP / Compartido / Publicado / Archivado) se anclan conceptualmente en **ISO 19650-1:2018**.

---

## 1. Matriz comparativa

**Leyenda de cobertura:** ●=cubre nativo · ◐=parcial/vía conversión o integración · ○=no/incierto · — = fuera de alcance.
**Fases:** Dis.=Diseño (coordinación/clash/BCF) · Cons.=Construcción (obra/tablet/snagging).
**Apertura BCF:** F=fichero · API=BCF-API REST estándar.

### A) Plataformas / CDE

| Herramienta | Visor IFC | CDE (ISO19650) | Incidencias | IFC4.3 | BCF | IDS | API agente | Estados 19650 | Obra/tablet | Precio | Dis. | Cons. |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---|:--:|:--:|
| **Autodesk ACC** | ● | ● | ● | ○ [I] | F 2.1 | ○ (3os) | ●● APS | ◐ carpetas | ● ACC/PlanGrid | ~1.625 USD/u/año [V] | ● | ● |
| **Trimble Connect** | ● | ● | ● | ● 4.3.2 [V] | **API 2.1+3.0** [V] | ○ [I] | ●● REST+SDK | ◐ | ● web+app | Free + pago [V] | ● | ● |
| **Bentley ProjectWise** | ◐ vía iModel | ● (19650 preconfig) | ◐ nativa | ● 4.3 [V] | ◐ débil [I] | ○ [I] | ●● iTwin | ● preconfig [V] | ● WorkSite | Contactar ventas [V] | ● | ◐ |
| **Oracle Aconex** | ● | ● (Kitemark) | ● | ○ [I] | **API 2.0/2.1** [V] | ○ [I] | ● REST (registro) | ● [V] | ● Aconex Field | Contactar ventas [V] | ● | ● |
| **Asite (Adoddle)** | ◐ 3D Repo | ● | ● | ○ [I] | F [V] | ○ [I] | ● REST | ◐ [I] | ● Asite Field | ~70 USD/u (CDE) [V] | ● | ● |
| **Thinkproject** | ● VDC | ● (TÜV cert.) | ● | ○ [I] | F [V] | ○ [I] | ● VDC/CDE API | ◐ [I] | ◐ Field Mgr | Contactar ventas [V] | ● | ◐ |
| **Catenda Hub** | ● | ● **(19650 nativo)** | ● | ○ [I] | **API 2.x+3.0** [V] | ● (claim) [V/I] | ●● REST+SDK | ● nativo [V] | ◐ web [I] | Contactar ventas [V] | ● | ◐ |
| **Dalux** | ● gratis | ● Box | ● Field | ○ [I] | F connector [V] | ○ [I] | ● REST (key) | ● Box [V] | ●● Field +1M | Free + pago [V] | ● | ●● |
| **usBIM (ACCA)** | ● | ● (cert. IFC) | ● bcf | ● (decl.) [V] | **API** [V] | ●● IDS 1.0 [V] | ◐ BCF/bSDD | ◐ GATES [I] | ● 100% web | Free + pago [V] | ● | ◐ |
| **Newforma Konekt** | ● | ● | ●● (ex-BIM Track) | ○ [I] | **API** [V] | ○ [I] | ●● REST v3 | ◐ [I] | ● Konekt Mobile | Contactar ventas [V] | ● | ● |

### B) Visores openBIM (incl. open source) y checkers

| Herramienta | Tipo | IFC4.3 | BCF | IDS | API/headless | Licencia | Obra/web | Precio | Dis. | Cons. |
|---|---|:--:|:--:|:--:|:--:|---|:--:|---|:--:|:--:|
| **That Open (web-ifc / components)** | Lib web OSS | ◐ parcial [I] | API 2.1+3.0 [V] | ● [V] | ●● JS/TS+Node | **web-ifc MPL-2.0; components MIT** [V] | ● navegador | Gratis (libs) [V] | ● | ◐ |
| **Speckle** | Plataforma OSS | ○ [I] | ○ (nativo, no BCF) [I] | ○ [I] | ●● GraphQL+Automate | **Apache-2.0 + 2 módulos EE** [V] | ● web | Gratis self-host [V] | ● | ◐ |
| **IfcOpenShell** | Toolkit OSS | ● 4x3 Add2 [V] | ● [V] | ●● IfcTester [V] | ●● Python/C++ | **LGPL-3.0** [V] | — (lib) | Gratis [V] | ● | — |
| **Solibri** | Checker/QA | ● init. v24.5 [V] | API Live + REST [V] | ◐ [I] | ● REST/OpenAPI [V] | Propietario | ○ desktop | Suscripción [I] | ●● | — |
| **BIMcollab (Zoom/Nexus)** | Checker + issues | ◐ [I] | **API 3.0** [V] | ●● [V] | ● Connection API (BCF) [V] | Propietario | ◐ desktop+web | Free tier [V] | ●● | ◐ |
| **Revizto** | Colab/issues | ○ (exp.4/2x3) [V] | F [V] | ○ [I] | ● REST [V] | Propietario | ● web/tablet/AR | Contactar ventas [V] | ● | ● |
| **BIMvision** | Visor freeware | ○ (2x3/4.0) [V] | F 2.1 [V] | ◐ plugin pago [V] | ◐ plugin Python | Propietario gratis [V] | ○ Windows | Gratis base [V] | ● | — |
| **usBIM.viewer+** | Visor gratis | ◐ [I] | ● [V] | ● [V] | ◐ plataforma | Propietario gratis | ● web+desktop | Gratis 10 GB [V] | ● | ◐ |
| **Open IFC Viewer (ODA)** | Visor gratis | ○ [I] | ◐ plugin [I] | ◐ [I] | ○ (SDK ODA aparte) | Propietario gratis [V] | ○ Windows | Gratis [V] | ● | — |
| **Autodesk Viewer / APS** | Visor web/SDK | ○ (traduce) [V] | ○ [I] | ○ [I] | ●● APS cloud | Propietario | ● web | Free + Flex tokens [V] | ● | ◐ |

### C) Incidencias / campo (foco fase Construcción)

| Herramienta | IFC | BCF | IDS | API agente | Móvil/offline | Precio público | Dis. | Cons. |
|---|:--:|:--:|:--:|:--:|:--:|---|:--:|:--:|
| **PlanRadar** | ● | F export [V] | ○ | ● REST (Pro/Ent) [V] | ●● offline [V] | ~49/159/239 USD/u [I] | ◐ | ●● |
| **Fieldwire (Hilti)** | ◐ [I] | ○ [I] | ○ | ◐ enterprise [V] | ●● offline [V] | **0/39/64/89 USD/u** [V] | ○ | ●● |
| **Dalux Field** | ● 4.x [V] | F connector [V] | ○ [I] | ● REST [V] | ●● offline [V] | Free Basic + ventas [V] | ◐ | ●● |
| **Bulldozair** | ◐ [I] | ◐ [I] | ○ | ◐ enterprise [V] | ●● offline [V] | % presup./facturación [V] | ○ | ●● |
| **Procore** | ◐ [I] | F **2.1** import [V] | ○ | ●● REST (Observations) [V] | ●● offline [V] | ACV, usuarios ilim. [V] | ◐ | ●● |

---

## 2. Fichas breves por herramienta

### Plataformas / CDE

**Autodesk Construction Cloud (ACC / BIM360 / Docs).** Suite cloud líder; Docs=CDE, Build=obra, BIM Collaborate=coordinación. *Fortaleza*: ecosistema y **APS (ex-Forge)**, la API/SDK más potente para traducir y operar modelos/issues. *Límite*: BCF solo por **fichero 2.1** (issues por API propietaria, no BCF-API estándar); IDS no nativo; IFC4.3 en el visor no confirmado. *Precio*: Build ~**1.625 USD/usuario/año** [V]; resto contactar ventas. Estados ISO 19650 por carpetas+permisos, no máquina de estados.

**Trimble Connect.** CDE openBIM-friendly del ecosistema Tekla/Trimble. *Fortaleza*: **BCF-API REST estándar con 2.1 Y 3.0** + OpenAPI + SDK (.NET/JS), **IFC 4.3.2** declarado, **tier gratuito**. *Límite*: IDS no confirmado nativo; estados 19650 por carpetas. *Precio*: free + planes de pago (cifras vía reseller, inciertas). Uno de los mejores para operación por agente.

**Bentley ProjectWise.** CDE de infraestructura; bundle **preconfigurado ISO 19650**. *Fortaleza*: **iTwin Platform** (REST + iTwin.js SDK OSS), IFC4.3 (vía iModel), estados 19650 reales. *Límite*: no es visor IFC puro (convierte a iModel); **BCF abierto débil**; IDS no. *Precio*: contactar ventas. App de campo WorkSite (online/offline).

**Oracle Aconex.** CDE neutral, primero con **BSI Kitemark ISO 19650** [V-parcial]. *Fortaleza*: gobernanza, inmutabilidad, audit trail; **BCF-API REST (OpenCDE)** 2.0/2.1; Aconex Field. *Límite*: IFC4.3 e IDS no declarados; API tras registro Oracle; **sin plan gratuito ni precio público**. *Precio*: contactar ventas.

**Asite (Adoddle).** CDE + capa BIM **3D Repo** (adquirida 2023). *Fortaleza*: **precio público orientativo** (raro): CDE desde **70 USD/85 EUR por usuario**, 3D Repo desde 50 USD [V]; API REST pública. *Límite*: BCF por fichero (versión/BCF-API sin verificar); IDS no (ojo: "IDP" ≠ IDS); IFC4.3 incierto.

**Thinkproject.** CDE NextGen (heredero CONCLUDE, **certificado TÜV SÜD ISO 19650**, feb-2024) + capa BIM VDC. *Fortaleza*: certificación 19650; APIs VDC/DESITE/CDE. *Límite*: BCF por fichero (versión/API sin confirmar); IDS incierto; **100% contactar ventas, sin cifra pública**.

**Catenda Hub (ex-Bimsync).** CDE openBIM noruego (spin-off SINTEF). *Fortaleza*: **el más fuerte en openBIM headless** — REST completa + **OpenCDE/BCF 2.x+3.0** + SDK de visor, **estados ISO 19650 nativos** y afirma **IDS**. *Límite*: app móvil nativa no confirmada; requiere alfabetización BIM; precio contactar ventas (usuarios ilimitados, tier Basic gratis). Candidato fuerte para "integrar".

**Dalux.** Suite con visor BIM gratuito masivo + Box (CDE 19650) + **Field** (obra). *Fortaleza*: **el más fuerte en obra/tablet** (+1M usuarios, offline), tiers gratuitos reales, Box implementa estados CDE. *Límite*: BCF (versión/BCF-API sin confirmar); IDS no confirmado; API REST por API-key (sin OAuth, sin soporte de código). *Precio*: Viewer y Field Basic gratis; módulos por cotización.

**usBIM (ACCA).** CDE cloud "primer CDE certificado IFC por bSI"; 100% navegador. *Fortaleza*: **IDS 1.0 authoring + validación** (usBIM.IDS/IDSeditor) — único verificado junto a la capa OSS; **BCF-API REST**; IFC4.3 declarado; bSDD. *Límite*: sin portal público de API REST propietaria para operar modelos headless (issues sí por BCF-API). *Precio*: freeware + planes de pago por cotización.

**Newforma Konekt (ex-BIM Track).** CDE abierto AEC para coordinación. *Fortaleza*: **REST API v3 completa (OAuth2) + BCF-API** — junto a Catenda, el mejor para agente sobre issues/datos; app móvil nativa offline. *Límite*: IFC4.3 e IDS no documentados; geometría headless no es el foco; precio contactar ventas (cuenta/visor gratis).

### Visores openBIM (incl. open source — clave para "construir")

**That Open Engine (web-ifc / @thatopen/components).** Toolkit JS/WASM web-first. *Fortaleza*: IFC nativo en navegador y **Node headless**, **BCF 2.1+3.0**, **IDS** (crear/validar), ideal para agente. *Licencia* (leída del repo): **web-ifc = MPL-2.0; @thatopen/components = MIT** [V] (no MPL); Three.js MIT. *Límite*: cobertura IFC4.3 parcial/en evolución; librería de desarrollador, no app de usuario; gratis.

**Speckle.** Plataforma de datos + visor web OSS. *Fortaleza*: **automatización headless excelente** (GraphQL + REST + **Speckle Automate** + SDKs Python/JS/.NET). *Licencia*: **Apache-2.0**, pero **open-core** — los módulos `workspaces/` y `gatekeeper/` están bajo **licencia EE propietaria** [V]. *Límite*: trabaja sobre **modelo de objetos, no IFC nativo de fichero**; no es BCF-céntrico ni valida IDS nativo. Gratis self-host.

**IfcOpenShell.** Toolkit OSS de referencia (lib, GUI=Bonsai/Blender). *Fortaleza*: **IFC2x3…4x3 Add2 completo**, **IDS (IfcTester)**, BCF, **Python/C++ totalmente headless** — el mejor encaje para que un agente opere IFC a fichero. *Licencia*: **LGPL-3.0-or-later** [V]. *Límite*: code-first, sin build de navegador nativo. Gratis.

**Solibri.** Checker/QA y clash desktop. *Fortaleza*: IFC fuerte (**2x3/4/4.3 inicial** v24.5), **IDS** (editor+validador), **BCF Live Connector + REST API** (`/bcfxml`). *Límite*: desktop (Anywhere=legacy); no CDE ni campo; curva alta. *Precio*: suscripción; "~280 €/u/mes" es de agregador [I], verificar.

**BIMcollab (Zoom/Nexus).** Checker (Zoom) + gestión de issues cloud (Nexus). *Fortaleza*: **BCF su terreno** — import **BCF 3.0**, **Connection API basada en BCF-API REST**, BCF Managers gratis; **IDS completo** [V]. *Límite*: orientado a coordinación (no app de campo); Zoom desktop. Free tier.

**Revizto.** Hub de colaboración/issues 2D+3D multiplataforma. *Fortaleza*: federación amplia, **REST API**, apps **web/tablet/móvil/AR** (cubre las 2 fases). *Límite*: BCF por fichero (versión sin confirmar); IDS probablemente no; IFC importado a su motor (exporta 4/2x3). Precio contactar ventas.

**BIMvision.** Visor IFC freeware Windows con plugins. *Fortaleza*: gratis (uso comercial incl.), **BCF 2.1** (plugin), arquitectura de plugins. *Límite*: solo **IFC 2x3/4.0** (no 4.3), solo Windows, IDS/Python por plugin de pago. Gratis base.

**usBIM.viewer+.** Visor IFC gratis (desktop+web) de ACCA. *Fortaleza*: gratis, navegador en cualquier dispositivo, **BCF** e **IDS**, bSDD. *Límite*: orientado a la plataforma usBIM, sin SDK abierto. Gratis (10 GB).

**Open IFC Viewer (ODA).** Visor IFC desktop gratuito de **Open Design Alliance** (no es ifcopenshell; no es OSS). *Fortaleza*: gratis, BCF Manager. *Límite*: solo Windows, no web, IFC4.3 e IDS no confirmados; el SDK de desarrollo es el producto comercial ODA aparte.

**Autodesk Viewer / APS.** Visor web hospedado + **SDK JS** embebible. *Fortaleza*: SDK potente, web sin instalación, pipeline cloud. *Límite*: **no IFC nativo** — traduce server-side a formato propietario (SVF2); no BCF/IDS. *Precio*: visor gratis; APS por **Flex tokens** (free mensual + pago por uso, desde 2025-12-08).

### Incidencias / campo (foco Construcción)

**PlanRadar.** Snagging/defectos/documentación SaaS. *Fortaleza*: **Open API REST** (Pro/Enterprise) + Connect + webhooks; móvil **offline**; **export BCF**; curva muy baja. *Límite*: no CDE formal; IDS no; versión BCF sin especificar. *Precio*: por usuario, **dependiente de región** (~49/159/239 USD/u, de agregador [I]); verificar en web.

**Fieldwire (Hilti).** Gestión de campo (tareas/punch/planos). *Fortaleza*: **precios públicos verificados** (**0/39/64/89 USD/usuario/mes** [V]); móvil offline; curva baja. *Límite*: BCF/IFC no confirmados; **API solo en contrato enterprise**; no CDE.

**Dalux Field.** (ver suite Dalux arriba) App de obra insignia, offline, AR/BIM, **Field Basic gratis**, REST API. Mejor en fase Construcción.

**Bulldozair.** Gestión de campo/punch/actas. *Fortaleza*: móvil offline; **precio por % de presupuesto (proyecto) o % de facturación (empresa), usuarios ilimitados** [V]; integra con CDE. *Límite*: IFC/BCF solo afirmados por terceros (sin confirmar oficial); API en Enterprise.

**Procore.** Plataforma de gestión de construcción (US-céntrica). *Fortaleza*: **REST API extensa (Observations API)** para CRUD de incidencias; móvil/campo fuerte; import **BCF 2.1**. *Límite*: IFC versión no confirmada; IDS no; no alineado a estados 19650. *Precio*: por volumen anual (ACV), **usuarios ilimitados**, contactar ventas.

---

## 3. Síntesis: qué cubre el mercado, dónde están los huecos, y lectura adoptar/integrar/construir

**Qué cubre bien el mercado.** La **visualización IFC** y la **gestión documental tipo CDE** están maduras y sobran opciones. La **coordinación de diseño con BCF por fichero** es casi universal. La **fase de construcción en tablet** (snagging, offline) está muy bien servida por Dalux, PlanRadar, Fieldwire, Procore y Bulldozair. Hay incluso una capa **open source potente** (IfcOpenShell, web-ifc/That Open, Speckle) que da base técnica real.

**Dónde están los huecos — y son los que importan para el foso del proyecto:**

1. **BCF-API REST estándar (no solo fichero).** Solo lo confirman **Trimble Connect (2.1+3.0)**, **Catenda (2.x+3.0)**, **Oracle Aconex (OpenCDE)**, **usBIM**, **Newforma** y **BIMcollab (3.0)**. La capa OSS lo cubre con **That Open (2.1+3.0)**. El líder de mercado **ACC es solo fichero 2.1**. Procore, **2.1**. El resto: versión sin verificar. Hueco: pocas plataformas exponen incidencias de forma programática **estándar**.
2. **IDS nativo.** Verificado solo en **usBIM**, **BIMcollab**, **Solibri**, y la capa OSS (**IfcOpenShell/IfcTester**, **That Open**). Catenda lo afirma. **El resto del CDE/plataforma comercial: no, o no confirmado.** Para un **corpus golden verificado por OIR**, la validación IDS tendría que vivir en vuestra capa o apoyarse en estas piezas — es un hueco explotable.
3. **Automatización por agente IA (headless real sobre modelo + incidencias).** Aquí el mercado se parte:
   - **Mejor para issues/datos por API**: Catenda, Newforma (REST v3), Trimble, Bentley iTwin, BIMcollab.
   - **Mejor para operar IFC a fichero, headless**: **IfcOpenShell (Python)** y **web-ifc/That Open (JS/Node)** — pero son librerías, no entornos.
   - **Nadie ofrece "de fábrica" un entorno abierto donde un copiloto opere modelo + incidencias + estados 19650 por API estándar y sin lock-in binario.** Ese es precisamente el espacio del proyecto.
4. **Estados ISO 19650 literales y por API.** Solo **Catenda** (nativo) y **ProjectWise** (preconfig) lo documentan claramente; el resto "alinea" por carpetas/permisos.
5. **Sin lock-in binario + IFC4.3 + API abierta a la vez.** Casi nadie reúne las tres. Trimble y Catenda son los que más se acercan en el lado comercial; la capa OSS lo logra pero sin producto de usuario terminado.

**Primera lectura adoptar / integrar / construir (insumo, no decisión):**

- **CONSTRUIR (núcleo del foso):** la **capa de operación headless openBIM** que ningún producto da cerrada — agente que lee/escribe IFC, valida contra **IDS**, y orquesta el **corpus golden + OIR**. Apoyarse en **IfcOpenShell (LGPL-3.0)** para IFC/IDS server-side y **That Open/web-ifc (MPL-2.0/MIT)** para el visor web embebible. *Atención licencias*: LGPL-3.0 y MPL-2.0 son "weak copyleft" a nivel de fichero/módulo (compatibles con uso comercial manteniendo abierto lo modificado de esas piezas); MIT (components, Three.js) sin fricción. En **Speckle**, vigilar el **open-core**: los módulos `workspaces` y `gatekeeper` son **EE propietaria**, no Apache.
- **INTEGRAR (no reinventar):** el **transporte estándar de incidencias** vía **BCF-API REST** (validar contra Trimble/Catenda/BIMcollab como referencia de interoperabilidad) y, si se quiere un CDE openBIM probado como columna documental, **Catenda Hub** es el más alineado (estados 19650 nativos + API completa + IDS) — el mejor candidato a "socio" interoperable sin lock-in.
- **ADOPTAR (cuando toque obra, sin construir):** para la **fase Construcción en tablet**, **Dalux Field** (gratis, masivo, offline) o **PlanRadar/Fieldwire** (API REST, precios públicos) como front de campo, conectados por API/BCF a vuestro entorno; evita gastar esfuerzo en reconstruir snagging móvil.

**Posición (abierta):** el mercado no ofrece el entorno que el proyecto necesita — abierto, IFC4.3/BCF/IDS, **operable por agente** y **sin lock-in binario** — como un solo producto. Lo más sensato apunta a **construir la capa de agente + IDS/golden sobre OSS** (el foso), **integrar BCF-API y un CDE openBIM como Catenda** para no reinventar gobernanza ISO 19650, y **adoptar apps de campo existentes** para obra. La decisión final (peso de construir vs. integrar, y qué socio de CDE) corresponde a JM.

---

## 4. Fuentes (consultadas 2026-06-24)

**Estándares (buildingSMART / ISO):**
- BCF: https://technical.buildingsmart.org/standards/bcf/ · BCF-API https://github.com/buildingSMART/BCF-API · BCF-XML releases (2.1, 3.0) https://github.com/buildingSMART/BCF-XML/releases · BCF 3.0 (2021) https://www.buildingsmart.org/bim-collaboration-format-bcf-3-0/
- IDS 1.0 (oficial 2024-06-01): https://www.buildingsmart.org/standards/bsi-standards/information-delivery-specification-ids/
- IFC / ISO 16739-1:2024: https://technical.buildingsmart.org/standards/ifc/ · IFC4.3 aprobado (2024-01-04) https://www.buildingsmart.org/ifc-4-3-approved-as-a-final-standard/ · docs https://ifc43-docs.standards.buildingsmart.org/
- ISO 19650-1:2018: https://www.iso.org/standard/68078.html · CDE/estados (UK BIM Framework Part C) https://ukbimframework.org/ · estados (BibLus) https://biblus.accasoftware.com/en/container-information-states-iso-19650-wip-shared-published-archived/
- Certificación IFC: https://www.buildingsmart.org/compliance/software-certification/ifc/

**Plataformas/CDE:** APS https://aps.autodesk.com/developer/documentation · Trimble Connect dev https://developer.trimble.com/docs/connect · Bentley iTwin https://developer.bentley.com · Aconex https://help.aconex.com · Asite API https://ecosystem.asite.com/asite-api-guide · Thinkproject dev https://bimdocs.thinkproject.com · Catenda https://developers.catenda.com · Dalux API https://support.dalux.com/hc/en-us/articles/9544314902556-Dalux-API · usBIM/ACCA https://www.accasoftware.com/en/ifc-viewer-on-line · Newforma/BIM Track https://bimtrackapis.readme.io · https://developer.newforma.cloud

**Visores / OSS:** web-ifc LICENSE (MPL-2.0) https://github.com/ThatOpen/engine_web-ifc/blob/main/LICENSE.md · @thatopen/components LICENSE (MIT) https://github.com/ThatOpen/engine_components/blob/main/LICENSE.md · That Open BCF https://docs.thatopen.com/Tutorials/Components/Core/BCFTopics · That Open IDS https://docs.thatopen.com/Tutorials/Components/Core/IDSSpecifications · Speckle LICENSE (Apache-2.0 + EE) https://github.com/specklesystems/speckle-server/blob/main/LICENSE · specklepy https://github.com/specklesystems/specklepy · IfcOpenShell https://ifcopenshell.org/ · IfcTester docs https://docs.ifcopenshell.org/ · Solibri IFC https://help.solibri.com/hc/en-us/articles/23779405208855 · Solibri REST https://solibri.github.io/Developer-Platform/ · BIMcollab https://www.bimcollab.com/en/developers/developer-sdk/ · BIMcollab IDS https://helpcenter.bimcollab.com/en/articles/327351 · Revizto API https://help.revizto.com/hc/en-us/articles/9420673106063 · BIMvision BCF https://store.bimvision.eu/plugin/ifc__comments__slashh__bcf-25 · usBIM.viewer+ https://www.accasoftware.com/en/ifc-viewer-on-line · Open IFC Viewer (ODA) https://openifcviewer.com/ · Autodesk APS/IFC https://aps.autodesk.com/topics/ifc · APS Flex https://aps.autodesk.com/blog/aps-business-model-evolution

**Campo/incidencias:** PlanRadar API https://help.planradar.com/hc/en-gb/articles/15480453097373-Open-API-Overview · PlanRadar precios https://www.planradar.com/pricing/ · Fieldwire precios https://www.fieldwire.com/pricing/ · Dalux Field Basic https://www.dalux.com/products/dalux-field-basic/ · Bulldozair precios https://www.bulldozair.com/pricing/ · Procore Observations API https://developers.procore.com/documentation/tutorial-observations · Procore BCF 2.1 https://support.procore.com/products/online/user-guide/project-level/coordination-issues/tutorials/import-coordination-issues-from-a-bcf-file

---

*Avisos de fiabilidad:* (1) Versiones exactas de BCF en Revizto, PlanRadar, Dalux, Asite, Thinkproject, ProjectWise: solo "BCF soportado" verificado, no la versión. Versión confirmada solo en Procore (2.1), ACC (2.1), BIMcollab (3.0 import), Trimble/Catenda/Aconex (API). (2) IFC4.3 confirmado solo en Trimble (4.3.2), ProjectWise (vía iModel), IfcOpenShell, Solibri (inicial), usBIM (declarado); resto incierto. (3) Precios por usuario de PlanRadar y Solibri proceden de agregadores (orientativos). (4) IFC/BCF de Bulldozair y Fieldwire no confirmados en fuente oficial. No se inventó ningún precio, licencia ni funcionalidad; lo no verificado va marcado [I].
