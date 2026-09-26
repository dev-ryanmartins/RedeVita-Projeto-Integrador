const CACHE_NAME = 'redevita-pwa-v1';
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/static/css/global.css',
  '/static/css/dashboard.css',
  '/static/js/theme.js',
  '/static/js/mascaras.js',
  '/static/img/icons/icon-192x192.png',
  '/static/img/icons/icon-512x512.png',
  '/static/img/icons/icon.svg'
];

// Instalação do Service Worker com cache seguro
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      // Adiciona itens individualmente para não quebrar a instalação se algum falhar
      for (const asset of STATIC_ASSETS) {
        try {
          await cache.add(asset);
        } catch (err) {
          console.warn('PWA: Não foi possível pré-armazenar:', asset, err);
        }
      }
    })
  );
  self.skipWaiting();
});

// Ativação e limpeza de versões antigas do cache
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Interceptação de requisições: Cache First para estáticos, Network First para dados dinâmicos
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Requisições para estáticos: Cache First com fallback para rede
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) return cached;
        return fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const copy = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return networkResponse;
        });
      })
    );
    return;
  }

  // Navegação HTML: Network First com fallback para o cache
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(event.request).then((cached) => {
          if (cached) return cached;
          return caches.match('/');
        });
      })
    );
    return;
  }

  // Demais requisições: Rede normal com fallback para cache
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});

// Sistema de Notificações Push - Módulo Aditivo
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'Nova notificação do RedeVita',
    icon: '/static/img/icons/icon-192x192.png',
    badge: '/static/img/icons/icon-512x512.png',
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Ver Detalhes',
        icon: '/static/img/icons/icon-192x192.png'
      },
      {
        action: 'close',
        title: 'Fechar',
        icon: '/static/img/icons/icon-192x192.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('RedeVita', options)
  );
});

// Tratamento de cliques em notificações
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then((clientList) => {
        for (const client of clientList) {
          if (client.url === '/' && 'focus' in client) {
            return client.focus();
          }
          if (client.url === '/') {
            return client.open('/');
          }
        }
      })
    );
  }
});
