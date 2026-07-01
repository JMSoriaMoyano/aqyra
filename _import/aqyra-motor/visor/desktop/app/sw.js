/* Visor IFC — Service Worker (offline). Estrategia:
   - HTML / navegación y models/manifest.json (config que cambia): network-first con fallback a caché.
   - Resto (CDN three/fragments/web-ifc + WASM + worker.mjs, modelos .frag/.props.json,
     iconos, webmanifest): cache-first, poblando en runtime. Tras UNA carga online, todo offline.
   Subir CACHE al cambiar de build para invalidar la caché antigua. */
const CACHE = "visor-ifc-v1.0-b6";
const PRECACHE = [
  "./visor-ifc-v1.0.html",
  "./visor.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-512-maskable.png"
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => Promise.allSettled(PRECACHE.map((u) => c.add(u))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("message", (e) => {
  if (e.data === "skipWaiting") self.skipWaiting();
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  const fresh = req.mode === "navigate" || url.pathname.endsWith(".html") || url.pathname.endsWith("manifest.json");

  if (fresh) {
    // network-first: lo más reciente cuando hay red, caché cuando no
    e.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match(req).then((m) => m || caches.match("./visor-ifc-v1.0.html")))
    );
    return;
  }

  // cache-first para CDN/WASM/worker/modelos/iconos (inmutables o versionados)
  e.respondWith(
    caches.match(req).then((hit) => {
      if (hit) return hit;
      return fetch(req).then((res) => {
        try {
          if (res && (res.ok || res.type === "opaque")) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
          }
        } catch (_) {}
        return res;
      });
    })
  );
});
