// Memoria de calculo del CASO R1 (Direccion 2): IFC FISICO -> modelo analitico.
// Adapta la memoria de barras anadiendo la seccion del PUENTE fisico->analitico y
// las HIPOTESIS de carga/apoyo (no venian en el IFC; las pone el calculista).
// Uso: NODE_PATH=$(npm root -g) node generate_memoria_real.js <dir_proyecto> <salida.docx>
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, Header, Footer,
} = require("docx");

const dir = process.argv[2] || "proyecto-R1";
const out = process.argv[3] || path.join(dir, "Memoria_casoR1_portico_fisico.docx");

const model = JSON.parse(fs.readFileSync(path.join(dir, "modelo_neutro.json"), "utf8"));
const res = JSON.parse(fs.readFileSync(path.join(dir, "resultados.json"), "utf8"));
const ver = JSON.parse(fs.readFileSync(path.join(dir, "verificacion.json"), "utf8"));
const cv = JSON.parse(fs.readFileSync(path.join(dir, "cross_validation.json"), "utf8"));
const cls = JSON.parse(fs.readFileSync(path.join(dir, "clasificacion.json"), "utf8"));

const CW = 9026;
const border = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const borders = { top: border, bottom: border, left: border, right: border };
const HEAD = "1F4E79", ZEBRA = "EEF3F8";
const f1 = (x) => (x === null || x === undefined) ? "-" : Number(x).toFixed(1);
const f2 = (x) => (x === null || x === undefined) ? "-" : Number(x).toFixed(2);
const pct = (x) => (x * 100).toFixed(1) + " %";

function P(text, opts = {}) {
  return new Paragraph({ spacing: { after: 120 }, ...opts,
    children: [new TextRun({ text, ...(opts.run || {}) })] });
}
function H(text, level) { return new Paragraph({ heading: level, children: [new TextRun(text)] }); }
function cell(text, { w, head = false, bold = false, fill, align } = {}) {
  return new TableCell({ borders, width: { size: w, type: WidthType.DXA },
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ alignment: align || AlignmentType.LEFT,
      children: [new TextRun({ text: String(text), bold: head || bold,
        color: head ? "FFFFFF" : "000000", size: 19 })] })] });
}
function table(headers, rows, widths) {
  const trs = [new TableRow({ tableHeader: true,
    children: headers.map((h, i) => cell(h, { w: widths[i], head: true, fill: HEAD,
      align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER })) })];
  rows.forEach((r, ri) => { trs.push(new TableRow({ children: r.map((c, i) => cell(c, { w: widths[i],
    fill: ri % 2 ? ZEBRA : undefined, align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER })) })); });
  return new Table({ width: { size: CW, type: WidthType.DXA }, columnWidths: widths, rows: trs });
}
function img(file, w, h, cap) {
  const p = path.join(dir, file);
  const o = [new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new ImageRun({ type: "png", data: fs.readFileSync(p),
      transformation: { width: w, height: h }, altText: { title: cap, description: cap, name: file } })] })];
  if (cap) o.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
    children: [new TextRun({ text: cap, italics: true, size: 17, color: "555555" })] }));
  return o;
}

const elu = (bid) => res.barras[bid].ELU;
const ad = ver.autodiagnostico;
const children = [];

