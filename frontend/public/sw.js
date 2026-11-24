// AI Grama Sahayak — Lightweight Service Worker
// Caches application shell so previously loaded pages remain readable when offline.
// NEVER caches API responses, health checks, or personal data.

const CACHE_NAME = "grama-sahayak-shell-v1";
const STATIC_SHELL_ASSETS = ["/", "/favicon.ico"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_SHELL_ASSETS).catch(() => {
        // Continue even if initial precache is partial
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // STRICT PRIVACY: NEVER cache API endpoints or health checks
  if (url.pathname.startsWith("/api/")) {
    return;
  }

  // Navigation requests: Network-first with offline cache fallback
  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response && response.status === 200) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return response;
        })
        .catch(() => {
          // Offline fallback: serve cached shell
          return caches.match(event.request).then((cached) => {
            return cached || caches.match("/");
          });
        })
    );
    return;
  }

  // Static assets: Stale-while-revalidate for fast rendering
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
