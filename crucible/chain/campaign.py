"""CRUCIBLE-CHAIN campaign: run candidates single-turn, score deterministically,
report the ladder.

Scoring never consults a model. The judge (judge_chain) contributes only the
advisory reasoning score and the "did it name the fork" signal for the
notice-act gap; it cannot move VCC.

    python -m crucible.chain.campaign run --system anthropic [--shard i/n]
    python -m crucible.chain.campaign scorecard
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from ..frontier_campaign import FRONTIER_MODELS
from ..llm import ModelClient, usage_summary
from ..paths import find_repo_root
from .score import (aggregate, cluster_bootstrap_ci, hazard_profile, reliability,
                    score_chain, wilson_interval)

LABEL = "release-3.0.0"

# NVIDIA NIM replaces the OpenRouter fleet for 3.0: same OpenAI-compatible
# wire, a different account, and the OpenRouter balance is exhausted
# (CORR-007). One flagship per vendor family, chosen for diversity of
# training lineage rather than for size.
# Only models this account can actually reach AND that are frontier-class.
# The /models listing advertises 102 models; five distinct account keys were
# probed with live completions (runs/probe_nim_keys.py) and all five reach the
# same six large models. Three are frontier flagships and are evaluated here.
# The other three reachable ones - meta/llama-3.1-70b-instruct and the two
# nvidia/llama-3.3-nemotron-super-49b variants - are a generation behind and
# are deliberately excluded: a benchmark that reports single-digit pass rates
# learns nothing from a system that fails at stage one for capability reasons
# unrelated to scientific judgment. Weak models belong in a harness-uplift
# experiment (does Marigold close the gap?), not in the frontier scorecard.
NIM_MODELS = [
    "nvidia/nemotron-3-ultra-550b-a55b",
    "nvidia/nemotron-3-super-120b-a12b",
    "deepseek-ai/deepseek-v4-flash-0731",
]
API_SYSTEMS = ["anthropic", "openai"] + [f"nvidia/{m}" for m in NIM_MODELS]
OPENROUTER_SYSTEMS = [f"openrouter/{m}" for m in FRONTIER_MODELS]
REPEATS = 3               # pass^3 is the headline; 3 independent runs per instance
HARNESS_CLASS = {"marigold": "H4 (opaque product)"}

CONTRACT = """You are a working scientist completing a real work order. You have the data
files that accompany it and nothing else - no external sources exist for this
job, and no one is available to ask.

Do the analysis yourself. Decide which data are eligible, apply the method the
work order and its attachments specify, and carry the consequences of those
decisions through to your conclusion. If something in the data or in the
request itself would change what a careful scientist reports, say so and let it
change your answer. If everything is sound, do not invent problems.

