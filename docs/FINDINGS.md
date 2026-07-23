# Findings: GLM-5.2 tok/s on 2× M5 Max 128GB

This note answers the practical question behind this repo:

> We are on DwarfStar (antirez `ds4`) with SSD streaming at roughly a **64 GB expert
> cache per M5 Mac**, seeing about **~3 tok/s**. Can we get to **~10+ tok/s**? What does
> the physics allow?

Short answer: **yes — but not by tuning the SSD cache.** At ~3 tok/s you are disk-bound.
The step that crosses ~10 tok/s is making the **routed experts memory-resident across both
Macs** (DwarfStar tensor-parallel over Thunderbolt, or this repo’s llama.cpp RPC
pipeline-parallel). Antirez’s own numbers on the same class of hardware already clear that
bar (~16.8 tok/s TP). This repo’s tuned llama.cpp path lands around **15.6 → 18.5 tok/s**.

---

## Hardware context (your box)

| Piece | Role |
|---|---|
| 2× Apple M5 Max, 128 GB unified each | Compute + residency budget (~256 GB pooled) |
| Internal 2 TB SSD each | Best place for the GGUF (random expert reads) |
| Lexar NM790 4 TB in an external enclosure | Capacity disk; fine for holding weights, weaker for hot expert streaming |
| Thunderbolt 5 cable between Macs | Required for any 2-box decode that hopes to beat streaming |

“64×64” in this note means the practical DwarfStar SSD-streaming knobs people land on for a
128 GB M5 Max: around a **64 GB routed-expert cache** (docs recommend starting ~48–64 GB;
auto often picks ~59 GB for PRO-class streaming). Same idea applies per Mac if you run
streaming on each node independently.

---

## Physics of one decode token

GLM-5.2 is a huge MoE (~753 B params, ~40 B active/token, 256 experts/layer, MLA/`glm-dsa`).
Per generated token the engine must:

1. Run attention + shared / dense weights (stay resident — small compared to experts).
2. Route and **read the selected experts for every MoE layer**.
3. Produce logits and sample.

Decode is almost never “compute limited” on an M5 Max for these quants. It is limited by
**how fast you can feed the next expert weights into the GPU**:

| Where the experts live | Binding constraint | Realistic decode band |
|---|---|---|
| Cold / thrashing SSD stream | NVMe random read + PCIe/enclosure latency | **~1–3 tok/s** |
| Warm SSD stream, good cache hit rate, internal SSD | Still some misses every token | **~4–5 tok/s** (antirez: **~4.8** for GLM 5.2 IQ2_XXS on one M5 Max 128 GB) |
| Fully resident on one machine | Unified memory bandwidth | Needs the whole model to fit (it does not at useful quants on 128 GB) |
| Fully resident **split across two Macs** | Memory bandwidth + a small cross-box sync | **~15–18 tok/s** on this hardware class |

Rough bandwidth intuition for streaming:

- Active expert traffic per token is on the order of **several to ~10+ GB** when many layers
  miss cache (depends on quant, top-k, and hit rate).
- An external Gen4 SSD in a Thunderbolt/USB4 enclosure often tops out around **~3 GB/s**
  sequential and is worse on the **small random reads** expert streaming actually does.
  Internal Apple SSD is the better hot path.
- At 3 GB/s sustained useful expert traffic you are already in the **low single-digit tok/s**
  regime. That matches “~3 tok/s with a 64 GB cache + Lexar enclosure” without needing a
  mysterious software bug.

So: **you will not climb from 3 → 10 by buying a faster enclosure or bumping the cache from
64 GB to 75 GB.** Cache tuning moves you inside the streaming band (~3–5). Crossing ~10
requires **removing the disk from the per-token critical path**.

---

## What antirez already measured (same machine class)

From the DwarfStar README, GLM 5.2 IQ2_XXS (~188 GiB) on **two M5 Max 128 GB MacBooks**:

| Mode | Decode | Prefill (4k) | Residency |
|---|---|---|---|
| One Mac, `--ssd-streaming` | **~4.8 tok/s** | ~3–5 tok/s | streams experts from SSD |
| Two Macs, `--tensor-parallel` over TB5/RDMA | **~16.8 tok/s** (15.4 at 4k ctx) | **~94 tok/s** | fully memory-resident (half the experts on each Mac) |

That is the “someone got ~10+” data point, with margin. Your ~3 tok/s is a **worse streaming
run** of the left column, not evidence that 10 is unreachable.

---

## Path A — stay on DwarfStar, go tensor-parallel (recommended first try)

Goal: keep using `ds4`, but stop streaming experts every token.

### Why TP works here

- Each Mac keeps **one contiguous half of the routed experts** resident (~97.5 GiB expert
  shard + dense/KV/scratch).
- Dense, attention, shared-expert, embed, and output weights are **replicated**.
- Both GPUs work on the **same token**; they exchange only **16–24 KB** partial sums per sync
  gate (RDMA over Thunderbolt when available).
- Unlike pipeline-distributed generation, TP is trying to cut **per-token latency**, not just
  fit a bigger model.

### One-time per boot (both Macs)

```sh
# Raise Metal wired limit so the resident expert shard can pin (~117 GB headroom).
sudo sysctl iogpu.wired_limit_mb=120000

# Put an IPv4 address on the Thunderbolt *member* interface (not the bridge).
# Example — adjust enX to whatever ifconfig shows as active for the TB5 cable:
sudo ifconfig en1 inet 10.99.0.2/30 alias   # coordinator
sudo ifconfig en6 inet 10.99.0.1/30 alias   # worker
```

