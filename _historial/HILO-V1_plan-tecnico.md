# Plan técnico — V1 · Visor OpenBIM industrializado (Aqyra)

> **Qué es:** plan de implementación de **V1** (convertir `visor-ifc` N0 artesanal en visor de producto N3: robusto, embebible, web sin instalación, tablet). Markdown en el repo; la IA propone, **JM firma**. Corresponde a **H1 / V1** de `HOJA_DE_RUTA.md`.
> **Decisiones ancladas que lo gobiernan:** D-001 (BCF completo + IDS validación-lectura; autoría IDS → V2), D-002 (web-ifc + Fragments puro, sin servidor), D-003 (cebo bajo Apache-2.0), D-004 (marca Aqyra), D-005 (frontera + `versions.lock`). Ver `DECISIONES.md`.
> **Estado:** PROPUESTA · 2026-06-24 · pendiente de ajuste y firma de JM.

---

## 1. Encuadre y Definición de Hecho (del brief §5)

V1 termina cuando, **todo dentro de `publico/`** (cebo) y sin tocar el moat:

1. Abre **cualquier IFC (4 / 4.3)** en **navegador y tablet**, sin instalación.
2. Navega el modelo e inspecciona **Psets**; **federa ≥2 modelos**.
3. **Ve y añade incidencias BCF**; **valida un requisito con IDS**.
4. Es **embebible** en nuestro entorno.
5. Repo **industrializado**: contrato declarado, tests en verde, paquete **SemVer** publicado.

**Principio rector (del brief §2.3):** *la curva de entrada es el enemigo, no la falta de features.* Todo lo que sigue se subordina a "abre y se usa, en obra, desde un navegador".

---

## 2. Stack técnico (consecuencia de D-002 y D-003)

| Capa | Pieza | Licencia | Por qué |
|---|---|---|---|
| Lectura IFC | **web-ifc** (That Open, WASM) | MPL-2.0 | IFC nativo en navegador, sin servidor |
| Teselado/rendimiento | **@thatopen/fragments** | MIT | formato Fragments para modelos grandes |
| Componentes BIM | **@thatopen/components** | MIT | `BCFTopics`, `IDSSpecifications`, selección, Psets, árbol |
| UI | **@thatopen/ui** | MIT | paneles/toolbars web-components, framework-agnóstico |
| Render 3D | **three.js** | MIT | motor de escena (dependencia de los anteriores) |

Todo **cliente puro**: el visor es una SPA/web-component que corre en el navegador; **cero backend** en V1 (coherente con "web sin instalación + tablet" y con el cebo OSS). El WASM de web-ifc se sirve como activo estático. *Riesgo IFC4.3: ver §7.*

---

## 3. Industrialización: monorepo, contrato, tests, SemVer

### 3.1 Estructura de paquetes (todo en `publico/`)

```
publico/
├── visor/            · paquete @aqyra/visor — núcleo del visor (carga, escena, selección, Psets, árbol)
├── openbim/          · paquete @aqyra/openbim — adaptadores BCF / IDS / bsDD (sobre @thatopen/components)
├── ui-nl/            · cáscara NL (placeholder; se enciende en V4 — solo andamiaje en V1)
├── embed/            · paquete @aqyra/embed — web-component <aqyra-viewer> que empaqueta visor+openbim
└── demo/             · app de demostración del DoD (no publicable como paquete)
```

Monorepo con **workspaces** (npm o pnpm — §8). Cada paquete con su `package.json`, su `CHANGELOG.md` (*Keep a Changelog*) y su versión **SemVer** independiente (gestión con *changesets*).

### 3.2 Contrato declarado (la API pública = el "contrato C-visor")

El equivalente en V1 a los contratos del núcleo es la **API pública del web-component embebible**, versionada SemVer (MAJOR = rotura de esta API). Esbozo:

```ts
// @aqyra/embed — contrato público v0
interface AqyraViewer {
  load(models: IFCSource | IFCSource[]): Promise<ModelHandle[]>;   // federación = array
  select(globalId: string): void;
  getProperties(globalId: string): PsetData;                       // Psets
  setVisibilityByClass(ifcClass: string, visible: boolean): void;
  setColorByClass(ifcClass: string, color: RGBA): void;
  bcf: { list(): Topic[]; create(t: NewTopic): Topic; exportZip(): Blob; importZip(b: Blob): void };
  ids: { loadSpec(xml: string): IdsSpec; validate(): IdsReport };   // validación-lectura (D-001)
  on(event: ViewerEvent, cb: Handler): Unsubscribe;
}
```

