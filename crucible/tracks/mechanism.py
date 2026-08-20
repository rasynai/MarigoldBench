"""Mechanism study: causal effect of the verification-gate component (C-VERIFY).

Guide section 17: a single-component toggle on the modular reference agent,
run under matched conditions (same model, same prompt, same max_tokens, same
tasks). The gate adds at most one repair round, so this is an M2 NATIVE-COST
comparison (the gated arm may spend more tokens); token spend per arm is
recorded from the usage ledger so the cost side is visible.

Permitted claim: "In this reference agent on these tasks, enabling the
verification gate changed reliable completion by X points (native-cost)."
Prohibited: any generalization to other agents, products, or task populations.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..agent import run_agent
from ..llm import PROVIDERS

TASKS = ("CHEM-LC-CAL-001/instances/N0-s101", "CHEM-LC-CAL-001/instances/N1-s102")


def run(out_dir: Path, repo_root: Path) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cells = []
    for provider in PROVIDERS:
        for gate in (True, False):
            for task_rel in TASKS:
                task_dir = repo_root / "tasks_public" / task_rel
                label = f"{provider}-gate{'on' if gate else 'off'}-{task_dir.name}"
                outcome = run_agent(
                    task_dir,
                    out_dir / label,
                    provider,
                    verification_gate=gate,
                    purpose="mechanism-study",
                )
                cells.append(
                    {
                        "provider": provider,
                        "verification_gate": gate,
                        "task": task_dir.name,
                        "reliable_completion": outcome["reliable_completion"],
                        "attempts": outcome["agent"]["attempts"],
                        "failed_gate_claim_ids": outcome["failed_gate_claim_ids"],
                    }
                )

    def rate(gate: bool) -> float | None:
        subset = [c["reliable_completion"] for c in cells if c["verification_gate"] == gate]
        return sum(subset) / len(subset) if subset else None

    report = {
        "component_contract": (
            "Treatment: after the first draft, local verifier failures are fed"
            " back for exactly one repair round. Control: first draft is final."
            " Model, prompt, contract, and max_tokens identical."
        ),
        "resource_condition": "M2 native-cost (treatment may use one extra model call)",
        "cells": cells,
        "rcr_gate_on": rate(True),
        "rcr_gate_off": rate(False),
        "effect_estimate": (rate(True) - rate(False))
        if rate(True) is not None and rate(False) is not None
        else None,
        "n_caveat": "4 runs per arm; effect estimate is a pilot signal, not a stable law",
        "permitted_claim_scope": "this reference agent, these two tasks, native-cost protocol",
    }
    (out_dir / "mechanism_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
