"""Agent-visible bundle packaging and truth-access boundary enforcement.

The evaluation runner must never see truth, verification manifests, or pilot
records (guide sections 26.2 and F.9). `build_agent_bundle` copies only the
task card and agent-visible inputs; `scan_for_truth` then proves by path AND
by content marker that nothing from the truth zone leaked into the bundle.
"""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from .paths import TRUTH_MARKER, TRUTH_ZONE_DIRS

AGENT_VISIBLE_PARTS = [
    ("task_card", "task_card"),
    ("inputs/agent_visible", "inputs"),
]


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_agent_bundle(task_dir: Path, out_dir: Path) -> list[Path]:
    """Copy only agent-visible material into *out_dir*. Returns copied files."""
    task_dir = task_dir.resolve()
    out_dir = out_dir.resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"Bundle target {out_dir} is not empty.")
    out_dir.mkdir(parents=True, exist_ok=True)

    copied: list[Path] = []
    for source_rel, dest_rel in AGENT_VISIBLE_PARTS:
        source = task_dir / source_rel
        if not source.exists():
            continue
        dest = out_dir / dest_rel
        shutil.copytree(source, dest)
        copied.extend(p for p in dest.rglob("*") if p.is_file())
    if not copied:
        raise FileNotFoundError(
            f"Task {task_dir} has no agent-visible material "
            "(expected task_card/ and inputs/agent_visible/)."
        )
    return copied


def scan_for_truth(bundle_dir: Path, task_dir: Path) -> list[str]:
    """Return a list of violations if any truth-zone content is in the bundle."""
    violations: list[str] = []
    bundle_dir = bundle_dir.resolve()
    task_dir = task_dir.resolve()

    # Hashes of every file that lives in a truth-zone directory of the task.
    truth_hashes: dict[str, str] = {}
    for zone in TRUTH_ZONE_DIRS:
        zone_dir = task_dir / zone
        if zone_dir.exists():
            for path in zone_dir.rglob("*"):
                if path.is_file():
                    truth_hashes[_file_hash(path)] = str(path.relative_to(task_dir))

    for path in bundle_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(bundle_dir)
        # Path-name check: nothing in the bundle may be named like a truth dir.
        if any(part in TRUTH_ZONE_DIRS for part in rel.parts[:-1]):
            violations.append(f"{rel}: truth-zone directory name inside bundle")
        # Content-identity check.
        digest = _file_hash(path)
        if digest in truth_hashes:
            violations.append(f"{rel}: identical content to truth file {truth_hashes[digest]}")
        # Canary-marker check.
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if TRUTH_MARKER in text:
            violations.append(f"{rel}: contains truth-zone canary marker")
    return violations
