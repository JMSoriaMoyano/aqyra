/**
 * Arnés golden — familia de TRAZADO · directriz horizontal RECTA + ARCO (slice 1).
 *
 * Llave 1 (golden verde): prueba que la alineación es DETERMINISTA, que el ARCO se
 * resuelve como CURVA REAL (no una recta), que la traza es CONTINUA y TANGENTE entre
 * segmentos (misma ley que `validacion_alineacion.py` de C1), que la asistencia de
 * radios avisa correctamente y que el handoff `alineaciones[]` casa con el contrato
 * C1 0.10.0 (golden C1-APERTURA-01). La IA prepara; la firma (Llave 2) es de JM. Un
 * fallo se arregla en el código, nunca aflojando el golden.
 *
 *   ../node_modules/.bin/vitest run --root . test/alineacion.golden.test.ts
 */
import { describe, it, expect } from "vitest";
import {
  resolverAlineacion, discretizar, selfCheckRadios, alineacionToAlto,
  checkAlineacionFixture, cambioDeCarrilClotoide, type Alineacion, type AlineacionFixture,
} from "../src/alineacion";

import vial from "../fixtures/alineacion-vial-acceso.json";
import circ from "../fixtures/alineacion-circulacion-parking.json";

const QC = Math.round((Math.PI / 2) * 300 * 1000) / 1000; // cuarto de círculo R=300

/** Recta + arco de 90° a izquierda + recta, escala carretera. */
const ejemplo: Alineacion = {
  nombre: "test",
  inicio: { x: 0, y: 0, acimut_deg: 0, cota: 0 },
  planta: [
    { tipo: "recta", longitud: 100 },
    { tipo: "curva", longitud: QC, radio: 300 },
    { tipo: "recta", longitud: 100 },
  ],
};

describe("alineación · directriz recta + arco", () => {
  it("determinista: mismo input → misma resolución y misma discretización", () => {
    expect(resolverAlineacion(ejemplo, 5)).toEqual(resolverAlineacion(ejemplo, 5));
    expect(discretizar(ejemplo, 5)).toEqual(discretizar(ejemplo, 5));
  });

  it("el arco gira el acimut exactamente 90° y cierra donde toca (no es una recta)", () => {
    const r = resolverAlineacion(ejemplo, 5);
    // recta(100)→(100,0); cuarto de círculo izq R=300 →(400,300) rumbo N; recta(100)→(400,400)
    expect(r.fin.x).toBeCloseTo(400, 3);
    expect(r.fin.y).toBeCloseTo(400, 3);
    expect(r.fin.az).toBeCloseTo(Math.PI / 2, 6);
    expect(r.segmentos[1].centro).toEqual([100, 300]); // centro a la izquierda del rumbo
  });

  it("la curva NO es una recta: el punto medio se separa de la cuerda", () => {
    const arco = resolverAlineacion(ejemplo, 5).segmentos[1];
    const a = arco.puntos[0], b = arco.puntos[arco.puntos.length - 1];
    const mid = arco.puntos[Math.floor(arco.puntos.length / 2)];
    // distancia del punto medio del arco a la cuerda a-b
    const A = b[1] - a[1], B = a[0] - b[0], C = -(A * a[0] + B * a[1]);
    const dist = Math.abs(A * mid[0] + B * mid[1] + C) / Math.hypot(A, B);
    expect(dist).toBeGreaterThan(10); // sagita real de un arco de R=300 (no ~0 de una recta)
  });

  it("continuidad + tangencia: el fin integrado coincide con el último punto y los segmentos encadenan", () => {
    const r = resolverAlineacion(ejemplo, 5);
    const ultimo = r.puntos[r.puntos.length - 1];
    expect(ultimo[0]).toBeCloseTo(r.fin.x, 3);
    expect(ultimo[1]).toBeCloseTo(r.fin.y, 3);
    for (let i = 0; i < r.segmentos.length - 1; i++) {
      const a = r.segmentos[i].fin, b = r.segmentos[i + 1].inicio;
      expect(Math.hypot(a.x - b.x, a.y - b.y)).toBeLessThan(0.05); // sin saltos (TOL_XY de C1)
      const kink = Math.abs(((a.az - b.az + Math.PI) % (2 * Math.PI)) - Math.PI);
      expect(kink).toBeLessThan(1e-3); // sin quiebros de tangencia (TOL_AZ de C1)
    }
  });

  it("paso más fino → más puntos, mismos extremos (la geometría no cambia)", () => {
    const grueso = discretizar(ejemplo, 20);
    const fino = discretizar(ejemplo, 2);
    expect(fino.length).toBeGreaterThan(grueso.length);
    expect(fino[0]).toEqual(grueso[0]);
    expect(fino[fino.length - 1]).toEqual(grueso[grueso.length - 1]);
  });

  it("asistencia de radios: avisa por debajo del mínimo, calla por encima/igual", () => {
    expect(selfCheckRadios(ejemplo, 250)).toEqual([]);          // R=300 ≥ 250
    expect(selfCheckRadios(ejemplo, 300)).toEqual([]);          // R=300 == 300 (no avisa)
    const av = selfCheckRadios(ejemplo, 350);                   // R=300 < 350
    expect(av.length).toBe(1);
    expect(av[0]).toMatchObject({ indice: 1, radio: 300, minimo: 350 });
  });

  it("giro a derechas (radio negativo): centro a la derecha, acimut decrece", () => {
    const der: Alineacion = {
      nombre: "der", inicio: { x: 0, y: 0, acimut_deg: 0, cota: 0 },
      planta: [{ tipo: "curva", longitud: QC, radio: -300 }],
    };
    const r = resolverAlineacion(der, 5);
    expect(r.segmentos[0].centro).toEqual([0, -300]); // a la derecha del rumbo +X
    expect(r.fin.az).toBeCloseTo(-Math.PI / 2, 6);
  });

  it("handoff alto: casa con el esquema de C1 (inicio + planta por longitud/radio)", () => {
    const alto = alineacionToAlto(ejemplo);
    expect(alto.inicio).toEqual({ x: 0, y: 0, acimut_deg: 0, cota: 0 });
    expect(alto.infraestructura).toEqual({ clase: "IfcRoad" }); // default del slice
    expect(alto.planta).toEqual([
      { tipo: "recta", longitud: 100 },
      { tipo: "curva", longitud: QC, radio: 300 },
      { tipo: "recta", longitud: 100 },
    ]);
  });
});

