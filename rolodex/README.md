# Rolodex — individual model APIs + lane failover

One OpenAI-compatible gateway. **Every catalog model has its own API id** you can call alone.
The same models are also mounted into **lanes** for automatic failover.

```
You / Hermes / OpenWorker / OpenCode
        ↓  http://127.0.0.1:4000/v1
   Rolodex gateway  (lists everything)
        ↓
   LiteLLM upstream :4001
        ↓
   independent ids          lanes (ordered failover)
   or/qwen3-coder      →    lane/code
   groq/llama-3.3-70b  →    lane/fast + lane/smart
   local/ds4           →    all lanes (fallback)
   gemini/2.5-flash    →    lane/smart
   …
```

## Two ways to call

| You type | What happens |
|----------|----------------|
| `model=or/qwen3-coder` | Runs **only** that model (independent API) |
| `model=groq/llama-3.3-70b` | Runs **only** Groq 70B |
| `model=lane/smart` | Failover across smart’s **ready** cards |
| `model=smart` | Same (alias) |
| `model=lanes` | Returns the full lane→rolodex dump (no LLM call) |

## List APIs

```bash
# Every lane + every individual model id (ready flag, ctx, t/s, tokens left)
curl -s http://127.0.0.1:4000/v1/models -H "Authorization: Bearer sk-rolodex" | jq .

# Full rolodex per lane (all cards, including missing-key)
curl -s http://127.0.0.1:4000/v1/lanes -H "Authorization: Bearer sk-rolodex" | jq .

curl -s http://127.0.0.1:4000/v1/lanes/code -H "Authorization: Bearer sk-rolodex" | jq .
```

Or:

```bash
./scripts/inventory.py
./scripts/smoke.sh lanes
./scripts/smoke.sh lane/smart
./scripts/smoke.sh groq/llama-3.3-70b
```

## Quickstart

```bash
cd rolodex
cp .env.example .env          # paste keys — each key unlocks that provider’s model APIs
python3 -m pip install -r requirements.txt
./scripts/start.sh            # gateway :4000  (LiteLLM :4001)
./scripts/test.sh             # unit + failover (38 tests)
./scripts/verify_live.sh      # against a running gateway
```

Auth: `Authorization: Bearer sk-rolodex`.

## Lanes

| Lane | Intent |
|------|--------|
| `lane/local` | Private GLM |
| `lane/fast` | Burst / tool loops |
| `lane/smart` | Default agent brain |
| `lane/code` | Coding |

Local GLM is on **every** lane as last-resort fallback, so typing any lane always resolves.

## Catalog

- [`catalog.yaml`](catalog.yaml) — 82 models / 27 providers with context, limits, t/s, lane membership
- [`CATALOG.md`](CATALOG.md) — approvable snapshot
- Missing keys ⇒ model still **listed**, but independent calls return `model_not_ready` until you add the key; lanes skip unready cards

## Clients

Point Hermes / OpenCode / OpenWorker at `http://127.0.0.1:4000/v1` — see `clients/`.
Pick either a **lane** or an **individual model id** from `/v1/models`.
