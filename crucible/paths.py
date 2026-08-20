"""Repository path discovery and shared constants."""
from __future__ import annotations

from pathlib import Path

REPO_MARKERS = ("pyproject.toml", "schemas")

# Canary marker embedded in every truth-zone file so the truth-boundary
# scanner can detect leakage into agent-visible bundles by content, not
# only by path.
TRUTH_MARKER = "CRUCIBLE-TRUTH-ZONE-DO-NOT-DISTRIBUTE"

# Directories inside a task that belong to the truth/verification zone and
# must never be packaged into an agent-visible bundle.
TRUTH_ZONE_DIRS = ("truth", "verification", "pilot", "leakage", "release")


def find_repo_root(start: Path | None = None) -> Path:
    """Walk upward from *start* until a directory looks like the repo root."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if all((candidate / marker).exists() for marker in REPO_MARKERS):
            return candidate
    raise FileNotFoundError(
        "Could not locate the CRUCIBLE repository root (needs pyproject.toml and schemas/)."
    )


def schemas_dir(root: Path | None = None) -> Path:
    return find_repo_root(root) / "schemas"


def registry_dir(root: Path | None = None) -> Path:
    d = find_repo_root(root) / "registry"
    d.mkdir(parents=True, exist_ok=True)
    return d