describe("fixtures golden — anti-regresión", () => {
  it("vial de acceso (recta+arco R=300, escala carretera) no regresiona", () => {
    const r = checkAlineacionFixture(vial as unknown as AlineacionFixture);
    expect(r.diffs).toEqual([]);
    expect(r.ok).toBe(true);
  });

  it("circulación de parking (ramal con giro R=6) no regresiona", () => {
    const r = checkAlineacionFixture(circ as unknown as AlineacionFixture);
    expect(r.diffs).toEqual([]);
    expect(r.ok).toBe(true);
  });
});

describe("clotoide · curva de transición (curvatura lineal en s)", () => {
  // Reproduce la planta del golden firmado C1-APERTURA-01: LINE·CLOTHOID·ARC·CLOTHOID·LINE
  const eje: Alineacion = {
    nombre: "Eje C-001", inicio: { x: 0, y: 0, acimut_deg: 0, cota: 100 },
    planta: [
      { tipo: "recta", longitud: 100 },
      { tipo: "clotoide", longitud: 60, radio_fin: 300 },
      { tipo: "curva", longitud: 80, radio: 300 },
      { tipo: "clotoide", longitud: 60, radio_ini: 300 },
      { tipo: "recta", longitud: 100 },
    ],
  };

  it("misma secuencia y longitud que el contrato firmado (L=400, A=√(300·60)=134,164)", () => {
    const r = resolverAlineacion(eje, 2);
    expect(r.segmentos.map((s) => s.tipo)).toEqual(["recta", "clotoide", "curva", "clotoide", "recta"]);
    expect(r.longitudTotal).toBeCloseTo(400, 3);
    expect(Math.sqrt(300 * 60)).toBeCloseTo(134.164, 3); // parámetro A de la clotoide del golden
  });

  it("continuidad + tangencia EXACTAS entre segmentos (umbrales de C1: 0,05 m / 1e-3 rad)", () => {
    const r = resolverAlineacion(eje, 2);
    for (let i = 0; i < r.segmentos.length - 1; i++) {
      const a = r.segmentos[i].fin, b = r.segmentos[i + 1].inicio;
      expect(Math.hypot(a.x - b.x, a.y - b.y)).toBeLessThan(0.05);
      expect(Math.abs(((a.az - b.az + Math.PI) % (2 * Math.PI)) - Math.PI)).toBeLessThan(1e-3);
    }
  });

  it("la clotoide curva DE VERDAD (su punto medio se separa de la cuerda) y es determinista", () => {
    const r = resolverAlineacion(eje, 2);
    expect(resolverAlineacion(eje, 2)).toEqual(r);
    const cl = r.segmentos[1];
    const a = cl.puntos[0], b = cl.puntos[cl.puntos.length - 1], m = cl.puntos[Math.floor(cl.puntos.length / 2)];
    const A = b[1] - a[1], B = a[0] - b[0], C = -(A * a[0] + B * a[1]);
    expect(Math.abs(A * m[0] + B * m[1] + C) / Math.hypot(A, B)).toBeGreaterThan(0.1);
  });

  it("self-check: la clotoide controla su extremo MÁS CERRADO (R=300)", () => {
    expect(selfCheckRadios(eje, 250)).toEqual([]); // todo ≥ 250
    expect(selfCheckRadios(eje, 350).length).toBe(3); // 2 clotoides + 1 arco, todos R=300 < 350
  });

  it("handoff a C1: clotoide con radio_ini/radio_fin (extremo recto omitido), como el contrato", () => {
    expect(alineacionToAlto(eje).planta).toEqual([
      { tipo: "recta", longitud: 100 },
      { tipo: "clotoide", longitud: 60, radio_fin: 300 },
      { tipo: "curva", longitud: 80, radio: 300 },
      { tipo: "clotoide", longitud: 60, radio_ini: 300 },
      { tipo: "recta", longitud: 100 },
    ]);
  });
});

