"""Verifier-correction rescoring (guide 20.9 / 32.17).

When a verifier bug is fixed, every affected stored submission is re-verified
with the corrected implementation, the campaign reports are rebuilt, and a
public correction record with before/after values is written. Nothing is
silently patched: the correction file lists every cell whose outcome changed.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .campaign import _track_c_metrics, build_scorecard
from .paths import find_repo_root
from .tracks import trackB
from .verification import run_verification

TASK_DIRS = {
    "N0-s101": "tasks_public/CHEM-LC-CAL-001/instances/N0-s101",
    "N1-s102": "tasks_public/CHEM-LC-CAL-001/instances/N1-s102",
    "N0-s103": "tasks_public/CHEM-LC-CAL-001/instances/N0-s103",
    "N2-s104": "tasks_public/CHEM-LC-CAL-002/instances/N2-s104",
    "S1-s201": "tasks_public/OPS-AUTH-001/instances/S1-s201",
}


def _reverify(repo: Path, task_name: str, submission: Path) -> dict:
    return run_verification(repo / TASK_DIRS[task_name], submission)


def rescore_campaign(label: str, correction_id: str, reason: str, root: Path | None = None) -> dict:
    repo = find_repo_root(root)
    out_dir = repo / "runs" / label
    changes: list[dict] = []

    # 1. Campaign agent outcomes -------------------------------------------
    outcomes_path = out_dir / "agent_outcomes.json"
    outcomes = json.loads(outcomes_path.read_text(encoding="utf-8"))
    for outcome in outcomes:
        submission = out_dir / "submissions" / outcome["system"] / outcome["task"]
        if not submission.exists():
            continue
        fresh = _reverify(repo, outcome["task"], submission)
        if fresh["reliable_completion"] != outcome["reliable_completion"]:
            changes.append(
                {
                    "surface": "campaign",
                    "cell": f"{outcome['system']}/{outcome['task']}",
                    "old": outcome["reliable_completion"],
                    "new": fresh["reliable_completion"],
                }
            )
        outcome["reliable_completion"] = fresh["reliable_completion"]
        outcome["abstained"] = fresh.get("abstained", False)
        outcome["failed_gate_claim_ids"] = fresh["failed_gate_claim_ids"]
        outcome["critical_operational_failures"] = fresh["critical_operational_failures"]
        outcome["diagnostic_profiles"] = fresh["diagnostic_profiles"]
        outcome["leaf_results"] = [
            {k: r[k] for k in ("claim_id", "status", "credit")} for r in fresh.get("leaf_results", [])
        ]
    outcomes_path.write_text(json.dumps(outcomes, indent=2), encoding="utf-8")

    # 2. Track B and C rebuilt from rescored outcomes ----------------------
    b_rows = [
        {"instance_id": f"{o['template']}-{o['task']}", "system": o["system"],
         "reliable_completion": o["reliable_completion"]}
        for o in outcomes
    ]
    trackB.generalization_report(b_rows, repo, out_dir / "trackB_report.json")
    (out_dir / "trackC_report.json").write_text(
        json.dumps(_track_c_metrics(outcomes), indent=2), encoding="utf-8"
    )

    # 3. Track F submissions ------------------------------------------------
    trackf_path = out_dir / "trackF" / "trackF_report.json"
    if trackf_path.exists():
        report = json.loads(trackf_path.read_text(encoding="utf-8"))
        for cell in report["results"]:
            submission = out_dir / "trackF" / f"{cell['participant']}-{cell['form']}-{cell['condition']}"
            if not submission.exists():
                continue
            fresh = _reverify(repo, cell["form"], submission)
            if fresh["reliable_completion"] != cell["reliable_completion"]:
                changes.append(
                    {
                        "surface": "trackF",
                        "cell": f"{cell['participant']}/{cell['form']}/{cell['condition']}",
                        "old": cell["reliable_completion"],
                        "new": fresh["reliable_completion"],
                    }
                )
            cell["reliable_completion"] = fresh["reliable_completion"]
            cell["failed_gate_claim_ids"] = fresh["failed_gate_claim_ids"]
        aided = [c["reliable_completion"] for c in report["results"] if c["condition"] == "assisted"]
        alone = [c["reliable_completion"] for c in report["results"] if c["condition"] == "alone"]
        report["ate_estimate"] = (
            (sum(aided) / len(aided)) - (sum(alone) / len(alone)) if aided and alone else None
        )
        trackf_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # 4. Mechanism submissions ----------------------------------------------
    mech_path = out_dir / "mechanism" / "mechanism_report.json"
    if mech_path.exists():
        report = json.loads(mech_path.read_text(encoding="utf-8"))
        for cell in report["cells"]:
            gate = "on" if cell["verification_gate"] else "off"
            submission = out_dir / "mechanism" / f"{cell['provider']}-gate{gate}-{cell['task']}"
            if not submission.exists():
                continue
            fresh = _reverify(repo, cell["task"], submission)
            if fresh["reliable_completion"] != cell["reliable_completion"]:
                changes.append(
                    {
                        "surface": "mechanism",
                        "cell": f"{cell['provider']}/gate-{gate}/{cell['task']}",
                        "old": cell["reliable_completion"],
                        "new": fresh["reliable_completion"],
                    }
                )
            cell["reliable_completion"] = fresh["reliable_completion"]
            cell["failed_gate_claim_ids"] = fresh["failed_gate_claim_ids"]
        def rate(gate: bool):
            subset = [c["reliable_completion"] for c in report["cells"] if c["verification_gate"] == gate]
            return sum(subset) / len(subset) if subset else None
        report["rcr_gate_on"] = rate(True)
        report["rcr_gate_off"] = rate(False)
        report["effect_estimate"] = (
            rate(True) - rate(False) if rate(True) is not None and rate(False) is not None else None
        )
        mech_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # 5. Scorecard + correction record --------------------------------------
    build_scorecard(repo, out_dir, outcomes)
    correction = {
        "correction_id": correction_id,
        "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "reason": reason,
        "cells_changed": changes,
        "rescope": "all stored submissions re-verified with the corrected verifier",
    }
    corrections_path = repo / "release" / "0.2.0" / "corrections.md"
    corrections_path.parent.mkdir(parents=True, exist_ok=True)
    existing = corrections_path.read_text(encoding="utf-8") if corrections_path.exists() else "# Corrections\n"
    entry = [f"\n## {correction_id} ({correction['date']})", "", reason, ""]
    if changes:
        entry.append("| Surface | Cell | Old | New |")
        entry.append("|---|---|---|---|")
        for change in changes:
            entry.append(f"| {change['surface']} | {change['cell']} | {change['old']} | {change['new']} |")
    else:
        entry.append("No cell outcomes changed after rescoring.")
    corrections_path.write_text(existing + "\n".join(entry) + "\n", encoding="utf-8")
    return correction
