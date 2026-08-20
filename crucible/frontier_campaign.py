"""Campaign 0.3.0: Marigold (native product) + frontier models via OpenRouter.

Systems under evaluation:
- marigold            : the native product on the user's GPU server, driven
                        through its real conversation API (mode N1, no agent
                        override, its own 48-tool spec and model routing).
- six OpenRouter models (one flagship per remaining frontier lab), run through
  the SAME two-call reference agent used in campaign 0.2.0 so the harness is
  matched across API models. Marigold is reported separately as a native
  product (guide 23.17: product rows are never causal model comparisons).

Judging: the Anthropic judge (meta-evaluated at 91% accuracy on the gold set)
judges every submission here - it is cross-family for every evaluated system
(Marigold's base model is gpt-5.6-sol). Judge verdicts remain advisory.

Stages are restartable exactly like campaign 0.2.0.
"""
from __future__ import annotations

import json
from pathlib import Path

from .agent import run_agent
from .judge import judge_submission
from .llm import extract_json, usage_summary
from .marigold_adapter import oneshot, run_marigold
from .paths import find_repo_root
from .stats import rate_with_denominator
from .tracks import trackD, trackE

FRONTIER_MODELS = [
    "google/gemini-3.7-flash",
    "x-ai/grok-4.6",
    "deepseek/deepseek-v4-pro",
    "qwen/qwen3.8-max",
    "moonshotai/kimi-k3",
    "z-ai/glm-5.2",
]

CAMPAIGN_INSTANCES = [
    ("CHEM-LC-CAL-001/instances/N0-s101", "CHEM-LC-CAL-001", "A", "B0"),
    ("CHEM-LC-CAL-001/instances/N1-s102", "CHEM-LC-CAL-001", "C", "B0"),
    ("CHEM-LC-CAL-001/instances/N0-s103", "CHEM-LC-CAL-001", "A", "B1"),
    ("CHEM-LC-CAL-002/instances/N2-s104", "CHEM-LC-CAL-002", "C", "B2"),
    ("OPS-AUTH-001/instances/S1-s201", "OPS-AUTH-001", "H", "B0"),
]

JUDGE_PROVIDER = "anthropic"


def _safe(name: str) -> str:
    return name.replace("/", "_").replace(".", "-")


def _outcome_row(outcome: dict, system: str, template: str, task: str, track: str,
                 holdout: str, judge: dict | None) -> dict:
    return {
        "system": system,
        "task": task,
        "template": template,
        "track": track,
        "holdout": holdout,
        "reliable_completion": outcome["reliable_completion"],
        "abstained": outcome.get("abstained", False),
        "failed_gate_claim_ids": outcome["failed_gate_claim_ids"],
        "critical_operational_failures": outcome["critical_operational_failures"],
        "integrity_problems": outcome.get("integrity_problems", []),
        "leaf_results": [
            {k: r[k] for k in ("claim_id", "status", "credit")}
            for r in outcome.get("leaf_results", [])
        ],
        "judge": judge,
        "agent": outcome.get("agent", {}),
    }


def _judge_safe(task_dir: Path, sub_dir: Path) -> dict | None:
    try:
        verdict = judge_submission(task_dir, sub_dir, JUDGE_PROVIDER)
        return {"provider": JUDGE_PROVIDER, "verdict": verdict["verdict"],
                "confidence": verdict.get("confidence")}
    except Exception as exc:  # noqa: BLE001
        return {"provider": JUDGE_PROVIDER, "verdict": "ERROR", "error": str(exc)[:200]}


def run_frontier_campaign(label: str = "release-0.3.0", root: Path | None = None,
                          budget_minutes_marigold: int = 25) -> dict:
    repo = find_repo_root(root)
    out_dir = repo / "runs" / label
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. OpenRouter frontier systems (per-system restartable) ---------------
    for model_id in FRONTIER_MODELS:
        stage = out_dir / "or_systems" / f"{_safe(model_id)}.json"
        if stage.exists():
            continue
        rows = []
        for rel, template, track, holdout in CAMPAIGN_INSTANCES:
            task_dir = repo / "tasks_public" / rel
            sub_dir = out_dir / "submissions" / _safe(model_id) / task_dir.name
            try:
                outcome = run_agent(task_dir, sub_dir, f"openrouter/{model_id}",
                                    verification_gate=True, purpose="frontier-agent")
            except Exception as exc:  # noqa: BLE001 - a dead model is an outcome, not a crash
                outcome = {
                    "reliable_completion": False, "abstained": False,
                    "failed_gate_claim_ids": [], "critical_operational_failures": [],
                    "integrity_problems": [f"agent run failed: {str(exc)[:300]}"],
                    "leaf_results": [], "agent": {"provider": f"openrouter/{model_id}"},
                }
            judge = _judge_safe(task_dir, sub_dir) if sub_dir.exists() else None
            rows.append(_outcome_row(outcome, model_id, template, task_dir.name,
                                     track, holdout, judge))
        stage.parent.mkdir(parents=True, exist_ok=True)
        stage.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    # 2. Marigold native product -------------------------------------------
    marigold_stage = out_dir / "marigold_outcomes.json"
    if not marigold_stage.exists():
        rows = []
        for rel, template, track, holdout in CAMPAIGN_INSTANCES:
            task_dir = repo / "tasks_public" / rel
            sub_dir = out_dir / "submissions" / "marigold" / task_dir.name
            try:
                outcome = run_marigold(task_dir, sub_dir, budget_minutes=budget_minutes_marigold)
            except Exception as exc:  # noqa: BLE001
                outcome = {
                    "reliable_completion": False, "abstained": False,
                    "failed_gate_claim_ids": [], "critical_operational_failures": [],
                    "integrity_problems": [f"marigold run failed: {str(exc)[:300]}"],
                    "leaf_results": [], "agent": {"provider": "marigold"},
                }
            judge = _judge_safe(task_dir, sub_dir) if sub_dir.exists() else None
            rows.append(_outcome_row(outcome, "marigold", template, task_dir.name,
                                     track, holdout, judge))
            marigold_stage.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    # 3. Tracks D and E for the new systems ---------------------------------
    def marigold_asker(system_prompt: str, user_prompt: str) -> dict:
        text = oneshot(system_prompt + "\n\n" + user_prompt, budget_minutes=10)
        return extract_json(text)

    if not (out_dir / "trackD" / "trackD_report.json").exists():
        trackD.run(out_dir / "trackD",
                   providers=[f"openrouter/{m}" for m in FRONTIER_MODELS],
                   custom_askers={"marigold": marigold_asker})
    if not (out_dir / "trackE" / "trackE_report.json").exists():
        trackE.run(out_dir / "trackE",
                   providers=[f"openrouter/{m}" for m in FRONTIER_MODELS],
                   custom_askers={"marigold": marigold_asker})

    scorecard = build_frontier_scorecard(repo, out_dir)
    return {"scorecard_path": str(scorecard)}


