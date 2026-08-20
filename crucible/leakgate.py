"""Repository-wide truth-boundary gate (CORR-005).

crucible.packaging already keeps truth out of the bundle a candidate sees; that
boundary works. This module enforces the OTHER boundary - what may be committed
and published - which nothing checked before. Run it in CI, in a pre-push hook,
and as a hard gate in release_build.

The failure it prevents is the most common one in the field: CORE-Bench shipped
values that made 20 of 45 hard tasks answerable without doing the analysis, and
GAIA published the answers for its own validation split.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .paths import find_repo_root

TRUTH_MARKER = "CRUCIBLE-TRUTH-ZONE-DO-NOT-DISTRIBUTE"

# Live credential shapes. CORR-013: a model printed os.environ inside the
# sandbox, the sandbox had inherited the parent's environment, and four
# provider keys were written into 26 episode transcripts - which this gate did
# not see, because it only looked at git-tracked files and the episode tree is
# gitignored. It now scans recorded data too, whether git would publish it or
# not, because "not committed" is not the same as "not distributed".
CREDENTIAL_PATTERNS = {
    "anthropic": r"sk-ant-api03-[A-Za-z0-9_\-]{20,}",
    "openai": r"sk-proj-[A-Za-z0-9_\-]{20,}",
    "openrouter": r"sk-or-v1-[A-Za-z0-9_\-]{20,}",
    "nvidia": r"nvapi-[A-Za-z0-9_\-]{20,}",
    "xai": r"xai-[A-Za-z0-9]{20,}",
    "huggingface": r"hf_[A-Za-z0-9]{30,}",
    "google_oauth": r"ya29\.[A-Za-z0-9_\-]{20,}",
    "private_key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
}

# Trees that are not committed but ARE published (the Hugging Face release
# ships the episode records). Scanned for credentials, not for truth paths.
DISTRIBUTED_DATA_GLOBS = ("runs/lab-*/systems/*/outcomes/*.json",
                          "runs/lab-*/systems/*/censored/*.json",
                          "runs/lab-*/scorecard.md",
                          "runs/corrections/**/*.json",
                          "runs/corrections/**/*.md")

# Paths that must never be publishable, expressed as path fragments.
FORBIDDEN_FRAGMENTS = (
    "/truth/", "/truth2/", "/truth_chain/",
    "/verification/tests/accepted/", "/verification/tests/rejected/",
    "tasks_sealed/", "tasks_chain_sealed/",
)
FORBIDDEN_FILES = (
    "crucible/taskgen/archetypes.py",
    "crucible/taskgen/factory.py",
    "crucible/chain/plan.py",
    "crucible/chain/exemplar.py",
)


def _tracked_files(repo: Path) -> list[str] | None:
    """Files git would publish. None when this is not a git working tree."""
    try:
        result = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def _ignore_rules(repo: Path) -> list[str]:
    path = repo / ".gitignore"
    if not path.exists():
        return []
    rules = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            rules.append(line)
    return rules


def _rule_regex(rule: str):
    """Translate the gitignore syntax we actually use into a regex."""
    import re

    is_dir = rule.endswith("/")
    body = rule.rstrip("/")
    anchored = body.startswith("/")
    body = body.lstrip("/")

    out = []
    index = 0
    while index < len(body):
        if body.startswith("**/", index):
            out.append("(?:.*/)?")
            index += 3
        elif body.startswith("/**", index):
            out.append("(?:/.*)?")
            index += 3
        elif body.startswith("**", index):
            out.append(".*")
            index += 2
        elif body[index] == "*":
            out.append("[^/]*")
            index += 1
        elif body[index] == "?":
            out.append("[^/]")
            index += 1
        else:
            out.append(re.escape(body[index]))
            index += 1
    pattern = "".join(out)
    # A directory rule matches the directory and everything beneath it; a file
    # rule matches the path itself. Unanchored rules may match at any depth.
    tail = "(?:/.*)?$" if is_dir else "(?:/.*)?$"
    head = "^" if anchored else "^(?:.*/)?"
    return re.compile(head + pattern + tail)


def _is_ignored(rel: str, rules: list[str]) -> bool:
    for rule in rules:
        if _rule_regex(rule).match(rel):
            return True
    return False


def scan(repo: Path | None = None) -> dict:
    repo = repo or find_repo_root()
    tracked = _tracked_files(repo)
    violations: list[str] = []

    if tracked is None:
        # Not a git repo yet: simulate what a first commit would publish by
        # walking the tree and applying the .gitignore rules ourselves.
        ignored = _ignore_rules(repo)
        candidates = []
        for pattern in ("tasks_public", "tasks_open", "tasks_chain",
                        "tasks_sealed", "tasks_chain_sealed", "crucible"):
            base = repo / pattern
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if not path.is_file():
                    continue
                rel = str(path.relative_to(repo)).replace("\\", "/")
                if not _is_ignored(rel, ignored):
                    candidates.append(rel)
        mode = "filesystem (no git tree; .gitignore applied)"
    else:
        candidates = tracked
        mode = "git-tracked"

    for rel in candidates:
        if any(fragment in "/" + rel for fragment in FORBIDDEN_FRAGMENTS):
            violations.append(f"forbidden path published: {rel}")
        if rel in FORBIDDEN_FILES:
            violations.append(f"generator/answer-deriving source published: {rel}")

    # The canary in a DATA file means real truth content leaked. In a .py file
    # it is the constant the packaging and scanning code is built around, which
    # is exactly where it belongs.
    marker_hits = []
    for rel in candidates:
        path = repo / rel
        if not path.is_file() or path.suffix.lower() not in (
                ".md", ".json", ".yaml", ".yml", ".txt", ".csv"):
            continue
        try:
            if TRUTH_MARKER in path.read_text(encoding="utf-8", errors="replace"):
                marker_hits.append(rel)
        except OSError:
            continue
    violations += [f"truth marker present in publishable data file: {m}" for m in marker_hits]

    creds, n_data = _credential_scan(repo, candidates)
    violations += creds

    return {"mode": mode, "n_checked": len(candidates),
            "n_data_checked": n_data,
            "violations": violations, "clean": not violations}


def _credential_scan(repo: Path, candidates: list[str]) -> tuple[list[str], int]:
    """Hunt live credentials in everything we might hand to someone else."""
    import glob as _glob
    import re as _re

    compiled = {name: _re.compile(pat) for name, pat in CREDENTIAL_PATTERNS.items()}
    targets = set()
    for rel in candidates:
        if (repo / rel).is_file():
            targets.add(str(repo / rel))
    for pattern in DISTRIBUTED_DATA_GLOBS:
        targets.update(_glob.glob(str(repo / pattern), recursive=True))

    found = []
    for path in sorted(targets):
        suffix = Path(path).suffix.lower()
        if suffix not in (".md", ".json", ".yaml", ".yml", ".txt", ".csv",
                          ".py", ".jsonl", ".env", ".cfg", ".toml"):
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError:
            continue
        for name, pat in compiled.items():
            if pat.search(text):
                rel = str(Path(path).relative_to(repo)).replace("\\", "/")
                found.append(f"live {name} credential in {rel}")
    return found, len(targets)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="leakgate")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = scan()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"leak gate: {report['mode']}, {report['n_checked']} files checked")
        for violation in report["violations"][:40]:
            print("  VIOLATION:", violation)
        print("CLEAN" if report["clean"] else f"{len(report['violations'])} VIOLATIONS")
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
