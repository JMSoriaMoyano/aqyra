import { defineConfig, loadEnv, type PluginOption } from "vite";
import { resolve } from "node:path";
import { existsSync, mkdirSync, appendFileSync, readFileSync, writeFileSync } from "node:fs";
import type { IncomingMessage } from "node:http";

/**
 * Plugin Aqyra del servidor de desarrollo. Dos cosas:
 *
 * 1) OPERADOR IA (recomendación elegida): endpoint `/__aqyra/llm` que llama a
 *    Claude (Messages API) con la clave server-side (.env, nunca en el navegador)
 *    y devuelve { reply, actions } por tool-calling. Es el cerebro real del
 *    copiloto de diseño, instantáneo y en lenguaje libre.
 *
 * 2) PUENTE A por ficheros (`/__aqyra/say|outbox|reset`): conservado para el modo
 *    "Claude en Cowork" / depuración. El skin en modo LLM usa `/__aqyra/llm`.
 *
 * Futuro anotado (no implementado aún): multi-proveedor con selector, modelo
 * LOCAL (Ollama) y BACKEND aparte. El protocolo { reply, actions } no cambia, así
 * que el visor no se toca al cambiar de motor. Ver demo/LLM.md.
 */

// Vocabulario de acciones que el LLM puede emitir (lo ejecuta el visor).
// - summary: rellena una fila del panel de estructura espacial (IFC).
// - view:    muestra una vista de la maqueta (volume|levels|grid|plan|reset).
// - space:   declara UN grupo de espacios de la planta tipo (una habitación-fila,
//            el pasillo o un núcleo). El visor lo acumula y dibuja la planta 2D.
//            "Una acción por dato": cada `space` corresponde a algo que el usuario
//            dijo; el LLM no inventa lo no dicho.
const RESPONDER_TOOL = {
  name: "responder",
  description:
    "Responde al usuario y actualiza el visor de diseño con acciones. " +
    "Usa `summary` para los nombres (proyecto/sitio/edificio), `storeys` para el nº de " +
    "plantas y su altura, `space` para declarar los espacios de la planta tipo (habitaciones, " +
    "pasillo, núcleos) y `view` para mostrar la maqueta (volumen, plantas, ejes o la PLANTA " +
    "TIPO en 2D). Con plantas + planta tipo, el visor materializa el ÁRBOL de instancias IFC " +
    "(una IfcBuildingStorey por planta; una IfcSpace por habitación/pasillo/núcleo; IfcZone privado/comunes).",
  input_schema: {
    type: "object",
    properties: {
      reply: { type: "string", description: "Mensaje para el usuario, en español, breve y claro." },
      actions: {
        type: "array",
        description: "Acciones a ejecutar en el visor (puede ir vacío).",
        items: {
          type: "object",
          properties: {
            type: { type: "string", enum: ["summary", "view", "space", "storeys", "program", "volume", "columns", "partition", "clear", "carpentry", "outline", "alignment"] },
            target: {
              type: "string",
              enum: ["cores", "corridor", "rooms", "grid", "partitions", "openings", "program", "outline", "alignment"],
              description: "Qué QUITAR (solo type=clear): cores (núcleos), corridor (pasillo), rooms (habitaciones), grid (retícula de pilares), partitions (tabiques), openings (carpintería: puertas/ventanas), program (tipología, p. ej. parking), outline (la huella poligonal → vuelve al rectángulo W×D).",
            },
            vertices: {
              type: "array",
              items: { type: "array", items: { type: "number" }, minItems: 2, maxItems: 2 },
              description: "HUELLA POLIGONAL (type=outline): lista de vértices [x,y] en metros (X=ancho desde la fachada oeste, Y=fondo desde la sur), en orden antihorario y SIN repetir el primero al cerrar. P. ej. una L de bbox 20×20 sin la esquina NE: [[0,0],[20,0],[20,10],[10,10],[10,20],[0,20]]. La envolvente (fachada=aristas, forjado/cubierta=polígono, retícula recortada) deriva de él; W×D (acción volume) se mantiene como marco. Mínimo 3 vértices.",
            },
            carp: { type: "string", enum: ["door", "window"], description: "Carpintería (type=carpentry): puerta o ventana." },
            cw: { type: "number", description: "Ancho del vano en m (type=carpentry; def. puerta 0,90 / ventana 1,20). Omitir si no lo dan." },
            ch: { type: "number", description: "Alto del vano en m (type=carpentry; def. puerta 2,10 / ventana 1,20). Omitir si no lo dan." },
            key: {
              type: "string",
              enum: ["project", "site", "building", "volume", "storeys", "spaces", "grid"],
              description: "Fila del resumen (solo para type=summary).",
            },
            value: { type: "string", description: "Valor de la fila (solo para type=summary)." },
            show: {
              type: "string",
              enum: ["volume", "levels", "grid", "plan", "reset"],
              description: "Qué mostrar en la maqueta (solo para type=view). `plan` abre la planta tipo en 2D.",
            },
            kind: {
              type: "string",
              enum: ["room", "corridor", "core"],
              description: "Tipo de espacio (solo para type=space): habitación, pasillo o núcleo.",
            },
            count: {
              type: "number",
              description: "Nº: en type=space (room: total de habitaciones por planta; core: nº de núcleos de esa orientación); en type=storeys: nº de plantas del edificio.",
            },
            width: {
              type: "number",
              description: "En type=space kind=corridor: ancho del pasillo (m). En type=volume: ANCHO del edificio (eje X, m).",
            },
            depth: {
              type: "number",
              description: "FONDO del edificio en metros (eje Y). Solo para type=volume.",
            },
            height: {
              type: "number",
              description: "En type=storeys: altura de planta a planta (m). En type=volume: ALTO TOTAL del edificio (m).",
            },
            layout: {
              type: "string",
              enum: ["both-sides", "single-side"],
              description: "Disposición de las habitaciones respecto al pasillo (solo kind=room).",
            },
            orientation: {
              type: "string",
              enum: ["N", "S", "E", "O", "NE", "NO", "SE", "SO"],
              description: "Orientación del núcleo según los cardinales del visor +Y=N/-Y=S/+X=E/-X=O (solo kind=core).",
            },
            detail: {
              type: "string",
              description: "Detalle libre del espacio, p. ej. '2 ascensores + escalera' o 'escalera' (solo type=space).",
            },
            zone: {
              type: "string",
              enum: ["privado", "comunes"],
              description: "IfcZone a la que pertenece: 'privado' (habitaciones) o 'comunes' (pasillo y núcleos). Si se omite, se deriva del kind. Solo type=space.",
            },
            generator: {
              type: "string",
              enum: ["residence-corridor", "parking-comb"],
              description: "Generador de distribución para tipologías NO residenciales (solo type=program). 'parking-comb' = aparcamiento en peine.",
            },
            bays: {
              type: "number",
              description: "Nº de plazas de aparcamiento por planta (solo type=program, parking-comb).",
            },
            aisle: {
              type: "number",
              description: "Ancho del vial de circulación en metros (solo type=program, parking-comb).",
            },
            ramps: {
              type: "array",
              items: { type: "string", enum: ["N", "S", "E", "O", "NE", "NO", "SE", "SO"] },
              description: "Extremos del edificio con rampa, p. ej. ['O','E'] para rampas en ambos extremos (solo type=program, parking-comb). El generador recorta las plazas que ocupa cada rampa.",
            },
            disposition: {
              type: "string",
              enum: ["bateria", "linea", "longitudinal"],
              description: "Disposición del aparcamiento (solo type=program, parking-comb). 'bateria' = plaza perpendicular al vial transversal (def). 'linea' = plaza en cordón. 'longitudinal' = VIALES A LO LARGO del eje largo (N-S), con bandas de plazas en batería a los lados (lo natural en una parcela larga y estrecha); usa lanes para el nº de viales. El visor decide cuántos caben según la huella y emite los ejes de vial como alineaciones.",
            },
            lanes: {
              type: "number",
              description: "Nº de viales longitudinales deseado (solo type=program, parking-comb, disposition=longitudinal). Omitir = los que quepan. El visor es la autoridad: si pides más de los que caben, coloca los que caben.",
            },
            sepX: {
              type: "number",
              description: "ATAJO uniforme: separación entre ejes de pilar en X (m), type=columns. El visor reparte ejes ANCLADOS a las dos fachadas (incluye 0 y el ancho). Usa axesX si necesitas ejes en posiciones concretas.",
            },
            sepY: {
              type: "number",
              description: "ATAJO uniforme: separación entre ejes de pilar en Y (m), type=columns. Anclado a las fachadas (incluye 0 y el fondo).",
            },
            axesX: {
              type: "array", items: { type: "number" },
              description: "EJES EXPLÍCITOS en X (m desde la fachada oeste), type=columns. Úsalo cuando el usuario alinea con líneas concretas (fachadas, borde de pasillo). Gana a sepX. P. ej. [0, 5, 10, 20].",
            },
            axesY: {
              type: "array", items: { type: "number" },
              description: "EJES EXPLÍCITOS en Y (m desde la fachada sur), type=columns. Para alinear pilares con fachada sur, borde de pasillo y fachada norte: p. ej. [0, 6.75, 15]. Gana a sepY.",
            },
            secW: {
              type: "number",
              description: "Ancho de la sección de pilar en m (solo type=columns; def. 0,40). Omitir si el usuario no lo dice.",
            },
            secD: {
              type: "number",
              description: "Canto de la sección de pilar en m (solo type=columns; def. 0,40). Omitir si el usuario no lo dice.",
            },
            x1: { type: "number", description: "Tabique (type=partition): X del inicio (m desde fachada oeste)." },
            y1: { type: "number", description: "Tabique (type=partition): Y del inicio (m desde fachada sur)." },
            x2: { type: "number", description: "Tabique (type=partition): X del fin (m)." },
            y2: { type: "number", description: "Tabique (type=partition): Y del fin (m)." },
            aliName: { type: "string", description: "Nombre de la alineación (type=alignment). P. ej. 'Eje C-001' o 'Ramal de acceso'." },
            aliWidth: { type: "number", description: "Ancho de la plataforma/calzada en m (type=alignment, ancho_ref). Informativo en este slice; omitir si no lo dan." },
            radioMin: { type: "number", description: "Radio mínimo en m para la asistencia (type=alignment). Por debajo, el visor resalta el arco en rojo. Def. 6 m (giro interior). Para carretera dalo según la velocidad de proyecto." },
            inicio: {
              type: "object",
              description: "Arranque de la directriz (type=alignment): posición y rumbo. x = m desde fachada oeste; y = m desde fachada sur; acimut_deg = rumbo en grados (0 = +X/Este, 90 = +Y/Norte, CCW).",
              properties: {
                x: { type: "number" }, y: { type: "number" }, acimut_deg: { type: "number" },
              },
              required: ["x", "y", "acimut_deg"],
            },
            planta: {
              type: "array",
              description: "Segmentos de la directriz horizontal (type=alignment), en orden. Solo RECTA y CURVA en este slice (la clotoide llega después). El visor integra desde 'inicio' y dibuja el arco REAL.",
              items: {
                type: "object",
                properties: {
                  tipo: { type: "string", enum: ["recta", "curva"], description: "recta = tramo recto; curva = arco circular." },
                  longitud: { type: "number", description: "Longitud del segmento en m (para la curva, la longitud del arco)." },
                  radio: { type: "number", description: "Radio del arco en m, CON SIGNO: + = giro a IZQUIERDA, − = a derecha (solo tipo=curva)." },
                },
                required: ["tipo", "longitud"],
              },
            },
          },
          required: ["type"],
        },
      },
    },
    required: ["reply", "actions"],
  },
};

