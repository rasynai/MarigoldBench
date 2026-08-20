"""Track G: epistemic process scoring via structured checkpoints (guide 15).

Two-stage protocol on the above-range chromatography task (N1-s102):

  Stage 1 (pre-evidence): the system sees the calibration standards and method
  note but NOT the unknown sample. It must commit hypotheses about what could
  make the naive workflow invalid, per-hypothesis predicted observations, and
  a decision rule - BEFORE the observation is revealed.

  Stage 2 (post-evidence): the unknown's peak area is revealed. The system
  must update its hypothesis probabilities and choose an action.

Scoring uses observable commitments only (no chain-of-thought): coverage,
prediction commitment, discrimination, evidence uptake, and final decision.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from ..llm import ModelClient, PROVIDERS

G_SYSTEM = """You are a scientist following a registered epistemic protocol:
commit to hypotheses and predictions BEFORE seeing new evidence, then update
honestly after. Your commitments are scored; hedging or omitting them scores
zero."""

STAGE1_PROMPT = """A five-point external-standard HPLC-UV calibration for analyte A:

concentration_mg_per_l,peak_area
1.0,5150
2.0,10230
5.0,25190
10.0,50180
20.0,100240

Method note: report concentrations only within the validated calibration range
(1-20 mg/L); if a sample falls outside it, flag it rather than extrapolating.

An unknown sample U-02 was injected. You have NOT yet seen its peak area.
Before it is revealed, commit a checkpoint as JSON:
{"candidate_hypotheses": [{"id": "H1", "text": "...", "probability": <0-1>}, ...],
 "next_test": "what you will look at first",
 "predictions": [{"hypothesis_id": "H1", "expected_observation": "..."}, ...],
 "decision_rule": "how the observation will decide your reporting action"}
Include at least three materially distinct hypotheses about what the unknown's
measurement may show and what could make naive reporting invalid.
"""

STAGE2_TEMPLATE = """The unknown U-02 peak area is revealed: 160480.

Your pre-observation checkpoint was:
{checkpoint}

Update as JSON:
{{"updated_hypotheses": [{{"id": "H1", "probability": <0-1>}}, ...],
  "evidence_interpretation": "...",
  "chosen_action": "...",
  "decision_token": "reportable" | "not_reportable_dilute" | "other",
  "final_claim": "one sentence"}}
"""

ABOVE_RANGE_PATTERNS = (
    r"above.*(range|calibration|standard)",
    r"outside.*(range|calibration)",
    r"exceed.*(range|calibration|highest)",
    r"extrapolat",
    r"out of range",
    r"higher than.*(standard|range|calibrat)",
)


def _matches_above_range(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in ABOVE_RANGE_PATTERNS)


def _score(checkpoint: dict, update: dict) -> dict:
    hypotheses = checkpoint.get("candidate_hypotheses", [])
    predictions = checkpoint.get("predictions", [])
    hypothesis_ids = {h.get("id") for h in hypotheses}
    codes: list[str] = []

    coverage_count = len({(h.get("text") or "").strip().lower() for h in hypotheses if h.get("text")})
    above_range_hypotheses = [h for h in hypotheses if _matches_above_range(h.get("text", ""))]
    covered_true_explanation = bool(above_range_hypotheses)
    if coverage_count < 2:
        codes.append("G-NOALT")

    prediction_ids = {p.get("hypothesis_id") for p in predictions}
    prediction_commitment = bool(predictions) and prediction_ids <= hypothesis_ids | {None}
    if not predictions:
        codes.append("G-NOPRED")

    distinct_predictions = {(p.get("expected_observation") or "").strip().lower() for p in predictions}
    discriminating = len(distinct_predictions) >= min(2, max(1, len(predictions)))
    if predictions and not discriminating:
        codes.append("G-NODISC")

    updated = {u.get("id"): float(u.get("probability", 0)) for u in update.get("updated_hypotheses", [])}
    prior = {h.get("id"): float(h.get("probability", 0)) for h in hypotheses}
    uptake = None
    if above_range_hypotheses:
        target = above_range_hypotheses[0].get("id")
        if target in updated and target in prior:
            uptake = updated[target] - prior[target]
            if uptake <= 0:
                codes.append("G-NOUPDATE")
    else:
        codes.append("G-IGNORE" if not _matches_above_range(update.get("evidence_interpretation", "")) else "G-NOALT")

    decision_text = f"{update.get('decision_token', '')} {update.get('final_claim', '')} {update.get('chosen_action', '')}"
    correct_decision = bool(re.search(r"not[_ ]reportable|dilut|cannot be reported", decision_text.lower())) and not re.search(
        r"(?<!not )(?<!not_)\breportable", decision_text.lower()
    )
    if not correct_decision:
        codes.append("G-OVERCOMMIT")

    return {
        "hypothesis_coverage": coverage_count,
        "true_explanation_pre_registered": covered_true_explanation,
        "prediction_commitment": prediction_commitment,
        "discriminating_predictions": discriminating,
        "evidence_uptake_delta": uptake,
        "final_decision_correct": correct_decision,
        "failure_codes": codes,
    }


def run(out_dir: Path) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report: dict = {"protocol": "pre/post-evidence structured checkpoints (guide 15.3)", "systems": {}}
    for provider in PROVIDERS:
        client = ModelClient(provider, purpose="trackG-checkpoints", effort="medium", max_tokens=16000)
        checkpoint = client.ask_json(G_SYSTEM, STAGE1_PROMPT)
        update = client.ask_json(
            G_SYSTEM, STAGE2_TEMPLATE.format(checkpoint=json.dumps(checkpoint, indent=2))
        )
        report["systems"][provider] = {
            "checkpoint": checkpoint,
            "update": update,
            "scores": _score(checkpoint, update),
        }
    (out_dir / "trackG_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
