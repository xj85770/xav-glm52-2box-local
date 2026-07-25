# lanes — local agent dashboard chat

Your **lanes** UI, fully wired to **lanes2** (free-API + local GLM rolodex).

```
browser → lanes (:3000) → lanes2 (:4000) → LiteLLM (:4001) → free APIs / local GLM
```

## One command (recommended)

From repo root:

```bash
./scripts/start-stack.sh
open http://127.0.0.1:3000
```

That starts:
1. LiteLLM upstream (`:4001`)
2. lanes2 gateway (`:4000`) — all model APIs + lanes
3. lanes dashboard (`:3000`) — agent chat UI

## What the UI does

- Lane pills: `local` / `fast` / `smart` / `code` (failover)
- Model dropdown: every individual API id from lanes2 (`or/…`, `groq/…`, `local/ds4`, …)
- Ready counts + context / t/s from lanes2 inventory
- Streaming chat via `POST /api/chat` → lanes2 `/v1/chat/completions`
- Local session list in memory

## API routes (lanes dashboard)

| Route | Purpose |
|-------|---------|
| `GET /` | Chat UI |
| `GET /health` | Dashboard + lanes2 health |
| `GET /api/models` | Proxy of lanes2 `/v1/models` |
| `GET /api/lanes` | Proxy of lanes2 `/v1/lanes` |
| `POST /api/chat` | Agent chat (SSE stream) |
| `GET/POST /api/sessions` | Local chat sessions |

## Separate start (if lanes2 already running)

```bash
cd lanes2 && ./scripts/start.sh   # terminal A
cd lanes && ./scripts/start.sh    # terminal B
```
