"""Assemble the public release package (guide 26.24 / 32.2).

`build(version)` gathers every report, verifies the sealed set is excluded,
computes artifact hashes, runs criterion validity, and writes release/<v>/.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from .paths import find_repo_root

PUBLIC_DOCS = [
    ("docs/LIMITATIONS.md", "limitations.md"),
    ("docs/NOT_DONE.md", "not_done.md"),
    ("analysis/preregistrations/campaign-0.2.0.md", "prereg-0.2.0.md"),
    ("analysis/preregistrations/campaign-0.3.0.md", "prereg-0.3.0.md"),
    ("analysis/preregistrations/campaign-1.0.0.md", "prereg-1.0.0.md"),
    ("runs/release-0.2.0/scorecard.md", "scorecard-0.2.0.md"),
    ("runs/release-0.3.0/scorecard.md", "scorecard-0.3.0.md"),
    ("runs/release-1.0.0/scorecard.md", "scorecard-1.0.0.md"),
    ("release/0.2.0/signoff.md", "signoff-0.2.0.md"),
    ("release/0.2.0/corrections.md", "corrections.md"),
    ("release/0.2.0/benchmark_card.md", "benchmark_card-0.2.0.md"),
    ("release/0.3.0/system_cards.md", "system_cards-0.3.0.md"),
    ("release/0.3.0/signoff.md", "signoff-0.3.0.md"),
    ("runs/corrections/CORR-002/CORR-002.md", "corrections-CORR-002.md"),
    ("runs/corrections/CORR-003/CORR-003.md", "corrections-CORR-003.md"),
    ("runs/corrections/CORR-004/CORR-004.md", "corrections-CORR-004.md"),
    ("runs/corrections/CORR-006/CORR-006.md", "corrections-CORR-006.md"),
    ("analysis/literature/README.md", "literature-review.md"),
    ("analysis/crucible3_design.md", "crucible3-design.md"),
    ("analysis/preregistrations/campaign-3.0.0.md", "prereg-3.0.0.md"),
    ("runs/corrections/CORR-004-rescore-report.json", "corrections-CORR-004-flips.json"),
    ("release/1.0.0/signoff.md", "signoff-1.0.0.md"),
    ("release/1.0.0/benchmark_card.md", "benchmark_card-1.0.0.md"),
    ("governance/program_charter.md", "program_charter.md"),
    ("governance/decision_rights_and_boards.md", "governance.md"),
]


def criterion_validity(repo: Path) -> dict:
    """Does cheap hidden-set RCR track the simulator outcomes across systems?
    Spearman rank correlation, tiny n - reported as a diagnostic, never proof."""
    summary_path = repo / "runs" / "release-1.0.0" / "summary.json"
    if not summary_path.exists():
        return {"status": "release campaign summary missing"}
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    rcr = {}
    for system, s in summary.items():
        hit, n = s["hidden"]
        if n:
            rcr[system] = hit / n

    briers = {}
    hits_e = {}
    for label in ("release-0.2.0", "release-0.3.0"):
        d = repo / "runs" / label / "trackD" / "trackD_report.json"
        e = repo / "runs" / label / "trackE" / "trackE_report.json"
        if d.exists():
            for name, score in json.loads(d.read_text(encoding="utf-8"))["scores"].items():
                if isinstance(score, float):
                    briers[name.replace("openrouter/", "")] = score
        if e.exists():
            for arm, data in json.loads(e.read_text(encoding="utf-8"))["arms"].items():
                ladder = data.get("ladder", {})
                hits_e[arm.replace("openrouter/", "")] = ladder.get("N_primary_positive", 0)

    def norm(name: str) -> str:
        return name.replace("openrouter/", "")

    pairs_d = [(rcr[s], briers[norm(s)]) for s in rcr if norm(s) in briers]
    pairs_e = [(rcr[s], hits_e[norm(s)]) for s in rcr if norm(s) in hits_e]

    def spearman(pairs):
        if len(pairs) < 4:
            return None
        def ranks(vals):
            order = sorted(range(len(vals)), key=lambda i: vals[i])
            out = [0.0] * len(vals)
            for rank, idx in enumerate(order):
                out[idx] = rank
            return out
        xs = ranks([p[0] for p in pairs]); ys = ranks([p[1] for p in pairs])
        n = len(pairs)
        mx = sum(xs) / n; my = sum(ys) / n
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
        return num / den if den else None

    return {
        "n_systems_with_brier": len(pairs_d),
        "spearman_rcr_vs_brier": spearman(pairs_d),
        "expected_direction": "negative (higher RCR should mean lower Brier)",
        "n_systems_with_discovery": len(pairs_e),
        "spearman_rcr_vs_discovery_hits": spearman(pairs_e),
        "caveat": "n<=9 systems; diagnostic only, not criterion-validity proof",
    }


def build(version: str = "1.0.0") -> dict:
    repo = find_repo_root()
    out = repo / "release" / version
    out.mkdir(parents=True, exist_ok=True)

    missing = []
    for src_rel, dst_name in PUBLIC_DOCS:
        src = repo / src_rel
        if src.exists():
            shutil.copy2(src, out / dst_name)
        else:
            missing.append(src_rel)

    cv = criterion_validity(repo)
    (out / "criterion_validity.json").write_text(json.dumps(cv, indent=2), encoding="utf-8")

    # Sealed-exclusion check: nothing under release/ may reference sealed paths
    # content, and the sealed directory itself is git-ignored.
    sealed_leak = []
    for path in out.rglob("*"):
        if path.is_file() and path.suffix in (".md", ".json"):
            text = path.read_text(encoding="utf-8", errors="replace")
            if "tasks_sealed/GEN-" in text and path.name not in ("build_manifest.json",):
                # naming the directory is fine; leaking instance content is not -
                # check for truth marker content
                pass
    for path in out.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace") if path.suffix in (".md", ".json") else ""
            if "CRUCIBLE-TRUTH-ZONE-DO-NOT-DISTRIBUTE" in text:
                sealed_leak.append(str(path))

    hashes = {}
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "build_manifest.json":
            hashes[path.relative_to(out).as_posix()] = hashlib.sha256(
                path.read_bytes()).hexdigest()
    manifest = {
        "version": version,
        "files": hashes,
        "missing_inputs": missing,
        "truth_marker_leaks": sealed_leak,
        "sealed_dir_gitignored": "tasks_sealed/" in (repo / ".gitignore").read_text(encoding="utf-8"),
    }
    (out / "build_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
