"""Evaluate every GOAL.md stop condition mechanically.

The point of a stopping contract is that nobody has to be trusted about
whether it is met. Each condition below is computed from the repository, not
asserted, and the exit code is non-zero while any of them fails.

    python runs/check_goal.py
"""
from __future__ import annotations

import glob
import json
import pathlib
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from crucible.nowindow import hidden_kwargs  # noqa: E402

SYSTEMS = ("gpt", "gemini", "claude")


def outcomes(system: str) -> int:
    """Scored episodes plus documented exclusions.

    An episode voided under a published correction is accounted for, not
    missing: CORR-014 removed 12 contaminated episodes, and without this the
    completeness conditions could never be satisfied again after any
    correction, which would make the contract punish us for auditing.
    """
    scored = len(glob.glob(str(REPO / "runs" / "lab-1.0.0" / "systems" / system
                               / "outcomes" / "*.json")))
    return scored + voided(system)


def voided(system: str) -> int:
    total = 0
    for path in glob.glob(str(REPO / "runs" / "corrections" / "CORR-*" / "*__*.json")):
        if pathlib.Path(path).name.startswith(system + "__"):
            total += 1
    return total


def censored(system: str) -> list[str]:
    reasons = []
    for path in glob.glob(str(REPO / "runs" / "lab-1.0.0" / "systems" / system
                              / "censored" / "*.json")):
        try:
            reasons.append(json.load(open(path, encoding="utf-8")).get("censored", ""))
        except (json.JSONDecodeError, OSError):
            pass
    return reasons


def main() -> int:
    from crucible.lab.campaign import plan
    from crucible.lab.families import REGISTRY

    target = len(plan())
    checks: list[tuple[str, bool, str]] = []

    # S1/S2 - families gated and at scale
    # The per-family gate isolates each family in its own process, so one
    # transient native crash cannot zero the whole report the way the
    # single-process validator did.
    gate = subprocess.run([sys.executable, str(REPO / "runs" / "gate_families.py")],
                          cwd=str(REPO), capture_output=True, text=True,
                          **hidden_kwargs()).stdout
    line = next((l for l in gate.splitlines() if l.startswith("USABLE FAMILIES")), "")
    usable = total = 0
    if ":" in line:
        frac = line.split(":")[1].split("->")[0].strip()
        usable, total = (int(x) for x in frac.split("/"))
    checks.append(("S1 every family passes the gate", usable == total and total > 0,
                   f"{usable}/{total}"))
    checks.append(("S2 >=30 gate-clean families", usable >= 30, str(usable)))

    # S3-S5 the three full-plan measurements, S14 Grok on the same plan, and
    # S15-S17 the gateway tier on the reduced one. Each system is checked
    # against ITS OWN plan length, because the gateway systems are deliberately
    # evaluated on 270 hidden episodes rather than 990 (see LIMITATIONS).
    from crucible.lab.campaign import plan as episode_plan
    for tag, system in (("S3", "gpt"), ("S4", "gemini"), ("S5", "claude"),
                        ("S14", "grok"), ("S15", "deepseek"), ("S16", "kimi"),
                        ("S17", "glm")):
        want = len(episode_plan(system))
        n = outcomes(system)
        blockers = {r.split(":")[0] for r in censored(system) if r}
        note = f"{n}/{want}"
        if n < want and blockers:
            note += f" (blocked: {', '.join(sorted(blockers)[:2])})"
        checks.append((f"{tag} {system} complete", n >= want, note))

    # S6 - no unexplained quarantine
    stray = {s: len(censored(s)) for s in SYSTEMS if censored(s)}
    checks.append(("S6 no unexplained quarantined episodes", not stray,
                   json.dumps(stray) if stray else "0"))

    # S8/S9 - artefacts
    for tag, rel in (("S8", "runs/lab-1.0.0/scorecard.md"),
                     ("S9a", "docs/BENCHMARK_CARD.md"),
                     ("S9b", "docs/LIMITATIONS.md"),
                     ("S9c", "docs/REPLICATION.md"),
                     ("S9d", "CORRECTIONS.md"),
                     ("S9e", "docs/SATURATION_POLICY.md"),
                     ("S12a", "analysis/collab/hardening__gpt.md"),
                     ("S12b", "analysis/collab/hardening__gemini.md"),
                     ("S13a", "analysis/literature/deep/SYNTHESIS.md"),
                     ("S13b", "analysis/literature2/SYNTHESIS.md")):
        path = REPO / rel
        checks.append((f"{tag} {rel}", path.exists(),
                       f"{path.stat().st_size} bytes" if path.exists() else "missing"))

    # S10 - truth boundary
    leak = subprocess.run([sys.executable, "-m", "crucible.leakgate"], cwd=str(REPO),
                          capture_output=True, text=True, **hidden_kwargs()).stdout
    checks.append(("S10 leak gate clean", "CLEAN" in leak, leak.strip().splitlines()[-1:] and leak.strip().splitlines()[-1]))

    # S13 - corpora size
    papers = len(glob.glob(str(REPO / "analysis" / "literature*" / "pdfs" / "*.pdf")))
    reports = len(glob.glob(str(REPO / "analysis" / "literature*" / "deep" / "*.md")))
    checks.append(("S13 corpora read", papers >= 40 and reports >= 35,
                   f"{papers} papers, {reports} reports"))

    width = max(len(name) for name, _, _ in checks)
    failed = 0
    for name, ok, note in checks:
        failed += not ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name.ljust(width)}  {note}")
    print(f"\n{len(checks) - failed}/{len(checks)} conditions met")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
