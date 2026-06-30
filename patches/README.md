# Patches

Apply against a pinned known-good `llama.cpp` checkout for reproducibility, then build with
`cmake -B build -DGGML_METAL=ON -DGGML_RPC=ON -DGGML_BLAS=OFF && cmake --build build -j`.
Build on **both** nodes from the same source (or build once and copy the whole `build/bin/`
**including the dylibs** — see "Binary parity" in the root README).

## `ggml-rpc-stability.patch` — the one worth upstreaming
Rewrites the **recursive** `add_tensor` and `create_node` in `ggml/src/ggml-rpc/ggml-rpc.cpp`
into **iterative (explicit-stack)** versions. A deep MoE graph (tens of thousands of nodes)
overflows the ~512 KiB macOS thread stack when these recurse; the worker then closes the RPC
socket mid-transfer and the coordinator aborts at `set_tensor` / `get_alloc_size`. The iterative
versions preserve the intended reachable-node materialization and wiring for normal graph
deserialization (functionally equivalent, not bit-exact internal ordering). The patch is tightly
scoped and genuinely upstreamable; if you run any large MoE over llama.cpp RPC on macOS, you likely
want this regardless of the rest of this repo.

## `glmdsa-mtp.patch` — nextn MTP self-speculative head for the GLM-DSA arch (optional)
Wires the model's NextN/MTP block as a real `LLM_GRAPH_TYPE_DECODER_MTP` draft head (MLA + MoE).
Single-box it drafts well (measured accept-len ~2.9). **But on this sparse-MoE RPC split, batched
verification raises active-expert weight traffic/work enough to erase the draft benefit.** Included
for the single-box case and for reference; see `docs/FINDINGS.md`. Touches
`src/models/glm-dsa.cpp`, `src/models/models.h`. Arch-specific — adapt the block builder for other
architectures.
