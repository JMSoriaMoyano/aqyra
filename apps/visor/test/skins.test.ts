// Tests «red» del Slice 1 · skins del visor por disciplina (SSD, test antes que código).
// Dominio PURO: sin three/web-ifc/WASM. Rojo esperado hasta que exista apps/visor/src/skins.ts
// y su re-export en src/index.ts (SKINS, colorPorClase, leyendaSkin).
// Ratificado por JM (2026-07-06): D-SK-2 (color categórico) y D-SK-4 (Diseño + Estructuras).
import { describe, it, expect } from "vitest";
import { SKINS, colorPorClase, leyendaSkin, aplicarSkin } from "@aqyra/visor";
import type { AplicadorSkin, ColorRGB } from "@aqyra/visor";

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

describe("colorPorClase · categórico por tipo IFC (D-SK-2)", () => {
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

describe("aplicarSkin · cableado al viewer (mock, sin wasm)", () => {
  // Doble del Viewer: registra las llamadas. El Viewer real satisface AplicadorSkin.
  function dobleViewer(presentes: Array<{ ifcType: string; count: number }>): {
    v: AplicadorSkin;
    pintadas: Array<{ ifcClass: string; color: ColorRGB }>;
    resets: () => number;
  } {
    const pintadas: Array<{ ifcClass: string; color: ColorRGB }> = [];
    let resets = 0;
    const v: AplicadorSkin = {
      resetColors(): void {
        resets += 1;
      },
      setColorByClass(ifcClass: string, color: ColorRGB): void {
        pintadas.push({ ifcClass, color });
      },
      classes(): Array<{ ifcType: string; count: number }> {
        return presentes;
      },
    };
    return { v, pintadas, resets: () => resets };
  }

  it("revierte al color base y pinta cada clase del dominio presente con su color categórico", () => {
    const d = dobleViewer([
      { ifcType: "IFCCOLUMN", count: 2 },
      { ifcType: "IFCWINDOW", count: 1 }, // fuera del dominio Estructuras → no se pinta
    ]);
    const leyenda = aplicarSkin(d.v, "estructuras");
    expect(d.resets()).toBe(1); // revierte antes de pintar
    expect(d.pintadas).toEqual([{ ifcClass: "IFCCOLUMN", color: colorPorClase("IFCCOLUMN") }]);
    expect(leyenda.map((e) => e.ifcClass)).toEqual(["IFCCOLUMN"]);
  });

  it("conmutar de disciplina revierte de nuevo (operación reversible)", () => {
    const d = dobleViewer([{ ifcType: "IFCWALL", count: 3 }]);
    aplicarSkin(d.v, "diseno");
    aplicarSkin(d.v, "estructuras");
    expect(d.resets()).toBe(2); // un reset por aplicación
  });
});

describe("superficie pública de skins", () => {
  it("exporta SKINS, colorPorClase, leyendaSkin y aplicarSkin", () => {
    expect(typeof colorPorClase).toBe("function");
    expect(typeof leyendaSkin).toBe("function");
    expect(typeof aplicarSkin).toBe("function");
    expect(SKINS.diseno).toBeDefined();
  });
});
