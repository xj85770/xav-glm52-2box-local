<div align="center">

# 🕹️ GLM-5.2 · 753B · fully local on two Macs

**A 753-billion-parameter model running in your room. No cloud. No API. Nothing leaves the machine.**

![params](https://img.shields.io/badge/params-753B-8A2BE2?style=for-the-badge)
![active](https://img.shields.io/badge/active%2Ftoken-~40B-9400D3?style=for-the-badge)
![speed](https://img.shields.io/badge/decode-18.5_tok%2Fs-00C853?style=for-the-badge)
![context](https://img.shields.io/badge/context-128K_served-00B8D4?style=for-the-badge)

![hardware](https://img.shields.io/badge/2×_Apple_M5_Max-128GB_each-1A1A2E?style=for-the-badge&logo=apple)
![backend](https://img.shields.io/badge/backend-Metal_·_llama.cpp_RPC-FF6D00?style=for-the-badge)
![cloud](https://img.shields.io/badge/cloud_spend-%240-success?style=for-the-badge)
![weights](https://img.shields.io/badge/weights-open-2962FF?style=for-the-badge)

</div>

---

Run **GLM-5.2**, a 753B-parameter Mixture-of-Experts model, **100% locally** on two Apple Silicon
Macs. No cloud, no API, no data leaving your machines. This repo has the patches, launch scripts, and
demo tooling to reproduce it, plus the exact config that gets the best speed.

A single 128GB Mac can't hold the model (it's ~202GB), so it falls back to SSD streaming at ~0.9 tok/s,
which is unusable. Pool two Macs over Thunderbolt into 256GB of unified memory and the whole model stays
resident: same model, same quant, **~16 → 18.5 tok/s**.

## Results

| Config | tok/s | vs start |
|---|---|---|
| q8_0 KV, top-8 experts (starting point) | 15.6 | — |
| f16 KV, top-8 | 16.67 | +6.8% |
| f16 KV, top-7 | 17.31 | +11.0% |
| **f16 KV, top-5** (recommended) | **18.52** | **+18.7%** |

Two free wins, no new model code:
1. **KV cache in f16 beats q8_0.** The per-step dequant of q8_0 costs more than its smaller read on the
   small MLA KV. Just use `f16`.
2. **Drop expert routing from top-8 to top-5.** Output stays coherent and you read fewer expert weights
   per token. (Odd values like 7 and 5 are stable; some even values trip an allocation edge on this build.)

**Context:** served up to **128K tokens** live (the model trains to 1M natively).

## Hardware

- 2× Apple M5 Max, 128GB unified memory each (256GB total)
- One Thunderbolt 5 cable between them (a single cable is the stable config)
- Metal backend on both, llama.cpp RPC, pipeline-parallel (each box holds half the weights)

## Model

GLM-5.2, 753B params (~40B active/token, MoE, 256 experts, `glm-dsa` / MLA attention), quantized to
**IQ1_S** (Unsloth dynamic build, ~202GB). Open weights.

## Quickstart

```sh
# 1. Build llama.cpp with the patches in patches/ on BOTH machines (identical binaries):
#    cmake ... -DGGML_METAL=ON -DGGML_RPC=ON -DGGML_BLAS=OFF
#    apply patches/ggml-rpc-stability.patch  (fixes a deep-MoE RPC stack overflow on macOS)
#    apply patches/glmdsa-mtp.patch          (glm-dsa nextn / MTP support)

# 2. Configure your two machines:
cp scripts/cluster.env.example scripts/cluster.env
$EDITOR scripts/cluster.env     # fill in NODE1 ssh/ip, binary paths, model path

# 3. Launch (run on NODE0 — the coordinator):
KV_TYPE=f16 N_EXPERT_USED=5 CTX=16384 scripts/launch.sh

# 4. It serves an OpenAI-compatible endpoint on localhost:8080.
scripts/verify.sh
```

The launcher is deliberately paranoid: it gates on the cross-node link, pre-flights free RAM on both
boxes, runs a smoke decode before the real load, and tears down cleanly (no leaked memory) on any failure.

## Rolodex (full free-API catalog + local lanes)

`rolodex/` is an OpenAI-compatible LiteLLM gateway over **all legitimate free/trial APIs** from
[free-llm-api-resources](https://github.com/cheahjs/free-llm-api-resources) plus this local GLM stack.
Swap by **lane** or by **exact model id**. Inventory shows context, typical/observed t/s, limits, and
tokens/requests left:

```sh
cd rolodex && cp .env.example .env
./scripts/inventory.py --write       # state/AGENT_CONTEXT.md for the agent
./scripts/start.sh                   # http://127.0.0.1:4000/v1
./scripts/smoke.sh lane/smart        # or: or/qwen3-coder / groq/llama-3.3-70b
./scripts/test.sh
```

See [`rolodex/README.md`](rolodex/README.md), [`rolodex/catalog.yaml`](rolodex/catalog.yaml), `rolodex/clients/`.

## Demo

`demo/` has the tooling used to make real-time proof videos (the on-screen numbers are streamed at true
wall-clock, nothing is sped up or faked):

- `bench-realtime.py` — streams a completion token-by-token at real speed with a live tok/s counter.
- `generate-pacman.py` — asks the local model to write a complete Pac-Man game in one file.
- `pacman.html` — a working Pac-Man **written by GLM-5.2 itself** (one one-character fix). Open it in a browser and play.
- `render-bench-video.py` — renders a transcript into a terminal-style MP4.

## Patches

- `patches/ggml-rpc-stability.patch` — converts a recursive graph walk to iterative, fixing a stack
  overflow on deep-MoE graphs over llama.cpp's RPC backend on macOS. Generally useful for large MoE + RPC.
- `patches/glmdsa-mtp.patch` — wires the glm-dsa nextn / MTP head into llama.cpp.

## Credits

Built on [llama.cpp](https://github.com/ggml-org/llama.cpp). Model: GLM-5.2 by Z.ai (zai-org).
IQ1_S dynamic quant by [Unsloth](https://github.com/unslothai). Thanks to the local-inference community.

## License

See [LICENSE](LICENSE).
