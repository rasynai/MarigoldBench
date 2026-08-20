# System configuration cards - campaign 0.3.0

## marigold (native product row)

- Product: Marigold core on the sponsor's GPU server (129.213.93.18), core
  http://127.0.0.1:8012, OpenHands Agent Server 1.36.1 with
  `marigold.agent_server_glue` + `marigold_uvicorn_runtime`.
- Agent spec: the server's pinned `default_agent.json` - 48 tools, tiered
  policy (t0 none / t1 low / t2 medium reasoning effort with plan-work,
  research and verifier stages at t2), condenser, critic; base model
  `openai/gpt-5.6-sol`.
- Mode: N1 autonomous work order, `NeverConfirm`, LocalWorkspace per run,
  budget 25 min/task, then interrupt; conversation deleted after export.
- Network/tools: the operator's standing core config (started by
  `start_cores.sh`) which DENIES retrieval tools
  (web_search/research/paper_qa/...). All benchmark tasks are offline by
  design, so no task required a denied tool.
- Adapter: minimal (crucible/marigold_adapter.py) - uploads the agent-visible
  bundle, submits the card + submission contract as the user message, polls,
  exports `final_submission/`, verifies locally. No output edits, no retries.
- **Disclosed repairs before the campaign** (guide 23.7 / 20.9):
  1. The product's pinned `llm.api_key` in `default_agent.json` was expired -
     every conversation died with LLMAuthenticationError. The sponsor's
     working OpenAI key was substituted (same base model, nothing else
     changed); backup at `default_agent.json.bak-crucible-20260815`, env
     backup at `marigold.env.bak-crucible-20260815`; core 8012 restarted via
     the operator's own `start_cores.sh`.
  2. Adapter payload fix during piloting (tags must be a string map).
- Cost: Marigold's model spend bills to the sponsor's OpenAI key; not in the
  local usage ledger.

## OpenRouter frontier systems (reference-agent rows)

All six run the SAME two-call reference agent as campaign 0.2.0 (draft + one
verification-gated repair, max_tokens 32000 escalating on truncation, no
tools, offline):

| System | Lab | Notes |
|---|---|---|
| google/gemini-3.7-flash | Google | newest Gemini generation available on OpenRouter (no 3.7-pro exists there) |
| x-ai/grok-4.6 | xAI | |
| deepseek/deepseek-v4-pro | DeepSeek | |
| qwen/qwen3.8-max | Alibaba | |
| moonshotai/kimi-k3 | Moonshot | |
| z-ai/glm-5.2 | Zhipu | |

Campaign 0.2.0 rows (claude-opus-5, gpt-5.6-sol) used first-party APIs with
the same reference agent and the same five tasks.

**Comparison rule (guide 23.17):** Marigold's row measures a whole product
(agentic loop + tools + tiering on a GPU server); reference-agent rows measure
bare models in a fixed two-call harness. The rows must not be read as a causal
model-vs-harness decomposition in either direction.
