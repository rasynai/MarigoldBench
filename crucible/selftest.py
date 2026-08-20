"""Verifier self-tests: accepted example submissions must pass, adversarial
wrong submissions must fail (guide 20.3.3 steps 10-11, 21.19).

A verifier that accepts the oracle is not enough; it must reject realistic
wrong work.
"""
from __future__ import annotations

from pathlib import Path

from .verification import run_verification


def run_selftests(task_dir: Path) -> dict:
    task_dir = Path(task_dir).resolve()
    report: dict = {"task_dir": str(task_dir), "accepted": [], "rejected": [], "ok": True}

    for kind, expect_reliable in (("accepted", True), ("rejected", False)):
        base = task_dir / "verification" / "tests" / kind
        if not base.exists():
            report["ok"] = False
            report[kind].append({"submission": None, "error": f"{base} missing"})
            continue
        for submission in sorted(p for p in base.iterdir() if p.is_dir()):
            outcome = run_verification(task_dir, submission)
            got = outcome["reliable_completion"]
            entry = {
                "submission": submission.name,
                "expected_reliable": expect_reliable,
                "got_reliable": got,
                "ok": got == expect_reliable,
                "failed_gate_claim_ids": outcome.get("failed_gate_claim_ids", []),
                "critical_failures": (
                    outcome.get("critical_scientific_failures", [])
                    + outcome.get("critical_operational_failures", [])
                ),
            }
            if not entry["ok"]:
                report["ok"] = False
            report[kind].append(entry)
    return report
