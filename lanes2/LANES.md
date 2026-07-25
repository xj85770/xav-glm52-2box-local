# lanes2 lanes

Type a **lane** to auto-swap across its populated cards, or an exact **card id**.

## `lane/local`  (2/3 ready)

Private local GLM (ds4 :8000 → llama.cpp :8080).
Aliases: `lane-local`, `local`

| order | ready | id | display | ctx | t/s | rpd | tok left/day | key |
|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | YES | `local/ds4` | GLM-5.2 via ds4-server | 131072 | 3.0 |  |  | LOCAL_API_KEY |
| 2 | YES | `local/llama` | GLM-5.2 via llama.cpp RPC | 131072 | 18.5 |  |  | LOCAL_API_KEY |
| 3 | no-key | `cf/glm-5.2` | CF GLM-5.2 | 131072 | 25 |  |  | CLOUDFLARE_API_TOKEN |

## `lane/fast`  (2/31 ready)

Burst chat: Groq → Cerebras → OpenRouter free-small.
Aliases: `fast`, `lane-fast`

| order | ready | id | display | ctx | t/s | rpd | tok left/day | key |
|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | no-key | `gemini/2.5-flash-lite` | Gemini 2.5 Flash-Lite | 1048576 | 120 | 20 |  | GEMINI_API_KEY |
| 1 | no-key | `gemini/3.1-flash-lite` | Gemini 3.1 Flash-Lite | 1048576 | 120 | 500 |  | GEMINI_API_KEY |
| 1 | no-key | `groq/llama-3.1-8b` | Groq Llama 3.1 8B | 131072 | 500 | 14400 |  | GROQ_API_KEY |
| 1 | no-key | `groq/llama-3.3-70b` | Groq Llama 3.3 70B | 131072 | 200 | 1000 |  | GROQ_API_KEY |
| 2 | no-key | `cerebras/gpt-oss-120b` | Cerebras GPT-OSS 120B | 65536 | 1000 | 14400 | 1000000 | CEREBRAS_API_KEY |
| 2 | no-key | `cerebras/llama3.1-8b` | Cerebras Llama 3.1 8B | 8192 | 1800 | 14400 | 1000000 | CEREBRAS_API_KEY |
| 2 | no-key | `gemini/3-flash` | Gemini 3 Flash | 1048576 | 100 | 20 |  | GEMINI_API_KEY |
| 2 | no-key | `groq/gpt-oss-20b` | Groq GPT-OSS 20B | 131072 | 400 | 1000 |  | GROQ_API_KEY |
| 3 | no-key | `gemini/gemma-3-12b` | Gemma 3 12B Instruct | 131072 | 80 | 14400 |  | GEMINI_API_KEY |
| 3 | no-key | `gemini/gemma-3-27b` | Gemma 3 27B Instruct | 131072 | 60 | 14400 |  | GEMINI_API_KEY |
| 3 | no-key | `or/llama-3.3-70b` | Llama 3.3 70B Instruct | 131072 | 40 | 50 |  | OPENROUTER_API_KEY |
| 4 | no-key | `gemini/gemma-3-4b` | Gemma 3 4B Instruct | 131072 | 120 | 14400 |  | GEMINI_API_KEY |
| 4 | no-key | `or/gpt-oss-20b` | OpenAI GPT-OSS 20B | 131072 | 60 | 50 |  | OPENROUTER_API_KEY |
| 4 | no-key | `or/nemotron-3-nano-30b` | Nemotron 3 Nano 30B | 131072 | 55 | 50 |  | OPENROUTER_API_KEY |
| 5 | no-key | `mistral/small` | Mistral Small | 128000 | 80 |  |  | MISTRAL_API_KEY |
| 5 | no-key | `or/llama-3.2-3b` | Llama 3.2 3B Instruct | 131072 | 80 | 50 |  | OPENROUTER_API_KEY |
| 6 | no-key | `cohere/command-r7b` | Command R7B | 128000 | 90 | 34 |  | COHERE_API_KEY |
| 6 | no-key | `or/gemma-4-26b` | Gemma 4 26B A4B IT | 131072 | 50 | 50 |  | OPENROUTER_API_KEY |
| 7 | no-key | `or/nemotron-nano-9b` | Nemotron Nano 9B V2 | 131072 | 70 | 50 |  | OPENROUTER_API_KEY |
| 8 | no-key | `or/laguna-xs` | Poolside Laguna XS 2.1 | 65536 | 70 | 50 |  | OPENROUTER_API_KEY |
| 9 | no-key | `nim/default` | NVIDIA NIM open models | 32768 | 40 |  |  | NVIDIA_API_KEY |
| 10 | no-key | `hf/llama-3.1-8b` | HF Llama 3.1 8B Instruct | 131072 | 30 |  |  | HF_TOKEN |
| 11 | no-key | `zen/deepseek-v4-flash` | DeepSeek V4 Flash Free (Zen) | 131072 | 80 |  |  | OPENCODE_ZEN_API_KEY |
| 12 | no-key | `groq/allam-2-7b` | Groq Allam 2 7B | 8192 | 400 | 7000 |  | GROQ_API_KEY |
| 13 | no-key | `github/phi-4` | GitHub Phi-4 | 16384 | 70 | 50 |  | GITHUB_TOKEN |
| 14 | no-key | `cf/gpt-oss-20b` | CF GPT-OSS 20B | 131072 | 40 |  |  | CLOUDFLARE_API_TOKEN |
| 15 | no-key | `fw/llama-3.3-70b` | Fireworks Llama 3.3 70B | 131072 | 120 |  |  | FIREWORKS_API_KEY |
| 16 | no-key | `hyp/llama-3.3-70b` | Hyperbolic Llama 3.3 70B | 131072 | 50 |  |  | HYPERBOLIC_API_KEY |
| 17 | no-key | `snova/llama-3.3-70b` | SambaNova Llama 3.3 70B | 131072 | 100 |  |  | SAMBANOVA_API_KEY |
| 99 | YES | `local/ds4` | GLM-5.2 via ds4-server | 131072 | 3.0 |  |  | LOCAL_API_KEY |
| 100 | YES | `local/llama` | GLM-5.2 via llama.cpp RPC | 131072 | 18.5 |  |  | LOCAL_API_KEY |

