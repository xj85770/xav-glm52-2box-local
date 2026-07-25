# Rolodex catalog — individual APIs + lane membership

Swap by **model id** (exact) or by **lane** (`lane/local|fast|smart|code`).
Limits from [free-llm-api-resources](https://github.com/cheahjs/free-llm-api-resources). `tokens_left_*` / `requests_left_*` are local budget remaining vs published free caps (not live provider dashboards).

| ready | id | display | provider | tier | ctx | t/s typ | t/s obs | rpm | rpd | tpm | tpd | req left/day | tok left/day | lanes |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| YES | `local/ds4` | GLM-5.2 via ds4-server | local | local | 131072 | 3.0 |  |  |  |  |  |  |  | local,fast,smart,code |
| YES | `local/llama` | GLM-5.2 via llama.cpp RPC | local | local | 131072 | 18.5 |  |  |  |  |  |  |  | local,fast,smart,code |
| no-key | `cerebras/gpt-oss-120b` | Cerebras GPT-OSS 120B | cerebras | free | 65536 | 1000 |  | 30 | 14400 | 60000 | 1000000 | 14400 | 1000000 | fast,smart,code |
| no-key | `cerebras/llama3.1-8b` | Cerebras Llama 3.1 8B | cerebras | free | 8192 | 1800 |  | 30 | 14400 | 60000 | 1000000 | 14400 | 1000000 | fast |
| no-key | `cf/glm-5.2` | CF GLM-5.2 | cloudflare | free | 131072 | 25 |  |  |  |  |  |  |  | smart,local |
| no-key | `cf/gpt-oss-120b` | CF GPT-OSS 120B | cloudflare | free | 131072 | 30 |  |  |  |  |  |  |  | smart,code |
| no-key | `cf/gpt-oss-20b` | CF GPT-OSS 20B | cloudflare | free | 131072 | 40 |  |  |  |  |  |  |  | fast |
| no-key | `cf/kimi-k2.7-code` | CF Kimi K2.7 Code | cloudflare | free | 131072 | 30 |  |  |  |  |  |  |  | code |
| no-key | `cf/llama-3.3-70b` | CF Llama 3.3 70B | cloudflare | free | 131072 | 35 |  |  |  |  |  |  |  | smart |
| no-key | `cf/qwen3-30b` | CF Qwen3 30B | cloudflare | free | 131072 | 35 |  |  |  |  |  |  |  | code,smart |
| no-key | `codestral/latest` | Codestral | codestral | free | 256000 | 70 |  | 30 | 2000 |  |  | 2000 |  | code |
| no-key | `cohere/command-a` | Command A 03-2025 | cohere | free | 256000 | 60 |  | 20 | 34 |  |  | 34 |  | smart |
| no-key | `cohere/command-r-plus` | Command R+ | cohere | free | 128000 | 50 |  | 20 | 34 |  |  | 34 |  | smart |
| no-key | `cohere/command-r7b` | Command R7B | cohere | free | 128000 | 90 |  | 20 | 34 |  |  | 34 |  | fast,smart |
| no-key | `github/gpt-4o-mini` | GitHub GPT-4o mini | github_models | free | 128000 | 50 |  |  | 50 |  |  | 50 |  | smart |
| no-key | `github/llama-3.3-70b` | GitHub Llama 3.3 70B | github_models | free | 128000 | 40 |  |  | 50 |  |  | 50 |  | smart |
| no-key | `github/phi-4` | GitHub Phi-4 | github_models | free | 16384 | 70 |  |  | 50 |  |  | 50 |  | fast |
| no-key | `gemini/2.5-flash` | Gemini 2.5 Flash | google | free | 1048576 | 100 |  | 5 | 20 | 250000 |  | 20 |  | smart |
| no-key | `gemini/2.5-flash-lite` | Gemini 2.5 Flash-Lite | google | free | 1048576 | 120 |  | 10 | 20 | 250000 |  | 20 |  | fast |
| no-key | `gemini/3-flash` | Gemini 3 Flash | google | free | 1048576 | 100 |  | 5 | 20 | 250000 |  | 20 |  | smart,fast |
| no-key | `gemini/3.1-flash-lite` | Gemini 3.1 Flash-Lite | google | free | 1048576 | 120 |  | 15 | 500 | 250000 |  | 500 |  | fast,smart |
| no-key | `gemini/3.5-flash` | Gemini 3.5 Flash | google | free | 1048576 | 90 |  | 5 | 20 | 250000 |  | 20 |  | smart |
| no-key | `gemini/gemma-3-12b` | Gemma 3 12B Instruct | google | free | 131072 | 80 |  | 30 | 14400 | 15000 |  | 14400 |  | fast |
| no-key | `gemini/gemma-3-27b` | Gemma 3 27B Instruct | google | free | 131072 | 60 |  | 30 | 14400 | 15000 |  | 14400 |  | smart,fast |
| no-key | `gemini/gemma-3-4b` | Gemma 3 4B Instruct | google | free | 131072 | 120 |  | 30 | 14400 | 15000 |  | 14400 |  | fast |
| no-key | `groq/allam-2-7b` | Groq Allam 2 7B | groq | free | 8192 | 400 |  |  | 7000 | 6000 |  | 7000 |  | fast |
| no-key | `groq/gpt-oss-120b` | Groq GPT-OSS 120B | groq | free | 131072 | 300 |  |  | 1000 | 8000 |  | 1000 |  | code,smart |
| no-key | `groq/gpt-oss-20b` | Groq GPT-OSS 20B | groq | free | 131072 | 400 |  |  | 1000 | 8000 |  | 1000 |  | fast,code |
| no-key | `groq/llama-3.1-8b` | Groq Llama 3.1 8B | groq | free | 131072 | 500 |  |  | 14400 | 6000 |  | 14400 |  | fast |
| no-key | `groq/llama-3.3-70b` | Groq Llama 3.3 70B | groq | free | 131072 | 200 |  |  | 1000 | 12000 |  | 1000 |  | fast,smart |
| no-key | `groq/qwen3.6-27b` | Groq Qwen 3.6 27B | groq | free | 131072 | 250 |  |  | 1000 | 8000 |  | 1000 |  | smart,code |
| no-key | `hf/llama-3.1-8b` | HF Llama 3.1 8B Instruct | huggingface | free | 131072 | 30 |  |  |  |  |  |  |  | fast |
| no-key | `mistral/large` | Mistral Large | mistral | free | 128000 | 50 |  | 60 |  | 500000 |  |  |  | smart |
| no-key | `mistral/small` | Mistral Small | mistral | free | 128000 | 80 |  | 60 |  | 500000 |  |  |  | smart,fast |
| no-key | `nim/default` | NVIDIA NIM open models | nvidia_nim | free | 32768 | 40 |  | 40 |  |  |  |  |  | smart,fast |
| no-key | `zen/deepseek-v4-flash` | DeepSeek V4 Flash Free (Zen) | opencode_zen | free | 131072 | 80 |  |  |  |  |  |  |  | fast |
| no-key | `zen/nemotron-3-super` | Nemotron 3 Super Free (Zen) | opencode_zen | free | 131072 | 40 |  |  |  |  |  |  |  | smart |
| no-key | `or/dolphin-mistral-24b` | Dolphin Mistral 24B Venice | openrouter | free | 32768 | 45 |  | 20 | 50 |  |  | 50 |  | smart |
| no-key | `or/gemma-4-26b` | Gemma 4 26B A4B IT | openrouter | free | 131072 | 50 |  | 20 | 50 |  |  | 50 |  | smart,fast |
| no-key | `or/gemma-4-31b` | Gemma 4 31B IT | openrouter | free | 131072 | 45 |  | 20 | 50 |  |  | 50 |  | smart |
| no-key | `or/gpt-oss-20b` | OpenAI GPT-OSS 20B | openrouter | free | 131072 | 60 |  | 20 | 50 |  |  | 50 |  | fast,code |
| no-key | `or/hermes-3-405b` | Hermes 3 Llama 3.1 405B | openrouter | free | 131072 | 25 |  | 20 | 50 |  |  | 50 |  | smart |
| no-key | `or/hy3` | Tencent HY3 | openrouter | free | 131072 | 40 |  | 20 | 50 |  |  | 50 |  | smart |
| no-key | `or/laguna-m` | Poolside Laguna M.1 | openrouter | free | 131072 | 40 |  | 20 | 50 |  |  | 50 |  | smart |
| no-key | `or/laguna-xs` | Poolside Laguna XS 2.1 | openrouter | free | 65536 | 70 |  | 20 | 50 |  |  | 50 |  | fast |
| no-key | `or/llama-3.2-3b` | Llama 3.2 3B Instruct | openrouter | free | 131072 | 80 |  | 20 | 50 |  |  | 50 |  | fast |
| no-key | `or/llama-3.3-70b` | Llama 3.3 70B Instruct | openrouter | free | 131072 | 40 |  | 20 | 50 |  |  | 50 |  | fast,smart |
| no-key | `or/nemotron-3-nano-30b` | Nemotron 3 Nano 30B | openrouter | free | 131072 | 55 |  | 20 | 50 |  |  | 50 |  | fast,smart |
| no-key | `or/nemotron-3-nano-omni` | Nemotron 3 Nano Omni 30B Reasoning | openrouter | free | 131072 | 40 |  | 20 | 50 |  |  | 50 |  | smart |
| no-key | `or/nemotron-3-super-120b` | Nemotron 3 Super 120B | openrouter | free | 131072 | 30 |  | 20 | 50 |  |  | 50 |  | smart |
| no-key | `or/nemotron-3-ultra-550b` | Nemotron 3 Ultra 550B | openrouter | free | 131072 | 15 |  | 20 | 50 |  |  | 50 |  | smart |
| no-key | `or/nemotron-nano-12b-vl` | Nemotron Nano 12B V2 VL | openrouter | free | 131072 | 50 |  | 20 | 50 |  |  | 50 |  | smart |
| no-key | `or/nemotron-nano-9b` | Nemotron Nano 9B V2 | openrouter | free | 131072 | 70 |  | 20 | 50 |  |  | 50 |  | fast |
| no-key | `or/north-mini-code` | Cohere North Mini Code | openrouter | free | 32768 | 60 |  | 20 | 50 |  |  | 50 |  | code |
| no-key | `or/qwen3-coder` | Qwen3 Coder | openrouter | free | 262144 | 35 |  | 20 | 50 |  |  | 50 |  | code |
| no-key | `or/qwen3-next-80b` | Qwen3 Next 80B A3B Instruct | openrouter | free | 131072 | 35 |  | 20 | 50 |  |  | 50 |  | smart,code |
| no-key | `vercel/gateway-default` | Vercel AI Gateway (routed) | vercel | free | 128000 | 50 |  |  |  |  |  |  |  | smart |
| no-key | `ai21/jamba-large` | AI21 Jamba Large | ai21 | trial | 256000 | 40 |  |  |  |  |  |  |  | smart |
| no-key | `alibaba/qwen-coder` | Qwen Coder (Model Studio) | alibaba | trial | 262144 | 45 |  |  |  |  | 1000000 |  | 1000000 | code |
| no-key | `alibaba/qwen-plus` | Qwen Plus (Model Studio) | alibaba | trial | 131072 | 50 |  |  |  |  | 1000000 |  | 1000000 | smart,code |
| no-key | `baseten/generic` | Baseten (deployed model) | baseten | trial | 128000 | 40 |  |  |  |  |  |  |  | smart |
| no-key | `fw/llama-3.3-70b` | Fireworks Llama 3.3 70B | fireworks | trial | 131072 | 120 |  |  |  |  |  |  |  | smart,fast |
| no-key | `hyp/deepseek-r1` | Hyperbolic DeepSeek R1 | hyperbolic | trial | 65536 | 30 |  |  |  |  |  |  |  | smart |
| no-key | `hyp/deepseek-v3` | Hyperbolic DeepSeek V3 0324 | hyperbolic | trial | 65536 | 40 |  |  |  |  |  |  |  | smart |
| no-key | `hyp/llama-3.3-70b` | Hyperbolic Llama 3.3 70B | hyperbolic | trial | 131072 | 50 |  |  |  |  |  |  |  | smart,fast |
| no-key | `hyp/qwen3-coder-480b` | Hyperbolic Qwen3 Coder 480B | hyperbolic | trial | 262144 | 25 |  |  |  |  |  |  |  | code |
| no-key | `inference/llama-70b` | Inference.net Llama 70B | inference_net | trial | 131072 | 45 |  |  |  |  |  |  |  | smart |
| no-key | `modal/openai-compat` | Modal OpenAI-compatible deploy | modal | trial | 128000 | 40 |  |  |  |  |  |  |  | smart |
| no-key | `nebius/llama-3.3-70b` | Nebius Llama 3.3 70B | nebius | trial | 131072 | 50 |  |  |  |  |  |  |  | smart |
| no-key | `nlpcloud/default` | NLP Cloud open models | nlpcloud | trial | 32768 | 30 |  |  |  |  |  |  |  | smart |
| no-key | `novita/llama-3.3-70b` | Novita Llama 3.3 70B | novita | trial | 131072 | 45 |  |  |  |  |  |  |  | smart |
| no-key | `snova/deepseek-v3.2` | SambaNova DeepSeek V3.2 | sambanova | trial | 65536 | 80 |  |  |  |  |  |  |  | smart |
| no-key | `snova/gemma-4-31b` | SambaNova Gemma 4 31B | sambanova | trial | 131072 | 100 |  |  |  |  |  |  |  | smart |
| no-key | `snova/gpt-oss-120b` | SambaNova GPT-OSS 120B | sambanova | trial | 131072 | 90 |  |  |  |  |  |  |  | smart,code |
| no-key | `snova/llama-3.3-70b` | SambaNova Llama 3.3 70B | sambanova | trial | 131072 | 100 |  |  |  |  |  |  |  | fast,smart |
| no-key | `scw/devstral-2` | Scaleway Devstral 2 123B | scaleway | trial | 131072 | 30 |  |  |  |  |  |  | 1000000 | code |
| no-key | `scw/gemma-3-27b` | Scaleway Gemma 3 27B | scaleway | trial | 131072 | 40 |  |  |  |  | 1000000 |  | 1000000 | smart |
| no-key | `scw/glm-5.2` | Scaleway GLM-5.2 | scaleway | trial | 131072 | 35 |  |  |  |  |  |  | 1000000 | smart,code |
| no-key | `scw/gpt-oss-120b` | Scaleway GPT-OSS 120B | scaleway | trial | 131072 | 40 |  |  |  |  |  |  | 1000000 | smart |
| no-key | `scw/llama-3.3-70b` | Scaleway Llama 3.3 70B | scaleway | trial | 131072 | 40 |  |  |  |  |  |  | 1000000 | smart |
| no-key | `scw/qwen3-coder-30b` | Scaleway Qwen3 Coder 30B | scaleway | trial | 262144 | 40 |  |  |  |  |  |  | 1000000 | code |
| no-key | `upstage/solar-pro` | Upstage Solar Pro | upstage | trial | 32768 | 50 |  |  |  |  |  |  |  | smart |

## Notes

- **Local GLM (two-box / ds4)** (`local`): Your Mac cluster. No cloud quota.
- **Cerebras** (`cerebras`): Very high decode speed on free tier.
- **Cloudflare Workers AI** (`cloudflare`): 10k neurons/day free. Set CLOUDFLARE_ACCOUNT_ID + CLOUDFLARE_API_TOKEN.
- **Mistral Codestral** (`codestral`): Codestral endpoint; 30 RPM / 2000 RPD; phone verify.
- **Cohere** (`cohere`): 20 RPM / 1000 requests/month shared across models.
- **GitHub Models** (`github_models`): Extremely restrictive I/O token limits; tier depends on Copilot plan.
- **Google AI Studio** (`google`): Data used for training outside UK/CH/EEA/EU. Per-model RPM/RPD/TPM.
- **Groq** (`groq`): Per-model free limits. Excellent latency.
- **HuggingFace Inference Providers** (`huggingface`): $0.10/month credits. Serverless often <10GB models.
- **Mistral La Plateforme** (`mistral`): Experiment plan; opt-in training; phone verify. 1 rps / 500k TPM / 1B TPM month per model.
- **NVIDIA NIM** (`nvidia_nim`): Phone verification required. Context often limited.
- **OpenCode Zen** (`opencode_zen`): Curated free models; may use data for improvement.
- **OpenRouter** (`openrouter`): All :free models share one account quota (20 RPM / 50 RPD; 1000 RPD with $10 lifetime topup).
- **Vercel AI Gateway** (`vercel`): $5/month gateway credit. Routes to many providers.
- **AI21** (`ai21`): $10 for 3 months. Jamba family.
- **Alibaba Cloud Model Studio** (`alibaba`): 1M free tokens per model (international).
- **Baseten** (`baseten`): $30 credit; pay by compute time.
- **Fireworks** (`fireworks`): $1 trial credit.
- **Hyperbolic** (`hyperbolic`): $1 credit.
- **Inference.net** (`inference_net`): $1 base; +$25 survey.
- **Modal** (`modal`): $5/mo signup; $30/mo with payment method. Bring your own deployed OpenAI-compatible endpoint.
- **Nebius Token Factory** (`nebius`): $1 trial.
- **NLP Cloud** (`nlpcloud`): $15 credit; phone verify.
- **Novita** (`novita`): $0.50 for 1 year.
- **SambaNova Cloud** (`sambanova`): $5 for 3 months.
- **Scaleway Generative APIs** (`scaleway`): 1,000,000 free tokens.
- **Upstage** (`upstage`): $10 for 3 months. Solar Pro/Mini.