Show the numbers you rely on. Then finish with the machine-readable block the
work order specifies, using exactly its field names. Each field must contain
ONLY your answer for that field - never a rejected alternative or a competing
hypothesis; a field that names more than one candidate answer is scored as no
answer. Explanations belong in the prose above the block. Give a calibrated
confidence in [0,1] for each field: these are read as the probability that your
value is correct, and being confidently wrong is penalised."""


def _safe(name: str) -> str:
    return name.replace("/", "_").replace(".", "-")


def _index(repo: Path) -> list[dict]:
    path = repo / "registry" / "chain_task_index.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def _key(instance_dir: Path) -> dict:
    raw = (instance_dir / "truth_chain" / "key.json").read_text(encoding="utf-8")
    return json.loads(re.sub(r"^//.*\n", "", raw))


def _render(repo: Path, row: dict) -> str:
    inst = repo / row["path"]
    prompt = (inst / "prompt.md").read_text(encoding="utf-8")
    parts = [f"--- FILE: {a.name} ---\n{a.read_text(encoding='utf-8', errors='replace')}"
             for a in sorted((inst / "artifacts").glob("*"))]
    return prompt + "\n\n# Attached data files\n" + "\n\n".join(parts)


HIDDEN_PER_TEMPLATE = 2   # one per condition family, rotated by template
SEALED_PER_TEMPLATE = 1


def plan(repo: Path, system: str) -> list[tuple[str, dict, int]]:
    """The evaluated subset, fixed and identical for every system.

    Running every instance three times over nine systems is ~5,900 calls and
    does not fit the sponsor's budget. Rather than cut repeats - which would
    destroy the reliability headline, the one number retrying cannot inflate -
    we evaluate a deterministic subsample of instances at the full 3 repeats.
    Selection is by sorted position only: it cannot depend on any outcome,
    and every system sees exactly the same instances.
    """
    rows = [r for r in _index(repo) if r["split"] in ("hidden_test", "sealed")]
    rows.sort(key=lambda r: (r["template_id"], r["split"], r["condition"], r["instance"]))

    chosen: list[dict] = []
    by_template: dict[str, list[dict]] = {}
    for row in rows:
        by_template.setdefault(row["template_id"], []).append(row)
    for index, (template_id, group) in enumerate(sorted(by_template.items())):
        hidden = [r for r in group if r["split"] == "hidden_test"]
        sealed = [r for r in group if r["split"] == "sealed"]
        # Rotate which conditions this template contributes so the population
        # stays balanced across C0/H1/F2 without any per-template cherry-picking.
        order = ["H1", "F2", "C0"]
        rotated = order[index % 3:] + order[:index % 3]
        picked: list[dict] = []
        for condition in rotated:
            for row in hidden:
                if row["condition"] == condition and row not in picked:
                    picked.append(row)
                    break
            if len(picked) >= HIDDEN_PER_TEMPLATE:
                break
        chosen += picked[:HIDDEN_PER_TEMPLATE] + sealed[:SEALED_PER_TEMPLATE]

    out = []
    for row in chosen:
        repeats = REPEATS if row["split"] == "hidden_test" else 1
        for run_no in range(1, repeats + 1):
            out.append((f"{row['template_id']}__{row['instance']}__r{run_no}", row, run_no))
    return out


# A run gets exactly one outcome file, and any worker that sees that file skips
# the run forever. So a transient 429 or read timeout would otherwise convert a
# momentary provider hiccup into a permanent scored failure - and the harder we
# parallelise, the more of those we manufacture. Retry the errors that carry no
# information about the system, then censor only if they persist.
TRANSIENT = re.compile(
    r"429|rate.?limit|timeout|timed out|502|503|504|overloaded|connection|"
    r"temporarily|too many requests", re.I)
MAX_ATTEMPTS = 4
BACKOFF_SECONDS = (20, 60, 150)


def _ask_with_retry(system: str, user: str) -> tuple[str, str | None]:
    """Return (reply, censor_reason). censor_reason is None on success.

    Right-censoring an infrastructure death keeps it out of the hazard
    analysis - it is not evidence about which stage a system can reach - but it
    still counts as a failure for VCC, so a retry that succeeds is worth real
    accuracy, not just tidiness.
    """
    last = ""
    for attempt in range(MAX_ATTEMPTS):
        try:
            if system == "marigold":
                from ..marigold_adapter import oneshot
                return oneshot(CONTRACT + "\n\n" + user, budget_minutes=15), None
            client = ModelClient(system, purpose="chain-candidate",
                                 max_tokens=24000, effort="high")
            return client.ask(CONTRACT, user), None
        except Exception as exc:  # noqa: BLE001
            last = str(exc)[:300]
            transient = bool(TRANSIENT.search(last))
            if not transient or attempt == MAX_ATTEMPTS - 1:
                return "", last
            time.sleep(BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)])
    return "", last


def run_candidates(system: str, shard: str | None) -> dict:
    repo = find_repo_root()
    root = repo / "runs" / LABEL / "systems" / _safe(system)
    jobs = plan(repo, system)
    if shard:
        i, n = (int(x) for x in shard.split("/"))
        jobs = jobs[i::n]
    done = skipped = failed = 0
    for run_id, row, run_no in jobs:
        out_path = root / "outcomes" / f"{run_id}.json"
        if out_path.exists():
            skipped += 1
            continue
        user = _render(repo, row)
        try:
            text, censored = _ask_with_retry(system, user)
        except Exception as exc:  # noqa: BLE001
            text, censored = "", str(exc)[:300]
        if censored:
            failed += 1
        result = score_chain(text, _key(repo / row["path"]))
        result.update({"system": system, "run_id": run_id, "run_no": run_no,
                       "template_id": row["template_id"], "instance": row["instance"],
                       "condition": row["condition"], "split": row["split"],
                       "area": row["area"], "workflow": row["workflow"],
                       "censored": censored})
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        (root / "submissions").mkdir(parents=True, exist_ok=True)
        (root / "submissions" / f"{run_id}.md").write_text(text or "", encoding="utf-8")
        done += 1
    return {"system": system, "done": done, "skipped": skipped, "infra_failures": failed}


def _load(repo: Path) -> dict[str, list[dict]]:
    systems: dict[str, list[dict]] = {}
    base = repo / "runs" / LABEL / "systems"
    if not base.exists():
        return systems
    for sys_dir in sorted(base.glob("*")):
        rows = [json.loads(p.read_text(encoding="utf-8"))
                for p in sorted((sys_dir / "outcomes").glob("*.json"))]
        if rows:
            systems[rows[0]["system"]] = rows
    return systems


def build_scorecard() -> Path:
    repo = find_repo_root()
    out_dir = repo / "runs" / LABEL
    systems = _load(repo)
    baselines_path = out_dir / "baselines.json"
    baselines = json.loads(baselines_path.read_text(encoding="utf-8")) \
        if baselines_path.exists() else {"rungs": {}}

    lines = ["# CRUCIBLE-CHAIN scorecard - " + LABEL, ""]
    lines.append("> **READ CORR-010 BEFORE CITING ANY NUMBER BELOW.** This campaign")
    lines.append("> measured a saturated instrument: the work orders printed the method")
    lines.append("> as a checklist and the answer schema enumerated the allowed values,")
    lines.append("> so frontier systems scored 94-100% against a single-digit design")
    lines.append("> target. These are valid measurements OF THE 3.0.0 INSTRUMENT and")
    lines.append("> are published as such; they are not evidence about frontier")
    lines.append("> scientific judgment. The defect is fixed in the 4.0 gates. Separately,")
    lines.append("> 8 templates give a clustered effective n of ~21, which cannot support")
    lines.append("> a public claim at any difficulty (analysis/statistical_power.md).")
    lines.append("")
    lines.append("Every task is an ordered chain of judgment calls in which each stage")
    lines.append("offers a plausible wrong path. A run counts only if EVERY stage and the")
    lines.append("final decision are right, so difficulty compounds by construction.")
    lines.append("")
    lines.append("Read the ladder, not a single number: pass^3 <= pass@1 <= pass@3.")
    lines.append("pass^3 is reliability (all three independent runs succeed) and is what")
    lines.append("retrying cannot inflate; pass@1 is the guard rail, because pass^3 goes")
    lines.append("to a hard zero once pass@1 drops below roughly 8%.")
    lines.append("")
    lines.append("No human baseline exists and none is planned: read every score against")
    lines.append("the baseline ladder below, never against a claim about people.")
    lines.append("")

    lines.append("## Baseline ladder (the scale these scores live on)")
    lines.append("")
    lines.append("| Rung | What it is | VCC rate | Gate |")
    lines.append("|---|---|---|---|")
    names = {"B0": "prior-only (artifacts withheld)", "B1": "degenerate submissions",
             "B5": "naive all-decoy path", "B8": "reference answer",
             "B9": "adversarial submissions"}
    for rung in ("B0", "B1", "B5", "B8", "B9"):
        data = baselines.get("rungs", {}).get(rung)
        if not data:
            continue
        gate = data.get("gate_ok")
        gate_txt = "-" if gate is None else ("PASS" if gate else "**FAIL**")
        lines.append(f"| {rung} | {names[rung]} | {data['vcc_rate']:.3f} | {gate_txt} |")
    lines.append("")

    lines.append("## Systems (hidden split)")
    lines.append("")
    lines.append("| System | Harness | pass^3 | pass@1 [95% CI] | pass@3 | Trap | FalseAlarm | Pushback |")
    lines.append("|---|---|---|---|---|---|---|---|")
    summary: dict = {}
    for system, rows in sorted(systems.items()):
        hidden = [r for r in rows if r["split"] == "hidden_test"]
        if not hidden:
            continue
        by_instance: dict[str, list[bool]] = {}
        for r in hidden:
            by_instance.setdefault(f"{r['template_id']}__{r['instance']}", []).append(r["vcc"])
        rel = reliability(by_instance, REPEATS)
        solved = sum(1 for r in hidden if r["vcc"])
        ci = wilson_interval(solved, len(hidden))
        boot = cluster_bootstrap_ci(
            [{"template_id": r["template_id"], "v": 1.0 if r["vcc"] else 0.0} for r in hidden],
            "v")
        c0 = [r for r in hidden if r["condition"] == "C0"]
        h1f2 = [r for r in hidden if r["condition"] in ("H1", "F2")]
        f2 = [r for r in hidden if r["condition"] == "F2"]
        trap = sum(1 for r in h1f2 if r["any_trap"]) / len(h1f2) if h1f2 else None
        # A false alarm on a clean control shows up as tripping the decoy on a
        # C0 chain, i.e. asserting the problem that does not exist.
        false_alarm = sum(1 for r in c0 if r["any_trap"]) / len(c0) if c0 else None
        pushback = sum(1 for r in f2 if r["decision_correct"]) / len(f2) if f2 else None

        def pct(x):
            return f"{100*x:.1f}%" if x is not None else "-"

        harness = HARNESS_CLASS.get(system, "H0 (single-turn, no tools)")
        lines.append(
            f"| {system} | {harness} | {pct(rel.get('pass_hat_k'))} "
            f"| {pct(rel.get('pass_at_1'))} [{100*ci[0]:.1f}, {100*ci[1]:.1f}] "
            f"| {pct(rel.get('pass_at_k'))} | {pct(trap)} | {pct(false_alarm)} "
            f"| {pct(pushback)} |")
        summary[system] = {
            "reliability": rel, "wilson_ci_pass_at_1": ci,
            "cluster_bootstrap_pass_at_1": boot,
            "trap_rate": trap, "false_alarm_rate": false_alarm,
            "premise_pushback": pushback,
            "hazard": hazard_profile([r for r in hidden if not r.get("censored")]),
            "calibration": aggregate(hidden),
        }

    lines.append("")
    lines.append("## Where the chains break (per-stage hazard)")
    lines.append("")
    lines.append("Hazard h_k is the probability of failing at stage k having reached it.")
    lines.append("Reported instead of a fraction-of-stages score, which is not comparable")
    lines.append("across chains of different length and moves if a stage is merely split.")
    for system, s in sorted(summary.items()):
        haz = s["hazard"]["hazard_by_stage"]
        if haz:
            profile = "  ".join(f"h{h['stage_index']}={h['hazard']:.2f}" for h in haz)
            lines.append(f"- {system}: {profile}  (E[depth]={s['hazard']['expected_depth']})")
    lines.append("")

    lines.append("## Calibration")
    for system, s in sorted(summary.items()):
        cal = s["calibration"]
        if cal.get("rms_calibration_error") is not None:
            lines.append(f"- {system}: RMS calibration error "
                         f"{cal['rms_calibration_error']}, Brier {cal.get('mean_brier')}, "
                         f"mean overconfidence {cal.get('mean_overconfidence')}")
    lines.append("")

    lines.append("## Cost")
    for model, totals in usage_summary(repo).items():
        cost = totals.get("cost_usd")
        lines.append(f"- {model}: {totals['calls']} calls, {totals['output_tokens']:,} out"
                     + (f", ${cost:.2f}" if cost else ""))

    path = out_dir / "scorecard.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str),
                                          encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="chain.campaign")
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--system", required=True)
    r.add_argument("--shard", default=None)
    r.add_argument("--log", default=None,
                   help="append stdout/stderr here (lets the worker run under "
                        "pythonw.exe, which never opens a console window)")
    sub.add_parser("scorecard")
    p = sub.add_parser("plan")
    p.add_argument("--system", default="anthropic")
    args = parser.parse_args(argv)
    if args.cmd == "run":
        if args.log:
            # Redirect in-process rather than with shell `>>`, so the task can
            # be a bare pythonw.exe action with no cmd.exe wrapper and no
            # console window flashing on the user's desktop.
            Path(args.log).parent.mkdir(parents=True, exist_ok=True)
            stream = open(args.log, "a", encoding="utf-8", buffering=1)
            sys.stdout = sys.stderr = stream
        print(json.dumps(run_candidates(args.system, args.shard)))
    elif args.cmd == "scorecard":
        print(str(build_scorecard()))
    else:
        print(len(plan(find_repo_root(), args.system)), "runs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
