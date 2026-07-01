// PreAdapter (PURO): autorado de apoyos/cargas como entradas `proposal` (D-011),
// contenedores de casos/combinación, y serialización al anejo diff-able. El
// CRITERIO normativo NO se prueba aquí porque NO vive aquí (anzuelo, privado/).
import { describe, it, expect } from "vitest";
import { PreAdapter } from "@aqyra/openbim";
import type {
  StructuralProvider,
  MemberEndRelease,
  MemberReleases,
  PreDataState,
  ResultGroup,
  ResultEnvelope,
} from "@aqyra/openbim";

/** Rótula estándar: liberar los dos flectores (D-020). */
const ROTULA: MemberEndRelease = { axial: false, vStrong: false, vWeak: false, torsion: false, mStrong: true, mWeak: true };

function fakeProvider(): { provider: StructuralProvider; persisted: Array<Array<{ name: string; value: string }>> } {
  const persisted: Array<Array<{ name: string; value: string }>> = [];
  const provider: StructuralProvider = {
    deriveModel: async () => ({
      nodes: [
        { id: "N1", x: 0, y: 0, z: 0 },
        { id: "N2", x: 0, y: 0, z: 4 },
      ],
      members: [{ id: "B30", kind: "beam", nodeStart: "N1", nodeEnd: "N2" }],
      surfaces: [
        { id: "S5", kind: "diaphragm", ifcType: "IFCSLAB", outline: [[0, 0, 4], [6, 0, 4], [6, 4, 4], [0, 4, 4]], center: [3, 2, 4], normal: [0, 0, 1] },
        { id: "S7", kind: "shell", ifcType: "IFCWALL", outline: [[0, 0, 0], [4, 0, 0], [4, 0, 3], [0, 0, 3]], center: [2, 0, 1.5], normal: [0, 1, 0] },
      ],
      cores: [],
      coreGroups: [],
    }),
    persist: (entries) => persisted.push(entries),
  };
  return { provider, persisted };
}

describe("PreAdapter · autorado proposal (D-011)", () => {
  it("getStructuralModel devuelve el derivado + autorado en estado proposal", async () => {
    const { provider } = fakeProvider();
    const pre = new PreAdapter(provider);
    const m = await pre.getStructuralModel();
    expect(m.state).toBe("proposal");
    expect(m.members.length).toBe(1);
    expect(m.nodes.length).toBe(2);
  });

  it("addLoad crea una carga proposal y persiste el anejo", () => {
    const { provider, persisted } = fakeProvider();
    const pre = new PreAdapter(provider);
    const id = pre.addLoad({ kind: "distributed", target: "B30", value: 5, direction: "y", case: "Q" });
    expect(id).toBe("L1");
    expect(pre.listLoads()[0]!.state).toBe("proposal");
    const last = persisted[persisted.length - 1]!;
    expect(last.some((e) => e.name === "load:L1" && e.value.includes("target=B30"))).toBe(true);
  });

  it("setSupport autora un empotrado proposal y deduplica por nudo", () => {
    const { provider } = fakeProvider();
    const pre = new PreAdapter(provider);
    pre.setSupport("N1", { ux: true, uy: true, uz: true, rx: true, ry: true, rz: true });
    pre.setSupport("N1", { ux: true, uy: true, uz: true, rx: false, ry: false, rz: false });
    expect(pre.listSupports().length).toBe(1);
    expect(pre.listSupports()[0]!.state).toBe("proposal");
    expect(pre.listSupports()[0]!.restraints.rx).toBe(false);
  });

  it("expone contenedores de casos (G,Q) y una combinación ELU genérica editable", () => {
    const { provider } = fakeProvider();
    const pre = new PreAdapter(provider);
    expect(pre.listLoadCases().map((c) => c.id)).toEqual(["G", "Q"]);
    expect(pre.listCombinations()[0]!.limitState).toBe("ULS");
  });

  it("expone superficies derivadas y cambia su idealización (diafragma↔lámina) persistiéndola", async () => {
    const { provider, persisted } = fakeProvider();
    const pre = new PreAdapter(provider);
    const m = await pre.getStructuralModel();
    expect(m.surfaces.length).toBe(2);
    expect(pre.listSurfaces().find((s) => s.id === "S5")!.kind).toBe("diaphragm");
    pre.setSurfaceKind("S5", "shell");
    expect(pre.listSurfaces().find((s) => s.id === "S5")!.kind).toBe("shell");
    const last = persisted[persisted.length - 1]!;
    expect(last.some((e) => e.name === "surface:S5" && e.value.includes("kind=shell"))).toBe(true);
  });

  it("sin proveedor, getStructuralModel falla (superficie declarada, no cableada)", async () => {
    const pre = new PreAdapter();
    await expect(pre.getStructuralModel()).rejects.toThrow();
  });
});

