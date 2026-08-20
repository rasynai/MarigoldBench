import shutil
from pathlib import Path

from crucible.packaging import build_agent_bundle, scan_for_truth


def test_bundle_contains_no_truth(lc_n0: Path, tmp_path: Path):
    bundle = tmp_path / "bundle"
    copied = build_agent_bundle(lc_n0, bundle)
    assert copied, "bundle is empty"
    violations = scan_for_truth(bundle, lc_n0)
    assert not violations, violations
    # The bundle must contain the card and inputs, and nothing else.
    names = {p.relative_to(bundle).parts[0] for p in bundle.rglob("*") if p.is_file()}
    assert names == {"task_card", "inputs"}


def test_scanner_catches_planted_truth_leak(lc_n0: Path, tmp_path: Path):
    bundle = tmp_path / "bundle"
    build_agent_bundle(lc_n0, bundle)
    # Simulate a packaging mistake: copy a truth file into the bundle.
    shutil.copy(lc_n0 / "truth" / "endpoint_concentration.yaml", bundle / "inputs" / "notes.yaml")
    violations = scan_for_truth(bundle, lc_n0)
    assert violations, "scanner failed to detect a planted truth leak"


def test_scanner_catches_marker_leak(ops_s1: Path, tmp_path: Path):
    bundle = tmp_path / "bundle"
    build_agent_bundle(ops_s1, bundle)
    # Simulate paraphrased truth pasted into an input file (marker survives).
    leaked = bundle / "inputs" / "project" / "hint.txt"
    leaked.write_text("psst: CRUCIBLE-TRUTH-ZONE-DO-NOT-DISTRIBUTE expected answer inside",
                      encoding="utf-8")
    violations = scan_for_truth(bundle, ops_s1)
    assert any("canary marker" in v for v in violations)
