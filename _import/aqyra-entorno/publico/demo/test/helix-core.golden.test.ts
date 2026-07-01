/**
 * Arnés golden — NÚCLEO DE RAMPA HELICOIDAL del parking (el PUENTE parking ⇄ trazado).
 *
 * Llave 1: prueba que (1) `parking-helix` compone una directriz HELICOIDAL de verdad
 * —arco en planta + alzado en rampa, una vuelta por planta— que SUBE de PB a la última
 * planta; (2) su huella cabe pegada a la fachada pedida; (3) el parking la coloca como
 * NucleoRampa (no IfcSpace), RECORTA plazas y PERFORA los forjados que atraviesa; (4)
 * cruza a C1 por `alineaciones[]` con su alzado → FRONTERA-CERO (C1 0.10.0 monta el
 * IfcAlignment helicoidal). preview = Maestro: la pendiente va redondeada a 3 decimales,
 * así que la hélice aterriza a ~3 cm del nivel exacto (determinista). La IA prepara; firma JM.
 *
 *   ../node_modules/.bin/vitest run --root . test/helix-core.golden.test.ts
 */
import { describe, it, expect } from "vitest";
import { helixFootprint, helixAlineacion, DEFAULT_HELIX_RADIUS } from "../src/parking-helix";
import { resolverAlineacion } from "../src/alineacion";
import { buildModel, openingCount, type BuildingInput } from "../src/model";
import { toAltoSpec } from "../src/c1-bridge";

// Caso del usuario: 20×200, PB+3 (4 plantas a 2,80), núcleo de rampa helicoidal en N.
const W = 20, D = 200, NF = 4, FF = 2.8, R = DEFAULT_HELIX_RADIUS; // R=6
const rise = (NF - 1) * FF; // 8.4 m (PB→P3)

describe("parking-helix — la directriz SUBE como una hélice (arco + rampa)", () => {
  it("huella del núcleo pegada a la fachada N y dentro de la huella", () => {
    const f = helixFootprint("N", R, W, D);
    expect(f.x).toBeGreaterThanOrEqual(0);
    expect(f.x + f.w).toBeLessThanOrEqual(W);
    expect(f.y + f.d).toBeCloseTo(D, 6);      // pegada a la fachada norte (y=D)
    expect(f.w).toBe(2 * (R + 3));            // bbox del círculo exterior (R + medio carril)
  });

  it("una vuelta por planta: planta = 1 arco radio R, alzado = 1 rampa", () => {
    const al = helixAlineacion("N", R, W, D, NF, FF, "NRH");
    expect(al.planta).toHaveLength(1);
    expect(al.planta[0]).toMatchObject({ tipo: "curva", radio: R });
    expect(al.alzado).toHaveLength(1);
    expect(al.alzado?.[0].tipo).toBe("rampa");
    expect(al.inicio.cota).toBe(0);
  });

  it("integrada, la hélice SUBE de 0 al desnivel total (≈ 8,4 m, preview = Maestro)", () => {
    const r = resolverAlineacion(helixAlineacion("N", R, W, D, NF, FF, "NRH"), 1);
    expect(r.puntos3D?.[0][2]).toBe(0);
    expect(r.cotaFin).toBeCloseTo(rise, 1);   // dentro de ~3 cm (pendiente a 3 decimales)
    expect(r.cotaFin).toBeLessThanOrEqual(rise + 1e-9);
  });

  it("determinista: misma hélice → misma directriz", () => {
    const a = resolverAlineacion(helixAlineacion("N", R, W, D, NF, FF, "NRH"), 1);
    const b = resolverAlineacion(helixAlineacion("N", R, W, D, NF, FF, "NRH"), 1);
    expect(JSON.stringify(a)).toEqual(JSON.stringify(b));
  });
});

describe("parking + núcleo helicoidal — no IfcSpace, perfora forjados", () => {
  const input: BuildingInput = {
    project: "Parking SABA", building: "P",
    storeys: { count: 3, height: 2.8 },
    plan: { rooms: null, corridor: null, cores: [] },
    program: { generator: "parking-comb", params: { bays: 60, aisle: 6, core: { kind: "helix", side: "N" } } },
  };
  const CTX = { W: 20, D: 60 };

  it("el NucleoRampa NO es un IfcSpace", () => {
    const m = buildModel(input, CTX);
    expect(m.storeys.flatMap((s) => s.spaces).some((s) => s.objectType === "NucleoRampa")).toBe(false);
  });

  it("perfora el forjado de cada planta de piso (no la cubierta)", () => {
    const m = buildModel(input, CTX);
    expect(openingCount(m)).toBe(2); // 3 plantas → forjados P01 y P02 (la cubierta no se perfora)
    const hue = m.storeys.flatMap((s) => s.elements).find((e) => e.ifcClass === "IfcOpeningElement")!;
    expect(hue.host).toMatch(/^AQ-FOR-P0[12]$/);
    expect(hue.placement.kind).toBe("polygon");
  });
});

describe("c1-bridge — la hélice cruza por alineaciones[] con alzado (frontera-cero)", () => {
  it("emite la alineación helicoidal con su rasante", () => {
    const helix = helixAlineacion("N", R, W, D, NF, FF, "Núcleo rampa helicoidal");
    const spec = toAltoSpec(buildModel({
      project: "P", building: "P", storeys: { count: NF, height: FF },
      plan: { rooms: null, corridor: null, cores: [] },
      program: { generator: "parking-comb", params: { bays: 40, aisle: 6, core: { kind: "helix", side: "N" } } },
    }, { W, D }), { ancho: W, largo: D, altura: FF }, [helix]);
    expect(spec.alineaciones?.length).toBe(1);
    const a = spec.alineaciones![0];
    expect(a.planta[0]).toMatchObject({ tipo: "curva", radio: R });
    expect(a.alzado?.[0].tipo).toBe("rampa");
    expect(a.alzado?.[0].pendiente_ini).toBeGreaterThan(0); // SUBE
  });
});
