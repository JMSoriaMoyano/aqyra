# Hilo 1 — Benchmark de entorno (Visor + CDE + Gestor de incidencias)

> **Estado:** evidencia preparada por la IA (Ing. BIM-IFC / PM) para que **JM decida y firme**. La IA opera y documenta; **no concluye la decisión de compra**.
> **Fecha de consulta de fuentes:** 2026-06-24 · **Método:** search-first (cada dato verificado contra fuente con URL).
> **Convención de fiabilidad:** `[V]` = verificado en fuente citada · `[I]` = inferido / razonado, no leído literalmente.
> **Nota:** *Aqyra* se retira del universo por indicación de JM (no es referente por el momento) y porque no era verificable en fuentes públicas.

---

## 1. Para qué sirve este documento

Estructurando 2.0 desarrollará sus pilotos (Decopak HQ, Terres Cavades) en un **entorno abierto propio**, ad hoc, basado en **IFC (openBIM, texto) + visor + CDE**, sin depender de binario propietario (Revit/Cype). La tesis es que *formato abierto + IA operando nativamente sobre él* es la palanca disruptiva. Antes de decidir **qué adoptamos, qué integramos y qué construimos**, este hilo levanta el **mapa del mercado** en tres capacidades (visor, CDE, gestor de incidencias) y dos fases (diseño y construcción).

Lo que más pesa para la tesis, y por tanto lo que se marca en las matrices:

1. **API REST pública y documentada** (¿puede un copiloto IA operar sin pedir permiso a un partner?).
2. **BCF nativo / BCF-API** (¿el ciclo de incidencias viaja en formato abierto estándar?).
3. **Visor IFC embebible / headless** (¿podemos meter el visor en *nuestro* entorno, o leer el modelo sin GUI?).

---

## 2. Matriz comparativa — eje de la tesis (apertura + automatización por agentes)

Lectura rápida de las tres columnas que deciden si una herramienta encaja en un entorno openBIM operado por IA. Escala: **Alto / Medio / Bajo / No**.

### 2.1 CDE / plataformas

| Herramienta | IFC nativo / visor | BCF | API REST pública | Apta para copiloto IA | Lock-in |
|---|---|---|---|---|---|
| **Catenda Hub** (ex Bimsync) | Sí, visor 2D/3D `[V]` | **BCF-API 2.1** `[V]` | **Sí, pública (Boost)** `[V]` | **Alta** | Muy bajo |
| **Trimble Connect** | Sí, visor web embebible `[V]` | **BCF-API 2.1 y 3.0** `[V]` | **Sí, pública** `[V]` | **Alta** | Alto (ecosist. Trimble) |
| **Autodesk ACC** (Docs/BIM360) | Sí, Viewer APS `[V]` | Import/export, no servidor BCF `[V]` | Sí, pública (APS) `[V]` | Media-Alta | **Alto (.rvt)** |
| **usBIM** (ACCA) | Sí, **CDE IFC certificado bSI** `[V]` | Import/export `[V]` | API/SDK (endpoints poco documentados) `[V/I]` | Media-Alta | Medio (cloud ACCA) |
| **Dalux** | Sí, visor IFC muy rápido `[V]` | Export (2.1) `[V]` | Sí, Swagger, **gated por licencia+key CSM** `[V]` | Media | Medio |
| **Oracle Aconex** | Sí, Model Explore `[V]` | **BCF-API 3.0** (adapter) `[V]` | Sí, REST OAuth `[V]` | Media | Medio (enterprise) |
| **Asite** (Adoddle) | Sí, cBIM web `[V]` | BCF `[I]` | Sí, Open Data API REST/SOAP `[V]` | Media | Alto (enterprise) |
| **Newforma Konekt** | Sí, visor 2D/3D `[V]` | **IFC+BCF nativos** `[V]` | API REST pública no confirmada `[I]` | Media | Bajo |
| **Thinkproject** | Sí, visor 3D `[V]` | BCF `[V]` | VDC API (OAuth2) `[V]` | Media | Alto (enterprise) |
| **Bentley ProjectWise** | Sí, iTwin Design Review `[V]` | **BCF NO nativo** `[V]` | iTwin Platform API `[V]` | Baja-Media | Alto (iModel) |

### 2.2 Visores IFC / openBIM

