// Kettle service worker: offline shell, model cache, web push alerts.
const CACHE = "kettle-v35-1";

const SHELL = [
  "/", "/family", "/kitchen", "/listen", "/start", "/pair", "/how-sure",
  "/manifest.webmanifest", "/img/icon-192.png", "/img/icon-512.png", "/img/icon.svg",
  "/css/app.css?v=w4", "/css/theme.css?v=w4", "/css/type.css?v=w4", "/css/landing.css?v=w4", "/css/landing2.css?v=w4", "/css/credits.css?v=w4",
  "/js/chrome.js?v=w4", "/js/family.js?v=w4", "/js/kitchen.js?v=w4", "/js/start.js?v=w4", "/js/howsure.js?v=w4", "/js/beyond.js?v=w4", "/js/landing.js?v=w4",
  "/js/common-legacy.js", "/js/core.js", "/js/ui.js", "/js/listen.js", "/js/sense.js", "/js/sounds.js", "/js/fx.js", "/js/sample.js", "/js/head.js", "/js/worklet.js",
  "/fonts/geist-latin-wght.woff2", "/fonts/instrument-serif-italic.woff2",
  "/vendor/qrcode.js", "/css/urgent.css?v=u1", "/js/pushclient.js", "/js/safety.js", "/js/family.js?v=u1", "/js/kitchen.js?v=u1",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) =>
      // One missing file must not block install, so add each on its own.
      Promise.all(SHELL.map((u) => cache.add(u).catch(() => {})))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

async function networkFirst(req) {
  const cache = await caches.open(CACHE);
  try {
    const res = await fetch(req);
    if (res.ok) cache.put(req, res.clone());
    return res;
  } catch (err) {
    const hit = await cache.match(req, { ignoreSearch: true });
    if (hit) return hit;
    throw err;
  }
}

async function cacheFirst(req) {
  const cache = await caches.open(CACHE);
  const hit = await cache.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok && res.status === 200) cache.put(req, res.clone());
  return res;
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  const p = url.pathname;
  if (p.startsWith("/api/") || p === "/sw.js") return; // always network
  if (req.mode === "navigate" || (req.headers.get("accept") || "").includes("text/html")) {
    event.respondWith(networkFirst(req));
  } else if (p.startsWith("/model/") || p.startsWith("/vendor/ort/")) {
    event.respondWith(cacheFirst(req)); // big files: cached after first load
  } else {
    event.respondWith(networkFirst(req)); // css/js/img: fresh when online, cached when not
  }
});

self.addEventListener("push", (event) => {
  let d = {};
  try { d = event.data ? event.data.json() : {}; } catch { d = {}; }
  const tier = d.tier || "concern";
  const urgent = tier === "urgent";
  const opts = {
    body: d.body || "",
    tag: d.tag || "kettle",
    renotify: true,
    requireInteraction: urgent,
    icon: "/img/icon-192.png",
    badge: "/img/icon-192.png",
    data: { url: d.url || "/family", alertId: d.alertId || "", home: d.home || "" },
  };
  if (urgent) opts.vibrate = [300, 100, 300, 100, 600];
  if (urgent || tier === "test") opts.actions = [{ action: "ack", title: "I've got it" }];
  event.waitUntil(self.registration.showNotification(d.title || "Kettle", opts));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const data = event.notification.data || {};
  const target = new URL(data.url || "/family", self.location.origin);
  if (event.action === "ack" && data.alertId) target.searchParams.set("ack", data.alertId);
  event.waitUntil((async () => {
    const wins = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    const match = wins.find((c) => new URL(c.url).pathname === target.pathname);
    if (match) {
      try {
        if (event.action === "ack") await match.navigate(target.href);
        return await match.focus();
      } catch { /* fall through to open a new window */ }
    }
    return self.clients.openWindow(target.href);
  })());
});
