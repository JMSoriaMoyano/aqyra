/**
 * Arnés golden — parking-comb · disposición LONGITUDINAL (viales N-S).
 *
 * Llave 1 (golden verde): prueba que la disposición longitudinal es DETERMINISTA, que
 * los viales corren A LO LARGO del eje largo (Y) con ancho `aisle` y fondo completo,
 * que las plazas van en BATERÍA en bandas a los lados (sin solapes, dentro de la huella)
 * y que los EJES de vial se emiten como ALINEACIONES con un SENTIDO por vial (puente al
 * "parking desde la circulación", paso A→B). La IA prepara; la firma (Llave 2) es de JM.
 * Un fallo se arregla en el código, nunca aflojando el golden.
 *
 *   ../node_modules/.bin/vitest run --root . test/parking-longitudinal.golden.test.ts
 */
import { describe, it, expect } from "vitest";
import { parkingGenerator, parkingAxes, parkingTrajectories, parkingDockY, type ParkingParams, type Footprint } from "../src/generators";
import { resolverAlineacion, selfCheckRadios } from "../src/alineacion";

const ctx = { W: 31, D: 200, h: 3 };
const base: ParkingParams = { bays: 0, aisle: 6, disposition: "longitudinal", lanes: 2 };

const of = (t: string, p: ParkingParams) =>
  parkingGenerator.generate(p, ctx).filter((s) => s.objectType === t);
const overlap = (a: Footprint, b: Footprint): boolean =>
  a.x < b.x + b.w - 1e-6 && a.x + a.w > b.x + 1e-6 && a.y < b.y + b.d - 1e-6 && a.y + a.d > b.y + 1e-6;

describe("parking-comb · disposición longitudinal", () => {
  it("determinista: mismo input → misma salida", () => {
    expect(parkingGenerator.generate(base, ctx)).toEqual(parkingGenerator.generate(base, ctx));
    expect(parkingAxes(base, ctx)).toEqual(parkingAxes(base, ctx));
  });

  it("los viales corren a lo LARGO (Y), ancho = aisle y fondo COMPLETO (no transversales)", () => {
    const viales = of("Vial", base).map((s) => s.footprint);
    expect(viales.length).toBe(2);
    for (const v of viales) {
      expect(v.w).toBe(6);     // ancho del vial = aisle, en X
      expect(v.d).toBe(200);   // fondo completo, en Y (longitudinal)
      expect(v.y).toBe(0);
    }
    expect(viales.map((v) => v.x)).toEqual([5, 21]); // sección: borde · vial · doble · vial · borde
  });

  it("plazas en batería a los lados (prof. en X = 5, ancho en Y = 2,5), llenan el fondo", () => {
    const plazas = of("PlazaAparcamiento", base).map((s) => s.footprint);
    expect(plazas.length).toBe(304); // 4 columnas × 76 plazas (las 4 del fondo S = área de giro, libres)
    expect(plazas[0]).toMatchObject({ w: 5, d: 2.5 }); // profundidad hacia el vial × anchura
    const colsX = [...new Set(plazas.map((f) => f.x))].sort((a, b) => a - b);
    expect(colsX).toEqual([0, 11, 16, 27]); // 2 bandas de borde + 1 banda doble (espalda-espalda)
    expect(Math.max(...plazas.map((f) => f.y + f.d))).toBeCloseTo(200, 6); // fondo lleno por el N
  });

  it("el fondo S queda libre de plazas (área de giro de 180°, R+holgura ≈ 9 m)", () => {
    const plazas = of("PlazaAparcamiento", base).map((s) => s.footprint);
    expect(Math.min(...plazas.map((f) => f.y))).toBeGreaterThanOrEqual(9 - 1e-6); // ninguna plaza pisa el giro
  });

  it("sin solapes y dentro de la huella", () => {
    const fps = of("PlazaAparcamiento", base).map((s) => s.footprint);
    for (const f of fps) {
      expect(f.x).toBeGreaterThanOrEqual(-1e-6);
      expect(f.y).toBeGreaterThanOrEqual(-1e-6);
      expect(f.x + f.w).toBeLessThanOrEqual(31 + 1e-6);
      expect(f.y + f.d).toBeLessThanOrEqual(200 + 1e-6);
    }
    for (let i = 0; i < fps.length; i++)
      for (let j = i + 1; j < fps.length; j++)
        expect(overlap(fps[i], fps[j])).toBe(false);
  });

  it("ejes de vial = alineaciones rectas N-S en el centro del vial, un SENTIDO por vial", () => {
    const ax = parkingAxes(base, ctx);
    expect(ax.length).toBe(2);
    // eje en el centro de cada vial (5+3=8 ; 21+3=24); recta de longitud = fondo
    expect(ax[0].inicio).toMatchObject({ x: 8, y: 0, acimut_deg: 90 });    // S→N
    expect(ax[1].inicio).toMatchObject({ x: 24, y: 200, acimut_deg: 270 }); // N→S (sentido opuesto)
    expect(ax[0].planta).toEqual([{ tipo: "recta", longitud: 200 }]);
    expect(ax.every((a) => a.infraestructura?.clase === "IfcRoad")).toBe(true);
  });

  it("el nº de viales lo decide la huella si no se pide (autoridad del visor)", () => {
    const auto = parkingAxes({ bays: 0, aisle: 6, disposition: "longitudinal" }, ctx);
    expect(auto.length).toBe(2); // en 31 m de ancho caben 2 viales de 6 m con sus bandas
    const tres = parkingAxes({ ...base, lanes: 3 }, ctx);
    expect(tres.length).toBe(2); // se piden 3 pero solo caben 2 → el visor coloca 2
  });

  it("una rampa de acceso recorta las plazas que pisa", () => {
    const sin = of("PlazaAparcamiento", base).length;
    const con = of("PlazaAparcamiento", { ...base, ramps: ["N"] }).length;
    expect(of("Rampa", { ...base, ramps: ["N"] }).length).toBe(1);
    expect(con).toBeLessThan(sin); // la rampa consume plazas por solape
  });

  it("el layout DESCUENTA las plazas que pisa la circulación (clotoides + giro + hueco)", () => {
    // sin rampa: solo el área de giro al S → 304/planta
    expect(of("PlazaAparcamiento", base).length).toBe(304);
    // con rampa N (= P1): además, hueco de rampa al N + barridos de las clotoides → 255.
    // (Corrección de golden ratificada por JM 2026-06-29: el valor previo 253 era artefacto de
    // una deriva de ~3 mm en el aterrizaje de las clotoides —el bucle entero corría al O y el
    // vial de vuelta caía en x=7,997 en vez de 8,000—. Con el aterrizaje exacto, 2 plazas de
    // borde [(0;157,5) y (0;160,0)] quedan a EXACTAMENTE 3,00 m del eje de su vial de acceso
    // = medio carril: son utilizables, como las pegadas a un vial que sostienen base=304.)
    const p1 = of("PlazaAparcamiento", { ...base, ramps: ["N"] });
    expect(p1.length).toBe(255);
    // ninguna plaza queda BAJO la trayectoria (a < medio carril de la directriz)
    const traj = parkingTrajectories({ ...base, ramps: ["N"] }, ctx);
    const pts = traj.flatMap((t) => resolverAlineacion(t, 1).puntos);
    const half = 6 / 2;
    for (const f of p1) {
      const cx = f.x + f.w / 2, cy = f.y + f.d / 2, hw = f.w / 2, hd = f.d / 2;
      const pisada = pts.some(([tx, ty]) => {
        const dx = Math.max(Math.abs(tx - cx) - hw, 0), dy = Math.max(Math.abs(ty - cy) - hd, 0);
        return dx * dx + dy * dy < half * half - 1e-9;
      });
      expect(pisada).toBe(false);
    }
  });
});