describe("cambio de carril con clotoides (alineaciones paralelas)", () => {
  it("S simétrica de 4 clotoides que aterriza el desfase exacto y sale PARALELA", () => {
    const Rt = 8, lateral = 8.5;
    const { segmentos } = cambioDeCarrilClotoide(270, lateral, Rt); // rumbo S, desfase a la izquierda
    expect(segmentos.length).toBe(4);
    expect(segmentos.every((s) => s.tipo === "clotoide")).toBe(true);
    // curvatura 0→+κ→0→−κ→0
    expect(segmentos[0].radio_fin).toBe(8); expect(segmentos[3].radio_ini).toBe(-8);
    // resolviendo desde un origen, aterriza +8,5 lateral y vuelve al rumbo S
    const al: Alineacion = { nombre: "lc", inicio: { x: 0, y: 0, acimut_deg: 270, cota: 0 }, planta: segmentos };
    const r = resolverAlineacion(al, 1);
    expect(r.fin.x).toBeCloseTo(8.5, 2);              // desfase lateral exacto (x, perpendicular a S)
    expect(Math.sin(r.fin.az)).toBeCloseTo(-1, 6);    // sale rumbo S (paralela)
    expect(selfCheckRadios(al, 6).length).toBe(0);    // Rt=8 ≥ 6 (vehículo ligero)
  });
});

describe("alzado (rasante) · perfil de cota por estación", () => {
  it("reproduce el alzado del contrato firmado C1-APERTURA: cotas encadenadas y rise neto", () => {
    // recta llana de 400 m con alzado rampa(150,2%) · acuerdo(100,2%→−3%) · rampa(150,−3%)
    const eje: Alineacion = {
      nombre: "rasante", inicio: { x: 0, y: 0, acimut_deg: 90, cota: 100 },
      planta: [{ tipo: "recta", longitud: 400 }],
      alzado: [
        { tipo: "rampa", longitud: 150, pendiente_ini: 0.02, pendiente_fin: 0.02 },
        { tipo: "acuerdo", longitud: 100, pendiente_ini: 0.02, pendiente_fin: -0.03 },
        { tipo: "rampa", longitud: 150, pendiente_ini: -0.03, pendiente_fin: -0.03 },
      ],
    };
    const r = resolverAlineacion(eje, 5);
    expect(r.puntos3D).toBeDefined();
    expect(r.cotaFin).toBeCloseTo(98, 3);   // 100 +3 (rampa1) −0.5 (acuerdo) −4.5 (rampa2)
    // la cota sube y luego baja (la rasante no es plana): hay un punto por encima de 103−ε
    const zMax = Math.max(...(r.puntos3D ?? []).map((p) => p[2]));
    expect(zMax).toBeGreaterThan(102.9);
    // handoff a C1: alzado con kv del acuerdo (= L/Δp = −2000)
    const alto = alineacionToAlto(eje);
    expect(alto.alzado?.length).toBe(3);
    expect(alto.alzado?.[1]).toMatchObject({ tipo: "acuerdo", kv: -2000 });
  });

  it("HÉLICE: planta = arco 360°×N · alzado = rampa → sube por planta y cierra el círculo", () => {
    const R = 6, vueltas = 3, grade = 0.08;
    const L = 2 * Math.PI * R * vueltas;
    const helix: Alineacion = {
      nombre: "Hélice N", inicio: { x: 7.5, y: 186.5, acimut_deg: 0, cota: 0 },
      planta: [{ tipo: "curva", longitud: L, radio: R }],
      alzado: [{ tipo: "rampa", longitud: L, pendiente_ini: grade, pendiente_fin: grade }],
    };
    const r = resolverAlineacion(helix, 1);
    // en PLANTA cierra el círculo (mismo XY de inicio y fin)
    expect(r.fin.x).toBeCloseTo(7.5, 3);
    expect(r.fin.y).toBeCloseTo(186.5, 3);
    // en ALZADO sube grade·L = 0.08·113.1 ≈ 9.05 m (3 plantas × ~3 m)
    expect(r.cotaFin).toBeCloseTo(grade * L, 2);
    expect(r.cotaFin).toBeGreaterThan(9);
    // el radio cumple el giro del vehículo ligero
    expect(selfCheckRadios(helix, 6).length).toBe(0); // R=6 ≥ 6
  });
});