Confirm RDMA is actually up (`rdma_ctl status`, `ibv_devinfo -v`). A working IP ping is not
enough; you need the IPv4-mapped GID on the verbs device. Fall back with `--transport tcp` on
both sides if RDMA will not come up (slower sync, still usually far above SSD streaming).

### Launch (same commit + same GGUF path on both)

```sh
MODEL=gguf/GLM-5.2-UD-IQ2_XXS_RoutedIQ2XXS_blk78Q2K.gguf

# Worker first:
./ds4 -m "$MODEL" --tensor-parallel --role worker \
  --coordinator 10.99.0.2 9911 --transport rdma

# Coordinator:
./ds4 -m "$MODEL" --tensor-parallel --role coordinator \
  --listen 10.99.0.2 9911 --transport rdma -c 8192 \
  -p "Tell me something about the sea."
```

Expect ~9 s/side to pre-fault and pin the ~100 GiB shard. Do **not** pass `--layers` in TP
mode (always a 50/50 split). TP is currently a `ds4` CLI feature, not `ds4-server` /
`ds4-agent`.

### Expected result

If residency succeeds and the TB5 link is healthy: **~15–17 tok/s decode**, i.e. past 10 with
headroom. If you still see ~3–5, you are still streaming (check startup: expert shards must
report resident / locked, not SSD-miss dominated).

---

## Path B — this repo (llama.cpp Metal + RPC, pipeline-parallel)

This repository’s launcher splits the IQ1_S Unsloth GGUF (~202 GB) across the two Macs with
llama.cpp RPC (`--device RPC0,MTL0`), Metal on both, one Thunderbolt 5 cable.

Measured here (warm decode, short prompt):

| Config | tok/s |
|---|---|
| q8_0 KV, top-8 experts | 15.6 |
| f16 KV, top-8 | 16.67 |
| f16 KV, top-7 | 17.31 |
| **f16 KV, top-5 (recommended)** | **18.52** |

Two free wins, no new model code:

1. **KV in f16 beats q8_0** on this MLA KV (dequant cost > savings from the smaller read).
2. **Drop `expert_used_count` from 8 → 5** (odd values only on some builds; see launcher notes).

```sh
KV_TYPE=f16 N_EXPERT_USED=5 CTX=16384 scripts/launch.sh
scripts/verify.sh   # bar defaults to >10 tok/s
```

Required patches live in `patches/` (RPC stack-overflow fix for deep MoE graphs on macOS;
optional glm-dsa MTP). Build with `GGML_METAL=ON GGML_RPC=ON GGML_BLAS=OFF` and keep **binary
parity** on both nodes (including dylibs).

MTP / self-speculation helps on a **single** box (accept-len ~2.9 measured) but on this
sparse-MoE RPC split, batched verification raises active-expert traffic enough to erase the
draft gain. Leave MTP off for the 2-box speed path.

---

## What will *not* get you from 3 → 10

| Idea | Why it stalls |
|---|---|
| Bigger `--ssd-streaming-cache-experts` (64 → 75 GB) | Still streaming; antirez saw auto ~59 GB ≈ manual 64–75 on M5 Max. Gains are small and risk paging. |
| Faster external enclosure alone | Enclosure sequential ~3 GB/s ceiling; expert traffic is random. Moves 3→ maybe ~4–5, not 10. |
| Running streaming on *each* Mac separately | Two independent ~3–5 tok/s sessions ≠ one 10 tok/s decode. |
| Pipeline-distributed generation for speed | Fits bigger models / helps **prefill**; autoregressive decode pays a hop every token and is usually **slower** than single-process (Flash Q4 example: 30.6 → 24.7 tok/s). |
| Expecting MTP/DSpark to save a streaming run | Speculation multiplies expert verification traffic; bad fit when experts already miss to disk. |

---

## Practical checklist to leave the ~3 tok/s regime

1. **Put the hot GGUF on internal SSD** (or accept that Lexar-in-enclosure is a capacity tier).
2. **One Thunderbolt 5 cable** between the two Macs; pin IPs on the member interfaces.
3. Prefer **DwarfStar `--tensor-parallel` + RDMA** *or* **this repo’s RPC launcher** — both make
   experts resident. Do not mix “streaming on both boxes” with a hope of TP-class speed.
4. Raise `iogpu.wired_limit_mb` before resident loads so Metal can pin the shard.
5. Confirm you are measuring **warm decode** (discard the first pass; `scripts/verify.sh` does).
6. Keep context modest while validating speed (`-c 8192` / `CTX=16384`); long context taxes KV
   and can look like a regression even when weights are resident.
7. For llama.cpp path: `KV_TYPE=f16` and `N_EXPERT_USED=5`.

---

## Bottom line

| Setup | Decode you should believe |
|---|---|
| DwarfStar SSD streaming, ~64 GB cache, weights on enclosure | **~3 tok/s** (your number) — expected |
| DwarfStar SSD streaming, tuned, internal SSD | **~4.8 tok/s** — streaming ceiling on one 128 GB M5 Max |
| DwarfStar TP over TB5 on both 128 GB M5 Maxes | **~16.8 tok/s** — clears 10 |
| This repo, llama.cpp RPC, f16 KV, top-5 | **~18.5 tok/s** — clears 10 |

The physics says the leap is **residency via two-box split**, not a cleverer SSD cache.
Once experts stop coming from disk every token, 10 tok/s is not aspirational on this
hardware — it is the conservative half of the measured band.
