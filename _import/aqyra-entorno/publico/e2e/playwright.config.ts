import { defineConfig } from "@playwright/test";

// Sirve el bundle e2e (vite build) + el WASM de web-ifc copiado a dist/, y
// arranca Chromium headless (WebGL por SwiftShader) para verificar el render.
export default defineConfig({
  testDir: __dirname,
  timeout: 60000,
  webServer: {
    command: "python3 -m http.server 5179 --directory dist",
    cwd: __dirname,
    port: 5179,
    reuseExistingServer: true,
  },
  use: { baseURL: "http://localhost:5179" },
});