## `lane/smart`  (2/59 ready)

Best free reasoning: Gemini → OpenRouter free-big → local.
Aliases: `lane-smart`, `smart`

| order | ready | id | display | ctx | t/s | rpd | tok left/day | key |
|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | no-key | `gemini/2.5-flash` | Gemini 2.5 Flash | 1048576 | 100 | 20 |  | GEMINI_API_KEY |
| 1 | no-key | `gemini/3-flash` | Gemini 3 Flash | 1048576 | 100 | 20 |  | GEMINI_API_KEY |
| 1 | no-key | `gemini/3.5-flash` | Gemini 3.5 Flash | 1048576 | 90 | 20 |  | GEMINI_API_KEY |
| 2 | no-key | `gemini/3.1-flash-lite` | Gemini 3.1 Flash-Lite | 1048576 | 120 | 500 |  | GEMINI_API_KEY |
| 2 | no-key | `or/hermes-3-405b` | Hermes 3 Llama 3.1 405B | 131072 | 25 | 50 |  | OPENROUTER_API_KEY |
| 2 | no-key | `or/nemotron-3-super-120b` | Nemotron 3 Super 120B | 131072 | 30 | 50 |  | OPENROUTER_API_KEY |
| 2 | no-key | `or/qwen3-next-80b` | Qwen3 Next 80B A3B Instruct | 131072 | 35 | 50 |  | OPENROUTER_API_KEY |
| 3 | no-key | `gemini/gemma-3-27b` | Gemma 3 27B Instruct | 131072 | 60 | 14400 |  | GEMINI_API_KEY |
| 3 | no-key | `groq/llama-3.3-70b` | Groq Llama 3.3 70B | 131072 | 200 | 1000 |  | GROQ_API_KEY |
| 3 | no-key | `or/nemotron-3-nano-omni` | Nemotron 3 Nano Omni 30B Reasoning | 131072 | 40 | 50 |  | OPENROUTER_API_KEY |
| 4 | no-key | `groq/gpt-oss-120b` | Groq GPT-OSS 120B | 131072 | 300 | 1000 |  | GROQ_API_KEY |
| 4 | no-key | `groq/qwen3.6-27b` | Groq Qwen 3.6 27B | 131072 | 250 | 1000 |  | GROQ_API_KEY |
| 4 | no-key | `mistral/large` | Mistral Large | 128000 | 50 |  |  | MISTRAL_API_KEY |
| 4 | no-key | `mistral/small` | Mistral Small | 128000 | 80 |  |  | MISTRAL_API_KEY |
| 5 | no-key | `cerebras/gpt-oss-120b` | Cerebras GPT-OSS 120B | 65536 | 1000 | 14400 | 1000000 | CEREBRAS_API_KEY |
| 5 | no-key | `or/llama-3.3-70b` | Llama 3.3 70B Instruct | 131072 | 40 | 50 |  | OPENROUTER_API_KEY |
| 6 | no-key | `cohere/command-a` | Command A 03-2025 | 256000 | 60 | 34 |  | COHERE_API_KEY |
| 6 | no-key | `or/dolphin-mistral-24b` | Dolphin Mistral 24B Venice | 32768 | 45 | 50 |  | OPENROUTER_API_KEY |
| 7 | no-key | `cohere/command-r7b` | Command R7B | 128000 | 90 | 34 |  | COHERE_API_KEY |
| 7 | no-key | `or/gemma-4-26b` | Gemma 4 26B A4B IT | 131072 | 50 | 50 |  | OPENROUTER_API_KEY |
| 8 | no-key | `cohere/command-r-plus` | Command R+ | 128000 | 50 | 34 |  | COHERE_API_KEY |
| 8 | no-key | `or/gemma-4-31b` | Gemma 4 31B IT | 131072 | 45 | 50 |  | OPENROUTER_API_KEY |
| 9 | no-key | `or/nemotron-3-nano-30b` | Nemotron 3 Nano 30B | 131072 | 55 | 50 |  | OPENROUTER_API_KEY |
| 10 | no-key | `or/nemotron-3-ultra-550b` | Nemotron 3 Ultra 550B | 131072 | 15 | 50 |  | OPENROUTER_API_KEY |
| 11 | no-key | `or/nemotron-nano-12b-vl` | Nemotron Nano 12B V2 VL | 131072 | 50 | 50 |  | OPENROUTER_API_KEY |
| 12 | no-key | `or/laguna-m` | Poolside Laguna M.1 | 131072 | 40 | 50 |  | OPENROUTER_API_KEY |
| 13 | no-key | `or/hy3` | Tencent HY3 | 131072 | 40 | 50 |  | OPENROUTER_API_KEY |
| 14 | no-key | `nim/default` | NVIDIA NIM open models | 32768 | 40 |  |  | NVIDIA_API_KEY |
| 15 | no-key | `vercel/gateway-default` | Vercel AI Gateway (routed) | 128000 | 50 |  |  | VERCEL_AI_GATEWAY_TOKEN |
| 16 | no-key | `zen/nemotron-3-super` | Nemotron 3 Super Free (Zen) | 131072 | 40 |  |  | OPENCODE_ZEN_API_KEY |
| 17 | no-key | `github/gpt-4o-mini` | GitHub GPT-4o mini | 128000 | 50 | 50 |  | GITHUB_TOKEN |
| 18 | no-key | `github/llama-3.3-70b` | GitHub Llama 3.3 70B | 128000 | 40 | 50 |  | GITHUB_TOKEN |
| 19 | no-key | `cf/glm-5.2` | CF GLM-5.2 | 131072 | 25 |  |  | CLOUDFLARE_API_TOKEN |
| 20 | no-key | `cf/gpt-oss-120b` | CF GPT-OSS 120B | 131072 | 30 |  |  | CLOUDFLARE_API_TOKEN |
| 21 | no-key | `cf/llama-3.3-70b` | CF Llama 3.3 70B | 131072 | 35 |  |  | CLOUDFLARE_API_TOKEN |
| 22 | no-key | `cf/qwen3-30b` | CF Qwen3 30B | 131072 | 35 |  |  | CLOUDFLARE_API_TOKEN |
| 23 | no-key | `fw/llama-3.3-70b` | Fireworks Llama 3.3 70B | 131072 | 120 |  |  | FIREWORKS_API_KEY |
| 24 | no-key | `baseten/generic` | Baseten (deployed model) | 128000 | 40 |  |  | BASETEN_API_KEY |
| 25 | no-key | `nebius/llama-3.3-70b` | Nebius Llama 3.3 70B | 131072 | 50 |  |  | NEBIUS_API_KEY |
| 26 | no-key | `novita/llama-3.3-70b` | Novita Llama 3.3 70B | 131072 | 45 |  |  | NOVITA_API_KEY |
| 27 | no-key | `ai21/jamba-large` | AI21 Jamba Large | 256000 | 40 |  |  | AI21_API_KEY |
| 28 | no-key | `upstage/solar-pro` | Upstage Solar Pro | 32768 | 50 |  |  | UPSTAGE_API_KEY |
| 29 | no-key | `nlpcloud/default` | NLP Cloud open models | 32768 | 30 |  |  | NLPCLOUD_API_KEY |
| 30 | no-key | `alibaba/qwen-plus` | Qwen Plus (Model Studio) | 131072 | 50 |  | 1000000 | DASHSCOPE_API_KEY |
| 31 | no-key | `modal/openai-compat` | Modal OpenAI-compatible deploy | 128000 | 40 |  |  | MODAL_TOKEN_ID |
| 32 | no-key | `inference/llama-70b` | Inference.net Llama 70B | 131072 | 45 |  |  | INFERENCE_NET_API_KEY |
| 33 | no-key | `hyp/deepseek-v3` | Hyperbolic DeepSeek V3 0324 | 65536 | 40 |  |  | HYPERBOLIC_API_KEY |
| 34 | no-key | `hyp/llama-3.3-70b` | Hyperbolic Llama 3.3 70B | 131072 | 50 |  |  | HYPERBOLIC_API_KEY |
| 35 | no-key | `hyp/deepseek-r1` | Hyperbolic DeepSeek R1 | 65536 | 30 |  |  | HYPERBOLIC_API_KEY |
| 36 | no-key | `snova/deepseek-v3.2` | SambaNova DeepSeek V3.2 | 65536 | 80 |  |  | SAMBANOVA_API_KEY |
| 37 | no-key | `snova/llama-3.3-70b` | SambaNova Llama 3.3 70B | 131072 | 100 |  |  | SAMBANOVA_API_KEY |
| 38 | no-key | `snova/gpt-oss-120b` | SambaNova GPT-OSS 120B | 131072 | 90 |  |  | SAMBANOVA_API_KEY |
| 39 | no-key | `snova/gemma-4-31b` | SambaNova Gemma 4 31B | 131072 | 100 |  |  | SAMBANOVA_API_KEY |
| 40 | no-key | `scw/gemma-3-27b` | Scaleway Gemma 3 27B | 131072 | 40 |  | 1000000 | SCALEWAY_API_KEY |
| 41 | no-key | `scw/llama-3.3-70b` | Scaleway Llama 3.3 70B | 131072 | 40 |  | 1000000 | SCALEWAY_API_KEY |
| 42 | no-key | `scw/glm-5.2` | Scaleway GLM-5.2 | 131072 | 35 |  | 1000000 | SCALEWAY_API_KEY |
| 43 | no-key | `scw/gpt-oss-120b` | Scaleway GPT-OSS 120B | 131072 | 40 |  | 1000000 | SCALEWAY_API_KEY |
| 99 | YES | `local/ds4` | GLM-5.2 via ds4-server | 131072 | 3.0 |  |  | LOCAL_API_KEY |
| 100 | YES | `local/llama` | GLM-5.2 via llama.cpp RPC | 131072 | 18.5 |  |  | LOCAL_API_KEY |

