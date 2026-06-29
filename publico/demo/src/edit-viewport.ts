/**
 * Pieza 2 del Hito 2 (modo edición) — VIEWPORT THREE de manipulación directa.
 *
 * Decisión JM (slice): renderer del viewport de manipulación = **Three híbrido** (Three
 * para el 3D editable; SVG sigue para la planta 2D). El gesto NO toca geometría suelta:
 * produce un OVERRIDE `{dx,dy,rotDeg}` que se escribe en `BuildingInput.overrides` y dispara
 * un rebuild → un gesto, misma salida con cualquier renderer (la capa de datos es la verdad).
 * TODA la matemática vive en el núcleo GOLDEN-VERDE de `model.ts`; aquí solo escena/picking/gizmo.
 *
 * ── Convención de ejes ───────────────────────────────────────────────────────────
 * Plano de Aqyra: X = ancho, Y = fondo, Z = altura. Three es Y-up. Mapeo:
 *   plan (x, y, z)  →  three (x, z, y)      [planX→threeX · planY→threeZ · alturaZ→threeY]
 * El giro de edición es sobre el eje VERTICAL (threeY); en plano = `rotDeg` CCW.
 * Nota r0.169: `TransformControls` ya NO es `Object3D` → se añade `control.getHelper()`
 * a la escena (no el control). GL solo en `mount()` (instanciable sin WebGL en jsdom).
 */

import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { TransformControls } from "three/examples/jsm/controls/TransformControls.js";
import {
  buildModel,
  type BuildingInput, type ElementInstance, type Placement, type ElementOverride,
} from "./model";
import type { PlanContext } from "./generators";

/** plan (x,y,z) → three (x,z,y). */
const toThree = (x: number, y: number, z: number): THREE.Vector3 => new THREE.Vector3(x, z, y);

/** Clases editables en v1 (familias con identidad propia; el slice de JM). Los atados a
 *  un driver (pilar=nudo, fachada=arista) NO se editan aquí: chocan con el generador. */
const EDITABLE = new Set(["IfcRamp", "IfcDoor", "IfcWindow", "IfcStair"]);

/** Centroide en planta de un placement (mismo criterio que `model.placementCentroid`). */
export function planCentroid(pl: Placement): [number, number] {
  if (pl.kind === "point") return [pl.x, pl.y];
  if (pl.kind === "line") return [(pl.start[0] + pl.end[0]) / 2, (pl.start[1] + pl.end[1]) / 2];
  let sx = 0, sy = 0; for (const [x, y] of pl.contour) { sx += x; sy += y; }
  const n = pl.contour.length || 1; return [sx / n, sy / n];
}

/** Construye la geometría de UN elemento como mini-grupo anclado en su centroide (planta),
 *  para que el gizmo lo gire/mueva sobre su propio origen (= pivote del override). */
function elementObject(e: ElementInstance, ff: number): THREE.Object3D {
  const g = new THREE.Group();
  g.name = e.code;
  const [cx, cy] = planCentroid(e.placement);
  const z0 = e.storeyIndex * ff;
  const mat = new THREE.MeshStandardMaterial({ color: 0xe0a23a, transparent: true, opacity: 0.6 });
  if (e.placement.kind === "line") {
    const [ax, ay] = e.placement.start, [bx, by] = e.placement.end;
    const len = Math.hypot(bx - ax, by - ay) || 0.1;
    const box = new THREE.Mesh(new THREE.BoxGeometry(len, (e.height ?? ff) * 0.06 + 0.1, e.width ?? 0.9), mat);
    box.position.copy(toThree(0, 0, (e.height ?? ff) / 2));
    box.rotation.y = -Math.atan2(by - ay, bx - ax); // orienta la caja a lo largo de la línea
    g.add(box);
  } else if (e.placement.kind === "point") {
    const col = new THREE.Mesh(new THREE.BoxGeometry(e.section?.w ?? 0.4, ff, e.section?.d ?? 0.4), mat);
    col.position.copy(toThree(0, 0, ff / 2));
    g.add(col);
  } else {
    const shape = new THREE.Shape(e.placement.contour.map(([x, y]) => new THREE.Vector2(x - cx, y - cy)));
    const slab = new THREE.Mesh(new THREE.ShapeGeometry(shape), mat);
    slab.rotation.x = Math.PI / 2; // del plano XY de la shape al plano del suelo (XZ)
    g.add(slab);
  }
  g.position.copy(toThree(cx, cy, z0)); // ancla en el centroide → pivote de giro
  return g;
}

export interface EditViewportOptions {
  /** Se invoca al SOLTAR el gizmo: el override del antes/después por código. */
  onOverride: (code: string, ov: ElementOverride) => void;
  /** Modelo (datos): de aquí salen los placements BASE. */
  input: BuildingInput;
  ctx: PlanContext;
  ff: number; // altura de planta (m)
}

