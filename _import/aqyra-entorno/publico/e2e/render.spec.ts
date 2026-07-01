import { test, expect } from "@playwright/test";

// Verificación en NAVEGADOR REAL del render de F1: monta <aqyra-viewer>, carga
// un IFC con geometría y comprueba que three.js dibujó mallas sobre un contexto
// WebGL real, sin errores de página.
test("monta <aqyra-viewer> y renderiza geometría IFC en WebGL", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto("/");
  await page.waitForFunction(
    () => (window as Record<string, unknown>).__aqyraReady === true,
    { timeout: 40000 },
  );

  const appError = await page.evaluate(() => (window as Record<string, unknown>).__aqyraError);
  expect(appError, `app error: ${appError}`).toBeFalsy();

  const hasGL = await page.evaluate(() => {
    const c = document.querySelector("canvas") as HTMLCanvasElement | null;
    return !!(c && (c.getContext("webgl2") || c.getContext("webgl")));
  });
  expect(hasGL).toBe(true);

  const meshes = await page.evaluate(() => (window as Record<string, unknown>).__aqyraMeshes as number);
  expect(meshes).toBeGreaterThan(0);
  expect(errors, errors.join("\n")).toEqual([]);
});
