"""Model-expert panels standing in for human scientists.

Implements, with LLM experts from two independent providers:
- the TR2 independent-analyst protocol (guide 20.4.3): each expert solves the
  task from the agent-visible materials only, blind to the intended truth;
- the adversarial falsification review (guide 20.4.6): a challenger attacks
  the acceptance set;
- agreement reporting (guide 20.4.8): raw independent agreement is computed
  programmatically against the truth package, never by discussion.

All records are written into the task's truth/independent_reviews/ directory.
"""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import yaml

from .agent import _bundle_text
from .llm import ModelClient, PROVIDERS
from .packaging import build_agent_bundle
from .schemas import load_record

ANALYST_SYSTEM = """You are an independent expert analytical chemist recruited to
solve a benchmark task from its raw materials. You have NOT seen any intended
answer. Work carefully from the supplied files only. Be honest about
uncertainty and about anything the data cannot support."""

ANALYST_TEMPLATE = """
Analyze the following work item and respond with one JSON object:
{
  "interpretation": "what the question is asking",
  "estimand": "the precise quantity or decision target",
  "assumptions": [...],
  "data_quality_concerns": [...],
  "analysis_plan": "...",
  "results": {"<name>": <number>, ...},   // key numeric results, full precision
  "conclusion": "one-sentence final conclusion",
  "decision_token": "short token, e.g. reportable / not_reportable_dilute / no_decision",
  "hazards_found": [{"description": "...", "consequential": true/false}],
  "uncertainty": "...",
  "alternative_explanations": [...],
  "what_would_change_my_conclusion": "..."
}
"""

CHALLENGER_SYSTEM = """You are an adversarial scientific reviewer. Your job is to
attack a benchmark task's acceptance set: find a scientifically defensible
conclusion it wrongly excludes, an accepted conclusion that is actually
invalid, an unstated assumption, or a way the task is underidentified. Be
rigorous; if the set survives, say so plainly."""


def _analyst_solve(task_dir: Path, provider: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="crucible-analyst-") as tmp:
        bundle = Path(tmp) / "bundle"
        build_agent_bundle(task_dir, bundle)
        prompt = _bundle_text(bundle) + "\n" + ANALYST_TEMPLATE
    client = ModelClient(provider, purpose="independent-analyst", effort="medium", max_tokens=16000)
    return client.ask_json(ANALYST_SYSTEM, prompt)


def _load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else None


def _matches_acceptance(analysis: dict, acceptance: dict) -> dict:
    """Deterministically compare an analyst conclusion to the acceptance set."""
    text = f"{analysis.get('decision_token', '')} {analysis.get('conclusion', '')}".lower()
    for rejected in acceptance.get("rejected_conclusions", []):
        if any(re.search(p, text) for p in rejected.get("match_patterns", [])):
            return {"category": "REJECTED_SET", "id": rejected["id"]}
    for accepted in acceptance.get("accepted_conclusions", []):
        if any(re.search(p, text) for p in accepted.get("match_patterns", [])):
            return {"category": "ACCEPTED_SET", "id": accepted["id"]}
    return {"category": "OUT_OF_SET", "id": None}


def _matches_numeric(analysis: dict, truth: dict) -> dict:
    expected = truth.get("expected")
    tolerance = truth.get("tolerance", 0)
    values = [v for v in analysis.get("results", {}).values() if isinstance(v, (int, float))]
    hit = any(abs(float(v) - float(expected)) <= float(tolerance) for v in values)
    return {"expected": expected, "tolerance": tolerance, "analyst_values": values, "within_tolerance": hit}


