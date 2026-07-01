/**
 * Arnés golden — USABILIDAD · slice #1 (skin Diseño): la columna izquierda.
 *
 * Llave 1 (golden verde) de la parte DETERMINISTA de una mejora de UX: las
 * invariantes de layout y de scroll de la columna izquierda de Diseño. No prueba
 * "que se vea bonito" (eso es la Llave 2, el ojo de JM) sino el contrato que evita
 * la regresión concreta que motivó el slice:
 *
 *   (1) el ÁRBOL (estructura espacial) es el panel primario y tiene un SUELO de
 *       altura ⇒ auditoría y detalle NO pueden ocultarlo (crecen con scroll propio);
 *   (2) el panel de AUDITORÍA usa el MISMO scroll "discreto" que el resto;
 *   (3) detalle + auditoría no pueden, sumados, reclamar toda la columna.
 *
 * Frontera C1: cero (UI/UX, no toca alto.json ni el contrato). La IA prepara; la
 * firma (Llave 2) es de JM. Un fallo se arregla en el código, nunca aflojando el
 * golden.
 *
 *   ../node_modules/.bin/vitest run --root . test/diseno-layout.golden.test.ts
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const html = readFileSync(fileURLToPath(new URL("../diseno.html", import.meta.url)), "utf8");

/** Cuerpo del bloque de reglas de un selector exacto `sel { … }` (primera aparición). */
function ruleBody(sel: string): string {
  const m = html.match(new RegExp(sel.replace(/[#.]/g, "\\$&") + "\\s*\\{([^}]*)\\}"));
  if (!m) throw new Error(`no se encontró la regla CSS «${sel} { … }»`);
  return m[1];
}

describe("Diseño · columna izquierda — el árbol no se oculta", () => {
  // El tamaño fino de detalle/auditoría lo gobierna ahora el splitter (slice #2);
  // la invariante de CSS que queda es el SUELO del árbol (la 2.ª fila), que también
  // es el `min` del track flex en el splitter: el árbol nunca colapsa a cero.
  it("el árbol (#tree) reserva un SUELO de altura con minmax()", () => {
    const rows = ruleBody("#tree").match(/grid-template-rows:\s*([^;]+);/);
    expect(rows, "#tree debe declarar grid-template-rows").not.toBeNull();
    expect(rows![1]).toMatch(/minmax\(\s*\d+px\s*,\s*1fr\s*\)/);
  });
});

describe("Diseño · columna izquierda — scroll discreto homogéneo", () => {
  // Selectores que comparten el tratamiento de scroll fino. #audit DEBE estar.
  const grupos = [
    /([^{}]*)\{\s*scrollbar-width:\s*thin/,                 // Firefox (scrollbar-width)
    /([^{}]*)::-webkit-scrollbar\s*\{\s*width:\s*7px/,      // WebKit (ancho)
    /([^{}]*)::-webkit-scrollbar-thumb\s*\{\s*background:\s*rgba\(255, 255, 255, \.09\)/, // WebKit (pulgar)
  ];
  it.each(grupos.map((re, i) => [i, re] as const))(
    "el panel de auditoría (#audit) está en el grupo de scroll discreto #%i",
    (_i, re) => {
      const m = html.match(re);
      expect(m, "no se encontró el grupo de scroll discreto").not.toBeNull();
      expect(m![1]).toContain("#audit");
    },
  );
});
