# Aqyra — Visor OpenBIM asistido por IA

> **Marca:** «Aqyra» (firmada por JM 2026-06-24, ver `DECISIONES.md` D-004). Marca paraguas única del ecosistema: CDE + visor + entorno. «Entorno» era el placeholder previo. *(La carpeta sigue llamándose `Entorno/` hasta la extracción a repo propio; entonces se renombra a `Aqyra/`.)*
> **Qué es:** el **primer producto** del ecosistema. Un **visor de modelos OpenBIM (IFC) asistido por IA**, donde el usuario trabaja en **lenguaje natural** para hacer el **pre-proceso** (ver estructura y cargas) y el **post-proceso** (ver esfuerzos y deformaciones) de un análisis. Stack 100% abierto (web-ifc/That Open + Three.js), estándares OpenBIM (IFC, BCF, IDS, bsDD).
> **Por qué existe (doble uso):** (a) **necesidad interna** — la experiencia del cálculo estructural de Decopak HQ exige pre/post-proceso visual; nos hace más competitivos desarrollando nuestros productos; (b) **entrada de mercado** — es el **cebo** de una estrategia *cebo y anzuelo* orientada a una **spin-off**.
> **Estado:** scaffold inicial · 2026-06-24 · preparado por la IA (PM) para arranque y firma de JM.

---

## Repo standalone — cómo promoverlo a proyecto propio

Este árbol está pensado para vivir como **repo y proyecto Cowork propios**, hermano de *Estructurando 2.0*, no dentro de él. Se ha creado aquí solo porque es la carpeta montada; el primer paso es **extraerlo**:

1. **Mover y renombrar la carpeta** `Entorno/` fuera de *Estructurando 2.0*, a `…/Claude/Projects/Aqyra/`.
2. **`git init`** en `Aqyra/` (repo propio). Dos visibilidades futuras: `publico/` podrá publicarse abierto; `privado/` nunca.
3. En el escritorio de Claude, **crear un proyecto Cowork nuevo** apuntando a esa carpeta.
4. Pegar el contenido de **`INSTRUCCIONES_PROYECTO.md`** como instrucciones del proyecto.
5. Conectar lo relevante (skills `visor-ifc`, `iso19650-openbim`; conectores que procedan).

Hasta que se extraiga, trabajar aquí es válido; solo conviene no mezclar su cadencia con el gobierno de certificación de 2.0.

## Por qué un proyecto aparte (resumen de la decisión)

- **La estrategia cebo-anzuelo exige un límite limpio público/privado.** El cebo (visor) puede publicarse abierto; el anzuelo (corpus golden, motores de cálculo, criterio del copiloto) **no debe filtrarse**. Repos separados hacen ese límite físico, no solo de intención.
- **Cadencia distinta.** El producto itera rápido; *Estructurando 2.0* gobierna certificación (dos llaves). Mezclarlos crea fricción.
- **Audiencia distinta.** Spin-off / externo vs. industrialización interna.
- **Pero gobernado, no huérfano:** Aqyra es **consumidor** del núcleo bajo el mismo gobierno — ancla versiones en `integracion/versions.lock`, y todo resultado de cálculo que muestre va **bajo dos llaves**. La IA opera; **JM firma**.

## Estructura

```
Aqyra/   (carpeta hoy «Entorno/», se renombra al extraer)
├── README.md                 · este mapa + pasos de promoción
├── HOJA_DE_RUTA.md           · roadmap del visor V1→V5 (entregable principal)
├── ESTRATEGIA_NEGOCIO.md     · cebo y anzuelo · spin-off · ingresos recurrentes
├── INSTRUCCIONES_PROYECTO.md · borrador de instrucciones del proyecto Cowork
├── publico/    · el CEBO (publicable OSS): visor + adaptadores OpenBIM. Sin moat.
├── privado/    · el ANZUELO (moat, NO publicable): copiloto-criterio, puente al cálculo/corpus.
└── integracion/· cómo consume el núcleo anclado (versions.lock) bajo el gobierno compartido.
```

## El límite que no se cruza (cebo vs anzuelo)

| Va en `publico/` (cebo, OSS) | Va en `privado/` (anzuelo, moat) |
|---|---|
| Visor web-ifc/Three.js, navegación, BCF, IDS | Corpus golden y su recuperación por OIR |
| Adaptadores IFC/BCF/bsDD | Motores de cálculo (consumidos anclados) |
| UI del lenguaje natural (la superficie) | El **criterio** que el copiloto recupera del corpus |
| Visualización pre/post (mecánica) | La verificación de dos llaves / la firma |

Regla: *si lo copia un competidor y no perdemos ventaja, es cebo (público). Si al filtrarse se erosiona el foso, es anzuelo (privado).*

---

*Procedencia: scaffold del proyecto Aqyra · Estructurando 2.0 (IA · PM) · 2026-06-24 · para arranque y firma de JM.*
