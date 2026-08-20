"""Statistical helpers: cluster-aware uncertainty for tiny pilot samples.

Guide rules: report denominators with every rate (32.8); intervals must not
treat seeds as independent tasks (24.16) - here the cluster unit is the task
template; Wilson intervals for binomial rates.
"""
from __future__ import annotations

import math
import random


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = (z / denom) * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return (max(0.0, center - margin), min(1.0, center + margin))


def cluster_bootstrap_rate(
    outcomes: list[dict],
    cluster_key: str = "template",
    value_key: str = "reliable_completion",
    n_boot: int = 2000,
    seed: int = 12345,
) -> dict:
    """Bootstrap a rate resampling CLUSTERS (templates), not instances."""
    clusters: dict[str, list[bool]] = {}
    for outcome in outcomes:
        clusters.setdefault(str(outcome.get(cluster_key, "?")), []).append(bool(outcome[value_key]))
    names = list(clusters)
    rng = random.Random(seed)
    rates = []
    for _ in range(n_boot):
        sample: list[bool] = []
        for _ in names:
            sample.extend(clusters[rng.choice(names)])
        if sample:
            rates.append(sum(sample) / len(sample))
    rates.sort()
    total = sum(len(v) for v in clusters.values())
    hits = sum(sum(v) for v in clusters.values())
    return {
        "rate": hits / total if total else None,
        "numerator": hits,
        "denominator": total,
        "n_clusters": len(names),
        "ci95_cluster_bootstrap": [
            rates[int(0.025 * len(rates))],
            rates[int(0.975 * len(rates)) - 1],
        ]
        if rates
        else None,
        "note": "clusters resampled at template level; instances are not independent",
    }


def rate_with_denominator(successes: int, n: int) -> str:
    if n == 0:
        return "0/0 (no eligible cases)"
    low, high = wilson_interval(successes, n)
    return f"{successes}/{n} ({successes / n:.0%}; 95% Wilson CI {low:.0%}-{high:.0%})"
