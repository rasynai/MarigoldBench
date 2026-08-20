"""MarigoldBench campaign runner.

Restart-proof (an existing outcome file is never re-run) and spend-aware: the
sponsor's ceiling is real money, so every episode's cost is priced from the
recorded token usage and the runner refuses to start an episode that would
cross the budget. CORR-008 is the reason this is enforced from recorded usage
rather than from an estimate that nobody writes down.

    python -m crucible.lab.campaign plan
    python -m crucible.lab.campaign run --system claude [--budget-usd 30]
    python -m crucible.lab.campaign score
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

from ..paths import find_repo_root
from .episode import SYSTEMS, run_episode
from .families import CONDITIONS, REGISTRY, build, verify

LABEL = "lab-1.0.0"
REPEATS = 3
SEEDS = [11, 12, 13, 14, 15, 16]
SEALED_SEEDS = {14, 16}
DEV_SEEDS = {11}

# USD per 1M tokens (input, output). Used only for the spend guard.
PRICES = {
    "claude": (15.0, 75.0),
    "gpt": (1.25, 10.0),
    "gemini": (1.25, 10.0),
    "gemini-vertex": (1.25, 10.0),
    "grok": (2.0, 6.0),
    # Fallbacks only: OpenRouter returns the authoritative cost per call and
    # `episode_cost` prefers it. These matter if the gateway ever omits it.
    "deepseek": (0.66, 1.98),
    "kimi": (0.60, 2.50),
    "glm": (0.40, 1.75),
    "grok-or": (2.0, 6.0),
}

# The sponsor's OpenRouter allowance, in force across every OpenRouter-hosted
# system at once: "DO NOT IN ANY CASE SPEND MORE THAN 100 USD from open
# router". Held at 95 so the last episode of a shard cannot overshoot into the
# hundredth dollar. CORR-008 is why this is enforced from recorded per-call
# cost and cross-checked against the gateway's own account total rather than
# estimated.
OPENROUTER_CEILING_USD = 95.0
OPENROUTER_SYSTEMS = tuple(sorted(
    name for name, spec in SYSTEMS.items() if spec["provider"] == "openrouter"))

# Systems evaluated on the reduced plan: hidden-test seeds, one attempt each.
# It is the split the headline is computed on, so the numbers stay comparable;
# what it cannot produce is pass^3 (needs repeats) or a contamination reading
# (needs the sealed seeds). Chosen because the full 990-episode plan costs
# more than the whole OpenRouter allowance for a single one of these systems.
# `grok` is NOT here: it runs on xAI's own key, so it is not competing for the
# OpenRouter allowance and can afford the full plan - which means pass^3 and a
# contamination reading, the same evidence the first three systems carry.
LITE_SYSTEMS = frozenset({"deepseek", "kimi", "glm", "grok-or"})


def split_for(seed: int) -> str:
    if seed in SEALED_SEEDS:
        return "sealed"
    if seed in DEV_SEEDS:
        return "development"
    return "hidden_test"


def episode_cost(system: str, usage: dict) -> float:
    """Price an episode from recorded usage, cache tiers included.

    Cache reads bill at 0.1x and cache writes at 1.25x of the input rate;
    ignoring the split would misreport spend by several-fold on a cached
    agent loop, and the guard is only worth having if the number is real.
    """
    if usage.get("billed_usd") is not None:
        return float(usage["billed_usd"])   # the biller's own number
    price_in, price_out = PRICES.get(system, (5.0, 25.0))
    plain = usage.get("input_tokens", 0)
    read = usage.get("cache_read", 0)
    write = usage.get("cache_write", 0)
    # Anthropic reports cached tokens separately from input_tokens; other
    # providers fold everything into input_tokens and report neither.
    return (plain * price_in + write * price_in * 1.25 + read * price_in * 0.1
            + usage.get("output_tokens", 0) * price_out) / 1e6


# Only families that pass every rung of runs/validate_families.py may be
# evaluated. Kept as an explicit allow-list rather than "whatever imports",
# so adding a family to the scorecard is a deliberate act.
USABLE = (
          "admet-filter", "affinity-delta", "assay-drift",
          "assay-mechanism", "assay-qc", "batch-effect-potency",
          "binder-selectivity", "conformer-energy", "crystal-artifact",
          "docking-decoy-control", "dose-extrapolation", "dose-units",
          "enrichment-null", "ensemble-disagreement", "feature-leakage-audit",
          "fold-confidence-calibration", "hill-slope-anomaly", "model-build",
          "multi-objective-pareto", "pose-rescoring", "promiscuity-flag",
          "qsar-inversion", "replicate-power", "selectivity-panel",
          "series-activity-cliff", "split-leakage", "stability-triage",
          "stereo-specificity", "synthesis-route-cost", "tautomer-trap")


def plan(system: str | None = None) -> list[tuple[str, int, str, int]]:
    """Every evaluated episode: (family, seed, condition, repeat).

    Hidden-test seeds carry the repeats that make pass^3 meaningful; sealed
    seeds are run once, because their job is contamination resistance rather
    than reliability estimation.
    """
    lite = system in LITE_SYSTEMS
    jobs = []
    for family in sorted(f for f in REGISTRY if f in USABLE):
        for seed in SEEDS:
            split = split_for(seed)
            if split == "development":
                continue
            if lite and split != "hidden_test":
                continue
            repeats = (1 if lite else REPEATS) if split == "hidden_test" else 1
            for condition in CONDITIONS:
                for repeat in range(1, repeats + 1):
                    jobs.append((family, seed, condition, repeat))
    return jobs


def _spend_so_far(root: Path) -> float:
    """Total recorded spend for this system, across every shard.

    Read fresh on each episode rather than accumulated locally: with N shards
    running, a per-process counter would let the real total reach N times the
    ceiling before any single worker noticed.
    """
    total = 0.0
    # Censored episodes are counted: an episode that died after burning tokens
    # cost real money even though it is not scored.
    for folder in ("outcomes", "censored"):
        for path in (root / folder).glob("*.json"):
            try:
                total += json.loads(path.read_text(encoding="utf-8")
                                    ).get("cost_usd", 0.0) or 0.0
            except (json.JSONDecodeError, OSError):
                pass
    return total


def openrouter_account_spend(repo: Path) -> float | None:
    """Spend since this campaign began, according to the gateway's own books.

    An independent check on `openrouter_spend`: that one trusts files we wrote,
    this one asks the party sending the bill. The first call records a baseline,
    so a pre-existing balance on the account is not charged to us. Returns None
    if the endpoint cannot be reached - a network failure must not become a
    licence to keep spending, so the caller treats None as "use the disk sum".
    """
    import os
    import urllib.request

    marker = repo / "runs" / LABEL / "openrouter_baseline.json"
    try:
        request = urllib.request.Request(
            "https://openrouter.ai/api/v1/credits",
            headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]})
        with urllib.request.urlopen(request, timeout=30) as response:
            used = float(json.load(response)["data"]["total_usage"])
    except Exception:  # noqa: BLE001 - unreachable biller, not a fatal error
        return None
    if marker.exists():
        baseline = json.loads(marker.read_text(encoding="utf-8"))["total_usage"]
    else:
        baseline = used
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({"total_usage": used}), encoding="utf-8")
    return max(0.0, used - baseline)


def openrouter_spend(repo: Path) -> float:
    """Everything spent through the gateway, across every system it hosts.

    Voided episodes are counted too. CORR-012 spent $31.51 on a Grok route the
    sponsor had forbidden, because a stop command silently failed and its
    errors went to Out-Null; those 236 episodes now live under
    runs/corrections/ and would otherwise vanish from the ceiling the moment
    they were voided. Money spent is money spent - a ceiling that only counts
    scored work is not a ceiling.
    """
    base = repo / "runs" / LABEL / "systems"
    live = sum(_spend_so_far(base / name) for name in OPENROUTER_SYSTEMS)
    voided = 0.0
    for folder in (repo / "runs" / "corrections").glob("CORR-*"):
        for path in folder.glob("*__*.json"):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if record.get("system") in VOIDED_OPENROUTER_SYSTEMS:
                voided += record.get("cost_usd", 0.0) or 0.0
    return live + voided


# Systems that WERE served through the gateway and are no longer evaluated.
# Their spend still counts against the gateway ceiling.
VOIDED_OPENROUTER_SYSTEMS = frozenset({"grok-or"})


def run(system: str, budget_usd: float, limit: int | None,
        shard: str | None = None) -> dict:
    repo = find_repo_root()
    root = repo / "runs" / LABEL / "systems" / system
    (root / "outcomes").mkdir(parents=True, exist_ok=True)

    jobs = plan(system)
    if shard:
        index, total_shards = (int(x) for x in shard.split("/"))
        jobs = jobs[index::total_shards]

    done = skipped = 0
    for family, seed, condition, repeat in jobs:
        run_id = f"{family}__s{seed}__{condition}__r{repeat}"
        out_path = root / "outcomes" / f"{run_id}.json"
        if out_path.exists():
            skipped += 1
            continue
        spent = _spend_so_far(root)
        if spent >= budget_usd:
            print(json.dumps({"stop": "budget", "spent_usd": round(spent, 2),
                              "budget_usd": budget_usd}), flush=True)
            break
        if SYSTEMS[system]["provider"] == "openrouter":
            shared = openrouter_spend(repo)
            # Every tenth episode, believe the gateway over our own files.
            if done % 10 == 0:
                billed = openrouter_account_spend(repo)
                if billed is not None:
                    shared = max(shared, billed)
            if shared >= OPENROUTER_CEILING_USD:
                print(json.dumps({"stop": "openrouter_ceiling",
                                  "spent_usd": round(shared, 2),
                                  "ceiling_usd": OPENROUTER_CEILING_USD}),
                      flush=True)
                break
        if limit is not None and done >= limit:
            break

        episode = build(family, seed, condition)
        workspace = repo / "runs" / LABEL / "workspaces" / system / run_id
        workspace.mkdir(parents=True, exist_ok=True)
        for name, text in episode.files.items():
            (workspace / name).write_text(text, encoding="utf-8")
        brief = (episode.brief + "\n\nFiles in your workspace: "
                 + ", ".join(sorted(episode.files))
                 + f"\nTool-call budget: {episode.budget}.")

        censored = None
        try:
            result = run_episode(system, brief, workspace, budget=episode.budget,
                                 max_turns=episode.budget + 6, max_tokens=12000)
            submitted, usage = result.submitted, result.usage
            transcript, stop = result.transcript, result.stop_reason
            calls, turns, seconds = result.tool_calls, result.turns, result.seconds
            reasoning = result.reasoning
        except Exception as exc:  # noqa: BLE001
            censored = f"{type(exc).__name__}: {str(exc)[:300]}"
            submitted, usage, transcript = None, {}, []
            stop, calls, turns, seconds, reasoning = "error", 0, 0, 0.0, ""

        verdict = verify(episode, submitted, workspace)
        cost = episode_cost(system, usage)
        record = {
            "run_id": run_id, "system": system, "family": family, "seed": seed,
            "condition": condition, "repeat": repeat, "split": split_for(seed),
            "vec": verdict.passed, "checkpoints": verdict.checkpoints,
            "first_failed": verdict.first_failed, "detail": verdict.detail,
            "submitted": submitted, "stop_reason": stop, "tool_calls": calls,
            "turns": turns, "seconds": seconds, "usage": usage,
            "cost_usd": round(cost, 4), "censored": censored,
            "transcript": transcript,
            "reasoning": (reasoning or "")[:4000],
        }
        # An infrastructure death is not a measurement. Writing it as an
        # outcome would both score the system for our bug and make the run
        # un-retryable (an existing outcome file is skipped forever), which
        # is how a harness TypeError silently became 231 model failures.
        target = (root / ("censored" if censored else "outcomes")
                  / f"{run_id}.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
        done += 1
        print(json.dumps({"run": run_id, "vec": verdict.passed,
                          "first_failed": verdict.first_failed,
                          "calls": calls, "cost": round(cost, 3),
                          "spent": round(spent + cost, 2)}), flush=True)
    return {"system": system, "done": done, "skipped": skipped,
            "spent_usd": round(_spend_so_far(root), 2)}


def _wilson(successes: int, n: int, z: float = 1.959964) -> list[float]:
    if n == 0:
        return [0.0, 1.0]
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [max(0.0, centre - half), min(1.0, centre + half)]


def score() -> None:
    repo = find_repo_root()
    base = repo / "runs" / LABEL / "systems"
    if not base.exists():
        print("no runs yet")
        return
    for sys_dir in sorted(base.glob("*")):
        rows = [json.loads(p.read_text(encoding="utf-8"))
                for p in sorted((sys_dir / "outcomes").glob("*.json"))]
        hidden = [r for r in rows if r["split"] == "hidden_test"]
        if not hidden:
            continue
        by_instance: dict[str, list[bool]] = {}
        for r in hidden:
            by_instance.setdefault(f"{r['family']}__s{r['seed']}__{r['condition']}",
                                   []).append(r["vec"])
        solved = sum(1 for r in hidden if r["vec"])
        ci = _wilson(solved, len(hidden))
        reliable = sum(1 for v in by_instance.values() if len(v) >= REPEATS and all(v))
        cost = sum(r.get("cost_usd", 0) for r in rows)
        stages: dict[str, int] = {}
        for r in hidden:
            if not r["vec"] and r.get("first_failed"):
                stages[r["first_failed"]] = stages.get(r["first_failed"], 0) + 1
        print(f"{sys_dir.name}: n={len(hidden)} pass@1={100*solved/len(hidden):.1f}% "
              f"[{100*ci[0]:.0f},{100*ci[1]:.0f}] "
              f"pass^{REPEATS}={100*reliable/max(len(by_instance),1):.1f}% "
              f"| ${cost:.2f} | first-failures {stages}")


def main() -> int:
    parser = argparse.ArgumentParser(prog="crucible.lab.campaign")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    r = sub.add_parser("run")
    r.add_argument("--system", required=True, choices=sorted(SYSTEMS))
    r.add_argument("--budget-usd", type=float, default=25.0)
    r.add_argument("--limit", type=int, default=None)
    r.add_argument("--shard", default=None, help="i/n, e.g. 0/6")
    r.add_argument("--log", default=None)
    sub.add_parser("score")
    args = parser.parse_args()
    if getattr(args, "log", None):
        stream = open(args.log, "a", encoding="utf-8", buffering=1)
        sys.stdout = sys.stderr = stream
    if args.cmd == "plan":
        jobs = plan()
        print(json.dumps({"families": sorted(REGISTRY), "episodes_per_system": len(jobs)}))
    elif args.cmd == "run":
        print(json.dumps(run(args.system, args.budget_usd, args.limit,
                             args.shard)), flush=True)
    else:
        score()
    return 0


if __name__ == "__main__":
    sys.exit(main())
