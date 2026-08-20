"""Is CRUCIBLE-CHAIN's scale statistically adequate? Exact answer, no vibes.

The unit-of-independence problem: runs within a template share a generator,
a science story, and a defect mechanism, so they are correlated. The effective
sample size is runs / DEFF where DEFF = 1 + (m-1)*ICC for m runs per template.
More instances of the same template buy almost no new information once ICC is
material; only new independent templates do. This script estimates ICC from
the campaign's real outcomes, then computes CI widths and the minimum
detectable difference between two systems for candidate designs.
"""
from __future__ import annotations

import glob
import json
import math
from collections import defaultdict

Z95 = 1.959964
Z80 = 0.841621  # 80% power


def wilson_width(p: float, n_eff: float) -> float:
    """Full width of the 95% Wilson interval at rate p with n_eff trials."""
    if n_eff <= 0:
        return float("nan")
    z2 = Z95 * Z95
    denom = 1 + z2 / n_eff
    half = (Z95 / denom) * math.sqrt(p * (1 - p) / n_eff + z2 / (4 * n_eff * n_eff))
    return 2 * half


def icc_anova(groups: list[list[int]]) -> float:
    """One-way ANOVA ICC(1) over binary outcomes grouped by template."""
    groups = [g for g in groups if len(g) >= 2]
    k = len(groups)
    if k < 2:
        return float("nan")
    n_total = sum(len(g) for g in groups)
    grand = sum(sum(g) for g in groups) / n_total
    m_bar = n_total / k
    ss_between = sum(len(g) * (sum(g) / len(g) - grand) ** 2 for g in groups)
    ss_within = sum(sum((x - sum(g) / len(g)) ** 2 for x in g) for g in groups)
    ms_between = ss_between / (k - 1)
    ms_within = ss_within / max(n_total - k, 1)
    # ANOVA estimator with unequal group sizes
    n0 = m_bar - sum(len(g) ** 2 for g in groups) / (k * n_total) / m_bar * m_bar
    n0 = (n_total - sum(len(g) ** 2 for g in groups) / n_total) / (k - 1)
    if ms_between + (n0 - 1) * ms_within <= 0:
        return 0.0
    return max(0.0, (ms_between - ms_within) / (ms_between + (n0 - 1) * ms_within))


def mdd_two_arm(p_base: float, n_eff: float) -> float:
    """Smallest detectable absolute difference vs p_base (alpha .05, power .80,
    two-sided, unpaired normal approximation, equal effective n per arm)."""
    lo, hi = 1e-4, 1 - p_base - 1e-4
    for _ in range(80):
        d = (lo + hi) / 2
        p2 = p_base + d
        need = ((Z95 + Z80) ** 2) * (p_base * (1 - p_base) + p2 * (1 - p2)) / (d * d)
        if need > n_eff:
            lo = d
        else:
            hi = d
    return (lo + hi) / 2


def main() -> None:
    # ---- ICC from the real campaign (use unsaturated systems: variance exists)
    by_sys_tmpl: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for path in glob.glob("runs/release-3.0.0/systems/*/outcomes/*.json"):
        d = json.load(open(path, encoding="utf-8"))
        if d["split"] != "hidden_test":
            continue
        by_sys_tmpl[d["system"]][d["template_id"]].append(1 if d["vcc"] else 0)

    print("ICC of VCC within template, by system (unsaturated systems only):")
    iccs = []
    for system, groups in sorted(by_sys_tmpl.items()):
        rates = [sum(g) / len(g) for g in groups.values()]
        overall = sum(sum(g) for g in groups.values()) / sum(len(g) for g in groups.values())
        if overall in (0.0, 1.0) or len(groups) < 3:
            print(f"  {system:44s} skipped (rate {overall:.2f}, {len(groups)} templates)")
            continue
        icc = icc_anova(list(groups.values()))
        iccs.append(icc)
        print(f"  {system:44s} ICC={icc:.3f}  (rate {overall:.2f}, "
              f"{len(groups)} templates, per-template rates "
              f"{['%.2f' % r for r in rates]})")
    icc = max(0.15, (sum(iccs) / len(iccs)) if iccs else 0.25)
    print(f"\nworking ICC (mean of estimable systems, floored at 0.15): {icc:.3f}\n")

    # ---- candidate designs: (name, templates, instances/template evaluated)
    designs = [
        ("CURRENT  8 templates x 6 eval runs",              8,   6),
        ("current instances, more repeats (8 x 18)",        8,  18),
        ("sponsor floor: 100 templates x 3",              100,   3),
        ("sponsor mid:   120 templates x 3",              120,   3),
        ("sponsor top:   135 templates x 3",              135,   3),
        ("wide-shallow:  200 templates x 2",              200,   2),
    ]
    print(f"{'design':42s} {'runs':>5s} {'DEFF':>5s} {'n_eff':>6s} "
          f"{'CI@5%':>7s} {'CI@10%':>7s} {'MDD@5%':>7s}")
    for name, k, m in designs:
        n = k * m
        deff = 1 + (m - 1) * icc
        n_eff = n / deff
        # cluster count is its own ceiling: CIs cannot be narrower than ~k allows
        n_eff = min(n_eff, k / (1 / m + icc * (1 - 1 / m)) if icc > 0 else n)
        print(f"{name:42s} {n:5d} {deff:5.2f} {n_eff:6.0f} "
              f"{100 * wilson_width(0.05, n_eff):6.1f}p {100 * wilson_width(0.10, n_eff):6.1f}p "
              f"{100 * mdd_two_arm(0.05, n_eff):6.1f}p")

    print("""
Reading:
  CI@p  = full width of the 95% Wilson interval on a single system's pass@1
  MDD@5% = smallest gap from a 5% baseline that a two-system comparison can
           detect with 80% power (unpaired; paired designs do somewhat better)
""")


if __name__ == "__main__":
    main()
