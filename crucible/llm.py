"""Model-expert clients (guide substitution policy: LLMs stand in for human experts).

Two independent providers are used everywhere a human panel is called for, so
no single model family grades itself:

- OpenAI  : gpt-5.6-sol
- Anthropic: claude-opus-5 (Fable 5 permitted as an alternate)

Every call is appended to runs/usage.jsonl with token counts so cost stays
auditable. Keys are read from .secrets/keys.env (never committed).
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

from .paths import find_repo_root

OPENAI_MODEL = "gpt-5.6-sol"
ANTHROPIC_MODEL = "claude-opus-5"
ANTHROPIC_FALLBACK = "claude-opus-4-8"

PROVIDERS = ("anthropic", "openai")

# Every third-party vendor is reached over the same OpenAI-compatible wire:
# `max_tokens` is the portable cap and unknown params are dropped upstream.
# Adding a vendor should mean adding a base_url and a credential, not a fourth
# request shape.
OPENAI_WIRE_PROVIDERS = ("openrouter/", "nvidia/", "gemini/", "vertex/")

# Fallback USD per 1M tokens (input, output) used ONLY when the provider does
# not report an actual cost. A missing cost must never be recorded as $0.00:
# that is exactly how the spend guard stayed silent through 1,151 calls and
# ~$194 of credit (CORR-008). An over-estimate stops the campaign early and
# costs a message; an under-estimate costs money that is not ours to spend.
FALLBACK_PRICE_PER_MTOK = {
    "x-ai/grok": (3.00, 15.00),
    "qwen": (1.20, 6.00),
    "moonshotai": (0.60, 2.50),
    "z-ai": (0.60, 2.20),
    "google/gemini": (0.30, 2.50),
    "deepseek": (0.28, 1.14),
}
DEFAULT_PRICE_PER_MTOK = (3.00, 15.00)   # deliberately the priciest tier


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = DEFAULT_PRICE_PER_MTOK
    for prefix, price in FALLBACK_PRICE_PER_MTOK.items():
        if model.startswith(prefix):
            price_in, price_out = price
            break
    return (input_tokens * price_in + output_tokens * price_out) / 1e6


def load_keys(root: Path | None = None) -> None:
    env_path = find_repo_root(root) / ".secrets" / "keys.env"
    if not env_path.exists():
        raise FileNotFoundError(
            "Missing .secrets/keys.env with OPENAI_API_KEY and ANTHROPIC_API_KEY."
        )
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def _usage_log(root: Path | None = None) -> Path:
    path = find_repo_root(root) / "runs" / "usage.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def extract_json(text: str):
    """Robustly pull the first JSON object out of a model reply."""
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidates = [fence.group(1)] if fence else []
    start = text.find("{")
    if start != -1:
        depth = 0
        in_string = False
        escape = False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
            elif char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[start:index + 1])
                    break
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError(f"No parseable JSON object in model reply (first 200 chars): {text[:200]!r}")


@dataclass
class ModelClient:
    provider: str  # "anthropic" | "openai"
    purpose: str = "general"
    max_tokens: int = 8000
    effort: str | None = None  # "low" | "medium" | "high" (None = provider default)

    def __post_init__(self):
        load_keys()
        if self.provider == "anthropic":
            import anthropic

            self._client = anthropic.Anthropic()
            self.model = ANTHROPIC_MODEL
        elif self.provider == "openai":
            import openai

            self._client = openai.OpenAI()
            self.model = OPENAI_MODEL
        elif self.provider.startswith("openrouter/"):
            # Frontier models via OpenRouter's OpenAI-compatible endpoint;
            # provider string is "openrouter/<vendor>/<model>".
            import openai

            self._client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.environ["OPENROUTER_API_KEY"],
            )
            self.model = self.provider.split("/", 1)[1]
        elif self.provider.startswith("gemini/"):
            # Google's Gemini API exposes an OpenAI-compatible surface, so it
            # reuses the same wire path as openrouter/nvidia rather than
            # needing a fourth client shape. Provider string is
            # "gemini/<model>", e.g. gemini/gemini-3.7-flash.
            import openai

            self._client = openai.OpenAI(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=os.environ["GEMINI_API_KEY"],
            )
            self.model = self.provider.split("/", 1)[1]
        elif self.provider.startswith("vertex/"):
            # Vertex AI via Application Default Credentials: no API key, billed
            # to GOOGLE_CLOUD_PROJECT. Vertex also speaks the OpenAI surface,
            # but it authenticates with a short-lived OAuth token minted from
            # ADC rather than a static key, so the token is refreshed per
            # client construction.
            import google.auth
            import google.auth.transport.requests
            import openai

            credentials, default_project = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"])
            credentials.refresh(google.auth.transport.requests.Request())
            project = os.environ.get("GOOGLE_CLOUD_PROJECT") or default_project
            location = os.environ.get("VERTEX_LOCATION", "us-central1")
            self._client = openai.OpenAI(
                base_url=f"https://{location}-aiplatform.googleapis.com/v1/"
                         f"projects/{project}/locations/{location}/endpoints/openapi",
                api_key=credentials.token,
            )
            self.model = "google/" + self.provider.split("/", 1)[1]
        elif self.provider.startswith("nvidia/"):
            # NVIDIA NIM, also OpenAI-compatible; provider string is
            # "nvidia/<vendor>/<model>".
            import openai

            self._client = openai.OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=os.environ["NVIDIA_API_KEY"],
            )
            self.model = self.provider.split("/", 1)[1]
        else:
            raise ValueError(f"unknown provider {self.provider}")

    # ------------------------------------------------------------------

    def _guard(self) -> None:
        """Hard campaign cost guards: total call count (CRUCIBLE_MAX_CALLS,
        default 20000 for the 2.0 era) and the sponsor's OpenRouter dollar
        ceiling (CRUCIBLE_OR_BUDGET_USD, default 100) summed from the actual
        per-call cost OpenRouter reports."""
        limit = int(os.environ.get("CRUCIBLE_MAX_CALLS", "20000"))
        path = _usage_log()
        if path.exists():
            count = 0
            or_spend = 0.0
            with path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    count += 1
                    if '"cost_usd"' in line:
                        try:
                            or_spend += float(json.loads(line).get("cost_usd") or 0.0)
                        except (json.JSONDecodeError, TypeError, ValueError):
                            pass
            if count >= limit:
                raise RuntimeError(
                    f"cost guard: {count} model calls recorded >= CRUCIBLE_MAX_CALLS={limit}"
                )
            if self.provider.startswith("openrouter/"):
                # Default is the measured requirement plus headroom ($30), not
                # a round $100. A ceiling far above the real need is not a
                # safeguard - it is permission to overspend by 3x before
                # anything complains.
                budget = float(os.environ.get("CRUCIBLE_OR_BUDGET_USD", "30"))
                if or_spend >= budget:
                    raise RuntimeError(
                        f"cost guard: OpenRouter spend ${or_spend:.2f} >= budget ${budget:.2f}"
                    )

    def _record(self, model: str, input_tokens: int, output_tokens: int,
                cost_usd: float | None = None, estimated: bool = False) -> None:
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "provider": self.provider,
            "model": model,
            "purpose": self.purpose,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }
        if cost_usd is not None:
            record["cost_usd"] = cost_usd
            record["cost_estimated"] = estimated
        with _usage_log().open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    def ask(self, system: str, user: str, max_tokens: int | None = None) -> str:
        self._guard()
        limit = max_tokens or self.max_tokens
        if self.provider == "anthropic":
            return self._ask_anthropic(system, user, limit)
        return self._ask_openai(system, user, limit)  # openai + openrouter/* (same wire shape)

    def _ask_anthropic(self, system: str, user: str, limit: int) -> str:
        extra = {"output_config": {"effort": self.effort}} if self.effort else {}
        # Streaming avoids SDK timeout guards at large max_tokens; thinking
        # tokens count against max_tokens on claude-opus-5, so keep headroom.
        with self._client.messages.stream(
            model=self.model,
            max_tokens=limit,
            system=system,
            messages=[{"role": "user", "content": user}],
            extra_body=extra or None,
        ) as stream:
            message = stream.get_final_message()
        if message.stop_reason == "refusal":
            # Client-side fallback (migration guide pattern 3): benign science
            # tasks can trip classifiers; retry once on the fallback model.
            with self._client.messages.stream(
                model=ANTHROPIC_FALLBACK,
                max_tokens=limit,
                system=system,
                messages=[{"role": "user", "content": user}],
            ) as stream:
                message = stream.get_final_message()
        self._record(message.model, message.usage.input_tokens, message.usage.output_tokens)
        if message.stop_reason == "refusal":
            raise RuntimeError("Anthropic model refused the request (both models).")
        return "".join(block.text for block in message.content if block.type == "text")

    def _ask_openai(self, system: str, user: str, limit: int) -> str:
        kwargs: dict = {"reasoning_effort": self.effort} if self.effort else {}
        if self.provider.startswith(OPENAI_WIRE_PROVIDERS):
            # Both route many vendors over an OpenAI-compatible wire; max_tokens
            # is the portable cap and unknown params are dropped upstream.
            response = self._client.chat.completions.create(
                model=self.model,
                max_tokens=limit,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                **({"extra_body": {"usage": {"include": True}}}
                   if self.provider.startswith("openrouter/") else {}),
            )
            usage = response.usage
            # Record the ACTUAL money. Omitting this is why the spend guard read
            # $0.00 through 1,151 OpenRouter calls and never fired (CORR-008).
            cost = None
            if usage is not None:
                raw = getattr(usage, "cost", None)
                if raw is None:
                    details = getattr(usage, "model_extra", None) or {}
                    raw = details.get("cost") if isinstance(details, dict) else None
                if raw is not None:
                    try:
                        cost = float(raw)
                    except (TypeError, ValueError):
                        cost = None
            prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(usage, "completion_tokens", 0) or 0
            estimated = False
            if cost is None and self.provider.startswith("openrouter/"):
                # NOT 0.0. An unreported cost is unknown, not free.
                cost = estimate_cost_usd(self.model, prompt_tokens, completion_tokens)
                estimated = True
            self._record(self.model, prompt_tokens, completion_tokens,
                         cost_usd=cost, estimated=estimated)
            # Reasoning models may return empty content (budget spent on
            # reasoning) - return "" so ask_json's retry loop escalates the
            # limit instead of crashing on the first empty reply.
            return response.choices[0].message.content or ""
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                max_completion_tokens=limit,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                **kwargs,
            )
        except TypeError:
            response = self._client.chat.completions.create(
                model=self.model,
                max_completion_tokens=limit,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        usage = response.usage
        self._record(self.model, usage.prompt_tokens, usage.completion_tokens)
        return response.choices[0].message.content or ""

    def ask_json(self, system: str, user: str, max_tokens: int | None = None, retries: int = 2):
        prompt = user + "\n\nRespond with a single valid JSON object and nothing else."
        limit = max_tokens or self.max_tokens
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            reply = self.ask(system, prompt, limit)
            try:
                return extract_json(reply)
            except ValueError as exc:
                last_error = exc
                # Truncation is the usual cause (reasoning tokens share the
                # output budget) - escalate the limit and demand compact JSON.
                limit = min(int(limit * 1.6), 64000)
                prompt = (
                    user
                    + "\n\nYour previous reply was not parseable JSON (it may have been"
                    " truncated). Respond with ONLY one COMPACT single-line JSON object:"
                    " no markdown fences, no prose, no pretty-printing, minimal"
                    " whitespace. Keep report text concise."
                )
        raise last_error  # type: ignore[misc]


def usage_summary(root: Path | None = None) -> dict:
    path = _usage_log(root)
    totals: dict[str, dict[str, int]] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:  # concurrent workers append; tolerate a rare interleaved line
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            bucket = totals.setdefault(record["model"], {"calls": 0, "input_tokens": 0, "output_tokens": 0})
            bucket["calls"] += 1
            bucket["input_tokens"] += record["input_tokens"]
            bucket["output_tokens"] += record["output_tokens"]
    return totals
