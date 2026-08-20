"""Track E: prospective empirical discovery inside the simulated laboratory.

Claim boundary (guide 19.2, 30.11): SIMULATOR source class - this measures
experimental design against a modeled response surface, NOT real-world
discovery. The protocol machinery is the real thing, though: immutable
registration before system access, full proposal denominators, blinded-order
testing, confirmation, and P-level reporting (guide sections 13 and 20.5).
"""
from __future__ import annotations

import json
import random
import time
from pathlib import Path

from .. import simlab
from ..llm import ModelClient, PROVIDERS

PROPOSALS_PER_ARM = 8

ARM_SYSTEM = """You are a synthetic chemist proposing reaction conditions for a
registered optimization study. Propose diverse, well-reasoned conditions and
give an honest calibrated probability of success for each - your calibration
is scored, so do not inflate probabilities."""


def _registration(out_dir: Path, arm_names: list[str] | None = None) -> dict:
    registration = {
        "project_id": "SIM-CC-001",
        "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scientific_question": (
            "Which conditions in the registered space give >= "
            f"{simlab.SUCCESS_THRESHOLD:.0f}% yield for the S1 cross-coupling?"
        ),
        "outcome_source": "SIMULATOR (crucible.simlab) - hidden response surface",
        "unknown_primary_outcome": True,
        "arms": arm_names or ["anthropic", "openai", "baseline_random", "baseline_grid"],
        "proposal_budget_per_arm": PROPOSALS_PER_ARM,
        "eligible_proposal_space": {
            "temp_c": list(simlab.TEMP_RANGE),
            "catalyst": list(simlab.CATALYSTS),
            "solvent": list(simlab.SOLVENTS),
        },
        "eligibility_screen": ["E-SCOPE: outside registered space", "E-DUP: duplicate condition"],
        "selection_rule": "test ALL eligible proposals (budget permits; no cherry-picking)",
        "primary_outcome": f"yield >= {simlab.SUCCESS_THRESHOLD:.0f}% at replicate seed 1",
        "confirmation_rule": "independent replicate (seed 2) also >= threshold",
        "blinding": "test order randomized (seed 42); simulator blind to arm",
        "negative_result_policy": "all tested outcomes retained and published",
        "analysis_plan": "per-arm denominator ladder, hit rates, Brier calibration",
        "claim_boundary": "simulator-based experimental design only",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "registration.json").write_text(json.dumps(registration, indent=2), encoding="utf-8")
    return registration


def _proposal_prompt() -> str:
    return (
        simlab.disclosed_prompt()
        + f"\n\nPropose exactly {PROPOSALS_PER_ARM} new conditions to test."
        " Respond with JSON: {\"proposals\": [{\"temp_c\": <number>,"
        " \"catalyst\": \"...\", \"solvent\": \"...\","
        " \"predicted_probability\": <0-1 probability that yield >= threshold>,"
        " \"rationale\": \"one sentence\"}]}"
    )


def _model_proposals(provider: str) -> list[dict]:
    client = ModelClient(provider, purpose="trackE-proposals", effort="medium", max_tokens=16000)
    reply = client.ask_json(ARM_SYSTEM, _proposal_prompt())
    return list(reply.get("proposals", []))[: PROPOSALS_PER_ARM * 2]


def _baseline_random(rng: random.Random) -> list[dict]:
    return [
        {
            "temp_c": round(rng.uniform(*simlab.TEMP_RANGE), 1),
            "catalyst": rng.choice(simlab.CATALYSTS),
            "solvent": rng.choice(simlab.SOLVENTS),
            "predicted_probability": 0.15,
            "rationale": "random baseline",
        }
        for _ in range(PROPOSALS_PER_ARM)
    ]


def _baseline_grid() -> list[dict]:
    grid = []
    for temp in (55.0, 105.0):
        for catalyst in simlab.CATALYSTS:
            if len(grid) >= PROPOSALS_PER_ARM:
                break
            solvent = simlab.SOLVENTS[len(grid) % len(simlab.SOLVENTS)]
            grid.append(
                {
                    "temp_c": temp,
                    "catalyst": catalyst,
                    "solvent": solvent,
                    "predicted_probability": 0.15,
                    "rationale": "coarse grid baseline",
                }
            )
    return grid[:PROPOSALS_PER_ARM]


