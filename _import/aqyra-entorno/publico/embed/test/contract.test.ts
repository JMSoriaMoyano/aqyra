import { describe, it, expect } from "vitest";
import { defineAqyraViewer, TAG, AqyraViewerElement } from "@aqyra/embed";

describe("aqyra-viewer · contrato", () => {
  it("registra el custom element <aqyra-viewer>", () => {
    defineAqyraViewer();
    expect(customElements.get(TAG)).toBe(AqyraViewerElement);
  });

  it("expone la superficie del contrato sin montar WebGL", () => {
    defineAqyraViewer();
    const el = document.createElement(TAG) as AqyraViewerElement;
    expect(typeof el.load).toBe("function");
    expect(typeof el.select).toBe("function");
    expect(typeof el.getProperties).toBe("function");
    expect(el.bcf.list()).toEqual([]);
    expect(typeof el.ids.validate).toBe("function");
  });

  it("getProperties/select fallan claro si no hay modelo cargado", async () => {
    defineAqyraViewer();
    const el = document.createElement(TAG) as AqyraViewerElement;
    await expect(el.getProperties("XXX")).rejects.toThrow(/GlobalId/);
    expect(() => el.select("XXX")).toThrow(/GlobalId/);
  });

  it("on() devuelve un unsubscribe invocable", () => {
    defineAqyraViewer();
    const el = document.createElement(TAG) as AqyraViewerElement;
    const off = el.on("model-loaded", () => {});
    expect(typeof off).toBe("function");
    off();
  });
});
