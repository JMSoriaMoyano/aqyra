# CN-1 — Convención de memoria del despacho (aprendizaje entre hilos)

> **Reconciliación de numeración (2026-06-27, firmada por JM).** Este contrato era **«C2 — memoria del despacho»**. Para evitar la colisión con el **C2 canónico = datos**, se traslada a la familia **CN- (Convenciones de Núcleo)**, que agrupa las convenciones transversales que no son interfaces entre piezas. Sucede a `C2_Contrato-memoria-despacho.md` (ahora puntero). Esquema vigente: interfaces **C1–C8** · convenciones de núcleo **CN-1 (memoria)**, **CN-2 (entregables/documentación)**.

**Núcleo transversal · PT 1.3 (Ola 1).** Generaliza el mecanismo de memoria ya probado en
estructuras para que **toda disciplina aprenda entre hilos** con el mismo formato y ubicación
estable. Estado a 22/06/2026 (numeración actualizada 2026-06-27).

> Las skills `criterios-memoria` de cada plugin **leen estos archivos al iniciar**: el formato y
> la ubicación deben mantenerse estables.

---

## 1. Dos niveles de memoria

1. **Criterios del despacho (entre proyectos):** un archivo por disciplina en la **raíz** de la
   carpeta de trabajo. Acumula decisiones que se repiten en todos los proyectos (materiales por
   defecto, Anejo Nacional, coeficientes, criterios de diseño, lecciones aprendidas).
   - `criterios-despacho.md` — estructuras *(ya existe)*
   - `criterios-instalaciones.md` — instalaciones *(a crear en Ola 4)*
   - `criterios-<disciplina>.md` — patrón general
2. **Memoria del proyecto (por obra):** una `memoria-<disciplina>.md` en la **subcarpeta** de
   cada proyecto, con las decisiones e hipótesis específicas y el registro de comprobaciones.

A esto se añade el **programa de aprendizaje** (3 docs en `Casos-de-uso/`): `PROGRAMA`,
`REPOSITORIO`, `CHANGELOG` — mecanismo de crecimiento del plugin.

---

## 2. Árbol de carpetas de proyecto (convención reutilizable)

```
<Carpeta-de-trabajo>/
├── criterios-<disciplina>.md          # criterios del despacho (transversal, entre proyectos)
├── Casos-de-uso/
│   ├── PROGRAMA-aprendizaje.md         # escalera de casos + protocolo (DoD)
│   ├── REPOSITORIO-aprendizaje.md      # lecciones, backlog de incidencias, métricas
│   └── CHANGELOG-plugin.md             # versiones del plugin (SemVer)
└── <Proyecto-X>/
    ├── memoria-<disciplina>.md         # memoria de la obra (decisiones, hipótesis, registro)
    ├── modelo.ifc                      # soporte IFC
    └── _resultados/                    # salidas (diagramas, memoria Word, JSON neutro)
```

---

## 3. Plantilla de `criterios-<disciplina>.md`

> Plantilla lista para copiar también en `plantilla-criterios-disciplina.md` (esta carpeta).

```markdown
# Criterios de despacho - <Disciplina>

> Capa transversal de memoria (se acumula entre todos los proyectos).
> Las skills del plugin `<plugin>` LEEN este archivo al iniciar: mantener formato y ubicación.
> Todo resultado derivado debe ser **revisado y firmado por técnico competente**.

## Normativa
- Anejo Nacional / reglamento por defecto: **España**
- Normas de referencia: <listar>

## Materiales / componentes habituales
- <p. ej. Hormigón C30/37; o, en instalaciones, tubería/cable/conducto por defecto>

## Coeficientes y criterios
- <coeficientes parciales, límites de servicio, criterios de diseño> [confirmar AN/Reglamento]

## Lecciones aprendidas (crece hilo a hilo)
- [AAAA-MM-DD] <lección> / <razón> / <referencia normativa>. [caso N]

## Formato de memoria
- Una memoria por obra en su subcarpeta; citar siempre el artículo aplicado.
- Marcar **[confirmar AN]** los valores NDP no verificados.
- Registro de comprobaciones fechado (AAAA-MM-DD): elemento / skill / parámetros / resultado / decisión.
- Unidades SI.
```

---

## 4. Reglas del contrato CN-1

- **Ubicación estable:** criterios en la raíz; memoria en la subcarpeta del proyecto.
- **Formato estable:** secciones fijas (Normativa, Materiales, Coeficientes, Lecciones, Formato).
- **Entradas fechadas:** toda lección y comprobación lleva fecha `AAAA-MM-DD` y, si aplica, el
  caso de uso que la originó.
- **Trazabilidad normativa:** citar artículo; marcar **[confirmar AN]** los NDP.
- **Una skill `criterios-memoria` por plugin** inicializa y mantiene estos archivos.

## 5. Checklist de cumplimiento (disciplina nueva)

- [ ] Tiene `criterios-<disciplina>.md` en la raíz con las 5 secciones.
- [ ] Tiene `Casos-de-uso/` con PROGRAMA + REPOSITORIO + CHANGELOG.
- [ ] Cada proyecto tiene su `memoria-<disciplina>.md` en subcarpeta.
- [ ] Su skill `criterios-memoria` lee/escribe estos archivos al iniciar.
