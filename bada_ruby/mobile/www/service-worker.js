// Bada XP — offline cache so the installed app works without a network.
const CACHE = "bada-xp-v1";
const ASSETS = [
  "./", "./index.html", "./manifest.webmanifest", "./icon.svg"
];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks =>
    Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  // Never cache LLM API calls; always hit the network for those.
  if (url.hostname.endsWith("anthropic.com") || url.hostname.endsWith("openai.com")) return;
  e.respondWith(
    caches.match(e.request).then(hit => hit || fetch(e.request).then(resp => {
      if (e.request.method === "GET" && resp.ok && url.origin === location.origin) {
        const copy = resp.clone(); caches.open(CACHE).then(c => c.put(e.request, copy));
      }
      return resp;
    }).catch(() => caches.match("./index.html")))
  );
});