| Herramienta | Código abierto | IFC | BCF | API/SDK headless | Soporte IA | Plataforma |
|---|---|---|---|---|---|---|
| **That Open Engine** (web-ifc) | **Sí, MPL-2.0** `[V]` | 2x3/4/4x3, lectura **y escritura** `[V]` | vía libs ecosistema `[I]` | **Alto** (JS/TS + C++/WASM) `[V]` | **Alto** | Web (embebible) |
| **Speckle** | **Sí, Apache-2.0** `[V]` | Importador vía IfcOpenShell `[V]` | issues propios, no BCF `[I]` | **Alto** (Python/.NET/JS + GraphQL) `[V]` | **Alto** | Web + conectores |
| **Trimble Connect** | No | 2x3/4 `[V]` | **BCF 2.1/3.0** `[V]` | Workspace API (JS) + .NET SDK `[V]` | Medio | Web+escr.+móvil |
| **Autodesk APS Viewer** | No | Sí (→ SVF propietario) `[V]` | vía servicios `[I]` | Viewer SDK JS embebible `[V]` | Medio | Web (embebible) |
| **Solibri Office** | No | 2x3 cert., 4 parcial, 4.3 inicial `[V]` | **Import + export** `[V]` | REST API (Office/Site) `[V]` | Medio | Escritorio |
| **BIMcollab Zoom** | No | Sí `[V]` | **BCF-API (Connection API)** `[V]` | REST (issues, no modelo) `[V]` | Medio | Escritorio |
| **usBIM.viewer+** (ACCA) | No | hasta IFC4X1/4X2 `[V]` | BCF `[I]` | No SDK público | Bajo | Web + escritorio |
| **Revizto** | No | Import/export IFC `[V]` | BCF por fichero `[I]` | API REST propietaria `[V]` | Bajo-Medio | Web+escr.+móvil |
| **BIMvision** | No (freeware) | 2x3/4 `[V]` | plugin BCF 2.1 `[V]` | SDK de plugins (C++/.NET) `[V]` | Bajo | Escritorio (Win) |
| **Open IFC Viewer** (ACCA) | No | Sí `[V]` | Parcial `[I]` | No | Bajo | Escritorio |

### 2.3 Gestores de incidencias (BCF / field)

| Herramienta | Orientación | BCF nativo (versión) | BCF-API estándar | API REST pública issues | Obra/tablet + offline |
|---|---|---|---|---|---|
| **BIMcollab** | Diseño/coord. | Sí, **2.1** `[V]` | **Sí (conforme bSI, OAuth2)** `[V]` | **Sí, pública** `[V]` | Bajo |
| **Revizto** | Coord. **+ campo** | 2.1, por fichero `[I]` | No (propietaria) | **Sí, pública** `[V]` | **Alto** (Site/V5, AR, offline) |
| **Solibri** | Diseño/QA | 1.0/2.0/2.1 + BCF Live `[V]` | Cliente, no servidor `[V]` | Limitada (API local, sin CRUD remoto) `[V]` | No (escritorio) |
| **Procore** | **Campo**/PM | 2.1, por fichero `[V]` | No (API propia) | **Sí, pública y amplia** `[V]` | **Alto** (offline cacheado) |
| **PlanRadar** | **Campo** + visor BIM | Export (versión s/e) `[I]` | No | **Sí, pública** (Pro/Ent.) `[V]` | **Alto** (offline + AR) |
| **Fieldwire** | **Campo** (2D) | **No** `[V]` | No | **Sí, pública** (tasks, de pago) `[V]` | **Alto** (offline completo) |
| **Dalux Field** | **Campo + coord.** | Sí, **2.1** + BCF Live `[V]` | Compatible vía Solibri `[V]` | Sí, documentada (gated) `[V]` | **Alto** (BIM móvil + offline) |
| **BulldozAIR** | **Campo** (2D/GIS) | **No** `[I]` | No | No pública (solo Enterprise) `[V/I]` | **Alto** (offline) |

### 2.4 Cobertura de capacidades y fases

`●` cubre · `◐` parcial · `○` no/marginal. Fases: **D** = diseño (coordinación, revisión, clash, BCF) · **C** = construcción (obra/tablet, snagging, avance).

