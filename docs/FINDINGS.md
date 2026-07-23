# Findings: GLM-5.2 tok/s on 2× M5 Max 128GB

This note answers the practical question behind this repo:

> We are on DwarfStar (antirez `ds4`) with SSD streaming at roughly a **64 GB expert
> cache per M5 Mac**, seeing about **~3 tok/s**. Can we get to **~10+ tok/s**? What does
> the physics allow?

Short answer: **If Q4 is non-negotiable, ~10 tok/s is not available on 2×128 GB.**

At ~3 tok/s you are disk-bound. Crossing ~10 requires making routed experts **memory-resident**.
A Q4 GLM GGUF is **~406–467 GB**. Two 128 GB Macs only pool **256 GB**, so Q4 **cannot
fully reside** here. DwarfStar also **rejects routed Q4 for tensor-parallel**. Antirez’s
**~16.8 tok/s** is **IQ2_XXS**, not Q4. Keeping Q4 means either **more pooled unified memory**
(the real path to ~10+) or accepting the **streaming band (~few tok/s)** and squeezing it.

---

## Hardware context (your box)

| Piece | Role |
|---|---|
| 2× Apple M5 Max, 128 GB unified each | Compute + residency budget (~256 GB pooled) |
| Internal 2 TB SSD each | Best place for the GGUF (random expert reads) |
| Lexar NM790 4 TB in an external enclosure | Capacity disk; fine for holding weights, weaker for hot expert streaming |
| Thunderbolt 5 cable between Macs | Required for any 2-box decode that hopes to beat streaming |

“64×64 on each one” in this note means the intentional **SSD expert-streaming** setup on
**each** M5 Max: the practical DwarfStar knobs people land on around **`--ssd-streaming-cache-experts 64GB`**
(and/or **`--ssd-streaming-full-layers`** derived from that budget — docs recommend starting
~48–64 GB). Same streaming recipe on both boxes. That is **not** full model residency.

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

## Q4 vs Q2 — the important correction

If you are on **Q4** and comparing to antirez’s speed posts, you are not on the same quant.

| GGUF | On-disk size | Fits resident in 2×128 GB? | DwarfStar 2-Mac TP? |
|---|---|---|---|
| antirez **IQ2_XXS** (the ~16.8 tok/s post) | **~211 GB** | Yes (with TP expert split) | **Yes** (ownership-aware) |
| antirez **Q2_K** | **~262 GB** | Borderline (dense is replicated) | **Yes** (ownership-aware) |
| antirez **Q4_K** | **~434 GB** | **No** (≫ 256 GB) | **Rejected before eval** |
| Unsloth **UD-Q4_K_XL** | **~467 GB** | **No** | Streaming / normal Metal only |
| This repo **IQ1_S** (Unsloth) | **~202–217 GB** | Yes via llama.cpp RPC split | N/A (use this repo’s launcher) |

From DwarfStar’s own README:

> Two-Mac tensor parallelism currently requires an ownership-aware IQ2_XXS or Q2_K routed
> layout; **a routed Q4 GLM must be rejected before evaluation.**

### Why your Q4 streaming is ~3 tok/s (and his Q2 looks faster)

- Same 64 GB expert cache holds **~half as many Q4 experts** as Q2/IQ2.
- Each cache miss moves **~2× the bytes**.
- Hit rate drops and disk work per token rises → landing around **~3 tok/s** on an enclosure
  is consistent; his **~4.8 tok/s** streaming ceiling is the **IQ2_XXS** curve, not Q4.

**You cannot expect his ~16.8 tok/s number while remaining on Q4 with 2×128 GB.** That number
is a fully-resident IQ2_XXS tensor-parallel run.

### Paths if you want ≥10 tok/s

1. **Keep DwarfStar, drop to IQ2_XXS or Q2_K, enable `--tensor-parallel`** → expect ~15–17 tok/s
   on TB5/RDMA (measured ~16.8 on IQ2_XXS). Quality tradeoff vs Q4.
2. **Keep this hardware, switch to this repo’s IQ1_S + llama.cpp RPC** → measured **~18.5 tok/s**.
   Also a heavier quant drop than Q4, but the residency math works.
