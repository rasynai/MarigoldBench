"""CRUCIBLE 2.0 rubric judge: deterministic anchors + criterion-level LLM
judgments with mandatory verbatim evidence (bias-mitigation design from the
2025-26 judge literature: binary per-criterion verdicts, evidence quotes
verified by substring check, cross-family assignment, gold-set meta-eval).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .llm import ModelClient

JUDGE_SYSTEM = """You are a meticulous scientific grader. You receive a task prompt, the
data artifacts the candidate saw, and the candidate's answer. You grade the
answer against rubric criteria ONE BY ONE. For each criterion output met
true/false. A criterion is met ONLY if the answer itself demonstrates it -
not if it is merely plausible or implied. For every met=true you MUST supply
"evidence": a short VERBATIM quote (<=25 words) copied exactly from the
candidate's answer that demonstrates the criterion. Penalty criteria
describe BAD behavior: met=true means the answer exhibits that bad behavior.
Judge only what is written; never reward confident prose over correct
content. Respond with JSON only."""

JUDGE_TEMPLATE = """# Task prompt (what the candidate was asked)
{prompt}

# Artifacts the candidate saw (truncated)
{artifacts}

# Ground truth for this instance (grader-only; the candidate never saw this)
{truth}

# Reference strong answer (grader-only, for calibration - the candidate's
# answer need not match its wording, only its demonstrated science)
{reference}

# Candidate answer (formatting stripped)
{submission}

# Rubric criteria to judge
{criteria}

Respond with JSON: {{"verdicts": [{{"id": "...", "met": true/false,
"evidence": "verbatim quote if met else empty string"}}]}} - one verdict per
criterion id listed, in order, nothing else."""


def _strip_style(text: str) -> str:
    """Style normalization before judging: markdown formatting biases judges
    far more than position does (Judging the Judges, 2026: up to +0.76 vs
    <=0.04), so grade content, not typography. The evidence-quote substring
    check runs against this same stripped text."""
    out = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
    out = re.sub(r"\*\*(.+?)\*\*", r"\1", out)
    out = re.sub(r"\*(.+?)\*", r"\1", out)
    out = re.sub(r"^\s*[-*+]\s+", "- ", out, flags=re.M)
    out = re.sub(r"`([^`]*)`", r"\1", out)
    return out


def _final_json_block(submission: str) -> dict | None:
    blocks = re.findall(r"```json\s*(.*?)```", submission, re.S)
    for block in reversed(blocks):
        try:
            parsed = json.loads(block.strip())
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return None


def _norm_token(value) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def check_anchor(item: dict, answers: dict | None, truth: dict) -> bool:
    if answers is None:
        return False
    auto = item["auto"]
    field, kind = auto["field"], auto.get("kind", "number")
    if field not in answers:
        return False
    expected = truth.get(auto["truth_key"])
    got = answers[field]
    if kind == "token":
        return _norm_token(got) == _norm_token(expected)
    try:
        got_f, exp_f = float(got), float(expected)
    except (TypeError, ValueError):
        return False
    tol_key = auto.get("tol_key")
    tol = float(truth.get(tol_key, 0.0)) if tol_key else max(abs(exp_f) * 0.01, 1e-9)
    return abs(got_f - exp_f) <= tol


def _norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def judge_submission2(instance_dir: Path, submission: str, judge_provider: str,
                     max_artifact_chars: int = 14000) -> dict:
    instance_dir = Path(instance_dir)
    rubric = json.loads(re.sub(r"^//.*\n", "",
                        (instance_dir / "truth2" / "rubric.json").read_text(encoding="utf-8")))
    truth = json.loads(re.sub(r"^//.*\n", "",
                       (instance_dir / "truth2" / "truth.json").read_text(encoding="utf-8")))
    prompt = (instance_dir / "prompt.md").read_text(encoding="utf-8")
    artifact_texts = []
    for artifact in sorted((instance_dir / "artifacts").glob("*")):
        artifact_texts.append(f"--- {artifact.name} ---\n"
                              + artifact.read_text(encoding="utf-8", errors="replace"))
    artifacts_blob = "\n".join(artifact_texts)[:max_artifact_chars]

    answers = _final_json_block(submission)
    results = []
    judged_items = []
    for item in rubric:
        if item.get("auto"):
            met = check_anchor(item, answers, truth)
            results.append({"id": item["id"], "group": item["group"],
                            "points": item["points"], "met": met,
                            "mode": "deterministic"})
        else:
            judged_items.append(item)

    if judged_items:
        reference = (instance_dir / "truth2" / "reference_answer.md").read_text(
            encoding="utf-8", errors="replace")
        client = ModelClient(judge_provider, purpose="judge2", max_tokens=20000,
                             effort="medium")
        stripped = _strip_style(submission)
        verdict_by_id: dict = {}
        # Batches capped at 8 criteria: verification accuracy degrades when
        # many criteria share one call over longer outputs (RuVerBench, 2026).
        for start in range(0, len(judged_items), 8):
            batch = judged_items[start:start + 8]
            criteria_desc = json.dumps(
                [{"id": i["id"], "group": i["group"], "points": i["points"],
                  "text": i["text"]} for i in batch], indent=1)
            reply = client.ask_json(JUDGE_SYSTEM, JUDGE_TEMPLATE.format(
                prompt=prompt[:8000], artifacts=artifacts_blob,
                truth=json.dumps(truth, default=str)[:4000],
                reference=_strip_style(reference)[:6000],
                submission=stripped[:24000], criteria=criteria_desc))
            for v in reply.get("verdicts", []):
                verdict_by_id[v.get("id")] = v
        sub_norm = _norm_ws(stripped)
        for item in judged_items:
            verdict = verdict_by_id.get(item["id"], {})
            met = bool(verdict.get("met"))
            evidence = str(verdict.get("evidence") or "")
            if met and item["points"] > 0:
                # anti-hallucination: the quote must actually appear
                if _norm_ws(evidence) and _norm_ws(evidence) in sub_norm:
                    pass
                else:
                    met = False
            results.append({"id": item["id"], "group": item["group"],
                            "points": item["points"], "met": met,
                            "evidence": evidence[:200], "mode": "judged"})

    pos_total = sum(r["points"] for r in results if r["points"] > 0)
    earned = sum(r["points"] for r in results if r["met"])
    score = max(0.0, earned / pos_total) if pos_total else 0.0
    by_group: dict = {}
    for r in results:
        g = by_group.setdefault(r["group"], {"met": 0, "n": 0})
        g["n"] += 1
        g["met"] += int(r["met"])
    return {
        "score": round(score, 4), "passed": score >= 0.70,
        "earned_points": earned, "possible_points": pos_total,
        "answers_block_present": answers is not None,
        "verdicts": results, "groups": by_group,
        "judge_provider": judge_provider,
    }