| Herramienta | Visor | CDE | Incidencias | D | C |
|---|---|---|---|---|---|
| Catenda Hub | ● | ● | ● | ● | ◐ |
| Trimble Connect | ● | ● | ● | ● | ● |
| Autodesk ACC | ● | ● | ● | ● | ● |
| usBIM (ACCA) | ● | ● | ● | ● | ◐ |
| Dalux | ● | ● | ● | ● | ● |
| Oracle Aconex | ● | ● | ● | ● | ● |
| Asite | ● | ● | ◐ | ● | ◐ |
| Newforma Konekt | ● | ● | ● | ● | ◐ |
| Thinkproject | ● | ● | ● | ● | ● |
| Bentley ProjectWise | ● | ● | ◐ | ● | ◐ |
| That Open Engine | ◐ (se construye) | ○ | ○ | ◐ | ◐ |
| Speckle | ● | ◐ | ◐ | ● | ◐ |
| Solibri | ● | ○ | ● (BCF) | ● | ○ |
| BIMcollab | ● (Zoom) | ◐ (Twin) | ● | ● | ○ |
| Revizto | ● | ◐ | ● | ● | ● |
| Procore | ● | ● | ● | ◐ | ● |
| PlanRadar | ● | ◐ | ● | ◐ | ● |
| Fieldwire | ● (2D + 3D) | ◐ | ● (sin BCF) | ○ | ● |
| BulldozAIR | ○ | ◐ | ● | ○ | ● |

---

## 3. Fichas breves por herramienta

### CDE / plataformas

**Catenda Hub** (ex Bimsync · Catenda, Noruega). CDE openBIM "API-first": visor 2D/3D IFC, fuerte alineación buildingSMART (IFC+BCF). Expone toda la plataforma como APIs abiertas (Catenda Boost) con **BCF-API estándar 2.1** y portal de desarrolladores público. *Límite:* menor peso enterprise que ACC/Aconex y menos potencia de campo que Dalux. *Precio:* colaboradores ilimitados; tarifa **bajo consulta** (2026-06-24). **La más abierta del grupo.** `[V]`

**Trimble Connect** (Trimble). CDE multiformato con visor 3D embebible y ecosistema Tekla. Actúa como **servidor BCF (2.1 y 3.0)**, Core/Workflow APIs REST y Workspace API (JS) para el visor. *Precio (2026-06-24):* Personal **gratis** (1 proyecto, 5 miembros, 10 GB); **Pro 12,41 $/u/mes**, **Innovate 29,08 $/u/mes** (oficial, may-2025). *Límite:* mejor en coordinación que en flujo documental 19650 formal. `[V]`

**Autodesk Construction Cloud** (ACC / Docs / ex-BIM 360). CDE líder de mercado. APIs potentes vía **Autodesk Platform Services (APS)**: Data Management, Model Derivative (visualiza IFC/RVT/NWD), AEC Data Model (GraphQL). Genera issues BCF import/export, pero **no es servidor BCF nativo**. *Límite clave:* apertura condicionada al **lock-in .rvt**. *Precio orientativo (revendedor, a confirmar en web oficial):* Docs ~500 $/año, BIM Collaborate Pro ~1.284 $/u/año. `[V]` (cifras de tercero)

**usBIM** (ACCA, Italia). **Primer CDE IFC certificado por buildingSMART**. Visor IFC web gratis (10 GB), federación IFC/BCF/COBie, versionado, auditoría; integra por plugins y API/SDK. *Límite:* endpoints de la API menos documentados públicamente; ecosistema muy ACCA. *Precio:* capa visor/colaboración **gratuita** con cuenta; módulos **bajo consulta**. `[V]`

**Dalux** (Dinamarca). CDE (Box) con el **visor IFC más rápido del sector** y la mejor usabilidad de campo (Field, mobile-first). Áreas Shared/Published y naming forzable (19650). API pública en SwaggerHub (GET/POST/PATCH) pero **requiere licencia de empresa y key generada por el CSM**, sin soporte de uso. *Precio:* **bajo consulta**; existe BIM Viewer gratuito. `[V]`

**Oracle Aconex** (Oracle). CDE enterprise de referencia en gran proyecto/infraestructura, neutral, muy fuerte en trazabilidad documental. APIs REST (OAuth); el Cloud Adapter usa **BCF-API v3.0**; visor Model Explore federado con IFC. *Límite:* pesado, orientado a grandes cuentas, coste enterprise. *Precio:* **bajo consulta**. `[V]`

**Asite** (Adoddle/ABOS, UK). CDE enterprise con **Kitemark BSI ISO 19650** y numeración de revisiones 19650/BS 1192. Visor cBIM web federado; **Open Data API REST/SOAP**. *Límite:* orientación enterprise; servidor BCF nativo no confirmado en fuente primaria. *Precio:* **bajo consulta**. `[V]` (API/19650) `[I]` (BCF)