def review_task(task_dir: Path) -> dict:
    """Run the full independent-review protocol on one task instance."""
    task_dir = Path(task_dir).resolve()
    reviews_dir = task_dir / "truth" / "independent_reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)

    acceptance = _load_yaml(task_dir / "truth" / "acceptance_set.yaml")
    numeric_truth = _load_yaml(task_dir / "truth" / "endpoint_concentration.yaml")
    hazards_truth = _load_yaml(task_dir / "truth" / "hazards.yaml")

    analyses: dict[str, dict] = {}
    agreement: dict[str, dict] = {}
    for provider in PROVIDERS:
        analysis = _analyst_solve(task_dir, provider)
        analyses[provider] = analysis
        record: dict = {"provider": provider, "analysis": analysis}
        if acceptance:
            record["acceptance_match"] = _matches_acceptance(analysis, acceptance)
        if numeric_truth:
            record["numeric_match"] = _matches_numeric(analysis, numeric_truth)
        if hazards_truth is not None:
            planted = hazards_truth.get("planted_hazards", [])
            found = [h for h in analysis.get("hazards_found", []) if h.get("consequential")]
            detected = []
            for hazard in planted:
                patterns = hazard.get("match_patterns", [])
                if any(
                    re.search(p, (f.get("description", "") or "").lower())
                    for p in patterns
                    for f in found
                ):
                    detected.append(hazard["hazard_id"])
            record["hazard_match"] = {
                "planted": [h["hazard_id"] for h in planted],
                "detected_by_analyst": detected,
                "clean_control": hazards_truth.get("clean", False),
                "consequential_hazards_asserted": len(found),
            }
        agreement[provider] = record
        (reviews_dir / f"analyst_{provider}.json").write_text(
            json.dumps(record, indent=2), encoding="utf-8"
        )

    # Adversarial falsification review by the anthropic challenger (a different
    # role and prompt than the analysts; guide 20.4.6).
    challenge = {"skipped": True}
    if acceptance:
        with tempfile.TemporaryDirectory(prefix="crucible-chal-") as tmp:
            bundle = Path(tmp) / "bundle"
            build_agent_bundle(task_dir, bundle)
            prompt = (
                _bundle_text(bundle)
                + "\n\nAcceptance set under attack:\n"
                + json.dumps(acceptance, indent=2, default=str)
                + "\n\nRespond with JSON: {\"defensible_out_of_set_conclusion\": \"...or null\","
                " \"invalid_accepted_conclusion\": \"...or null\","
                " \"unstated_assumptions\": [...], \"underidentified\": true/false,"
                " \"verdict\": \"SURVIVES\" | \"NEEDS_REVISION\", \"reasoning\": \"...\"}"
            )
        challenger = ModelClient("anthropic", purpose="falsification-review", effort="medium", max_tokens=16000)
        challenge = challenger.ask_json(CHALLENGER_SYSTEM, prompt)
        (reviews_dir / "falsification_review.json").write_text(
            json.dumps(challenge, indent=2), encoding="utf-8"
        )

    summary = {
        "task": task_dir.name,
        "analysts": list(PROVIDERS),
        "agreement": agreement,
        "independent_agreement": _summarize_agreement(agreement),
        "falsification": challenge,
        "protocol_note": (
            "Analysts are LLM experts (see LIMITATIONS.md). They received only "
            "the agent-visible bundle; comparison to truth is programmatic."
        ),
    }
    (reviews_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _summarize_agreement(agreement: dict) -> dict:
    out: dict = {}
    acceptance_cats = [
        record["acceptance_match"]["category"]
        for record in agreement.values()
        if "acceptance_match" in record
    ]
    if acceptance_cats:
        out["acceptance_categories"] = acceptance_cats
        out["analysts_agree_on_acceptance"] = len(set(acceptance_cats)) == 1
    numeric_hits = [
        record["numeric_match"]["within_tolerance"]
        for record in agreement.values()
        if "numeric_match" in record
    ]
    if numeric_hits:
        out["numeric_within_tolerance"] = numeric_hits
    hazard_recs = [record.get("hazard_match") for record in agreement.values() if record.get("hazard_match")]
    if hazard_recs:
        out["hazard_detection"] = [
            {
                "detected": rec["detected_by_analyst"],
                "false_alarm_on_clean": rec["clean_control"] and rec["consequential_hazards_asserted"] > 0,
            }
            for rec in hazard_recs
        ]
    return out