describe("parking longitudinal · TRAYECTORIA de circulación (alineación)", () => {
  it("determinista y con la forma recta + arco 180° + recta", () => {
    expect(parkingTrajectories(base, ctx)).toEqual(parkingTrajectories(base, ctx));
    const t = parkingTrajectories(base, ctx);
    expect(t.length).toBe(1); // un bucle por pareja de viales
    const tipos = t[0].planta.map((s) => s.tipo);
    expect(tipos).toEqual(["recta", "curva", "recta"]);
  });

  it("baja por el vial E (N→S) y el giro de 180° tiene radio = media separación de ejes", () => {
    const t = parkingTrajectories(base, ctx)[0];
    expect(t.inicio).toMatchObject({ x: 24, y: 200, acimut_deg: 270 }); // arranque en E, hacia S
    const arco = t.planta[1] as { tipo: string; radio: number; longitud: number };
    expect(arco.radio).toBe(-8);               // giro a derechas, R = (24−8)/2 = 8 m
    expect(arco.longitud).toBeCloseTo(Math.PI * 8, 6); // semicírculo (180°)
  });

  it("el bucle CIERRA: termina en el vial O (x≈8) rumbo N (180° exactos)", () => {
    const r = resolverAlineacion(parkingTrajectories(base, ctx)[0], 1);
    expect(r.fin.x).toBeCloseTo(8, 6);
    expect(r.fin.y).toBeCloseTo(200, 6);
    expect(r.fin.az).toBeCloseTo(Math.PI / 2, 9); // rumbo Norte (subida por O)
  });

  it("vehículo ligero: el giro CUMPLE el radio mínimo (R=8 ≥ 6 m); avisaría si fuese menor", () => {
    const t = parkingTrajectories(base, ctx)[0];
    expect(selfCheckRadios(t, 6).length).toBe(0);   // R=8 ≥ 6 → sin aviso
    expect(selfCheckRadios(t, 9).length).toBe(1);   // si exigiéramos 9 m, avisaría
  });

  it("con rampa N: arranca en el EXTREMO ALTO de la rampa, rumbo S (no en la fachada)", () => {
    const t = parkingTrajectories({ ...base, ramps: ["N"] }, ctx)[0];
    // extremo alto que atraca P1: x=eje rampa (15.5), y = D − recorrido (200 − 20 = 180), rumbo S
    expect(t.inicio).toMatchObject({ x: 15.5, y: 180, acimut_deg: 270 });
  });

  it("ENTRADA y SALIDA con CLOTOIDES (no giros): entra y sale por la rampa = 11 segmentos", () => {
    const t = parkingTrajectories({ ...base, ramps: ["N"] }, ctx)[0];
    // 4 clotoides (entrada) + baja + giro 180° + sube + 4 clotoides (salida)
    expect(t.planta.length).toBe(11);
    expect(t.planta.slice(0, 4).every((s) => s.tipo === "clotoide")).toBe(true);  // entrada
    expect(t.planta[4].tipo).toBe("recta");   // baja E
    expect(t.planta[5].tipo).toBe("curva");   // giro 180°
    expect(t.planta[6].tipo).toBe("recta");   // sube O
    expect(t.planta.slice(7, 11).every((s) => s.tipo === "clotoide")).toBe(true); // salida
    // cada S: curvatura 0→+κ→0→−κ→0 (radios de extremo ±Rt)
    const c = t.planta as Array<{ radio_ini?: number; radio_fin?: number }>;
    expect(c[0].radio_fin).toBe(8); expect(c[3].radio_ini).toBe(-8);  // entrada (desplaza a la izquierda)
    expect(c[7].radio_fin).toBe(-8); expect(c[10].radio_ini).toBe(8); // salida (a la derecha → signo opuesto)
  });

  it("las transiciones cumplen el radio mínimo del vehículo ligero (Rt=8 ≥ 6)", () => {
    const t = parkingTrajectories({ ...base, ramps: ["N"] }, ctx)[0];
    expect(selfCheckRadios(t, 6).length).toBe(0);   // Rt=8 ≥ 6 → sin aviso
    expect(selfCheckRadios(t, 9).length).toBe(9);   // si exigiéramos 9: 4 (entrada) + arco 180° + 4 (salida)
  });

  it("el bucle ENTRA y SALE por la rampa: aterriza en vial E, gira, vuelve a la rampa rumbo N", () => {
    const t = parkingTrajectories({ ...base, ramps: ["N"] }, ctx)[0];
    const r = resolverAlineacion(t, 1);
    // arranca en el extremo alto de la rampa (15.5, 180) rumbo S
    expect(t.inicio).toMatchObject({ x: 15.5, y: 180, acimut_deg: 270 });
    // tras la entrada (4 clotoides) está en el eje del vial E (x=24) rumbo S
    expect(r.segmentos[3].fin.x).toBeCloseTo(24, 3);
    expect(Math.sin(r.segmentos[3].fin.az)).toBeCloseTo(-1, 6);
    // y el bucle completo VUELVE a la rampa (15.5, 180) rumbo N para salir de P1
    expect(r.fin.x).toBeCloseTo(15.5, 2);
    expect(r.fin.y).toBeCloseTo(180, 2);
    expect(Math.sin(r.fin.az)).toBeCloseTo(1, 6); // rumbo N (hacia la rampa de bajada)
  });
});

