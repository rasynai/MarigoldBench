"""The spend guard must actually stop spending.

CORR-008: the guard summed a `cost_usd` field the code never wrote, so it read
$0.00 through 1,151 OpenRouter calls and never fired. There was no test that
made the guard fire, so nothing caught it. These tests do exactly that.
"""
from __future__ import annotations

import json

import pytest

from crucible import llm


def _write_usage(tmp_path, records):
    runs = tmp_path / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    (runs / "usage.jsonl").write_text(
        "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    (tmp_path / ".git").mkdir(exist_ok=True)
    return tmp_path


def _client(monkeypatch, tmp_path, provider="openrouter/x-ai/grok-4.6"):
    monkeypatch.setattr(llm, "find_repo_root", lambda root=None: tmp_path)
    client = llm.ModelClient.__new__(llm.ModelClient)   # skip network __post_init__
    client.provider = provider
    client.purpose = "test"
    return client


def test_guard_fires_once_budget_is_reached(monkeypatch, tmp_path):
    _write_usage(tmp_path, [
        {"model": "x-ai/grok-4.6", "input_tokens": 1, "output_tokens": 1,
         "cost_usd": 30.0} for _ in range(4)
    ])
    monkeypatch.setenv("CRUCIBLE_OR_BUDGET_USD", "100")
    with pytest.raises(RuntimeError, match=r"OpenRouter spend \$120\.00"):
        _client(monkeypatch, tmp_path)._guard()


def test_guard_allows_calls_below_budget(monkeypatch, tmp_path):
    _write_usage(tmp_path, [
        {"model": "x-ai/grok-4.6", "input_tokens": 1, "output_tokens": 1,
         "cost_usd": 5.0}
    ])
    monkeypatch.setenv("CRUCIBLE_OR_BUDGET_USD", "100")
    _client(monkeypatch, tmp_path)._guard()   # must not raise


def test_unreported_cost_is_estimated_not_zero():
    """The CORR-008 failure mode: a missing cost recorded as $0.00 is invisible
    to the guard no matter how many calls are made."""
    cost = llm.estimate_cost_usd("x-ai/grok-4.6", 2_000, 13_000)
    assert cost > 0.0
    assert cost == pytest.approx((2_000 * 3.00 + 13_000 * 15.00) / 1e6)


def test_unknown_model_is_priced_at_the_most_expensive_tier():
    """An unknown model must not be assumed cheap - the guard has to
    over-estimate, because under-estimating spends money we do not have."""
    unknown = llm.estimate_cost_usd("brand-new/model", 1_000, 1_000)
    priciest = max(llm.estimate_cost_usd(f"{p}/x", 1_000, 1_000)
                   for p in llm.FALLBACK_PRICE_PER_MTOK)
    assert unknown >= priciest


def test_estimated_costs_still_trip_the_guard(monkeypatch, tmp_path):
    """An entire campaign of unreported costs must still hit the ceiling."""
    per_call = llm.estimate_cost_usd("x-ai/grok-4.6", 1_861, 13_375)
    calls = int(100 / per_call) + 2
    _write_usage(tmp_path, [
        {"model": "x-ai/grok-4.6", "input_tokens": 1_861,
         "output_tokens": 13_375, "cost_usd": per_call, "cost_estimated": True}
        for _ in range(calls)
    ])
    monkeypatch.setenv("CRUCIBLE_OR_BUDGET_USD", "100")
    with pytest.raises(RuntimeError, match="cost guard"):
        _client(monkeypatch, tmp_path)._guard()


def test_guard_does_not_block_first_party_providers(monkeypatch, tmp_path):
    """Anthropic/OpenAI are billed separately; an exhausted OpenRouter budget
    must not stop first-party work."""
    _write_usage(tmp_path, [
        {"model": "x-ai/grok-4.6", "input_tokens": 1, "output_tokens": 1,
         "cost_usd": 999.0}
    ])
    monkeypatch.setenv("CRUCIBLE_OR_BUDGET_USD", "100")
    _client(monkeypatch, tmp_path, provider="anthropic")._guard()   # must not raise
