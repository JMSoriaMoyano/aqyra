import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { IfcMeshData } from "./ifc-loader.js";
import { dataStateStyle, type DataState } from "./data-state.js";

export interface PickInfo {
  modelID: number;
  expressId: number;
  ifcType: string;
}

/**
 * Convenio Z-up de la ingesta (paso 1). web-ifc entrega la geometria en su marco
 * Y-up (swap IFC (x,y,z) -> (x, z, -y)). `aZup` DESHACE ese swap con una rotacion
 * de +90 sobre X: (x, y, z)_yup -> (x, -z, y)_ifc, devolviendo el IFC Z-up nativo.
 * Es el inverso EXACTO de m(v)=[x, z, -y] de bcf.ts (round-trip comprobado). La
 * escena aplica esta MISMA rotacion al grupo del modelo en `addIfcModel`; este
 * helper es el ancla numerica del convenio (y el que verifica el test de ingesta).
 */
export function aZup(v: [number, number, number]): [number, number, number] {
  return [v[0], -v[2], v[1]];
}

/** Angulo de la rotacion de ingesta a Z-up (+90 sobre X). */
const ZUP_ROT_X = Math.PI / 2;

/**
 * Viewer — escena 3D de Aqyra (three.js).
 *
 * F0: escena vacía. F1: carga/encuadre + órbita. F2: selección por clic con
 * resaltado y control de visibilidad/color por clase IFC. El renderer WebGL solo
 * se crea en `mount()` (instanciable sin GL en tests jsdom).
 */
export class Viewer {
  private renderer?: THREE.WebGLRenderer;
  private readonly scene = new THREE.Scene();
  private readonly camera: THREE.PerspectiveCamera;
  private readonly models = new THREE.Group();
  private readonly modelGroups = new Map<number, THREE.Group>();
  /** Capa del pre-proceso (V2): idealizado + glifos de apoyo/carga. Todo `proposal`. */
  private readonly overlay = new THREE.Group();
  /** Proxies CLICABLES de los núcleos (columna-cajón): cuadriláteros de la sección. */
  private readonly coreGroup = new THREE.Group();
  /** Gizmo de ejes XYZ (orientación); se re-dimensiona con el modelo. */
  private readonly axesGroup = new THREE.Group();
  /** Callback al clicar un núcleo (lo cablea embed). */
  onCorePick?: (coreId: string) => void;
  private readonly raycaster = new THREE.Raycaster();
  private container?: HTMLElement;
  private controls?: OrbitControls;
  private raf = 0;

  private selectedMesh?: THREE.Mesh;
  private selectedPrevEmissive = 0x000000;
  private downXY: [number, number] | null = null;

  /** Color de ACENTO de la UX (ámbar) para selección/BCF — distinto del emissive D29. */
  private readonly ACCENT = 0xff8a3d;
  /** Mallas con acento activo (para restaurar su emissive). */
  private selectionAccent: THREE.Mesh[] = [];
  /** Observa el tamaño real del contenedor (#8): el renderer sigue a `#escena`. */
  private resizeObserver?: ResizeObserver;

  /** Estado de dato (D-021) del layer de resultado activo. `null` = sin resultado a la vista. */
  private dataState: DataState | null = null;
  private stateChip?: HTMLElement;
  private stateWatermark?: HTMLElement;

  /** Callback de selección por clic (lo cablea embed). */
  onPick?: (info: PickInfo) => void;