describe("PB+2 · rampas telescópicas y circulación de P2", () => {
  it("la 2ª rampa TELESCOPA al S: P2 atraca ≈22 m (ocupación clotoide) + 20 m (recorrido) más al S que P1", () => {
    const d1 = parkingDockY(1, base, ctx);
    const d2 = parkingDockY(2, base, ctx);
    expect(d1).toBe(180);                 // P1 = D − recorrido (200 − 20)
    expect(d2).toBeCloseTo(138.5, 1);     // P2 = 180 − (ocupación≈21,5 + recorrido 20)
    // el INICIO de la rampa P1→P2 (= atraque P2 + recorrido) cae al S de la ocupación de P1
    const inicioRampa2 = d2 + 20;
    expect(inicioRampa2).toBeCloseTo(158.5, 1); // = 180 − ocupación: libre de las clotoides de P1
  });

  it("la circulación de P2 repite el patrón, atracada en su cota, y cierra en su rampa", () => {
    const d2 = parkingDockY(2, base, ctx);
    const t = parkingTrajectories({ ...base, ramps: ["N"] }, ctx, 1.0, undefined, d2)[0];
    expect(t.inicio).toMatchObject({ x: 15.5, acimut_deg: 270 });
    expect(t.inicio.y).toBeCloseTo(d2, 2);     // atraca en la cota de P2 (no en 180)
    const r = resolverAlineacion(t, 1);
    expect(r.fin.x).toBeCloseTo(15.5, 2);      // sale por SU rampa (centrada)
    expect(r.fin.y).toBeCloseTo(d2, 2);        // de vuelta a la cota de P2
    expect(Math.sin(r.fin.az)).toBeCloseTo(1, 6); // rumbo N (baja a P1 por la rampa 2)
    expect(selfCheckRadios(t, 6).length).toBe(0); // mismas transiciones, mismo Rt
  });
});
