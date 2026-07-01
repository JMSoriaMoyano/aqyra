# Mapa del ecosistema Aqyra

> **Qué es este documento:** la fuente única de verdad del ecosistema AEC que se desarrolla bajo `Documents\Claude\Projects`. Da perspectiva de conjunto: qué hay, qué rol juega cada pieza, en qué versión está y cómo dependen unas de otras. Es un documento vivo: se actualiza cuando cambia el disco.
>
> **Proyecto raíz:** `Aqyra-Raiz` (esta carpeta; renombrada desde `Aquira Alfa`, ver `MARCA_Y_NOMENCLATURA.md`). No contiene copias de los proyectos; es el **panel de mando** que los observa.
>
> **Fecha de la foto:** 2026-06-26 · **Modo:** solo lectura (no se ha movido, borrado ni renombrado nada).

---

## 1. La idea en una frase

Un **ecosistema de ingeniería AEC sobre estándares OpenBIM** con dos mitades que se sostienen:

- **El foso (anzuelo):** un motor de cálculo `IFC → FEM → Eurocódigos` y una familia de plugins verticales (estructuras, puentes, obras lineales, instalaciones, ISO 19650), más el corpus golden verificado. Es conocimiento certificado y no copiable. Es lo que se monetiza.
- **El cebo:** **Aqyra**, un visor OpenBIM asistido por IA, abierto y subvencionado, que ensancha el mercado quitando licencia y curva de aprendizaje. Es la puerta de entrada que cuelga del foso.

La lógica de negocio (cebo y anzuelo / spin-off) está firmada por JM en `Entorno/ESTRATEGIA_NEGOCIO.md` y `Entorno/DECISIONES.md` (D-001…D-007).

---

## 2. Las tres capas + satélites

El ecosistema **no son 10 proyectos sueltos**, son **tres capas** con una relación productor → consumidor, más casos piloto y trabajo lateral.

```
                    ┌─────────────────────────────────┐
                    │   Aqyra-Raiz   (panel raíz)      │  ← estás aquí
                    │   mapa · índice · gobierno       │
                    └─────────────────────────────────┘
                                   observa
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                           ▼
┌───────────────┐        ┌──────────────────┐        ┌──────────────────┐
│  Estructurando│  prod. │ Estructurando 2.0│ cons.  │     Entorno      │
│   (TALLER)    │───────▶│  (GOBIERNO/QA)   │◀──────▶│   (PRODUCTO      │
│  núcleo+plugins│ tags  │ versions.lock    │ ancla  │    Aqyra/visor)  │
└───────────────┘        │ corpus golden    │        └──────────────────┘
                         └──────────────────┘
        ▲                                                     ▲
        │ casos reales que alimentan el corpus                │
   ┌────┴─────┬──────────────┬───────────────────┐
   ▼          ▼              ▼                   ▼
IFC Decopak  Terres      Modelos IFC sin     Fuelia
(Decopak HQ) Cavades     editor Gráfico      Pricing
```

### Capa 1 — El taller (productor): `Estructurando`

> Nota: la carpeta se llamaba `Estrucutrando` (errata); **renombrada a `Estructurando` el 2026-06-26** (Foco 2 del plan).

Es el taller real donde todo se ha construido de forma artesanal. **1,1 GB, 1.345 ficheros.** Contiene:

- El **motor de cálculo** estructural (`Fase1-motor-calculo` … `Fase7-mixtas`, `Nucleo-transversal`).
- El **motor FEM** (`motor-fem`, solver PyNite/MITC4).
- Los **plugins verticales**: `iso19650-openbim`, `puentes`, `obras-lineales`, `instalaciones`, `visor`, `narracion-ifc`.
- El **catálogo de 52 casos de uso** (`Casos-de-uso/`), cada uno con IFC de prueba → modelo neutro → solver → verificación Eurocódigos → memoria.
- Las **hojas de ruta** maestras (ecosistema, motor de cálculo, puentes/FEM, visor).
- Los `.plugin` empaquetados: la **última versión de cada plugin** a la vista en la raíz; las **versiones históricas archivadas en `_releases-historico/`** (Foco 4, 2026-06-26).

