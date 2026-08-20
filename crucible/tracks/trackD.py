"""Track D: temporal scientific forecasting against the simulated laboratory.

Forecasts are registered and collected BEFORE outcomes are computed (enforced
by code order in `run`); the information set is exactly the disclosed
historical measurements. Scored with proper scoring rules against reference
baselines (guide section 12). Cohort label: D2-analog inside a simulator.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .. import simlab
from ..llm import ModelClient, PROVIDERS

FORECAST_QUESTIONS = [
    {"forecast_id": "D-001", "temp_c": 95.0, "catalyst": "Pd-B", "solvent": "DMF"},
    {"forecast_id": "D-002", "temp_c": 60.0, "catalyst": "Pd-B", "solvent": "DMF"},
    {"forecast_id": "D-003", "temp_c": 95.0, "catalyst": "Pd-B", "solvent": "toluene"},
    {"forecast_id": "D-004", "temp_c": 70.0, "catalyst": "Pd-A", "solvent": "DMF"},
    {"forecast_id": "D-005", "temp_c": 110.0, "catalyst": "Ni-C", "solvent": "toluene"},
]

FORECAST_SYSTEM = """You are a chemist making calibrated probability forecasts.
You are scored with the Brier score, so report your honest probability, not a
confident guess."""


def run(out_dir: Path, providers: list[str] | None = None,
        custom_askers: dict | None = None) -> dict:
    """providers: ModelClient provider strings (incl. 'openrouter/<id>').
    custom_askers: {name: callable(system_prompt, user_prompt) -> dict} for
    systems that are not ModelClient-compatible (e.g. the Marigold product)."""
    providers = providers if providers is not None else list(PROVIDERS)
    custom_askers = custom_askers or {}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    registration = {
        "cohort_id": "SIM-FORECAST-001",
        "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "information_cutoff": "disclosed historical measurements only",
        "questions": [
            {
                **q,
                "question": (
                    f"Will T={q['temp_c']:.0f} C, {q['catalyst']}, {q['solvent']} give "
                    f">= {simlab.SUCCESS_THRESHOLD:.0f}% yield (replicate seed 1)?"
                ),
            }
            for q in FORECAST_QUESTIONS
        ],
        "resolution_rule": "crucible.simlab.simulate(condition, replicate_seed=1) >= threshold",
        "baselines": ["base_rate_0.17 (1/6 heuristic)", "nearest_disclosed_heuristic"],
        "claim_boundary": "forecasting inside a simulator; not live scientific forecasting",
    }
    (out_dir / "registration.json").write_text(json.dumps(registration, indent=2), encoding="utf-8")

    # --- Collect forecasts BEFORE any outcome is computed -------------------
    question_block = "\n".join(
        f"{q['forecast_id']}: T={q['temp_c']:.0f} C, catalyst={q['catalyst']}, solvent={q['solvent']}"
        for q in FORECAST_QUESTIONS
    )
    prompt = (
        simlab.disclosed_prompt()
        + "\n\nFor EACH condition below, give the probability that its measured"
        f" yield is >= {simlab.SUCCESS_THRESHOLD:.0f}%.\n"
        + question_block
        + "\n\nRespond with JSON: {\"forecasts\": [{\"forecast_id\": \"D-001\","
        " \"probability\": <0-1>, \"predicted_yield\": <number>,"
        " \"rationale\": \"one sentence\"}]}"
    )
    forecasts: dict[str, dict[str, dict]] = {}
    for provider in providers:
        client = ModelClient(provider, purpose="trackD-forecast", effort="medium", max_tokens=16000)
        reply = client.ask_json(FORECAST_SYSTEM, prompt)
        forecasts[provider] = {
            f["forecast_id"]: f for f in reply.get("forecasts", []) if "forecast_id" in f
        }
    for name, asker in custom_askers.items():
        try:
            reply = asker(FORECAST_SYSTEM, prompt)
            forecasts[name] = {
                f["forecast_id"]: f for f in reply.get("forecasts", []) if "forecast_id" in f
            }
        except Exception as exc:  # noqa: BLE001 - record the failure, keep scoring others
            forecasts[name] = {}
            (out_dir / f"asker_error_{name}.txt").write_text(str(exc), encoding="utf-8")
    (out_dir / "forecasts.json").write_text(json.dumps(forecasts, indent=2), encoding="utf-8")

    # --- Resolve outcomes (only after forecasts are stored) -----------------
    outcomes = {}
    for q in FORECAST_QUESTIONS:
        value = simlab.simulate(q["temp_c"], q["catalyst"], q["solvent"], 1)
        outcomes[q["forecast_id"]] = {
            "yield_percent": value,
            "positive": value >= simlab.SUCCESS_THRESHOLD,
        }

    def brier(probabilities: dict[str, float]) -> float | None:
        scored = [
            (probabilities[fid] - (1.0 if outcomes[fid]["positive"] else 0.0)) ** 2
            for fid in outcomes
            if fid in probabilities
        ]
        return sum(scored) / len(scored) if scored else None

    base_rate = {fid: 1 / 6 for fid in outcomes}

    def nearest_heuristic() -> dict[str, float]:
        disclosed = simlab.disclosed_measurements()
        probs = {}
        for q in FORECAST_QUESTIONS:
            same = [m for m in disclosed if m["catalyst"] == q["catalyst"] and m["solvent"] == q["solvent"]]
            pool = same or disclosed
            closest = min(pool, key=lambda m: abs(m["temp_c"] - q["temp_c"]))
            probs[q["forecast_id"]] = 0.6 if closest["yield_percent"] >= 60 else 0.1
        return probs

    report = {
        "registration": registration,
        "outcomes": outcomes,
        "scores": {
            "base_rate_baseline": brier(base_rate),
            "nearest_disclosed_heuristic": brier(nearest_heuristic()),
        },
        "forecasts": forecasts,
    }
    for provider, provider_forecasts in forecasts.items():
        probabilities = {
            fid: float(f.get("probability", 0.5)) for fid, f in provider_forecasts.items()
        }
        report["scores"][provider] = brier(probabilities)
    (out_dir / "trackD_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