def build_frontier_scorecard(repo: Path, out_dir: Path) -> Path:
    systems: dict[str, list[dict]] = {}
    for stage in sorted((out_dir / "or_systems").glob("*.json")):
        rows = json.loads(stage.read_text(encoding="utf-8"))
        if rows:
            systems[rows[0]["system"]] = rows
    marigold_stage = out_dir / "marigold_outcomes.json"
    if marigold_stage.exists():
        systems["marigold"] = json.loads(marigold_stage.read_text(encoding="utf-8"))

    def load(name: str, subdir: str):
        path = out_dir / subdir / name
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    track_d = load("trackD_report.json", "trackD")
    track_e = load("trackE_report.json", "trackE")

    lines = ["# CRUCIBLE frontier scorecard - campaign " + out_dir.name, ""]
    lines.append("Native product row (marigold) and API-model rows are NOT causally")
    lines.append("comparable (guide 23.17): marigold runs its own 48-tool agentic")
    lines.append("harness on the user's GPU server; API models run the matched two-call")
    lines.append("reference agent. All caveats in docs/LIMITATIONS.md apply; judge")
    lines.append("verdicts are advisory (anthropic judge, 91% gold-set accuracy).")
    lines.append("")
    lines.append("## Reliable completion by system (5 task instances)")
    lines.append("")
    lines.append("| System | Harness | Overall | Track A (2) | Track C (2) | Track H (1) | Judge PASS |")
    lines.append("|---|---|---|---|---|---|---|")
    for system, rows in sorted(systems.items()):
        def _cnt(track=None):
            subset = [r for r in rows if track is None or r["track"] == track]
            return sum(r["reliable_completion"] for r in subset), len(subset)
        overall = _cnt()
        a = _cnt("A")
        c = _cnt("C")
        h = _cnt("H")
        judge_pass = sum(1 for r in rows if (r.get("judge") or {}).get("verdict") == "PASS")
        harness = "native product" if system == "marigold" else "reference agent"
        lines.append(
            f"| {system} | {harness} | {overall[0]}/{overall[1]} | {a[0]}/{a[1]} "
            f"| {c[0]}/{c[1]} | {h[0]}/{h[1]} | {judge_pass}/{len(rows)} |"
        )
    lines.append("")
    lines.append("Campaign 0.2.0 reference (same tasks, same reference agent, post-CORR-001):")
    lines.append("claude-opus-5 5/5, gpt-5.6-sol 4/5 - see runs/release-0.2.0/scorecard.md.")
    lines.append("")

    lines.append("## Per-system failure notes")
    for system, rows in sorted(systems.items()):
        for row in rows:
            if not row["reliable_completion"]:
                why = row["failed_gate_claim_ids"] or row["integrity_problems"] or ["(gate)"]
                lines.append(f"- {system} / {row['task']}: {str(why)[:160]}")
    lines.append("")

    if track_d:
        lines.append("## Track D - simulator forecasting (Brier, lower is better)")
        for name, score in sorted(track_d["scores"].items(),
                                  key=lambda kv: (kv[1] is None, kv[1])):
            display = f"{score:.3f}" if isinstance(score, float) else str(score)
            lines.append(f"- {name}: {display}")
        lines.append("")
    if track_e:
        lines.append("## Track E - simulator discovery ladder")
        for arm, data in track_e["arms"].items():
            ladder = data.get("ladder", {})
            brier = data.get("calibration_brier")
            brier_txt = f"; Brier {brier:.3f}" if isinstance(brier, float) else ""
            lines.append(
                f"- {arm}: generated {ladder.get('N_generated', 0)}, eligible "
                f"{ladder.get('N_eligible', 0)}, tested {ladder.get('N_tested', 0)}, "
                f"primary+ {ladder.get('N_primary_positive', 0)}, confirmed+ "
                f"{ladder.get('N_confirmatory_positive', 0)}{brier_txt}"
            )
        lines.append("")

    lines.append("## Cost accounting (local ledger; marigold's own spend is on its server)")
    for model, totals in usage_summary(repo).items():
        lines.append(
            f"- {model}: {totals['calls']} calls, {totals['input_tokens']:,} in / "
            f"{totals['output_tokens']:,} out tokens"
        )

    scorecard_path = out_dir / "scorecard.md"
    scorecard_path.write_text("\n".join(lines), encoding="utf-8")
    return scorecard_path
