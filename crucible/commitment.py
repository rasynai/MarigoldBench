"""Cryptographic pre-campaign commitment to the sealed split.

The community's most-repeated integrity complaint is that "we preregistered"
is self-attestation. This makes it checkable: before a campaign, every sealed
file is hashed with a private salt into a manifest, and the single manifest
digest is published (committed to git, and printable anywhere external).
After the campaign, releasing the salt plus the manifest lets anyone verify
that the sealed instances scored are byte-identical to the ones committed to
before any candidate ran - no post-hoc swaps, no quiet regeneration.

The salt lives in .secrets/ (never committed): publishing the digest reveals
nothing about the sealed content, publishing the salt later proves it.

    python -m crucible.commitment make [--label NAME]
    python -m crucible.commitment verify --label NAME
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

from .paths import find_repo_root

SEALED_DIRS = ("tasks_chain_sealed", "tasks_sealed")


def _salt(repo: Path) -> bytes:
    path = repo / ".secrets" / "commitment_salt.bin"
    if not path.exists():
        import os
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(os.urandom(32))
    return path.read_bytes()


def _manifest(repo: Path) -> dict[str, str]:
    salt = _salt(repo)
    entries: dict[str, str] = {}
    for base in SEALED_DIRS:
        root = repo / base
        if not root.exists():
            continue
        for file in sorted(root.rglob("*")):
            if not file.is_file():
                continue
            digest = hashlib.sha256(salt + file.read_bytes()).hexdigest()
            entries[str(file.relative_to(repo)).replace("\\", "/")] = digest
    return entries


def make(label: str) -> Path:
    repo = find_repo_root()
    entries = _manifest(repo)
    manifest_bytes = json.dumps(entries, sort_keys=True).encode()
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    out = repo / "commitments" / f"{label}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "label": label,
        "committed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_sealed_files": len(entries),
        "manifest_sha256": digest,
        "scheme": "sha256(salt || file_bytes) per file; manifest digest over"
                  " the sorted JSON; salt withheld until post-campaign reveal",
    }, indent=2), encoding="utf-8")
    # The full salted manifest stays private until reveal.
    private = repo / ".secrets" / f"commitment_manifest_{label}.json"
    private.write_text(json.dumps(entries, sort_keys=True, indent=1), encoding="utf-8")
    print(json.dumps({"label": label, "sealed_files": len(entries),
                      "manifest_sha256": digest, "public": str(out)}))
    return out


def verify(label: str) -> int:
    repo = find_repo_root()
    public = json.loads((repo / "commitments" / f"{label}.json").read_text(encoding="utf-8"))
    entries = _manifest(repo)
    digest = hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()
    ok = digest == public["manifest_sha256"]
    changed = []
    if not ok:
        old = json.loads((repo / ".secrets" / f"commitment_manifest_{label}.json")
                         .read_text(encoding="utf-8"))
        changed = sorted(set(old) ^ set(entries)) \
            + sorted(k for k in set(old) & set(entries) if old[k] != entries[k])
    print(json.dumps({"label": label, "intact": ok, "changed": changed[:20]}))
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(prog="crucible.commitment")
    sub = parser.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("--label", default=time.strftime("%Y%m%d", time.gmtime()))
    v = sub.add_parser("verify")
    v.add_argument("--label", required=True)
    args = parser.parse_args()
    return make(args.label) and 0 if args.cmd == "make" else verify(args.label)


if __name__ == "__main__":
    sys.exit(main())
