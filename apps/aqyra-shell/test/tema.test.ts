// Tests «red» del Slice A · tematización + estado del rail (SSD, test antes que código).
// Dominio PURO: sin React/DOM/WASM. Ancla D-CH-2 (tematización por disciplina) y el estado del
// rail (activas Diseño+Estructuras; bloqueadas por ingesta las otras 3). Ratificado por JM
// (2026-07-07). Ver openspec/changes/visor-chrome-shell/.
import { describe, it, expect } from "vitest";
import {
  temaDisciplina,
  railEstados,
  estadoDisciplina,
  DISCIPLINAS_ACTIVAS,
} from "../src/tema";

describe("tema · tematización del chrome por disciplina (D-CH-2)", () => {
  it("Diseño → acento azul de marca + acento suave rgba .16", () => {
    expect(temaDisciplina("diseno")).toEqual({
      acc: "#2f6bed",
      accSoft: "rgba(47, 107, 237, 0.16)",
    });
  });

  it("Estructuras → acento terracota", () => {
    expect(temaDisciplina("estructuras").acc).toBe("#e07a4f");
  });

  it("id desconocido cae en la primera disciplina (Diseño), no lanza", () => {
    expect(temaDisciplina("???").acc).toBe("#2f6bed");
  });
});

describe("rail · estado de disciplina (activa vs bloqueada por ingesta)", () => {
  it("Diseño y Estructuras están activas", () => {
    expect(estadoDisciplina("diseno").estado).toBe("activa");
    expect(estadoDisciplina("estructuras").estado).toBe("activa");
  });

  it("Instalaciones / Obras lineales / Puentes bloqueadas por ingesta", () => {
    for (const id of ["instalaciones", "lineales", "puentes"]) {
      const e = estadoDisciplina(id);
      expect(e.estado).toBe("bloqueada");
      expect(e.motivo).toBe("ingesta");
    }
  });

  it("railEstados cubre las 5 disciplinas en orden y sólo 2 activas", () => {
    const r = railEstados();
    expect(r.map((x) => x.id)).toEqual([
      "diseno",
      "estructuras",
      "instalaciones",
      "lineales",
      "puentes",
    ]);
    expect(r.filter((x) => x.estado === "activa")).toHaveLength(2);
  });

  it("DISCIPLINAS_ACTIVAS = diseno + estructuras", () => {
    expect([...DISCIPLINAS_ACTIVAS].sort()).toEqual(["diseno", "estructuras"]);
  });
});