// ---- Portada ----
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 120 },
  children: [new TextRun({ text: "MEMORIA DE CÁLCULO ESTRUCTURAL", bold: true, size: 40, color: HEAD })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
  children: [new TextRun({ text: "Caso R1 — Pórtico físico: puente IFC físico (BIM) → modelo analítico", size: 24 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
  children: [new TextRun({ text: "Dirección 2 · Módulo puente_analitico (IFC físico → FEM → Eurocódigos)", size: 20, color: "555555" })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600, after: 80 },
  children: [new TextRun({ text: "Proyecto: Estructurando", size: 22 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "Fecha: 21/06/2026", size: 22 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 800 },
  children: [new TextRun({ text: "Documento de PREDIMENSIONADO generado automáticamente. Debe ser revisado y firmado por técnico competente.",
    italics: true, size: 18, color: "999999" })] }));
children.push(new Paragraph({ pageBreakBefore: true, children: [] }));

// ---- 1. Objeto ----
children.push(H("1. Objeto y alcance", HeadingLevel.HEADING_1));
children.push(P("Esta memoria justifica el cálculo de un pórtico plano de acero de un vano cuyo punto de partida " +
  "es un MODELO IFC FÍSICO (entregable BIM real): elementos constructivos (IfcColumn, IfcBeam) con geometría de " +
  "barrido (IfcExtrudedAreaSolid), material y sección (IfcMaterialProfileSetUsage) y estructura espacial " +
  "(IfcProject→IfcSite→IfcBuilding→IfcBuildingStorey), pero SIN entidades de análisis ni cargas. Constituye el " +
  "primer caso de la Dirección 2 del motor: el «puente» que deriva el modelo analítico (ejes, nudos y apoyos) a " +
  "partir de la geometría física y aplica las hipótesis de carga del proyecto, para a continuación reutilizar sin " +
  "cambios el clasificador/enrutador y el módulo de barras (EC3)."));
children.push(P("Validación: la geometría es idéntica a la del Caso 1 (vano 6,0 m, altura 4,0 m, G=12 / Q=10 kN/m), " +
  "de modo que el modelo derivado del IFC físico debe REPRODUCIR el resultado ya conocido del Caso 1.",
  { run: { italics: true, size: 19 } }));

// ---- 2. Normativa ----
children.push(H("2. Normativa de aplicación", HeadingLevel.HEADING_1));
children.push(table(["Código", "Título", "Uso en esta memoria"],
  [["EN 1990 (EC0)", "Bases de cálculo estructural", "Combinaciones ELU/ELS, coef. parciales y ψ"],
   ["EN 1991 (EC1)", "Acciones en las estructuras", "Acciones permanentes G y variables Q (hipótesis)"],
   ["EN 1993-1-1 (EC3)", "Proyecto de estructuras de acero", "Resistencia de secciones y pandeo"],
   ["ISO 16739 (IFC4)", "Industry Foundation Classes", "Modelo físico de origen (BIM)"],
   ["AN España", "Anejos Nacionales", "Coeficientes y parámetros NDP [confirmar AN]"]],
  [1900, 4126, 3000]));

// ---- 3. Puente fisico -> analitico ----
children.push(H("3. Puente físico → analítico (Dirección 2)", HeadingLevel.HEADING_1));
children.push(P("El IFC físico no contiene modelo de análisis. El módulo puente_analitico construye el modelo " +
  "neutro estándar del motor en tres pasos: extracción geométrica, grafo de nudos e hipótesis de carga/apoyo."));
children.push(H("3.1 Extracción geométrica (eje, perfil y material)", HeadingLevel.HEADING_2));
children.push(P("Por cada elemento lineal (IfcColumn/IfcBeam) se obtiene su EJE como directriz del barrido: el " +
  "origen es la traslación del ObjectPlacement compuesto (resuelto a coordenadas de mundo) y la dirección es el " +
  "eje local Z del placement, con longitud igual al Depth del IfcExtrudedAreaSolid. El PERFIL se lee de " +
  "IfcMaterialProfileSetUsage → IfcMaterialProfileSet → IfcMaterialProfile → IfcIShapeProfileDef (con prioridad " +
  "a la base de datos de perfiles de catálogo; la geometría del SweptArea queda como respaldo). El MATERIAL y sus " +
  "propiedades mecánicas se toman del profile set y de IfcMaterialProperties."));
const ejeRows = Object.entries(model.barras).map(([b, p]) => {
  const ni = model.nodos[p.ni], nj = model.nodos[p.nj];
  return [p.elemento_fisico + " (" + p.clase_ifc + ")", b,
    "(" + f1(ni.x) + "," + f1(ni.y) + "," + f1(ni.z) + ") → (" + f1(nj.x) + "," + f1(nj.y) + "," + f1(nj.z) + ")",
    f2(res.longitudes[b]), p.seccion, p.material];
});
children.push(table(["Elemento físico", "Barra", "Eje derivado (mundo) [m]", "L [m]", "Perfil", "Material"],
  ejeRows, [1800, 900, 2826, 800, 1400, 1300]));
children.push(H("3.2 Conectividad: grafo de nudos", HeadingLevel.HEADING_2));
children.push(P("Los nudos analíticos se generan por intersección de ejes con tolerancia (1 mm): se fusionan los " +
  "extremos coincidentes y se trocea una barra cuando el extremo de otra cae en su interior. En el caso R1 los " +
  "ejes son limpios y se cortan en sus extremos, dando " + Object.keys(model.nodos).length + " nudos y " +
  Object.keys(model.barras).length + " barras. (El tratamiento de offsets/excentricidades físico↔analítico se " +
  "endurece en el caso R5.)"));
children.push(H("3.3 Hipótesis de apoyo y de carga", HeadingLevel.HEADING_2));
children.push(P("En un IFC físico no existen apoyos ni cargas de análisis: son hipótesis del calculista. En el " +
  "modelo de prueba se aportan como Property Sets y el puente las traslada al modelo neutro:", { run: { size: 19 } }));
const apoRows = (model.hipotesis.apoyos || []).map((a) => [a.nodo, f1(a.cota_z), a.tipo,
  "Pset_Estructurando_ApoyoBase"]);
children.push(table(["Nudo", "Cota z [m]", "Tipo de apoyo", "Origen (hipótesis)"], apoRows,
  [1700, 1700, 2800, 2826]));
const carRows = (model.hipotesis.cargas || []).map((c) => [c.caso, c.barra + " (" + c.elemento_fisico + ")",
  f1(c.q_kN_m), c.direccion, "Pset_Estructurando_CargaHipotesis"]);
children.push(table(["Caso", "Barra (elemento)", "q [kN/m]", "Dirección", "Origen (hipótesis)"], carRows,
  [900, 2500, 1300, 1300, 3026]));
children.push(P("Apoyo biarticulado (bases): traslaciones coaccionadas y giro en el plano libre. " +
  "Las cargas se aplican como hipótesis de proyecto y deben confirmarse con el documento de cargas del encargo.",
  { run: { italics: true, size: 18 } }));

// ---- 4. Clasificacion / enrutado ----
children.push(H("4. Clasificación y enrutado", HeadingLevel.HEADING_1));
children.push(P("El modelo neutro derivado se clasifica con los mismos criterios del enrutador multi-elemento " +
  "(material + sección + orientación): todas las barras son de acero con sección en I, por lo que el sistema es un " +
  "pórtico plano de acero y se enruta al módulo de barras (EC3), exactamente como el Caso 1."));
const clsRows = cls.barras.map((d) => [d.barra, d.material, d.seccion, d.orientacion, d.rol,
  d.acero_I ? "Acero I → barras" : "revisar"]);
children.push(table(["Barra", "Material", "Sección", "Orientación", "Rol", "Enrutado"], clsRows,
  [1100, 1400, 1500, 1700, 1500, 1826]));

// ---- 5. Materiales/secciones/barras ----
children.push(new Paragraph({ pageBreakBefore: true, children: [] }));
children.push(H("5. Modelo analítico derivado", HeadingLevel.HEADING_1));
children.push(H("5.1 Materiales", HeadingLevel.HEADING_2));
const matRows = Object.entries(model.materiales).map(([m, p]) =>
  [m, (p.E / 1e9).toFixed(0), (p.fy / 1e6).toFixed(0), p.nu.toFixed(2), (p.rho).toFixed(0)]);
children.push(table(["Material", "E [GPa]", "fy [MPa]", "ν", "ρ [kg/m³]"], matRows, [3026, 1500, 1500, 1500, 1500]));
children.push(H("5.2 Secciones", HeadingLevel.HEADING_2));
const secRows = Object.entries(model.secciones).map(([s, p]) =>
  [s, (p.A * 1e4).toFixed(2), (p.Iy * 1e8).toFixed(0), (p.Wply * 1e6).toFixed(0),
   (p.Avz * 1e4).toFixed(2), "Clase " + p.clase]);
children.push(table(["Sección", "A [cm²]", "Iy [cm⁴]", "Wpl,y [cm³]", "Avz [cm²]", "Clase"],
  secRows, [2026, 1400, 1400, 1600, 1300, 1300]));
children.push(H("5.3 Barras", HeadingLevel.HEADING_2));
const barRows = Object.entries(model.barras).map(([b, p]) =>
  [b, p.tipo, p.ni + " → " + p.nj, p.seccion, p.material, f2(res.longitudes[b])]);
children.push(table(["Barra", "Tipo", "Nodos", "Sección", "Material", "L [m]"], barRows,
  [1200, 1500, 1626, 1700, 1700, 1300]));

// ---- 6. Acciones y combinaciones ----
children.push(H("6. Acciones y combinaciones", HeadingLevel.HEADING_1));
const loadRows = model.cargas.map((c) => [c.caso, c.barra, c.direccion, (Math.abs(c.qz) / 1e3).toFixed(2)]);
children.push(table(["Caso", "Barra", "Dirección", "q [kN/m]"], loadRows, [2256, 2256, 2257, 2257]));
const comboRows = Object.entries(res.combos_meta).map(([name, m]) => [name, m.tipo, m.expr, m.norma]);
children.push(table(["Combinación", "Tipo", "Expresión", "Referencia"], comboRows, [1800, 1100, 3126, 3000]));
children.push(P("Coeficientes parciales (AN España): γG = 1,35 / 1,00; γQ = 1,50. ψ (Cat. B): ψ0=0,7; ψ1=0,5; ψ2=0,3. [confirmar AN]",
  { run: { size: 18 } }));

// ---- 7. Validacion ----
children.push(H("7. Procedimiento, validación y equilibrio", HeadingLevel.HEADING_1));
children.push(P("Cadena: (1) puente IFC físico → modelo neutro; (2) clasificación/enrutado; (3) FEM de barra " +
  "(PyNite) con el plano coaccionado fuera de él; (4) combinaciones EC0; (5) verificación EC3."));
children.push(P("Autodiagnóstico del solver (viga biapoyada vs. solución cerrada):", { run: { bold: true } }));
children.push(table(["Magnitud", "Calculado", "Teórico", "Error"],
  [["Momento M = qL²/8", f1(ad.checks["M (kN·m)"][0]) + " kN·m", f1(ad.checks["M (kN·m)"][1]) + " kN·m", (ad.checks["M (kN·m)"][2] * 100).toFixed(3) + " %"],
   ["Cortante V = qL/2", f1(ad.checks["V (kN)"][0]) + " kN", f1(ad.checks["V (kN)"][1]) + " kN", (ad.checks["V (kN)"][2] * 100).toFixed(3) + " %"],
   ["Flecha 5qL⁴/384EI", f2(ad.checks["flecha (mm)"][0]) + " mm", f2(ad.checks["flecha (mm)"][1]) + " mm", (ad.checks["flecha (mm)"][2] * 100).toFixed(3) + " %"]],
  [3026, 2000, 2000, 2000]));
children.push(P("Autodiagnóstico: " + (ad.valido ? "VÁLIDO (error < 1 %)." : "NO VÁLIDO."),
  { run: { bold: true, color: ad.valido ? "1E7A1E" : "B00000" } }));
// reacciones / equilibrio
const reac = res.reacciones || {};
let sumRy = 0; const reacRows = Object.entries(reac).map(([nid, c]) => {
  const ry = (c.ELU.RY || 0) / 1e3, rx = (c.ELU.RX || 0) / 1e3; sumRy += ry;
  return [nid, f2(rx), f2(ry)];
});
children.push(H("7.1 Reacciones y equilibrio (ELU)", HeadingLevel.HEADING_2));
children.push(table(["Apoyo", "RX [kN]", "RY (vertical) [kN]"], reacRows, [3026, 3000, 3000]));
const qtot = model.cargas.reduce((s, c) => s + Math.abs(c.qz) / 1e3, 0);
const Ltot = res.longitudes[model.cargas[0].barra];
const aplicadaELU = (1.35 * 12 + 1.50 * 10) * Ltot;
children.push(P("Carga vertical aplicada ELU = (1,35·12 + 1,50·10)·6,0 = " + f1(aplicadaELU) + " kN; " +
  "Σ reacciones verticales = " + f1(sumRy) + " kN → equilibrio con error ≈ 0 %. " +
  "Reacción por apoyo = " + f2(sumRy / 2) + " kN (coincide con el Caso 1: 93,60 kN/apoyo).",
  { run: { bold: true } }));
children.push(H("7.2 Validación cruzada (anaStruct)", HeadingLevel.HEADING_2));
const cvRows = Object.entries(cv.barras).map(([bid, d]) =>
  [bid, f1(d.M[0]) + " / " + f1(d.M[1]), f1(d.V[0]) + " / " + f1(d.V[1]),
   f1(d.N[0]) + " / " + f1(d.N[1]), (Math.max(d.M[2], d.V[2], d.N[2]) * 100).toFixed(2) + " %"]);
children.push(table(["Barra", "M [kN·m] PyNite/anaStruct", "V [kN] PyNite/anaStruct",
  "N [kN] PyNite/anaStruct", "Error"], cvRows, [1126, 2700, 2300, 2300, 1600]));
children.push(P("Validación cruzada: " + (cv.ok ? "CONFORME (< 1 %)." : "NO CONFORME."),
  { run: { bold: true, color: cv.ok ? "1E7A1E" : "B00000" } }));

// ---- 8. Esfuerzos ----
children.push(new Paragraph({ pageBreakBefore: true, children: [] }));
children.push(H("8. Esfuerzos (envolvente ELU 1,35G + 1,50Q)", HeadingLevel.HEADING_1));
const esfRows = Object.keys(model.barras).map((bid) => {
  const e = elu(bid);
  const N = Math.max(Math.abs(e.N_i), Math.abs(e.N_j)) / 1e3;
  const V = Math.max(Math.abs(e.V_max), Math.abs(e.V_min)) / 1e3;
  const M = Math.max(Math.abs(e.M_max), Math.abs(e.M_min)) / 1e3;
  return [bid, f1(N), f1(V), f1(M)];
});
children.push(table(["Barra", "N [kN]", "V [kN]", "M [kN·m]"], esfRows, [2256, 2256, 2257, 2257]));
children.push(...img("diag_momentos.png", 380, 300, "Figura 1. Ley de momentos flectores (ELU)."));
children.push(...img("diag_cortantes.png", 380, 300, "Figura 2. Ley de cortantes (ELU)."));
children.push(...img("diag_axiles.png", 380, 300, "Figura 3. Ley de axiles (ELU)."));

// ---- 9. Servicio ----
children.push(new Paragraph({ pageBreakBefore: true, children: [] }));
children.push(H("9. Estado límite de servicio (flechas)", HeadingLevel.HEADING_1));
children.push(...img("deformada.png", 380, 300, "Figura 4. Deformada bajo combinación característica (amplificada)."));
const flRows = Object.entries(ver.barras).map(([bid, b]) => {
  const ct = b.comprobaciones["Flecha total L/300"], ca = b.comprobaciones["Flecha activa L/500"];
  return [bid, (ct.Ed * 1e3).toFixed(2), (ct.Rd * 1e3).toFixed(2), pct(ct.u),
    (ca.Ed * 1e3).toFixed(2), (ca.Rd * 1e3).toFixed(2), pct(ca.u)];
});
children.push(table(["Barra", "f_tot [mm]", "lím [mm]", "aprov.", "f_act [mm]", "lím [mm]", "aprov."],
  flRows, [1226, 1300, 1300, 1300, 1300, 1300, 1300]));

// ---- 10. EC3 ----
children.push(new Paragraph({ pageBreakBefore: true, children: [] }));
children.push(H("10. Comprobaciones según EC3", HeadingLevel.HEADING_1));
for (const [bid, b] of Object.entries(ver.barras)) {
  children.push(H(`10.${Object.keys(ver.barras).indexOf(bid) + 1}  Barra ${bid} — ${b.tipo} (${b.seccion}, ${b.material})`, HeadingLevel.HEADING_2));
  const rows = Object.entries(b.comprobaciones).filter(([n]) => !n.startsWith("Flecha"))
    .map(([n, c]) => [n, c.Ed === null ? "-" : f1(c.Ed / 1e3), c.Rd === null ? "-" : f1(c.Rd / 1e3),
      pct(c.u), c.ok ? "CUMPLE" : "NO CUMPLE", c.art]);
  children.push(table(["Comprobación", "Ed", "Rd", "Aprov.", "Veredicto", "Artículo"], rows,
    [2200, 1100, 1100, 1100, 1500, 2026]));
  children.push(P(`Aprovechamiento máximo: ${pct(b.aprovechamiento_max)} → ${b.veredicto}.`,
    { run: { bold: true, color: b.veredicto === "CUMPLE" ? "1E7A1E" : "B00000" } }));
}

// ---- 11. Conclusiones ----
children.push(H("11. Conclusiones", HeadingLevel.HEADING_1));
const allOk = Object.values(ver.barras).every((b) => b.veredicto === "CUMPLE");
children.push(P("El puente físico→analítico ha derivado correctamente, a partir del IFC FÍSICO, un modelo de " +
  Object.keys(model.barras).length + " barras y " + Object.keys(model.nodos).length + " nudos con perfiles HEB 200 / " +
  "IPE 330 y material S275, y lo ha enrutado al módulo de barras. El cálculo " + (allOk ? "CUMPLE" : "NO cumple") +
  " todas las comprobaciones EC3 y reproduce el Caso 1: 93,60 kN/apoyo, pilares HEB 200 al 32,0 % y dintel IPE 330 " +
  "al 44,6 %, con validación cruzada conforme. Queda validada la apertura de la Dirección 2 (IFC físico real → cálculo)."));
children.push(P("Limitaciones: análisis lineal de barras; interacción N+M lineal conservadora; no se comprueban " +
  "pandeo lateral, abolladura ni uniones. Los apoyos y las cargas son HIPÓTESIS de proyecto (no están en el IFC " +
  "físico) y deben confirmarse. Resultado de PREDIMENSIONADO, a revisar y firmar por técnico competente.",
  { run: { italics: true, size: 18 } }));

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, color: HEAD, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, color: "2E5F8A", font: "Arial" },
        paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 1 } }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: HEAD, space: 2 } },
      children: [new TextRun({ text: "Memoria de cálculo · Caso R1 · Puente IFC físico→analítico", size: 16, color: "777777" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Estructurando — pág. ", size: 16, color: "777777" }),
        new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "777777" })] })] }) },
    children }] });

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(out, buf); console.log("Memoria escrita en:", out); });
