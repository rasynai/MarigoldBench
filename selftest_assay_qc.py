"""Self-test for the assay-qc family: B8 reference, B1 degenerate, B5 naive.

Run:  cd A:/PERTURB-Bench && python selftest_assay_qc.py
"""
from __future__ import annotations

import math
import sys
from collections import Counter
from pathlib import Path

from crucible.lab.fam.assay_qc import (FAMILY, IC50_TOLERANCE_FACTOR,
                                       INHIBITION_TOLERANCE_PP, build,
                                       reference_submission, verify)

SEEDS = [11, 12, 13, 14, 15, 16]
CONDITIONS = ["C0", "H1", "F2"]
WORKSPACE = Path("runs/_selftest_assay_qc")
failures: list[str] = []


def check(label: str, ok: bool, extra: str = "") -> None:
    if not ok:
        failures.append(f"{label} {extra}".strip())
        print(f"  FAIL  {label} {extra}")


def reference(episode) -> dict:
    """B8 built straight from the key, so the key itself is under test."""
    key = episode.key
    ic50 = key["true_ic50_uM"] if key["determinable"] else "cannot_determine"
    return {"ic50_uM": ic50,
            "max_inhibition_pct": key["max_inhibition_pct"],
            "n_wells_excluded": key["n_artifacts"],
            "decision": key["decision"],
            "conf_ic50_uM": 0.8, "conf_max_inhibition_pct": 0.9,
            "conf_n_wells_excluded": 0.9, "conf_decision": 0.8}


# --- the naive analyst: read the CSV, fit what is printed in it, report ------
def naive(episode, do_qc: bool) -> dict:
    import re

    from crucible.lab.fam.assay_qc import _fit_ic50, _median, _parse_plate

    plate = _parse_plate(episode.files["plate_readout.csv"])
    threshold = float(re.search(r"at or below ([0-9.]+) uM",
                                episode.files["project_criteria.txt"]).group(1))
    neutral = _median([r["signal"] for r in plate if r["kind"] == "NEUTRAL"])
    floor = _median([r["signal"] for r in plate if r["kind"] == "MAXINH"])
    rows = [r for r in plate if r["kind"] == "TEST"]
    dropped = 0
    if do_qc:
        keep = [r for r in rows if 0.25 * floor < r["signal"] < 1.6 * neutral]
        dropped = len(rows) - len(keep)
        rows = keep
    by_dose: dict[int, list[float]] = {}
    for r in rows:
        by_dose.setdefault(r["dose"], []).append(r["signal"])
    means = {d: sum(v) / len(v) for d, v in by_dose.items()}
    max_inh = max(100.0 * (neutral - s) / (neutral - floor) for s in means.values())
    fit = _fit_ic50([math.log10(r["conc"]) for r in rows], [r["signal"] for r in rows])
    ic50 = fit["ic50_uM"] if fit else 1.0
    return {"ic50_uM": round(ic50, 4), "max_inhibition_pct": round(max_inh, 2),
            "n_wells_excluded": dropped,
            "decision": "advance" if ic50 <= threshold else "hold"}