**Newforma Konekt** (Newforma). CDE "open" que trabaja **IFC y BCF de forma nativa** sin software extra; visor 2D/3D, flujo de incidencias BCF nativo e interoperable. *Límite:* la existencia de API REST pública documentada no se confirma en fuente primaria (su fuerte es el workflow BCF, no necesariamente headless). *Precio:* **bajo consulta**. `[V]` (BCF/19650/visor) `[I]` (API)

**Thinkproject** (Alemania). Suite enterprise con CDE Enterprise/Infrastructure, visor 3D BIM y comunicación por **BCF**; **VDC API (OAuth2)** documentada; apps iOS/Android offline. *Límite:* plataforma pesada, foco gran cliente. *Precio:* **personalizado/bajo consulta**. `[V]`

**Bentley ProjectWise** (Bentley). DMS/CDE de referencia en infraestructura, "powered by iTwin". Revisión 3D vía iTwin Design Review, export IFC desde iModel, **iTwin Platform API pública**. *Límite crítico:* **ProjectWise 365 no produce ni ingiere BCF de forma nativa** (solo comparte el fichero); el flujo nativo es iModel, no openBIM puro → fricción para un copiloto BCF. *Precio:* **bajo consulta**. `[V]`

### Visores

**That Open Engine / web-ifc** (That Open Company, ex IFC.js). Motor open source para **leer y escribir IFC en JS a velocidad nativa** (C++→WASM); base de un ecosistema modular (web-ifc, components sobre Three.js, fragments). API clara `IfcAPI()→OpenModel()→consultar geometría/propiedades`; **`IfcImporter` corre en frontend y backend (node)** → una IA carga IFC y lee/escribe sin GUI. *Licencia:* **MPL-2.0** (verificado en LICENSE.md; **no MIT** como suele repetirse) — copyleft débil por fichero, permite embeber en producto propietario pero obliga a liberar las modificaciones de los ficheros cubiertos. *Precio:* gratis. *Límite:* no es app de usuario final; hay que construir la aplicación. `[V]`

**Speckle** (Speckle Systems). Plataforma de datos cloud open source para AEC: conectores con apps de autoría, base de datos versionada de objetos, **visor web 3D embebible** y API. SDK potente (**specklepy** Python, **Speckle.Sdk** .NET, JS, GraphQL); importador IFC vía IfcOpenShell; **self-host 100% gratis**. *Licencia:* **Apache-2.0**. *Precio cloud:* free tier; se cobra por *Editors*, *Viewers* gratis (cifras concretas de planes no verificadas). *Límite:* capa de datos más que comprobación/clash; BCF no es su eje. `[V]`

**Solibri** (Office/Anywhere · Nemetschek). Estándar de **QA/QC y clash** sobre IFC. Office de pago; **Anywhere (visor gratuito) es legacy**, retirada anunciada Q4 2026. **BCF import+export** y BCF Live Connector; **REST API desde v9.10.3** (local, requiere licencia Office/Site). *Precio (oficial, 2026-06-24):* Starter 99 €, Essential 1.428 €, Advanced 2.109 €, Premium 2.772 €/año. *Límite:* cerrado, escritorio; API no hace CRUD remoto de issues. `[V]`

**BIMcollab Zoom** (KUBUS). Visor IFC de escritorio con clash y gestión de incidencias **BCF** integrada con la nube BIMcollab. Versión Viewer gratuita; lo potente (clash por reglas, Smart Issues) es de pago. **BCF vía Connection API (BCF-API buildingSMART, REST)**. *Precio:* freemium (cifras exactas no verificadas). *Límite:* cerrado; automatiza issues, no el modelo. `[V]`

**Revizto** (Suiza). Plataforma de coordinación e **issue tracking** multiplataforma (web+escritorio+móvil) sobre IFC/RVT/point clouds. Issues ligados a posición 3D, multidispositivo, AR. **Import BCF**; export nativo a BCF estándar reportado como limitado. API REST **propietaria**. *Precio:* suscripción, no público. *Límite:* propietario; fricción BCF con otras plataformas. `[V/I]`

