"""The episode harness: one frozen agent loop, three candidate providers.

Bar B10 of GOAL.md is the reason this file exists and is deliberately dumb.
PaperBench measured a scaffold flipping the ranking of two models (Claude
21.0% under BasicAgent vs 16.1% under IterativeAgent), so any cleverness here
- retries, planning scaffolds, reflection prompts, tool-choice hints - would
be measuring our harness, not the model. The loop therefore does exactly one
thing: relay the model's tool calls to the tool belt and its real results
back, until the model submits or the budget runs out.

The contract text is a module constant and is byte-identical for every task,
condition and candidate (bar B7).
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..llm import load_keys
from .tools import ToolBelt, ToolError, tool_schemas

# Frozen. Do not template anything per-task into this string.
CONTRACT = """You are a computational scientist with access to a working laboratory:
structure prediction, protein design, docking, generative chemistry, a
cheminformatics library, and a Python environment where you can compute and
train models. The tools are real, they run real jobs, and they can fail.

Do the work the brief asks for. Decide for yourself which tools to use and in
what order, inspect what they return, and carry the consequences of what you
find. If a tool fails, read the error and decide what to do about it. If the
task as posed cannot be done with what you have, say so and explain why
rather than producing a number that is not supported.

You have a limited number of tool calls. Spend them on the analysis, not on
exploration you do not need.

