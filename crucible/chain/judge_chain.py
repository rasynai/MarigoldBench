"""Notice detection and advisory reasoning quality.

This is the only place a model touches scoring, and it can never move VCC.
Its job is the one thing determinism cannot see: whether the answer NAMED the
judgment call at a fork, independently of whether it then ACTED on it.

The gap between those two is the headline diagnostic. GeneBench-Pro identified
"models detect diagnostic red flags but fail to propagate them into changed
analysis decisions" as the dominant failure of frontier systems in this
setting, and then graded pass/fail only, which cannot separate the two. Here
noticing is judged from the prose and acting is checked deterministically from
the answer block, so the difference is measurable.

Bias mitigations, each adopted because it was measured to work: criterion-level
binary verdicts rather than a holistic score; a verbatim evidence quote that is
substring-verified against the answer; formatting stripped before judging;
small batches; and a judge from a different model family than the candidate.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from ..llm import ModelClient
from .judge2_style import strip_style  # shared formatting normaliser

NOTICE_SYSTEM = """You are checking whether a scientific report NAMED a specific issue. You are
not judging whether the report is right, well written, or whether it acted on
the issue - only whether it explicitly identified and described that issue.

A criterion is met ONLY if the report itself names it. Do not credit vague
gestures ("there may be some concerns about the data"), and do not credit a
report for merely reproducing a number that happens to be affected. For every
met=true you MUST supply a VERBATIM quote of at most 25 words copied exactly
from the report. Respond with JSON only."""

NOTICE_TEMPLATE = """# The report being checked
{submission}

# Issues to check for
{forks}

For each issue, did the report explicitly name and describe it?

Respond with JSON: {{"verdicts": [{{"id": "&lt;stage key&gt;", "noticed": true/false,
"evidence": "verbatim quote if noticed else empty string"}}]}}"""

QUALITY_SYSTEM = """You are grading the scientific quality of a report against a reference
answer that is known to be correct. Judge method soundness, whether
uncertainty and limitations are stated honestly, and whether the conclusion is
actionable for the decision the work order poses. Do not reward confident
prose, length, or formatting. Respond with JSON only."""

QUALITY_TEMPLATE = """# Work order
{prompt}

# Reference answer (known correct; the candidate need not match its wording)
{reference}

# Candidate report
{submission}

Score each dimension 0-4 (0 absent, 2 adequate, 4 excellent):
method_soundness, uncertainty_honesty, actionability.

Respond with JSON: {{"method_soundness": n, "uncertainty_honesty": n,
"actionability": n, "one_line_justification": "..."}}"""


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def judge_notice(instance_dir: Path, submission: str, judge_provider: str) -> dict:
    """Which forks did the answer name? Deterministic acting is scored
    elsewhere; this is only the noticing half of the gap."""
    instance_dir = Path(instance_dir)
    raw = (instance_dir / "truth_chain" / "key.json").read_text(encoding="utf-8")
    key = json.loads(re.sub(r"^//.*\n", "", raw))
    stages = key["stages"]
    if not submission.strip():
        return {"verdicts": {}, "judge_provider": judge_provider, "empty": True}

    stripped = strip_style(submission)
    forks = json.dumps([{"id": name, "issue": spec["fork"]}
                        for name, spec in stages.items()], indent=1)
    client = ModelClient(judge_provider, purpose="chain-judge-notice",
                         max_tokens=8000, effort="medium")
    try:
        reply = client.ask_json(NOTICE_SYSTEM, NOTICE_TEMPLATE.format(
            submission=stripped[:20000], forks=forks))
    except Exception as exc:  # noqa: BLE001 - judging is advisory; never fatal
        return {"verdicts": {}, "judge_provider": judge_provider, "error": str(exc)[:200]}

    body = _norm(stripped)
    verdicts = {}
    for verdict in reply.get("verdicts", []):
        name = verdict.get("id")
        if name not in stages:
            continue
        noticed = bool(verdict.get("noticed"))
        evidence = str(verdict.get("evidence") or "")
        # A quote that is not actually in the answer is a hallucinated credit.
        if noticed and _norm(evidence) not in body:
            noticed = False
        verdicts[name] = {"noticed": noticed, "evidence": evidence[:200]}
    return {"verdicts": verdicts, "judge_provider": judge_provider}


def judge_quality(instance_dir: Path, submission: str, judge_provider: str) -> dict:
    """Advisory reasoning score. Never enters VCC."""
    instance_dir = Path(instance_dir)
    if not submission.strip():
        return {"total": 0, "judge_provider": judge_provider, "empty": True}
    prompt = (instance_dir / "prompt.md").read_text(encoding="utf-8")
    reference = re.sub(r"^<!--.*?-->\n", "",
                       (instance_dir / "truth_chain" / "reference_answer.md")
                       .read_text(encoding="utf-8"))
    client = ModelClient(judge_provider, purpose="chain-judge-quality",
                         max_tokens=6000, effort="medium")
    try:
        reply = client.ask_json(QUALITY_SYSTEM, QUALITY_TEMPLATE.format(
            prompt=prompt[:6000], reference=strip_style(reference)[:6000],
            submission=strip_style(submission)[:16000]))
    except Exception as exc:  # noqa: BLE001
        return {"total": None, "judge_provider": judge_provider, "error": str(exc)[:200]}
    dims = {k: reply.get(k) for k in
            ("method_soundness", "uncertainty_honesty", "actionability")}
    scores = [v for v in dims.values() if isinstance(v, (int, float))]
    return {**dims, "total": round(sum(scores) / (4 * len(scores)), 4) if scores else None,
            "justification": str(reply.get("one_line_justification") or "")[:300],
            "judge_provider": judge_provider}


def notice_act_gap(scored_runs: list[dict], notice_reports: list[dict]) -> dict:
    """P(named the fork) - P(got that stage right). A large positive gap is the
    signature failure: the system SAW the problem and did not let it change the
    analysis."""
    noticed = acted = both = total = 0
    for run, report in zip(scored_runs, notice_reports):
        for stage in run["stages"]:
            verdict = report.get("verdicts", {}).get(stage["stage"])
            if verdict is None:
                continue
            total += 1
            n, a = bool(verdict["noticed"]), bool(stage["correct"])
            noticed += n
            acted += a
            both += n and a
    if not total:
        return {"n_stage_observations": 0}
    return {
        "n_stage_observations": total,
        "notice_rate": round(noticed / total, 4),
        "act_rate": round(acted / total, 4),
        "gap": round((noticed - acted) / total, 4),
        "acted_given_noticed": round(both / noticed, 4) if noticed else None,
        "noticed_but_did_not_act": round((noticed - both) / total, 4),
    }