def _screen(proposals: list[dict]) -> tuple[list[dict], list[dict]]:
    eligible, excluded = [], []
    seen = set()
    for proposal in proposals:
        try:
            temp = float(proposal["temp_c"])
            catalyst = str(proposal["catalyst"])
            solvent = str(proposal["solvent"])
        except (KeyError, TypeError, ValueError):
            excluded.append({"proposal": proposal, "code": "E-MISSING"})
            continue
        if not simlab.valid_condition(temp, catalyst, solvent):
            excluded.append({"proposal": proposal, "code": "E-SCOPE"})
            continue
        key = (round(temp), catalyst, solvent)
        if key in seen:
            excluded.append({"proposal": proposal, "code": "E-DUP"})
            continue
        seen.add(key)
        eligible.append({**proposal, "temp_c": temp, "catalyst": catalyst, "solvent": solvent})
    return eligible, excluded


def run(out_dir: Path, providers: list[str] | None = None,
        custom_askers: dict | None = None) -> dict:
    providers = providers if providers is not None else list(PROVIDERS)
    custom_askers = custom_askers or {}
    out_dir = Path(out_dir)
    registration = _registration(
        out_dir,
        providers + list(custom_askers) + ["baseline_random", "baseline_grid"],
    )

    arms: dict[str, list[dict]] = {}
    for provider in providers:
        arms[provider] = _model_proposals(provider)
    for name, asker in custom_askers.items():
        try:
            reply = asker(ARM_SYSTEM, _proposal_prompt())
            arms[name] = list(reply.get("proposals", []))[: PROPOSALS_PER_ARM * 2]
        except Exception as exc:  # noqa: BLE001
            arms[name] = []
            (out_dir / f"asker_error_{name}.txt").write_text(str(exc), encoding="utf-8")
    arms["baseline_random"] = _baseline_random(random.Random(7))
    arms["baseline_grid"] = _baseline_grid()

    report: dict = {"registration": registration, "arms": {}}
    test_queue: list[tuple[str, dict]] = []
    for arm, proposals in arms.items():
        eligible, excluded = _screen(proposals)
        report["arms"][arm] = {
            "N_generated": len(proposals),
            "N_eligible": len(eligible),
            "exclusions": excluded,
            "proposals": eligible,
        }
        test_queue.extend((arm, p) for p in eligible)

    # Blinded execution: randomized run order, arm labels not given to the lab.
    random.Random(42).shuffle(test_queue)
    for arm, proposal in test_queue:
        primary = simlab.simulate(proposal["temp_c"], proposal["catalyst"], proposal["solvent"], 1)
        proposal["primary_yield"] = primary
        proposal["primary_positive"] = primary >= simlab.SUCCESS_THRESHOLD
        if proposal["primary_positive"]:
            confirm = simlab.simulate(proposal["temp_c"], proposal["catalyst"], proposal["solvent"], 2)
            proposal["confirmatory_yield"] = confirm
            proposal["confirmatory_positive"] = confirm >= simlab.SUCCESS_THRESHOLD

    for arm, data in report["arms"].items():
        eligible = data["proposals"]
        tested = eligible  # test-all policy
        p3 = [p for p in tested if p.get("primary_positive")]
        p4 = [p for p in p3 if p.get("confirmatory_positive")]
        brier = (
            sum(
                (float(p.get("predicted_probability", 0.5)) - (1.0 if p.get("primary_positive") else 0.0)) ** 2
                for p in tested
            )
            / len(tested)
            if tested
            else None
        )
        data["ladder"] = {
            "N_generated": data["N_generated"],
            "N_eligible": data["N_eligible"],
            "N_selected": len(tested),
            "N_tested": len(tested),
            "N_primary_positive": len(p3),
            "N_confirmatory_positive": len(p4),
        }
        data["tested_hit_rate"] = len(p3) / len(tested) if tested else None
        data["confirmed_hit_rate"] = len(p4) / len(tested) if tested else None
        data["calibration_brier"] = brier

    report["permitted_claim"] = (
        "Under the registered simulator project, each arm's confirmatory"
        " positives among tested eligible proposals are as reported."
        " This is simulator-based experimental design, not empirical discovery."
    )
    (out_dir / "trackE_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
