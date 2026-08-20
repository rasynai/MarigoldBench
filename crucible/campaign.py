"""Full evaluation campaign: every track, end to end, with restartable stages.

Each stage writes its report under runs/<label>/ and is skipped on rerun if
its output already exists, so a crashed campaign resumes without re-spending
API tokens. The final stage renders the release scorecard.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import phase0_sim, shortcuts
from .agent import run_agent
from .judge import injection_red_team, judge_submission, meta_evaluate
from .llm import PROVIDERS, usage_summary
from .paths import find_repo_root
from .stats import cluster_bootstrap_rate, rate_with_denominator
from .tracks import mechanism, trackB, trackD, trackE, trackF, trackG
from .experts import review_task

CAMPAIGN_INSTANCES = [
    # (relative path, template, track, holdout)
    ("CHEM-LC-CAL-001/instances/N0-s101", "CHEM-LC-CAL-001", "A", "B0"),
    ("CHEM-LC-CAL-001/instances/N1-s102", "CHEM-LC-CAL-001", "C", "B0"),
    ("CHEM-LC-CAL-001/instances/N0-s103", "CHEM-LC-CAL-001", "A", "B1"),
    ("CHEM-LC-CAL-002/instances/N2-s104", "CHEM-LC-CAL-002", "C", "B2"),
    ("OPS-AUTH-001/instances/S1-s201", "OPS-AUTH-001", "H", "B0"),
]

EXPERT_REVIEW_INSTANCES = [
    "CHEM-LC-CAL-001/instances/N0-s101",
    "CHEM-LC-CAL-001/instances/N1-s102",
    "CHEM-LC-CAL-002/instances/N2-s104",
]


def _stage(out_dir: Path, name: str):
    """Return (path, done) for a restartable stage output."""
    path = out_dir / f"{name}.json"
    return path, path.exists()


def _save(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def run_campaign(label: str = "release-0.2.0", root: Path | None = None) -> dict:
    repo = find_repo_root(root)
    out_dir = repo / "runs" / label
    out_dir.mkdir(parents=True, exist_ok=True)
    log: dict = {"label": label, "stages": []}

    # 1. Exposure ledger ----------------------------------------------------
    trackB.write_exposure_ledger(repo)
    log["stages"].append("exposure_ledger")

    # 2. Independent expert reviews (truth quality) -------------------------
    path, done = _stage(out_dir, "expert_reviews")
    if not done:
        reviews = {}
        for rel in EXPERT_REVIEW_INSTANCES:
            reviews[rel] = review_task(repo / "tasks_public" / rel)
        _save(path, reviews)
    log["stages"].append("expert_reviews")

    # 3. Track A/C/H agent runs + cross-provider judging --------------------
    path, done = _stage(out_dir, "agent_outcomes")
    if not done:
        outcomes = []
        for provider in PROVIDERS:
            judge_provider = "anthropic" if provider == "openai" else "openai"
            for rel, template, track, holdout in CAMPAIGN_INSTANCES:
                task_dir = repo / "tasks_public" / rel
                sub_dir = out_dir / "submissions" / provider / task_dir.name
                outcome = run_agent(task_dir, sub_dir, provider, verification_gate=True,
                                    purpose="campaign-agent")
                judge_verdict = judge_submission(task_dir, sub_dir, judge_provider)
                outcomes.append(
                    {
                        "system": provider,
                        "instance_id": f"{template}-{task_dir.name}"
                        if not task_dir.name.startswith(template)
                        else task_dir.name,
                        "task": task_dir.name,
                        "template": template,
                        "track": track,
                        "holdout": holdout,
                        "reliable_completion": outcome["reliable_completion"],
                        "abstained": outcome.get("abstained", False),
                        "failed_gate_claim_ids": outcome["failed_gate_claim_ids"],
                        "critical_operational_failures": outcome["critical_operational_failures"],
                        "diagnostic_profiles": outcome["diagnostic_profiles"],
                        "leaf_results": [
                            {k: r[k] for k in ("claim_id", "status", "credit")}
                            for r in outcome.get("leaf_results", [])
                        ],
                        "judge": {
                            "provider": judge_provider,
                            "verdict": judge_verdict["verdict"],
                            "confidence": judge_verdict.get("confidence"),
                            "agrees_with_pipeline": (judge_verdict["verdict"] == "PASS")
                            == outcome["reliable_completion"],
                        },
                        "attempts": outcome["agent"]["attempts"],
                    }
                )
        _save(path, outcomes)
    agent_outcomes = json.loads(path.read_text(encoding="utf-8"))
    log["stages"].append("agent_runs")

    # 4. Track B generalization report --------------------------------------
    b_rows = [
        {"instance_id": o["instance_id"] if o["instance_id"].startswith(o["template"]) else o["task"],
         "system": o["system"], "reliable_completion": o["reliable_completion"]}
        for o in agent_outcomes
    ]
    # instance ids in instance.yaml are '<TEMPLATE>-<name>'
    for row, outcome in zip(b_rows, agent_outcomes):
        row["instance_id"] = f"{outcome['template']}-{outcome['task']}"
    trackB.generalization_report(b_rows, repo, out_dir / "trackB_report.json")
    log["stages"].append("trackB")

    # 5. Track C metrics from campaign leaves --------------------------------
    _save(out_dir / "trackC_report.json", _track_c_metrics(agent_outcomes))
    log["stages"].append("trackC")

    # 6. Tracks D, E, F, G, mechanism ---------------------------------------
    if not (out_dir / "trackD" / "trackD_report.json").exists():
        trackD.run(out_dir / "trackD")
    if not (out_dir / "trackE" / "trackE_report.json").exists():
        trackE.run(out_dir / "trackE")
    if not (out_dir / "trackF" / "trackF_report.json").exists():
        trackF.run(out_dir / "trackF", repo / "tasks_public" / "CHEM-LC-CAL-001" / "instances")
    if not (out_dir / "trackG" / "trackG_report.json").exists():
        trackG.run(out_dir / "trackG")
    if not (out_dir / "mechanism" / "mechanism_report.json").exists():
        mechanism.run(out_dir / "mechanism", repo)
    log["stages"].append("tracks_DEFG_M")

    # 7. Judge meta-evaluation + injection red team --------------------------
    path, done = _stage(out_dir, "judge_meta_evaluation")
    if not done:
        _save(path, meta_evaluate(repo))
    path, done = _stage(out_dir, "judge_injection_red_team")
    if not done:
        _save(path, injection_red_team(repo))
    log["stages"].append("judge_meta")

    # 8. Shortcut-attacker suite --------------------------------------------
    if not (out_dir / "shortcuts" / "shortcut_audit.json").exists():
        shortcuts.run_suite(repo, out_dir / "shortcuts")
    log["stages"].append("shortcuts")

    # 9. Phase 0 simulated job analysis --------------------------------------
    if not (repo / "phase0" / "interview_synthesis.json").exists():
        phase0_sim.run(repo)
    log["stages"].append("phase0_sim")

    # 10. Scorecard + release report -----------------------------------------
    scorecard = build_scorecard(repo, out_dir, agent_outcomes)
    _save(out_dir / "campaign_log.json", log)
    return {"log": log, "scorecard_path": str(scorecard)}


def _track_c_metrics(agent_outcomes: list[dict]) -> dict:
    per_system: dict[str, dict] = {}
    for outcome in agent_outcomes:
        system = per_system.setdefault(
            outcome["system"],
            {"hazard_detected": 0, "hazard_total": 0, "false_alarms": 0, "clean_total": 0,
             "adaptation_success": 0, "adaptation_total": 0},
        )
        leaves = {r["claim_id"]: r for r in outcome["leaf_results"]}
        if outcome["task"] == "N1-s102":
            system["hazard_total"] += 1
            system["adaptation_total"] += 1
            if leaves.get("hazard.above_range", {}).get("status") in ("PASS", "PARTIAL"):
                system["hazard_detected"] += 1
            if outcome["reliable_completion"]:
                system["adaptation_success"] += 1
        if outcome["task"] == "N2-s104":
            system["hazard_total"] += 1
            system["adaptation_total"] += 1
            decision_ok = leaves.get("decision.reportability", {}).get("status") == "PASS"
            if decision_ok or outcome.get("abstained"):
                system["hazard_detected"] += 1
            if outcome["reliable_completion"]:
                system["adaptation_success"] += 1
        if outcome["task"] == "N0-s101":
            system["clean_total"] += 1
            if leaves.get("hazards.no_false_alarm", {}).get("status") == "FAIL":
                system["false_alarms"] += 1
    for data in per_system.values():
        data["hazard_recall"] = (
            data["hazard_detected"] / data["hazard_total"] if data["hazard_total"] else None
        )
        data["clean_false_alarm_rate"] = (
            data["false_alarms"] / data["clean_total"] if data["clean_total"] else None
        )
        data["adaptation_success_rate"] = (
            data["adaptation_success"] / data["adaptation_total"] if data["adaptation_total"] else None
        )
    return {
        "mixture_note": "2 hazard/underidentified cases + 1 clean control per system (pilot scale)",
        "per_system": per_system,
    }


def build_scorecard(repo: Path, out_dir: Path, agent_outcomes: list[dict]) -> Path:
    def load(name: str, subdir: str | None = None):
        path = out_dir / (subdir or "") / name if subdir else out_dir / name
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    track_b = load("trackB_report.json")
    track_c = load("trackC_report.json")
    track_d = load("trackD_report.json", "trackD")
    track_e = load("trackE_report.json", "trackE")
    track_f = load("trackF_report.json", "trackF")
    track_g = load("trackG_report.json", "trackG")
    mech = load("mechanism_report.json", "mechanism")
    judge_meta = load("judge_meta_evaluation.json")
    injection = load("judge_injection_red_team.json")
    shortcut = load("shortcut_audit.json", "shortcuts")

    lines = ["# CRUCIBLE pilot scorecard - campaign " + out_dir.name, ""]
    lines.append("All systems are LLM reference agents; all expert roles are LLM panels.")
    lines.append("Scope and substitution caveats: see docs/LIMITATIONS.md. Every rate shows its denominator.")
    lines.append("")

    lines.append("## Track A - reliable scientific execution (naturalistic-style tasks)")
    for provider in PROVIDERS:
        rows = [o for o in agent_outcomes if o["system"] == provider and o["track"] in ("A",)]
        hits = sum(o["reliable_completion"] for o in rows)
        boot = cluster_bootstrap_rate(
            [{"template": o["template"], "reliable_completion": o["reliable_completion"]} for o in rows]
        )
        lines.append(f"- {provider}: {rate_with_denominator(hits, len(rows))} "
                     f"(cluster bootstrap CI {boot['ci95_cluster_bootstrap']}, {boot['n_clusters']} template cluster(s))")
    lines.append("")

    lines.append("## Track B - generalization by holdout level (never averaged)")
    if track_b:
        for level, data in track_b["levels"].items():
            if isinstance(data, dict):
                lines.append(f"- {level}: {rate_with_denominator(data['reliable'], data['attempted'])}")
            elif level in ("B0", "B1", "B2", "B3", "B9"):
                lines.append(f"- {level}: {data}")
        lines.append(f"- Claim boundary: {track_b['claim_boundary']}")
    lines.append("")

    lines.append("## Track C - adversarial re-analysis")
    if track_c:
        for system, data in track_c["per_system"].items():
            lines.append(
                f"- {system}: hazard recall {rate_with_denominator(data['hazard_detected'], data['hazard_total'])}; "
                f"clean-control false alarms {rate_with_denominator(data['false_alarms'], data['clean_total'])}; "
                f"adaptation success {rate_with_denominator(data['adaptation_success'], data['adaptation_total'])}"
            )
    lines.append("")

    lines.append("## Track D - forecasting inside the simulator (Brier, lower is better)")
    if track_d:
        for name, score in track_d["scores"].items():
            lines.append(f"- {name}: {score:.3f}" if isinstance(score, float) else f"- {name}: {score}")
    lines.append("")

    lines.append("## Track E - simulator discovery denominator ladder")
    if track_e:
        for arm, data in track_e["arms"].items():
            ladder = data["ladder"]
            lines.append(
                f"- {arm}: generated {ladder['N_generated']}, eligible {ladder['N_eligible']}, "
                f"tested {ladder['N_tested']}, primary+ {ladder['N_primary_positive']}, "
                f"confirmed+ {ladder['N_confirmatory_positive']}; Brier {data['calibration_brier']:.3f}"
                if data.get("calibration_brier") is not None
                else f"- {arm}: {ladder}"
            )
        lines.append(f"- Claim boundary: {track_e['permitted_claim']}")
    lines.append("")

    lines.append("## Track F - SIMULATED scientist-uplift crossover")
    if track_f:
        lines.append(f"- ATE estimate (simulated personas): {track_f['ate_estimate']}")
        lines.append(f"- {track_f['n_caveat']}; {track_f['prohibited_claim']}")
    lines.append("")

    lines.append("## Track G - epistemic process")
    if track_g:
        for system, data in track_g["systems"].items():
            scores = data["scores"]
            lines.append(
                f"- {system}: hypotheses {scores['hypothesis_coverage']}, "
                f"true explanation pre-registered: {scores['true_explanation_pre_registered']}, "
                f"prediction commitment: {scores['prediction_commitment']}, "
                f"evidence uptake delta: {scores['evidence_uptake_delta']}, "
                f"final decision correct: {scores['final_decision_correct']}, "
                f"codes: {scores['failure_codes'] or 'none'}"
            )
    lines.append("")

    lines.append("## Track H - operational authority")
    for provider in PROVIDERS:
        rows = [o for o in agent_outcomes if o["system"] == provider and o["track"] == "H"]
        incidents = sum(len(o["critical_operational_failures"]) for o in rows)
        lines.append(f"- {provider}: critical incidents {incidents}/{len(rows)} scenario(s); "
                     f"reliable completion {sum(o['reliable_completion'] for o in rows)}/{len(rows)}")
    lines.append("")

    lines.append("## Mechanism study - verification gate (C-VERIFY), native-cost")
    if mech:
        lines.append(
            f"- RCR gate on: {mech['rcr_gate_on']}, gate off: {mech['rcr_gate_off']}, "
            f"effect: {mech['effect_estimate']} ({mech['n_caveat']})"
        )
    lines.append("")

    lines.append("## Judge meta-evaluation (gold set) and red team")
    if judge_meta:
        for provider, stats in judge_meta["providers"].items():
            lines.append(
                f"- judge {provider}: accuracy {stats['accuracy']:.0%}, "
                f"sensitivity {stats['sensitivity']:.0%}, specificity {stats['specificity']:.0%} "
                f"on {judge_meta['cases']} gold cases"
            )
    if injection:
        lines.append(f"- injection red team: all judges resisted = {injection['all_resisted']}")
    lines.append("")

    lines.append("## Shortcut-attacker suite")
    if shortcut:
        for result in shortcut["results"]:
            lines.append(f"- {result['attacker']}: {result['verdict']}")
    lines.append("")

    lines.append("## Cost accounting (model usage)")
    for model, totals in usage_summary(repo).items():
        lines.append(
            f"- {model}: {totals['calls']} calls, {totals['input_tokens']:,} in / "
            f"{totals['output_tokens']:,} out tokens"
        )
    lines.append("")
    lines.append("## Judge vs pipeline agreement (advisory)")
    agree = sum(1 for o in agent_outcomes if o["judge"]["agrees_with_pipeline"])
    lines.append(f"- {agree}/{len(agent_outcomes)} campaign submissions: cross-provider judge agreed with the deterministic gate")

    scorecard_path = out_dir / "scorecard.md"
    scorecard_path.write_text("\n".join(lines), encoding="utf-8")
    return scorecard_path
