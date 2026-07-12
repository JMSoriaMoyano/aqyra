// @vitest-environment node
/** Dashboard de valor (E6.1) — tests-first (TDD). `dashboard.ts` es `apps/` puro: presentación de
 *  la proyección PRECOMPUTADA (sin three/web-ifc), corre headless. La ACEPTACIÓN reproduce
 *  `GOL-PRE-03` desde una fixture EMITIDA DEL ENGINE (`apps/visor/fixtures/proyeccion_valor.json`,
 *  vía `tools/emitir_proyeccion_visor.py`), no un oráculo propio: un desajuste se corrige
 *  RE-EMITIENDO la fixture, NUNCA editando el cliente (D-DV-4). El visor está en la Llave 1; el loop
 *  TS corre en la máquina de JM. */
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it, expect } from "vitest";
import {
  modeloVista, sumaVista, vistaDe, guidsDeGrupo, ejesDe, cortesDe,
  isCertified, ESTADO_PROYECCION,
} from "@aqyra/visor";
import type { IndiceProyeccion } from "@aqyra/visor";

const aqui = dirname(fileURLToPath(import.meta.url));
const FIX = join(aqui, "..", "fixtures", "proyeccion_valor.json");
const indice: IndiceProyeccion = JSON.parse(readFileSync(FIX, "utf-8"));

/** Grupo por nombre dentro de una vista (helper de test). */
function grupo(eje: string, corte: string, nombre: string) {
  const v = vistaDe(indice, eje, corte)!;
  return v.grupos.find((g) => g.grupo === nombre)!;
}

describe("dashboard · consume la proyección, no la calcula", () => {
  it("dada (coste, espacial), produce una fila por grupo con valor/unidad/fuente del índice", () => {
    const v = vistaDe(indice, "coste", "espacial")!;
    const mv = modeloVista(v);
    expect(mv.filas.length).toBe(v.grupos.length);
    mv.filas.forEach((f, i) => {
      expect(f.valor).toBe(v.grupos[i]!.valor_total); // valor tal cual del índice
      expect(f.unidad).toBe(v.grupos[i]!.unidad);
      expect(f.fuente).toBe(v.grupos[i]!.fuente);
      expect(f.guids).toEqual(v.grupos[i]!.guids);
    });
  });

  it("no altera ningún valor_total (la presentación es lectura, no cálculo)", () => {
    for (const v of indice.vistas) {
      const mv = modeloVista(v);
      const dentro = mv.filas.map((f) => f.valor);
      const fuente = v.grupos.map((g) => g.valor_total);
      expect(dentro).toEqual(fuente);
    }
  });

  it("dos renders del mismo índice → mismas filas y mismo orden (determinismo)", () => {
    const v = vistaDe(indice, "coste", "funcional")!;
    expect(modeloVista(v)).toEqual(modeloVista(v));
    // el orden es el de la proyección (primera aparición), no reordenado
    expect(modeloVista(v).filas.map((f) => f.grupo)).toEqual(v.grupos.map((g) => g.grupo));
  });

  it("la escala de la barra es geometría de la fila (|valor|/máx), ∈ [0,1]", () => {
    const mv = modeloVista(vistaDe(indice, "coste", "espacial")!);
    for (const f of mv.filas) {
      expect(f.escala).toBeGreaterThanOrEqual(0);
      expect(f.escala).toBeLessThanOrEqual(1);
    }
    expect(Math.max(...mv.filas.map((f) => f.escala))).toBeCloseTo(1, 10); // el mayor grupo llena la barra
  });
});

describe("dashboard · invariante Σ (la vista no pierde ni inventa valor)", () => {
  it("Σ valor_total(grupos) == suma de la vista (±0,01) en las 6 vistas de v0", () => {
    expect(indice.vistas.length).toBe(6); // {coste,carbono} × {espacial,funcional,uniclass}
    for (const v of indice.vistas) {
      expect(sumaVista(v)).toBeCloseTo(v.suma, 2);
      expect(modeloVista(v).invarianteOk).toBe(true);
    }
  });

  it("muestra los grupos residuales (sin geometría)/(sin clasificar) con su fuente, sin ocultarlos", () => {
    const esp = modeloVista(vistaDe(indice, "coste", "espacial")!);
    const sg = esp.filas.find((f) => f.grupo === "(sin geometría)")!;
    expect(sg).toBeDefined();
    expect(sg.fuente).toBe("regla");
    const uni = modeloVista(vistaDe(indice, "coste", "uniclass")!);
    expect(uni.filas.find((f) => f.grupo === "(sin clasificar)")!.fuente).toBe("—");
  });
});