/**
 * Viewport de manipulación. GL solo se crea en `mount()` (instanciable sin WebGL en
 * tests jsdom, igual que `visor/src/viewer.ts`). El picking selecciona un elemento
 * editable; el gizmo lo transforma; al soltar, emite el override.
 */
export class EditViewport {
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(60, 1, 0.1, 5000);
  private readonly group = new THREE.Group();
  private readonly raycaster = new THREE.Raycaster();
  private renderer?: THREE.WebGLRenderer;
  private orbit?: OrbitControls;
  private gizmo?: TransformControls;
  private base = new Map<string, Placement>(); // code → placement BASE (sin override)
  private picked?: THREE.Object3D;

  constructor(private readonly opts: EditViewportOptions) {
    this.camera.position.set(20, 20, 20);
    this.camera.lookAt(0, 0, 0);
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.8));
    const dir = new THREE.DirectionalLight(0xffffff, 0.7); dir.position.set(10, 20, 10);
    this.scene.add(dir, this.group);
    this.rebuildScene();
  }

  /** Reconstruye los objetos editables desde el modelo (datos) y cachea los placements base. */
  rebuildScene(): void {
    this.group.clear();
    this.base.clear();
    const m = buildModel(this.opts.input, this.opts.ctx);
    for (const st of m.storeys) for (const e of st.elements) {
      if (!EDITABLE.has(e.ifcClass)) continue;
      this.base.set(e.code, e.placement);
      this.group.add(elementObject(e, this.opts.ff));
    }
  }

  /** Crea el renderer WebGL y cablea órbita + gizmo + picking. Solo en navegador. */
  mount(container: HTMLElement): void {
    const r = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    r.setSize(container.clientWidth || 600, container.clientHeight || 420);
    this.camera.aspect = (container.clientWidth || 600) / (container.clientHeight || 420);
    this.camera.updateProjectionMatrix();
    container.appendChild(r.domElement);
    this.renderer = r;

    this.orbit = new OrbitControls(this.camera, r.domElement);

    const gz = new TransformControls(this.camera, r.domElement);
    gz.setMode("translate");      // 'translate' | 'rotate' (toggle desde la UI)
    gz.setSpace("world");
    gz.showY = false;             // edición en planta: traslación XZ (no vertical, z diferida)
    this.scene.add(gz.getHelper()); // r0.169: el helper va a la escena, no el control
    gz.addEventListener("dragging-changed", (ev) => { if (this.orbit) this.orbit.enabled = !ev.value; });
    gz.addEventListener("mouseUp", () => this.commit());
    this.gizmo = gz;

    r.domElement.addEventListener("pointerdown", (ev) => this.onPointerDown(ev));
    const loop = (): void => { this.orbit?.update(); r.render(this.scene, this.camera); requestAnimationFrame(loop); };
    loop();
  }

  /** Picking: selecciona el objeto editable bajo el cursor y le engancha el gizmo. */
  private onPointerDown(ev: PointerEvent): void {
    if (!this.renderer || !this.gizmo) return;
    const rect = this.renderer.domElement.getBoundingClientRect();
    const ndc = new THREE.Vector2(((ev.clientX - rect.left) / rect.width) * 2 - 1, -((ev.clientY - rect.top) / rect.height) * 2 + 1);
    this.raycaster.setFromCamera(ndc, this.camera);
    const hit = this.raycaster.intersectObjects(this.group.children, true)[0];
    if (!hit) return;
    let o: THREE.Object3D | null = hit.object;
    while (o && !this.base.has(o.name)) o = o.parent;
    if (!o) return;
    this.picked = o;
    this.gizmo.attach(o);
  }

  /** Modo del gizmo (desde la UI): trasladar o girar. */
  setMode(mode: "translate" | "rotate"): void { this.gizmo?.setMode(mode); }

  /** Al soltar el gizmo: lee la transformada relativa al ancla (= centroide base) y emite
   *  el override (plan desde three: x→dx, z→dy, giro sobre threeY → rotDeg). */
  private commit(): void {
    const o = this.picked;
    if (!o) return;
    const base = this.base.get(o.name);
    if (!base) return;
    const [ax, ay] = planCentroid(base);
    const ov: ElementOverride = {
      dx: round2(o.position.x - ax),
      dy: round2(o.position.z - ay),
      rotDeg: round2((-o.rotation.y) * 180 / Math.PI),
    };
    if ((ov.dx ?? 0) === 0 && (ov.dy ?? 0) === 0 && (ov.rotDeg ?? 0) === 0) return;
    this.opts.onOverride(o.name, ov);
  }

  dispose(): void { this.renderer?.dispose(); this.gizmo?.dispose(); this.orbit?.dispose(); }
}

const round2 = (x: number): number => Math.round(x * 100) / 100;
