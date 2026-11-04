# Rongcheng Jingtu · Web Frontend

An interactive health-aware navigation interface built with **Vue 3 + Vite**. It handles map rendering, origin/destination input, preference switching, result presentation and real-time navigation. The frontend calls the `python/` backend over REST and Socket.IO, and relies on AMap JS API 2.0 for mapping.

## Requirements

| Dependency | Version |
| --- | --- |
| Node.js | >= 20.19 (required by Vite 8) |
| AMap JS API | security code `VITE_AMAP_SECURITY_CODE` (same account as the backend Web Service key) |

## Quick Start

```bash
npm install
copy .env.example .env      # Windows; use cp on Linux/macOS
# edit .env and set VITE_AMAP_SECURITY_CODE
npm run dev                 # http://localhost:3000
```

- Chinese UI: <http://localhost:3000/index.html>
- English UI: <http://localhost:3000/index_en.html>

The dev server proxies `/api` and `/socket.io` (including the WebSocket upgrade) to `http://localhost:5000`, so start the backend first.

## Commands

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the dev server (port 3000, listening on `0.0.0.0`) |
| `npm run build` | Production build; both entry points are written to `dist/` |
| `npm run preview` | Preview the built artefacts locally |

## Directory Structure

```
frontend/
├── index.html                 # Chinese entry, injects the security code
├── index_en.html              # English entry
├── vite.config.js             # dual-entry build + API/Socket.IO proxy
├── .env.example               # environment variable template
├── public/
│   └── favicon.svg
└── src/
    ├── main_zh.js / main_en.js # mount scripts for the two entries
    ├── App.vue
    ├── components/            # page components such as HomeView
    ├── composables/           # useAMapStrict: map loading and instance management
    ├── locales/               # zh.js / en.js UI strings
    ├── router/                # vue-router configuration
    └── style.css
```

## Interaction States

- **Loading**: a skeleton placeholder is shown before the map initialises; buttons are disabled while a planning request is in flight.
- **Empty**: when no destination is selected, the result panel prompts for an origin and destinations and no request is sent.
- **Error**: invalid parameters, an expired key or an unreachable backend produce a readable message in the panel while keeping the user's input.
- **Success**: the optimal visiting order, total distance, average AQI, health score and per-stop AQI are displayed, and the route is drawn on the map.

## FAQ

| Symptom | Check |
| --- | --- |
| Blank map / `INVALID_USER_SCODE` | `VITE_AMAP_SECURITY_CODE` is missing from `.env`, or Vite was not restarted after the change |
| API 404 / connection refused | The backend is not running or not listening on port 5000 |
| Frequent Socket.IO reconnects | The proxy is missing `ws: true`; check `vite.config.js` |
| 404 after refreshing a built page | The deployment must fall back unknown routes to `index.html` |

See the root [README.md](../README.md) for the full project documentation.