# --- an independent competent path: normalise to percent inhibition against
#     the controls, take the concentrations the handler log implies, fit there.
def competent(episode, absolute_convention: bool = False) -> dict:
    import re

    import numpy as np
    from scipy.optimize import curve_fit

    from crucible.lab.fam.assay_qc import _parse_plate, _series_from_log

    plate = _parse_plate(episode.files["plate_readout.csv"])
    top_conc, factor = _series_from_log(episode.files["run_log.txt"])
    threshold = float(re.search(r"at or below ([0-9.]+) uM",
                                episode.files["project_criteria.txt"]).group(1))
    neutral = np.mean([r["signal"] for r in plate if r["kind"] == "NEUTRAL"])
    floor = np.mean([r["signal"] for r in plate if r["kind"] == "MAXINH"])
    keep = [r for r in plate if r["kind"] == "TEST"
            and r["signal"] > 0 and r["signal"] < 2.0 * neutral]
    dropped = len(plate) - len(keep) - 8          # 8 control wells
    pct = [100.0 * (neutral - r["signal"]) / (neutral - floor) for r in keep]
    x = np.array([math.log10(top_conc * factor ** -(r["dose"] - 1)) for r in keep])
    y = np.array(pct)
    max_inh = float(max(pct))
    if max_inh < 50.0:              # the series never reaches its own midpoint
        return {"ic50_uM": "cannot_determine", "max_inhibition_pct": round(max_inh, 1),
                "n_wells_excluded": dropped, "decision": "cannot_determine"}

    if absolute_convention:
        def model(xx, log_ic50, hill):
            return 100.0 / (1.0 + 10.0 ** (hill * (xx - log_ic50)))
        p0 = [float(np.median(x)), 1.0]
    else:
        def model(xx, bottom, span, log_ic50, hill):
            return bottom + span / (1.0 + 10.0 ** (hill * (xx - log_ic50)))
        p0 = [float(y.min()), float(y.max() - y.min()), float(np.median(x)), 1.0]
    try:
        popt, _ = curve_fit(model, x, y, p0=p0, maxfev=40000)
        ic50 = float(10.0 ** popt[-2])
    except Exception:                              # noqa: BLE001
        ic50 = float("nan")
    if not math.isfinite(ic50):
        return {"ic50_uM": "cannot_determine", "max_inhibition_pct": round(max_inh, 1),
                "n_wells_excluded": dropped, "decision": "cannot_determine"}
    return {"ic50_uM": round(ic50, 4), "max_inhibition_pct": round(max_inh, 1),
            "n_wells_excluded": dropped,
            "decision": "advance" if ic50 <= threshold else "hold"}


print("=" * 78)
print("assay-qc self-test")
print("=" * 78)

answers: dict[str, list] = {f"{c}:{k}": [] for c in CONDITIONS
                            for k in ("ic50_uM", "decision", "n_excluded", "max_inh")}

for seed in SEEDS:
    episodes = {}
    for condition in CONDITIONS:
        episode = episodes[condition] = build(seed, condition)
        ws = WORKSPACE / f"s{seed}_{condition}"
        ws.mkdir(parents=True, exist_ok=True)
        for name, text in episode.files.items():
            (ws / name).write_text(text, encoding="utf-8")

        # B8 reference must pass
        verdict = verify(episode, reference(episode), ws)
        check(f"s{seed}/{condition} B8 reference", verdict.passed,
              f"first_failed={verdict.first_failed} {verdict.checkpoints} {verdict.detail}")

        # B1 degenerate must fail
        check(f"s{seed}/{condition} B1 empty fails",
              not verify(episode, {}, ws).passed)
        check(f"s{seed}/{condition} B1 none fails",
              not verify(episode, None, ws).passed)

        # B5 naive paths must fail
        v_raw = verify(episode, naive(episode, do_qc=False), ws)
        check(f"s{seed}/{condition} B5 no-QC-printed-conc fails", not v_raw.passed,
              f"passed with {v_raw.checkpoints}")
        v_qc = verify(episode, naive(episode, do_qc=True), ws)
        if condition == "C0":
            check(f"s{seed}/C0 careful-analyst passes (false-alarm control)",
                  v_qc.passed, f"{v_qc.first_failed} {v_qc.detail}")
        else:
            check(f"s{seed}/{condition} B5 printed-conc fails", not v_qc.passed,
                  f"passed with {v_qc.checkpoints}")

        # verifier's own recomputation must agree with the construction
        detail = verify(episode, reference(episode), ws).detail
        check(f"s{seed}/{condition} QC rule finds the planted artifacts",
              detail["n_bad_recomputed"] == episode.key["n_artifacts"]
              and detail["recomputed_bad_wells"] == episode.key["artifact_wells"],
              f"{detail['recomputed_bad_wells']} vs {episode.key['artifact_wells']}")
        if episode.key["determinable"]:
            ratio = detail["ic50_recomputed"] / episode.key["true_ic50_uM"]
            check(f"s{seed}/{condition} refit matches construction",
                  0.85 <= ratio <= 1.18, f"ratio={ratio:.3f}")
        else:
            check(f"s{seed}/{condition} F2 judged non-determinable",
                  detail["determinable_recomputed"] is False,
                  f"max_inh={detail['max_inhibition_recomputed']}")

        answers[f"{condition}:ic50_uM"].append(
            None if not episode.key["determinable"] else round(episode.key["true_ic50_uM"], 3))
        answers[f"{condition}:decision"].append(episode.key["decision"])
        answers[f"{condition}:n_excluded"].append(episode.key["n_artifacts"])
        answers[f"{condition}:max_inh"].append(round(episode.key["max_inhibition_pct"], 1))

    # C0/H1 byte-identity of the brief, and of everything except the handler log
    c0, h1, f2 = episodes["C0"], episodes["H1"], episodes["F2"]
    check(f"s{seed} C0/H1 briefs byte-identical", c0.brief == h1.brief)
    check(f"s{seed} C0/F2 briefs byte-identical", c0.brief == f2.brief)
    differing = sorted(n for n in c0.files if c0.files[n] != h1.files[n])
    check(f"s{seed} C0/H1 differ only in run_log.txt", differing == ["run_log.txt"],
          str(differing))
    check(f"s{seed} H1 answer differs from C0 answer",
          abs(math.log10(h1.key["true_ic50_uM"] / c0.key["true_ic50_uM"])) > 0.3
          and h1.key["decision"] != c0.key["decision"],
          f"{c0.key['true_ic50_uM']:.4g} vs {h1.key['true_ic50_uM']:.4g}")
    size = sum(len(t) for t in c0.files.values())
    check(f"s{seed} workspace small ({size} B)", size < 6000)

