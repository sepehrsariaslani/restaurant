const CACHE_VERSION = "veederakht-pwa-v2";
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;

const PRECACHE_URLS = [
	"/",
	"/menu",
	"/cart",
	"/customer/login",
	"/assets/restaurant/frontend/favicon.svg",
	"/assets/restaurant/frontend/NoshYar.png",
];

self.addEventListener("install", (event) => {
	event.waitUntil(
		caches
			.open(STATIC_CACHE)
			.then((cache) => cache.addAll(PRECACHE_URLS))
			.catch(() => undefined)
			.then(() => self.skipWaiting()),
	);
});

self.addEventListener("activate", (event) => {
	event.waitUntil(
		caches
			.keys()
			.then((keys) =>
				Promise.all(
					keys
						.filter(
							(key) =>
								key.startsWith("veederakht-pwa-") &&
								!key.startsWith(CACHE_VERSION),
						)
						.map((key) => caches.delete(key)),
				),
			)
			.then(() => self.clients.claim()),
	);
});

function isApiRequest(url) {
	return url.pathname.startsWith("/api/") || url.pathname.startsWith("/socket.io/");
}

function isStaticAsset(url) {
	return (
		url.pathname.startsWith("/assets/restaurant/frontend/") ||
		url.pathname.startsWith("/files/") ||
		url.pathname.endsWith(".js") ||
		url.pathname.endsWith(".css") ||
		url.pathname.endsWith(".png") ||
		url.pathname.endsWith(".svg") ||
		url.pathname.endsWith(".jpg") ||
		url.pathname.endsWith(".jpeg") ||
		url.pathname.endsWith(".webp") ||
		url.pathname.endsWith(".woff2") ||
		url.pathname.endsWith(".ttf")
	);
}

async function networkFirst(request) {
	const cache = await caches.open(RUNTIME_CACHE);
	try {
		const fresh = await fetch(request);
		if (fresh && fresh.ok && request.method === "GET") {
			cache.put(request, fresh.clone());
		}
		return fresh;
	} catch (error) {
		const cached = await cache.match(request);
		if (cached) return cached;
		throw error;
	}
}

async function staleWhileRevalidate(request) {
	const cache = await caches.open(RUNTIME_CACHE);
	const cached = await cache.match(request);
	const fetched = fetch(request)
		.then((response) => {
			if (response && response.ok && request.method === "GET") {
				cache.put(request, response.clone());
			}
			return response;
		})
		.catch(() => undefined);
	return cached || fetched || Response.error();
}

function offlinePage() {
	return new Response(
		`<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>آفلاین | Veederakht</title>
  <style>
    body{margin:0;min-height:100vh;display:grid;place-items:center;background:#f7f1ea;color:#24473b;font-family:system-ui,-apple-system,sans-serif;text-align:center;padding:24px}
    .card{max-width:420px;background:#fff;border-radius:28px;padding:28px;box-shadow:0 20px 60px rgba(36,71,59,.14)}
    h1{margin:0 0 12px;font-size:1.4rem}p{line-height:1.9;margin:0 0 18px;color:#66756f}a{color:#fff;background:#24473b;text-decoration:none;border-radius:999px;padding:10px 18px;display:inline-block}
  </style>
</head>
<body><main class="card"><h1>فعلاً آفلاین هستید</h1><p>اتصال اینترنت برقرار نیست. بعضی صفحات ذخیره‌شده ممکن است در دسترس باشند.</p><a href="/">تلاش دوباره</a></main></body>
</html>`,
		{
			headers: { "Content-Type": "text/html; charset=utf-8" },
		},
	);
}

self.addEventListener("fetch", (event) => {
	const { request } = event;
	if (request.method !== "GET") return;

	const url = new URL(request.url);
	if (url.origin !== self.location.origin) return;

	if (isApiRequest(url)) {
		event.respondWith(networkFirst(request));
		return;
	}

	if (request.mode === "navigate") {
		event.respondWith(networkFirst(request).catch(() => offlinePage()));
		return;
	}

	if (isStaticAsset(url)) {
		event.respondWith(staleWhileRevalidate(request));
	}
});
