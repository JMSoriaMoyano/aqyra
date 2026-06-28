# Estrategia de negocio — Cebo y anzuelo (spin-off)

> **Estado:** propuesta de la IA (PM) para revisión y firma de JM · 2026-06-24. Insumo de negocio; **JM decide**.
> **Base:** decisión de producto de JM (visor = primer producto, entrada subvencionada) · `../TESIS_PRODUCTO.md` (señuelo/foso) · `HOJA_DE_RUTA.md`.

---

## 1. El modelo en una frase

> **Cebo:** un visor OpenBIM asistido por IA, abierto y **subvencionado**, que quita los dos guardianes del sector (licencia y curva de aprendizaje) y entra ancho al mercado. **Anzuelo:** los **ingresos recurrentes** que cuelgan de esa entrada — cálculo de firma certificado, reaplicación del corpus golden, y futuras propuestas de valor sobre la misma semilla.

Es la misma lógica de la tesis, vista desde el negocio: el **cebo es el señuelo** (table stakes, asumidamente copiable) y el **anzuelo es el foso** (confianza verificada, no copiable).

---

## 2. El cebo (oferta inicial subvencionada)

- **Qué es:** el visor de la `HOJA_DE_RUTA.md` (V1–V5), con pre/post estructural y copiloto en lenguaje natural, sobre estándares OpenBIM y stack abierto.
- **Por qué subvencionado:** el objetivo no es monetizar el visor, es **adopción**. Quitar licencia + curva ensancha el mercado más allá del BIM manager (proyectista pequeño, técnico de obra, encargado con tablet).
- **Por qué es creíble como gratis/barato:** su coste de desarrollo **ya se amortiza internamente** (ver §4); el cebo externo es el mismo activo que necesitamos dentro.
- **Baja responsabilidad:** un visor no firma; vende proceso y visualización, no responsabilidad estructural. Comprador amplio, fricción comercial baja.

## 3. El anzuelo (ingresos recurrentes)

Lo que se monetiza, colgando de la semilla abierta que el cebo pone en manos del usuario:

- **Cálculo de firma certificado** (bajo dos llaves): convertir el modelo en proyecto calculado y firmado es un incremento ínfimo sobre la semilla, pero la **responsabilidad verificada** es lo escaso y lo que se paga.
- **Reaplicación del corpus golden:** el caso N+1 más barato que el N (el flywheel). El usuario paga por recuperar conocimiento verificado, no por una herramienta.
- **Futuras propuestas de valor:** obra (replanteo en tablet), mantenimiento, premium, soporte — todas cuelgan del mismo IFC vivo.
- **Naturaleza recurrente:** suscripción al anzuelo, no venta única del cebo. El cebo es coste de adquisición; el anzuelo es el *lifetime value*.

## 4. El doble uso (por qué la apuesta es asimétrica)

El visor no es solo un cebo externo: es una **necesidad interna**. La experiencia de Decopak HQ lo demostró — para calcular bien hace falta ver cargas (pre) y esfuerzos/deformaciones (post) sobre el modelo. Por tanto:

- **Lo construiríamos igualmente** para ser más competitivos desarrollando nuestros productos.
- Que **además** sirva de entrada de mercado convierte un coste interno en un **activo de adquisición**. El riesgo de "invertir en un visor commodity" se neutraliza: el commodity es infraestructura propia que ya necesitamos.

Esta asimetría —construyo lo que necesito y de paso me da el wedge— es la mejor razón para que el cebo sea barato de ofrecer.

## 5. La spin-off

- **Aqyra** es el vehículo **externalizable**: producto, marca, OSS, cadencia rápida, audiencia externa.
- El **moat permanece en el ecosistema**: corpus golden, motores de cálculo, criterio del copiloto, gobierno de dos llaves. La spin-off **consume** ese moat (licencia/servicio), no lo posee.
- Por eso el repo separa `publico/` (lo que la spin-off puede publicar) de `privado/` (lo que nunca sale). El límite físico protege la valoración del foso aunque la spin-off escale o se abra.

## 6. Coherencia con la tesis (disciplina de inversión)

| | Cebo (señuelo) | Anzuelo (foso) |
|---|---|---|
| Qué es | Visor asistido por IA, OpenBIM, OSS | Corpus golden verificado + cálculo de firma |
| Riesgo | Copiable (~18 meses) | No scrapeable; confianza acuñada por proceso |
| Regla de inversión | **Lo justo + subvencionado** | **El grueso del esfuerzo** |
| Rol de negocio | Adquisición (entrada ancha) | Ingreso recurrente (LTV) |

**Línea roja:** el éxito del cebo (descargas, adopción) **no es** el éxito del producto. El producto es el flywheel del anzuelo. Vigilar que la tracción del visor no desvíe la inversión del foso.

## 7. Métricas

- **Adopción del cebo:** usuarios activos, modelos abiertos, retención (telemetría V5).
- **Conversión al anzuelo:** % de usuarios del visor que pasan a cálculo/corpus de pago.
- **Flywheel (métrica estrella heredada):** coste marginal del caso N+1 vs N.
- **Doble uso interno:** horas ahorradas en nuestros propios proyectos por usar el pre/post visual.

## 8. Decisiones abiertas para JM

1. ~~Marca del producto~~ **RESUELTO (2026-06-24):** **Aqyra** (paraguas único: CDE + visor + entorno). Ver `DECISIONES.md` D-004.
2. **Grado de subvención / modelo OSS** del cebo (gratis total, freemium, open-core).
3. **Precio del anzuelo** (suscripción; rango por definir; enlaza con la hipótesis de pricing del wedge).
4. **Momento de la spin-off** (cuándo se separa societariamente del ecosistema).
5. **Objetivo de primer cliente externo** (Can Cabassa como validación / primer LOI).

---

*Procedencia: estrategia de negocio del proyecto Aqyra · Estructurando 2.0 (IA · PM) · 2026-06-24 · insumo para decisión y firma de JM.*