3. **Stay on Q4 for quality** → you need **more unified memory** (roughly ≥512 GB pooled for a
   true resident Q4-class MoE), or accept streaming (~few tok/s). Pipeline-parallel across the
   two 128 GB Macs cannot hide a 430 GB+ weight set.

---

## Q4 is non-negotiable — what that actually implies

Constraint: **do not drop below Q4** for work quality.

Then the speed problem is no longer “tune DwarfStar.” It is **capacity arithmetic**:

| Pooled unified memory | Can Q4 (~406–467 GB) be fully resident? | Realistic decode |
|---|---|---|
| **2×128 GB = 256 GB** (your box) | **No** (~150–210 GB short) | SSD streaming: **~3 tok/s** now; maybe **~4–5** if everything is optimized |
| **2×256 GB = 512 GB** (e.g. two M3/M5 Ultra 256 GB class) | **Yes** with llama.cpp RPC / layer split (~200 GiB/node reported for UD-Q4_K_S) | This is the hardware class where **resident Q4 ~10+ tok/s** becomes plausible |
| **4×128 GB = 512 GB** | **Yes** if you pipeline-split layers across four boxes | Same residency idea; more sync hops than 2×256 |
| One **512 GB+** Mac | **Yes** single-node | Simplest ops; no RPC |

People already run **Unsloth UD-Q4_K_S (~406 GB)** resident across **two 256 GB Mac Studios** via
llama.cpp RPC (~205 GiB weights/node under a ~248 GiB wired cap). That is the existence proof
that **Q4 + ~10-class decode needs ~512 GB pooled**, not 256 GB.

On your current 2×128 GB kit, staying on Q4 means:

### What you can still do (streaming squeeze — not a path to 10)

These only move you inside the streaming band:

1. **Hot GGUF on internal SSD**, not the Lexar enclosure (enclosure = capacity tier).
2. Prefer **automatic** `--ssd-streaming` budget; if manual, stay around **48–64 GB** expert
   cache and watch that the cache stays lockable (overshoot → paging → slower than 3).
3. Let GLM keep the largest **full-layer prefix** resident (`--ssd-streaming-full-layers` auto);
   don’t starve KV/scratch to inflate the expert cache.
4. Raise `iogpu.wired_limit_mb` so Metal can pin what does fit.
5. Measure **warm** decode only; long context and thinking mode both look slower.

Honest ceiling on 2×128 GB + Q4: **low single digits**. Software will not invent the missing
~200 GB of unified memory.

### What actually gets Q4 to ~10+

Pick one capacity upgrade (quant stays Q4):

1. **Replace / add memory class:** two machines with **≥256 GB each**, Thunderbolt link,
   llama.cpp RPC (or future ds4 Q4 TP if it ever lands) so each node holds ~half the Q4
   weights fully resident.
2. **Add boxes at 128 GB:** enough nodes that layer slices sum to ≥~450 GB resident (typically
   **four** 128 GB Macs), accepting more pipeline hops.
3. **One big box:** a **512 GB+** Mac Studio-class machine and skip the cluster.

Until one of those is true, treat “~10 tok/s on Q4” as a **hardware purchase target**, not a
config flag.

---

## “64×64 on each Mac” — streaming experts on purpose

Yes: the working design is **not** “fit all Q4 weights in RAM.” It is:

- dense / shared / attention resident where possible
- **routed experts streamed from SSD** into a ~**64 GB** (per Mac) dynamic cache
- optionally a **full-layer prefix** kept resident from the same budget
- and you run that recipe **on each** of the two M5 Maxes

That is exactly DwarfStar’s SSD-streaming mode. It does **not** change the decode ceiling
the way people hope when they hear “two machines × 64 GB.”

### What 64 GB of expert cache actually buys (Q4)

Rough Q4 arithmetic (~434 GB antirez Q4_K, ~78 MoE layers × 256 experts):

| Budget on one 128 GB Mac | About what it holds |
|---|---|
| **64 GB dynamic expert cache** | ~3k experts ≈ **~17%** of all routed experts |
| **64 full MoE layers** (if taken literally) | ~**300 GB+** — **does not fit**; ds4 will cap full-layers from the byte budget |
| 64 GB as full-layer budget | only ~**13** full layers resident, rest still stream |