**BIMvision** (Datacomp). **Visor IFC freeware** (gratis comercial), primer visor con arquitectura de **plugins**. Núcleo gratis; clashes/IDS/BCF/exports por plugins de pago. IFC 2x3 y 4.0; **plugin BCF v2.1**. *Límite:* cerrado, Windows, SDK de plugins (no librería embebible/headless). `[V]`

**usBIM.viewer+** (ACCA). **Visor + editor IFC gratuito** (web+escritorio) con cuenta usBIM (10 GB); edita el IFC y reexporta. Hasta IFC4X1/4X2. *Límite:* ligado al cloud ACCA, cerrado, sin SDK público. BCF citado en fuentes terciarias, no confirmado en primaria. `[V/I]`

**Open IFC Viewer** (ACCA, gratuito). Visor IFC gratuito de escritorio (Windows/Microsoft Store), ligero. *Límite:* visor puro, cerrado, sin API (no confundir con usBIM.viewer+). `[V]`

**Autodesk APS Viewer** (ex Forge). **Viewer SDK web embebible**; renderiza muchos formatos. *Límite:* requiere traducir el modelo a **formato propietario SVF** (Model Derivative, coste por tokens; IFC = "Complex job"). *Precio:* comercial / Flex tokens (cifras no verificadas). `[V]`

### Gestores de incidencias

**BIMcollab** (Nexus/Cloud/Zoom · KUBUS). Ecosistema OpenBIM para coordinación e issues sobre IFC+BCF. **Única con BCF-API REST conforme buildingSMART (Connection API, OAuth2), incluida en todos los planes** + plug-ins gratuitos para CAD. *Precio (2026-06-24):* Basic 12,50 €, Advanced 18,75 €, Enterprise 25 €/u/mes (anual). *Límite:* oficina, no obra; móvil sin offline real. **La más agente-friendly en coordinación.** `[V]`

**Revizto** (issue tracking). Issue Tracker tipo Jira sobre visor 2D/3D federado + clash; cruza con fuerza **diseño y campo** (apps Site/V5 con AR y offline). API REST pública documentada (issue ops, clash, logs) pero **propietaria** (BCF solo por fichero). *Precio:* solo cotización. *Límite:* no es CDE documental 19650; dialecto propio, no BCF-API. `[V]`

**Solibri** (model-checking). Referencia en **QA reglado sobre IFC** (clash, IDS, QTO). BCF sólido (.bcfzip + BCF Live Connector a cualquier servidor BCF-API). *Límite:* escritorio, sin app de campo; su REST API es **local** y no expone CRUD remoto de incidencias → **productor** de issues, no gestor automatizable por API. `[V]`

**Procore** (PM/campo). Plataforma SaaS de gestión de construcción: documental, RFIs, observations, punch list, Coordination Issues con visor 3D. **API REST pública muy amplia (OAuth2)** + fuerte campo con offline. BCF solo **2.1 por fichero** (sin BCF-API). *Precio:* anual por ACV, **no público**. *Límite:* implantación larga; coordinación openBIM limitada. `[V]`

