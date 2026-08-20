"""Release 1.0 campaign over the generated hidden + sealed task population.

Design (preregistered in analysis/preregistrations/campaign-1.0.0.md):

- Systems: 2 first-party reference agents, 6 OpenRouter frontier reference
  agents, and the Marigold native product (subset - it is slow hardware).
- Instances: every hidden_test instance once, every sealed instance once;
  the first 6 hidden instances get 2 extra repeat runs (run-to-run variance).
- Per-system workers are independent processes writing one outcome file per
  (instance, run) so any crash resumes for free.
- Judges: cross-family sample of 6 submissions per system, advisory.

Worker CLI:
    python -m crucible.release_campaign worker --system <provider> [--label L]
Finalizer:
    python -m crucible.release_campaign finalize [--label L]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from .agent import run_agent
from .frontier_campaign import FRONTIER_MODELS
from .judge import judge_submission
from .llm import usage_summary
from .paths import find_repo_root
from .stats import cluster_bootstrap_rate, rate_with_denominator, wilson_interval

API_SYSTEMS = ["anthropic", "openai"] + [f"openrouter/{m}" for m in FRONTIER_MODELS]
REPEAT_INSTANCES = 6          # first N hidden instances get repeats
REPEATS = 3                   # total runs on those instances (1 + 2 extra)
MARIGOLD_HIDDEN_SUBSET = 20
MARIGOLD_SEALED_SUBSET = 8
JUDGE_SAMPLE_PER_SYSTEM = 6


def _safe(name: str) -> str:
    return name.replace("/", "_").replace(".", "-")


def _index(repo: Path) -> list[dict]:
    return json.loads((repo / "registry" / "generated_task_index.json").read_text(encoding="utf-8"))


def eval_plan(repo: Path, system: str) -> list[tuple[str, dict, int]]:
    """[(run_id, index_row, run_number)] for one system, deterministic order."""
    rows = [r for r in _index(repo) if r["split"] in ("hidden_test", "sealed")]
    rows.sort(key=lambda r: (r["split"], r["template_id"], r["instance"]))
    if system == "marigold":
        hidden = [r for r in rows if r["split"] == "hidden_test"]
        sealed = [r for r in rows if r["split"] == "sealed"]
        rng = random.Random(1000)
        rows = rng.sample(hidden, MARIGOLD_HIDDEN_SUBSET) + rng.sample(sealed, MARIGOLD_SEALED_SUBSET)
    plan = []
    hidden_count = 0
    for row in rows:
        runs = 1
        if system != "marigold" and row["split"] == "hidden_test":
            hidden_count += 1
            if hidden_count <= REPEAT_INSTANCES:
                runs = REPEATS
        for run_no in range(1, runs + 1):
            plan.append((f"{row['template_id']}-{row['instance']}-r{run_no}", row, run_no))
    return plan


def worker(system: str, label: str, shard: str | None = None) -> dict:
    repo = find_repo_root()
    out_root = repo / "runs" / label / "systems" / _safe(system)
    out_root.mkdir(parents=True, exist_ok=True)
    plan = eval_plan(repo, system)
    if shard:  # "i/n" -> every n-th run starting at i (parallel marigold cores)
        i, n = (int(x) for x in shard.split("/"))
        plan = plan[i::n]
    done = skipped = failed = 0
    for run_id, row, run_no in plan:
        outcome_path = out_root / "outcomes" / f"{run_id}.json"
        if outcome_path.exists():
            skipped += 1
            continue
        task_dir = repo / row["path"]
        sub_dir = out_root / "submissions" / run_id
        try:
            if system == "marigold":
                from .marigold_adapter import run_marigold

                outcome = run_marigold(task_dir, sub_dir, budget_minutes=18)
            else:
                outcome = run_agent(task_dir, sub_dir, system,
                                    verification_gate=True, purpose="release-1.0")
        except Exception as exc:  # noqa: BLE001 - a dead system run is an outcome
            outcome = {"reliable_completion": False, "abstained": False,
                       "failed_gate_claim_ids": [], "critical_operational_failures": [],
                       "integrity_problems": [f"run failed: {str(exc)[:300]}"],
                       "leaf_results": [], "diagnostic_profiles": {}}
            failed += 1
        record = {
            "system": system, "run_id": run_id, "run_no": run_no,
            "template_id": row["template_id"], "archetype": row["archetype"],
            "instance": row["instance"], "condition": row["condition"],
            "split": row["split"], "holdout_level": row["holdout_level"],
            "reliable_completion": outcome["reliable_completion"],
            "abstained": outcome.get("abstained", False),
            "failed_gate_claim_ids": outcome["failed_gate_claim_ids"],
            "integrity_problems": outcome.get("integrity_problems", []),
        }
        outcome_path.parent.mkdir(parents=True, exist_ok=True)
        outcome_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        done += 1
    summary = {"system": system, "completed": done, "resumed_skips": skipped, "hard_failures": failed}
    (out_root / "worker_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _load_all(repo: Path, label: str) -> dict[str, list[dict]]:
    systems = {}
    for sys_dir in sorted((repo / "runs" / label / "systems").glob("*")):
        rows = [json.loads(p.read_text(encoding="utf-8"))
                for p in sorted((sys_dir / "outcomes").glob("*.json"))]
        if rows:
            systems[rows[0]["system"]] = rows
    return systems


def _judge_sample(repo: Path, label: str, systems: dict[str, list[dict]]) -> dict:
    report = {}
    for system, rows in systems.items():
        judge_provider = "openai" if system == "anthropic" else "anthropic"
        rng = random.Random(hash(system) & 0xFFFF)
        candidates = [r for r in rows if not r["integrity_problems"]]
        sample = rng.sample(candidates, min(JUDGE_SAMPLE_PER_SYSTEM, len(candidates)))
        agree = judged = 0
        for row in sample:
            sub_dir = (repo / "runs" / label / "systems" / _safe(system)
                       / "submissions" / row["run_id"])
            task_dir = repo / next(r["path"] for r in _index(repo)
                                   if r["template_id"] == row["template_id"]
                                   and r["instance"] == row["instance"])
            try:
                verdict = judge_submission(task_dir, sub_dir, judge_provider)
            except Exception:  # noqa: BLE001
                continue
            judged += 1
            if (verdict["verdict"] == "PASS") == row["reliable_completion"]:
                agree += 1
        report[system] = {"judged": judged, "agree_with_gate": agree,
                          "judge_provider": judge_provider}
    return report


def finalize(label: str) -> Path:
    repo = find_repo_root()
    out_dir = repo / "runs" / label
    systems = _load_all(repo, label)

    # CORR-003 guard: a billing failure (HTTP 402) means the model never ran;
    # publishing a scorecard over such rows would report infrastructure, not
    # capability. Refuse until those runs are voided and re-run.
    billing = [f"{s}/{r['run_id']}" for s, rows in systems.items() for r in rows
               if any("402" in x for x in r.get("integrity_problems", []))]
    if billing:
        raise RuntimeError(
            f"{len(billing)} outcomes carry provider-billing (402) failures - "
            f"void and re-run them before finalizing: {billing[:5]}...")

    judge_path = out_dir / "judge_sample.json"
    if not judge_path.exists():
        judge_path.write_text(json.dumps(_judge_sample(repo, label, systems), indent=2),
                              encoding="utf-8")
    judge_report = json.loads(judge_path.read_text(encoding="utf-8"))

    lines = [f"# CRUCIBLE 1.0 scorecard - campaign {label}", ""]
    lines.append("Population: 30 generated templates / 10 archetypes; hidden (66) and")
    lines.append("sealed (22) instances; conditions: clean (N0), planted hazard (N1),")
    lines.append("underidentified (N2). All caveats in docs/LIMITATIONS.md apply;")
    lines.append("archetype is the top cluster unit for every interval below.")
    lines.append("")
    lines.append("## Hidden-set reliable completion (first run per instance)")
    lines.append("")
    lines.append("| System | Harness | Hidden overall | N0 clean | N1 hazard | N2 underid. | Sealed | Repeat flip rate |")
    lines.append("|---|---|---|---|---|---|---|---|")

    summary_rows = {}
    for system, rows in sorted(systems.items()):
        first_hidden = [r for r in rows if r["split"] == "hidden_test" and r["run_no"] == 1]
        sealed = [r for r in rows if r["split"] == "sealed"]

        def cnt(rows_, cond=None):
            subset = [r for r in rows_ if cond is None or r["condition"] == cond]
            return sum(r["reliable_completion"] for r in subset), len(subset)

        boot = cluster_bootstrap_rate(
            [{"template": r["archetype"], "reliable_completion": r["reliable_completion"]}
             for r in first_hidden])
        # repeat stability: instances with >1 run - did outcome flip?
        by_key: dict[str, set] = {}
        for r in rows:
            if r["split"] == "hidden_test":
                by_key.setdefault(f"{r['template_id']}-{r['instance']}", set()).add(
                    r["reliable_completion"])
        multi = [k for k, v in by_key.items()
                 if sum(1 for r in rows if f"{r['template_id']}-{r['instance']}" == k) > 1]
        flips = sum(1 for k in multi if len(by_key[k]) > 1)
        o = cnt(first_hidden); n0 = cnt(first_hidden, "N0")
        n1 = cnt(first_hidden, "N1"); n2 = cnt(first_hidden, "N2"); se = cnt(sealed)
        harness = "native product" if system == "marigold" else "reference agent"
        lines.append(
            f"| {system} | {harness} | {o[0]}/{o[1]} | {n0[0]}/{n0[1]} | {n1[0]}/{n1[1]} "
            f"| {n2[0]}/{n2[1]} | {se[0]}/{se[1]} | {flips}/{len(multi)} |")
        summary_rows[system] = {
            "hidden": o, "sealed": se, "n0": n0, "n1": n1, "n2": n2,
            "cluster_ci": boot["ci95_cluster_bootstrap"], "n_clusters": boot["n_clusters"],
            "repeat_flips": [flips, len(multi)],
        }
    lines.append("")
    lines.append("## Cluster-aware intervals (hidden first-run, archetype clusters)")
    for system, s in sorted(summary_rows.items()):
        hit, n = s["hidden"]
        lines.append(f"- {system}: {rate_with_denominator(hit, n)}; "
                     f"archetype-cluster bootstrap CI {s['cluster_ci']} ({s['n_clusters']} clusters)")
    lines.append("")
    lines.append("## Hidden vs sealed gap (memorization probe)")
    for system, s in sorted(summary_rows.items()):
        h_hit, h_n = s["hidden"]; s_hit, s_n = s["sealed"]
        if h_n and s_n:
            gap = h_hit / h_n - s_hit / s_n
            lines.append(f"- {system}: hidden {h_hit}/{h_n} vs sealed {s_hit}/{s_n} (gap {gap:+.0%})")
    lines.append("")
    lines.append("## Judge agreement sample (advisory, cross-family)")
    for system, jr in sorted(judge_report.items()):
        lines.append(f"- {system}: {jr['agree_with_gate']}/{jr['judged']} agree"
                     f" (judge: {jr['judge_provider']})")
    lines.append("")
    lines.append("## Cost accounting")
    for model, totals in usage_summary(repo).items():
        lines.append(f"- {model}: {totals['calls']} calls, {totals['input_tokens']:,} in /"
                     f" {totals['output_tokens']:,} out tokens")

    scorecard = out_dir / "scorecard.md"
    scorecard.write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "summary.json").write_text(
        json.dumps(summary_rows, indent=2, default=str), encoding="utf-8")
    return scorecard


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="release_campaign")
    sub = parser.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("worker")
    w.add_argument("--system", required=True)
    w.add_argument("--label", default="release-1.0.0")
    w.add_argument("--shard", default=None)
    f = sub.add_parser("finalize")
    f.add_argument("--label", default="release-1.0.0")
    p = sub.add_parser("plan")
    p.add_argument("--system", default="anthropic")
    args = parser.parse_args(argv)
    if args.cmd == "worker":
        print(json.dumps(worker(args.system, args.label, args.shard), indent=2))
    elif args.cmd == "finalize":
        print(str(finalize(args.label)))
    else:
        repo = find_repo_root()
        plan = eval_plan(repo, args.system)
        print(f"{len(plan)} runs for {args.system}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