Este contrato se **declara, se testea y se congela por SemVer**. Es lo que "industrializa" el visor y lo hace embebible de forma estable.

### 3.3 Toolchain de calidad

- **TypeScript** estricto; **Vite** para build/dev (bundler a confirmar, §8).
- **Tests:** unit/componentes con **Vitest**; e2e en navegador y **tablet (viewport touch)** con **Playwright** (incluye prueba de carga de IFC4.3 y federación).
- **CI:** lint + typecheck + tests + build en cada PR; **gate verde** obligatorio (alinea con la disciplina golden del gobierno).
- **Licencias:** `license-checker` en CI vuelca a `publico/THIRD-PARTY-NOTICES` y **bloquea** si aparece GPL/AGPL (cierra el residual de D-003).
- **Publicación:** paquetes SemVer (registro npm público o privado, §8); el tag de release es la evidencia para JM.

---

## 4. Fases de implementación (incrementales, cada una con su DoD)

| Fase | Entrega | DoD de la fase | Cubre del DoD-V1 |
|---|---|---|---|
| **F0 · Andamiaje** | Monorepo + CI + contrato `@aqyra/embed` vacío + `<aqyra-viewer>` que monta escena vacía y se **embebe** en `demo/` | CI verde; web-component se inserta en una página host | §5.4, §5.5 (base) |
| **F1 · Carga IFC sólida** | Carga IFC4 e **IFC4.3** vía web-ifc → **Fragments**; **federación ≥2 modelos**; rendimiento en modelo grande | Abre un IFC4.3 y dos modelos federados; FPS aceptable en modelo de referencia | §5.1, §5.2 (federación) |
| **F2 · Navegación e inspección** | Industrializar `visor-ifc` N0: órbita/zoom/encuadre, selección, **panel de Psets**, **árbol espacial**, color/visibilidad por clase | Selecciona elemento y ve sus Psets; filtra por clase IFC | §5.2 (Psets) |
| **F3 · BCF** | `@aqyra/openbim` BCF sobre `BCFTopics`: **ver y crear** incidencias, import/export `.bcfzip` | Crea una incidencia con viewpoint y la exporta/reimporta | §5.3 (BCF) |
| **F4 · IDS + bsDD** | **Cargar un IDS** y **validar** sobre el modelo (`IDSSpecifications`); **lectura** de clasificación/propiedades bsDD | Valida un requisito (p. ej. `IfcDoor`→`FireRating`) y muestra el informe | §5.3 (IDS) |
| **F5 · Tablet + embebido + hardening** | Responsive/touch, gestos, rendimiento en tablet; pulido del contrato embebible; estados de carga/errores | Usable en tablet real desde navegador; sin instalación | §5.1, §5.4 |
| **F6 · Cierre de producto** | Cobertura de tests del contrato, `THIRD-PARTY-NOTICES` real, **release SemVer**, **demo del DoD** | Paquete publicado; demo Decopak HQ-ish reproducible | §5.5 + demo |

El orden prioriza el camino crítico del DoD: **abrir/federar (F1)** y **embeber (F0/F5)** antes que BCF/IDS, porque son lo que materializa "web sin instalación + tablet".

> **Estado de ejecución (2026-06-24):** **F0 ✅**, **F1 ✅** (carga IFC4/4.3, federación, Psets, render three.js, cámara) y **F2 ✅** (selección, Psets, color/visibilidad por clase, árbol espacial). Verificado en **navegador real con Decopak HQ** y **12 tests headless verdes**. Prototipo de la dirección de producto (lienzo limpio + NL contextual) en `publico/demo/calculista.html` (D-007). **Siguiente:** F3 (BCF). Snapshot completo y backlog F3–F6 en **`ESTADO_V1.md`**; detalle técnico en `publico/DEV.md`.

---

## 5. Gobierno aplicado en V1 (aunque V1 no muestre cálculo)

