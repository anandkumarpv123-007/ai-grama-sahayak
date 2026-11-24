// AI Grama Sahayak — Privacy-Hardened Service Worker (v2)
// Caches only same-origin public application shell resources so the UI remains readable offline.
// STRICT SAFETY: Excludes API requests, non-GET requests, uploads, and external responses.

const CACHE_NAME = "grama-sahayak-shell-v2";
const STATIC_SHELL_ASSETS = ["/", "/favicon.ico"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_SHELL_ASSETS).catch(() => {
        // Continue even if precache is partial
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME && key.startsWith("grama-sahayak-"))
          .map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  // 1. SAFETY: Exclude all non-GET requests (POST, PUT, DELETE, etc.)
  if (event.request.method !== "GET") {
    return;
  }

  const url = new URL(event.request.url);

  // 2. PRIVACY: Only handle same-origin requests; never cache external origins
  if (url.origin !== self.location.origin) {
    return;
  }

  // 3. STRICT EXCLUSION: Never touch or cache API endpoints, uploads, audio or health checks
  if (
    url.pathname.startsWith("/api/") ||
    url.pathname.includes("/api") ||
    url.pathname.includes("document") ||
    url.pathname.includes("upload") ||
    url.pathname.includes("voice") ||
    url.pathname.includes("transcribe") ||
    url.pathname.includes("tts")
  ) {
    return;
  }

  // 4. Navigation requests (HTML pages): Network-first with short timeout to prevent serving outdated deployments indefinitely
  if (event.request.mode === "navigate") {
    event.respondWith(
      (async () => {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 2500);

          const networkResponse = await fetch(event.request, {
            signal: controller.signal,
          });
          clearTimeout(timeoutId);

          if (networkResponse && networkResponse.status === 200) {
            const copy = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return networkResponse;
        } catch {
          // Network offline or timed out: fall back to cached shell
          const cached = await caches.match(event.request);
          if (cached) return cached;
          const fallbackShell = await caches.match("/");
          if (fallbackShell) return fallbackShell;
          return new Response("Offline. Please reconnect to access AI Grama Sahayak.", {
            status: 503,
            headers: { "Content-Type": "text/plain; charset=utf-8" },
          });
        }
      })()
    );
    return;
  }

  // 5. Version-hashed Next.js static assets and icons: Stale-While-Revalidate
  if (
    url.pathname.startsWith("/_next/static/") ||
    url.pathname.endsWith(".ico") ||
    url.pathname.endsWith(".png") ||
    url.pathname.endsWith(".css") ||
    url.pathname.endsWith(".js")
  ) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        const fetchPromise = fetch(event.request)
          .then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              const copy = networkResponse.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
            }
            return networkResponse;
          })
          .catch(() => cachedResponse);

        return cachedResponse || fetchPromise;
      })
    );
  }
});
