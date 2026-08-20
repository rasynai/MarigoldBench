"""Collect everything the figures need into one JSON, computed from episodes.

Figures are drawn from this file and nothing else, so a figure can never show a
number that was not recomputed from the recorded episodes.
"""
from __future__ import annotations

import collections
import glob
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crucible.lab.campaign import REPEATS, USABLE  # noqa: E402

DISPLAY = {
    "grok": "Grok 4.6",
    "gpt": "GPT-5.6 Sol",
    "claude": "Claude Opus 5",
    "deepseek": "DeepSeek V4 Pro",
    "gemini": "Gemini 3.1 Pro",
    "glm": "GLM-4.7",
    "kimi": "Kimi K2 Thinking",
}
FULL_PLAN = ("claude", "gpt", "gemini", "grok")


def cluster_ci(rows, draws=20000, seed=7):
    """Resample FAMILIES, not episodes: episodes share a generator."""
    by_family = collections.defaultdict(list)
    for r in rows:
        by_family[r["family"]].append(bool(r["vec"]))
    families = list(by_family)
    rng = random.Random(seed)
    draws_out = []
    for _ in range(draws):
        hits = total = 0
        for _ in families:
            values = by_family[families[rng.randrange(len(families))]]
            hits += sum(values)
            total += len(values)
        draws_out.append(hits / total)
    draws_out.sort()
    return draws_out[int(0.025 * draws)], draws_out[int(0.975 * draws)]


def main() -> None:
    rows = []
    for path in glob.glob("runs/lab-1.0.0/systems/*/outcomes/*.json"):
        record = json.load(open(path, encoding="utf-8"))
        if record["family"] in USABLE:
            rows.append(record)
    hidden = [r for r in rows if r["split"] == "hidden_test"]
    systems = [s for s in DISPLAY if any(r["system"] == s for r in hidden)]

    out = {"display": DISPLAY, "full_plan": list(FULL_PLAN), "systems": {}}

    # per-family pass rates, needed before the tiers can be decided
    per_family = collections.defaultdict(dict)
    for family in sorted({r["family"] for r in hidden}):
        for system in systems:
            sub = [r for r in hidden
                   if r["family"] == family and r["system"] == system]
            if sub:
                per_family[family][system] = sum(r["vec"] for r in sub) / len(sub)
    tiers = {f: ("anchor" if max(v.values()) >= 0.80 else "discriminating")
             for f, v in per_family.items()}

    for system in systems:
        mine = [r for r in hidden if r["system"] == system]
        lo, hi = cluster_ci(mine)
        by_instance = collections.defaultdict(list)
        for r in mine:
            by_instance[f"{r['family']}__s{r['seed']}__{r['condition']}"].append(r["vec"])
        complete = [v for v in by_instance.values() if len(v) >= REPEATS]
        conditions = {}
        for cond in ("C0", "H1", "F2"):
            sub = [r for r in mine if r["condition"] == cond]
            conditions[cond] = sum(r["vec"] for r in sub) / len(sub)
        band = {}
        for tier in ("discriminating", "anchor"):
            sub = [r for r in mine if tiers[r["family"]] == tier]
            band[tier] = sum(r["vec"] for r in sub) / len(sub)
        all_rows = [r for r in rows if r["system"] == system]
        cost = sum(r.get("cost_usd", 0) or 0 for r in all_rows)
        out["systems"][system] = {
            "n_hidden": len(mine),
            "pass_at_1": sum(r["vec"] for r in mine) / len(mine),
            "ci": [lo, hi],
            "pass_at_3": (sum(1 for v in complete if all(v)) / len(complete)
                          if complete else None),
            "conditions": conditions,
            "band": band,
            "cost_total": cost,
            "cost_per_episode": cost / len(all_rows),
            "median_tool_calls": sorted(r["tool_calls"] for r in all_rows)[len(all_rows) // 2],
        }

    out["families"] = {f: {"tier": tiers[f], "scores": per_family[f]}
                       for f in sorted(per_family)}
    Path("runs/_figdata.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({"systems": len(out["systems"]),
                      "families": len(out["families"]),
                      "discriminating": sum(1 for t in tiers.values()
                                            if t == "discriminating")}))


if __name__ == "__main__":
    main()