const SYSTEM = `Eres el copiloto de diseño de Aqyra: ayudas a crear un edificio desde cero conversando, en español, con respuestas breves.
Guía al usuario por estos pasos y, a medida que te dé datos, emite acciones con la herramienta "responder":
1. EMPLAZAMIENTO: nombre del proyecto, sitio (ciudad/ref. catastral) y edificio. → summary key=project/site/building.
2. VOLUMETRÍA: ancho × fondo × alto. → emite la acción volume con width=ancho (m), depth=fondo (m), height=alto total (m). El visor redibuja la caja a esas dimensiones reales (y reescala la planta). Puedes añadir summary key=volume con el texto. IMPORTANTE: si el usuario CORRIGE las dimensiones más tarde, emite OTRA acción volume con los nuevos números para que el dibujo se actualice.
3. PLANTAS: número y separación entre plantas. → emite la acción storeys con count=nº de plantas y height=altura de piso a piso en metros (p. ej. "PB+4" → count=5; si dan altura total, divide). El visor genera una IfcBuildingStorey por planta en el árbol. Puedes añadir summary key=storeys con el texto.
4. USO y PLANTA TIPO: uso del edificio y distribución de la planta tipo. Cada espacio que el usuario describa se declara con una acción "space" y se dibuja en la planta 2D. Tras declarar la planta, emite view show=plan y resume en summary key=spaces el conteo total.
   - Habitaciones: emite space kind=room con count=nº TOTAL de habitaciones por planta y layout=both-sides si van a lado y lado de un pasillo (o single-side si a un solo lado). Cada habitación es un IfcSpace (zona privado).
   - Pasillo: emite space kind=corridor con width=ancho en metros. Es un IfcSpace de circulación (zona comunes).
   - Núcleos: emite UNA acción space kind=core por cada núcleo, con su orientation y un detail (p. ej. '2 ascensores + escalera'). Son IfcSpace de circulación (zona comunes). IMPORTANTE: coloca núcleos SOLO si el usuario los pide explícitamente; NO los añadas por iniciativa propia (aunque pienses que faltan comunicaciones verticales). Si crees que conviene uno, PREGUNTA antes; no lo coloques sin que lo pida.
5. RETÍCULA ESTRUCTURAL (pilares): si el usuario pide pilares, retícula o estructura, emite la acción columns. DOS formas:
   - Si solo da una separación ("pilares cada 6 m"), usa sepX/sepY: el visor reparte ejes uniformes ANCLADOS a las dos fachadas (el pilar de fachada SIEMPRE cae; ya no se desplaza).
   - Si el usuario ALINEA los pilares con líneas concretas (fachadas, borde del pasillo, "un eje en la fachada norte"), usa axesX/axesY = listas con las posiciones de eje en metros (p. ej. axesY=[0, 6.75, 15] para fachada sur, borde de pasillo y fachada norte). Calcula tú las coordenadas a partir de la geometría que el usuario describe; los ejes explícitos ganan a sepX/sepY.
   Opcional secW×secD = sección del pilar en m (def. 0,40×0,40, HA-30); OMÍTELA si no la dan. El visor coloca un IfcColumn en cada nudo (producto de los ejes) y lo REPITE por planta (todas menos la cubierta). Cada pilar lleva su eje lógico (p. ej. B2). Puedes añadir summary key=grid con el texto.
6. TABIQUES interiores (divisorias): si el usuario pide una división/tabique interior, emite la acción partition con la LÍNEA del tabique: x1,y1 (inicio) y x2,y2 (fin) en metros. CALCULA tú las coordenadas a partir de la geometría: si lo quiere "alineado con el eje 2" o "el eje central", usa la coordenada de ese eje (p. ej. un tabique vertical en el eje X=7 va de (7,0) a (7,fondo)); si da una línea libre, úsala. El tabique es un IfcWall interior (exterior:false), por planta, de fachada a fachada salvo que el usuario diga otra cosa. Cada partition AÑADE un tabique (se acumulan). NO confundir con el pasillo (que es un IfcSpace, acción space kind=corridor): el tabique es el MURO, el pasillo es el ESPACIO.
7. QUITAR (edición): si el usuario pide ELIMINAR/quitar/borrar algo ya colocado, emite la acción clear con target = cores | corridor | rooms | grid | partitions | openings | program. IMPORTANTE: NO digas que has eliminado algo si no has emitido la acción clear correspondiente; sin esa acción, NO se quita nada (el visor solo refleja acciones, no tu intención).
8b. HUELLA POLIGONAL (solar no rectangular): si el usuario describe un contorno que NO es un rectángulo (planta en L, en U, chaflán, lados oblicuos, "el solar tiene esta forma…"), emite la acción outline con vertices = lista de [x,y] en metros (X=ancho desde el oeste, Y=fondo desde el sur), en orden ANTIHORARIO y sin repetir el primer vértice al cerrar. Calcula tú los vértices a partir de la geometría que describa. La envolvente deriva del polígono: la FACHADA pasa a ser sus aristas, el FORJADO/CUBIERTA el polígono y la RETÍCULA se RECORTA a los pilares que caen dentro (los nudos fuera del contorno no se colocan). Mantén la acción volume (W×D = ancho×fondo) como MARCO/bbox que encuadra el polígono. Esto es SOLO la envolvente: la subdivisión de habitaciones sobre forma irregular todavía no está. Para volver al rectángulo, clear target=outline.
9. CARPINTERÍA (puertas/ventanas): si el usuario pide una puerta o ventana, emite la acción carpentry con carp = door | window y el PUNTO sobre el muro: x1,y1 en metros (el visor busca el muro que pasa por ese punto y aloja ahí el hueco). Calcula tú el punto a partir de la geometría (p. ej. "una ventana en la fachada sur en x=5" → (5,0); "una puerta en el tabique del eje 7 a media altura del fondo" → (7, fondo/2)). Opcional cw×ch = ancho×alto del vano; OMÍTELOS si no los dan (def. puerta 0,90×2,10, ventana 1,20×1,20). La puerta/ventana queda HOSTEADA por el muro (lo vacía). Si el punto no cae sobre ningún muro, el visor no la coloca: avisa y pide otro punto.

ORIENTACIÓN (importante): el visor usa cardinales fijos +Y=Norte, -Y=Sur, +X=Este, -X=Oeste. Cuando el usuario sitúe un núcleo "al S-E", "al N-O", etc., usa ese valor literal en orientation (SE, NO, NE, SO, N, S, E, O). No reinterpretes ni gires las orientaciones.

COHERENCIA DE CUENTAS (importante): mantén las cuentas que dé el usuario. Si dice 20 habitaciones a lado y lado, son 10+10. El total de espacios por planta = habitaciones + 1 pasillo + nº de núcleos. El total del edificio = espacios por planta × nº de plantas. Refleja esas cifras en summary key=spaces (p. ej. "20 hab (10+10) · pasillo 1,5 m · núcleo SE (2 asc.+esc.) · núcleo NO (esc.) = 23/planta · 115 total").

TIPOLOGÍA (planta tipo no residencial): si el edificio es un APARCAMIENTO, no uses space room/corridor/core; emite una acción program con generator=parking-comb, bays=nº de plazas por planta deseado, aisle=ancho de vial (m), ramps=lista de FACHADAS con rampa de ACCESO (sube de una planta a la siguiente; p. ej. ["N"] = rampa de acceso en la fachada norte, ["O","E"] = en ambos extremos) y, si el usuario lo indica, disposition=bateria|linea|longitudinal (batería = plaza perpendicular al vial transversal, por defecto; línea = en cordón; LONGITUDINAL = viales a lo largo del eje largo N-S con bandas de plazas en batería a los lados —lo natural en una parcela LARGA Y ESTRECHA—, con lanes=nº de viales y un sentido de circulación por vial). El visor coloca plazas y viales y, por cada fachada pedida, una RAMPA DE ACCESO (IfcRamp, losa inclinada LOCALIZADA pegada a esa fachada, recorrido = desnivel/pendiente, un tramo por salto de planta) que RECORTA las plazas que pisa; NO es una franja a lo largo de todo el edificio. La rampa NO es un IfcSpace. Monta el árbol. Para residencia sigue usando space room/corridor/core. Generadores disponibles: residence-corridor, parking-comb.

DISCIPLINA GEOMÉTRICA (importante): tú das la INTENCIÓN (cuántas plazas quiere, en qué extremos van las rampas, qué separación de ejes para los pilares); NO calcules tú la geometría ni el número final de plazas o pilares que caben: esa es la AUTORIDAD del visor según la huella real. No afirmes recuentos ni posiciones que no hayas emitido como acciones; la planta dibujada es la verdad. Si recibes un mensaje "[Visor · comprobación]" con cifras distintas a las que esperabas, son las REALES: acéptalas y corrige tu texto. Si piden una tipología o un detalle que los generadores aún no soportan, dilo con claridad en vez de fingir que lo has dibujado.

TRAZADO (alineaciones): si el usuario describe un EJE, VIAL, RAMAL, RAMPA en planta o una DIRECTRIZ por la que algo discurre (una carretera, un vial de circulación del parking, un eje de acceso), emite una acción alignment con: inicio = {x, y, acimut_deg} (arranque y rumbo: acimut 0 = Este/+X, 90 = Norte/+Y, CCW) y planta = lista ordenada de segmentos {tipo, longitud, radio}. Solo RECTA y CURVA en este slice (la clotoide y el alzado/rampa llegan después). El RADIO va con signo: + giro a izquierda, − a derecha. Opcional aliName, aliWidth (ancho de plataforma) y radioMin (radio mínimo de aviso). Tú das los segmentos (la INTENCIÓN del trazado); el visor integra la directriz, dibuja el ARCO real y avisa (en rojo) de los arcos por debajo del radio mínimo: NO certifiques el trazado, eso es de obras-lineales y lo firma técnico competente. La alineación es un IfcAlignment (objeto propio), no un espacio ni un muro.

Reglas: una sola acción por dato; no inventes datos que el usuario no haya dado, pregúntalos. La estructura espacial (proyecto, sitio, edificio, plantas, espacios, ejes) y los espacios (habitaciones/pasillo/núcleos, agrupables en IfcZone privado/comunes) son IFC; la caja de volumen es solo ayuda visual. Cuando el usuario quiera empezar de nuevo, usa view show=reset.`;

