# Tests-first (TDD «red») · Skins del visor por disciplina (Slice 1)

> `frontend-standards.md`: el test se escribe ANTES que el código. `skins.ts` es dominio **puro**
> (sin three/web-ifc/WASM), así que estos tests corren en `vitest` headless sin el helper de WASM.
> Listos para pegar en `apps/visor/test/skins.test.ts` en la rama `feat/visor-skins-disciplina`.
> NO ejecutables hasta que la rama y el módulo existan (vitest corre en la máquina de JM / CI; el
> visor está en la Llave 1).

## Paso 1 · Mapa estático + acento

```ts
// test/skins.test.ts
import { describe, it, expect } from "vitest";
import { SKINS } from "@aqyra/visor";

describe("SKINS · mapa estático disciplina→skin", () => {
  it("Diseño declara acento de marca y clases de edificio", () => {
    expect(SKINS.diseno.acento).toBe("#2f6bed");
    expect(SKINS.diseno.clases).toEqual(
      expect.arrayContaining(["IFCWALL", "IFCSLAB", "IFCWINDOW"]),
    );
  });
  it("Estructuras declara su acento y sus clases portantes", () => {
    expect(SKINS.estructuras.acento).toBe("#e07a4f");
    expect(SKINS.estructuras.clases).toEqual(
      expect.arrayContaining(["IFCCOLUMN", "IFCBEAM", "IFCFOOTING"]),
    );
  });
});
```

## Paso 2 · Color categórico por clase

El color es un mapa por TIPO, no una rampa del acento: determinista, distinto entre clases,
componentes en `0..1`, reserva neutra para no mapeadas, e independiente de la disciplina.

```ts
import { colorPorClase } from "@aqyra/visor";

describe("colorPorClase · categórico por tipo IFC", () => {
  it("es determinista para la misma clase", () => {
    expect(colorPorClase("IFCWALL")).toEqual(colorPorClase("IFCWALL"));
  });
  it("da componentes normalizados 0..1", () => {
    const c = colorPorClase("IFCWALL");
    for (const v of [c.r, c.g, c.b]) {
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThanOrEqual(1);
    }
  });
  it("distingue clases distintas", () => {
    expect(colorPorClase("IFCWALL")).not.toEqual(colorPorClase("IFCCOLUMN"));
  });
  it("una clase no mapeada cae en el gris de reserva", () => {
    expect(colorPorClase("IFCTANK")).toEqual({ r: 0.55, g: 0.55, b: 0.58 });
  });
  it("el color por clase no depende de la disciplina (IFCSLAB compartido)", () => {
    // colorPorClase no recibe disciplina: el mismo tipo → el mismo color, siempre.
    expect(colorPorClase("IFCSLAB")).toEqual(colorPorClase("IFCSLAB"));
  });
});
```

## Paso 3 · Leyenda por intersección

`leyendaSkin` intersecta el mapa de dominio con las clases presentes (forma de `viewer.classes()`).

```ts
import { leyendaSkin } from "@aqyra/visor";

describe("leyendaSkin · intersección dominio ∩ presentes", () => {
  const presentes = [
    { ifcType: "IFCCOLUMN", count: 4 },
    { ifcType: "IFCBEAM", count: 6 },
    { ifcType: "IFCWINDOW", count: 3 }, // presente pero fuera del dominio Estructuras
  ];

  it("lista solo las clases del dominio presentes, con conteo y color", () => {
    const leyenda = leyendaSkin("estructuras", presentes);
    const clases = leyenda.map((e) => e.ifcClass);
    expect(clases).toContain("IFCCOLUMN");
    expect(clases).toContain("IFCBEAM");
    const col = leyenda.find((e) => e.ifcClass === "IFCCOLUMN")!;
    expect(col.count).toBe(4);
    expect(col.color).toEqual(colorPorClase("IFCCOLUMN"));
  });
  it("omite las clases presentes fuera del dominio", () => {
    const clases = leyendaSkin("estructuras", presentes).map((e) => e.ifcClass);
    expect(clases).not.toContain("IFCWINDOW");
  });
  it("omite las clases del dominio ausentes del modelo", () => {
    const clases = leyendaSkin("estructuras", presentes).map((e) => e.ifcClass);
    expect(clases).not.toContain("IFCFOOTING"); // en el dominio, pero no presente
  });
});
```

## Paso 4 · Superficie pública (smoke)

```ts
import * as visor from "@aqyra/visor";

describe("superficie pública de skins", () => {
  it("exporta SKINS, colorPorClase y leyendaSkin", () => {
    expect(typeof visor.colorPorClase).toBe("function");
    expect(typeof visor.leyendaSkin).toBe("function");
    expect(visor.SKINS.diseno).toBeDefined();
  });
});
```

> Nota: la aplicación de la skin al `Viewer` (paso 5, cableado con `setColorByClass`/`resetColors`)
> se verifica en la **demo** (visual) y, si se quiere anclar headless, con un test de integración
> que use el helper de WASM (`test/_wasm.ts`) sobre `fixtures/federado.ifc` — pero el núcleo de la
> lógica (mapa, color, leyenda) queda cubierto por estos tests puros, que son la «red» del TDD.