- **Frontera cebo/anzuelo:** todo el código de V1 vive en `publico/`. `ui-nl/` solo recibe andamiaje (la superficie); su **criterio** es de V4 y vive en `privado/`. Nada del moat entra.
- **Dos llaves:** V1 no pinta resultados de cálculo, pero el contrato del visor **reserva el estado de los datos** (`propuesta` / `verificado-firmado`) para que en V3 el post-proceso nunca pinte como válido lo no firmado. Se diseña el hueco ahora.
- **Consumo anclado:** `visor-ifc 0.1.0` e `iso19650-openbim 0.8.2` se consumen desde `integracion/versions.lock`; subir versión = bump deliberado + suite en verde.
- **Formato abierto:** IFC/BCF/IDS entran y salen como texto; cero binario propietario.

---

## 6. Mapa a hitos y a la hoja de ruta

- **H0** (extraer repo + proyecto Cowork) — precondición; en curso (ver README, residuales en `DECISIONES.md`).
- **H1 = fin de V1** — este plan. Prueba: *abre IFC en tablet; BCF básico* (`HOJA_DE_RUTA.md` §5).
- **Prepara el terreno sin invadir V2/V3:** F1 deja el pipeline `IFC→Fragments+props` listo para que V2 (pre-proceso, write-back) y V3 (post-proceso, contrato C5) se enganchen. La **decisión abierta de dónde regenera el spec** (Capa 2·C) **NO se resuelve aquí** — es de V2 (`estado-inicial_narracion-IFC.md`).

---

## 7. Riesgos técnicos

1. **Cobertura IFC4.3 de web-ifc parcial/en evolución** [del benchmark, §168]. *Mitigación:* prueba de aceptación con un set de IFC4.3 reales en F1; si hay pérdida, **fallback de parsing con IfcOpenShell server-side** — pero eso introduce backend y LGPL, así que se mantiene **opt-in y en `privado/`** para no romper "sin servidor" ni la frontera de licencias. Decisión sólo si F1 lo exige.
2. **Rendimiento en modelos grandes / tablet.** *Mitigación:* Fragments + carga progresiva; presupuesto de FPS y memoria medido en F1/F5 sobre un modelo de referencia y una tablet real.
3. **Federación de modelos** (coordenadas, georreferencia, ids colisionando). *Mitigación:* prueba con ≥2 modelos desalineados en F1; normalizar a un origen común.
4. **Touch/gestos en tablet** (órbita vs scroll, selección con dedo). *Mitigación:* F5 dedicada; e2e Playwright con viewport touch.
5. **Madurez de `IDSSpecifications`/`BCFTopics`** (API en evolución de That Open). *Mitigación:* anclar versión exacta de `@thatopen/components`; envolver tras `@aqyra/openbim` para aislar cambios upstream.
6. **Deriva del contrato embebible.** *Mitigación:* el contrato §3.2 se testea como API pública; romperlo = MAJOR.

---

## 8. Decisiones técnicas menores — CERRADAS por JM (2026-06-24)

1. **Gestor de paquetes/monorepo:** **pnpm workspaces.**
2. **Bundler:** **Vite.**
3. **Registro de publicación SemVer:** **registro privado hasta V5** (SemVer y tags ya; no se publica abierto hasta cerrar el gate legal D-003 y la marca D-004).
4. **Envoltorio embebible:** **Web Component estándar** (`<aqyra-viewer>`, framework-agnóstico).
5. **Scope npm:** **`@aqyra/*`** (sujeto a confirmar scope libre al verificar marca/dominio — residual D-004).
6. **Modelo de referencia de rendimiento:** **Decopak HQ** (caso de uso guía), en navegador y tablet.

> Registradas como **D-006** en `DECISIONES.md`.

---

## 9. Fuera de alcance de V1 (no dispersar)

Pre-proceso (V2), post-proceso (V3), copiloto NL (V4), SaaS/cebo desplegable (V5), editor paramétrico / round-trip del spec (se prepara el terreno, se decide en V2). El NL en V1 **no es el foco**: `publico/ui-nl/` solo recibe andamiaje.

---

*Procedencia: plan técnico de V1 · proyecto Aqyra · IA (PM / Ing. BIM-IFC) · 2026-06-24 · para ajuste y firma de JM. La IA propone; JM firma.*
