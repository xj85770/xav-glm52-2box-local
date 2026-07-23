# Tuning findings — GLM-5.2 on 2× M5 Max (llama.cpp RPC)

Measured on 2× Apple M5 Max, 128GB unified memory each, Thunderbolt 5 link, IQ1_S
quant (~202GB), pipeline-parallel RPC split. All numbers are **warm decode** tok/s from
`llama-server` timings (`predicted_per_second`), not prefill.

## The residency cliff (why ~3 tok/s vs ~18 tok/s)

| Regime | What is happening | tok/s |
|---|---|---|
| Single Mac, weights on SSD | Every token streams expert shards from disk | **~0.9–3** |
| Two Macs, weights fully resident | Decode is GPU + unified-memory bound | **~16–18.5** |

A 202GB model cannot fit in 128GB. External NVMe (e.g. Lexar) adds capacity but not
inference speed — even fast USB/TB enclosures are ~5–7 GB/s vs hundreds of GB/s in
unified memory. **Ceiling speed requires the 2-box RPC split with both halves resident.**

## Decode tuning table (same hardware, same quant)

| Config | tok/s | Notes |
|---|---|---|
| q8_0 KV, top-8 experts | 15.6 | Baseline |
| f16 KV, top-8 | 16.67 | f16 wins on small MLA KV |
| f16 KV, top-7 | 17.31 | Odd expert count |
| **f16 KV, top-5** | **18.52** | **Recommended ceiling** |

### Why f16 KV beats q8_0 here

GLM-DSA uses MLA (multi-head latent attention). The per-token KV footprint is already
small. The per-step dequant cost of q8_0 KV exceeds the bandwidth saved by the smaller
representation. Use `-ctk`/`-ctv` only if you are memory-starved, not for speed.

### Why top-5 experts (LExI-style override)

MoE routing normally activates 8 experts per token. `--override-kv
glm-dsa.expert_used_count=int:5` reduces expert weight traffic per token with coherent
output on this model. **Use odd values (5, 7).** Some even values (6, 8) hit allocation
edge cases on certain llama.cpp RPC builds and can crash or garble.

### What does *not* help on 2-box RPC

- **MTP / speculative decoding** (`glmdsa-mtp.patch`): accept-len ~2.9 single-box, but
  batched verification on the sparse-MoE RPC split increases cross-link expert traffic
  enough to erase the draft benefit. Skip for ceiling 2-box runs.
- **Higher batch (`-b`/`-ub`)**: decode is single-sequence (`--parallel 1`). Larger
  micro-batches do not help latency-bound token generation here.
- **Dual TB5 cables in parallel**: llama.cpp RPC uses one TCP socket. A second cable is
  for **failover**, not bandwidth aggregation. Use one link at a time; pin stable bridge
  IPs on both cables (see `cluster.env`).

## Recommended ceiling flags (`serve.sh`)

```
-ngl 999 --no-mmap -fa on -c 16384 --parallel 1 -b 256 -ub 256
KV_TYPE=f16
N_EXPERT_USED=5
--device RPC0,MTL0 --rpc NODE1_IP:50052
```

## Thunderbolt / dual-cable setup

1. Connect **both** TB5 cables (redundancy). Pick one bridge as **primary** (`NODE1_IP`),
   the other as **backup** (`NODE1_IP_BACKUP`).
2. Assign static link-local or RFC1918 IPs on each bridge (they drift after sleep).
   Use `LINK_PIN_CMD` / `LINK_PIN_CMD_BACKUP` in `cluster.env` if needed.
3. RPC traffic must use the **fast link IP**, not Wi‑Fi or Ethernet.
4. `scripts/lib.sh` pings primary first, then fails over to backup before aborting.

## Memory gates (do not skip)

- NODE1 needs **≥90 GiB free** before the serve load (`MIN_FREE_GB`). A busy or
  just-booted worker with stranded Metal residency will crash RPC mid-decode.
- Reboot NODE1 if teardown does not return free RAM to idle levels.
- Keep the GGUF on **internal SSD** on NODE0; copy shards once, do not stream from
  external enclosures during serve.

## Required patch

`patches/ggml-rpc-stability.patch` — without it, deep MoE graphs overflow the macOS
~512 KiB thread stack in RPC graph deserialization. Symptom: worker silently closes the
socket; coordinator dies at `set_tensor`. You will never reach ceiling speed with a
crashing worker.

## Measurement

```sh
# Quick (bar > 10 t/s):
scripts/verify.sh

# Ceiling proof (bar > 17 t/s, 5 warm passes):
THRESHOLD=17.0 PASSES=5 scripts/verify.sh

# One-shot launch + verify:
scripts/ceiling.sh
```

First pass after cold load is always slower — discard it. Report the best of passes 2+.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| ~1–3 tok/s, disk LED active | SSD streaming / single box | Enable 2-box RPC; confirm ~100GB+ RAM used on **each** Mac |
| RPC smoke fails | Wrong IP, worker down, patch missing | `scripts/preflight.sh`; check `/tmp/moe2box-rpc.log` on NODE1 |
| Garbled output | Even expert count or corrupt quant | Use `N_EXPERT_USED=5`; re-download GGUF |
| 8–12 tok/s | Suboptimal KV/experts or memory pressure | `KV_TYPE=f16 N_EXPERT_USED=5`; reboot NODE1 |
| Passes then crash | NODE1 memory leak / no patch | Apply stability patch; clean teardown between runs |