check("FAMILY exports build and verify",
      FAMILY["build"] is build and FAMILY["verify"] is verify)

# --- gate: giveaway scan over the brief and every artifact ------------------
try:
    from crucible.chain.spec import giveaway_scan
    episode = build(11, "C0")
    findings = giveaway_scan({"prompt": episode.brief, "artifacts": episode.files,
                              "stages": []})
    check("giveaway_scan clean", not findings, "; ".join(findings[:4]))
    print("  giveaway_scan over brief + 3 artifacts: "
          f"{len(findings)} findings")
except ImportError as exc:                       # pragma: no cover
    print(f"  (giveaway_scan unavailable: {exc})")

print("\nanswer distribution across seeds 11-16 (requirement 6)")
print("-" * 78)
for condition in CONDITIONS:
    for stage in ("ic50_uM", "max_inh", "n_excluded", "decision"):
        values = answers[f"{condition}:{stage}"]
        distinct = len(set(map(str, values)))
        note = ""
        # The two abstention-valued stages are constant *within* F2 by
        # definition - F2 is the condition in which the refusal is the answer -
        # so the constancy bar is applied to every other stage and to the
        # decision pooled over conditions.
        exempt = condition == "F2" and stage in ("ic50_uM", "decision")
        if exempt:
            note = "  (abstention stage, exempt)"
        else:
            check(f"{condition}/{stage} not constant across seeds", distinct > 1)
        print(f"  {condition} {stage:<11} {values}   distinct={distinct}{note}")

print("\ncondition does not determine the answer")
print("-" * 78)
for condition in CONDITIONS:
    print(f"  {condition} decision: {Counter(answers[f'{condition}:decision'])}")
check("C0 decisions vary", len(set(answers["C0:decision"])) > 1)
check("H1 decisions vary", len(set(answers["H1:decision"])) > 1)
pooled = sum((answers[f"{c}:decision"] for c in CONDITIONS), [])
check("pooled decisions take >=3 values", len(set(pooled)) >= 3)
for value in ("advance", "hold"):
    check(f"'{value}' occurs in both C0 and H1",
          value in answers["C0:decision"] and value in answers["H1:decision"])

print("\nbaseline ladder (checkpoints scored, per condition, seeds 11-16)")
print("-" * 78)
ladder: dict[str, Counter] = {}
for condition in CONDITIONS:
    for label, make in (("B8 reference (from key)", lambda e: reference(e)),
                        ("B8a module reference_submission", reference_submission),
                        ("B8b independent 4PL path", lambda e: competent(e)),
                        ("B8c absolute-IC50 convention",
                         lambda e: competent(e, absolute_convention=True)),
                        ("B1 empty", lambda e: {}),
                        ("B5 naive (no QC, printed conc)", lambda e: naive(e, False)),
                        ("B5 careful (QC, printed conc)", lambda e: naive(e, True))):
        tally = ladder.setdefault(f"{label} | {condition}", Counter())
        for seed in SEEDS:
            episode = build(seed, condition)
            verdict = verify(episode, make(episode), WORKSPACE / f"s{seed}_{condition}")
            tally["pass" if verdict.passed else "fail"] += 1
            if not verdict.passed:
                tally[f"first={verdict.first_failed}"] += 1
                for name, ok in verdict.checkpoints.items():
                    if not ok:
                        tally[f"-{name}"] += 1
