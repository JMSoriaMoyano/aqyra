// Visor IFC — app de escritorio (Electron). Sin servidor externo: levanta un
// servidor http ESTÁTICO dentro del propio proceso de Electron (127.0.0.1) y
// carga el visor. Así no hay un Python ni un proceso aparte que un antivirus
// pueda cerrar: si la app está abierta, el servidor está dentro de ella.
const { app, BrowserWindow, shell } = require("electron");
const http = require("http");
const fs = require("fs");
const path = require("path");

// Raíz de los archivos web: app/ (empaquetado) o ../ (ejecutando en desarrollo).
const ROOT = fs.existsSync(path.join(__dirname, "app", "visor-ifc-v1.2.html"))
  ? path.join(__dirname, "app")
  : path.join(__dirname, "..");

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".webmanifest": "application/manifest+json; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".frag": "application/octet-stream",
  ".wasm": "application/wasm",
  ".png": "image/png",
  ".ico": "image/x-icon",
  ".svg": "image/svg+xml",
  ".bcfzip": "application/octet-stream"
};

function createServer() {
  return http.createServer((req, res) => {
    try {
      let p = decodeURIComponent((req.url || "/").split("?")[0]);
      if (p === "/" || p === "") p = "/visor-ifc-v1.2.html";
      const fp = path.normalize(path.join(ROOT, p));
      if (!fp.startsWith(ROOT)) { res.writeHead(403); res.end("forbidden"); return; }
      fs.readFile(fp, (err, data) => {
        if (err) { res.writeHead(404); res.end("not found"); return; }
        res.writeHead(200, {
          "Content-Type": MIME[path.extname(fp).toLowerCase()] || "application/octet-stream",
          "Cache-Control": "no-store"
        });
        res.end(data);
      });
    } catch (e) { res.writeHead(500); res.end("error"); }
  });
}

function listenOnFreePort(ports) {
  return new Promise((resolve, reject) => {
    const tryNext = (i) => {
      if (i >= ports.length) { reject(new Error("sin puerto libre")); return; }
      const srv = createServer();
      srv.once("error", (e) => { if (e.code === "EADDRINUSE") tryNext(i + 1); else reject(e); });
      srv.listen(ports[i], "127.0.0.1", () => resolve({ srv, port: ports[i] }));
    };
    tryNext(0);
  });
}

let win = null;

async function start() {
  let port;
  try {
    ({ port } = await listenOnFreePort([8731, 8732, 8733, 8745, 8766, 8777]));
  } catch (e) {
    console.error("No se pudo iniciar el servidor interno:", e);
    app.quit();
    return;
  }

  win = new BrowserWindow({
    width: 1440,
    height: 900,
    backgroundColor: "#1e2330",
    autoHideMenuBar: true,
    title: "Visor IFC — Estructurando",
    icon: path.join(__dirname, "assets", "icon.ico"),
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  win.removeMenu();

  // Descargas (exportar IFC / BCF / caché): guardar con diálogo nativo.
  win.webContents.session.on("will-download", () => { /* usa el diálogo por defecto */ });

  // Enlaces externos (URIs de clasificación) al navegador del sistema.
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) { shell.openExternal(url); return { action: "deny" }; }
    return { action: "allow" };
  });

  win.loadURL("http://127.0.0.1:" + port + "/visor-ifc-v1.2.html");
  win.on("closed", () => { win = null; });
}

app.whenReady().then(start);
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) start(); });
app.on("window-all-closed", () => { app.quit(); });
