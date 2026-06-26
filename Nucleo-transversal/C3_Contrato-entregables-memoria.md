# C3 — Contrato de entregables y memoria (documentación)

**Núcleo transversal · PT 1.4 (Ola 1).** Define una **estructura de memoria homogénea** para
todas las disciplinas, de modo que las skills de memoria (`memoria-calculo`, `memoria-cte`,
futura `memoria-instalaciones`…) compartan formato, citas y trazabilidad. Estado a 22/06/2026.

> Motor de documentos común: skills `docx`/`pdf`/`pptx`/`xlsx`. La estructura de contenido es la
> que se fija aquí; el formato de salida (Word/PDF) lo aporta la skill correspondiente.

---

## 1. Estructura común de memoria (todas las disciplinas)

Toda memoria sigue el mismo esqueleto, con los apartados específicos de cada disciplina dentro:

1. **Datos del proyecto** — emplazamiento, uso/tipología, Anejo Nacional, condicionantes
   (exposición/durabilidad, zona sísmica, zona climática, etc. según disciplina).
2. **Normativa aplicada** — normas y artículos de referencia.
3. **Materiales / componentes adoptados** — con sus parámetros característicos.
4. **Acciones e hipótesis / bases de cálculo** — cargas y combinaciones (C4), o caudales/
   potencias/ocupación en instalaciones.
5. **Comprobaciones por elemento / sistema** — el cuerpo técnico: para cada elemento, el
   modelo, el cálculo, la cláusula normativa y el **aprovechamiento/resultado**.
6. **Registro de comprobaciones (fechado)** — trazabilidad: `AAAA-MM-DD` / elemento / skill /
   parámetros / resultado / decisión.
7. **Conclusiones** — síntesis y advertencias.

---

## 2. Reglas invariables (todas las disciplinas)

- **Citar siempre** el artículo de la norma aplicada (p. ej. *EN 1992-1-1 §6.4.4*; *RIPCI*;
  *REBT ITC-BT-19*).
- Marcar **[confirmar AN]** todo valor NDP (parámetro de determinación nacional) o de
  reglamento no verificado.
- **Unidades SI** coherentes y declaradas (kN, kN·m, MPa, mm en estructuras; l/s, kPa, kW, A en
  instalaciones).
- **Predimensionado/asistencia:** toda memoria incluye la advertencia de **revisión y firma por
  técnico competente**.
- **Una memoria por obra** en su subcarpeta (no mezclar proyectos); hereda los criterios
  transversales de `criterios-<disciplina>.md` (contrato C2).
- **Registro fechado** de cada comprobación, enlazable al caso de uso que la originó.

---

## 3. Encaje con las skills de memoria existentes

- `estructuras-eurocodigos:memoria-calculo` y `motor-calculo-estructural` (memoria Word) →
  memoria de cálculo estructural.
- `cte-documentos-basicos:memoria-cte` → justificación de cumplimiento del CTE.
- Futuro `instalaciones:memoria-instalaciones` → mismo esqueleto, apartados MEP.

Todas reutilizan el motor de documentos (`docx`/`pdf`) y la **plantilla** común
(`plantilla-memoria.md`, esta carpeta).

> **Fuente canónica = `plantilla-memoria.md`** (los 7 apartados de §1). Toda disciplina nueva parte
> de ella. **Alineación pendiente (H4):** la skill `estructuras-eurocodigos:memoria-calculo` documenta
> hoy una estructura distinta ("Objeto y alcance" en vez de "Datos del proyecto", "Modelo estructural"
> separado y **sin** el apartado "Registro de comprobaciones (fechado)"). El generador del motor
> `sismico/generate_memoria_nucleo.py` (caso 15) **sí** sigue este esqueleto. Ajustar la skill al de
> §1 — cambio en el plugin `estructuras-eurocodigos` (Settings > Capabilities), no en este contrato.

## 4. Checklist de cumplimiento (disciplina nueva)

- [ ] Su memoria sigue el esqueleto de 7 apartados.
- [ ] Cita artículos y marca **[confirmar AN]** los NDP.
- [ ] Incluye registro fechado y advertencia de revisión/firma.
- [ ] Una memoria por obra, hereda criterios del despacho (C2).
- [ ] Reutiliza el motor de documentos común para la salida Word/PDF.
