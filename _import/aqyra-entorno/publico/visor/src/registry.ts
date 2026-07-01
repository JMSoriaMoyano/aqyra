import type { LoadedModel } from "./ifc-loader.js";

/** Registro de FEDERACIÓN: varios modelos cargados + índice por GlobalId. */
export class ModelRegistry {
  private readonly models = new Map<string, LoadedModel>();
  private readonly index = new Map<string, { modelId: string; expressId: number }>();

  add(model: LoadedModel): void {
    this.models.set(model.id, model);
    for (const e of model.elements) {
      this.index.set(e.globalId, { modelId: model.id, expressId: e.expressId });
    }
  }

  list(): LoadedModel[] {
    return [...this.models.values()];
  }

  get(id: string): LoadedModel | undefined {
    return this.models.get(id);
  }

  findByGlobalId(globalId: string): { model: LoadedModel; expressId: number } | undefined {
    const hit = this.index.get(globalId);
    if (!hit) return undefined;
    const model = this.models.get(hit.modelId);
    return model ? { model, expressId: hit.expressId } : undefined;
  }

  remove(id: string): void {
    this.models.delete(id);
    this.index.clear();
    for (const m of this.models.values())
      for (const e of m.elements) this.index.set(e.globalId, { modelId: m.id, expressId: e.expressId });
  }

  clear(): void {
    this.models.clear();
    this.index.clear();
  }
}