So “64×64” is a **large cache relative to RAM**, not a large cache relative to the **Q4 expert
set**. Most experts still live on disk. Every decode token that misses still pays NVMe.

### Why “on each one” does not 2× the tok/s

Decode is **one token at a time**:

| How the two Macs are used | What happens to tok/s |
|---|---|
| Two independent streaming sessions (64 GB cache each) | Two chats at ~3 tok/s each — **not** one chat at 6–10 |
| One decode, layer-split across both, each side still SSD-streaming its experts | Still **disk-bound on every hop**; extra Mac adds sync cost, does not remove expert I/O |
| One decode, experts **fully resident** (needs ~512 GB pooled for Q4) | Leaves the streaming regime — this is the ~10+ path |

Two × 64 GB caches are **not** one 128 GB shared expert working set for a single token.
Each process only sees its own cache. Misses still read the Lexar/internal SSD.

### So does streaming-with-64×64 get you to 10?

**No.** It is the mechanism that *produces* ~3 tok/s on Q4. Tuning 64→75 GB or mirroring
the same flags on the second Mac stays inside the streaming band (maybe ~4–5 if the hot
GGUF is on internal SSD and the cache stays lockable). **~10 tok/s on Q4 still requires
enough pooled RAM to stop streaming experts every token** (~512 GB class), as in the
section above.

---

## What antirez already measured (same machine class, **IQ2_XXS**)

From the DwarfStar README, GLM 5.2 **IQ2_XXS** (~188 GiB) on **two M5 Max 128 GB MacBooks**:

| Mode | Decode | Prefill (4k) | Residency |
|---|---|---|---|
| One Mac, `--ssd-streaming` | **~4.8 tok/s** | ~3–5 tok/s | streams experts from SSD |
| Two Macs, `--tensor-parallel` over TB5/RDMA | **~16.8 tok/s** (15.4 at 4k ctx) | **~94 tok/s** | fully memory-resident (half the experts on each Mac) |

That is the “someone got ~10+” data point — **on Q2-class weights**. A Q4 streaming run at
~3 tok/s is a different regime, not a failed attempt at that number.

---

## Path A — DwarfStar tensor-parallel (**IQ2_XXS / Q2_K only**)

Goal: keep using `ds4`, but stop streaming experts every token.

**Prerequisite:** use an ownership-aware **IQ2_XXS or Q2_K** GGUF. Routed **Q4 is rejected**
for TP. If you stay on Q4, skip to “stay on Q4” above — Path A will not start.

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
| Stay on **Q4** and chase antirez’s ~16.8 number | That number is **IQ2_XXS TP**. Q4 is ~434 GB, won’t reside in 256 GB, and ds4 **rejects** Q4 for TP. |
| Bigger `--ssd-streaming-cache-experts` (64 → 75 GB) | Still streaming; antirez saw auto ~59 GB ≈ manual 64–75 on M5 Max. Gains are small and risk paging. |
| Faster external enclosure alone | Enclosure sequential ~3 GB/s ceiling; expert traffic is random. Moves 3→ maybe ~4–5 on Q2, still worse on Q4. |
| Running streaming on *each* Mac separately | Two independent ~3 tok/s Q4 sessions ≠ one 10 tok/s decode. |
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
| **Q4** + 2×128 GB + SSD streaming (you, now) | **~3 tok/s** — expected; maybe ~4–5 if tuned |
| **Q4** + ~512 GB pooled, weights resident (2×256 or 4×128) | **The real path to ~10+ while keeping Q4** |
| DwarfStar **IQ2_XXS** TP on 2×128 GB | **~16.8 tok/s** — faster, but below your Q4 floor |
| This repo **IQ1_S** RPC on 2×128 GB | **~18.5 tok/s** — faster, but below your Q4 floor |

With **Q4 locked**, the missing ingredient is **~200 GB more pooled unified memory**, not a
better SSD-cache knob. On the current two 128 GB Macs, plan for low-single-digit tok/s and
treat a 2×256 GB (or equivalent) upgrade as the requirement for work-speed Q4.