function aqyraPlugin(env: Record<string, string>): PluginOption {
  const dir = resolve(__dirname, ".aqyra");
  const inbox = resolve(dir, "inbox.jsonl");
  const outbox = resolve(dir, "outbox.json");
  const apiKey = env.ANTHROPIC_API_KEY || process.env.ANTHROPIC_API_KEY || "";
  const model = env.ANTHROPIC_MODEL || "claude-sonnet-4-6";
  const readBody = (req: IncomingMessage): Promise<string> =>
    new Promise((ok) => {
      let b = "";
      req.on("data", (c) => (b += c));
      req.on("end", () => ok(b));
    });
  return {
    name: "aqyra-plugin",
    configureServer(server) {
      mkdirSync(dir, { recursive: true });

      // ── Operador IA: el visor consulta a Claude y recibe { reply, actions } ──
      server.middlewares.use("/__aqyra/llm", (req, res, next) => {
        if (req.method !== "POST") return next();
        void readBody(req).then(async (body) => {
          res.setHeader("content-type", "application/json");
          if (!apiKey) {
            res.end(JSON.stringify({ reply: "Falta ANTHROPIC_API_KEY en publico/demo/.env (reinicia el servidor tras crearlo).", actions: [] }));
            return;
          }
          let messages: unknown = [];
          try { messages = JSON.parse(body || "{}").messages ?? []; } catch { /* ignore */ }
          try {
            const r = await fetch("https://api.anthropic.com/v1/messages", {
              method: "POST",
              headers: { "x-api-key": apiKey, "anthropic-version": "2023-06-01", "content-type": "application/json" },
              body: JSON.stringify({
                model, max_tokens: 1024, system: SYSTEM, messages,
                tools: [RESPONDER_TOOL], tool_choice: { type: "tool", name: "responder" },
              }),
            });
            const data = (await r.json()) as { content?: Array<{ type: string; name?: string; input?: unknown }>; error?: { message?: string } };
            const tool = (data.content ?? []).find((c) => c.type === "tool_use" && c.name === "responder");
            const out = tool?.input ?? { reply: data.error?.message ? "Error de la API: " + data.error.message : "(sin respuesta)", actions: [] };
            res.end(JSON.stringify(out));
          } catch (e) {
            res.end(JSON.stringify({ reply: "No pude llamar al LLM: " + String(e), actions: [] }));
          }
        });
      });

      // ── Entorno (P1·A): proxy a Catastro/CartoCiudad (CORS + el GML no se ──────
      //    surfacea directo). Reenvía y devuelve el GML/XML; el cliente normaliza
      //    a GeoJSON con `@aqyra/visor` (environment.ts). Solo fuentes oficiales.
      server.middlewares.use("/__aqyra/geo", (req, res) => {
        const u = new URL(req.url ?? "", "http://localhost");
        const src = u.searchParams.get("src") ?? "";
        const refcat = encodeURIComponent(u.searchParams.get("refcat") ?? "");
        const srs = u.searchParams.get("srs") ?? "EPSG::25831";
        const bbox = u.searchParams.get("bbox") ?? "";
        const CP = "https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx";
        const BU = "https://ovc.catastro.meh.es/INSPIRE/wfsBU.aspx";
        // Viales: WFS INSPIRE de Transportes del IGN/IDEE (tn-ro:RoadLink; urbano 1:2000).
        const TN = "https://servicios.idee.es/wfs-inspire/transportes";
        // Tesela de altura (terreny-RGB 5 m del ICGC) → binaria. Servida same-origin
        // para poder leer sus píxeles (decodificar la cota) sin tainting de canvas.
        if (src === "vt") {
          // Tesela vectorial (MVT/PBF) del ICGC (mapa-base2) → binaria, mismo origen.
          // Capa 'transportation' = viario vector (esquema OpenMapTiles).
          const z = u.searchParams.get("z"), x = u.searchParams.get("x"), y = u.searchParams.get("y");
          fetch(`https://geoserveis.icgc.cat/servei/catalunya/mapa-base2/vt/${z}/${x}/${y}.pbf`)
            .then((r) => r.arrayBuffer())
            .then((buf) => { res.setHeader("content-type", "application/x-protobuf"); res.end(Buffer.from(buf)); })
            .catch((e) => { res.statusCode = 502; res.end(String(e)); });
          return;
        }
        if (src === "elev") {
          // Cota por puntos (JSON). open-meteo (Copernicus DEM, abierto) — robusto y
          // sin teselas. NOTA: para producción, sustituir por el MDT del ICGC.
          const lats = u.searchParams.get("lats") ?? "";
          const lons = u.searchParams.get("lons") ?? "";
          fetch(`https://api.open-meteo.com/v1/elevation?latitude=${lats}&longitude=${lons}`)
            .then((r) => r.text())
            .then((t) => { res.setHeader("content-type", "application/json"); res.end(t); })
            .catch((e) => { res.statusCode = 502; res.end(JSON.stringify({ error: String(e) })); });
          return;
        }
        let upstream = "";
        if (src === "cp-parcel")
          upstream = `${CP}?service=wfs&version=2.0.0&request=getfeature&STOREDQUERY_ID=GetParcel&refcat=${refcat}&srsname=${srs}`;
        else if (src === "cp-neighbour")
          upstream = `${CP}?service=wfs&version=2.0.0&request=getfeature&STOREDQUERY_ID=GetNeighbourParcel&refcat=${refcat}&srsname=${srs}`;
        else if (src === "bu-all")
          upstream = `${BU}?service=wfs&version=2.0.0&request=getfeature&STOREDQUERY_ID=GetAllConstructionByParcel&refcat=${refcat}&srsname=${srs}`;
        else if (src === "bu-part")
          // Partes de edificio: aquí viene poblado el nº de plantas (altura).
          upstream = `${BU}?service=wfs&version=2.0.0&request=getfeature&STOREDQUERY_ID=GetBuildingPartByParcel&refcat=${refcat}&srsname=${srs}`;
        else if (src === "roads") {
          // bbox con el CRS en URN → fija el orden de ejes E-N del 25831.
          const bboxCrs = bbox ? `${bbox},urn:ogc:def:crs:${srs}` : "";
          upstream = `${TN}?service=WFS&version=2.0.0&request=GetFeature&typenames=tn-ro:RoadLink&srsname=${srs}&bbox=${bboxCrs}&count=300`;
        }
        else { res.statusCode = 400; res.end("src desconocido"); return; }
        fetch(upstream)
          .then((r) => r.text())
          .then((t) => { res.setHeader("content-type", "application/xml; charset=utf-8"); res.end(t); })
          .catch((e) => { res.setHeader("content-type", "application/xml"); res.end(`<!-- geo proxy error: ${String(e)} --><FeatureCollection/>`); });
      });

      // ── Puente A por ficheros (modo "Claude en Cowork" / depuración) ─────────
      server.middlewares.use("/__aqyra/say", (req, res, next) => {
        if (req.method !== "POST") return next();
        void readBody(req).then((b) => {
          let text = "";
          try { text = String(JSON.parse(b || "{}").text ?? ""); } catch { /* ignore */ }
          appendFileSync(inbox, JSON.stringify({ id: Date.now().toString(), ts: new Date().toISOString(), text }) + "\n");
          res.setHeader("content-type", "application/json");
          res.end(JSON.stringify({ id: Date.now().toString() }));
        });
      });
      server.middlewares.use("/__aqyra/outbox", (_req, res) => {
        res.setHeader("content-type", "application/json");
        res.end(existsSync(outbox) ? readFileSync(outbox, "utf8") : "{}");
      });
      server.middlewares.use("/__aqyra/reset", (_req, res) => {
        writeFileSync(inbox, ""); writeFileSync(outbox, "{}"); res.end("ok");
      });
    },
  };
}

// Alias a las fuentes de los paquetes del workspace: permite `vite dev` sin build.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, __dirname, "");
  return {
    plugins: [aqyraPlugin(env)],
    resolve: {
      alias: {
        "@aqyra/embed": resolve(__dirname, "../embed/src/index.ts"),
        "@aqyra/visor": resolve(__dirname, "../visor/src/index.ts"),
        "@aqyra/openbim": resolve(__dirname, "../openbim/src/index.ts"),
      },
    },
  };
});