// ── Contrato C5 extendido (V3 · D-018/D-019/D-020/D-021) ──────────────────────
describe("PreAdapter · contrato C5 extendido (V3)", () => {
  it("la combinación lleva `terms` {caso:factor} y se persiste (D-019·C.2.a)", () => {
    const { provider, persisted } = fakeProvider();
    const pre = new PreAdapter(provider);
    const elu = pre.listCombinations()[0]!;
    expect(elu.terms).toEqual({ G: 1.35, Q: 1.5 });
    expect(elu.expression).toContain("1.35"); // se conserva solo para mostrar
    // forzar un persist para inspeccionar el anejo
    pre.setSupport("N1", { ux: true, uy: true, uz: true, rx: true, ry: true, rz: true });
    const last = persisted[persisted.length - 1]!;
    expect(last.some((e) => e.name === "comb:ELU1" && e.value.includes("terms=G:1.35|Q:1.5"))).toBe(true);
  });

  it("setRelease autora una rótula, la adjunta al miembro y la persiste (D-020)", async () => {
    const { provider, persisted } = fakeProvider();
    const pre = new PreAdapter(provider);
    pre.setRelease("B30", "j", ROTULA);
    expect(pre.listReleases()).toEqual([{ memberId: "B30", releases: { j: ROTULA } as MemberReleases }]);
    // se adjunta al miembro al re-derivar el modelo
    const m = await pre.getStructuralModel();
    expect(m.members.find((x) => x.id === "B30")!.releases!.j!.mStrong).toBe(true);
    // round-trip en el anejo: i sin liberar (------), j con los dos flectores (000011)
    const last = persisted[persisted.length - 1]!;
    expect(last.some((e) => e.name === "release:B30" && e.value === "i=------;j=000011")).toBe(true);
  });

  it("setRelease(null) deja el extremo rígido y limpia el release del miembro", () => {
    const { provider } = fakeProvider();
    const pre = new PreAdapter(provider);
    pre.setRelease("B30", "j", ROTULA);
    pre.setRelease("B30", "j", null);
    expect(pre.listReleases()).toEqual([]);
  });

  it("setSurfaceAreaLoad autora carga por área sobre el área real y la persiste (D-019·C.3.a)", async () => {
    const { provider, persisted } = fakeProvider();
    const pre = new PreAdapter(provider);
    await pre.getStructuralModel(); // deriva las superficies S5/S7
    pre.setSurfaceAreaLoad("S5", { q: 5, case: "Q", distributeTo: "edges" });
    expect(pre.listSurfaces().find((s) => s.id === "S5")!.areaLoad!.q).toBe(5);
    const last = persisted[persisted.length - 1]!;
    expect(last.some((e) => e.name === "surface:S5" && e.value.includes("q=5") && e.value.includes("qto=edges"))).toBe(true);
  });

  it("DataState/PreDataState admite las cuatro llaves (D-021)", () => {
    const estados: PreDataState[] = ["proposal", "computed", "qa-passed", "verified-signed"];
    expect(estados).toHaveLength(4);
  });
});

// ── Esquema de RESULTADOS C5 (tipos públicos de salida · D-019·B.3) ────────────
describe("Contrato C5 · esquema de resultados", () => {
  it("un ResultGroup nace `computed` con signos D-018 (N>0 tracción)", () => {
    const rg: ResultGroup = {
      id: "RG-ELU1",
      combinationId: "ELU1",
      state: "computed",
      members: [
        {
          memberId: "B30",
          stations: [
            { x: 0, N: 12.5, V_strong: 3, V_weak: 0, M_strong: -8, M_weak: 0, T: 0, dx: 0, dy: 0, dz: 0 },
            { x: 4, N: 12.5, V_strong: -3, V_weak: 0, M_strong: 0, M_weak: 0, T: 0, dx: 0, dy: -0.012, dz: 0 },
          ],
          utilization: 0.62,
          governing: "flexión eje fuerte",
          passes: true,
        },
      ],
      nodes: [
        { nodeId: "N1", ux: 0, uy: 0, uz: 0, rx: 0, ry: 0, rz: 0, reaction: { fx: 0, fy: 0, fz: 12.5, mx: 0, my: 0, mz: 0 } },
      ],
      surfaces: [],
    };
    expect(rg.state).toBe("computed"); // 0 llaves: NUNCA certificado
    expect(rg.members[0]!.stations[0]!.N).toBeGreaterThan(0); // tracción (D-018)
    expect(rg.members[0]!.passes).toBe(true);
    expect(rg.nodes[0]!.reaction!.fz).toBeGreaterThan(0); // reacción +Z bajo gravedad −Z
  });

  it("una envolvente reporta el extremo y su combinación gobernante", () => {
    const env: ResultEnvelope = {
      id: "ENV-ELU",
      combinationIds: ["ELU1", "ELU2"],
      state: "computed",
      entries: [{ memberId: "B30", maxUtilization: 1.07, governingCombination: "ELU2", passes: false }],
    };
    expect(env.entries[0]!.passes).toBe(false); // aprov. > 1 = «qué no cumple»
    expect(env.entries[0]!.governingCombination).toBe("ELU2");
  });
});
