self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(clients.claim());
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') {
    return;
  }
  event.respondWith(
    caches.open('offline-cache').then((cache) =>
      cache.match(event.request).then((resp) => {
        const fetchPromise = fetch(event.request).then((networkResp) => {
          cache.put(event.request, networkResp.clone());
          return networkResp;
        });
        return resp || fetchPromise;
      })
    )
  );
});