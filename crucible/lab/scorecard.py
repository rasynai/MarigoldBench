"""MarigoldBench scorecard.

Reports the ladder, not a number. Three commitments drive the layout:

- **Clustered uncertainty.** Episodes within a family share a generator, a
  science story and a defect mechanism, so they are not independent evidence.
  Miller (2024) measures clustered standard errors up to 3.05x the naive ones
  on DROP; our own chain track measured ICC ~0.26, and this campaign's hidden
  split measures 0.40 (design effect 8.4 at 19.3 episodes per family, so a
  naive interval is 2.9x too narrow). Every headline therefore
  carries a family-clustered bootstrap interval, and the naive Wilson interval
  is printed beside it only to show the size of the lie.
- **Failure anatomy over a single score.** AgentBench's transferable finding
  was that a bare score hides whether failure is science or scaffolding, so
  the card reports stop reasons, tool-call economy and per-checkpoint
  survival next to VEC.
- **Condition asymmetry is the point.** C0 false alarms and F2 refusals are
  reported separately: a system that refuses everything and a system that
  answers everything can share a VEC and be opposite instruments.

    python -m crucible.lab.scorecard
"""
from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

from ..paths import find_repo_root
from .campaign import LABEL, REPEATS, USABLE

Z95 = 1.959964