describe("dashboard · reproduce GOL-PRE-03 (coste)", () => {
  it("(coste, espacial): Planta Baja=3815.28 ifc, Nivel 01=2502.9 ifc, (sin geometría)=137.7 regla; Σ=7022.53", () => {
    expect(vistaDe(indice, "coste", "espacial")!.suma).toBeCloseTo(7022.53, 2);
    const pb = grupo("coste", "espacial", "Emplazamiento/Edificio/Planta Baja");
    expect(pb.valor_total).toBeCloseTo(3815.28, 2);
    expect(pb.fuente).toBe("ifc");
    expect(grupo("coste", "espacial", "Emplazamiento/Edificio/Nivel 01").valor_total).toBeCloseTo(2502.9, 2);
    const sg = grupo("coste", "espacial", "(sin geometría)");
    expect(sg.valor_total).toBeCloseTo(137.7, 2);
    expect(sg.fuente).toBe("regla");
  });

  it("(coste, uniclass): (sin clasificar)=6884.83 (—) + (sin geometría)=137.7 regla; Σ=7022.53", () => {
    expect(vistaDe(indice, "coste", "uniclass")!.suma).toBeCloseTo(7022.53, 2);
    const sc = grupo("coste", "uniclass", "(sin clasificar)");
    expect(sc.valor_total).toBeCloseTo(6884.83, 2);
    expect(sc.fuente).toBe("—");
    expect(grupo("coste", "uniclass", "(sin geometría)").valor_total).toBeCloseTo(137.7, 2);
  });

  it("(coste, funcional): Estructura=3754.35 criterio, Aulas=1820.66 ifc, Sys-Portico=543.84 ifc; Σ=7022.53", () => {
    expect(vistaDe(indice, "coste", "funcional")!.suma).toBeCloseTo(7022.53, 2);
    const estructura = grupo("coste", "funcional", "Estructura");
    expect(estructura.valor_total).toBeCloseTo(3754.35, 2);
    expect(estructura.fuente).toBe("criterio"); // *fallback* del criterio visible (D22)
    expect(grupo("coste", "funcional", "Aulas").valor_total).toBeCloseTo(1820.66, 2);
    expect(grupo("coste", "funcional", "Sys-Portico").valor_total).toBeCloseTo(543.84, 2);
    expect(grupo("coste", "funcional", "Sys-Portico").fuente).toBe("ifc");
  });

  it("expone ambos ejes {coste, carbono} y los 3 cortes de v0 (D-DV-2)", () => {
    expect(ejesDe(indice)).toEqual(["coste", "carbono"]);
    expect(cortesDe(indice, "coste")).toEqual(["espacial", "funcional", "uniclass"]);
    expect(cortesDe(indice, "carbono")).toEqual(["espacial", "funcional", "uniclass"]);
  });
});

describe("dashboard · selección → GUIDs (integración con la selección del Viewer)", () => {
  it("seleccionar un grupo expone exactamente los guids[] de ese grupo", () => {
    const v = vistaDe(indice, "coste", "espacial")!;
    const pb = v.grupos.find((g) => g.grupo === "Emplazamiento/Edificio/Planta Baja")!;
    const guids = guidsDeGrupo(v, "Emplazamiento/Edificio/Planta Baja");
    expect(guids).toEqual(pb.guids); // exactamente los del grupo, sin añadir ni quitar
    expect(guids).toContain("0EAm14JNX7Hu9QtYUgOaK4"); // el muro M-Fachada (GUID estable, E2E 5D/6D)
    expect(guids.length).toBeGreaterThan(0);
  });

  it("un grupo residual sin geometría no resalta nada; un grupo inexistente da lista vacía", () => {
    const v = vistaDe(indice, "coste", "espacial")!;
    expect(guidsDeGrupo(v, "(sin geometría)")).toEqual([]);
    expect(guidsDeGrupo(v, "grupo-que-no-existe")).toEqual([]);
  });
});

describe("la vista de proyección no certifica (regla dura «propone», D-DV-5/D-021)", () => {
  it("el estado de la proyección mostrada nunca es 'verified-signed'", () => {
    // la proyección es consulta; el export firmable (dos llaves) llega como acción, no como estado
    expect(ESTADO_PROYECCION).toBe("proposal");
    expect(isCertified(ESTADO_PROYECCION)).toBe(false);
    expect(isCertified("computed")).toBe(false);
    expect(isCertified("verified-signed")).toBe(true); // sólo el export firmado, forward
  });
});