## `lane/code`  (2/21 ready)

Coding: Codestral → Qwen-coder free → Groq gpt-oss → local.
Aliases: `code`, `lane-code`

| order | ready | id | display | ctx | t/s | rpd | tok left/day | key |
|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | no-key | `codestral/latest` | Codestral | 256000 | 70 | 2000 |  | MISTRAL_API_KEY |
| 2 | no-key | `or/qwen3-coder` | Qwen3 Coder | 262144 | 35 | 50 |  | OPENROUTER_API_KEY |
| 3 | no-key | `cerebras/gpt-oss-120b` | Cerebras GPT-OSS 120B | 65536 | 1000 | 14400 | 1000000 | CEREBRAS_API_KEY |
| 3 | no-key | `groq/gpt-oss-120b` | Groq GPT-OSS 120B | 131072 | 300 | 1000 |  | GROQ_API_KEY |
| 3 | no-key | `groq/qwen3.6-27b` | Groq Qwen 3.6 27B | 131072 | 250 | 1000 |  | GROQ_API_KEY |
| 3 | no-key | `or/north-mini-code` | Cohere North Mini Code | 32768 | 60 | 50 |  | OPENROUTER_API_KEY |
| 4 | no-key | `groq/gpt-oss-20b` | Groq GPT-OSS 20B | 131072 | 400 | 1000 |  | GROQ_API_KEY |
| 4 | no-key | `or/gpt-oss-20b` | OpenAI GPT-OSS 20B | 131072 | 60 | 50 |  | OPENROUTER_API_KEY |
| 5 | no-key | `or/qwen3-next-80b` | Qwen3 Next 80B A3B Instruct | 131072 | 35 | 50 |  | OPENROUTER_API_KEY |
| 6 | no-key | `cf/gpt-oss-120b` | CF GPT-OSS 120B | 131072 | 30 |  |  | CLOUDFLARE_API_TOKEN |
| 7 | no-key | `cf/qwen3-30b` | CF Qwen3 30B | 131072 | 35 |  |  | CLOUDFLARE_API_TOKEN |
| 8 | no-key | `cf/kimi-k2.7-code` | CF Kimi K2.7 Code | 131072 | 30 |  |  | CLOUDFLARE_API_TOKEN |
| 9 | no-key | `alibaba/qwen-coder` | Qwen Coder (Model Studio) | 262144 | 45 |  | 1000000 | DASHSCOPE_API_KEY |
| 9 | no-key | `alibaba/qwen-plus` | Qwen Plus (Model Studio) | 131072 | 50 |  | 1000000 | DASHSCOPE_API_KEY |
| 10 | no-key | `hyp/qwen3-coder-480b` | Hyperbolic Qwen3 Coder 480B | 262144 | 25 |  |  | HYPERBOLIC_API_KEY |
| 11 | no-key | `snova/gpt-oss-120b` | SambaNova GPT-OSS 120B | 131072 | 90 |  |  | SAMBANOVA_API_KEY |
| 12 | no-key | `scw/glm-5.2` | Scaleway GLM-5.2 | 131072 | 35 |  | 1000000 | SCALEWAY_API_KEY |
| 12 | no-key | `scw/qwen3-coder-30b` | Scaleway Qwen3 Coder 30B | 262144 | 40 |  | 1000000 | SCALEWAY_API_KEY |
| 13 | no-key | `scw/devstral-2` | Scaleway Devstral 2 123B | 131072 | 30 |  | 1000000 | SCALEWAY_API_KEY |
| 99 | YES | `local/ds4` | GLM-5.2 via ds4-server | 131072 | 3.0 |  |  | LOCAL_API_KEY |
| 100 | YES | `local/llama` | GLM-5.2 via llama.cpp RPC | 131072 | 18.5 |  |  | LOCAL_API_KEY |