When you are finished, call the `submit` tool exactly once with your result.
Everything you want scored must be in that call: values you did not submit are
not scored, and prose outside the submission is read only as your reasoning.
Give a calibrated confidence in [0,1] for each submitted field, read as the
probability that the value is correct; being confidently wrong is penalised."""

SUBMIT_SCHEMA = {
    "name": "submit",
    "description": "Submit your final result. Call this exactly once, when done.",
    "input_schema": {
        "type": "object",
        "properties": {
            "result": {
                "type": "object",
                "description": "Your answer: the fields the brief asks for, "
                               "plus conf_<field> in [0,1] for each.",
            },
            "reasoning": {
                "type": "string",
                "description": "How you reached it, and anything a reviewer "
                               "would need to reproduce or challenge it.",
            },
        },
        "required": ["result", "reasoning"],
    },
}



# Rate limits and transient service errors are not measurements. Without a
# retry an episode dies mid-run and would be scored (or quarantined) for a
# provider hiccup, and with 8 shards against one Gemini quota those are
# routine. Retries are on the TRANSPORT only - the model never sees them and
# no tool call is repeated, so the science being measured is unchanged.
TRANSIENT = ("429", "rate limit", "resource exhausted", "503", "502", "504",
             "overloaded", "timeout", "timed out", "temporarily unavailable",
             "connection")
RETRY_WAITS = (15, 45, 120, 240)


def _is_transient(exc: Exception) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    return any(marker in text for marker in TRANSIENT)


def _with_retry(call, label: str):
    """Run a provider call, retrying only transient transport failures."""
    last: Exception | None = None
    for attempt in range(len(RETRY_WAITS) + 1):
        try:
            return call()
        except Exception as exc:  # noqa: BLE001
            last = exc
            if not _is_transient(exc) or attempt == len(RETRY_WAITS):
                raise
            time.sleep(RETRY_WAITS[attempt])
    raise last  # pragma: no cover


@dataclass
class EpisodeResult:
    submitted: dict | None
    reasoning: str
    transcript: list[dict]
    tool_calls: int
    turns: int
    stop_reason: str
    seconds: float
    usage: dict = field(default_factory=dict)


def _submission(payload: dict) -> tuple[object, str]:
    """Read a submission liberally, then explain why that is not cheating.

    CORR-016: 73 Claude episodes recorded stop_reason "submitted" with nothing
    stored, against zero for GPT, because the model put its result object in the
    `reasoning` argument or passed `result` as a JSON string. Scoring those as
    empty submissions charged one model for a parsing choice of ours, which is
    exactly the scaffold confound the frozen loop exists to prevent.

    Liberal here means recovering an object the model did emit. It never
    invents, repairs or completes one: a salvaged blob still has to satisfy
    every checkpoint on its own.
    """
    result = payload.get("result")
    reasoning = payload.get("reasoning", "") or ""
    if isinstance(result, dict) and result:
        return result, reasoning
    for text in (result if isinstance(result, str) else None, reasoning):
        if not isinstance(text, str) or "{" not in text:
            continue
        found = _first_object(text)
        if found is not None:
            return found, reasoning
    return result, reasoning


def _first_object(text: str) -> dict | None:
    """The outermost balanced JSON object in a blob of prose, or None."""
    start = text.find("{")
    while start != -1:
        depth = 0
        for index in range(start, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        candidate = json.loads(text[start:index + 1])
                    except json.JSONDecodeError:
                        break
                    if isinstance(candidate, dict) and candidate:
                        return candidate
                    break
        start = text.find("{", start + 1)
    return None


def _anthropic_loop(model: str, brief: str, belt: ToolBelt,
                    max_turns: int, max_tokens: int, effort: str) -> EpisodeResult:
    import anthropic

    client = anthropic.Anthropic()
    tools = [{"name": t["name"], "description": t["description"],
              "input_schema": t["input_schema"]} for t in tool_schemas()]
    tools.append(SUBMIT_SCHEMA)
    # The contract and the tool schemas are byte-identical on every turn of
    # every episode, and an agent loop re-sends them each turn. Marking the
    # end of the tool block caches that prefix, which is most of the input
    # bill: the first cost probe ran 58k input tokens for 7 turns of a task
    # whose actual content was a few thousand.
    tools[-1] = {**tools[-1], "cache_control": {"type": "ephemeral"}}
    messages: list[dict] = [{"role": "user", "content": brief}]
    submitted, reasoning, stop = None, "", "max_turns"
    usage = {"input_tokens": 0, "output_tokens": 0}
    started = time.time()

    for turn in range(max_turns):
        extra = {"output_config": {"effort": effort}} if effort else {}

        def _send():
            with client.messages.stream(model=model, max_tokens=max_tokens,
                                        system=CONTRACT, messages=messages,
                                        tools=tools,
                                        extra_body=extra or None) as stream:
                return stream.get_final_message()

        message = _with_retry(_send, "anthropic")
        usage["input_tokens"] += message.usage.input_tokens
        usage["output_tokens"] += message.usage.output_tokens
        usage["cache_write"] = usage.get("cache_write", 0) + (
            getattr(message.usage, "cache_creation_input_tokens", 0) or 0)
        usage["cache_read"] = usage.get("cache_read", 0) + (
            getattr(message.usage, "cache_read_input_tokens", 0) or 0)
        messages.append({"role": "assistant", "content": message.content})

        tool_uses = [b for b in message.content if b.type == "tool_use"]
        if not tool_uses:
            reasoning += "".join(b.text for b in message.content if b.type == "text")
            stop = "no_tool_call"
            break

        results = []
        for use in tool_uses:
            if use.name == "submit":
                submitted, reasoning = _submission(dict(use.input))
                stop = "submitted"
                break
            try:
                value = belt.call(use.name, **use.input)
                payload, is_error = json.dumps(value, default=str)[:6000], False
            except ToolError as exc:
                payload, is_error = str(exc), True
            results.append({"type": "tool_result", "tool_use_id": use.id,
                            "content": payload, "is_error": is_error})
        if stop == "submitted":
            break
        messages.append({"role": "user", "content": results})
    else:
        turn = max_turns - 1

    return EpisodeResult(submitted, reasoning, belt.transcript, belt.calls_used,
                         turn + 1, stop, round(time.time() - started, 1), usage)


def _responses_loop(model: str, brief: str, belt: ToolBelt, max_turns: int,
                    max_tokens: int, effort: str) -> EpisodeResult:
    """OpenAI Responses API.

    Required, not preferred: gpt-5.6-sol rejects function tools on
    /v1/chat/completions unless reasoning_effort is 'none', and the sponsor
    specified maximum thinking. Reasoning items must also be echoed back in
    `input` so the model keeps its chain across tool calls.
    """
    import openai

    client = openai.OpenAI()
    tools = [{"type": "function", "name": t["name"],
              "description": t["description"], "parameters": t["input_schema"]}
             for t in tool_schemas() + [SUBMIT_SCHEMA]]
    conversation: list[Any] = [{"role": "user", "content": brief}]
    submitted, reasoning, stop = None, "", "max_turns"
    usage = {"input_tokens": 0, "output_tokens": 0}
    started = time.time()

    for turn in range(max_turns):
        response = _with_retry(lambda: client.responses.create(
            model=model, instructions=CONTRACT, input=conversation,
            tools=tools, max_output_tokens=max_tokens,
            reasoning={"effort": effort or "high"}), "openai")
        if response.usage:
            usage["input_tokens"] += response.usage.input_tokens or 0
            usage["output_tokens"] += response.usage.output_tokens or 0

        calls = []
        for item in response.output:
            conversation.append(item)          # includes reasoning items
            if getattr(item, "type", None) == "function_call":
                calls.append(item)
            elif getattr(item, "type", None) == "message":
                for part in getattr(item, "content", []) or []:
                    if getattr(part, "type", None) == "output_text":
                        reasoning += part.text

        if not calls:
            stop = "no_tool_call"
            break

        for call in calls:
            try:
                args = json.loads(call.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            if call.name == "submit":
                submitted, text = _submission(args)
                reasoning = text or reasoning
                stop = "submitted"
                break
            try:
                value = belt.call(call.name, **args)
                payload = json.dumps(value, default=str)[:6000]
            except ToolError as exc:
                payload = f"ERROR: {exc}"
            conversation.append({"type": "function_call_output",
                                 "call_id": call.call_id, "output": payload})
        if stop == "submitted":
            break
    else:
        turn = max_turns - 1

    return EpisodeResult(submitted, reasoning, belt.transcript, belt.calls_used,
                         turn + 1, stop, round(time.time() - started, 1), usage)


def _openai_loop(provider: str, model: str, brief: str, belt: ToolBelt,
                 max_turns: int, max_tokens: int, effort: str) -> EpisodeResult:
    """Chat-completions wire, used by the Gemini paths."""
    import openai

    if provider == "gemini":
        import os
        client = openai.OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=os.environ["GEMINI_API_KEY"])
    elif provider == "vertex":
        import os

        import google.auth
        import google.auth.transport.requests
        credentials, default_project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"])
        credentials.refresh(google.auth.transport.requests.Request())
        project = os.environ.get("GOOGLE_CLOUD_PROJECT") or default_project
        location = os.environ.get("VERTEX_LOCATION", "us-central1")
        # The 3.x preview line is served ONLY from the `global` location, and
        # global uses the unprefixed host - `global-aiplatform...` returns an
        # HTML error page rather than a 404, which is easy to misread as the
        # model not existing.
        if model.startswith("gemini-3"):
            location = "global"
        host = ("aiplatform.googleapis.com" if location == "global"
                else f"{location}-aiplatform.googleapis.com")
        client = openai.OpenAI(
            base_url=f"https://{host}/v1/projects/{project}"
                     f"/locations/{location}/endpoints/openapi",
            api_key=credentials.token)
        model = "google/" + model
    elif provider in OPENAI_COMPATIBLE:
        import os
        endpoint = OPENAI_COMPATIBLE[provider]
        client = openai.OpenAI(base_url=endpoint["base_url"],
                               api_key=os.environ[endpoint["key_env"]])
    else:
        raise ValueError(f"unknown provider {provider}")

    tools = [{"type": "function",
              "function": {"name": t["name"], "description": t["description"],
                           "parameters": t["input_schema"]}}
             for t in tool_schemas() + [SUBMIT_SCHEMA]]
    messages: list[dict] = [{"role": "system", "content": CONTRACT},
                            {"role": "user", "content": brief}]
    submitted, reasoning, stop = None, "", "max_turns"
    usage = {"input_tokens": 0, "output_tokens": 0}
    started = time.time()

    for turn in range(max_turns):
        kwargs: dict = {"model": model, "messages": messages, "tools": tools,
                        "max_tokens": max_tokens}
        if provider == "openrouter":
            # The gateway will price the call for us. CORR-008 was a spend
            # guard that summed a cost field nobody recorded; an authoritative
            # per-call number from the biller is the fix for that class of bug,
            # so we ask for it and store it verbatim.
            kwargs["extra_body"] = {"usage": {"include": True}}
        response = _with_retry(
            lambda: client.chat.completions.create(**kwargs), "chat")
        choices = getattr(response, "choices", None) or []
        choice = choices[0].message if choices else None
        if choice is None:
            # A response with no choices (safety stop, empty candidate) is the
            # end of the episode, not a crash: record it and let scoring see
            # an unsubmitted result.
            stop = "empty_response"
            break
        if response.usage:
            usage["input_tokens"] += response.usage.prompt_tokens or 0
            usage["output_tokens"] += response.usage.completion_tokens or 0
            billed = getattr(response.usage, "cost", None)
            if billed is not None:
                usage["billed_usd"] = usage.get("billed_usd", 0.0) + float(billed)
        messages.append(choice.model_dump(exclude_none=True))

        calls = choice.tool_calls or []
        if not calls:
            reasoning += choice.content or ""
            stop = "no_tool_call"
            break

        for call in calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            if name == "submit":
                submitted, reasoning = _submission(args)
                stop = "submitted"
                break
            try:
                value = belt.call(name, **args)
                payload = json.dumps(value, default=str)[:6000]
            except ToolError as exc:
                payload = f"ERROR: {exc}"
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": payload})
        if stop == "submitted":
            break
    else:
        turn = max_turns - 1

    return EpisodeResult(submitted, reasoning, belt.transcript, belt.calls_used,
                         turn + 1, stop, round(time.time() - started, 1), usage)


# Gateways that speak the OpenAI chat-completions wire. Keeping them in one
# table is what makes "adding a system is one line" true for them as well.
OPENAI_COMPATIBLE = {
    "xai": {"base_url": "https://api.x.ai/v1", "key_env": "XAI_API_KEY"},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1",
                   "key_env": "OPENROUTER_API_KEY"},
}


# Candidate registry. Adding a system means adding a line here and nothing else.
SYSTEMS: dict[str, dict] = {
    "claude": {"provider": "anthropic", "model": "claude-opus-5", "effort": "high"},
    "gpt": {"provider": "openai", "model": "gpt-5.6-sol", "effort": "high"},
    # Vertex on this project serves the 2.5 line; every 3.x id returns 404
    # (probed 2026-08-17), so 2.5 Pro is the strongest Gemini available here.
    "gemini": {"provider": "vertex", "model": "gemini-3.1-pro-preview", "effort": ""},
    "gemini-25": {"provider": "vertex", "model": "gemini-2.5-pro", "effort": ""},
    # Grok direct on xAI. The key the sponsor supplied is a MANAGEMENT key, not
    # an inference key - api.x.ai rejects it and management-api.x.ai validates
    # it - so an inference key was minted through
    # POST /auth/teams/{teamId}/api-keys and granted `api-key:endpoint:*` and
    # `api-key:model:*` (a new key has no access until its ACLs are set).
    # grok-4.6 is the newest and priciest of the twelve models the key can see.
    # The gateway route is deliberately absent: the sponsor's instruction is
    # not to run Grok through OpenRouter at all.
    "grok": {"provider": "xai", "model": "grok-4.6", "effort": ""},
    # OpenRouter-hosted open-weight frontier. Every one of these is billed
    # against ONE shared ceiling (see campaign.OPENROUTER_CEILING_USD), which
    # the sponsor set at $100 and which is enforced, not advisory.
    "deepseek": {"provider": "openrouter", "model": "deepseek/deepseek-v4-pro",
                 "effort": ""},
    "kimi": {"provider": "openrouter", "model": "moonshotai/kimi-k2-thinking",
             "effort": ""},
    "glm": {"provider": "openrouter", "model": "z-ai/glm-4.7", "effort": ""},
}


def run_episode(system: str, brief: str, workspace: Path, budget: int = 25,
                max_turns: int = 30, max_tokens: int = 16000) -> EpisodeResult:
    load_keys()
    spec = SYSTEMS[system]
    belt = ToolBelt(workspace=workspace, budget=budget)
    if spec["provider"] == "anthropic":
        return _anthropic_loop(spec["model"], brief, belt, max_turns,
                               max_tokens, spec["effort"])
    if spec["provider"] == "openai":
        return _responses_loop(spec["model"], brief, belt, max_turns,
                               max_tokens, spec["effort"])
    return _openai_loop(spec["provider"], spec["model"], brief, belt,
                        max_turns, max_tokens, spec["effort"])