def wilson(successes: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    denom = 1 + Z95 * Z95 / n
    centre = (p + Z95 * Z95 / (2 * n)) / denom
    half = (Z95 / denom) * math.sqrt(p * (1 - p) / n + Z95 * Z95 / (4 * n * n))
    return (max(0.0, centre - half), min(1.0, centre + half))


def cluster_bootstrap(rows: list[dict], key: str = "vec",
                      cluster: str = "family", draws: int = 4000) -> tuple[float, float]:
    """Resample FAMILIES, not episodes.

    Resampling episodes would treat 33 instances of one generator as 33
    independent facts and report an interval several times too narrow.
    """
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        groups[row[cluster]].append(1.0 if row[key] else 0.0)
    names = list(groups)
    if len(names) < 2:
        return wilson(sum(1 for r in rows if r[key]), len(rows))
    rng = random.Random(20260816)
    means = []
    for _ in range(draws):
        picked = [groups[names[rng.randrange(len(names))]] for _ in names]
        flat = [v for group in picked for v in group]
        if flat:
            means.append(sum(flat) / len(flat))
    means.sort()
    lo = means[int(0.025 * len(means))]
    hi = means[int(0.975 * len(means)) - 1]
    return (lo, hi)


def load(repo: Path) -> dict[str, list[dict]]:
    base = repo / "runs" / LABEL / "systems"
    systems: dict[str, list[dict]] = {}
    if not base.exists():
        return systems
    for sys_dir in sorted(base.glob("*")):
        rows = []
        for path in sorted((sys_dir / "outcomes").glob("*.json")):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            # Only the gated allow-list is scored. Retired families (lead-opt,
            # pose-triage) survive on disk from pilot runs that predate the
            # hardening gates, and two systems have them while the third does
            # not: including them would compare systems on different family
            # sets, which is a worse error than losing the episodes.
            if row["family"] in USABLE:
                rows.append(row)
        if rows:
            systems[sys_dir.name] = rows
    return systems


def _pct(x) -> str:
    return "-" if x is None else f"{100 * x:.1f}%"


def build() -> Path:
    repo = find_repo_root()
    systems = load(repo)
    out_dir = repo / "runs" / LABEL
    lines: list[str] = []
    add = lines.append

    add("# MarigoldBench scorecard")
    add("")
    add("The model is given a working computational laboratory - structure")
    add("prediction, protein design, docking, generative chemistry, RDKit and a")
    add("Python environment - and is measured on whether it drives that lab to a")
    add("defensible result. Scoring is **Verified Episode Completion (VEC)**:")
    add("every checkpoint must pass, and the harness RECOMPUTES each physical or")
    add("statistical claim from the submitted artifact. Nothing self-reported is")
    add("taken as evidence.")
    add("")
    add("Each family ships three conditions with byte-identical briefs for the")
    add("first two: **C0** sound (claiming a problem is a false alarm), **H1** a")
    add("planted defect that changes the answer, **F2** a flawed premise where a")
    add("documented refusal is the only correct outcome.")
    add("")
    add("Read the family-clustered interval, not the naive one: episodes inside")
    add("a family share a generator and are not independent evidence.")
    add("")

    summary: dict = {}
    add("## Headline (hidden split)")
    add("")
    add("| System | n | VEC pass@1 | family-clustered 95% CI | naive Wilson | "
        f"pass^{REPEATS} | cost |")
    add("|---|---|---|---|---|---|---|")
    for system, rows in sorted(systems.items()):
        hidden = [r for r in rows if r["split"] == "hidden_test"]
        if not hidden:
            continue
        solved = sum(1 for r in hidden if r["vec"])
        boot = cluster_bootstrap(hidden)
        naive = wilson(solved, len(hidden))
        by_instance: dict[str, list[bool]] = defaultdict(list)
        for r in hidden:
            by_instance[f"{r['family']}__s{r['seed']}__{r['condition']}"].append(r["vec"])
        complete = [v for v in by_instance.values() if len(v) >= REPEATS]
        reliable = sum(1 for v in complete if all(v))
        cost = sum(r.get("cost_usd", 0) or 0 for r in rows)
        add(f"| {system} | {len(hidden)} | {_pct(solved / len(hidden))} "
            f"| [{100*boot[0]:.1f}, {100*boot[1]:.1f}] "
            f"| [{100*naive[0]:.1f}, {100*naive[1]:.1f}] "
            f"| {_pct(reliable / len(complete)) if complete else '-'} "
            f"| ${cost:.2f} |")
        summary[system] = {"n_hidden": len(hidden), "pass_at_1": solved / len(hidden),
                           "clustered_ci": boot, "wilson_ci": naive,
                           "pass_hat_k": (reliable / len(complete)) if complete else None,
                           "cost_usd": round(cost, 2)}
    add("")

    add("## By condition")
    add("")
    add("A system that refuses everything and one that answers everything can")
    add("share a VEC. These columns separate them.")
    add("")
    add("| System | C0 sound | H1 planted defect | F2 flawed premise |")
    add("|---|---|---|---|")
    for system, rows in sorted(systems.items()):
        hidden = [r for r in rows if r["split"] == "hidden_test"]
        cells = []
        for condition in ("C0", "H1", "F2"):
            subset = [r for r in hidden if r["condition"] == condition]
            cells.append(f"{sum(1 for r in subset if r['vec'])}/{len(subset)}"
                         if subset else "-")
        add(f"| {system} | " + " | ".join(cells) + " |")
        if system in summary:
            summary[system]["by_condition"] = {
                c: [sum(1 for r in hidden if r["condition"] == c and r["vec"]),
                    sum(1 for r in hidden if r["condition"] == c)]
                for c in ("C0", "H1", "F2")}
    add("")

    # Difficulty tiers. Some families run at >90% for frontier systems and
    # inflate the aggregate; LIMITATIONS promises they are not headline
    # evidence, so the card has to actually separate them. The split is
    # measured, not assigned: a family is DISCRIMINATING if the best system
    # scores below 80% on it, ANCHOR otherwise.
    hidden_by_family: dict[str, dict[str, tuple[int, int]]] = {}
    for system, rows in systems.items():
        for row in rows:
            if row["split"] != "hidden_test":
                continue
            cell = hidden_by_family.setdefault(row["family"], {}).setdefault(
                system, [0, 0])
            cell[0] += 1 if row["vec"] else 0
            cell[1] += 1
    tiers: dict[str, str] = {}
    for family, per_system in hidden_by_family.items():
        best = max((won / max(total, 1) for won, total in per_system.values()),
                   default=0.0)
        tiers[family] = "anchor" if best >= 0.80 else "discriminating"
    discriminating = sorted(f for f, t in tiers.items() if t == "discriminating")

    add("## Headline on the discriminating band")
    add("")
    add("Families where no system exceeds 80% - the ones carrying the signal.")
    add(f"Anchor families (>=80% for some system) are listed separately and are")
    add("not headline evidence; a benchmark with no easy items cannot tell")
    add('"hard" from "broken", but they inflate an aggregate.')
    add("")
    add(f"Discriminating: {len(discriminating)} of {len(tiers)} families - "
        + ", ".join(discriminating))
    add("")
    add("| System | n | VEC pass@1 | family-clustered 95% CI |")
    add("|---|---|---|---|")
    for system, rows in sorted(systems.items()):
        subset = [r for r in rows if r["split"] == "hidden_test"
                  and tiers.get(r["family"]) == "discriminating"]
        if not subset:
            continue
        won = sum(1 for r in subset if r["vec"])
        boot = cluster_bootstrap(subset)
        add(f"| {system} | {len(subset)} | {_pct(won / len(subset))} "
            f"| [{100*boot[0]:.1f}, {100*boot[1]:.1f}] |")
        if system in summary:
            summary[system]["discriminating_pass_at_1"] = won / len(subset)
            summary[system]["discriminating_n"] = len(subset)
    add("")

    add("## By family")
    add("")
    add("| Family | " + " | ".join(sorted(systems)) + " |")
    add("|---" * (len(systems) + 1) + "|")
    families = sorted({r["family"] for rows in systems.values() for r in rows})
    per_family: dict[str, dict] = {}
    for family in families:
        cells = []
        for system in sorted(systems):
            subset = [r for r in systems[system]
                      if r["family"] == family and r["split"] == "hidden_test"]
            cells.append(f"{sum(1 for r in subset if r['vec'])}/{len(subset)}"
                         if subset else "-")
            per_family.setdefault(family, {})[system] = cells[-1]
        add(f"| {family} | " + " | ".join(cells) + " |")
    add("")

    add("## Where episodes break")
    add("")
    add("First failing checkpoint, and how the episode ended. A run that never")
    add("submits is a different failure from one that submits a wrong answer.")
    add("")
    for system, rows in sorted(systems.items()):
        hidden = [r for r in rows if r["split"] == "hidden_test"]
        first = Counter(r["first_failed"] for r in hidden
                        if not r["vec"] and r.get("first_failed"))
        stops = Counter(r.get("stop_reason") for r in hidden)
        calls = [r.get("tool_calls", 0) for r in hidden]
        add(f"- **{system}**: first-failures {dict(first.most_common(6))}")
        add(f"  - stop reasons {dict(stops)}; "
            f"mean tool calls {sum(calls)/max(len(calls),1):.1f}")
        if system in summary:
            summary[system]["first_failures"] = dict(first)
            summary[system]["stop_reasons"] = dict(stops)
            summary[system]["mean_tool_calls"] = round(sum(calls)/max(len(calls),1), 2)
    add("")

    add("## Sealed split")
    add("")
    add("Never published in any form. A large gap between hidden and sealed is")
    add("the contamination signal.")
    add("")
    for system, rows in sorted(systems.items()):
        sealed = [r for r in rows if r["split"] == "sealed"]
        hidden = [r for r in rows if r["split"] == "hidden_test"]
        if not sealed or not hidden:
            continue
        s_rate = sum(1 for r in sealed if r["vec"]) / len(sealed)
        h_rate = sum(1 for r in hidden if r["vec"]) / len(hidden)
        add(f"- {system}: sealed {_pct(s_rate)} (n={len(sealed)}) vs hidden "
            f"{_pct(h_rate)}; gap {100*(h_rate - s_rate):+.1f} pp")
        if system in summary:
            summary[system]["sealed_rate"] = s_rate
            summary[system]["sealed_gap_pp"] = round(100 * (h_rate - s_rate), 1)
    add("")

    add("## Integrity")
    add("")
    add("- Every family passes the baseline ladder before it may be scored:")
    add("  its own reference submission completes it (B8), an empty submission")
    add("  fails every instance (B1), C0 and H1 briefs are byte-identical, and")
    add("  no scored field is constant across the population.")
    add("- Infrastructure failures are quarantined, never scored: a harness")
    add("  crash is not a measurement of a model.")
    add("- Tool calls are cached and replayed, so re-scoring never depends on a")
    add("  live service and two systems making the same call see the same bytes.")
    add("")

    path = out_dir / "scorecard.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / "summary.json").write_text(
        json.dumps({"systems": summary, "by_family": per_family},
                   indent=2, default=str), encoding="utf-8")
    return path


if __name__ == "__main__":
    print(build())