for name, tally in ladder.items():
    print(f"  {name:<40} {dict(tally)}")
    if name.startswith("B8"):
        check(f"{name} solves the episode", tally.get("pass") == len(SEEDS))
    if name.startswith(("B1", "B5 naive")):
        check(f"{name} is rejected", tally.get("fail") == len(SEEDS))
    if name.startswith("B5 careful") and "C0" not in name:
        check(f"{name} is rejected", tally.get("fail") == len(SEEDS))

print("\ngenerator robustness over 60 fresh seeds")
print("-" * 78)
worst_inh, worst_ic50, built = 0.0, 1.0, 0
spread: dict[str, float] = {}
for seed in range(1, 61):
    for condition in CONDITIONS:
        episode = build(seed, condition)
        built += 1
        verdict = verify(episode, reference(episode), WORKSPACE / "sweep")
        check(f"s{seed}/{condition} reference passes", verdict.passed,
              f"{verdict.first_failed} {verdict.detail}")
        for label, submission in (("module reference", reference_submission(episode)),
                                  ("independent 4PL", competent(episode)),
                                  ("absolute IC50", competent(episode, True))):
            other = verify(episode, submission, WORKSPACE / "sweep")
            check(f"s{seed}/{condition} {label} passes", other.passed,
                  f"{other.first_failed} {submission} {other.detail}")
            if episode.key["determinable"]:
                r = submission["ic50_uM"] / other.detail["ic50_recomputed"]
                spread[label] = max(spread.get(label, 1.0), max(r, 1.0 / r))
        worst_inh = max(worst_inh, abs(verdict.detail["max_inhibition_recomputed"]
                                       - episode.key["max_inhibition_pct"]))
        if episode.key["determinable"]:
            worst_ic50 = max(worst_ic50, max(
                verdict.detail["ic50_recomputed"] / episode.key["true_ic50_uM"],
                episode.key["true_ic50_uM"] / verdict.detail["ic50_recomputed"]))
print(f"  built and scored {built} episodes; worst |constructed - recomputed| "
      f"inhibition = {worst_inh:.2f} pp (tolerance {INHIBITION_TOLERANCE_PP}), "
      f"worst construction-vs-refit IC50 ratio = {worst_ic50:.3f} "
      f"(tolerance {IC50_TOLERANCE_FACTOR})")
print("  worst solver-vs-verifier IC50 ratio by path: "
      + ", ".join(f"{k} {v:.3f}" for k, v in sorted(spread.items())))
check("construction and recomputation agree on every seed",
      worst_inh < 5.0 and worst_ic50 < 1.20, f"{worst_inh:.2f} pp, {worst_ic50:.3f}x")

print("\nworked example (seed 12)")
print("-" * 78)
for condition in CONDITIONS:
    episode = build(12, condition)
    verdict = verify(episode, reference(episode), WORKSPACE / f"s12_{condition}")
    print(f"  {condition}: key ic50={episode.key['true_ic50_uM']:.4g} uM  "
          f"nominal={episode.key['nominal_ic50_uM']:.4g} uM  "
          f"thr={episode.key['threshold_uM']} uM  decision={episode.key['decision']}  "
          f"defect={episode.key['defect']}  bad_wells={episode.key['artifact_wells']}")
    print(f"      verifier: refit={verdict.detail.get('ic50_recomputed')} "
          f"max_inh={verdict.detail['max_inhibition_recomputed']} "
          f"determinable={verdict.detail['determinable_recomputed']} "
          f"passed={verdict.passed}")

print("\n" + "=" * 78)
print(f"{'ALL CHECKS PASSED' if not failures else str(len(failures)) + ' FAILURES'}")
for line in failures[:20]:
    print("  - " + line)
print("=" * 78)
sys.exit(1 if failures else 0)
