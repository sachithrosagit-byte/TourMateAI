# frontend/ — Presentation Tier (React)

**Owner:** Web developer.
**Stack:** React + Vite, **JavaScript** (`.jsx`).

The single-page app users interact with. It talks to the Flask backend over HTTP/JSON and never
calls AI models directly — it calls backend endpoints, which internally call `/api/ai/*`.

## Initialize (first time)

This folder is a structure skeleton. Scaffold the Vite app into it, then keep the `src/` layout
below:

```
npm create vite@latest . -- --template react
npm install
npm run dev
```

## Folder layout

| Folder | What goes here |
|--------|----------------|
| `public/` | Static assets served as-is |
| `src/assets/` | Images, icons, fonts |
| `src/components/` | Reusable UI components (buttons, cards, nav) |
| `src/pages/` | Route-level pages: Dashboard, Recommendations, Chatbot, ImageIdentify, Maps, Profile, Admin |
| `src/services/` | API client modules that call the backend (one per domain) |
| `src/hooks/` | Custom React hooks |
| `src/context/` | React context providers (e.g. auth/user state) |
| `src/utils/` | Helpers (formatting, validation) |
| `src/styles/` | Global styles / theme |

## Talking to the backend

- Base URL comes from an env var (e.g. `VITE_API_BASE_URL`) — add a `frontend/.env` (git-ignored).
- Request/response shapes for AI features are fixed in [`../docs/api-contract.md`](../docs/api-contract.md).
- Firebase Authentication is used on the client; send the ID token to the backend for verification.

## Boundaries

- ✅ Owns everything under `frontend/`.
- ❌ Do not put business logic or secrets here; the backend owns those.
