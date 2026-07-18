const CACHE = 'food-map-v1';
const urls = [
  '.',
  'index.html',
  '海陸海產店.html',
  '臭麵攤.html',
  '萬華必比登美食.html',
  'YMS by onefifteen.html',
  'icon.svg',
  'manifest.json'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(urls))
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((r) => r || fetch(e.request))
  );
});