**PlanRadar** (Austria). SaaS de gestión de incidencias/defectos y trabajo de campo con apps nativas y **offline real**. Visor BIM/IFC propio (2x3/4/**4.3**, federado, AR) con tickets sobre la geometría + **API REST pública** (Pro/Enterprise) con webhooks. Export BCF por fichero (versión s/e). *Precio:* ~35/119/179 $/u/mes indicativo (BIM y API en Pro/Enterprise). *Límite:* no es coordinador de clashes ni CDE normativo. `[V/I]`

**Fieldwire** (by Hilti). App de obra **centrada en planos 2D/PDF**: tareas, punch, inspecciones; offline completo + **API REST pública** (tasks CRUD, webhooks) + visor BIM 3D (IFC ≤4.3) en planes Business+. **No soporta BCF** (verificado por ausencia). *Precio (2026-06-24):* Basic 0 $, Pro 39 $, Business 64 $, Business Plus 89 $/u/mes. *Límite:* 3D solo consulta; sin coordinación openBIM. `[V]`

**Dalux Field** (+Box/BIM Viewer). Plataforma de ciclo completo: Box (CDE 19650), BIM Viewer (IFC móvil rápido, gratis), Field (snagging/QA). **De las que mejor cruzan diseño y obra**: visor IFC federado en tablet con offline + **BCF 2.1** (+ BCF Live vía Solibri) + API REST documentada (SwaggerHub) + **tier gratuito** (≤3 proyectos). *Límite:* API requiere licencia empresa y key por CSM; precios comerciales no públicos. `[V]`

**BulldozAIR** (Mezzoteam, Francia). App de obra y colaboración de campo: punch/reservas (OPR), partes, actas, formularios, sobre planos 2D/DWG, GIS y vista 3D; offline + sync e informes automáticos. *Límite crítico:* **no es openBIM** — sin BCF, sin visor IFC real, **sin API pública documentada** (API solo Enterprise, bajo contrato). *Precio:* % del presupuesto/facturación, sin tarifa por usuario pública. `[V/I]`

---

## 4. Síntesis

### 4.1 Qué cubre bien el mercado

El mercado de **CDE comerciales está maduro y saturado**: ACC, Aconex, ProjectWise, Asite, Thinkproject, Trimble Connect, Dalux y usBIM cubren las tres capacidades (visor + CDE + incidencias) y las dos fases con solvencia. La **gestión de incidencias de campo** (PlanRadar, Fieldwire, Dalux Field, Procore, Revizto) está muy resuelta en lo que importa al encargado: app móvil nativa, **offline real**, snagging sobre plano/modelo y AR. Y existe una **base openBIM real y verificable**: el estándar **BCF** está implementado de forma seria por varias plataformas, y dos motores open source —**That Open Engine** (MPL-2.0) y **Speckle** (Apache-2.0)— permiten leer/escribir IFC y embeber visor sin lock-in.

### 4.2 Dónde están los huecos (lo que nos interesa)

El hueco no está en "visor" ni en "CDE" como funciones — están commoditizadas. Está en la **intersección que define nuestra tesis**:

1. **Apertura real + automatización por agentes a la vez es rara.** De ~10 CDE, solo **Catenda Hub** y **Trimble Connect** combinan, sin gatekeeping, los tres requisitos: API REST pública + **servidor BCF-API** + visor IFC embebible. El resto o no tiene BCF nativo (ProjectWise), o tiene la API **gated** por licencia/partner (Dalux, en parte ACC con su lock-in .rvt), o su apertura no se confirma en fuente (Newforma, Asite).

2. **BCF-API REST conforme buildingSMART casi no existe como producto.** En incidencias, **solo BIMcollab** ofrece un BCF-API estándar público. Todas las demás con API pública (Procore, PlanRadar, Fieldwire, Revizto, Dalux) hablan **dialecto propietario**: un copiloto tendría que aprender N APIs distintas en vez de un estándar. Nadie ofrece "BCF estándar **y** API abierta **y** uso de campo de primera" en un solo producto.

3. **Ningún producto está diseñado para que una IA sea el operador principal.** Las APIs existen para integrar dashboards o sincronizar datos, no para que un agente genere el modelo, lo audite y mueva incidencias de forma nativa. **Ese es exactamente el espacio del foso.**

4. **La capa headless/embebible solo la dan los open source.** Si queremos que el visor y el modelo vivan *dentro* de nuestro entorno y que la IA opere sin GUI, los únicos caminos sin lock-in son **web-ifc** (control fino del IFC en navegador y node, JS/C++) y **Speckle** (capa de datos versionada + SDK Python/.NET). Son **complementarios**, no excluyentes.

### 4.3 Primera lectura: adoptar / integrar / construir

*Posición de la IA como insumo; la decisión es de JM.*

**CONSTRUIR (núcleo del entorno propio, donde está el foso):**
- **Visor + acceso al modelo** sobre **That Open Engine / web-ifc** (MPL-2.0). Es lo que nos permite que la IA lea/escriba IFC sin GUI y que el visor sea *nuestro*. Aquí no hay producto que comprar que no implique lock-in.
- **La capa de orquestación IA** (generar IFC desde lenguaje natural, auditar, acuñar incidencias) — es justamente lo que el mercado no ofrece.

**INTEGRAR (no reinventar; conectar por estándar):**
- **Speckle** (Apache-2.0, self-host gratis) como **capa de datos versionada / CDE ligero** y como visor web compartible alternativo. Reduce muchísimo el trabajo de la parte "data layer" y se autohospeda.
- **BCF como protocolo de incidencias** y, si se quiere un gestor BCF de coordinación llave en mano, **BIMcollab** por ser el único con BCF-API estándar — encaja con una IA que habla BCF nativo.
- Para **obra/campo**, integrar vía API con **Dalux Field** o **PlanRadar** (los mejores en tablet+offline) en lugar de construir una app de campo desde cero.

**ADOPTAR (usar tal cual cuando un piloto lo exija, sin construir):**
- **Solibri / BIMcollab Zoom** como **acuñadores de incidencias por reglas/IDS** en diseño (productores de BCF que luego nuestra capa IA gestiona).
- **Trimble Connect** (free tier) o **usBIM** (visor IFC gratis, certificado bSI) como CDE/visor de referencia para **comparar paridad** y para pilotos donde el cliente ya los use.

**Cadena de referencia openBIM que sugiere el conjunto:** *Solibri/Zoom acuña issues por reglas → BCF estándar → nuestra capa IA (web-ifc + Speckle) gestiona el modelo y las incidencias → Dalux/PlanRadar las baja a obra en tablet.* Nuestro diferencial no es ninguna de esas piezas: es **ser el operador IA nativo que las une por formato abierto**.

### 4.4 Una bandera para JM

El mercado valida la tesis por **ausencia**: hay visores, hay CDE, hay BCF, hay open source — pero **nadie ha puesto a la IA como operador nativo sobre formato abierto**. El riesgo no es técnico (las piezas existen y son libres), es de **enfoque**: si construimos de más (otro CDE, otro visor de campo) competimos en un mercado saturado; si construimos solo el **operador IA + el corpus golden verificado**, atacamos el hueco real. Esta lectura **apunta**, no cierra: la decisión adoptar/integrar/construir pieza a pieza es de JM.

---

## 5. Avisos de rigor (verificado vs. inferido)

- **Precios.** Cifras fiables de lista oficial: **Trimble Connect** (may-2025), **Solibri** (2026-06-24), **BIMcollab** (2026-06-24), **Fieldwire** (2026-06-24). Cifras de **revendedor/tercero** (orientativas, a confirmar en web oficial): **ACC**, **Solibri** (fuente alternativa coincidente), **PlanRadar**, **Revizto**, **BulldozAIR**. **Bajo consulta** (sin lista pública): Catenda, usBIM (módulos), Dalux, Aconex, Asite, Newforma, Thinkproject, Bentley, Procore.
- **Inferencias `[I]` a cerrar antes de cualquier compra:** BCF 3.0 en Revizto/Procore/Dalux (asumir 2.1); versión de BCF y existencia de BCF-API en PlanRadar; BCF nativo en Asite; API REST pública en Newforma; BCF en usBIM.viewer+; estados S0–S7 explícitos por plataforma; licencia **paquete a paquete** del ecosistema That Open (conviven MPL-2.0 y posibles MIT — verificar antes de cerrar arquitectura).
- **Aqyra:** retirada del benchmark por indicación de JM y por no ser verificable en fuente pública a 2026-06-24.

---

## 6. Fuentes (consulta 2026-06-24)

**CDE / plataformas**
- Autodesk APS — ACC APIs `https://aps.autodesk.com/apis-and-services/autodesk-construction-cloud-acc-apis` · IFC `https://aps.autodesk.com/topics/ifc` · AEC Data Model `https://aps.autodesk.com/en/docs/aecdatamodel/v1/developers_guide/overview/` · precios G2 `https://www.g2.com/products/autodesk-construction-cloud/pricing`
- Trimble Connect — Developer portal `https://developer.trimble.com/docs/connect/` · BCF Topics API `https://developer.trimble.com/docs/connect/tools/api/topics/` · planes Pro/Innovate (may-2025) `https://community.trimble.com/blogs/lindsay-renkel/2025/05/05/trimble-connect-new-pro-and-innovate-plans-faq`
- Bentley — iTwin Platform APIs `https://developer.bentley.com/apis/` · IFC export `https://developer.bentley.com/apis/synchronization/supported-formats/` · PW365 BCF (Architosh) `https://architosh.com/2020/06/bentleys-projectwise-365-has-gone-saas-brings-broad-market-and-platform-appeal-to-aeco-industry/2/`
- Oracle Aconex — APIs `https://help.aconex.com/aconex/aconex-apis/` · Model Collaboration (BCF/Model Explore) `https://www.oracle.com/a/ocom/docs/aconex-model-collaboration-cloud-service-ds.pdf` · Cloud Adapter BCF-API v3.0 `https://docs.oracle.com/en/industries/construction-engineering/smart-construction-platform/aconex-adapter/use-cases.html`
- Asite — Open Data API `https://help.asite.com/en/articles/5700569-open-data-api` · Kitemark/19650 `https://www.asite.com/blogs/7-enterprise-cde-criteria-for-bim-and-iso-19650`
- Thinkproject — CDE Enterprise `https://www.thinkproject.com/products/cde-enterprise/` · VDC API `https://bimdocs.thinkproject.com/vdcAPI/4.0/class_web_forms_a_p_i.html`
- Catenda — Catenda Boost `https://catenda.com/bim-solutions-open-standards/catenda-boost-bim-api/` · BCF v2.1 `https://bimsync.com/developers/reference/bcf/v2_1` · pricing `https://catenda.com/offers/`
- Dalux — API (SwaggerHub, licencia+key CSM) `https://support.dalux.com/hc/en-us/articles/9544314902556-Dalux-API` · Box (19650) `https://www.dalux.com/products/dalux-box/`
- usBIM (ACCA) — IFC Viewer `https://www.accasoftware.com/en/ifc-viewer` · CDE manual (certif. bSI) `https://cdn-resources.accasoftware.com/accasoftware/pdf/usBIM.platform_CDE_manual_Ed2_EN.pdf`
- Newforma Konekt — Konekt `https://www.newforma.com/newforma-konekt/` · ISO 19650 `https://www.newforma.com/iso-19650-what-newforma-brings-to-you/`

**Visores**
- That Open — LICENSE.md MPL-2.0 `https://github.com/ThatOpen/engine_web-ifc/blob/main/LICENSE.md` · repo `https://github.com/ThatOpen/engine_web-ifc` · docs IfcImporter `https://docs.thatopen.com/Tutorials/Fragments/Fragments/IfcImporter/`
- Speckle — pricing/Viewers free `https://speckle.systems/blog/projects-get-a-new-home-and-pricing-plans/` · Cloud vs Self-Hosting (Apache-2.0) `https://speckle.systems/blog/speckle-cloud-vs-self-hosting/` · IFC (IfcOpenShell) `https://speckle.systems/integrations/ifc/` · specklepy `https://pypi.org/project/specklepy/`
- Solibri — IFC soportado `https://help.solibri.com/hc/en-us/articles/23779405208855-IFC-Standards-Supported-by-Solibri` · REST API `https://solibri.github.io/Developer-Platform/9.12.9/RestApiUsage.html` · Anywhere legacy `https://www.solibri.com/products/solibri-anywhere`
- BIMcollab — Free IFC Viewer `https://www.bimcollab.com/en/go/free-ifc-viewer/` · Developer SDK/Connection API `https://helpcenter.bimcollab.com/en/articles/327345-bimcollab-developer-sdk`
- BIMvision — freeware `https://bimvision.eu/` · plugin BCF 2.1 `https://store.bimvision.eu/plugin/ifc__comments__slashh__bcf-25`
- Open IFC Viewer `https://openifcviewer.com/` · Autodesk APS Viewer `https://aps.autodesk.com/apis-and-services/viewer` · pricing/Flex tokens `https://aps.autodesk.com/topics/pricing`

**Gestores de incidencias**
- BIMcollab pricing `https://www.bimcollab.com/en/pricing/` · Connection API (BCF-API) `https://helpcenter.bimcollab.com/en/articles/327345-bimcollab-developer-sdk`
- Revizto — developer `https://developer.revizto.com/` · viewers/BCF `https://revizto.com/resources/blog/top-10-bim-viewers`
- Solibri pricing `https://www.solibri.com/pricing` · BCF Live Connector `https://help.solibri.com/`
- Procore — developers `https://developers.procore.com/` · Coordination Issues/BCF `https://support.procore.com/`
- PlanRadar — API `https://www.planradar.com/api/` · BIM/IFC `https://www.planradar.com/bim-construction-software/`
- Fieldwire — pricing `https://www.fieldwire.com/pricing/` · developers `https://developers.fieldwire.com/`
- Dalux — API `https://support.dalux.com/hc/en-us/articles/9544314902556-Dalux-API` · Field `https://www.dalux.com/products/dalux-field/`
- BulldozAIR `https://www.bulldozair.com/` · buildingSMART BCF-API `https://github.com/buildingSMART/BCF-API`

---

*Procedencia: entregable del Hilo 1 preparado por la IA (Ing. BIM-IFC / PM) de Estructurando 2.0 · 2026-06-24 · evidencia para decisión y firma de JM.*