Rol: **productor**. Desarrolla artesanal en su rama y publica releases etiquetadas y firmadas que los demás consumen.

### Capa 2 — El gobierno (consumidor): `Estructurando 2.0`

La capa de industrialización: lleva el ecosistema del nivel artesanal (N0) al de producción certificada (N4–N5). **88 ficheros, 696 KB.** Contiene:

- `GOBIERNO_QA_Y_VERSIONES.md` — el contrato productor/consumidor y la QA independiente.
- `versions.lock` — anclaje SemVer de lo que consume (hoy en plantilla, ver desorden #3).
- `contratos-golden/`, `qa/`, `metricas/`, `memoria/`.
- `producto-wedge/` — el PRD del producto de entrada (visor + ISO 19650 + checklist CTE; pricing 1.200–2.400 €/empresa/año).
- `pilotos/` — p. ej. Can Cabassa (primer objetivo de LOI).
- `TESIS_PRODUCTO.md`, `N1.1_plan_release_nucleo.md`, `SPRINT_0.md`.

Rol: **consumidor**. Nunca consume la rama viva; ancla versiones exactas y solo adopta si la suite golden está en verde.

### Capa 3 — El producto (cebo): `Entorno` = Aqyra

El visor OpenBIM productizado. **161 ficheros, 155 MB** (incluye `node_modules`). Monorepo pnpm con frontera física foso/cebo:

- `publico/` — lo que la spin-off puede publicar (visor, openbim, ui-nl, embed, demo, e2e). Stack: web-ifc + That Open Fragments + Vite. Licencia Apache-2.0 (D-003).
- `privado/` — lo que nunca sale (firma, puente-cálculo, qa-pynite, servicio-calculo, verificación-ec).
- `integracion/versions.lock` — ancla el núcleo que consume (este **sí** tiene tags reales).
- Estrategia, decisiones firmadas (D-001…D-007), hojas de ruta del visor (V1–V5).

Rol: **producto / cebo**. Consume el núcleo anclado, no lo bifurca ni lo incrusta.

### Satélites (casos y trabajo lateral)

| Carpeta | Qué es | Relación con el ecosistema |
|---|---|---|
| **IFC Decopak** | Modelo de referencia **Decopak HQ** (21 IFC, validaciones, memorias). | Benchmark de rendimiento y caso de calibración del motor. |
| **Terres Cavades** | IFCs de una estación de servicio (surtidores, lavado, recarga, pérgolas, explanadas). | Caso real multidisciplina; alimenta el corpus. |
| **Modelos IFC sin editor Gráfico** | Trabajo temprano del plugin iso19650 (crear IFC sin Revit/Bonsai). | Histórico; superado por el plugin en el taller. |
| **Fuelia Pricing** | Experimento de pricing (CSV + Python). | Negocio lateral; enlaza con la hipótesis de pricing del anzuelo. |
| ~~Visor IFC~~ | Estaba vacía. | **Retirada el 2026-06-26** (Foco 5). El visor vive en `Entorno/publico/visor` y en el taller. |
| **Aqyra-Raiz** | **Esta carpeta** (antes `Aquira Alfa`, era vacía). | Panel raíz del ecosistema. |

---

## 3. Índice de plugins (últimas versiones empaquetadas)

Artefactos `.plugin` encontrados en el taller. La última versión es la referencia; las anteriores son histórico.

| Plugin | Última versión | Rol en el ecosistema |
|---|---|---|
| `iso19650-openbim` | **v0.9.2** | Parser IFC, BCF, bsDD, requisitos (OIR/EIR), LOIN, validación, CDE-audit. Contrato C1. |
| `motor-calculo-estructural` | **v0.23.0** | Agente ingeniero-estructurista: orquesta IFC→FEM→Eurocódigos→memoria. |
| `motor-fem` | **v0.3.0** | Solver FEM (barras, láminas MITC4, modal). Contrato C5. |
| `puentes` | **v0.6.0** | Tableros (vigas pretensadas, losa postesada, cajón, mixto, celosía, pilas, estribos). |
| `obras-lineales` | **v0.4.0** | Trazado 3.1-IC, firmes 6.1-IC, drenaje 5.2-IC, saneamiento, abastecimiento. |
| `instalaciones` | **v0.3.0** | PCI (BIE, rociadores), eléctrico (REBT). |

A estos se suman las skills `estructuras-eurocodigos` y `cte-documentos-basicos` (instaladas como plugins en el entorno Cowork) y `visor-ifc` / `narracion-ifc`.

---

## 4. Catálogo de casos de uso (52)

El motor crece "núcleo estable + catálogo que crece caso a caso". Cada caso = receta de 7 pasos reutilizando el núcleo.

- **Estructuras (15):** pórtico acero, forjado losa-vigas, losa plana, cubierta inclinada, soporte-zapata, forjado mixto, muros, losa cimentación, cimentación profunda, edificio integrado, pantalla-sismo EC8, viga/losa postesada, viga postesada hiperestática, núcleo sísmico.
- **Puentes (15):** vigas pretensadas, losa postesada, pórtico, celosía, pila-cimentación, estribo, vigas artesa, losa ancha, marco paso inferior, pasarela celosía, pila-pilotes, pila-encepado, estribo cerrado K0 / abierto Ka, puente completo.
- **Obras lineales (6):** eje carretera, trazado, firmes, drenaje, saneamiento, abastecimiento.
- **Instalaciones / PCI (4):** red PCI, BIE a presión, rociadores en malla, MEP.
- **Federación (2):** federación multidisciplina, caso integrado.

---

## 5. Modelo de versiones (contratos C1…C8)

El gobierno versiona **contratos** (interfaces), no solo código (SemVer; MAJOR = cambia un contrato). El productor publica tags firmados; los consumidores los anclan en `versions.lock` y solo adoptan si la golden está en verde.

> **Numeración reconciliada 2026-06-27 (firmada por JM).** Dos familias: **interfaces C1–C8** (C1 IFC · C2 datos · C3 reservado · C4 red · C5 motor-fem · C6 corpus · C7 operador IA · C8 CDE) y **convenciones de núcleo CN-*** (CN-1 memoria del despacho, CN-2 entregables/documentación, CN-3 acciones/bases de cálculo/demanda), que salen del espacio C para no colisionar. Registro único en `Estructurando 2.0/contratos-golden/`. La antigua «C4 = acciones/demanda» pasó a **CN-3** (barrido ejecutado); **C4 = red** queda como interfaz pendiente de documento.

Hay **tres** `versions.lock` en el ecosistema y **no están sincronizados** (ver desorden #3):

| Ubicación | Estado |
|---|---|
| `Entorno/integracion/versions.lock` | Tags reales anclados (motor-fem 0.1.0, motor-calculo 0.1.0, iso19650 0.8.2, visor 0.1.0, estructuras 0.1.0). |
| `Estructurando 2.0/versions.lock` | Plantilla — todo a `0.0.0`. Desincronizado. |
| (referencias en `Estructurando`) | Plan de release N1.1 con los tags del primer corte. |

El cierre formal del release N1.1 (sello de dos llaves: suite golden en verde + tag GPG firmado por JM) figura como **pendiente**.

---

## 6. Documentos clave (para no perderse)

- Negocio: `Entorno/ESTRATEGIA_NEGOCIO.md`, `Entorno/TESIS_PRODUCTO.md`
- Decisiones firmadas: `Entorno/DECISIONES.md` (D-001…D-007)
- Gobierno/QA: `Estructurando 2.0/GOBIERNO_QA_Y_VERSIONES.md`, `N1.1_plan_release_nucleo.md`
- Hojas de ruta: `Estructurando/Hoja-de-ruta_Ecosistema-ingenieria.md`, `Entorno/HOJA_DE_RUTA.md` (visor V1–V5)
- Continuidad del motor: `Estructurando/CONTINUAR-en-nuevo-hilo.md`

---

## 7. Estado de salud del ecosistema

**Lo sólido:** la arquitectura objetivo (productor→consumidor, contratos versionados, foso/cebo, QA golden) está pensada y firmada. El motor tiene 52 casos validados y 6 plugins versionados. El problema **no es de diseño**.

**El problema:** el disco no refleja todavía ese diseño. Hay deriva de nombres, de marca y de versiones. Esto está detallado y priorizado en **`PLAN_CONSOLIDACION.md`** (en esta misma carpeta).
