const CACHE_NAME = 'redevita-v3';
const STATIC_ASSETS = [
  '/',
  '/static/css/global.css',
  '/static/js/components.js',
  '/static/js/mascaras.js',
  '/static/js/toast_notifications.js',
  '/static/js/dynamic_search.js',
  '/static/js/app_integration.js',
  '/static/js/keyboard_shortcuts.js',
  '/static/js/user_tour.js',
  '/static/js/qrcode_generator.js',
  '/static/js/table_status_filter.js',
  '/static/js/accessibility.js',
  '/static/js/idle_timer.js',
  '/static/js/pwa_installer.js',
  '/static/js/chatbot_widget.js',
  '/static/js/pharma_calculator.js',
  '/static/js/offline_sync.js',
  '/static/js/chart.umd.min.js',
  '/static/js/leaflet.js',
  '/static/css/leaflet.css',
  '/static/img/login-bg.jpg',
  '/static/manifest.json',
];

// Cache-first strategy para assets estáticos
const CACHE_FIRST_URLS = [
  '/static/css/',
  '/static/js/',
  '/static/img/',
];

// Network-first strategy para API
const NETWORK_FIRST_URLS = [
  '/api/',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Background Sync para sincronização offline
self.addEventListener('sync', event => {
  if (event.tag === 'sync-doacoes') {
    event.waitUntil(
      self.clients.matchAll().then(clients => {
        clients.forEach(client => {
          client.postMessage({
            type: 'SYNC_DOACOES'
          });
        });
      })
    );
  }
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  if (event.request.method !== 'GET') return;

  // Cache-first para assets estáticos
  for (const pattern of CACHE_FIRST_URLS) {
    if (url.pathname.startsWith(pattern)) {
      event.respondWith(
        caches.match(event.request).then(cached => {
          if (cached) {
            // Retorna do cache imediatamente
            return cached;
          }
          // Se não está no cache, busca na rede e cacheia
          return fetch(event.request).then(response => {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
            return response;
          });
        })
      );
      return;
    }
  }

  // Network-first para APIs
  for (const pattern of NETWORK_FIRST_URLS) {
    if (url.pathname.startsWith(pattern)) {
      event.respondWith(
        fetch(event.request).then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          return response;
        }).catch(() => {
          return caches.match(event.request);
        })
      );
      return;
    }
  }

  // Para outras requisições, tenta cache primeiro, depois rede
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) {
        return cached;
      }
      return fetch(event.request).then(response => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        return response;
      }).catch(() => {
        // Offline fallback para navegação
        if (event.request.mode === 'navigate') {
          return caches.match('/');
        }
      });
    })
  );
});
