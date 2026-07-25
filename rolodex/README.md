# Rolodex — full free-API + local lane gateway

One OpenAI-compatible endpoint. Behind it: **every legitimate free/trial card** from
[cheahjs/free-llm-api-resources](https://github.com/cheahjs/free-llm-api-resources), plus your local GLM.

```
Hermes / OpenWorker / OpenCode / curl
        ↓  http://127.0.0.1:4000/v1
     Rolodex (LiteLLM)
        ↓  swap by lane OR exact model id
  lane/local|fast|smart|code
  or/llama-3.3-70b · groq/llama-3.3-70b · gemini/2.5-flash · local/ds4 · …
```

## What you can see before swapping

```bash
./scripts/inventory.py              # full table: ctx, t/s, rpm/rpd/tpm, tokens left
./scripts/inventory.py --available  # only cards whose keys are configured
./scripts/inventory.py --lane code
./scripts/inventory.py --write      # refreshes state/AGENT_CONTEXT.md (+ .json)
```

Each row includes:

| field | meaning |
|-------|---------|
| `id` | exact model name to send in `model:` |
| `context` | context window (tokens) |
| `tps_typical` | expected decode speed |
| `tps_observed` | last measured t/s from your traffic |
| `rpm/rpd/tpm/tpd` | published free limits |
| `req left/day` / `tok left/day` | **remaining** vs those caps (local tracker) |

Put `state/AGENT_CONTEXT.md` in the agent’s context so it can pick an approved model.

## Quickstart

```bash
cd rolodex
cp .env.example .env          # paste any free-tier keys you have
python3 -m pip install -r requirements.txt
./scripts/start.sh            # builds runtime + inventory, serves :4000
```

```bash
./scripts/smoke.sh lane/smart
./scripts/smoke.sh or/qwen3-coder
./scripts/smoke.sh groq/llama-3.3-70b
./scripts/test.sh
```

Auth: `Authorization: Bearer sk-rolodex` (`ROLODEX_MASTER_KEY`).

## Lanes

| Lane | Intent | Typical order |
|------|--------|----------------|
| `lane/local` | Private GLM | ds4 → llama.cpp → CF GLM |
| `lane/fast` | Burst / tool loops | Groq → Gemini lite → Cerebras → OR small |
| `lane/smart` | Default agent brain | Gemini → OR big → Groq → local |
| `lane/code` | Coding | Codestral → OR qwen-coder → Groq → local |

Aliases: `local`, `fast`, `smart`, `code`.

## Catalog

- Source of truth: [`catalog.yaml`](catalog.yaml) (providers, models, context, limits, t/s, lanes)
- Missing keys ⇒ card omitted from runtime (safe)
- `ROLODEX_TIERS=local,free` to skip trial-credit providers
- Usage written to `state/usage.json` via LiteLLM callback

## Clients

See `clients/` for Hermes / OpenCode / OpenWorker snippets. Point `base_url` at
`http://127.0.0.1:4000/v1` and set `model` to a lane or exact id from inventory.

## Don’t abuse free tiers

Shared quotas (OpenRouter, Cohere, …) drain across models. Prefer `lane/local` for private work.
