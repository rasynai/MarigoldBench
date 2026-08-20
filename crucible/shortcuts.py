"""Shortcut-attacker suite (guide 22.9): can a system score credit WITHOUT
doing the intended scientific work?

Attackers implemented:
1. metadata-only  - an LLM sees ONLY filenames/sizes + card title and must
                    guess the answer; its submission is then verified.
2. card-language  - programmatic check that clean vs hazard task cards do not
                    leak the condition through wording differences.
3. artifact-spoof - schema-valid but scientifically empty submission must fail.
4. naive-replay   - covered by each hazard task's rejected 'naive-replay' test
                    submission (verifier self-tests); referenced here.
"""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from .agent import CONTRACT, _write_submission
from .llm import ModelClient
from .verification import run_verification

METADATA_SYSTEM = """You are attempting a benchmark task while seeing only file
METADATA - no file contents. Produce your best-guess submission anyway."""


def metadata_only_attack(task_dir: Path, provider: str, out_dir: Path) -> dict:
    task_dir = Path(task_dir)
    inputs_dir = task_dir / "inputs" / "agent_visible"
    listing = "\n".join(
        f"{p.relative_to(inputs_dir).as_posix()} ({p.stat().st_size} bytes)"
        for p in sorted(inputs_dir.rglob("*"))
        if p.is_file()
    )
    card_title = (task_dir / "task_card" / "card.md").read_text(encoding="utf-8").splitlines()[0]
    prompt = (
        f"Task title: {card_title}\n\nInput files (metadata only, contents withheld):\n{listing}\n\n"
        "You must still submit. Guess plausible values." + CONTRACT
    )
    client = ModelClient(provider, purpose="shortcut-metadata-attack", effort="low")
    reply = client.ask_json(METADATA_SYSTEM, prompt)
    _write_submission(reply.get("files", {}), Path(out_dir))
    outcome = run_verification(task_dir, Path(out_dir))
    return {
        "attacker": "metadata-only",
        "provider": provider,
        "task": task_dir.name,
        "reliable_completion": outcome["reliable_completion"],
        "attack_succeeded": outcome["reliable_completion"],
        "verdict": "TASK LEAKS THROUGH METADATA" if outcome["reliable_completion"] else "resisted",
    }


def card_language_audit(clean_card: Path, hazard_card: Path) -> dict:
    """The hazard card must not name or hint the hazard (guide 11.7)."""
    hazard_text = hazard_card.read_text(encoding="utf-8").lower()
    clean_text = clean_card.read_text(encoding="utf-8").lower()
    leak_patterns = [
        r"above.*range", r"out of range", r"extrapolat", r"exceed", r"dilut",
        r"hazard", r"trap", r"planted", r"careful", r"suspicious", r"beware",
    ]
    leaks = [p for p in leak_patterns if re.search(p, hazard_text) and not re.search(p, clean_text)]
    return {
        "attacker": "card-language",
        "clean_card": str(clean_card),
        "hazard_card": str(hazard_card),
        "leaking_patterns": leaks,
        "verdict": "CARD LEAKS HAZARD" if leaks else "resisted",
    }


def artifact_spoof_attack(task_dir: Path) -> dict:
    """Schema-valid, scientifically empty files must not pass (guide 22.9 #10)."""
    task_dir = Path(task_dir)
    spoof_files = {
        "status.json": json.dumps({"status": "COMPLETED", "note": "spoof"}),
        "report.md": "# Result\n\nDone.",
        "claims.json": json.dumps({"claims": [], "hazards": []}),
        "artifacts/calibration.json": json.dumps({"slope": 1.0, "intercept": 0.0, "r_squared": 1.0}),
        "artifacts/result.json": json.dumps({"sample_id": "X", "concentration_mg_per_l": 1.0}),
        "reproduction/reproduce.py": "print('spoof')\n",
    }
    with tempfile.TemporaryDirectory(prefix="crucible-spoof-") as tmp:
        spoof_dir = Path(tmp) / "spoof"
        _write_submission(spoof_files, spoof_dir)
        outcome = run_verification(task_dir, spoof_dir)
    return {
        "attacker": "artifact-spoof",
        "task": task_dir.name,
        "reliable_completion": outcome["reliable_completion"],
        "verdict": "SPOOF PASSED - verifier invalid" if outcome["reliable_completion"] else "resisted",
    }


def run_suite(repo_root: Path, out_dir: Path) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n0 = repo_root / "tasks_public" / "CHEM-LC-CAL-001" / "instances" / "N0-s101"
    n1 = repo_root / "tasks_public" / "CHEM-LC-CAL-001" / "instances" / "N1-s102"
    results = [
        metadata_only_attack(n0, "openai", out_dir / "metadata-openai-N0"),
        metadata_only_attack(n1, "anthropic", out_dir / "metadata-anthropic-N1"),
        card_language_audit(n0 / "task_card" / "card.md", n1 / "task_card" / "card.md"),
        artifact_spoof_attack(n0),
        {
            "attacker": "naive-replay",
            "note": "exercised by verifier self-tests (rejected/naive-replay must fail)",
            "verdict": "resisted (see verify selftest)",
        },
    ]
    report = {
        "results": results,
        "all_resisted": all("resisted" in r["verdict"] for r in results),
    }
    (out_dir / "shortcut_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