  constructor() {
    this.camera = new THREE.PerspectiveCamera(60, 1, 0.1, 5000);
    // Convenio Z-up (paso 1): el «arriba» de la escena es +Z (marco IFC nativo),
    // no +Y. Fija el polo de orbita de OrbitControls (se crea en mount()).
    this.camera.up.set(0, 0, 1);
    this.camera.position.set(15, 15, 15);
    this.camera.lookAt(0, 0, 0);
    // Iluminación con profundidad: hemisférica (cielo claro / suelo oscuro) da el
    // gradiente que lee el volumen, + luz principal y de relleno para la forma.
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x2a3444, 0.85));
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.22));
    const key = new THREE.DirectionalLight(0xffffff, 0.75);
    key.position.set(12, 22, 8);
    this.scene.add(key);
    const fill = new THREE.DirectionalLight(0xffffff, 0.28);
    fill.position.set(-14, 6, -10);
    this.scene.add(fill);
    this.scene.add(this.models);
    this.scene.add(this.overlay);
    this.scene.add(this.coreGroup);
    this.scene.add(this.axesGroup);
  }

  // ── Pre-proceso (V2): capa idealizada + glifos (proposal) ────────────────────

  private subGroup(name: string): THREE.Group {
    let g = this.overlay.getObjectByName(name) as THREE.Group | undefined;
    if (g) {
      g.clear();
    } else {
      g = new THREE.Group();
      g.name = name;
      this.overlay.add(g);
    }
    return g;
  }

  /** Pinta el wireframe del modelo IDEALIZADO (ejes de barra). */
  setIdealization(segments: Array<{ a: [number, number, number]; b: [number, number, number] }>): void {
    const g = this.subGroup("ideal");
    if (!segments.length) return;
    const pos = new Float32Array(segments.length * 6);
    segments.forEach((s, i) => {
      pos.set([s.a[0], s.a[1], s.a[2], s.b[0], s.b[1], s.b[2]], i * 6);
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    // depthTest:false + renderOrder alto ⇒ el idealizado se dibuja SIEMPRE por
    // encima del físico (si no, las líneas quedan ocultas dentro de los sólidos).
    const mat = new THREE.LineBasicMaterial({ color: 0x18e0ff, depthTest: false, transparent: true });
    const line = new THREE.LineSegments(geo, mat);
    line.renderOrder = 999;
    g.add(line);
  }

  /** Glifos de NUDO: puntos destacados (tamaño fijo en pantalla, por encima de todo). */
  setNodeGlyphs(points: Array<[number, number, number]>): void {
    const g = this.subGroup("nodes");
    if (!points.length) return;
    const pos = new Float32Array(points.length * 3);
    points.forEach((p, i) => pos.set([p[0], p[1], p[2]], i * 3));
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    const mat = new THREE.PointsMaterial({
      color: 0xffffff,
      size: 5,
      sizeAttenuation: false, // tamaño constante en píxeles ⇒ los nudos siempre se ven
      depthTest: false,
      transparent: true,
    });
    const pts = new THREE.Points(geo, mat);
    pts.renderOrder = 1001;
    g.add(pts);
  }

  /** Glifos de apoyo (cubo en el nudo coaccionado). */
  setSupportGlyphs(points: Array<[number, number, number]>): void {
    const g = this.subGroup("supports");
    const size = this.glyphSize();
    const geo = new THREE.BoxGeometry(size, size, size);
    const mat = new THREE.MeshBasicMaterial({ color: 0xffcc33, depthTest: false, transparent: true });
    for (const p of points) {
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(p[0], p[1], p[2]);
      mesh.renderOrder = 1000;
      g.add(mesh);
    }
  }

  /** Glifos de carga (flecha desde el punto/centro del miembro en la dirección dada). */
  setLoadGlyphs(arrows: Array<{ at: [number, number, number]; dir: [number, number, number] }>): void {
    const g = this.subGroup("loads");
    const len = this.glyphSize() * 4;
    for (const a of arrows) {
      const dir = new THREE.Vector3(a.dir[0], a.dir[1], a.dir[2]);
      if (dir.lengthSq() === 0) continue;
      dir.normalize();
      // La flecha apunta HACIA el punto de aplicación (origen retranqueado).
      const origin = new THREE.Vector3(a.at[0], a.at[1], a.at[2]).addScaledVector(dir, -len);
      const arrow = new THREE.ArrowHelper(dir, origin, len, 0xff5544, len * 0.3, len * 0.18);
      arrow.renderOrder = 1000;
      (arrow.line.material as THREE.LineBasicMaterial).depthTest = false;
      (arrow.cone.material as THREE.MeshBasicMaterial).depthTest = false;
      g.add(arrow);
    }
  }

  /** Glifos de SUPERFICIE: diafragma (contorno verde + nudo maestro) y lámina (malla naranja). */
  setSurfaceGlyphs(
    surfaces: Array<{
      kind: string;
      outline: Array<[number, number, number]>;
      center: [number, number, number];
      mesh?: { nodes: Array<[number, number, number]>; quads: Array<[number, number, number, number]> };
      planar?: boolean;
      thick?: boolean;
      skewed?: boolean;
      group?: string;
      groupClosed?: boolean;
    }>,
  ): void {
    const g = this.subGroup("surfaces");
    if (!surfaces.length) return;
    const dia: number[] = [];
    const shell: number[] = [];
    const warn: number[] = []; // contornos de superficies NO planas (caja/núcleo) → rojo
    const grpC: number[] = []; // contornos de caras de núcleo CERRADO reconocido
    const grpO: number[] = []; // contornos de caras de núcleo ABIERTO (U/L)
    const thk: number[] = []; // contornos de superficies GRUESAS (lámina delgada no aplica)
    const skw: number[] = []; // contornos de muros TORCIDOS (artefacto de derivación)
    const masters: number[] = [];
    for (const s of surfaces) {
      if (s.planar === false) {
        const o = s.outline;
        for (let k = 0; k < o.length; k++) {
          const a = o[k];
          const b = o[(k + 1) % o.length];
          warn.push(a[0], a[1], a[2], b[0], b[1], b[2]);
        }
        continue; // no se dibuja como lámina/diafragma: requiere descomposición
      }
      if (s.kind === "shell" && s.mesh) {
        for (const q of s.mesh.quads) {
          for (let k = 0; k < 4; k++) {
            const a = s.mesh.nodes[q[k]];
            const b = s.mesh.nodes[q[(k + 1) % 4]];
            shell.push(a[0], a[1], a[2], b[0], b[1], b[2]);
          }
        }
      } else {
        const o = s.outline;
        for (let k = 0; k < o.length; k++) {
          const a = o[k];
          const b = o[(k + 1) % o.length];
          dia.push(a[0], a[1], a[2], b[0], b[1], b[2]);
        }
        masters.push(s.center[0], s.center[1], s.center[2]);
      }
      // Núcleo reconocido por caras: resalta el contorno (cerrado=teal, abierto=ámbar).
      if (s.group) {
        const arr = s.groupClosed ? grpC : grpO;
        const o = s.outline;
        for (let k = 0; k < o.length; k++) {
          const a = o[k];
          const b = o[(k + 1) % o.length];
          arr.push(a[0], a[1], a[2], b[0], b[1], b[2]);
        }
      }
      // GRUESO (Indicación C): resalta el contorno en rosa (lámina delgada no aplica).
      if (s.thick) {
        const o = s.outline;
        for (let k = 0; k < o.length; k++) {
          const a = o[k];
          const b = o[(k + 1) % o.length];
          thk.push(a[0], a[1], a[2], b[0], b[1], b[2]);
        }
      }
      // TORCIDO (Indicación C): muro ladeado → artefacto, contorno en rojo puro.
      if (s.skewed) {
        const o = s.outline;
        for (let k = 0; k < o.length; k++) {
          const a = o[k];
          const b = o[(k + 1) % o.length];
          skw.push(a[0], a[1], a[2], b[0], b[1], b[2]);
        }
      }
    }
    const addLines = (arr: number[], color: number): void => {
      if (!arr.length) return;
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(arr), 3));
      const m = new THREE.LineSegments(geo, new THREE.LineBasicMaterial({ color, depthTest: false, transparent: true }));
      m.renderOrder = 997;
      g.add(m);
    };
    addLines(dia, 0x66ff99); // diafragma → verde
    addLines(shell, 0xffaa55); // lámina → naranja
    addLines(warn, 0xff3344); // no-plano (caja/núcleo) → rojo (necesita descomposición)
    addLines(grpC, 0x33ffe0); // núcleo CERRADO reconocido por caras → teal
    addLines(grpO, 0xffd23a); // núcleo ABIERTO (U/L) reconocido → ámbar
    addLines(thk, 0xff5fd0); // GRUESO: lámina delgada no aplica → rosa (Indicación C)
    addLines(skw, 0xff0000); // TORCIDO: artefacto de derivación → rojo puro (Indicación C)
    if (masters.length) {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(masters), 3));
      const pts = new THREE.Points(geo, new THREE.PointsMaterial({ color: 0x66ff99, size: 9, sizeAttenuation: false, depthTest: false, transparent: true }));
      pts.renderOrder = 1002;
      g.add(pts);
    }
  }

  /** Glifos de COLUMNA-CAJÓN: eje vertical + contorno de sección (magenta) + proxy clicable. */
  setCoreGlyphs(cores: Array<{ id: string; axis: { a: [number, number, number]; b: [number, number, number] }; sectionOutline: Array<[number, number, number]> }>): void {
    const g = this.subGroup("cores");
    this.coreGroup.clear();
    if (!cores.length) return;
    const seg: number[] = [];
    for (const c of cores) {
      seg.push(c.axis.a[0], c.axis.a[1], c.axis.a[2], c.axis.b[0], c.axis.b[1], c.axis.b[2]);
      const o = c.sectionOutline;
      for (let k = 0; k < o.length; k++) {
        const a = o[k];
        const b = o[(k + 1) % o.length];
        seg.push(a[0], a[1], a[2], b[0], b[1], b[2]);
      }
      // Proxy CLICABLE: caja envolvente de TODO el núcleo (fácil de acertar), casi invisible.
      let minx = Infinity, miny = Infinity, minz = Infinity, maxx = -Infinity, maxy = -Infinity, maxz = -Infinity;
      const acc = (p: [number, number, number]): void => {
        minx = Math.min(minx, p[0]); maxx = Math.max(maxx, p[0]);
        miny = Math.min(miny, p[1]); maxy = Math.max(maxy, p[1]);
        minz = Math.min(minz, p[2]); maxz = Math.max(maxz, p[2]);
      };
      for (const p of o) acc(p);
      acc(c.axis.a);
      acc(c.axis.b);
      const sx = Math.max(maxx - minx, 0.1), sy = Math.max(maxy - miny, 0.1), sz = Math.max(maxz - minz, 0.1);
      const box = new THREE.Mesh(
        new THREE.BoxGeometry(sx, sy, sz),
        new THREE.MeshBasicMaterial({ color: 0xcc66ff, transparent: true, opacity: 0.06, depthWrite: false }),
      );
      box.position.set((minx + maxx) / 2, (miny + maxy) / 2, (minz + maxz) / 2);
      box.userData = { coreId: c.id };
      this.coreGroup.add(box);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(seg), 3));
    const m = new THREE.LineSegments(geo, new THREE.LineBasicMaterial({ color: 0xcc66ff, depthTest: false, transparent: true }));
    m.renderOrder = 1003;
    g.add(m);
  }

  /** Malla shell COSIDA de los núcleos (4 láminas conectadas): cerrado=teal, abierto=ámbar. */
  setCoreShellGlyphs(groups: Array<{ closed: boolean; mesh?: { nodes: Array<[number, number, number]>; quads: Array<[number, number, number, number]> } }>): void {
    const g = this.subGroup("coreshell");
    if (!groups.length) return;
    const tealArr: number[] = [];
    const amberArr: number[] = [];
    for (const grp of groups) {
      if (!grp.mesh) continue;
      const arr = grp.closed ? tealArr : amberArr;
      for (const q of grp.mesh.quads) {
        for (let k = 0; k < 4; k++) {
          const a = grp.mesh.nodes[q[k]];
          const b = grp.mesh.nodes[q[(k + 1) % 4]];
          arr.push(a[0], a[1], a[2], b[0], b[1], b[2]);
        }
      }
    }
    const draw = (arr: number[], color: number): void => {
      if (!arr.length) return;
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(arr), 3));
      const m = new THREE.LineSegments(geo, new THREE.LineBasicMaterial({ color, depthTest: false, transparent: true }));
      m.renderOrder = 1004;
      g.add(m);
    };
    draw(tealArr, 0x33ffe0);
    draw(amberArr, 0xffd23a);
  }

  /** Pinta la DEFORMADA coloreada por aprovechamiento (post-proceso V3). Cada
   * segmento lleva su color (rampa de aprovechamiento). Capa propia, sobre todo. */
  setDeformed(segments: Array<{ a: [number, number, number]; b: [number, number, number]; color: [number, number, number] }>): void {
    const g = this.subGroup("deformed");
    if (!segments.length) return;
    const pos = new Float32Array(segments.length * 6);
    const col = new Float32Array(segments.length * 6);
    segments.forEach((s, i) => {
      pos.set([s.a[0], s.a[1], s.a[2], s.b[0], s.b[1], s.b[2]], i * 6);
      col.set([s.color[0], s.color[1], s.color[2], s.color[0], s.color[1], s.color[2]], i * 6);
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
    const mat = new THREE.LineBasicMaterial({ vertexColors: true, depthTest: false, transparent: true });
    const line = new THREE.LineSegments(geo, mat);
    line.renderOrder = 1005;
    g.add(line);
  }

  /** Limpia la capa de deformada (post-proceso). */
  clearDeformed(): void {
    const g = this.overlay.getObjectByName("deformed") as THREE.Group | undefined;
    g?.clear();
  }

  /** Atenúa (fantasma) o restaura el modelo FÍSICO, para que el idealizado se lea. */
  ghostPhysical(on: boolean): void {
    this.eachMesh((m) => {
      const mat = m.material as THREE.MeshLambertMaterial;
      if (on) {
        mat.transparent = true;
        mat.opacity = 0.1;
        mat.depthWrite = false;
      } else {
        const o = (m.userData.opacity0 as number) ?? 1;
        mat.opacity = o;
        mat.transparent = o < 1;
        mat.depthWrite = true;
      }
    });
  }

  /** Tamaño de glifo proporcional al modelo. */
  private glyphSize(): number {
    const box = new THREE.Box3().setFromObject(this.models);
    if (box.isEmpty()) return 0.2;
    const s = box.getSize(new THREE.Vector3());
    return Math.max(0.1, Math.max(s.x, s.y, s.z) * 0.01);
  }

  /** Limpia toda la capa de pre-proceso. */
  clearOverlay(): void {
    this.overlay.clear();
  }

  // ── Estado de dato (D-021): chip + marca de agua sobre el canvas ─────────────

  /** Crea el chip de estado y la marca de agua «NO VERIFICADO» en el contenedor. */
  private buildStateOverlay(container: HTMLElement): void {
    if (container.style.position === "" || container.style.position === "static") {
      container.style.position = "relative";
    }
    const chip = document.createElement("div");
    chip.setAttribute("data-aqyra", "state-chip");
    chip.style.cssText =
      "position:absolute;top:10px;left:10px;z-index:30;font:600 12px/1 system-ui,sans-serif;color:#fff;padding:6px 10px;border-radius:6px;box-shadow:0 1px 6px rgba(0,0,0,.4);pointer-events:none;display:none;letter-spacing:.02em;";
    const watermark = document.createElement("div");
    watermark.setAttribute("data-aqyra", "state-watermark");
    // Marca «NO VERIFICADO» MUY tenue y espaciada: presente como guarda (no pasa por
    // certificado en capturas) pero discreta, no captura eventos.
    watermark.style.cssText =
      "position:absolute;inset:0;z-index:20;pointer-events:none;display:none;overflow:hidden;" +
      "color:rgba(180,60,70,.06);font:600 11px/9 system-ui,sans-serif;white-space:pre;text-align:center;transform:rotate(-22deg);letter-spacing:.35em;";
    container.appendChild(watermark);
    container.appendChild(chip);
    this.stateChip = chip;
    this.stateWatermark = watermark;
    this.applyDataState();
  }

  /** Fija el estado de dato del resultado a la vista (`null` = sin resultado). */
  setDataState(state: DataState | null): void {
    this.dataState = state;
    this.applyDataState();
  }

  /** Estado de dato actual del layer de resultado a la vista. */
  getDataState(): DataState | null {
    return this.dataState;
  }

  /** Aplica el estado al chip y la marca de agua. El trato certificado (limpio,
   * sin marca) SOLO se da si el estilo lo marca como certificado (verified-signed). */
  private applyDataState(): void {
    const chip = this.stateChip;
    const wm = this.stateWatermark;
    if (!chip || !wm) return;
    if (this.dataState === null) {
      chip.style.display = "none";
      wm.style.display = "none";
      return;
    }
    const s = dataStateStyle(this.dataState);
    chip.textContent = s.label;
    chip.style.background = s.color;
    chip.style.display = "block";
    // La marca de agua solo se retira con el trato certificado (verified-signed).
    if (s.watermark && !s.certified) {
      wm.textContent = ("NO VERIFICADO          ".repeat(3) + "\n").repeat(7);
      wm.style.display = "block";
    } else {
      wm.style.display = "none";
    }
  }

  mount(container: HTMLElement): void {
    if (this.renderer) return;
    this.container = container;
    this.buildStateOverlay(container);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth || 1, container.clientHeight || 1);
    renderer.setClearColor(0x0e1116, 1);
    container.appendChild(renderer.domElement);
    this.renderer = renderer;
    const controls = new OrbitControls(this.camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.zoomToCursor = true;
    controls.screenSpacePanning = true;
    controls.enableRotate = true;
    controls.enablePan = true;
    controls.enableZoom = true;
    // Izquierdo = girar · rueda = zoom · rueda pulsada o derecho = mano (pan)
    controls.mouseButtons = {
      LEFT: THREE.MOUSE.ROTATE,
      MIDDLE: THREE.MOUSE.PAN,
      RIGHT: THREE.MOUSE.PAN,
    };
    this.controls = controls;
    renderer.domElement.addEventListener("pointerdown", this.onPointerDown);
    renderer.domElement.addEventListener("pointerup", this.onPointerUp);
    this.resize();
    // #8 — el renderer sigue el tamaño REAL del contenedor (antes quedaba fijo tras mount).
    if (typeof ResizeObserver !== "undefined") {
      this.resizeObserver = new ResizeObserver(() => this.resize());
      this.resizeObserver.observe(container);
    }
    if (typeof window !== "undefined") window.addEventListener("resize", this.onWindowResize);
    this.animate();
  }

  /** Construye y añade la malla de un modelo IFC; etiqueta y encuadra. */
  addIfcModel(modelID: number, meshes: IfcMeshData[]): void {
    const group = new THREE.Group();
    // Convenio Z-up (paso 1): deshace el swap Y-up de web-ifc rotando +90 sobre X.
    // Equivale a aplicar `aZup` a cada vertice del modelo (mismo mapeo (x,y,z)->(x,-z,y)),
    // dejando la escena en el Z-up nativo del IFC.
    group.rotation.x = ZUP_ROT_X;
    for (const md of meshes) {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(md.positions, 3));
      geo.setAttribute("normal", new THREE.BufferAttribute(md.normals, 3));
      geo.setIndex(new THREE.BufferAttribute(md.indices, 1));
      const mat = new THREE.MeshLambertMaterial({
        color: new THREE.Color(md.color.r, md.color.g, md.color.b),
        transparent: md.color.a < 1,
        opacity: md.color.a,
        side: THREE.DoubleSide,
      });
      const mesh = new THREE.Mesh(geo, mat);
      const world = new THREE.Matrix4().fromArray(md.matrix);
      mesh.applyMatrix4(world);
      mesh.userData = { modelID, expressId: md.expressId, ifcType: md.ifcType, color0: { r: md.color.r, g: md.color.g, b: md.color.b }, opacity0: md.color.a };
      group.add(mesh);
      // Aristas: definen los cantos y dan profundidad al gris plano. No son `isMesh`
      // (los ignoran selección/ghost/heatmap/meshCount) y no reciben picking.
      const edges = new THREE.LineSegments(
        new THREE.EdgesGeometry(geo, 30),
        new THREE.LineBasicMaterial({ color: 0x0a0f16, transparent: true, opacity: 0.35 }),
      );
      edges.applyMatrix4(world);
      edges.raycast = () => {};
      edges.userData = { isEdge: true, modelID };
      group.add(edges);
    }
    this.modelGroups.set(modelID, group);
    this.models.add(group);
    this.fitToModels();
  }

  /** Elevación (eje Z = cota IFC en el convenio Z-up) del centro de cada elemento. */
  elementElevations(modelID: number): Map<number, number> {
    this.models.updateMatrixWorld(true);
    const group = this.modelGroups.get(modelID);
    const acc = new Map<number, { min: number; max: number }>();
    if (!group) return new Map();
    group.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      const id = m.userData.expressId as number;
      const box = new THREE.Box3().setFromObject(m);
      // Z-up (paso 1): la cota vertical es el eje Z de la escena (antes .y en Y-up).
      const a = acc.get(id) ?? { min: Infinity, max: -Infinity };
      a.min = Math.min(a.min, box.min.z);
      a.max = Math.max(a.max, box.max.z);
      acc.set(id, a);
    });
    const out = new Map<number, number>();
    for (const [id, { min, max }] of acc) out.set(id, (min + max) / 2);
    return out;
  }

  /** Tipo IFC de cada elemento de un modelo (de las mallas). */
  elementTypes(modelID: number): Map<number, string> {
    const group = this.modelGroups.get(modelID);
    const out = new Map<number, string>();
    if (!group) return out;
    group.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) out.set(m.userData.expressId as number, (m.userData.ifcType as string) ?? "OTROS");
    });
    return out;
  }

  /** Elimina las mallas de un modelo (para recargar tras saneamiento). */
  removeModel(modelID: number): void {
    const group = this.modelGroups.get(modelID);
    if (!group) return;
    this.models.remove(group);
    group.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) {
        m.geometry.dispose();
        (m.material as THREE.Material).dispose();
      }
    });
    this.modelGroups.delete(modelID);
  }

  meshCount(): number {
    let n = 0;
    this.models.traverse((o) => {
      if ((o as THREE.Mesh).isMesh) n++;
    });
    return n;
  }

  /** Clases IFC presentes con su número de mallas. */
  classes(): Array<{ ifcType: string; count: number }> {
    const counts = new Map<string, number>();
    this.eachMesh((m) => {
      const t = (m.userData.ifcType as string) ?? "OTROS";
      counts.set(t, (counts.get(t) ?? 0) + 1);
    });
    return [...counts.entries()]
      .map(([ifcType, count]) => ({ ifcType, count }))
      .sort((a, b) => a.ifcType.localeCompare(b.ifcType));
  }

  setVisibilityByClass(ifcClass: string, visible: boolean): void {
    this.eachMesh((m) => {
      if (m.userData.ifcType === ifcClass) m.visible = visible;
    });
  }

  setColorByClass(ifcClass: string, color: { r: number; g: number; b: number }): void {
    this.eachMesh((m) => {
      if (m.userData.ifcType === ifcClass) {
        const mat = m.material as THREE.MeshLambertMaterial;
        mat.color.setRGB(color.r, color.g, color.b);
      }
    });
  }

  /** Restaura el color original (web-ifc) de todas las mallas. */
  resetColors(): void {
    this.eachMesh((m) => {
      const c = m.userData.color0 as { r: number; g: number; b: number } | undefined;
      if (c) (m.material as THREE.MeshLambertMaterial).color.setRGB(c.r, c.g, c.b);
    });
  }

  /**
   * V9 · Heatmap de coste (5D): colorea cada malla por el color ya calculado (rampa de
   * `costHeatColor`) de su elemento. Las mallas sin coste (p. ej. sin partida) se atenúan a
   * gris para que el coloreado destaque. `clearCostHeatmap` = `resetColors`.
   */
  setCostHeatmap(modelID: number, colorByExpressId: Map<number, { r: number; g: number; b: number }>): void {
    this.eachMesh((m) => {
      if (m.userData.modelID !== modelID) return;
      const mat = m.material as THREE.MeshLambertMaterial;
      const c = colorByExpressId.get(m.userData.expressId as number);
      if (c) mat.color.setRGB(c.r, c.g, c.b);
      else mat.color.setRGB(0.55, 0.55, 0.58); // gris neutro: sin coste asignado
    });
  }

  /**
   * 6D · Cumplimiento: colorea cada malla por el color de su `Resultado` (D-6D-4). Mismo mecanismo
   * que el heatmap 5D (color por expressID); las mallas sin resultado se atenúan a gris. Reversible
   * con `resetColors`.
   */
  setCumplimientoColors(modelID: number, colorByExpressId: Map<number, { r: number; g: number; b: number }>): void {
    this.eachMesh((m) => {
      if (m.userData.modelID !== modelID) return;
      const mat = m.material as THREE.MeshLambertMaterial;
      const c = colorByExpressId.get(m.userData.expressId as number);
      if (c) mat.color.setRGB(c.r, c.g, c.b);
      else mat.color.setRGB(0.55, 0.55, 0.58); // gris neutro: sin resultado de cumplimiento
    });
  }

  /** Aísla las mallas de un modelo cuyo expressID esté en el conjunto. */
  isolateByExpressIds(modelID: number, ids: Set<number>): void {
    this.eachMesh((m) => {
      m.visible = m.userData.modelID === modelID && ids.has(m.userData.expressId as number);
    });
  }

  /** Hace visibles todas las mallas y restaura el físico (quita el modo fantasma). */
  showAll(): void {
    this.eachMesh((m) => {
      m.visible = true;
    });
    this.ghostPhysical(false);
  }

  /** Resalta un elemento por expressID (selección programática). */
  highlightByExpressId(modelID: number, expressId: number): void {
    this.eachMesh((m) => {
      if (m.userData.modelID === modelID && m.userData.expressId === expressId) {
        this.applyHighlight(m);
      }
    });
  }

  /** Camara del viewpoint BCF (D29 del contrato C4): posicion/direccion/up en el
   *  MARCO DEL VISOR (Y-up). Para coordenadas IFC (Z-up) del BCF, mapear antes con
   *  `bcfCameraToViewer` (bcf.ts). Adaptacion declarada del re-home (hilo 3.1). */
  setCamera(position: [number, number, number], direction: [number, number, number],
            up: [number, number, number], fovDeg?: number): void {
    this.camera.position.set(position[0], position[1], position[2]);
    this.camera.up.set(up[0], up[1], up[2]);
    const target = new THREE.Vector3(
      position[0] + direction[0], position[1] + direction[1], position[2] + direction[2]);
    if (fovDeg !== undefined) {
      this.camera.fov = fovDeg;
      this.camera.updateProjectionMatrix();
    }
    if (this.controls) {
      this.controls.target.copy(target);
      this.controls.update();
    }
    this.camera.lookAt(target);
  }

  private readonly onWindowResize = (): void => { this.resize(); };

  /** #4 · «Vista general»: quita acento/ghost y re-encuadra el modelo completo.
   *  NO altera la cámara D29 de los viewpoints BCF (es aditivo, a demanda del usuario). */
  frameAll(): void {
    this.clearSelectionAccent();
    this.showAll();
    this.fitToModels();
  }

  /** #9 · Encuadra la cámara sobre un elemento (árbol → escena). */
  frameElement(modelID: number, expressId: number): void {
    this.models.updateMatrixWorld(true);
    const box = new THREE.Box3();
    let found = false;
    this.eachMesh((m) => {
      if (m.userData.modelID === modelID && m.userData.expressId === expressId) {
        box.expandByObject(m);
        found = true;
      }
    });
    if (!found || box.isEmpty()) return;
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const radius = Math.max(size.x, size.y, size.z) || 1;
    const d = radius * 3;
    this.camera.position.set(center.x + d, center.y + d, center.z + d);
    this.camera.near = Math.max(0.01, radius / 500);
    this.camera.far = Math.max(this.camera.far, radius * 500);
    this.camera.updateProjectionMatrix();
    this.camera.lookAt(center);
    if (this.controls) {
      this.controls.target.copy(center);
      this.controls.update();
    }
  }

  /** #1/#9 · Resalta un conjunto de elementos con color de ACENTO; opcional: atenúa
   *  el resto (ghost) para que el topic BCF deje OBVIO qué señala. */
  highlightSelection(modelID: number, expressIds: number[], opts?: { ghost?: boolean; accent?: number }): void {
    const set = new Set(expressIds);
    const accent = opts?.accent ?? this.ACCENT;
    this.clearSelectionAccent();
    if (opts?.ghost) this.ghostExcept(modelID, set);
    this.eachMesh((m) => {
      if (m.userData.modelID === modelID && set.has(m.userData.expressId as number)) {
        const mat = m.material as THREE.MeshLambertMaterial;
        (m.userData as { accentPrev?: number }).accentPrev = mat.emissive.getHex();
        mat.emissive.setHex(accent);
        this.selectionAccent.push(m);
      }
    });
  }

  /** Restaura el emissive de las mallas con acento. */
  clearSelectionAccent(): void {
    for (const m of this.selectionAccent) {
      const mat = m.material as THREE.MeshLambertMaterial;
      const prev = (m.userData as { accentPrev?: number }).accentPrev;
      mat.emissive.setHex(prev ?? 0x000000);
    }
    this.selectionAccent = [];
  }

  /** Atenúa (ghost) todas las mallas salvo las del conjunto `keep`. */
  private ghostExcept(modelID: number, keep: Set<number>): void {
    this.eachMesh((m) => {
      const mat = m.material as THREE.MeshLambertMaterial;
      const keepIt = m.userData.modelID === modelID && keep.has(m.userData.expressId as number);
      if (keepIt) {
        const o = (m.userData.opacity0 as number) ?? 1;
        mat.opacity = o;
        mat.transparent = o < 1;
        mat.depthWrite = true;
      } else {
        mat.transparent = true;
        mat.opacity = 0.08;
        mat.depthWrite = false;
      }
    });
  }

  private eachMesh(fn: (m: THREE.Mesh) => void): void {
    this.models.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) fn(m);
    });
  }

  private applyHighlight(mesh: THREE.Mesh): void {
    if (this.selectedMesh && this.selectedMesh !== mesh) {
      (this.selectedMesh.material as THREE.MeshLambertMaterial).emissive.setHex(
        this.selectedPrevEmissive,
      );
    }
    const mat = mesh.material as THREE.MeshLambertMaterial;
    this.selectedPrevEmissive = mat.emissive.getHex();
    mat.emissive.setHex(0x2b6cb0);
    this.selectedMesh = mesh;
  }

  private readonly onPointerDown = (e: PointerEvent): void => {
    this.downXY = [e.clientX, e.clientY];
  };

  private readonly onPointerUp = (e: PointerEvent): void => {
    if (!this.downXY) return;
    if (e.button !== 0) {
      this.downXY = null;
      return;
    }
    const dx = e.clientX - this.downXY[0];
    const dy = e.clientY - this.downXY[1];
    this.downXY = null;
    if (Math.hypot(dx, dy) > 5) return; // fue un arrastre (órbita), no un clic
    this.pickAt(e.clientX, e.clientY);
  };

  private pickAt(clientX: number, clientY: number): void {
    if (!this.renderer) return;
    const rect = this.renderer.domElement.getBoundingClientRect();
    const ndc = new THREE.Vector2(
      ((clientX - rect.left) / rect.width) * 2 - 1,
      -((clientY - rect.top) / rect.height) * 2 + 1,
    );
    this.raycaster.setFromCamera(ndc, this.camera);
    // PRIORIDAD al núcleo: si el clic cae sobre la caja de un núcleo, gana sobre el físico.
    const coreHit = this.raycaster.intersectObjects(this.coreGroup.children, true).find((h) => h.object.visible);
    if (coreHit) {
      const id = (coreHit.object.userData as { coreId?: string }).coreId;
      if (id) {
        this.onCorePick?.(id);
        return;
      }
    }
    const hits = this.raycaster.intersectObjects(this.models.children, true);
    const first = hits.find((h) => (h.object as THREE.Mesh).isMesh && h.object.visible);
    if (!first) return;
    const mesh = first.object as THREE.Mesh;
    this.applyHighlight(mesh);
    this.onPick?.(mesh.userData as PickInfo);
  }

  private fitToModels(): void {
    const box = new THREE.Box3().setFromObject(this.models);
    if (box.isEmpty()) return;
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    // Encuadre iso: media diagonal + distancia por el FOV, desde un ángulo elevado.
    // Para modelos bajos y anchos evita que la cámara caiga casi en el plano.
    const radius = 0.5 * size.length() || 1;
    const fov = THREE.MathUtils.degToRad(this.camera.fov);
    const d = (radius / Math.sin(fov / 2)) * 1.35;
    // Z-up (paso 1): vista iso elevada con la vertical en +Z (antes en +Y).
    const off = new THREE.Vector3(1, 1, 0.9).normalize();
    this.camera.position.copy(center).addScaledVector(off, d);
    this.camera.near = Math.max(0.01, radius / 500);
    this.camera.far = radius * 500;
    this.camera.updateProjectionMatrix();
    this.camera.lookAt(center);
    if (this.controls) {
      this.controls.target.copy(center);
      this.controls.update();
    }
    this.updateAxes(box);
  }

  /** Gizmo de ejes XYZ (X rojo, Y verde, Z azul) con brazos de IGUAL longitud —
   *  permite comparar visualmente la escala real en cada dirección. Se ancla en la
   *  esquina mínima del modelo. Solo con renderer (se omite en tests headless). */
  private updateAxes(box: THREE.Box3): void {
    if (!this.renderer) return;
    this.axesGroup.clear();
    const size = box.getSize(new THREE.Vector3());
    const len = 0.5 * Math.max(size.x, size.y, size.z) || 1;
    // En el CENTRO del modelo (y por encima de todo con depthTest:false) para que
    // sea siempre visible y sirva de regla de escala contra la geometría.
    const origin = box.getCenter(new THREE.Vector3());
    const axes = new THREE.AxesHelper(len);
    axes.position.copy(origin);
    (axes.material as THREE.Material).depthTest = false;
    axes.renderOrder = 998;
    this.axesGroup.add(axes);
    const label = (t: string, col: string, p: THREE.Vector3): void => {
      const c = document.createElement("canvas");
      c.width = 128; c.height = 128;
      const ctx = c.getContext("2d");
      if (!ctx) return;
      ctx.font = "bold 90px sans-serif";
      ctx.fillStyle = col; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(t, 64, 64);
      const spr = new THREE.Sprite(
        new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), depthTest: false, transparent: true }),
      );
      spr.position.copy(p);
      spr.scale.setScalar(len * 0.09);
      spr.renderOrder = 999;
      this.axesGroup.add(spr);
    };
    label("X", "#ff6a6a", origin.clone().add(new THREE.Vector3(len * 1.12, 0, 0)));
    label("Y", "#6ad86a", origin.clone().add(new THREE.Vector3(0, len * 1.12, 0)));
    label("Z", "#6a9dff", origin.clone().add(new THREE.Vector3(0, 0, len * 1.12)));
  }

  private resize(): void {
    if (!this.renderer || !this.container) return;
    const w = this.container.clientWidth || 1;
    const h = this.container.clientHeight || 1;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  private readonly animate = (): void => {
    if (!this.renderer) return;
    this.controls?.update();
    this.renderer.render(this.scene, this.camera);
    this.raf = requestAnimationFrame(this.animate);
  };

  dispose(): void {
    if (this.raf) cancelAnimationFrame(this.raf);
    this.resizeObserver?.disconnect();
    this.resizeObserver = undefined;
    if (typeof window !== "undefined") window.removeEventListener("resize", this.onWindowResize);
    this.stateChip?.remove();
    this.stateWatermark?.remove();
    this.stateChip = undefined;
    this.stateWatermark = undefined;
    this.controls?.dispose();
    this.controls = undefined;
    if (this.renderer) {
      this.renderer.domElement.removeEventListener("pointerdown", this.onPointerDown);
      this.renderer.domElement.removeEventListener("pointerup", this.onPointerUp);
      if (this.container && this.renderer.domElement.parentElement === this.container) {
        this.container.removeChild(this.renderer.domElement);
      }
      this.renderer.dispose();
      this.renderer = undefined;
    }
  }
}
