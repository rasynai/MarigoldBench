"""Track B: hidden-generalization ladder bookkeeping and reporting.

Every instance carries a holdout level (B0-B9) and exposure class in its
instance.yaml; this module writes the exposure ledger and produces the
by-level generalization report from campaign outcomes (guide sections 10, 22).
Levels not yet populated are reported as NOT POPULATED - never averaged away.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

LEVELS = [f"B{i}" for i in range(10)]


def write_exposure_ledger(repo_root: Path) -> Path:
    """One ledger row per instance (guide 22.3)."""
    rows = []
    for instance_yaml in sorted(repo_root.glob("tasks_public/*/instances/*/instance.yaml")):
        record = yaml.safe_load(instance_yaml.read_text(encoding="utf-8"))
        rows.append(
            {
                "instance_id": record["instance_id"],
                "template_id": record["template_id"],
                "holdout_level": record["holdout_level"],
                "exposure_class": record["exposure_class"],
                "split": record["split"],
                "source_public": False,
                "task_text_public": True,
                "truth_public": True,
                "note": (
                    "Synthetic construction; whole repository is local, so all"
                    " instances are at best E3 once evaluated systems' vendors"
                    " could ever see them. Sealed cohorts require new"
                    " instances created after a system freeze."
                ),
            }
        )
    ledger_path = repo_root / "registry" / "exposure_ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return ledger_path


def generalization_report(campaign_outcomes: list[dict], repo_root: Path, out_path: Path) -> dict:
    levels: dict[str, dict] = {}
    instance_levels = {}
    for instance_yaml in repo_root.glob("tasks_public/*/instances/*/instance.yaml"):
        record = yaml.safe_load(instance_yaml.read_text(encoding="utf-8"))
        instance_levels[record["instance_id"]] = record["holdout_level"]

    for outcome in campaign_outcomes:
        level = instance_levels.get(outcome["instance_id"], "?")
        bucket = levels.setdefault(level, {"attempted": 0, "reliable": 0, "systems": {}})
        bucket["attempted"] += 1
        bucket["reliable"] += int(outcome["reliable_completion"])
        system_bucket = bucket["systems"].setdefault(outcome["system"], {"attempted": 0, "reliable": 0})
        system_bucket["attempted"] += 1
        system_bucket["reliable"] += int(outcome["reliable_completion"])

    report = {
        "rule": "levels are reported separately and never averaged (guide 10.6)",
        "levels": {},
    }
    for level in LEVELS:
        if level in levels:
            data = levels[level]
            report["levels"][level] = {
                "reliable": data["reliable"],
                "attempted": data["attempted"],
                "by_system": data["systems"],
            }
        else:
            report["levels"][level] = "NOT POPULATED (no cohort at this level yet)"
    gap = None
    if isinstance(report["levels"].get("B0"), dict) and isinstance(report["levels"].get("B1"), dict):
        b0 = report["levels"]["B0"]
        b1 = report["levels"]["B1"]
        if b0["attempted"] and b1["attempted"]:
            gap = b0["reliable"] / b0["attempted"] - b1["reliable"] / b1["attempted"]
    report["gap_B0_to_B1"] = gap
    report["strongest_populated_level"] = max(
        (lvl for lvl, v in report["levels"].items() if isinstance(v, dict)), default=None
    )
    report["claim_boundary"] = (
        "Populated levels reach B2. No B3+ or sealed cohort exists, so no"
        " contamination-resistant generalization claim is permitted."
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
