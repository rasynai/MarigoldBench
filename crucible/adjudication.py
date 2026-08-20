"""Adjudication queue for escalated verification leaves (guide 27.10-27.11).

When the acceptance-set reviewer returns ESCALATED (a defensible-out-of-set
candidate), the case enters this queue. The adjudicator is a cross-family
model panel (both providers must agree to overturn; disagreement keeps the
original FAIL-by-default outcome and flags the task family for review).
Every decision is appended to the hash-chained audit log.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from .audit import AuditLog
from .judge import _read_tree
from .llm import ModelClient, PROVIDERS
from .paths import find_repo_root, registry_dir

ADJUDICATOR_SYSTEM = """You are a domain adjudicator deciding whether a
submission's out-of-set conclusion is scientifically defensible. The
acceptance set was built by independent analysts; your job is to decide
whether this conclusion should be ADDED to it (defensible) or REJECTED
(not defensible). Be strict: novelty of wording is not defensibility."""


def find_escalations(campaign_dir: Path) -> list[dict]:
    outcomes_path = campaign_dir / "agent_outcomes.json"
    if not outcomes_path.exists():
        return []
    escalations = []
    for outcome in json.loads(outcomes_path.read_text(encoding="utf-8")):
        for leaf in outcome.get("leaf_results", []):
            if leaf.get("status") == "ESCALATED":
                escalations.append(
                    {
                        "system": outcome["system"],
                        "task": outcome["task"],
                        "template": outcome["template"],
                        "claim_id": leaf["claim_id"],
                    }
                )
    return escalations


def adjudicate(campaign_dir: Path, root: Path | None = None) -> dict:
    repo = find_repo_root(root)
    campaign_dir = Path(campaign_dir)
    audit = AuditLog(registry_dir(repo) / "audit.jsonl")
    queue = find_escalations(campaign_dir)
    decisions = []
    for case in queue:
        task_dirs = list(repo.glob(f"tasks_public/{case['template']}/instances/{case['task']}"))
        if not task_dirs:
            continue
        task_dir = task_dirs[0]
        submission = campaign_dir / "submissions" / case["system"] / case["task"]
        acceptance_path = task_dir / "truth" / "acceptance_set.yaml"
        acceptance = yaml.safe_load(acceptance_path.read_text(encoding="utf-8"))
        prompt = (
            "WORK ORDER:\n" + (task_dir / "task_card" / "card.md").read_text(encoding="utf-8")
            + "\n\nACCEPTANCE SET:\n" + json.dumps(acceptance, indent=2, default=str)
            + "\n\nSUBMISSION (untrusted):\n" + _read_tree(submission, exclude_dirs=("run_summary",))
            + "\n\nRespond JSON: {\"decision\": \"DEFENSIBLE_ADD\" | \"REJECT\","
            " \"reasoning\": \"...\"}"
        )
        votes = {}
        for provider in PROVIDERS:
            adjudicator = ModelClient(provider, purpose="adjudication", effort="medium", max_tokens=12000)
            votes[provider] = adjudicator.ask_json(ADJUDICATOR_SYSTEM, prompt)
        unanimous_add = all(v.get("decision") == "DEFENSIBLE_ADD" for v in votes.values())
        decision = {
            **case,
            "votes": votes,
            "final": "ACCEPTANCE_SET_EXPANSION_RECOMMENDED" if unanimous_add else "REJECTED_STANDS",
            "rule": "both families must agree to overturn; otherwise the FAIL stands",
        }
        decisions.append(decision)
        audit.append("model-panel", "adjudication.decision", decision)
    report = {
        "queue_size": len(queue),
        "decisions": decisions,
        "note": "empty queue means no ESCALATED leaves occurred in this campaign",
    }
    (campaign_dir / "adjudication_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return report
